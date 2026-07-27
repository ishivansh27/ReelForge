"""
user_assets table -- the photos/videos a user uploads for a project,
plus the metadata the AI matcher needs (CLIP embedding, face detection,
dimensions) to decide which asset_slot each one belongs in.
"""
import enum
import uuid
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin


class AssetType(str, enum.Enum):
    photo = "photo"
    video = "video"


class UploadStatus(str, enum.Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class UserAsset(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "user_assets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType, name="asset_type"), nullable=False)
    upload_status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="upload_status"), default=UploadStatus.uploading, nullable=False
    )

    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # video only
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # AI matching metadata
    clip_embedding: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    has_face: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    face_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dominant_colors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="assets")
    project: Mapped["Project"] = relationship(back_populates="assets")
    matched_slots: Mapped[List["AssetSlot"]] = relationship(
        back_populates="matched_asset", foreign_keys="AssetSlot.matched_asset_id"
    )

    def __repr__(self) -> str:
        return f"<UserAsset {self.asset_type} {self.s3_key}>"
