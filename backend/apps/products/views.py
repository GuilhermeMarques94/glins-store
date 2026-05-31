from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Count
from django.utils.text import slugify
from django.conf import settings
from supabase import create_client
import uuid, os

from .models import Product, Category
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer


# ── Supabase Storage helper ──────────────────────────────────────────────────
def upload_image_to_supabase(file) -> str:
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    ext      = file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    content  = file.read()

    sb.storage.from_(settings.SUPABASE_BUCKET).upload(
        path=filename,
        file=content,
        file_options={"content-type": file.content_type}
    )

    public_url = sb.storage.from_(settings.SUPABASE_BUCKET).get_public_url(filename)
    return public_url


# ── Categories ───────────────────────────────────────────────────────────────
class CategoryListView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count('products'))


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
        qs = Product.objects.filter(is_active=True).select_related('category')

        category = self.request.query_params.get('category')
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
        return Product.objects.filter(is_active=True)


class ProductImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        product = Product.objects.get(pk=pk)
        serializer = ProductImageSerializer(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        url = upload_image_to_supabase(request.FILES['image'])
        product.image_url = url
        product.save()

        return Response({'image_url': url}, status=status.HTTP_200_OK)


class AdminProductListView(generics.ListAPIView):
    """Lista todos os produtos para o admin (incluindo inativos)"""
    serializer_class   = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_admin:
            return Product.objects.none()
        return Product.objects.all().select_related('category').order_by('-created_at')

