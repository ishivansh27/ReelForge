"""
Shared helpers for building FFmpeg `drawtext` filters -- used by both
gap-fill clip generation (Day 16, standalone placeholder clips) and
text-overlay burn-in on real footage (Day 19, overlaid on top of
matched user assets). Pulled out once a second feature needed the same
text-wrapping/escaping machinery, rather than duplicating it.
"""
from pathlib import Path

from PIL import ImageFont

MAX_TOTAL_CHARS = 120


def ffmpeg_path_escape(path: str) -> str:
    # FFmpeg's filtergraph parser treats ":" as an option separator, so
    # a Windows drive letter ("C:") must be escaped; forward slashes
    # avoid backslash-escaping headaches entirely.
    return path.replace("\\", "/").replace(":", "\\:")


def wrap_text_to_width(text: str, font_path: str, fontsize: int, max_width_px: float) -> str:
    # Wraps by *measured* pixel width, not a guessed character count --
    # a fixed character limit overflows badly for bold fonts / wide
    # frames and underuses narrow ones (Day 16 caught this by actually
    # looking at a rendered sample, not just assuming it worked).
    text = text.strip()
    if len(text) > MAX_TOTAL_CHARS:
        text = text[: MAX_TOTAL_CHARS - 3].rstrip() + "..."

    font = ImageFont.truetype(font_path, fontsize)

    def width_of(s: str) -> int:
        box = font.getbbox(s)
        return box[2] - box[0]

    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if width_of(candidate) > max_width_px and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def write_text_file(directory: str, filename: str, text: str) -> str:
    path = Path(directory) / filename
    path.write_text(text, encoding="utf-8")
    return str(path)
