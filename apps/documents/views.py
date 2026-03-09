"""Представления (views) для приложения Documents."""

from typing import Any

from django.db.models import Count, QuerySet, Sum

import structlog
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import DocumentFilter
from .models import Document
from .permissions import IsOwner
from .serializers import (
    DocumentCreateSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
)
from .throttles import UploadRateThrottle

logger = structlog.get_logger(__name__)


class DocumentViewSet(viewsets.ModelViewSet[Document]):
    """
    ViewSet для работы с документами.

    Предоставляет CRUD операции для документов пользователя.
    Пользователь видит только свои документы (IsOwner permission).

    **GET /api/documents/** — Список документов пользователя
    **POST /api/documents/** — Загрузка нового документа
    **GET /api/documents/{id}/** — Детали документа
    **DELETE /api/documents/{id}/soft_delete/** — Мягкое удаление
    **POST /api/documents/{id}/restore/** — Восстановление документа
    **GET /api/documents/statistics/** — Статистика по документам
    """

    queryset = Document.objects.select_related("owner")
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DocumentFilter
    search_fields = ["original_filename"]
    ordering_fields = ["created_at", "file_size", "reviewed_at"]
    ordering = ["-created_at"]

    def get_throttles(self) -> list[Any]:
        """Применить throttle для загрузки документов."""
        throttles = super().get_throttles()
        if self.action == "create":
            throttles.append(UploadRateThrottle())
        return throttles

    def get_serializer_class(self) -> type[serializers.Serializer[Any]]:
        """Выбрать сериализатор в зависимости от действия."""
        if self.action == "create":
            return DocumentCreateSerializer
        elif self.action == "list":
            return DocumentListSerializer
        return DocumentDetailSerializer

    def get_queryset(self) -> QuerySet[Document]:
        """Фильтрация: показывать только документы текущего пользователя."""
        queryset = super().get_queryset()
        if (
            not self.request.query_params.get("include_deleted")
            and self.action != "restore"
        ):
            queryset = queryset.filter(is_deleted=False)
        return queryset.filter(owner=self.request.user)

    def perform_create(  # type: ignore[override]
        self, serializer: serializers.Serializer[Document]
    ) -> None:
        """Логирование создания документа."""
        document = serializer.save()
        logger.info(
            "document_uploaded",
            document_id=str(document.id),
            user_id=str(self.request.user.id),
            filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
        )

    @action(detail=True, methods=["delete"])
    def soft_delete(self, request: Request, pk: str | None = None) -> Response:
        """Мягкое удаление документа (без физического удаления из БД)."""
        document = self.get_object()
        document.soft_delete()
        logger.info(
            "document_soft_deleted",
            document_id=str(document.id),
            user_id=str(request.user.id),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request: Request, pk: str | None = None) -> Response:
        """Восстановление мягко удалённого документа."""
        document = self.get_object()
        document.restore()
        logger.info(
            "document_restored",
            document_id=str(document.id),
            user_id=str(request.user.id),
        )
        return Response(
            {"message": "Document restored successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def statistics(self, request: Request) -> Response:
        """Получить агрегированную статистику по документам пользователя."""
        queryset = self.get_queryset()
        include_deleted = request.query_params.get("include_deleted")
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)

        total_stats = queryset.aggregate(
            total_documents=Count("id"),
            total_size=Sum("file_size"),
        )

        by_status = {}
        for status_choice in Document.Status:
            count = queryset.filter(status=status_choice.value).count()
            by_status[status_choice.value] = count

        by_file_type = {}
        for file_type_choice in Document.FileType:
            count = queryset.filter(file_type=file_type_choice.value).count()
            by_file_type[file_type_choice.value] = count

        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        recent_uploads = {
            "last_24h": queryset.filter(
                created_at__gte=now - timedelta(hours=24)
            ).count(),
            "last_7d": queryset.filter(created_at__gte=now - timedelta(days=7)).count(),
            "last_30d": queryset.filter(
                created_at__gte=now - timedelta(days=30)
            ).count(),
        }

        return Response(
            {
                "total_documents": total_stats["total_documents"],
                "total_size_bytes": total_stats["total_size"] or 0,
                "by_status": by_status,
                "by_file_type": by_file_type,
                "recent_uploads": recent_uploads,
            },
            status=status.HTTP_200_OK,
        )
