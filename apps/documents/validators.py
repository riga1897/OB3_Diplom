"""Валидаторы для приложения Documents."""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

import filetype

from .file_types import DANGEROUS_EXTENSIONS, get_file_extension


def validate_file_type(file: UploadedFile) -> None:
    """Валидация типа файла по magic numbers (определение MIME-типа).

    Использует библиотеку filetype для анализа содержимого файла
    вместо проверки расширения, которое можно подделать.

    Разрешённые типы:
    - application/pdf (PDF)
    - application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)
    - text/plain (TXT)
    - image/jpeg (JPEG)
    - image/png (PNG)

    Args:
        file: Экземпляр Django UploadedFile

    Raises:
        ValidationError: Если тип файла не разрешён
    """
    allowed_mime_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "image/jpeg",
        "image/png",
    ]

    file.seek(0)
    file_head = file.read(2048)
    file.seek(0)

    kind = filetype.guess(file_head)

    if kind is None:
        if _is_text_content(file_head):
            mime_type = "text/plain"
        else:
            raise ValidationError(
                _("Не удалось определить тип файла."),
                code="unknown_file_type",
            )
    else:
        mime_type = kind.mime

    if mime_type not in allowed_mime_types:
        raise ValidationError(
            _(
                f"Неподдерживаемый тип файла: {mime_type}. "
                f"Разрешённые типы: PDF, DOCX, TXT, JPEG, PNG."
            ),
            code="invalid_file_type",
        )


def _is_text_content(data: bytes) -> bool:
    """Проверка, является ли содержимое текстовым.

    Проверяет наличие null-bytes и контрольных символов,
    которые обычно присутствуют в бинарных файлах.

    Args:
        data: Байты для проверки

    Returns:
        True если данные похожи на текст, иначе False
    """
    if not data:
        return False

    if b"\x00" in data[:512]:
        return False

    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        text_chars = set(range(32, 127)) | {9, 10, 13}
        return sum(1 for b in data[:512] if b in text_chars) / min(len(data), 512) > 0.7


def validate_file_size(file: UploadedFile) -> None:
    """Валидация размера файла.

    Args:
        file: Экземпляр Django UploadedFile

    Raises:
        ValidationError: Если размер файла превышает лимит
    """
    from django.conf import settings

    max_size: int = getattr(settings, "MAX_UPLOAD_SIZE", 10485760)  # 10MB default

    if file.size is not None and file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _(f"Размер файла превышает максимально допустимый: {max_size_mb:.1f}MB."),
            code="file_too_large",
        )


def validate_file_extension_safety(file: UploadedFile) -> None:
    """Валидация расширения файла на безопасность.

    Проверяет, что расширение файла не входит в список опасных.
    Опасные расширения включают исполняемые файлы, скрипты,
    макросы Office и другие потенциально вредоносные типы.

    Args:
        file: Экземпляр Django UploadedFile

    Raises:
        ValidationError: Если расширение файла опасно
    """
    filename = file.name if file.name else ""
    ext = get_file_extension(filename)

    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(
            _(
                f"Загрузка файлов с расширением '{ext}' запрещена "
                f"из соображений безопасности."
            ),
            code="dangerous_file_extension",
        )
