"""
Celery task: generates an aesthetic animated text clip for any
AssetSlot that AI matching (Day 14) and manual override (Day 15) left
unfilled -- no real user footage exists for it, so we generate a
placeholder with FFmpeg: bold centered text, a color pulled from the
reference video at that exact point in the timeline (so it visually
belongs), and a smooth fade in/out.

Text content: if the reference video actually had on-screen text
during that scene (Day 10's OCR), we reuse it -- there's no more
honest content to draw from. Otherwise a friendly generic placeholder.
"""
import tempfile
import uuid
from pathlib import Path

import cv2

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.asset_slot import AssetSlot
from app.models.blueprint import Blueprint
from app.services.color import contrasting_text_color, get_dominant_color
from app.services.gap_fill import render_gap_fill_clip
from app.services.media_frame import extract_frame_at_time
from app.services.s3 import download_file_from_s3, upload_file_to_s3

GENERIC_FALLBACK_TEXT = "Your Moment Here"


def _scene_text_for_slot(blueprint: Blueprint, slot_index: int) -> str:
    scenes = (blueprint.edit_blueprint or {}).get("scenes", [])
    for scene in scenes:
        if scene["scene_index"] == slot_index:
            overlays = scene.get("text_overlays", [])
            if overlays:
                # Longest overlay tends to be the substantive line, not a stray fragment.
                return max((o["text"] for o in overlays), key=len)
    return GENERIC_FALLBACK_TEXT


@celery_app.task(name="app.tasks.gap_fill.generate_gap_fills", bind=True)
def generate_gap_fills(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or blueprint.source_video_s3_key is None:
            return

        gap_slots = (
            db.query(AssetSlot)
            .filter(AssetSlot.blueprint_id == blueprint.id, AssetSlot.matched_asset_id.is_(None))
            .order_by(AssetSlot.slot_index)
            .all()
        )
        if not gap_slots:
            return

        width = blueprint.resolution_width or 1080
        height = blueprint.resolution_height or 1920
        fps = blueprint.fps or 30.0

        with tempfile.TemporaryDirectory() as tmpdir:
            ref_local_path = str(Path(tmpdir) / "reference_video.mp4")
            download_file_from_s3(blueprint.source_video_s3_key, ref_local_path)

            cap = cv2.VideoCapture(ref_local_path)
            try:
                for slot in gap_slots:
                    midpoint = (slot.start_time_seconds + slot.end_time_seconds) / 2
                    frame_bgr = extract_frame_at_time(cap, midpoint, fps)
                    bg_color = get_dominant_color(frame_bgr) if frame_bgr is not None else (40, 40, 40)
                    text_color = contrasting_text_color(bg_color)

                    text = slot.fallback_text_content or _scene_text_for_slot(blueprint, slot.slot_index)
                    duration = slot.end_time_seconds - slot.start_time_seconds

                    output_path = str(Path(tmpdir) / f"gapfill_{slot.id}.mp4")
                    render_gap_fill_clip(
                        text=text,
                        duration_seconds=duration,
                        width=width,
                        height=height,
                        bg_color_rgb=bg_color,
                        text_color=text_color,
                        output_path=output_path,
                        fps=fps,
                    )

                    key = f"projects/{project_id}/gap_fills/{slot.id}.mp4"
                    upload_file_to_s3(output_path, key, content_type="video/mp4")

                    slot.gap_fill_s3_key = key
                    if not slot.fallback_text_content:
                        slot.fallback_text_content = text
                    db.commit()
            finally:
                cap.release()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
