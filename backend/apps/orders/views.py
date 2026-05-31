from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from cart.models import CartItem


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Histórico de pedidos do usuário"""
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related('items').order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)

    @transaction.atomic
    def post(self, request):
        """Criar pedido a partir do carrinho"""
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        addr = serializer.validated_data

        cart_items = CartItem.objects.filter(
            user=request.user
        ).select_related('product')

        if not cart_items.exists():
            return Response(
                {'error': 'Carrinho vazio'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar estoque de todos os itens
        for item in cart_items:
            if item.product.stock < item.quantity:
                return Response(
                    {'error': f'Estoque insuficiente para "{item.product.name}"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calcular total
        total = sum(i.subtotal for i in cart_items)

        # Criar pedido
        order = Order.objects.create(
            user=request.user,
            total=total,
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

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items')


# ── Admin Views ───────────────────────────────────────────────────────────────
class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)

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
            return Response(status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, pk=pk)
        new_status     = request.data.get('status')
        tracking_code  = request.data.get('tracking_code')

        if new_status:
            valid = [s[0] for s in Order.STATUS]
            if new_status not in valid:
                return Response({'error': 'Status inválido'}, status=400)
            order.status = new_status

        if tracking_code:
            order.tracking_code = tracking_code

        order.save()
        return Response(OrderSerializer(order).data)
