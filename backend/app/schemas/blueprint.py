"""
Response shape for viewing a project's blueprint / analysis results.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.blueprint import BlueprintStatus


class BlueprintOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: BlueprintStatus

    source_video_s3_key: Optional[str] = None
    source_duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None

    scene_cuts: Optional[dict] = None
    beat_map: Optional[dict] = None
    transitions: Optional[dict] = None
    camera_movements: Optional[dict] = None
    color_grading_profile: Optional[dict] = None
    audio_stem_s3_keys: Optional[dict] = None
    transcript: Optional[dict] = None
    text_overlays: Optional[dict] = None
    edit_blueprint: Optional[dict] = None

    created_at: datetime

    model_config = {"from_attributes": True}
