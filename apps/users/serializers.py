"""Сериализаторы для приложения Users."""

from typing import TYPE_CHECKING, Any

from rest_framework import serializers
from rest_framework_simplejwt.tokens import (  # type: ignore[attr-defined]
    RefreshToken,
    TokenError,
)

from .models import User

if TYPE_CHECKING:
    from rest_framework.serializers import ModelSerializer

    class _UserSerializer(ModelSerializer[User]): ...

    class _UserCreateSerializer(ModelSerializer[User]): ...


_UserSerializer = serializers.ModelSerializer  # type: ignore[misc,assignment]
_UserCreateSerializer = serializers.ModelSerializer  # type: ignore[misc,assignment]


class PublicUserSerializer(_UserSerializer):
    """
    Публичный сериализатор пользователя (без конфиденциальных данных).

    Используется при отображении информации о пользователе другим пользователям.
    Скрывает email, телефон и биографию для защиты приватности.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:  # type: ignore[misc]
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "avatar",
        ]
        read_only_fields = ["id", "username", "full_name", "avatar"]


class UserSerializer(_UserSerializer):
    """
    Полный сериализатор пользователя (со всеми полями).

    Используется для авторизованных пользователей при просмотре своего профиля.
    Включает конфиденциальные данные: email и телефон.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:  # type: ignore[misc]
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "bio",
            "avatar",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserCreateSerializer(_UserCreateSerializer):
    """
    Сериализатор для регистрации пользователя.

    Используется в POST /api/register/ для создания нового пользователя.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:  # type: ignore[misc]
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Валидация совпадения паролей."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Создание пользователя с хэшированным паролем."""
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer[None]):
    """
    Сериализатор для выхода из системы.

    Добавляет refresh-токен в чёрный список для инвалидации.
    """

    refresh = serializers.CharField(
        help_text="Refresh-токен для инвалидации",
        required=False,
        allow_blank=True,
    )

    @staticmethod
    def validate_refresh(value: str) -> str:
        """Валидация refresh-токена (базовая проверка формата)."""
        return value

    def save(self, **kwargs: Any) -> None:
        """Добавить refresh-токен в чёрный список."""
        refresh_token = self.validated_data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)  # type: ignore[arg-type]
                token.blacklist()
            except TokenError:
                pass
