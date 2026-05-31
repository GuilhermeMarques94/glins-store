from django.urls import path
from . import views

urlpatterns = [
    path('',          views.CartView.as_view(),      name='cart'),
    path('<int:pk>/', views.CartItemView.as_view(),  name='cart_item'),
]
