"""Django configuration package."""

from .celery import app

# Export as both 'app' and 'celery_app' for compatibility
celery_app = app

__all__ = ("app", "celery_app")
