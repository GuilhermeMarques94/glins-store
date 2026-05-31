from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display        = ('email', 'name', 'phone', 'city', 'state', 'is_staff', 'is_active', 'created_at')
    list_filter         = ('is_staff', 'is_admin', 'is_active', 'state')
    search_fields       = ('email', 'name', 'phone')
    ordering            = ('-created_at',)
    readonly_fields     = ('created_at',)
    filter_horizontal   = ('groups', 'user_permissions')

    fieldsets = (
        ('🔐 Login',        {'fields': ('email', 'password')}),
        ('👤 Dados',        {'fields': ('name', 'phone')}),
        ('📍 Endereço',     {'fields': ('zipcode', 'street', 'number', 'complement', 'city', 'state')}),
        ('⚙️ Permissões',   {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('📅 Datas',        {'fields': ('created_at',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'name', 'password1', 'password2', 'is_staff', 'is_admin'),
        }),
    )
