from rest_framework import serializers
from .models import Product, Category, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'product_count']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['id', 'image_url', 'order']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    in_stock      = serializers.BooleanField(read_only=True)
    images        = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'category', 'category_name',
            'name', 'slug', 'description',
            'price', 'stock', 'in_stock',
            'image_url', 'images',          # ← image_url legado + galeria nova
            'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    order = serializers.IntegerField(default=0, required=False)
