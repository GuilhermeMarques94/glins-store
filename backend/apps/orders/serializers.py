from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal      = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    product_name  = serializers.CharField(source='name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'name', 'price', 'quantity', 'subtotal']

    def get_product_image(self, obj):
        if obj.product:
            return obj.product.image_url or None
        return None


class OrderUserSerializer(serializers.Serializer):
    """Serializer leve só para expor dados do cliente no pedido"""
    name       = serializers.SerializerMethodField()
    email      = serializers.EmailField()
    first_name = serializers.CharField(default='')
    last_name  = serializers.CharField(default='')

    def get_name(self, obj):
        return getattr(obj, 'name', None) or f'{obj.first_name} {obj.last_name}'.strip() or obj.email


class OrderSerializer(serializers.ModelSerializer):
    items        = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    user         = OrderUserSerializer(read_only=True)  # ✅ expõe dados do cliente

    class Meta:
        model  = Order
        fields = [
            'id', 'status', 'status_label', 'total',
            'street', 'number', 'complement',
            'city', 'state', 'zipcode',
            'shipping_cost', 'tracking_code',
            'items', 'user',               # ✅ user incluído
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'status', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    street     = serializers.CharField()
    number     = serializers.CharField()
    complement = serializers.CharField(required=False, allow_blank=True)
    city       = serializers.CharField()
    state      = serializers.CharField(max_length=2)
    zipcode    = serializers.CharField(max_length=10)
