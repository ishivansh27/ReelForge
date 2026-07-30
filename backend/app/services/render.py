"""
Core render pipeline: stitches segments (matched user assets and
gap-fill clips) together in the exact order and duration specified by
the Edit Blueprint, applying the transition type detected at each
boundary (Day 18), burning in real on-screen text overlays at their
original relative timing (Day 19), and grading every segment toward
the reference video's own color profile (Day 20) -- an FFmpeg `xfade`
crossfade/fade-through-black/fade-through-white or a straight hard cut
between segments, plus optional `drawtext` overlays on top of real
footage segments. Silent output.

Each segment is independently normalized (scaled/padded to a common
canvas, common fps, common pixel format) before combining, since
inputs are a mix of arbitrary-sized user photos, user videos, and
generated gap-fill clips.
"""
import subprocess
import tempfile
from pathlib import Path

from app.services.color_grade import build_color_grade_filter
from app.services.drawtext import ffmpeg_path_escape, wrap_text_to_width, write_text_file
from app.services.ffmpeg import get_ffmpeg_cmd
from app.services.fonts import get_font_path

TRANSITION_DURATION_SECONDS = 0.35
OVERLAY_WIDTH_FRACTION = 0.7  # narrower than gap-fill's 0.85 -- this sits on top of real footage, not a full-frame placeholder

# Maps our own classifier's vocabulary (app.services.transitions) to
# FFmpeg's xfade transition names. Note "dissolve" maps to xfade's
# "fade" -- empirically, ffmpeg's own "dissolve" transition is a
# different (non-linear/dithered) effect, not the smooth cross-blend
# "dissolve" means in our vocabulary. Verified against ffmpeg's actual
# output while building the classifier, not assumed from the name.
XFADE_NAME = {
    "dissolve": "fade",
    "fade_black": "fadeblack",
    "fade_white": "fadewhite",
}


def _overlay_filters(overlays: list, width: int, tmpdir: str, seg_index: int) -> str:
    """Returns a comma-joined chain of drawtext filters (no brackets), one per
    overlay, each gated to only show during its own relative time window."""
    font_path = ffmpeg_path_escape(get_font_path())
    fontsize = max(width // 16, 18)

    parts = []
    for i, ov in enumerate(overlays):
        wrapped = wrap_text_to_width(ov["text"], get_font_path(), fontsize, width * OVERLAY_WIDTH_FRACTION)
        text_path = write_text_file(tmpdir, f"overlay_{seg_index}_{i}.txt", wrapped)
        text_path_escaped = ffmpeg_path_escape(text_path)
        start = max(ov["start"], 0.0)
        end = max(ov["end"], start + 0.1)
        # Commas inside the between() call must be escaped -- ffmpeg's
        # filtergraph parser otherwise reads them as ending this
        # filter's option list.
        parts.append(
            f"drawtext=fontfile='{font_path}':textfile='{text_path_escaped}':"
            f"fontcolor=white:fontsize={fontsize}:box=1:boxcolor=black@0.6:boxborderw=14:"
            f"x=(w-text_w)/2:y=h-text_h-60:enable='between(t\\,{start:.3f}\\,{end:.3f})'"
        )
    return ",".join(parts)


def _segment_filter(
    index: int,
    is_photo: bool,
    duration: float,
    width: int,
    height: int,
    fps: float,
    overlays: list,
    tmpdir: str,
    color_profile: dict = None,
) -> tuple:
    label_in = f"{index}:v"
    label_out = f"seg{index}"

    scale_pad = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )

    # settb pins every stream to the same explicit timebase (1/fps).
    # Without it, chaining multiple xfade filters fails outright --
    # xfade's output carries a different internal timebase
    # (microseconds) than a freshly-filtered segment (1/fps), and
    # feeding that mismatch into the next xfade in the chain errors
    # with "First input link main timebase do not match the
    # corresponding second input link xfade timebase". Real bug hit
    # while testing multi-transition renders, not a hypothetical.
    if is_photo:
        # -loop 1 -t already gives the exact duration at the demuxer
        # level; no trim/pad needed here.
        chain = f"[{label_in}]{scale_pad},fps={fps},format=yuv420p,settb=1/{fps}"
    else:
        # trim (cuts if longer than needed) -> tpad by up to `duration`
        # extra by cloning the last frame (covers the "shorter than
        # needed" case) -> trim again to the exact final length
        # (removes any excess padding). Robust without needing to know
        # the input's real duration ahead of time.
        chain = (
            f"[{label_in}]trim=duration={duration},setpts=PTS-STARTPTS,"
            f"tpad=stop_mode=clone:stop_duration={duration},"
            f"trim=duration={duration},setpts=PTS-STARTPTS,"
            f"{scale_pad},fps={fps},format=yuv420p,settb=1/{fps}"
        )

    # Color grade goes on before overlays -- it should tint the real
    # footage/gap-fill background, not the burned-in text box sitting
    # on top of it.
    if color_profile:
        chain = chain + "," + build_color_grade_filter(color_profile)

    if overlays:
        chain = chain + "," + _overlay_filters(overlays, width, tmpdir, index)

    return f"{chain}[{label_out}]", label_out


