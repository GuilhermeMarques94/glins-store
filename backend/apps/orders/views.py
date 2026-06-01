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
    """
    POST /api/orders/shipping/
    Body: { "state": "MG", "city": "Uberlândia" }
    """
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
    """
    POST /api/orders/payment/preference/
    Cria a preferência de pagamento no MP e retorna o preference_id
    """
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

        # Montar itens para o MP
        mp_items = []
        for item in cart_items:
            mp_items.append({
                'id':          str(item.product.id),
                'title':       item.product.name,
                'quantity':    item.quantity,
                'unit_price':  float(item.product.price),
                'currency_id': 'BRL',
            })

        # Adiciona frete como item (se houver)
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
            'back_urls': {
                'success': f'{settings.FRONTEND_URL}/pages/checkout.html?status=success',
                'failure': f'{settings.FRONTEND_URL}/pages/checkout.html?status=failure',
                'pending': f'{settings.FRONTEND_URL}/pages/checkout.html?status=pending',
            },
            'auto_return':          'approved',
            'statement_descriptor': 'GLINS STORE',
            'external_reference':   str(request.user.id),
        }

        result = sdk.preference().create(preference_data)

        if result['status'] not in [200, 201]:
            return Response({'error': 'Erro ao criar preferência MP'}, status=502)

        preference = result['response']
        return Response({
            'preference_id': preference['id'],
            'init_point':    preference['init_point'],       # produção
            'sandbox_url':   preference['sandbox_init_point'], # teste
            'shipping_cost': shipping_cost,
        })


# ── Webhook Mercado Pago ───────────────────────────────────────────────────────
class MPWebhookView(APIView):
    """
    POST /api/orders/payment/webhook/
    Recebe notificações do Mercado Pago
    """
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
                p      = payment['response']
                mp_status = p.get('status')           # approved / pending / rejected
                ext_ref   = p.get('external_reference')  # user.id
                amount    = Decimal(str(p.get('transaction_amount', 0)))

                # Atualiza o pedido mais recente pendente do usuário
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

        # Validar estoque
        for item in cart_items:
            if item.product.stock < item.quantity:
                return Response(
                    {'error': f'Estoque insuficiente para "{item.product.name}"'},
                    status=400
                )

        # Calcular frete
        shipping_cost = Decimal(str(
            calculate_shipping(addr['state'], addr['city'])
        ))

        # Calcular total
        subtotal = sum(i.subtotal for i in cart_items)
        total    = subtotal + shipping_cost

        # Criar pedido
        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_cost=shipping_cost,
            **addr
        )

        # Criar itens e baixar estoque
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

        # Limpar carrinho
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
