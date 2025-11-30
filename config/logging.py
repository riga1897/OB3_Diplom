"""Конфигурация structlog для OB3 Document Processing Service.

Настраивает структурированное логирование:
- Development: цветной консольный вывод для удобства чтения
- Production: JSON-формат для парсинга и анализа

Использование:
    import structlog
    logger = structlog.get_logger(__name__)

    logger.info("document_uploaded", document_id=doc.id, user_id=user.id)
    logger.warning("validation_failed", errors=errors)
    logger.error("processing_error", document_id=doc.id, error=str(e))
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def configure_structlog(debug: bool = True, log_level: str = "INFO") -> None:
    """Настроить structlog для приложения.

    Args:
        debug: True для development (цветной вывод), False для production (JSON)
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=False)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if debug:
        # Development: цветной консольный вывод
        processors: list[Processor] = [
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        renderer: Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Production: JSON-формат
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Настраиваем форматтер для stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Настраиваем handler для вывода в stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Получаем root logger и настраиваем его
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Настраиваем логгеры приложения
    for logger_name in ["apps", "django", "celery"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = False


def get_logger(name: str | None = None) -> Any:
    """Получить structlog logger.

    Args:
        name: Имя логгера (обычно __name__)

    Returns:
        structlog.BoundLogger: Настроенный логгер

    Пример:
        logger = get_logger(__name__)
        logger.info("event_name", key="value")
    """
    return structlog.get_logger(name)
