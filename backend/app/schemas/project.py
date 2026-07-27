"""
Request/response shapes for the projects endpoints.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from app.models.project import ProjectStatus, SourcePlatform


class ProjectCreate(BaseModel):
    source_url: HttpUrl


class ProjectOut(BaseModel):
    id: uuid.UUID
    title: str
    source_url: str
    source_platform: SourcePlatform
    status: ProjectStatus
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
