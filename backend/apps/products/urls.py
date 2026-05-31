from django.urls import path
from . import views

urlpatterns = [
    # Categorias
    path('categories/',          views.CategoryListView.as_view(),       name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(),     name='category_detail'),

    # Produtos públicos
    path('',                     views.ProductListView.as_view(),         name='product_list'),
    path('<int:pk>/',             views.ProductDetailView.as_view(),       name='product_detail'),
    path('<int:pk>/upload-image/',views.ProductImageUploadView.as_view(), name='product_upload'),

    # Admin
    path('admin/all/',           views.AdminProductListView.as_view(),    name='admin_products'),
]
