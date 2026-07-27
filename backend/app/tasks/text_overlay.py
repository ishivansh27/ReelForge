"""
Celery task: detects on-screen text overlays -- what they say and
exactly when they appear/disappear -- using Tesseract OCR over frames
sampled at a fixed interval across the whole video.

Second-to-last stage of the Week 2 (reference video analysis)
pipeline: download -> scenes -> camera movement -> beats -> text
overlays -> [Day 11] assemble edit blueprint. CPU-only, no GPU/heavy
model needed -- Tesseract is the classical OCR engine, no PyTorch
involved.
"""
import difflib
import tempfile
import uuid
from pathlib import Path

import cv2

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.services.ocr import extract_text
from app.services.s3 import download_file_from_s3
from app.tasks.blueprint_assembly import generate_edit_blueprint

SAMPLE_INTERVAL_SECONDS = 0.5
MIN_TEXT_LENGTH = 2  # filters out single stray characters misread from background noise
SIMILARITY_THRESHOLD = 0.6  # how similar consecutive samples' text must be to count as "the same overlay"
MAX_GAP_SECONDS = SAMPLE_INTERVAL_SECONDS * 2  # max time gap to still merge into the same overlay


def _sample_video_text(local_path: str, fps: float, duration: float) -> list:
    cap = cv2.VideoCapture(local_path)
    samples = []
    try:
        t = 0.0
        while t < duration:
            frame_idx = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if ok:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                text = extract_text(gray)
                if len(text) >= MIN_TEXT_LENGTH:
                    samples.append((t, text))
            t += SAMPLE_INTERVAL_SECONDS
    finally:
        # Same Windows file-lock issue as Days 7-8: must release before
        # the temp dir cleanup tries to delete the video file.
        cap.release()
    return samples


def _group_into_overlays(samples: list) -> list:
    if not samples:
        return []

    overlays = []
    group_texts = [samples[0][1]]
    group_start = samples[0][0]
    group_end = samples[0][0]

    for t, text in samples[1:]:
        similar = difflib.SequenceMatcher(None, group_texts[-1], text).ratio() >= SIMILARITY_THRESHOLD
        within_gap = (t - group_end) <= MAX_GAP_SECONDS
        if similar and within_gap:
            group_texts.append(text)
            group_end = t
        else:
            overlays.append(
                {
                    "text": max(group_texts, key=len),
                    "start_time_seconds": round(group_start, 3),
                    "end_time_seconds": round(group_end + SAMPLE_INTERVAL_SECONDS, 3),
                }
            )
            group_texts = [text]
            group_start = t
            group_end = t

    overlays.append(
        {
            "text": max(group_texts, key=len),
            "start_time_seconds": round(group_start, 3),
            "end_time_seconds": round(group_end + SAMPLE_INTERVAL_SECONDS, 3),
        }
    )
    return overlays


@celery_app.task(name="app.tasks.text_overlay.detect_text_overlays", bind=True)
def detect_text_overlays(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or blueprint.source_video_s3_key is None:
            return

        fps = blueprint.fps or 30.0
        duration = blueprint.source_duration_seconds or 0.0

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = str(Path(tmpdir) / "reference_video.mp4")
            download_file_from_s3(blueprint.source_video_s3_key, local_path)
            samples = _sample_video_text(local_path, fps, duration)

        overlays = _group_into_overlays(samples)
        blueprint.text_overlays = {"overlays": overlays, "overlay_count": len(overlays)}
        db.commit()

        # Chain into the final pipeline stage: combine everything into
        # one structured Edit Blueprint (this is what actually marks
        # the blueprint/project as ready).
        generate_edit_blueprint.delay(project_id)

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
