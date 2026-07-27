"""
Celery task: detects camera movement (pan, zoom, shake, static) per
scene, using sparse optical flow (Lucas-Kanade) over a handful of
sampled frame pairs within each scene from Day 7's scene_cuts. Results
are attached to those scenes by scene_index.

How the classification works, in plain terms: we track a set of
distinctive points frame-to-frame and look at how they moved.
  - Points barely moving at all -> "static"
  - Points moving outward from the frame center (or inward) -> zoom
  - Points all moving the same direction together -> pan/tilt
  - Points moving in inconsistent/random directions -> camera shake

CPU-only (OpenCV optical flow), no GPU/ML model needed.
"""
import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.blueprint import Blueprint, BlueprintStatus
from app.tasks.audio_analysis import detect_beats
from app.services.s3 import download_file_from_s3

MAX_SAMPLES_PER_SCENE = 10
STATIC_MAGNITUDE_THRESHOLD = 1.5  # avg pixels moved per sampled frame-pair
ZOOM_RADIAL_THRESHOLD = 0.6  # how outward/inward flow must be (0-1) to call it a zoom
PAN_CONSISTENCY_THRESHOLD = 0.6  # how uniform flow direction must be (0-1) to call it a pan

LK_PARAMS = dict(
    winSize=(15, 15),
    maxLevel=2,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
)
FEATURE_PARAMS = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)


def _sample_frame_indices(start_frame: int, end_frame: int, max_samples: int) -> list:
    span = max(end_frame - start_frame, 1)
    step = max(span // max_samples, 1)
    indices = list(range(start_frame, end_frame, step))
    return indices or [start_frame]


def _track_flow(cap: cv2.VideoCapture, frame_indices: list):
    """Returns (list of Nx2 flow-vector arrays, list of matching Nx2 origin-point arrays, frame_size)."""
    flows, origins, frame_size = [], [], None
    prev_gray = None

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_size = gray.shape[::-1]  # (width, height)

        if prev_gray is not None:
            p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
            if p0 is not None:
                p1, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, p0, None, **LK_PARAMS)
                if p1 is not None:
                    good_new = p1[status == 1]
                    good_old = p0[status == 1]
                    if len(good_new) > 0:
                        flows.append(good_new - good_old)
                        origins.append(good_old)

        prev_gray = gray

    return flows, origins, frame_size


def _classify_motion(flows: list, origins: list, frame_size) -> dict:
    if not flows or frame_size is None:
        return {"movement_type": "static", "confidence": 0.0, "magnitude": 0.0}

    all_flow = np.concatenate(flows)
    all_origins = np.concatenate(origins)
    magnitude = float(np.mean(np.linalg.norm(all_flow, axis=1)))

    if magnitude < STATIC_MAGNITUDE_THRESHOLD:
        return {"movement_type": "static", "confidence": 1.0, "magnitude": round(magnitude, 3)}

    width, height = frame_size
    center = np.array([width / 2, height / 2])
    to_center = all_origins - center
    norms = np.linalg.norm(to_center, axis=1, keepdims=True)
    norms[norms == 0] = 1e-6
    radial_unit = to_center / norms
    radial_component = np.sum(all_flow * radial_unit, axis=1)
    radial_score = float(np.mean(radial_component)) / max(magnitude, 1e-6)

    mean_flow = np.mean(all_flow, axis=0)
    pan_consistency = float(np.linalg.norm(mean_flow) / max(magnitude, 1e-6))

    if abs(radial_score) > ZOOM_RADIAL_THRESHOLD:
        movement_type = "zoom_in" if radial_score > 0 else "zoom_out"
        confidence = min(abs(radial_score), 1.0)
    elif pan_consistency > PAN_CONSISTENCY_THRESHOLD:
        dx, dy = mean_flow
        if abs(dx) >= abs(dy):
            movement_type = "pan_right" if dx > 0 else "pan_left"
        else:
            movement_type = "tilt_down" if dy > 0 else "tilt_up"
        confidence = pan_consistency
    else:
        movement_type = "camera_shake"
        confidence = 1.0 - pan_consistency

    return {
        "movement_type": movement_type,
        "confidence": round(confidence, 3),
        "magnitude": round(magnitude, 3),
    }


@celery_app.task(name="app.tasks.camera_movement.detect_camera_movement", bind=True)
def detect_camera_movement(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or blueprint.source_video_s3_key is None or not blueprint.scene_cuts:
            return

        fps = blueprint.fps or 30.0
        cuts = blueprint.scene_cuts.get("cuts", [])

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = str(Path(tmpdir) / "reference_video.mp4")
            download_file_from_s3(blueprint.source_video_s3_key, local_path)

            cap = cv2.VideoCapture(local_path)
            results = []
            for cut in cuts:
                start_frame = int(cut["start_time_seconds"] * fps)
                end_frame = int(cut["end_time_seconds"] * fps)
                frame_indices = _sample_frame_indices(start_frame, end_frame, MAX_SAMPLES_PER_SCENE)
                flows, origins, frame_size = _track_flow(cap, frame_indices)
                classification = _classify_motion(flows, origins, frame_size)
                results.append({"scene_index": cut["scene_index"], **classification})

            # Same Windows file-lock issue as Day 7: must release before
            # the temp dir cleanup below tries to delete the video file.
            cap.release()

        blueprint.camera_movements = {"scenes": results}
        db.commit()

        # Chain into the next pipeline stage.
        detect_beats.delay(project_id)

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
