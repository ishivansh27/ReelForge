"""
Response shape for listing a project's uploaded assets.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.user_asset import AssetType, UploadStatus


class UserAssetOut(BaseModel):
    id: uuid.UUID
    asset_type: AssetType
    upload_status: UploadStatus
    s3_key: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    has_face: Optional[bool] = None
    face_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
