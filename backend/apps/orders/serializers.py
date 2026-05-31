from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'name', 'price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items        = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'status', 'status_label', 'total',
            'street', 'number', 'complement',
            'city', 'state', 'zipcode',
            'shipping_cost', 'tracking_code',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'status', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    street     = serializers.CharField()
    number     = serializers.CharField()
    complement = serializers.CharField(required=False, allow_blank=True)
    city       = serializers.CharField()
    state      = serializers.CharField(max_length=2)
    zipcode    = serializers.CharField(max_length=10)
