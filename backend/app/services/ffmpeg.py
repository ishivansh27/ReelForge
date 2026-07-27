"""
Resolves the ffmpeg/ffprobe binaries to call. See the note on
FFMPEG_CMD in app.core.config for why this doesn't just rely on PATH
on Windows.
"""
import glob
import os

from app.core.config import settings

_WINGET_GLOB = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_*\ffmpeg-*-full_build\bin"
)


def _resolve(configured: str, binary_name: str) -> str:
    if configured:
        return configured

    if os.name == "nt":
        matches = glob.glob(os.path.join(_WINGET_GLOB, f"{binary_name}.exe"))
        if matches:
            return matches[0]

    return binary_name  # rely on PATH -- works on Linux prod (apt install ffmpeg)


def get_ffmpeg_cmd() -> str:
    return _resolve(settings.FFMPEG_CMD, "ffmpeg")


def get_ffprobe_cmd() -> str:
    return _resolve(settings.FFPROBE_CMD, "ffprobe")
