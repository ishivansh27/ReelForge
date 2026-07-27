"""
Response shape for asset requirements -- what the frontend shows the
user so they know exactly what to upload.
"""
import uuid
from typing import Optional

from pydantic import BaseModel

from app.models.asset_slot import SlotOrientation, SlotType


class AssetSlotOut(BaseModel):
    id: uuid.UUID
    slot_index: int
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    slot_type: SlotType
    required_orientation: SlotOrientation
    camera_movement_type: Optional[str] = None
    description: Optional[str] = None
    matched_asset_id: Optional[uuid.UUID] = None
    match_confidence: Optional[float] = None
    is_manual: bool = False
    gap_fill_s3_key: Optional[str] = None


class AssetSlotAssignRequest(BaseModel):
    # None clears the assignment and hands the slot back to AI matching;
    # a real asset_id locks it in as a manual override that the AI
    # matching task will never touch again.
    asset_id: Optional[uuid.UUID] = None
