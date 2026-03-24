from celery import Celery

from app.config import settings

celery_app = Celery(
    "stats_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.analysis", "app.tasks.data_pipeline"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
