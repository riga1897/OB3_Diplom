"""Тесты для валидаторов документов."""

from io import BytesIO
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest

from apps.documents.validators import (
    _is_text_content,
    validate_file_extension_safety,
    validate_file_type,
)


@pytest.mark.unit
class TestIsTextContent:
    """Тесты для функции _is_text_content."""

    def test_utf8_text_returns_true(self) -> None:
        """UTF-8 текст должен возвращать True."""
        data = "Привет, мир! Hello, world!".encode("utf-8")
        assert _is_text_content(data) is True

    def test_ascii_text_returns_true(self) -> None:
        """ASCII текст должен возвращать True."""
        data = b"Hello, world! 123"
        assert _is_text_content(data) is True

    def test_latin1_printable_text_returns_true(self) -> None:
        """Печатный Latin-1 текст должен возвращать True."""
        data = b"Hello world! This is printable ASCII text."
        assert _is_text_content(data) is True

    def test_binary_with_null_bytes_returns_false(self) -> None:
        """Бинарные данные с null-bytes должны возвращать False."""
        data = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])
        assert _is_text_content(data) is False

    def test_empty_data_returns_false(self) -> None:
        """Пустые данные должны возвращать False."""
        assert _is_text_content(b"") is False

    def test_non_utf8_mostly_control_chars_returns_false(self) -> None:
        """Non-UTF8 данные с преобладанием контрольных символов возвращают False."""
        control_chars = bytes([0x80, 0x81, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
        data = control_chars * 100
        assert _is_text_content(data) is False


@pytest.mark.unit
class TestValidateFileType:
    """Тесты для функции validate_file_type."""

    def test_unknown_binary_file_raises_error(self, monkeypatch: Any) -> None:
        """Неизвестный бинарный файл должен вызывать ValidationError."""
        import filetype

        monkeypatch.setattr(filetype, "guess", lambda x: None)

        binary_content = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05] * 100)
        test_file = SimpleUploadedFile(
            "unknown.bin",
            binary_content,
            content_type="application/octet-stream",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_file_type(test_file)

        assert exc_info.value.code == "unknown_file_type"

    def test_valid_pdf_passes(self) -> None:
        """Валидный PDF файл должен проходить валидацию."""
        pdf_header = b"%PDF-1.4\n"
        test_file = SimpleUploadedFile(
            "test.pdf",
            pdf_header + b"dummy content",
            content_type="application/pdf",
        )

        validate_file_type(test_file)

    def test_valid_png_passes(self) -> None:
        """Валидный PNG файл должен проходить валидацию."""
        png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        test_file = SimpleUploadedFile(
            "test.png",
            png_header + b"dummy content",
            content_type="image/png",
        )

        validate_file_type(test_file)

    def test_valid_jpeg_passes(self) -> None:
        """Валидный JPEG файл должен проходить валидацию."""
        jpeg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0])
        test_file = SimpleUploadedFile(
            "test.jpg",
            jpeg_header + b"dummy content",
            content_type="image/jpeg",
        )

        validate_file_type(test_file)

    def test_valid_text_passes(self) -> None:
        """Валидный текстовый файл должен проходить валидацию."""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Hello, this is a text file content.",
            content_type="text/plain",
        )

        validate_file_type(test_file)

    def test_invalid_mime_type_raises_error(self, monkeypatch: Any) -> None:
        """Неразрешённый MIME-тип должен вызывать ValidationError."""
        import filetype

        class MockType:
            mime = "application/x-executable"

        monkeypatch.setattr(filetype, "guess", lambda x: MockType())

        test_file = SimpleUploadedFile(
            "malware.exe",
            b"MZ" + b"\x00" * 100,
            content_type="application/x-executable",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_file_type(test_file)

        assert exc_info.value.code == "invalid_file_type"


@pytest.mark.unit
class TestValidateFileExtensionSafety:
    """Тесты для функции validate_file_extension_safety."""

    def test_safe_extension_passes(self) -> None:
        """Безопасное расширение должно проходить валидацию."""
        test_file = SimpleUploadedFile(
            "document.pdf",
            b"Safe content",
            content_type="application/pdf",
        )

        validate_file_extension_safety(test_file)

    def test_dangerous_exe_extension_fails(self) -> None:
        """Расширение .exe должно вызывать ValidationError."""
        test_file = SimpleUploadedFile(
            "malware.exe",
            b"Dangerous content",
            content_type="application/octet-stream",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension_safety(test_file)

        assert "запрещена" in str(exc_info.value)
        assert ".exe" in str(exc_info.value)
        assert exc_info.value.code == "dangerous_file_extension"

    def test_dangerous_bat_extension_fails(self) -> None:
        """Расширение .bat должно вызывать ValidationError."""
        test_file = SimpleUploadedFile(
            "script.bat",
            b"Batch script",
            content_type="text/plain",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension_safety(test_file)

        assert "запрещена" in str(exc_info.value)
        assert ".bat" in str(exc_info.value)

    def test_dangerous_dll_extension_fails(self) -> None:
        """Расширение .dll должно вызывать ValidationError."""
        test_file = SimpleUploadedFile(
            "library.dll",
            b"DLL content",
            content_type="application/octet-stream",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension_safety(test_file)

        assert "запрещена" in str(exc_info.value)

    def test_none_filename_passes(self) -> None:
        """Файл с None именем должен проходить валидацию."""
        from unittest.mock import MagicMock

        test_file = MagicMock()
        test_file.name = None

        validate_file_extension_safety(test_file)
