"""Конфигурация приложения документов."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Конфигурация приложения документов."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "Документы"
