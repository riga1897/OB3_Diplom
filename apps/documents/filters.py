"""Фильтры django-filter для приложения Documents."""

from typing import TYPE_CHECKING

from django.db import models

from django_filters import rest_framework as filters

from .models import Document

if TYPE_CHECKING:
    from django.db.models import QuerySet


class DocumentFilter(filters.FilterSet):
    """Расширенная фильтрация для модели Document."""

    status = filters.MultipleChoiceFilter(
        choices=Document.Status.choices,
        help_text="Фильтр по одному или нескольким статусам",
    )
    file_type = filters.MultipleChoiceFilter(
        choices=Document.FileType.choices,
        help_text="Фильтр по одному или нескольким типам файлов",
    )

    created_after = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        help_text="Документы, созданные после этой даты",
    )
    created_before = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        help_text="Документы, созданные до этой даты",
    )
    file_size_min = filters.NumberFilter(
        field_name="file_size",
        lookup_expr="gte",
        help_text="Минимальный размер файла в байтах",
    )
    file_size_max = filters.NumberFilter(
        field_name="file_size",
        lookup_expr="lte",
        help_text="Максимальный размер файла в байтах",
    )

    is_deleted = filters.BooleanFilter(
        help_text="Фильтр удалённых документов",
    )
    is_reviewed = filters.BooleanFilter(
        method="filter_is_reviewed",
        help_text="Фильтр проверенных документов",
    )

    search = filters.CharFilter(
        method="filter_search",
        help_text="Поиск по имени файла",
    )

    class Meta:
        model = Document
        fields = [
            "status",
            "file_type",
            "is_deleted",
            "created_after",
            "created_before",
            "file_size_min",
            "file_size_max",
            "is_reviewed",
            "search",
        ]

    def filter_is_reviewed(
        self, queryset: "QuerySet[Document]", name: str, value: bool
    ) -> "QuerySet[Document]":
        """Фильтрация проверенных документов."""
        if value:
            return queryset.filter(
                status__in=[Document.Status.APPROVED, Document.Status.REJECTED]
            )
        return queryset.filter(status=Document.Status.PENDING)

    def filter_search(
        self, queryset: "QuerySet[Document]", name: str, value: str
    ) -> "QuerySet[Document]":
        """Поиск по нескольким полям."""
        return queryset.filter(models.Q(original_filename__icontains=value))
