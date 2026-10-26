from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin configuration for managing portal users and roles.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Portal Role & Contact', {
            'fields': ('role', 'phone_number'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Portal Role & Contact', {
            'fields': ('role', 'phone_number'),
        }),
    )
    list_display = (
        'username',
        'email',
        'role',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)