"""Tests for file type categorization system."""

import pytest

from apps.documents.file_types import (
    ALLOWED_EXTENSIONS,
    ARCHIVE_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DANGEROUS_EXTENSIONS,
    DATA_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    EBOOK_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    FileCategory,
    get_allowed_extensions_list,
    get_file_category,
    get_file_category_info,
    get_file_extension,
    is_file_allowed,
    is_file_dangerous,
)


@pytest.mark.unit
class TestGetFileExtension:
    """Tests for get_file_extension function."""

    def test_simple_extension(self) -> None:
        """Test extraction of simple file extension."""
        assert get_file_extension("document.pdf") == ".pdf"

    def test_uppercase_extension(self) -> None:
        """Test extraction converts to lowercase."""
        assert get_file_extension("IMAGE.PNG") == ".png"

    def test_multiple_dots(self) -> None:
        """Test extraction with multiple dots."""
        assert get_file_extension("archive.tar.gz") == ".gz"

    def test_no_extension(self) -> None:
        """Test file without extension."""
        assert get_file_extension("README") == ""

    def test_hidden_file(self) -> None:
        """Test hidden file without extension."""
        assert get_file_extension(".gitignore") == ""

    def test_path_with_extension(self) -> None:
        """Test full path with extension."""
        assert get_file_extension("/path/to/file.docx") == ".docx"


@pytest.mark.unit
class TestGetFileCategory:
    """Tests for get_file_category function."""

    def test_document_category(self) -> None:
        """Test document files return DOCUMENT category."""
        assert get_file_category("report.pdf") == FileCategory.DOCUMENT
        assert get_file_category("document.docx") == FileCategory.DOCUMENT
        assert get_file_category("notes.txt") == FileCategory.DOCUMENT

    def test_image_category(self) -> None:
        """Test image files return IMAGE category."""
        assert get_file_category("photo.jpg") == FileCategory.IMAGE
        assert get_file_category("logo.png") == FileCategory.IMAGE
        assert get_file_category("icon.svg") == FileCategory.IMAGE

    def test_audio_category(self) -> None:
        """Test audio files return AUDIO category."""
        assert get_file_category("song.mp3") == FileCategory.AUDIO
        assert get_file_category("podcast.wav") == FileCategory.AUDIO
        assert get_file_category("music.flac") == FileCategory.AUDIO

    def test_video_category(self) -> None:
        """Test video files return VIDEO category."""
        assert get_file_category("movie.mp4") == FileCategory.VIDEO
        assert get_file_category("clip.avi") == FileCategory.VIDEO
        assert get_file_category("video.mkv") == FileCategory.VIDEO

    def test_archive_category(self) -> None:
        """Test archive files return ARCHIVE category."""
        assert get_file_category("backup.zip") == FileCategory.ARCHIVE
        assert get_file_category("files.rar") == FileCategory.ARCHIVE
        assert get_file_category("package.tar") == FileCategory.ARCHIVE

    def test_data_category(self) -> None:
        """Test data files return DATA category."""
        assert get_file_category("config.json") == FileCategory.DATA
        assert get_file_category("data.csv") == FileCategory.DATA
        assert get_file_category("settings.xml") == FileCategory.DATA

    def test_ebook_category(self) -> None:
        """Test ebook files return EBOOK category."""
        assert get_file_category("book.epub") == FileCategory.EBOOK
        assert get_file_category("manual.mobi") == FileCategory.EBOOK
        assert get_file_category("document.fb2") == FileCategory.EBOOK

    def test_dangerous_category(self) -> None:
        """Test dangerous files return DANGEROUS category."""
        assert get_file_category("virus.exe") == FileCategory.DANGEROUS
        assert get_file_category("script.bat") == FileCategory.DANGEROUS
        assert get_file_category("malware.dll") == FileCategory.DANGEROUS

    def test_unknown_category(self) -> None:
        """Test unknown extensions return UNKNOWN category."""
        assert get_file_category("file.xyz123") == FileCategory.UNKNOWN
        assert get_file_category("data.unknownext") == FileCategory.UNKNOWN

    def test_no_extension_returns_unknown(self) -> None:
        """Test file without extension returns UNKNOWN category."""
        assert get_file_category("README") == FileCategory.UNKNOWN
        assert get_file_category("Makefile") == FileCategory.UNKNOWN


