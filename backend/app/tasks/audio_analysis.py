"""
Celery task: detects BPM and beat timestamps from the reference
video's audio track, using librosa's beat tracker.

CPU-only, no GPU needed -- this is the local half of Day 9's audio
analysis. Speech transcription (Whisper) is a separate, GPU-hungry
step that per project policy must run offloaded (RunPod/Colab), not
on this laptop, so it isn't part of this task.
"""
import tempfile
import uuid
from pathlib import Path

import librosa

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.services.audio import extract_audio_waveform
from app.services.s3 import download_file_from_s3
from app.tasks.text_overlay import detect_text_overlays


@celery_app.task(name="app.tasks.audio_analysis.detect_beats", bind=True)
def detect_beats(self, project_id: str) -> None:
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
            waveform, sr = extract_audio_waveform(local_path)

        if waveform.size == 0:
            blueprint.beat_map = {"has_audio": False, "bpm": None, "beat_times_seconds": []}
            db.commit()
            detect_text_overlays.delay(project_id)
            return

        tempo, beat_times = librosa.beat.beat_track(y=waveform, sr=sr, units="time")
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)

        blueprint.beat_map = {
            "has_audio": True,
            "bpm": round(bpm, 2),
            "beat_times_seconds": [round(float(t), 3) for t in beat_times],
            "beat_count": len(beat_times),
        }
        db.commit()

        # Chain into the next (final) pipeline stage.
        detect_text_overlays.delay(project_id)

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
