"""
Категории типов файлов для OB3 Document Processing Service.

Модуль содержит:
- Whitelist разрешённых расширений по категориям
- Blacklist опасных расширений
- Функции для определения категории файла
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final


class FileCategory(str, Enum):
    """Категории файлов."""

    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    DATA = "data"
    EBOOK = "ebook"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FileCategoryInfo:
    """Информация о категории файла."""

    category: FileCategory
    icon: str
    label: str
    description: str
    color: str
    is_blocked: bool = False


CATEGORY_INFO: Final[dict[FileCategory, FileCategoryInfo]] = {
    FileCategory.DOCUMENT: FileCategoryInfo(
        category=FileCategory.DOCUMENT,
        icon="📄",
        label="Документ",
        description="Текстовые документы и офисные файлы",
        color="#0d6efd",
    ),
    FileCategory.IMAGE: FileCategoryInfo(
        category=FileCategory.IMAGE,
        icon="🖼️",
        label="Изображение",
        description="Растровые и векторные изображения",
        color="#198754",
    ),
    FileCategory.AUDIO: FileCategoryInfo(
        category=FileCategory.AUDIO,
        icon="🎵",
        label="Аудио",
        description="Аудиофайлы",
        color="#6f42c1",
    ),
    FileCategory.VIDEO: FileCategoryInfo(
        category=FileCategory.VIDEO,
        icon="🎬",
        label="Видео",
        description="Видеофайлы",
        color="#d63384",
    ),
    FileCategory.ARCHIVE: FileCategoryInfo(
        category=FileCategory.ARCHIVE,
        icon="🗜️",
        label="Архив",
        description="Сжатые архивы (проверяйте содержимое!)",
        color="#fd7e14",
    ),
    FileCategory.DATA: FileCategoryInfo(
        category=FileCategory.DATA,
        icon="📊",
        label="Данные",
        description="Файлы данных и конфигурации",
        color="#20c997",
    ),
    FileCategory.EBOOK: FileCategoryInfo(
        category=FileCategory.EBOOK,
        icon="📖",
        label="Электронная книга",
        description="Электронные книги",
        color="#6610f2",
    ),
    FileCategory.DANGEROUS: FileCategoryInfo(
        category=FileCategory.DANGEROUS,
        icon="🔴",
        label="Заблокировано",
        description="Потенциально опасный файл. Загрузка запрещена.",
        color="#dc3545",
        is_blocked=True,
    ),
    FileCategory.UNKNOWN: FileCategoryInfo(
        category=FileCategory.UNKNOWN,
        icon="❓",
        label="Неизвестный",
        description="Неизвестный тип файла",
        color="#6c757d",
    ),
}


DOCUMENT_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".txt",
        ".rtf",
        ".md",
        ".log",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".pdf",
        ".pages",
        ".numbers",
        ".key",
        ".tex",
        ".latex",
    }
)

IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".tiff",
        ".tif",
        ".ico",
        ".heic",
        ".heif",
        ".raw",
        ".cr2",
        ".nef",
        ".arw",
        ".dng",
        ".svg",
        ".psd",
        ".ai",
        ".xcf",
        ".eps",
    }
)

AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".wma",
        ".m4a",
        ".aiff",
        ".opus",
        ".alac",
        ".ape",
        ".mid",
        ".midi",
    }
)

VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".mkv",
        ".webm",
        ".flv",
        ".mpeg",
        ".mpg",
        ".m4v",
        ".3gp",
        ".ts",
        ".mts",
        ".vob",
    }
)

ARCHIVE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tgz",
        ".tbz2",
        ".lzma",
        ".cab",
    }
)

DATA_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".csv",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".html",
        ".htm",
        ".xhtml",
        ".ini",
        ".cfg",
        ".conf",
        ".toml",
        ".sql",
        ".sqlite",
        ".db",
    }
)

EBOOK_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".epub",
        ".mobi",
        ".azw",
        ".azw3",
        ".fb2",
        ".djvu",
        ".cbr",
        ".cbz",
    }
)

DANGEROUS_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".exe",
        ".com",
        ".bat",
        ".cmd",
        ".scr",
        ".pif",
        ".msi",
        ".msp",
        ".mst",
        ".app",
        ".apk",
        ".deb",
        ".rpm",
        ".pkg",
        ".vbs",
        ".vbe",
        ".js",
        ".jse",
        ".ws",
        ".wsf",
        ".wsh",
        ".ps1",
        ".psm1",
        ".psd1",
        ".sh",
        ".bash",
        ".zsh",
        ".csh",
        ".docm",
        ".xlsm",
        ".pptm",
        ".dotm",
        ".xltm",
        ".potm",
        ".xlam",
        ".ppam",
        ".sldm",
        ".dll",
        ".sys",
        ".drv",
        ".ocx",
        ".cpl",
        ".scf",
        ".reg",
        ".lnk",
        ".url",
        ".hta",
        ".chm",
        ".hlp",
        ".iso",
        ".img",
        ".dmg",
        ".vhd",
        ".vhdx",
        ".vmdk",
        ".ova",
        ".ovf",
        ".jar",
        ".jnlp",
        ".class",
        ".war",
        ".ear",
        ".inf",
        ".gadget",
        ".msc",
        ".application",
        ".appref-ms",
    }
)


def get_file_extension(filename: str) -> str:
    """
    Получить расширение файла в нижнем регистре.

    Args:
        filename: Имя файла

    Returns:
        Расширение файла с точкой (например, '.pdf')
    """
    import os

    return os.path.splitext(filename)[1].lower()


def get_file_category(filename: str) -> FileCategory:
    """
    Определить категорию файла по расширению.

    Args:
        filename: Имя файла или путь к файлу

    Returns:
        FileCategory: Категория файла
    """
    ext = get_file_extension(filename)

    if not ext:
        return FileCategory.UNKNOWN

    if ext in DANGEROUS_EXTENSIONS:
        return FileCategory.DANGEROUS

    if ext in DOCUMENT_EXTENSIONS:
        return FileCategory.DOCUMENT

    if ext in IMAGE_EXTENSIONS:
        return FileCategory.IMAGE

    if ext in AUDIO_EXTENSIONS:
        return FileCategory.AUDIO

    if ext in VIDEO_EXTENSIONS:
        return FileCategory.VIDEO

    if ext in ARCHIVE_EXTENSIONS:
        return FileCategory.ARCHIVE

    if ext in DATA_EXTENSIONS:
        return FileCategory.DATA

    if ext in EBOOK_EXTENSIONS:
        return FileCategory.EBOOK

    return FileCategory.UNKNOWN


def get_file_category_info(filename: str) -> FileCategoryInfo:
    """
    Получить полную информацию о категории файла.

    Args:
        filename: Имя файла или путь к файлу

    Returns:
        FileCategoryInfo: Информация о категории
    """
    category = get_file_category(filename)
    return CATEGORY_INFO[category]


def is_file_allowed(filename: str) -> bool:
    """
    Проверить, разрешён ли файл для загрузки.

    Args:
        filename: Имя файла

    Returns:
        True, если файл разрешён
    """
    category = get_file_category(filename)
    return category != FileCategory.DANGEROUS


def is_file_dangerous(filename: str) -> bool:
    """
    Проверить, является ли файл опасным.

    Args:
        filename: Имя файла

    Returns:
        True, если файл опасен
    """
    return get_file_category(filename) == FileCategory.DANGEROUS


ALLOWED_EXTENSIONS: Final[frozenset[str]] = (
    DOCUMENT_EXTENSIONS
    | IMAGE_EXTENSIONS
    | AUDIO_EXTENSIONS
    | VIDEO_EXTENSIONS
    | ARCHIVE_EXTENSIONS
    | DATA_EXTENSIONS
    | EBOOK_EXTENSIONS
)


def get_allowed_extensions_list() -> list[str]:
    """
    Получить список разрешённых расширений без точки.

    Returns:
        Список расширений (например, ['pdf', 'docx', 'jpg'])
    """
    return sorted([ext.lstrip(".") for ext in ALLOWED_EXTENSIONS])
