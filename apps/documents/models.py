"""Модели документов для OB3 Document Processing Service."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from apps.core.models import SoftDeleteModel, TimeStampedModel, UUIDModel

from .validators import validate_file_extension_safety

if TYPE_CHECKING:
    from .file_types import FileCategory, FileCategoryInfo


class Document(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Модель загруженных документов."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает проверки"  # type: ignore[misc]
        APPROVED = "approved", "Подтверждён"  # type: ignore[misc]
        REJECTED = "rejected", "Отклонён"  # type: ignore[misc]

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF документ"  # type: ignore[misc]
        DOCX = "docx", "Word документ"  # type: ignore[misc]
        TXT = "txt", "Текстовый файл"  # type: ignore[misc]
        IMAGE = "image", "Изображение"  # type: ignore[misc]

    owner = models.ForeignKey(  # type: ignore[var-annotated]
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Владелец",
    )
    file = models.FileField(
        upload_to="documents/%Y/%m/%d/",
        validators=[validate_file_extension_safety],
        verbose_name="Файл",
    )
    file_type = models.CharField(  # type: ignore[var-annotated]
        max_length=10,
        choices=FileType.choices,
        db_index=True,
        verbose_name="Тип файла",
    )
    file_size = models.PositiveIntegerField(  # type: ignore[var-annotated]
        help_text="Размер в байтах",
        verbose_name="Размер файла",
    )
    status = models.CharField(  # type: ignore[var-annotated]
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус",
    )

    original_filename = models.CharField(  # type: ignore[var-annotated]
        max_length=255, verbose_name="Исходное имя файла"
    )
    rejection_reason = models.TextField(  # type: ignore[var-annotated]
        blank=True,
        verbose_name="Причина отклонения",
        help_text="Заполняется при отклонении документа",
    )
    reviewed_at = models.DateTimeField(  # type: ignore[var-annotated]
        null=True,
        blank=True,
        verbose_name="Дата проверки",
    )

    class Meta:  # type: ignore[override]
        db_table = "documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["file_type", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self) -> str:
        status_display: str = self.get_status_display()  # type: ignore[attr-defined]
        return f"{self.original_filename} ({status_display})"

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        """Сохранение документа с проверкой безопасности расширения."""
        from django.core.exceptions import ValidationError

        from .file_types import get_file_extension, is_file_dangerous

        filenames_to_check = []
        if self.original_filename:
            filenames_to_check.append(self.original_filename)
        if self.file and self.file.name:
            filenames_to_check.append(self.file.name)

        for filename in filenames_to_check:
            if is_file_dangerous(filename):
                ext = get_file_extension(filename)
                raise ValidationError(
                    f"Загрузка файлов с расширением '{ext}' запрещена "
                    f"из соображений безопасности."
                )

        if update_fields is None and self._state.adding:
            self.full_clean()

        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @property
    def file_extension(self) -> str:
        """Получить расширение файла."""
        return os.path.splitext(self.original_filename)[1].lower()

    @property
    def is_reviewed(self) -> bool:
        """Проверить, был ли документ рассмотрен."""
        return self.status in [self.Status.APPROVED, self.Status.REJECTED]

    def get_file_category(self) -> FileCategory:
        """Получить категорию файла по расширению."""
        from .file_types import get_file_category

        return get_file_category(self.original_filename)

    def get_file_category_info(self) -> FileCategoryInfo:
        """Получить полную информацию о категории файла."""
        from .file_types import get_file_category_info

        return get_file_category_info(self.original_filename)

    @property
    def is_file_dangerous(self) -> bool:
        """Проверить, является ли файл опасным."""
        from .file_types import FileCategory

        return self.get_file_category() == FileCategory.DANGEROUS

    @property
    def is_file_allowed(self) -> bool:
        """Проверить, разрешён ли файл для обработки."""
        return not self.is_file_dangerous
