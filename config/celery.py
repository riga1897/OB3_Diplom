"""Celery configuration for OB3 Document Processing Service."""

import os
from typing import Any

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("ob3_documents")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self: Any) -> str:
    """Debug task for testing Celery."""
    return f"Request: {self.request!r}"


app.conf.beat_schedule = {
    "cleanup-old-documents": {
        "task": "apps.documents.tasks.cleanup_old_documents",
        "schedule": crontab(hour=2, minute=0),  # Every day at 2:00 AM
    },
}
