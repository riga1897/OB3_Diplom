"""Базовые абстрактные модели для OB3 Document Processing Service."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Абстрактная модель с UUID в качестве первичного ключа."""

    id = models.UUIDField(  # type: ignore[var-annotated]
        primary_key=True, default=uuid.uuid4, editable=False
    )

    class Meta:  # type: ignore[override]
        abstract = True


class TimeStampedModel(models.Model):
    """Абстрактная модель с полями created_at и updated_at."""

    created_at = models.DateTimeField(  # type: ignore[var-annotated]
        auto_now_add=True, db_index=True, verbose_name="Создано"
    )
    updated_at = models.DateTimeField(  # type: ignore[var-annotated]
        auto_now=True, verbose_name="Обновлено"
    )

    class Meta:  # type: ignore[override]
        abstract = True


class SoftDeleteModel(models.Model):
    """Абстрактная модель с функциональностью мягкого удаления."""

    is_deleted = models.BooleanField(  # type: ignore[var-annotated]
        default=False, db_index=True, verbose_name="Удалён"
    )
    deleted_at = models.DateTimeField(  # type: ignore[var-annotated]
        null=True, blank=True, verbose_name="Дата удаления"
    )

    class Meta:  # type: ignore[override]
        abstract = True

    def soft_delete(self) -> None:
        """Мягкое удаление объекта."""
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self) -> None:
        """Восстановление мягко удалённого объекта."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])
