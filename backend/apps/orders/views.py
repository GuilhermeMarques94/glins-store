# apps/orders/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import mercadopago
import uuid
import logging

from django.conf import settings

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from .shipping import calculate_shipping
from .emails import (                           # ← NOVO
    send_order_created_email,
    send_payment_approved_email,
)
from apps.cart.models import CartItem

logger = logging.getLogger(__name__)


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
            'payment_methods': {
                'excluded_payment_types': [
                    {'id': 'debit_card'},
                    {'id': 'prepaid_card'},
                    {'id': 'ticket'},
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.warning(f"[MP] TOKEN USADO: {settings.MP_ACCESS_TOKEN[:20]}...")
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
        form_data = request.data

        logger.warning(f"[MP] form_data recebido: {dict(form_data)}")

        payer = form_data.get('payer', {})

        payer_data = {}
        if isinstance(payer, dict):
            payer_data['email'] = payer.get('email', '')
            if payer.get('identification'):
                payer_data['identification'] = {
                    'type':   payer['identification'].get('type', 'CPF'),
                    'number': payer['identification'].get('number', ''),
                }
        else:
            payer_data['email'] = payer

        payment_data = {
            'transaction_amount': float(form_data.get('transaction_amount', 0)),
            'description':        form_data.get('description', 'Glins Store'),
            'payment_method_id':  form_data.get('payment_method_id', 'pix'),
            'installments':       int(form_data.get('installments', 1)),
            'payer':              payer_data,
            'external_reference':   str(request.user.id),
            'notification_url':     f'{settings.BACKEND_URL}/api/orders/payment/webhook/',
            'statement_descriptor': 'GLINS STORE',
        }

        if form_data.get('token'):
            payment_data['token'] = form_data.get('token')
        if form_data.get('issuer_id'):
            payment_data['issuer_id'] = form_data.get('issuer_id')

        logger.warning(f"[MP] payload enviado: {payment_data}")

        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'X-Idempotency-Key': str(uuid.uuid4())
        }

        result     = sdk.payment().create(payment_data, request_options)
        payment    = result.get('response', {})
        mp_status  = payment.get('status')
        mp_detail  = payment.get('status_detail', '')
        payment_id = payment.get('id')

        logger.warning(f"[MP] status: {mp_status} | detail: {mp_detail} | id: {payment_id}")
        logger.warning(f"[MP] response completo: {payment}")

        if mp_status not in ['approved', 'pending']:
            return Response({
                'status':        mp_status,
                'status_detail': mp_detail,
                'payment_id':    payment_id,
                'error':         self._traduz_erro(mp_detail),
            }, status=200)

        addr_data = request.data.get('address', {})

        try:
            order = self._criar_pedido(request.user, addr_data, payment_id, mp_status)
        except Exception as e:
            logger.error(f"[PEDIDO] Erro ao criar pedido: {e}")
            return Response({
                'status':     mp_status,
                'payment_id': payment_id,
                'warning':    'Pagamento confirmado mas houve erro ao registrar pedido.',
            })

        # ── Disparo de e-mails ─────────────────────────────────────────────────
        try:
            if mp_status == 'pending':
                send_order_created_email(order)       # PIX aguardando pagamento
            elif mp_status == 'approved':
                send_payment_approved_email(order)    # Cartão aprovado + notifica admin
        except Exception as e:
            logger.error(f"[EMAIL] Erro ao enviar e-mail pós-pagamento: {e}")
        # ──────────────────────────────────────────────────────────────────────

        response_data = {
            'status':     mp_status,
            'payment_id': payment_id,
            'order_id':   order.id,
        }

        if mp_status == 'pending':
            poi  = payment.get('point_of_interaction', {})
            tx   = poi.get('transaction_data', {})
            qr   = tx.get('qr_code', '')
            qr64 = tx.get('qr_code_base64', '')

            logger.warning(f"[PIX] qr_code presente: {bool(qr)} | base64 presente: {bool(qr64)}")

            response_data['qr_code']        = qr
            response_data['qr_code_base64'] = qr64

        return Response(response_data)

    @transaction.atomic
    def _criar_pedido(self, user, addr_data, payment_id, mp_status):
        cart_items = CartItem.objects.filter(
            user=user
        ).select_related('product')

        if not cart_items.exists():
            raise ValueError('Carrinho vazio ao tentar criar pedido')

        for item in cart_items:
            if item.product.stock < item.quantity:
                raise ValueError(f'Estoque insuficiente: {item.product.name}')

        shipping_cost = Decimal(str(
            calculate_shipping(
                addr_data.get('state', ''),
                addr_data.get('city', '')
            )
        ))

        subtotal = sum(i.subtotal for i in cart_items)
        total    = subtotal + shipping_cost

        order = Order.objects.create(
            user          = user,
            total         = total,
            shipping_cost = shipping_cost,
            payment_id    = str(payment_id) if payment_id else '',
            status        = 'paid' if mp_status == 'approved' else 'pending',
            street        = addr_data.get('street', ''),
            number        = addr_data.get('number', ''),
            complement    = addr_data.get('complement', ''),
            city          = addr_data.get('city', ''),
            state         = addr_data.get('state', ''),
            zipcode       = addr_data.get('zipcode', ''),
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

        logger.warning(f"[PEDIDO] Criado #{order.id} status={order.status}")
        return order

    def _traduz_erro(self, detail):
        erros = {
            'cc_rejected_insufficient_amount':    'Saldo insuficiente no cartão.',
            'cc_rejected_bad_filled_card_number': 'Número do cartão inválido.',
            'cc_rejected_bad_filled_date':        'Data de validade inválida.',
            'cc_rejected_bad_filled_security_code': 'CVV inválido.',
            'cc_rejected_blacklist':              'Cartão não autorizado.',
            'cc_rejected_call_for_authorize':     'Ligue para seu banco para autorizar.',
            'cc_rejected_duplicated_payment':     'Pagamento duplicado detectado.',
            'cc_rejected_high_risk':              'Pagamento recusado por segurança.',
        }
        return erros.get(detail, 'Pagamento não aprovado. Tente novamente.')


# ── Webhook Mercado Pago ───────────────────────────────────────────────────────
class MPWebhookView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        topic       = request.data.get('type') or request.query_params.get('topic')
        resource_id = (
            request.data.get('data', {}).get('id')
            or request.query_params.get('id')
        )

        logger.warning(f"[WEBHOOK] topic={topic} | id={resource_id}")

        if topic == 'payment' and resource_id:
            sdk    = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            result = sdk.payment().get(resource_id)

            if result['status'] == 200:
                p          = result['response']
                mp_status  = p.get('status')
                payment_id = str(p.get('id', ''))

                logger.warning(f"[WEBHOOK] payment_id={payment_id} status={mp_status}")

                try:
                    order = Order.objects.get(payment_id=payment_id)
                    if mp_status == 'approved' and order.status != 'paid':
                        order.status = 'paid'
                        order.save()
                        logger.warning(f"[WEBHOOK] Pedido #{order.id} marcado como PAGO")

                        # ── Disparo e-mail aprovação via webhook (PIX confirmado) ──
                        try:
                            send_payment_approved_email(order)
                        except Exception as e:
                            logger.error(f"[EMAIL] Erro no webhook ao enviar e-mail: {e}")
                        # ──────────────────────────────────────────────────────────

                except Order.DoesNotExist:
                    ext_ref = p.get('external_reference')
                    try:
                        order = Order.objects.filter(
                            user_id=ext_ref,
                            status='pending'
                        ).latest('created_at')
                        if mp_status == 'approved':
                            order.status = 'paid'
                            order.save()
                            logger.warning(f"[WEBHOOK] Pedido #{order.id} pago via fallback")

                            # ── Disparo e-mail fallback ────────────────────────────
                            try:
                                send_payment_approved_email(order)
                            except Exception as e:
                                logger.error(f"[EMAIL] Erro no webhook fallback: {e}")
                            # ──────────────────────────────────────────────────────

                    except Order.DoesNotExist:
                        logger.warning(f"[WEBHOOK] Nenhum pedido encontrado para payment_id={payment_id}")

        return Response({'ok': True})


# ── Listar / Criar Pedidos ────────────────────────────────────────────────────
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
