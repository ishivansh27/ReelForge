"""
OCR helpers for text overlay detection. pytesseract is a thin wrapper
around the Tesseract-OCR system binary -- this module does not do OCR
itself, Tesseract does.
"""
import os

import pytesseract

from app.core.config import settings

_WINDOWS_DEFAULT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _configure_tesseract_cmd() -> None:
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    elif os.name == "nt" and os.path.exists(_WINDOWS_DEFAULT_PATH):
        # A fresh winget install often isn't on PATH for already-open
        # shells/processes -- fall back to the known default location.
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_DEFAULT_PATH
    # else: leave pytesseract's default ("tesseract"), relying on PATH
    # -- this is what works out of the box on Linux prod once
    # tesseract-ocr is apt-installed.


_configure_tesseract_cmd()


def extract_text(frame_gray) -> str:
    """Runs OCR on a grayscale OpenCV frame. Returns cleaned text, or "" if none found."""
    raw = pytesseract.image_to_string(frame_gray)
    return " ".join(raw.split())  # collapse whitespace/newlines, strip
