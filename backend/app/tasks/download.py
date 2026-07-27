"""
Celery task: downloads the reference video for a project via yt-dlp,
uploads it to S3, and records its metadata on the project's blueprint.

Runs on CPU -- yt-dlp and the S3 upload are both light enough not to
need GPU offload, unlike the analysis steps in later days (Whisper,
Demucs, CLIP), which per project policy must NOT run on this laptop.
"""
import tempfile
import uuid
from pathlib import Path

import yt_dlp

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.models.project import Project, ProjectStatus
from app.services.s3 import build_reference_video_key, upload_file_to_s3
from app.tasks.scene_detection import detect_scenes


@celery_app.task(name="app.tasks.download.download_reference_video", bind=True)
def download_reference_video(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        project = db.get(Project, uuid.UUID(project_id))
        if project is None:
            return

        project.status = ProjectStatus.downloading
        db.commit()

        with tempfile.TemporaryDirectory() as tmpdir:
            outtmpl = str(Path(tmpdir) / "%(id)s.%(ext)s")
            ydl_opts = {
                "outtmpl": outtmpl,
                # Prefer a single pre-muxed file (video+audio already
                # combined) -- merging separate streams needs ffmpeg,
                # which isn't installed yet. Falls back to "best" if
                # no mp4 option exists.
                "format": "best[ext=mp4]/best",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "restrictfilenames": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(project.source_url, download=True)
                local_path = ydl.prepare_filename(info)

            ext = Path(local_path).suffix or ".mp4"
            key = build_reference_video_key(project.id, ext)
            upload_file_to_s3(local_path, key, content_type="video/mp4")

        blueprint = db.query(Blueprint).filter(Blueprint.project_id == project.id).first()
        if blueprint is None:
            blueprint = Blueprint(project_id=project.id)
            db.add(blueprint)

        blueprint.source_video_s3_key = key
        blueprint.source_duration_seconds = info.get("duration")
        blueprint.fps = info.get("fps")
        blueprint.resolution_width = info.get("width")
        blueprint.resolution_height = info.get("height")
        # Download is done, but scene detection / audio analysis / etc.
        # (Days 7-10) haven't run yet -- "processing" reflects that the
        # overall blueprint pipeline is still in progress, not finished.
        blueprint.status = BlueprintStatus.processing

        project.status = ProjectStatus.analyzing
        db.commit()

        # Chain into the next pipeline stage now that the video is on
        # S3 -- this is what makes it a real pipeline rather than a
        # series of manually-triggered steps.
        detect_scenes.delay(str(project.id))

    except Exception as exc:
        db.rollback()
        project = db.get(Project, uuid.UUID(project_id))
        if project is not None:
            project.status = ProjectStatus.failed
            project.error_message = str(exc)[:2000]
            db.commit()
        raise

    finally:
        db.close()
