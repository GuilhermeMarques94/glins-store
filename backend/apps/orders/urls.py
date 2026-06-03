# apps/orders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Pedidos
    path('',                          views.OrderListView.as_view(),           name='order_list'),
    path('<int:pk>/',                  views.OrderDetailView.as_view(),         name='order_detail'),

    # Frete
    path('shipping/',                  views.ShippingCalculateView.as_view(),   name='shipping_calculate'),

    # Mercado Pago
    path('payment/preference/',        views.CreateMPPreferenceView.as_view(),  name='mp_preference'),
    path('payment/process/',           views.PaymentProcessView.as_view(),      name='mp_process'),   # ✅ NOVO
    path('payment/webhook/',           views.MPWebhookView.as_view(),           name='mp_webhook'),

    # Admin
    path('admin/',                     views.AdminOrderListView.as_view(),      name='admin_orders'),
    path('admin/<int:pk>/',            views.AdminOrderUpdateView.as_view(),    name='admin_order_update'),
]
