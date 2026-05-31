from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import CartItem
from .serializers import CartItemSerializer
from apps.products.models import Product


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def _cart_response(self, user):
        items      = CartItem.objects.filter(user=user).select_related('product__category')
        serialized = CartItemSerializer(items, many=True)
        total      = sum(i.subtotal for i in items)
        quantity   = sum(i.quantity for i in items)
        return Response({
            'items':    serialized.data,
            'total':    total,
            'quantity': quantity,
        })

    def get(self, request):
        return self._cart_response(request.user)

    def post(self, request):
        """Adicionar ou atualizar item no carrinho"""
        product_id = request.data.get('product_id')
        quantity   = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id, is_active=True)

        if product.stock < quantity:
            return Response(
                {'error': f'Estoque insuficiente. Disponível: {product.stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_qty = item.quantity + quantity
            if product.stock < new_qty:
                return Response(
                    {'error': f'Estoque insuficiente. Disponível: {product.stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.quantity = new_qty
            item.save()

        return self._cart_response(request.user)

    def delete(self, request):
        """Limpar carrinho inteiro"""
        CartItem.objects.filter(user=request.user).delete()
        return Response({'message': 'Carrinho limpo'})


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """Atualizar quantidade de um item"""
        item     = get_object_or_404(CartItem, pk=pk, user=request.user)
        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            item.delete()
            return Response({'message': 'Item removido'})

        if item.product.stock < quantity:
            return Response(
                {'error': f'Estoque insuficiente. Disponível: {item.product.stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = quantity
        item.save()

        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        """Remover item específico"""
        item = get_object_or_404(CartItem, pk=pk, user=request.user)
        item.delete()
        return Response({'message': 'Item removido'})
