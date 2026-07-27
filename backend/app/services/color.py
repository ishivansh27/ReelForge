"""
Dominant color extraction -- gives gap-fill text clips (Day 16) a
background color pulled from the actual reference video at that point
in the timeline, rather than a generic placeholder color.
"""
import cv2
import numpy as np
from sklearn.cluster import KMeans


def get_dominant_color(frame_bgr: np.ndarray, k: int = 3) -> tuple:
    """Returns the most common color cluster as (r, g, b), 0-255 each."""
    small = cv2.resize(frame_bgr, (100, 100), interpolation=cv2.INTER_AREA)
    pixels = small.reshape(-1, 3).astype(np.float32)

    kmeans = KMeans(n_clusters=k, n_init=4, random_state=0)
    labels = kmeans.fit_predict(pixels)
    counts = np.bincount(labels)
    dominant_bgr = kmeans.cluster_centers_[np.argmax(counts)]

    b, g, r = dominant_bgr
    return int(r), int(g), int(b)


def contrasting_text_color(rgb: tuple) -> str:
    """Returns 'white' or 'black' -- whichever reads better on this background."""
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "black" if luminance > 0.6 else "white"
