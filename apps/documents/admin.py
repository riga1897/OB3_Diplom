"""Конфигурация админки для приложения Documents."""

from typing import Any, cast

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.html import format_html

import structlog

from apps.users.models import User

from .file_types import FileCategory
from .models import Document

logger = structlog.get_logger(__name__)


def get_admin_username(request: HttpRequest) -> str:
    """Получить username текущего администратора."""
    user = cast(User, request.user)
    return user.username


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    Админ-интерфейс для модели Document.

    Только суперюзеры могут подтверждать/отклонять документы.
    Обычные staff-пользователи могут только просматривать.
    """

    list_display = [
        "file_info_display",
        "owner",
        "status_colored",
        "file_size_human",
        "created_at",
    ]
    list_filter = ["status", "file_type", "created_at"]
    search_fields = ["original_filename", "owner__email"]
    readonly_fields = [
        "id",
        "owner",
        "file_preview",
        "created_at",
        "updated_at",
        "reviewed_at",
        "file_size",
        "status",
        "original_filename",
    ]
    ordering = ["-created_at"]
    list_per_page = 25
    date_hierarchy = "created_at"
    actions = [
        "approve_documents",
        "reject_documents",
    ]

    fieldsets = (
        (
            "Информация о файле",
            {"fields": ("file_preview", "original_filename", "file_size")},
        ),
        ("Владелец", {"fields": ("owner",)}),
        (
            "Проверка",
            {
                "fields": (
                    "status",
                    "reviewed_at",
                )
            },
        ),
        (
            "Временные метки",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Файл", ordering="original_filename")
    def file_info_display(self, obj: Document) -> str:
        """Отображение файла с иконкой категории и предупреждением."""
        category_info = obj.get_file_category_info()
        icon = category_info.icon
        label = category_info.label
        color = category_info.color

        if category_info.is_blocked:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>'
                '<br><span style="color: #dc3545; font-size: 11px;">⚠️ {}</span>',
                color,
                icon,
                obj.original_filename,
                category_info.description,
            )

        return format_html(
            '<span>{} {}</span>'
            '<br><span style="color: {}; font-size: 11px;">{}</span>',
            icon,
            obj.original_filename,
            color,
            label,
        )

    @admin.display(description="Статус", ordering="status")
    def status_colored(self, obj: Document) -> str:
        """Отображение статуса с цветовой индикацией."""
        colors = {
            "pending": "#FFA500",
            "approved": "#28A745",
            "rejected": "#DC3545",
        }
        color = colors.get(obj.status, "#6C757D")
        status_display: str = obj.get_status_display()  # type: ignore[attr-defined]
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_display,
        )

    @admin.display(description="Размер")
    def file_size_human(self, obj: Document) -> str:
        """Отображение размера файла в человекочитаемом формате."""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"

    @admin.display(description="Предпросмотр")
    def file_preview(self, obj: Document) -> str:
        """Предпросмотр документа: миниатюра для изображений, ссылка для остальных."""
        if not obj.file:
            return "Файл отсутствует"

        if obj.is_file_dangerous:
            category_info = obj.get_file_category_info()
            return format_html(
                '<div style="padding: 16px; background: #f8d7da; border: 1px solid #f5c6cb; '
                'border-radius: 4px; color: #721c24;">'
                '<strong>{} {}</strong><br>'
                '<span style="font-size: 12px;">{}</span><br><br>'
                '<span style="font-size: 11px; color: #856404;">Предпросмотр и скачивание заблокированы.</span>'
                "</div>",
                category_info.icon,
                category_info.label,
                category_info.description,
            )

        file_url = obj.file.url
        category_info = obj.get_file_category_info()

        if obj.get_file_category() == FileCategory.IMAGE:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;" />'
                "</a>",
                file_url,
                file_url,
            )
        elif obj.file_type == Document.FileType.PDF:
            return format_html(
                '<a href="{}" target="_blank" style="display: inline-block; padding: 8px 16px; '
                'background: #dc3545; color: white; text-decoration: none; border-radius: 4px;">'
                "📄 Открыть PDF</a>",
                file_url,
            )
        elif obj.file_type == Document.FileType.DOCX:
            return format_html(
                '<a href="{}" target="_blank" style="display: inline-block; padding: 8px 16px; '
                'background: #0d6efd; color: white; text-decoration: none; border-radius: 4px;">'
                "📝 Скачать DOCX</a>",
                file_url,
            )
        else:
            return format_html(
                '<a href="{}" target="_blank" style="display: inline-block; padding: 8px 16px; '
                'background: {}; color: white; text-decoration: none; border-radius: 4px;">'
                "{} Скачать файл</a>",
                file_url,
                category_info.color,
                category_info.icon,
            )

    @admin.action(description="✅ Подтвердить выбранные документы")
    def approve_documents(
        self, request: HttpRequest, queryset: QuerySet[Document]
    ) -> None:
        """Подтверждение документов с уведомлением пользователей."""
        from .tasks import send_user_notification_task

        total_selected = queryset.count()
        pending_docs = queryset.filter(status=Document.Status.PENDING)
        documents_to_approve = list(pending_docs.values_list("id", flat=True))
        skipped = total_selected - len(documents_to_approve)

        count = pending_docs.update(
            status=Document.Status.APPROVED,
            reviewed_at=timezone.now(),
            rejection_reason="",
        )

        for doc_id in documents_to_approve:
            send_user_notification_task.delay(str(doc_id), "approved")
            logger.info(
                "document_approved",
                document_id=str(doc_id),
                admin_user=get_admin_username(request),
                old_status="pending",
                new_status="approved",
            )

        if skipped > 0:
            self.message_user(
                request,
                f"Подтверждено: {count}. Пропущено (уже обработаны): {skipped}.",
                messages.WARNING,
            )
        elif count > 0:
            self.message_user(
                request,
                f"Подтверждено документов: {count}. Уведомления отправлены.",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Нет документов для подтверждения.",
                messages.INFO,
            )

    @admin.action(description="❌ Отклонить выбранные документы")
    def reject_documents(
        self, request: HttpRequest, queryset: QuerySet[Document]
    ) -> None:
        """Отклонение документов с уведомлением пользователей."""
        from .tasks import send_user_notification_task

        total_selected = queryset.count()
        pending_docs = queryset.filter(status=Document.Status.PENDING)
        documents_to_reject = list(pending_docs.values_list("id", flat=True))
        skipped = total_selected - len(documents_to_reject)

        count = pending_docs.update(
            status=Document.Status.REJECTED,
            rejection_reason="Отклонено администратором",
            reviewed_at=timezone.now(),
        )

        for doc_id in documents_to_reject:
            send_user_notification_task.delay(str(doc_id), "rejected")
            logger.info(
                "document_rejected",
                document_id=str(doc_id),
                admin_user=get_admin_username(request),
                old_status="pending",
                new_status="rejected",
                reason="Отклонено администратором",
            )

        if skipped > 0:
            self.message_user(
                request,
                f"Отклонено: {count}. Пропущено (уже обработаны): {skipped}.",
                messages.WARNING,
            )
        elif count > 0:
            self.message_user(
                request,
                f"Отклонено документов: {count}. Уведомления отправлены.",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Нет документов для отклонения.",
                messages.INFO,
            )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Document]:
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related("owner")

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        """Скрыть bulk-действия approve/reject для не-суперюзеров."""
        actions = super().get_actions(request)
        user = cast(User, request.user)
        if not user.is_superuser:
            actions.pop("approve_documents", None)
            actions.pop("reject_documents", None)
        return actions

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Запретить создание документов через админку (только через API)."""
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Document | None = None
    ) -> bool:
        """Запретить удаление документов."""
        return False

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Document | None = None,
    ) -> HttpResponse:
        """Скрыть стандартные кнопки сохранения."""
        context["submit_row"] = False
        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def response_change(self, request: HttpRequest, obj: Document) -> Any:
        """Обработка кастомных действий (approve/reject). Только для суперюзеров."""
        from django.http import HttpResponseRedirect

        user = cast(User, request.user)
        if not user.is_superuser:
            return super().response_change(request, obj)

        if "_approve" in request.POST:
            from .tasks import send_user_notification_task

            obj.status = Document.Status.APPROVED
            obj.reviewed_at = timezone.now()
            obj.rejection_reason = ""
            obj.save(update_fields=["status", "reviewed_at", "rejection_reason"])

            send_user_notification_task.delay(str(obj.id), "approved")
            logger.info(
                "document_approved",
                document_id=str(obj.id),
                admin_user=get_admin_username(request),
                old_status="pending",
                new_status="approved",
            )

            self.message_user(
                request,
                f"Документ '{obj.original_filename}' подтвержден. Уведомление отправлено.",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(request.path)

        elif "_reject" in request.POST:
            from .tasks import send_user_notification_task

            obj.status = Document.Status.REJECTED
            obj.rejection_reason = "Отклонено администратором"
            obj.reviewed_at = timezone.now()
            obj.save(update_fields=["status", "rejection_reason", "reviewed_at"])

            send_user_notification_task.delay(str(obj.id), "rejected")
            logger.info(
                "document_rejected",
                document_id=str(obj.id),
                admin_user=get_admin_username(request),
                old_status="pending",
                new_status="rejected",
                reason="Отклонено администратором",
            )

            self.message_user(
                request,
                f"Документ '{obj.original_filename}' отклонен. Уведомление отправлено.",
                messages.WARNING,
            )
            return HttpResponseRedirect(request.path)

        return super().response_change(request, obj)
