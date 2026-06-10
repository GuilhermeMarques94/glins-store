from django.db import models
from django.conf import settings
from apps.products.models import Product


class Order(models.Model):
    STATUS = [
        ('pending',   '⏳ Aguardando pagamento'),
        ('paid',      '✅ Pago'),
        ('preparing', '🔨 Preparando'),
        ('shipped',   '🚚 Enviado'),
        ('delivered', '📦 Entregue'),
        ('cancelled', '❌ Cancelado'),
    ]

    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status        = models.CharField(max_length=20, choices=STATUS, default='pending')
    total         = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id    = models.CharField(max_length=100, blank=True, default='')  # ✅ NOVO
    # Endereço
    street        = models.CharField(max_length=200)
    number        = models.CharField(max_length=10)
    complement    = models.CharField(max_length=100, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=2)
    zipcode       = models.CharField(max_length=10)
    # Frete
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tracking_code = models.CharField(max_length=50, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            user_label = getattr(self.user, 'name', None) or getattr(self.user, 'email', f'ID {self.user_id}')
        except Exception:
            user_label = f'Usuário #{self.user_id}'
        return f'Pedido #{self.id} — {user_label}'


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name     = models.CharField(max_length=200)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity
