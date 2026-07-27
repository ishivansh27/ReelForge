"""
Celery task: reads the assembled Edit Blueprint (Day 11) and generates
one AssetSlot row per scene -- exactly what footage the user needs to
upload: clip or photo, how long, what orientation, and a human-
readable description of the shot. Day 13's upload flow and Day 14's AI
matching both build on these rows.
"""
import uuid

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.asset_slot import AssetSlot, SlotOrientation, SlotType
from app.models.blueprint import Blueprint
from app.models.project import Project, ProjectStatus

# Short, static scenes can be filled with a photo instead of requiring
# real video footage -- there's nothing moving for video to capture.
PHOTO_MAX_DURATION_SECONDS = 1.5


def _determine_slot_type(scene: dict) -> SlotType:
    movement = scene["camera_movement"]["movement_type"]
    duration = scene["duration_seconds"]
    if movement == "static" and duration < PHOTO_MAX_DURATION_SECONDS:
        return SlotType.photo
    return SlotType.video_clip


def _determine_orientation(width, height) -> SlotOrientation:
    if not width or not height:
        return SlotOrientation.any
    if width < height:
        return SlotOrientation.portrait
    if width > height:
        return SlotOrientation.landscape
    return SlotOrientation.square


def _build_description(scene: dict, slot_type: SlotType) -> str:
    movement = scene["camera_movement"]["movement_type"].replace("_", " ")
    duration = scene["duration_seconds"]
    kind = "photo" if slot_type == SlotType.photo else "video clip"
    parts = [f"{duration:.1f}s {kind}", f"{movement} shot"]
    if scene["beat_alignment"]["is_on_beat"]:
        parts.append("cuts on the beat")
    if scene["text_overlays"]:
        parts.append("reference has on-screen text here")
    return ", ".join(parts)


@celery_app.task(name="app.tasks.asset_requirements.generate_asset_slots", bind=True)
def generate_asset_slots(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or not blueprint.edit_blueprint:
            return

        # Idempotent: regenerating (e.g. after a re-analysis) replaces
        # old slots rather than piling up duplicates.
        existing = db.query(AssetSlot).filter(AssetSlot.blueprint_id == blueprint.id).all()
        for slot in existing:
            db.delete(slot)

        orientation = _determine_orientation(blueprint.resolution_width, blueprint.resolution_height)
        scenes = blueprint.edit_blueprint.get("scenes", [])

        for scene in scenes:
            slot_type = _determine_slot_type(scene)
            db.add(
                AssetSlot(
                    blueprint_id=blueprint.id,
                    slot_index=scene["scene_index"],
                    start_time_seconds=scene["start_time_seconds"],
                    end_time_seconds=scene["end_time_seconds"],
                    slot_type=slot_type,
                    required_orientation=orientation,
                    camera_movement_type=scene["camera_movement"]["movement_type"],
                    description=_build_description(scene, slot_type),
                )
            )

        project = db.get(Project, uuid.UUID(project_id))
        if project is not None:
            project.status = ProjectStatus.awaiting_assets

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