def render_final_video(
    segments: list,
    width: int,
    height: int,
    fps: float,
    output_path: str,
    transitions: list = None,
    color_profile: dict = None,
    audio_source_path: str = None,
) -> None:
    """
    segments: ordered list of {"path": str, "is_photo": bool, "duration": float,
    "overlays": list (optional)}. Each overlay is {"text": str, "start": float,
    "end": float} with start/end relative to that segment's own timeline (0 =
    segment start), not the original reference video's timeline.

    transitions: list of len(segments)-1 transition-type strings (one
    per boundary, in our own vocabulary: "cut"/"dissolve"/"fade_black"/
    "fade_white"). None or "cut" means a straight hard cut at that
    boundary.

    color_profile: optional dict from app.services.color_grade.analyze_color_profile,
    applied identically to every segment (matched footage and gap-fill
    alike) so the whole output reads as one consistent grade.

    audio_source_path: optional path to a video/audio file whose audio
    track becomes the final render's soundtrack -- normally the
    reference video itself, since beat-sync only means anything against
    the reference's own music. Padded with silence if shorter than the
    final render, trimmed if longer. None (e.g. the reference had no
    audio track at all) produces a silent render, same as before.
    """
    if transitions is None:
        transitions = ["cut"] * (len(segments) - 1)

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [get_ffmpeg_cmd(), "-y"]
        filters = []
        seg_labels = []

        for i, seg in enumerate(segments):
            if seg["is_photo"]:
                cmd += ["-loop", "1", "-framerate", str(fps), "-t", str(seg["duration"]), "-i", seg["path"]]
            else:
                cmd += ["-i", seg["path"]]
            filt, label = _segment_filter(
                i,
                seg["is_photo"],
                seg["duration"],
                width,
                height,
                fps,
                seg.get("overlays") or [],
                tmpdir,
                color_profile,
            )
            filters.append(filt)
            seg_labels.append(label)

        # Sequential fold: combine the running "accumulated" stream with
        # each next segment, using a hard concat or an xfade crossfade
        # depending on that boundary's detected transition. This handles
        # an arbitrary mix of cuts and transitions across N segments,
        # unlike a single N-way concat (which can only do hard cuts).
        acc_label = seg_labels[0]
        acc_duration = segments[0]["duration"]

        for i in range(1, len(segments)):
            next_label = seg_labels[i]
            next_duration = segments[i]["duration"]
            transition = transitions[i - 1]
            out_label = f"acc{i}"

            xfade_name = XFADE_NAME.get(transition)
            if xfade_name is None:
                filters.append(f"[{acc_label}][{next_label}]concat=n=2:v=1:a=0,settb=1/{fps}[{out_label}]")
                acc_duration = acc_duration + next_duration
            else:
                trans_dur = min(TRANSITION_DURATION_SECONDS, acc_duration / 2, next_duration / 2)
                offset = max(acc_duration - trans_dur, 0)
                filters.append(
                    f"[{acc_label}][{next_label}]xfade=transition={xfade_name}:"
                    f"duration={trans_dur}:offset={offset},settb=1/{fps}[{out_label}]"
                )
                acc_duration = acc_duration + next_duration - trans_dur

            acc_label = out_label

        filters.append(f"[{acc_label}]format=yuv420p[outv]")

        output_args = ["-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p"]

        if audio_source_path:
            audio_input_index = len(segments)
            cmd += ["-i", audio_source_path]
            # apad first (pads with silence up to acc_duration if the
            # reference's audio is shorter -- e.g. it looped or a
            # trailing scene ran past where the music stopped), then
            # atrim enforces the exact upper bound if it's longer.
            filters.append(
                f"[{audio_input_index}:a]apad=whole_dur={acc_duration},"
                f"atrim=0:{acc_duration},asetpts=PTS-STARTPTS[outa]"
            )
            output_args += ["-map", "[outa]", "-c:a", "aac", "-b:a", "192k"]

        filter_complex = ";".join(filters)
        cmd += ["-filter_complex", filter_complex, *output_args, output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg render failed:\n{result.stderr[-4000:]}")
