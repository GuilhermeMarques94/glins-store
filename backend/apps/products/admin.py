from django.contrib import admin
from .models import Category, Product, ProductImage  # ← adiciona ProductImage

# ── Inline de imagens ──────────────────────────────────────────
class ProductImageInline(admin.TabularInline):
    model   = ProductImage
    extra   = 3        # abre 3 campos vazios por padrão
    fields  = ('image_url', 'order')
    ordering = ('order',)

# ── Category ───────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ('name', 'slug', 'icon')
    search_fields       = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ── Product ────────────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ('name', 'category', 'price', 'stock', 'in_stock', 'is_active', 'created_at')
    list_filter         = ('category', 'is_active')
    search_fields       = ('name', 'description')
    list_editable       = ('price', 'stock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields     = ('created_at', 'updated_at', 'in_stock')
    ordering            = ('-created_at',)
    inlines             = [ProductImageInline]  # ← adiciona aqui

    fieldsets = (
        ('📦 Produto',    {'fields': ('category', 'name', 'slug', 'description', 'image_url')}),
        ('💰 Preço',      {'fields': ('price', 'stock')}),
        ('⚙️ Controle',  {'fields': ('is_active', 'in_stock')}),
        ('📅 Datas',      {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(boolean=True, description='Em estoque?')
    def in_stock(self, obj):
        return obj.in_stock
