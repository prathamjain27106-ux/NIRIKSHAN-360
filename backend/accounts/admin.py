from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "cell", "is_active", "created_at")
    list_filter = ("role", "cell", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("NIRIKSHAN 360", {"fields": ("role", "cell")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("NIRIKSHAN 360", {"fields": ("role", "cell")}),
    )
