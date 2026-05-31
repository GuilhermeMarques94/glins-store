from rest_framework import serializers
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'product_count']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    in_stock      = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'category', 'category_name',
            'name', 'slug', 'description',
            'price', 'stock', 'in_stock',
            'image_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
