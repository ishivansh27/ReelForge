"""
Face detection via OpenCV's YuNet model (cv2.FaceDetectorYN). CPU-only,
no PyTorch involved -- this is a small ONNX model bundled in the repo
at app/data/, not something downloaded at runtime.

Note: opencv-python 5.x removed the classic CascadeClassifier/Haar
cascade Python bindings entirely (no cascade XML files ship in the
wheel anymore either) -- FaceDetectorYN is the modern, actually more
accurate replacement, so this isn't a downgrade.
"""
from pathlib import Path

import cv2
import numpy as np

_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "face_detection_yunet_2023mar.onnx"

_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        _detector = cv2.FaceDetectorYN_create(str(_MODEL_PATH), "", (320, 320))
    return _detector


def detect_faces(frame_bgr: np.ndarray) -> tuple:
    """Returns (has_face: bool, face_count: int) for a BGR OpenCV frame."""
    detector = _get_detector()
    height, width = frame_bgr.shape[:2]
    detector.setInputSize((width, height))
    _, faces = detector.detect(frame_bgr)
    count = 0 if faces is None else len(faces)
    return count > 0, count
