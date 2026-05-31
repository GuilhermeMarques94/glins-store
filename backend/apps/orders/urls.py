from django.urls import path
from . import views

urlpatterns = [
    path('',              views.OrderListView.as_view(),        name='order_list'),
    path('<int:pk>/',     views.OrderDetailView.as_view(),      name='order_detail'),
    path('admin/',        views.AdminOrderListView.as_view(),   name='admin_orders'),
    path('admin/<int:pk>/',views.AdminOrderUpdateView.as_view(),name='admin_order_update'),
]
