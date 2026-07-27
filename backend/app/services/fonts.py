"""
Resolves a bold font file for gap-fill text rendering (Day 16). See
the note on FONT_PATH in app.core.config.
"""
import os

from app.core.config import settings

_CANDIDATE_PATHS = [
    r"C:\Windows\Fonts\segoeuib.ttf",  # Segoe UI Bold (Windows)
    r"C:\Windows\Fonts\arialbd.ttf",  # Arial Bold (Windows)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # common on Debian/Ubuntu
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def get_font_path() -> str:
    if settings.FONT_PATH:
        return settings.FONT_PATH

    for path in _CANDIDATE_PATHS:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "No bold font found. Set FONT_PATH in .env to a valid .ttf file."
    )
