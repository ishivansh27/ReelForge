"""
Celery task: detects scene cuts in the downloaded reference video.

Uses PySceneDetect's ContentDetector, which flags a cut wherever the
frame-to-frame visual content changes sharply (the standard approach
for finding hard cuts in edited video). Runs on OpenCV under the hood
-- CPU only, no GPU/heavy model needed.
"""
import tempfile
import uuid
from pathlib import Path

from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.services.s3 import download_file_from_s3
from app.tasks.camera_movement import detect_camera_movement


@celery_app.task(name="app.tasks.scene_detection.detect_scenes", bind=True)
def detect_scenes(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or blueprint.source_video_s3_key is None:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = str(Path(tmpdir) / "reference_video.mp4")
            download_file_from_s3(blueprint.source_video_s3_key, local_path)

            video = open_video(local_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector())
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()

            # OpenCV's VideoCapture keeps the file handle open until
            # released. On Windows (unlike Linux/Mac) you can't delete
            # a file that's still open, so without this the
            # TemporaryDirectory cleanup below throws PermissionError/
            # NotADirectoryError and the whole task looks like it
            # failed -- even though detection itself already succeeded.
            video.capture.release()

        cuts = [
            {
                "scene_index": i,
                "start_time_seconds": start.get_seconds(),
                "end_time_seconds": end.get_seconds(),
                "duration_seconds": end.get_seconds() - start.get_seconds(),
            }
            for i, (start, end) in enumerate(scene_list)
        ]

        blueprint.scene_cuts = {"cuts": cuts, "cut_count": len(cuts)}
        db.commit()

        # Chain into the next pipeline stage.
        detect_camera_movement.delay(project_id)

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
