"""
Snaps scene-cut boundaries onto the nearest detected beat, so cuts in
the final render land exactly on the music instead of just close to
it. Only the shared boundary between two consecutive slots is ever
moved -- the very first slot's start and the very last slot's end stay
fixed, since those aren't "cuts" at all.

Only snaps a boundary where a beat is genuinely nearby (within
SNAP_THRESHOLD_SECONDS). A boundary far from any detected beat (e.g.
past the point librosa's beat tracker lost the beat, as happened on
our own reference video after ~14s) is left exactly where scene
detection put it, rather than snapped to some unrelated beat -- that
would make the edit worse, not better.
"""

SNAP_THRESHOLD_SECONDS = 0.3


def compute_beat_synced_boundaries(slots: list, beat_times: list) -> list:
    """
    slots: ordered list of objects with .start_time_seconds/.end_time_seconds.
    Returns a list of (start, end) tuples, one per slot.
    """
    n = len(slots)
    boundaries = [slots[0].start_time_seconds] + [s.end_time_seconds for s in slots]

    if beat_times:
        for i in range(1, n):  # internal boundaries only
            original_t = boundaries[i]
            nearest = min(beat_times, key=lambda b: abs(b - original_t))
            if abs(nearest - original_t) <= SNAP_THRESHOLD_SECONDS:
                boundaries[i] = nearest

    return [(boundaries[i], boundaries[i + 1]) for i in range(n)]
