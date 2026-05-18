"""
Celery application — async task queue for long-running AI operations.
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "qagent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.run_requirement_ingestion": {"queue": "ai"},
        "app.workers.tasks.run_story_generation": {"queue": "ai"},
        "app.workers.tasks.run_test_case_generation": {"queue": "ai"},
        "app.workers.tasks.run_test_execution": {"queue": "execution"},
        "app.workers.tasks.run_automation_generation": {"queue": "ai"},
    },
)
