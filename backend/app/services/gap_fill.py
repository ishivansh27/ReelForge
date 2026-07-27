"""
Renders a gap-fill clip: bold centered text over a solid color
background, with fade in/out, sized to a slot's exact duration and the
reference video's resolution. Uses FFmpeg directly via subprocess --
this multi-filter composition (color source + drawtext + fades) is
exactly what FFmpeg is built for.
"""
import subprocess
import tempfile
from pathlib import Path

from app.services.drawtext import ffmpeg_path_escape, wrap_text_to_width
from app.services.ffmpeg import get_ffmpeg_cmd
from app.services.fonts import get_font_path

FADE_SECONDS = 0.4
WRAP_WIDTH_FRACTION = 0.85  # leave a margin so text never touches the frame edges


def render_gap_fill_clip(
    text: str,
    duration_seconds: float,
    width: int,
    height: int,
    bg_color_rgb: tuple,
    text_color: str,
    output_path: str,
    fps: float = 30.0,
) -> None:
    duration_seconds = max(duration_seconds, 0.5)
    fade_duration = min(FADE_SECONDS, duration_seconds / 3)

    r, g, b = bg_color_rgb
    hex_color = f"0x{r:02X}{g:02X}{b:02X}"
    fontsize = max(min(width, height) // 12, 24)
    fade_out_start = max(duration_seconds - fade_duration, 0)

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_font_path = get_font_path()
        wrapped = wrap_text_to_width(text, raw_font_path, fontsize, width * WRAP_WIDTH_FRACTION)

        # Text goes through a file, not inline in the filter string --
        # sidesteps having to escape quotes/colons/commas that could
        # appear in real OCR-derived text.
        text_file = Path(tmpdir) / "gapfill_text.txt"
        text_file.write_text(wrapped, encoding="utf-8")

        font_path = ffmpeg_path_escape(raw_font_path)
        text_path = ffmpeg_path_escape(str(text_file))

        vf = (
            f"drawtext=fontfile='{font_path}':textfile='{text_path}':"
            f"fontcolor={text_color}:fontsize={fontsize}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=8,"
            f"fade=t=in:st=0:d={fade_duration},"
            f"fade=t=out:st={fade_out_start}:d={fade_duration}"
        )

        cmd = [
            get_ffmpeg_cmd(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={hex_color}:s={width}x{height}:d={duration_seconds}:r={fps}",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-3000:]}")
