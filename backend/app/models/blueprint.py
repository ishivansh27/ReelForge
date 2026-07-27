"""
blueprints table -- the structured "Edit Blueprint" extracted from the
reference video: cut timings, beat sync, transitions, camera movement,
text overlays, color grading. One blueprint per project.
"""
import enum
import uuid
from typing import List, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin


class BlueprintStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Blueprint(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "blueprints"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one blueprint per project
        index=True,
    )

    status: Mapped[BlueprintStatus] = mapped_column(
        Enum(BlueprintStatus, name="blueprint_status"),
        default=BlueprintStatus.pending,
        nullable=False,
    )

    # Basic video info
    source_video_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Analysis results (each is a JSON blob produced by a different tool)
    scene_cuts: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # PySceneDetect
    beat_map: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # librosa
    transitions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    camera_movements: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    color_grading_profile: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    audio_stem_s3_keys: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Demucs
    transcript: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Whisper
    text_overlays: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # OCR (Tesseract)

    # The combined, structured Edit Blueprint: scene cuts + camera
    # movement + beat alignment + text overlays + audio profile,
    # assembled into one per-scene timeline. This is what asset
    # matching (Week 3) and rendering (Week 4) actually consume --
    # the columns above are the raw per-tool outputs it's built from.
    edit_blueprint: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    raw_analysis_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="blueprint")
    asset_slots: Mapped[List["AssetSlot"]] = relationship(
        back_populates="blueprint", cascade="all, delete-orphan", order_by="AssetSlot.slot_index"
    )

    def __repr__(self) -> str:
        return f"<Blueprint project_id={self.project_id} status={self.status}>"
