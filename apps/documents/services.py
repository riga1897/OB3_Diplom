"""Сервисный слой для бизнес-логики обработки документов."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Сервис для обработки документов."""

    def extract_text(self, document: Any) -> str:
        """
        Извлечь текст из документа в зависимости от типа файла.

        Args:
            document: Экземпляр модели Document

        Returns:
            str: Извлечённый текст
        """
        from .models import Document

        file_path = document.file.path

        try:
            if document.file_type == Document.FileType.PDF:
                return self._extract_text_from_pdf(file_path)
            elif document.file_type == Document.FileType.DOCX:
                return self._extract_text_from_docx(file_path)
            elif document.file_type == Document.FileType.TXT:
                return self._extract_text_from_txt(file_path)
            elif document.file_type == Document.FileType.IMAGE:
                return self._extract_text_from_image(file_path)
            else:
                raise ValueError(f"Неподдерживаемый тип файла: {document.file_type}")

        except Exception as e:
            logger.error(f"Ошибка извлечения текста из {file_path}: {e}")
            raise

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Извлечь текст из PDF файла."""
        import pypdf

        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Извлечь текст из DOCX файла."""
        import docx

        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()

    def _extract_text_from_txt(self, file_path: str) -> str:
        """Извлечь текст из TXT файла."""
        with open(file_path, encoding="utf-8") as file:
            return file.read().strip()

    def _extract_text_from_image(self, file_path: str) -> str:
        """Извлечь текст из изображения с помощью OCR (заглушка)."""
        # TODO: Реализовать OCR с tesseract
        logger.warning("OCR ещё не реализован, возвращаем пустую строку")
        return ""

    def classify_document(self, text: str) -> tuple[str, float]:
        """
        Классифицировать документ на основе извлечённого текста.

        Args:
            text: Извлечённый текст из документа

        Returns:
            Tuple[str, float]: (классификация, оценка_уверенности)
        """
        # Простая классификация по ключевым словам (заглушка)
        # TODO: Реализовать ML-классификацию

        text_lower = text.lower()

        classifications = {
            "invoice": ["invoice", "bill", "payment", "total", "amount"],
            "contract": ["agreement", "contract", "terms", "conditions", "signature"],
            "report": ["report", "summary", "analysis", "conclusion", "findings"],
            "letter": ["dear", "sincerely", "regards", "letter"],
        }

        scores = {}
        for category, keywords in classifications.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score / len(keywords)

        if not scores or max(scores.values()) == 0:
            return "unclassified", 0.0

        classification = max(scores, key=lambda k: scores[k])
        confidence = scores[classification]

        logger.info(f"Классифицирован как: {classification} (уверенность: {confidence:.2f})")

        return classification, confidence
