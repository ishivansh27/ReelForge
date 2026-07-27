"""
Celery task: combines Week 2's separate analysis outputs (scene cuts,
camera movement, beat/audio profile, text overlays) into one
structured "Edit Blueprint" document, organized as a per-scene
timeline. This is what asset matching (Week 3) and rendering (Week 4)
will actually read from -- the other blueprint columns are the raw
per-tool outputs it's assembled from.

Also computes beat alignment: for each scene cut, how close it lands
to the nearest detected beat. That's new information, not just a copy
of existing data -- Days 7-10 never compared scene timing to beat
timing against each other.

This is the last stage of the Week 2 analysis pipeline: it's what
marks the blueprint as complete and chains into Day 12's asset
requirements generation.
"""
import uuid
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.models.project import Project, ProjectStatus
from app.tasks.asset_requirements import generate_asset_slots

# How close (in seconds) a scene cut must land to a beat to count as
# "on beat". ~0.15s is roughly a quarter-beat of tolerance at 120 BPM --
# tight enough to mean something, loose enough for real-world footage.
ON_BEAT_THRESHOLD_SECONDS = 0.15


def _nearest_beat(scene_start: float, beat_times: list) -> dict:
    if not beat_times:
        return {"nearest_beat_time_seconds": None, "offset_seconds": None, "is_on_beat": False}
    nearest = min(beat_times, key=lambda b: abs(b - scene_start))
    offset = abs(nearest - scene_start)
    return {
        "nearest_beat_time_seconds": round(nearest, 3),
        "offset_seconds": round(offset, 3),
        "is_on_beat": offset <= ON_BEAT_THRESHOLD_SECONDS,
    }


def _overlays_in_range(overlays: list, start: float, end: float) -> list:
    # Any overlay whose time range intersects this scene's range at all.
    return [
        {
            "text": o["text"],
            "start_time_seconds": o["start_time_seconds"],
            "end_time_seconds": o["end_time_seconds"],
        }
        for o in overlays
        if o["start_time_seconds"] < end and o["end_time_seconds"] > start
    ]


@celery_app.task(name="app.tasks.blueprint_assembly.generate_edit_blueprint", bind=True)
def generate_edit_blueprint(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None:
            return

        scene_cuts = (blueprint.scene_cuts or {}).get("cuts", [])
        camera_by_index = {
            c["scene_index"]: c for c in (blueprint.camera_movements or {}).get("scenes", [])
        }
        beat_times = (blueprint.beat_map or {}).get("beat_times_seconds", [])
        overlays = (blueprint.text_overlays or {}).get("overlays", [])

        scenes = []
        for cut in scene_cuts:
            idx = cut["scene_index"]
            camera = camera_by_index.get(
                idx, {"movement_type": "unknown", "confidence": 0.0, "magnitude": 0.0}
            )
            scenes.append(
                {
                    "scene_index": idx,
                    "start_time_seconds": cut["start_time_seconds"],
                    "end_time_seconds": cut["end_time_seconds"],
                    "duration_seconds": cut["duration_seconds"],
                    "camera_movement": camera,
                    "beat_alignment": _nearest_beat(cut["start_time_seconds"], beat_times),
                    "text_overlays": _overlays_in_range(
                        overlays, cut["start_time_seconds"], cut["end_time_seconds"]
                    ),
                }
            )

        edit_blueprint = {
            "video": {
                "duration_seconds": blueprint.source_duration_seconds,
                "fps": blueprint.fps,
                "resolution": {
                    "width": blueprint.resolution_width,
                    "height": blueprint.resolution_height,
                },
            },
            "audio_profile": {
                "has_audio": (blueprint.beat_map or {}).get("has_audio", False),
                "bpm": (blueprint.beat_map or {}).get("bpm"),
                "beat_count": (blueprint.beat_map or {}).get("beat_count", 0),
                "beat_times_seconds": beat_times,
            },
            "scenes": scenes,
            "scene_count": len(scenes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        blueprint.edit_blueprint = edit_blueprint
        blueprint.status = BlueprintStatus.completed

        project = db.get(Project, uuid.UUID(project_id))
        if project is not None:
            project.status = ProjectStatus.blueprint_ready

        db.commit()

        # Chain into Week 3: generate the actual upload requirements
        # from this blueprint.
        generate_asset_slots.delay(project_id)

    except Exception:
        db.rollback()
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is not None:
            blueprint.status = BlueprintStatus.failed
            db.commit()
        raise

    finally:
        db.close()
