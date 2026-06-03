# apps/orders/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import mercadopago

from django.conf import settings

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from .shipping import calculate_shipping
from apps.cart.models import CartItem


# ── Calcular Frete ─────────────────────────────────────────────────────────────
class ShippingCalculateView(APIView):
    def post(self, request):
        state = request.data.get('state', '').strip()
        city  = request.data.get('city', '').strip()

        if not state or not city:
            return Response(
                {'error': 'Informe estado e cidade'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cost = calculate_shipping(state, city)
        return Response({
            'state':         state.upper(),
            'city':          city,
            'shipping_cost': cost,
            'free':          cost == 0.00,
        })


# ── Criar Preferência Mercado Pago ─────────────────────────────────────────────
class CreateMPPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart_items = CartItem.objects.filter(
            user=request.user
        ).select_related('product')

        if not cart_items.exists():
            return Response({'error': 'Carrinho vazio'}, status=400)

        state = request.data.get('state', '')
        city  = request.data.get('city', '')

        if not state or not city:
            return Response({'error': 'Informe estado e cidade'}, status=400)

        shipping_cost = calculate_shipping(state, city)

        mp_items = []
        for item in cart_items:
            mp_items.append({
                'id':          str(item.product.id),
                'title':       item.product.name,
                'quantity':    item.quantity,
                'unit_price':  float(item.product.price),
                'currency_id': 'BRL',
            })

        if shipping_cost > 0:
            mp_items.append({
                'id':          'shipping',
                'title':       'Frete',
                'quantity':    1,
                'unit_price':  float(shipping_cost),
                'currency_id': 'BRL',
            })

        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

        preference_data = {
            'items': mp_items,
            'payer': {
                'email': request.user.email,
                'name':  getattr(request.user, 'name', request.user.email),
            },
            # ✅ Só PIX e cartão de crédito, máximo 3x
            'payment_methods': {
                'excluded_payment_types': [
                    {'id': 'debit_card'},
                    {'id': 'prepaid_card'},
                    {'id': 'bank_transfer'},
                    {'id': 'ticket'},          # boleto
                    {'id': 'atm'},
                ],
                'installments': 3,
            },
            'back_urls': {
                'success': f'{settings.FRONTEND_URL}/pages/checkout.html?status=success',
                'failure': f'{settings.FRONTEND_URL}/pages/checkout.html?status=failure',
                'pending': f'{settings.FRONTEND_URL}/pages/checkout.html?status=pending',
            },
            'auto_return':          'approved',
            'statement_descriptor': 'GLINS STORE',
            # ✅ Usamos o ID do pedido futuramente; por ora user.id
            'external_reference':   str(request.user.id),
            'notification_url':     f'{settings.BACKEND_URL}/api/orders/payment/webhook/',
        }

        result = sdk.preference().create(preference_data)

        if result['status'] not in [200, 201]:
            return Response({'error': 'Erro ao criar preferência MP'}, status=502)

        preference = result['response']
        return Response({
            'preference_id': preference['id'],
            'init_point':    preference['init_point'],
            'sandbox_url':   preference['sandbox_init_point'],
            'shipping_cost': shipping_cost,
        })


# ── Processar Pagamento (chamado pelo Brick) ───────────────────────────────────
class PaymentProcessView(APIView):
    """
    POST /api/orders/payment/process/
    Recebe formData do Brick, cria o pagamento no MP e retorna status + QR PIX se necessário.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sdk       = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        form_data = request.data  # vem direto do Brick do MP

        result  = sdk.payment().create(form_data)
        payment = result['response']

        mp_status = payment.get('status')          # approved / pending / rejected
        payment_id = payment.get('id')

        # Atualiza o pedido pendente mais recente do usuário
        if mp_status in ['approved', 'pending']:
            try:
                order = Order.objects.filter(
                    user=request.user,
                    status='pending'
                ).latest('created_at')

                if mp_status == 'approved':
                    order.status = 'paid'
                    order.save()
                # pending → mantém 'pending', webhook vai atualizar quando pix for pago

            except Order.DoesNotExist:
                pass

        response_data = {
            'status':     mp_status,
            'payment_id': payment_id,
        }

        # ✅ Se for PIX pendente, devolve os dados do QR
        if mp_status == 'pending' and payment.get('point_of_interaction'):
            response_data['point_of_interaction'] = payment['point_of_interaction']

        return Response(response_data)


# ── Webhook Mercado Pago ───────────────────────────────────────────────────────
class MPWebhookView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        topic = request.data.get('type') or request.query_params.get('topic')
        resource_id = (
            request.data.get('data', {}).get('id')
            or request.query_params.get('id')
        )

        if topic == 'payment' and resource_id:
            sdk     = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            payment = sdk.payment().get(resource_id)

            if payment['status'] == 200:
                p         = payment['response']
                mp_status = p.get('status')
                ext_ref   = p.get('external_reference')  # user.id

                try:
                    order = Order.objects.filter(
                        user_id=ext_ref,
                        status='pending'
                    ).latest('created_at')

                    if mp_status == 'approved':
                        order.status = 'paid'
                        order.save()
                except Order.DoesNotExist:
                    pass

        return Response({'ok': True})


# ── Criar Pedido ───────────────────────────────────────────────────────────────
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related('items').order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        addr = serializer.validated_data

        cart_items = CartItem.objects.filter(
            user=request.user
        ).select_related('product')

        if not cart_items.exists():
            return Response({'error': 'Carrinho vazio'}, status=400)

        for item in cart_items:
            if item.product.stock < item.quantity:
                return Response(
                    {'error': f'Estoque insuficiente para "{item.product.name}"'},
                    status=400
                )

        shipping_cost = Decimal(str(
            calculate_shipping(addr['state'], addr['city'])
        ))

        subtotal = sum(i.subtotal for i in cart_items)
        total    = subtotal + shipping_cost

        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_cost=shipping_cost,
            **addr
        )

        for item in cart_items:
            OrderItem.objects.create(
                order    = order,
                product  = item.product,
                name     = item.product.name,
                price    = item.product.price,
                quantity = item.quantity,
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()

        return Response(OrderSerializer(order).data, status=201)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items')


# ── Admin Views ────────────────────────────────────────────────────────────────
class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(status=403)

        orders = Order.objects.all().select_related(
            'user'
        ).prefetch_related('items').order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)

        return Response(OrderSerializer(orders, many=True).data)


class AdminOrderUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_admin:
            return Response(status=403)

        order         = get_object_or_404(Order, pk=pk)
        new_status    = request.data.get('status')
        tracking_code = request.data.get('tracking_code')

        if new_status:
            valid = [s[0] for s in Order.STATUS]
            if new_status not in valid:
                return Response({'error': 'Status inválido'}, status=400)
            order.status = new_status

        if tracking_code:
            order.tracking_code = tracking_code

        order.save()
        return Response(OrderSerializer(order).data)
