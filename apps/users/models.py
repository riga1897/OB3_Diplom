"""Модели пользователей для OB3 Document Processing Service."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Расширенная модель пользователя с дополнительными полями."""

    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(  # type: ignore[var-annotated]
        max_length=20, blank=True, verbose_name="Телефон"
    )
    bio = models.TextField(blank=True, verbose_name="О себе")  # type: ignore[var-annotated]
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )

    created_at = models.DateTimeField(  # type: ignore[var-annotated]
        auto_now_add=True, verbose_name="Создан"
    )
    updated_at = models.DateTimeField(  # type: ignore[var-annotated]
        auto_now=True, verbose_name="Обновлён"
    )

    class Meta:  # type: ignore[override]
        db_table = "users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Получить полное имя пользователя."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
