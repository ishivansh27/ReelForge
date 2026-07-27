"""
Audio extraction from video files using PyAV, which bundles its own
FFmpeg libraries inside the wheel -- no system ffmpeg install required.
"""
import av
import numpy as np


def extract_audio_waveform(local_path: str, target_sr: int = 22050) -> tuple[np.ndarray, int]:
    """Returns (mono_waveform, sample_rate). Waveform is empty if the video has no audio track."""
    container = av.open(local_path)
    try:
        if not container.streams.audio:
            return np.array([], dtype=np.float32), target_sr

        audio_stream = container.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(format="fltp", layout="mono", rate=target_sr)

        chunks = []
        for frame in container.decode(audio_stream):
            for resampled in resampler.resample(frame):
                chunks.append(resampled.to_ndarray())
        for resampled in resampler.resample(None):  # flush any buffered samples
            chunks.append(resampled.to_ndarray())

        if not chunks:
            return np.array([], dtype=np.float32), target_sr

        waveform = np.concatenate(chunks, axis=1).flatten().astype(np.float32)
        return waveform, target_sr
    finally:
        container.close()
