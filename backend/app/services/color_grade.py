"""
Extracts a color grading profile from the reference video (overall
color tint, saturation, contrast) and turns it into an FFmpeg filter
that pushes every rendered segment -- matched user footage AND
gap-fill clips alike -- toward that same look, so the final render
visually matches the reference's grade instead of showing each clip's
own native colors untouched.

Heuristic, not real color-transfer (no per-shot LUT extraction, no ML
model) -- similar in spirit to Day 8's camera movement classifier and
Day 18's transition classifier. Reads the reference's overall color
tendencies (is it warm/cool, punchy/flat, vivid/muted) as one profile
for the whole video, applies the same profile uniformly to every
output segment. Good enough to visibly read as "the same style" for a
demo; not frame-accurate scene-by-scene color matching.
"""
import cv2
import numpy as np

SAMPLE_COUNT = 12

# Baselines a "neutral, ungraded" clip is assumed to sit around, on a
# 0-255 scale. The profile's gain/target values are expressed relative
# to these -- e.g. a reference that measures mean_saturation=140 against
# a baseline of 90 means "push output saturation up by ~1.5x", not
# "set saturation to 140" (FFmpeg's eq filter takes a multiplier, not
# an absolute level).
NEUTRAL_SATURATION_BASELINE = 90.0
NEUTRAL_CONTRAST_BASELINE = 50.0

# Clamp ranges keep a single unusual reference frame (e.g. one
# near-solid-black synthetic test clip) from producing a nonsensical
# filter -- a real color grade nudges a look, it doesn't invert it.
CHANNEL_GAIN_RANGE = (0.5, 1.8)
SATURATION_RANGE = (0.4, 1.8)
CONTRAST_RANGE = (0.7, 1.6)


def _clamp(value: float, bounds: tuple) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def analyze_color_profile(cap, sample_count: int = SAMPLE_COUNT) -> dict:
    """
    cap: an already-open cv2.VideoCapture on the reference video.
    Returns {"mean_r", "mean_g", "mean_b", "mean_saturation", "mean_contrast"},
    each an average over `sample_count` evenly spaced frames.
    """
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = sample_count

    frame_indices = np.linspace(0, max(total_frames - 1, 0), num=sample_count, dtype=int)

    r_sums, g_sums, b_sums = [], [], []
    saturation_sums = []
    contrast_sums = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue

        b, g, r = cv2.split(frame.astype(np.float32))
        r_sums.append(float(np.mean(r)))
        g_sums.append(float(np.mean(g)))
        b_sums.append(float(np.mean(b)))

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation_sums.append(float(np.mean(hsv[:, :, 1])))

        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        contrast_sums.append(float(np.std(luminance)))

    if not r_sums:
        # Never happens with a real video, but a degenerate/empty
        # capture should read as "no grade applied" rather than crash.
        return {
            "mean_r": 128.0,
            "mean_g": 128.0,
            "mean_b": 128.0,
            "mean_saturation": NEUTRAL_SATURATION_BASELINE,
            "mean_contrast": NEUTRAL_CONTRAST_BASELINE,
        }

    return {
        "mean_r": sum(r_sums) / len(r_sums),
        "mean_g": sum(g_sums) / len(g_sums),
        "mean_b": sum(b_sums) / len(b_sums),
        "mean_saturation": sum(saturation_sums) / len(saturation_sums),
        "mean_contrast": sum(contrast_sums) / len(contrast_sums),
    }


def build_color_grade_filter(profile: dict) -> str:
    """Returns a single FFmpeg filter expression (no brackets) that nudges
    a clip's color balance/saturation/contrast toward the given profile."""
    grand_mean = (profile["mean_r"] + profile["mean_g"] + profile["mean_b"]) / 3 or 1.0

    r_gain = _clamp(profile["mean_r"] / grand_mean, CHANNEL_GAIN_RANGE)
    g_gain = _clamp(profile["mean_g"] / grand_mean, CHANNEL_GAIN_RANGE)
    b_gain = _clamp(profile["mean_b"] / grand_mean, CHANNEL_GAIN_RANGE)

    saturation = _clamp(profile["mean_saturation"] / NEUTRAL_SATURATION_BASELINE, SATURATION_RANGE)
    contrast = _clamp(profile["mean_contrast"] / NEUTRAL_CONTRAST_BASELINE, CONTRAST_RANGE)

    return f"colorchannelmixer=rr={r_gain:.4f}:gg={g_gain:.4f}:bb={b_gain:.4f},eq=saturation={saturation:.4f}:contrast={contrast:.4f}"
