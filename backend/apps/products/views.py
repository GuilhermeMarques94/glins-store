from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from django.utils.text import slugify
from django.conf import settings
from supabase import create_client
import uuid

from .models import Product, Category, ProductImage
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductImageSerializer, ProductImageUploadSerializer,
    ProductImageURLSerializer
)


# ── Supabase Storage helper ──────────────────────────────────────────────────
def upload_image_to_supabase(file) -> str:
    sb       = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    ext      = file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    content  = file.read()

    sb.storage.from_(settings.SUPABASE_BUCKET).upload(
        path=filename,
        file=content,
        file_options={"content-type": file.content_type}
    )
    return sb.storage.from_(settings.SUPABASE_BUCKET).get_public_url(filename)


# ── Categories ───────────────────────────────────────────────────────────────
class CategoryListView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        )


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]


# ── Products ─────────────────────────────────────────────────────────────────
class ProductListView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['name', 'description', 'category__name']
    ordering_fields  = ['price', 'created_at', 'name']
    ordering         = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = (Product.objects
              .filter(is_active=True)
              .select_related('category')
              .prefetch_related('images'))   # ← prefetch das imagens

        category  = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        in_stock  = self.request.query_params.get('in_stock')

        if category:
            qs = qs.filter(category__slug=category)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if in_stock == 'true':
            qs = qs.filter(stock__gt=0)

        return qs

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name', '')
        serializer.save(slug=slugify(name))


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return (Product.objects
                .filter(is_active=True)
                .select_related('category')
                .prefetch_related('images'))


# ── Imagens do Produto ────────────────────────────────────────────────────────
class ProductImageListView(APIView):
    """
    GET  /products/<pk>/images/  → lista imagens do produto
    POST /products/<pk>/images/  → upload de arquivo OU URL direta
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        images = ProductImage.objects.filter(product_id=pk)
        return Response(ProductImageSerializer(images, many=True).data)

    def post(self, request, pk):
        product = Product.objects.get(pk=pk)

        # ── Modo 1: URL direta (JSON com image_url) ──────────────────────────
        if 'image_url' in request.data:
            serializer = ProductImageURLSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            url   = serializer.validated_data['image_url']
            order = serializer.validated_data.get('order', 0)

        # ── Modo 2: Upload de arquivo (multipart com image) ──────────────────
        elif 'image' in request.FILES:
            serializer = ProductImageUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            url   = upload_image_to_supabase(request.FILES['image'])
            order = serializer.validated_data.get('order', 0)

        else:
            return Response(
                {'error': 'Envie "image_url" (URL) ou "image" (arquivo).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        img = ProductImage.objects.create(product=product, image_url=url, order=order)

        # ✅ Só sincroniza image_url legado se for a PRIMEIRA imagem do produto
        ja_tem_imagens = ProductImage.objects.filter(product=product).exclude(pk=img.pk).exists()
        if not ja_tem_imagens:
            product.image_url = url
            product.save(update_fields=['image_url'])

        return Response(ProductImageSerializer(img).data, status=status.HTTP_201_CREATED)


class ProductImageDeleteView(APIView):
    """DELETE /products/<pk>/images/<img_id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, img_id):
        img = ProductImage.objects.get(pk=img_id, product_id=pk)
        img.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Admin ────────────────────────────────────────────────────────────────────
class AdminProductListView(generics.ListAPIView):
    serializer_class   = ProductSerializer
    permission_classes = [IsAuthenticated]
    # SEM filter_backends — tudo manual para garantir funcionamento

    def get_queryset(self):
        if not self.request.user.is_admin:
            return Product.objects.none()

        qs = (Product.objects.all()
              .select_related('category')
              .prefetch_related('images')
              .order_by('-created_at'))

        # 🔍 Busca por nome ou descrição
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )

        # 📂 Filtro por categoria (ID)
        category = self.request.query_params.get('category', '').strip()
        if category:
            qs = qs.filter(category__id=category)

        # ✅/❌ Filtro por status
        status_filter = self.request.query_params.get('status', '').strip()
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inactive':
            qs = qs.filter(is_active=False)

        return qs