@pytest.mark.unit
class TestGetFileCategoryInfo:
    """Tests for get_file_category_info function."""

    def test_returns_category_info(self) -> None:
        """Test function returns FileCategoryInfo object."""
        info = get_file_category_info("document.pdf")

        assert info.category == FileCategory.DOCUMENT
        assert info.label == "Документ"
        assert info.icon == "📄"
        assert info.is_blocked is False

    def test_dangerous_file_blocked(self) -> None:
        """Test dangerous files have is_blocked=True."""
        info = get_file_category_info("malware.exe")

        assert info.category == FileCategory.DANGEROUS
        assert info.is_blocked is True


@pytest.mark.unit
class TestIsFileAllowed:
    """Tests for is_file_allowed function."""

    def test_safe_file_allowed(self) -> None:
        """Test safe files are allowed."""
        assert is_file_allowed("document.pdf") is True
        assert is_file_allowed("image.jpg") is True
        assert is_file_allowed("data.json") is True

    def test_dangerous_file_not_allowed(self) -> None:
        """Test dangerous files are not allowed."""
        assert is_file_allowed("virus.exe") is False
        assert is_file_allowed("script.bat") is False


@pytest.mark.unit
class TestIsFileDangerous:
    """Tests for is_file_dangerous function."""

    def test_safe_file_not_dangerous(self) -> None:
        """Test safe files are not dangerous."""
        assert is_file_dangerous("document.pdf") is False
        assert is_file_dangerous("image.png") is False

    def test_dangerous_file_is_dangerous(self) -> None:
        """Test dangerous files are detected."""
        assert is_file_dangerous("malware.exe") is True
        assert is_file_dangerous("hack.dll") is True


@pytest.mark.unit
class TestGetAllowedExtensionsList:
    """Tests for get_allowed_extensions_list function."""

    def test_returns_sorted_list(self) -> None:
        """Test function returns sorted list."""
        extensions = get_allowed_extensions_list()

        assert isinstance(extensions, list)
        assert extensions == sorted(extensions)

    def test_no_dots_in_extensions(self) -> None:
        """Test extensions don't have leading dots."""
        extensions = get_allowed_extensions_list()

        for ext in extensions:
            assert not ext.startswith(".")

    def test_common_extensions_included(self) -> None:
        """Test common extensions are in the list."""
        extensions = get_allowed_extensions_list()

        assert "pdf" in extensions
        assert "jpg" in extensions
        assert "mp3" in extensions


@pytest.mark.unit
class TestExtensionSets:
    """Tests for extension set constants."""

    def test_dangerous_extensions_not_in_allowed(self) -> None:
        """Test dangerous extensions are not in allowed set."""
        for ext in DANGEROUS_EXTENSIONS:
            assert ext not in ALLOWED_EXTENSIONS

    def test_all_categories_in_allowed(self) -> None:
        """Test all safe category extensions are in allowed set."""
        all_safe = (
            DOCUMENT_EXTENSIONS
            | IMAGE_EXTENSIONS
            | AUDIO_EXTENSIONS
            | VIDEO_EXTENSIONS
            | ARCHIVE_EXTENSIONS
            | DATA_EXTENSIONS
            | EBOOK_EXTENSIONS
        )
        assert all_safe == ALLOWED_EXTENSIONS

    def test_extensions_have_dots(self) -> None:
        """Test all extensions start with dots."""
        for ext in DANGEROUS_EXTENSIONS:
            assert ext.startswith(".")
        for ext in DOCUMENT_EXTENSIONS:
            assert ext.startswith(".")
