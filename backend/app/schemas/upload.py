"""
Request/response shapes for the direct-to-S3 upload endpoints.
"""
import uuid

from pydantic import BaseModel, Field

from app.models.user_asset import AssetType, UploadStatus


class PresignUploadRequest(BaseModel):
    project_id: uuid.UUID
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    asset_type: AssetType


class PresignUploadResponse(BaseModel):
    asset_id: uuid.UUID
    upload_url: str
    s3_key: str
    expires_in: int


class ConfirmUploadResponse(BaseModel):
    asset_id: uuid.UUID
    upload_status: UploadStatus
    file_size_bytes: int | None = None
