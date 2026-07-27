"""
asset_slots table -- each row is one "slot" in the blueprint's timeline
that needs to be filled: a video clip, a photo, or (if nothing matches)
an animated text / motion graphic placeholder.
"""
import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin


class SlotType(str, enum.Enum):
    video_clip = "video_clip"
    photo = "photo"
    text_overlay = "text_overlay"
    motion_graphic = "motion_graphic"


class SlotOrientation(str, enum.Enum):
    portrait = "portrait"
    landscape = "landscape"
    square = "square"
    any = "any"


class AssetSlot(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "asset_slots"

    blueprint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False, index=True
    )

    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)  # order in the timeline
    start_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    slot_type: Mapped[SlotType] = mapped_column(Enum(SlotType, name="slot_type"), nullable=False)
    required_orientation: Mapped[SlotOrientation] = mapped_column(
        Enum(SlotOrientation, name="slot_orientation"), default=SlotOrientation.any, nullable=False
    )
    camera_movement_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Filled in once the AI matching step runs
    matched_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_assets.id", ondelete="SET NULL"), nullable=True
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # True once a human has overridden this slot's assignment -- the AI
    # matching task (Day 14) must never touch a manually-assigned slot
    # on a re-run, and must treat its asset as already spoken for.
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Used only if slot_type is text_overlay/motion_graphic, or as a fallback
    # when no user asset was matched for a video_clip/photo slot.
    fallback_text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Set once Day 16's gap-filling has generated an animated text clip
    # for a slot with no matched footage.
    gap_fill_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    blueprint: Mapped["Blueprint"] = relationship(back_populates="asset_slots")
    matched_asset: Mapped[Optional["UserAsset"]] = relationship(
        back_populates="matched_slots", foreign_keys=[matched_asset_id]
    )

    def __repr__(self) -> str:
        return f"<AssetSlot #{self.slot_index} {self.slot_type}>"
