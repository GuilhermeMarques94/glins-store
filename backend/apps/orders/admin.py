from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    readonly_fields = ('product', 'name', 'price', 'quantity', 'subtotal')
    can_delete      = False

    @admin.display(description='Subtotal')
    def subtotal(self, obj):
        return f'R$ {obj.subtotal:.2f}'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ('id', 'user_name', 'status', 'total_fmt', 'shipping_cost', 'tracking_code', 'created_at')
    list_filter     = ('status',)
    search_fields   = ('user__email', 'user__name', 'tracking_code')
    readonly_fields = ('user', 'total', 'shipping_cost', 'street', 'number',
                       'complement', 'city', 'state', 'zipcode', 'created_at', 'updated_at')
    ordering        = ('-created_at',)
    inlines         = [OrderItemInline]

    fieldsets = (
        ('👤 Cliente',      {'fields': ('user',)}),
        ('📋 Pedido',       {'fields': ('status', 'total', 'shipping_cost')}),
        ('📍 Endereço',     {'fields': ('zipcode', 'street', 'number', 'complement', 'city', 'state')}),
        ('🚚 Entrega',      {'fields': ('tracking_code',)}),
        ('📅 Datas',        {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Cliente')
    def user_name(self, obj):
        return obj.user.name

    @admin.display(description='Total')
    def total_fmt(self, obj):
        return f'R$ {obj.total:.2f}'
