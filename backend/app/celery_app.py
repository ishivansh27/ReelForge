"""
Celery app instance. Background jobs (video download, analysis,
matching, rendering) get defined as @celery_app.task functions in
later phases and imported here via `include=[...]`.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "reelapp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.render",
        "app.tasks.download",
        "app.tasks.scene_detection",
        "app.tasks.camera_movement",
        "app.tasks.audio_analysis",
        "app.tasks.text_overlay",
        "app.tasks.blueprint_assembly",
        "app.tasks.asset_requirements",
        "app.tasks.asset_matching",
        "app.tasks.gap_fill",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
