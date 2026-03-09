"""Сериализаторы для приложения Documents."""

from typing import Any

from django.core.files.uploadedfile import UploadedFile

from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Document
from .validators import (
    validate_file_extension_safety,
    validate_file_size,
    validate_file_type,
)


class DocumentListSerializer(serializers.ModelSerializer[Document]):
    """
    Сериализатор для списка документов.

    Используется в GET /api/documents/ для отображения краткой информации.
    """

    owner = UserSerializer(read_only=True)
    file_extension = serializers.ReadOnlyField()
    is_reviewed = serializers.ReadOnlyField()

    class Meta:  # type: ignore[override]
        model = Document
        fields = [
            "id",
            "owner",
            "original_filename",
            "file_type",
            "file_size",
            "file_extension",
            "status",
            "is_reviewed",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = ["id", "created_at"]


class DocumentDetailSerializer(serializers.ModelSerializer[Document]):
    """
    Сериализатор для детального просмотра документа.

    Используется в GET /api/documents/{id}/ для отображения полной информации.
    """

    owner = UserSerializer(read_only=True)
    file_extension = serializers.ReadOnlyField()
    is_reviewed = serializers.ReadOnlyField()

    class Meta:  # type: ignore[override]
        model = Document
        fields = [
            "id",
            "owner",
            "file",
            "original_filename",
            "file_type",
            "file_size",
            "file_extension",
            "status",
            "is_reviewed",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "file_type",
            "file_size",
            "status",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        ]


class DocumentCreateSerializer(serializers.ModelSerializer[Document]):
    """
    Сериализатор для загрузки документа.

    Используется в POST /api/documents/ для создания нового документа.
    Автоматически определяет тип файла и отправляет уведомление администратору.
    """

    class Meta:  # type: ignore[override]
        model = Document
        fields = ["file"]

    @staticmethod
    def validate_file(value: UploadedFile) -> UploadedFile:
        """Валидация загружаемого файла (безопасность, тип и размер)."""
        validate_file_extension_safety(value)
        validate_file_type(value)
        validate_file_size(value)
        return value

    def create(self, validated_data: dict[str, Any]) -> Document:
        """Создание документа с метаданными и отправка уведомления администратору."""
        from .tasks import send_admin_notification_task

        file = validated_data["file"]
        original_filename = file.name

        extension = original_filename.split(".")[-1].lower()
        file_type_mapping = {
            "pdf": Document.FileType.PDF,
            "docx": Document.FileType.DOCX,
            "txt": Document.FileType.TXT,
            "jpg": Document.FileType.IMAGE,
            "jpeg": Document.FileType.IMAGE,
            "png": Document.FileType.IMAGE,
        }
        file_type = file_type_mapping.get(extension, Document.FileType.PDF)

        document = Document(
            owner=self.context["request"].user,
            file=file,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file.size,
        )
        document.full_clean()
        document.save()

        send_admin_notification_task.delay(str(document.id))

        return document
