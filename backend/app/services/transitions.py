"""
Classifies the transition type at each scene-cut boundary in the
reference video, by inspecting a small window of real frames around
the boundary: a hard cut, a dissolve/crossfade, or a fade through
black/white. Feeds the render pipeline's choice of FFmpeg transition
filter between adjacent segments.

Heuristic, not ground truth -- similar in spirit to Day 8's camera
movement classifier. Most fast-cut short-form edits are plain hard
cuts (that's literally what PySceneDetect's ContentDetector, used in
Day 7, is built to find), so "cut" being the common result is expected
and honest, not a sign the classifier isn't doing anything.
"""
import cv2
import numpy as np

WINDOW_FRAMES = 5  # frames sampled on each side of the boundary
DARK_THRESHOLD = 40.0  # mean pixel value (0-255) below this counts as "near black"
LIGHT_THRESHOLD = 215.0
# How closely middle frames must match a predicted linear blend to
# count as a dissolve. Empirically, real crossfades (verified against
# ffmpeg's own xfade output) land ~10-30 here even for a perfectly
# clean synthetic transition, due to H.264/YUV420 compression and
# xfade's blend curve not being perfectly linear in time -- it's not
# near-zero like a naive "it's just alpha blending" model would
# suggest. A real hard cut, by contrast, peaks around 80-90 at the
# window's midpoint (a 50/50 blend prediction is maximally wrong when
# frames are actually 100% one color then 100% another). 35 sits
# comfortably between the two based on that measurement.
BLEND_ERROR_THRESHOLD = 35.0
MIN_CHANGE_FOR_BLEND = 15.0  # first/last frame must actually differ, or "matches a blend" is meaningless
# If one single consecutive frame-step accounts for more than this
# fraction of the total first-to-last change, that's a hard cut,
# full stop -- regardless of average blend error. Needed because on
# real (lower-contrast) footage, a hard cut's blend-error signature
# can come close enough to BLEND_ERROR_THRESHOLD to be ambiguous on
# its own; a single dominant jump is a more direct, reliable tell.
# Caught a real false-positive "dissolve" on the actual reference
# video this way (a shot change where before/after happened to share
# a similar warm color palette, tricking the blend-error check).
SINGLE_STEP_DOMINANCE_FRACTION = 0.45


def _read_frames_around(cap, boundary_frame: int) -> list:
    start = max(boundary_frame - WINDOW_FRAMES, 0)
    frames = []
    for idx in range(start, boundary_frame + WINDOW_FRAMES + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    return frames


def classify_transition(cap, boundary_time_seconds: float, fps: float) -> str:
    boundary_frame = int(boundary_time_seconds * fps)
    frames = _read_frames_around(cap, boundary_frame)
    if len(frames) < 3:
        return "cut"  # not enough data around this boundary to say otherwise

    # Full-color (unweighted) mean, not luma-weighted grayscale -- a
    # luma conversion (0.114*B + 0.587*G + 0.299*R) makes saturated
    # blue read as "dark" (~29/255) even though it isn't faded to
    # black at all. That's a real bias, not just a synthetic-test
    # artifact: it would misfire on any real cut into a dark-blue scene.
    colors = [f.astype(np.float32) for f in frames]
    brightness = [float(c.mean()) for c in colors]

    if min(brightness) < DARK_THRESHOLD and brightness[0] > DARK_THRESHOLD * 1.5:
        return "fade_black"
    if max(brightness) > LIGHT_THRESHOLD and brightness[0] < LIGHT_THRESHOLD * 0.85:
        return "fade_white"

    # A real crossfade is, mathematically, a linear blend between the
    # frame before it starts and the frame after it ends: frame(t) =
    # (1-a)*first + a*last. Check how closely the actual middle frames
    # match that prediction -- a hard cut (or unrelated content) won't.
    n = len(colors)
    first, last = colors[0], colors[-1]
    total_change = float(np.abs(first - last).mean())

    if total_change > MIN_CHANGE_FOR_BLEND:
        step_diffs = [float(np.abs(colors[i + 1] - colors[i]).mean()) for i in range(n - 1)]
        if max(step_diffs) > SINGLE_STEP_DOMINANCE_FRACTION * total_change:
            return "cut"

        blend_errors = []
        for i in range(1, n - 1):
            alpha = i / (n - 1)
            predicted = (1 - alpha) * first + alpha * last
            blend_errors.append(float(np.abs(colors[i] - predicted).mean()))
        if blend_errors and (sum(blend_errors) / len(blend_errors)) < BLEND_ERROR_THRESHOLD:
            return "dissolve"

    return "cut"


def detect_all_transitions(cap, boundary_times_seconds: list, fps: float) -> list:
    return [classify_transition(cap, t, fps) for t in boundary_times_seconds]
