"""Конфигурация админки для приложения Users."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .models import User

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административный интерфейс для модели User."""

    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = (
        *(BaseUserAdmin.fieldsets or ()),
        ("Дополнительная информация", {"fields": ("phone", "bio", "avatar")}),
        ("Временные метки", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at"]
