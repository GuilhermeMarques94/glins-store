import threading
import logging
import os

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer
from .emails import send_welcome_email

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = _get_tokens(user)

        # ✅ Thread sem daemon=True — Gunicorn não mata antes de terminar
        thread = threading.Thread(target=self._send_email, args=(user,))
        thread.daemon = False  # ← era True antes, esse era o problema
        thread.start()

        return Response({
            'user': UserSerializer(user).data,
            **tokens
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def _send_email(user):
        try:
            send_welcome_email(user)
            logger.info(f"[EMAIL] ✅ Boas-vindas enviado para {user.email}")
        except Exception as e:
            logger.error(f"[EMAIL] ❌ Boas-vindas falhou para {user.email}: {e}")

    @staticmethod
    def _send_email(user):
        try:
            send_welcome_email(user)
        except Exception as e:
            logger.error(f"[EMAIL] Boas-vindas falhou para {user.email}: {e}")


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Credenciais inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        tokens = _get_tokens(user)
        return Response({
            'user': UserSerializer(user).data,
            **tokens
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Logout realizado com sucesso'})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Senha atual incorreta'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Senha alterada com sucesso'})


# ── Helper ─────────────────────────────────────────────────────────────
def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
    }


# ── Endpoint TEMPORÁRIO para criar superusuário ────────────────────────
@csrf_exempt
def create_superuser_temp(request):
    secret = request.GET.get('secret', '')
    if secret != os.environ.get('SUPERUSER_SECRET', ''):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    email    = os.environ.get('SUPERUSER_EMAIL', '')
    password = os.environ.get('SUPERUSER_PASSWORD', '')
    name     = os.environ.get('SUPERUSER_NAME', 'Admin')

    if not email or not password:
        return JsonResponse(
            {'error': 'Variáveis SUPERUSER_EMAIL e SUPERUSER_PASSWORD não configuradas'},
            status=400
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse({'message': 'Superusuário já existe!'})

    User.objects.create_superuser(email=email, name=name, password=password)
    return JsonResponse({'message': f'Superusuário {email} criado com sucesso!'})
