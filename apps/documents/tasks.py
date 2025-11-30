"""Celery-задачи для обработки документов."""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def send_admin_notification_task(self: Any, document_id: str) -> dict[str, Any]:
    """
    Отправка уведомления администратору о новом документе.

    Args:
        document_id: UUID загруженного документа

    Returns:
        dict: Результат отправки
        :param document_id:
        :param self:
    """
    from apps.users.models import User

    from .models import Document

    try:
        document = Document.objects.select_related("owner").get(id=document_id)

        admin_emails = list(
            User.objects.filter(is_staff=True, is_active=True).values_list(
                "email", flat=True
            )
        )

        if not admin_emails:
            logger.warning("no_admin_emails_found", document_id=document_id)
            return {"status": "skipped", "reason": "no_admins"}

        subject = f"Новый документ загружен: {document.original_filename}"
        file_type_display: str = document.get_file_type_display()  # type: ignore[attr-defined]
        message = (
            f"Пользователь {document.owner.email} загрузил новый документ.\n\n"
            f"Файл: {document.original_filename}\n"
            f"Тип: {file_type_display}\n"
            f"Размер: {document.file_size} байт\n"
            f"Дата: {document.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Перейдите в Django Admin для просмотра и подтверждения документа."
        )

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ob3.example.com")

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=admin_emails,
                fail_silently=False,
            )
        except Exception as mail_exc:
            logger.error(
                "smtp_error_admin_notification",
                document_id=document_id,
                error=str(mail_exc),
            )
            raise self.retry(
                exc=mail_exc, countdown=60 * (2**self.request.retries)
            ) from mail_exc

        logger.info(
            "admin_notification_sent",
            document_id=document_id,
            recipients_count=len(admin_emails),
            filename=document.original_filename,
            owner_email=document.owner.email,
        )

        return {
            "status": "sent",
            "document_id": str(document_id),
            "recipients_count": len(admin_emails),
        }

    except Document.DoesNotExist:
        logger.error("document_not_found_admin_notification", document_id=document_id)
        return {"status": "error", "reason": "document_not_found"}


@shared_task(bind=True, max_retries=3)
def send_user_notification_task(
    self: Any, document_id: str, action: str
) -> dict[str, Any]:
    """
    Отправка уведомления пользователю о статусе документа.

    Args:
        document_id: UUID документа
        action: Действие ('approved' или 'rejected')

    Returns:
        dict: Результат отправки
        :param action:
        :param document_id:
        :param self:
    """
    from .models import Document

    try:
        document = Document.objects.select_related("owner").get(id=document_id)

        if not document.owner.email:
            logger.warning(
                "user_has_no_email",
                document_id=document_id,
                user_id=str(document.owner.id),
            )
            return {"status": "skipped", "reason": "no_user_email"}

        if action == "approved":
            subject = f"Документ подтверждён: {document.original_filename}"
            message = (
                f"Ваш документ был подтверждён администратором.\n\n"
                f"Файл: {document.original_filename}\n"
                f"Дата загрузки: {document.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"Дата подтверждения: {document.reviewed_at.strftime('%d.%m.%Y %H:%M') if document.reviewed_at else 'N/A'}\n\n"
                f"Спасибо за использование нашего сервиса!"
            )
        elif action == "rejected":
            subject = f"Документ отклонён: {document.original_filename}"
            message = (
                f"К сожалению, ваш документ был отклонён администратором.\n\n"
                f"Файл: {document.original_filename}\n"
                f"Причина: {document.rejection_reason or 'Не указана'}\n"
                f"Дата загрузки: {document.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Вы можете загрузить документ повторно после исправления."
            )
        else:
            logger.error("unknown_action", document_id=document_id, action=action)
            return {"status": "error", "reason": f"unknown_action: {action}"}

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ob3.example.com")

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[document.owner.email],
                fail_silently=False,
            )
        except Exception as mail_exc:
            logger.error(
                "smtp_error_user_notification",
                document_id=document_id,
                action=action,
                error=str(mail_exc),
            )
            raise self.retry(
                exc=mail_exc, countdown=60 * (2**self.request.retries)
            ) from mail_exc

        logger.info(
            "user_notification_sent",
            document_id=document_id,
            action=action,
            recipient=document.owner.email,
            filename=document.original_filename,
        )

        return {
            "status": "sent",
            "document_id": str(document_id),
            "action": action,
            "recipient": document.owner.email,
        }

    except Document.DoesNotExist:
        logger.error("document_not_found_user_notification", document_id=document_id)
        return {"status": "error", "reason": "document_not_found"}


@shared_task
def cleanup_old_documents() -> dict[str, Any]:
    """
    Очистка старых документов (мягко удалённых > 30 дней).

    Returns:
        dict: Статистика очистки
    """
    from .models import Document

    threshold_date = timezone.now() - timedelta(days=30)

    old_documents = Document.objects.filter(
        is_deleted=True, deleted_at__lt=threshold_date
    )

    count = old_documents.count()
    logger.info("cleanup_started", documents_to_delete=count)

    for doc in old_documents:
        try:
            if doc.file:
                doc.file.delete(save=False)
            doc.delete()
            logger.debug("document_deleted", document_id=str(doc.id))
        except Exception as e:
            logger.error("cleanup_error", document_id=str(doc.id), error=str(e))

    logger.info("cleanup_completed", deleted_count=count)

    return {"deleted_count": count, "threshold_date": str(threshold_date)}


@shared_task
def generate_statistics_report() -> dict[str, Any]:
    """
    Генерация статистики по документам.

    Returns:
        dict: Статистика
    """
    from django.db.models import Count, Q, Sum

    from .models import Document

    stats = Document.objects.aggregate(
        total_documents=Count("id"),
        total_size=Sum("file_size"),
        pending=Count("id", filter=Q(status=Document.Status.PENDING)),
        approved=Count("id", filter=Q(status=Document.Status.APPROVED)),
        rejected=Count("id", filter=Q(status=Document.Status.REJECTED)),
    )

    logger.info(
        "statistics_generated",
        total_documents=stats["total_documents"],
        pending=stats["pending"],
        approved=stats["approved"],
        rejected=stats["rejected"],
    )

    return stats
