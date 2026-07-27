"""
Extracts a representative frame + metadata (width, height, duration)
from an uploaded photo or video file, for CLIP embedding and face
detection. Also used to pull a frame at a specific timestamp from the
reference video, for building each slot's "target" embedding.
"""
from typing import Optional

import cv2
import numpy as np
from PIL import Image


def extract_frame_and_metadata(local_path: str, is_video: bool) -> tuple:
    """Returns (frame_bgr, metadata) where metadata has width/height/duration_seconds."""
    if not is_video:
        frame_bgr = cv2.imread(local_path)
        if frame_bgr is None:
            raise ValueError(f"Could not read image: {local_path}")
        height, width = frame_bgr.shape[:2]
        return frame_bgr, {"width": width, "height": height, "duration_seconds": None}

    cap = cv2.VideoCapture(local_path)
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else None

        # A frame from partway through reads better than frame 0, which
        # is often a fade-in/black/transition frame.
        target_frame = frame_count // 2 if frame_count > 1 else 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ok, frame_bgr = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame_bgr = cap.read()
        if not ok:
            raise ValueError(f"Could not read any frame from video: {local_path}")

        return frame_bgr, {"width": width, "height": height, "duration_seconds": duration}
    finally:
        cap.release()


def extract_frame_at_time(cap: cv2.VideoCapture, time_seconds: float, fps: float) -> Optional[np.ndarray]:
    frame_idx = int(time_seconds * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    return frame if ok else None


def bgr_to_pil(frame_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)
