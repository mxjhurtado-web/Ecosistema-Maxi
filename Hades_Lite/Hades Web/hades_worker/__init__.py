"""
Hades Worker - Celery worker para procesamiento asíncrono.
"""

from .celery_app import celery_app
from .tasks import process_image_task, export_to_drive_task

__all__ = ["celery_app", "process_image_task", "export_to_drive_task"]
