"""
CLIP image embeddings, for comparing how visually similar two images
are (a user's uploaded asset vs. the reference video's frame for a
given slot). Runs on CPU -- fine for one-off single-image embeddings,
unlike full audio/video model passes (Whisper/Demucs), which is why
this wasn't offloaded to RunPod/Colab like those were.

The model is loaded once per worker process (module-level singleton)
and reused across task calls -- reloading a ~350MB model on every
single task invocation would be wasteful.
"""
import numpy as np
import open_clip
import torch
from PIL import Image

_model = None
_preprocess = None


def _get_model():
    global _model, _preprocess
    if _model is None:
        # "-quickgelu" matches the activation function the "openai"
        # pretrained weights were actually trained with -- the plain
        # "ViT-B-32" config mismatches it silently (still runs, just
        # produces slightly-off embeddings).
        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32-quickgelu", pretrained="openai"
        )
        model.eval()
        _model = model
        _preprocess = preprocess
    return _model, _preprocess


def embed_image(image: Image.Image) -> list:
    model, preprocess = _get_model()
    tensor = preprocess(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).tolist()


def cosine_similarity(a: list, b: list) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
