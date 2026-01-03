"""
Celery Application Configuration

Background task processing using Celery with Redis broker
"""

from celery import Celery

from src.core.config import settings

# Create Celery application
celery_app = Celery(
    "eda_platform",
    broker=settings.celery.celery_broker_url,
    backend=settings.celery.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.celery.celery_task_track_started,
    task_time_limit=settings.celery.celery_task_time_limit,
    task_soft_time_limit=settings.celery.celery_task_soft_time_limit,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure Celery Beat for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs-daily": {
        "task": "tasks.cleanup_old_jobs",
        "schedule": 86400.0,  # Run daily (24 hours)
        "args": (7,),  # Keep jobs for 7 days
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.tasks"])
