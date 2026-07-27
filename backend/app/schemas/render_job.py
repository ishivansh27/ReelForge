"""
Response shape for render job status/progress.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.render_job import RenderJobStatus


class RenderJobOut(BaseModel):
    id: uuid.UUID
    status: RenderJobStatus
    progress_percent: int
    output_s3_key: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
