"""
Celery task: AI asset matching.

Step 1: for each uploaded (ready) UserAsset, compute a CLIP embedding,
detect faces, and fill in width/height/duration.

Step 2: for each AssetSlot, pull the frame at that slot's timestamp
from the *reference* video and CLIP-embed it too -- this is the
"target" the slot is looking for.

Step 3: score every (slot, asset) pair by CLIP cosine similarity, with
bonuses for matching type (photo slot <-> photo asset) and face
presence (a slot whose reference frame has a face should prefer an
asset that also has one). Then use scipy's Hungarian algorithm for a
globally optimal one-to-one assignment, rather than greedily picking
whichever asset looks best for the first slot processed.

CPU-only throughout -- CLIP on single images is light enough not to
need GPU offload, unlike Whisper/Demucs.
"""
import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.asset_slot import AssetSlot, SlotType
from app.models.blueprint import Blueprint
from app.models.project import Project, ProjectStatus
from app.models.user_asset import AssetType, UploadStatus, UserAsset
from app.services.clip_embedding import cosine_similarity, embed_image
from app.services.face_detection import detect_faces
from app.services.media_frame import bgr_to_pil, extract_frame_and_metadata, extract_frame_at_time
from app.services.s3 import download_file_from_s3

TYPE_MATCH_BONUS = 0.2
FACE_MATCH_BONUS = 0.2
FACE_MISMATCH_PENALTY = 0.3


def _slot_expected_asset_type(slot_type: SlotType) -> AssetType:
    return AssetType.photo if slot_type == SlotType.photo else AssetType.video


@celery_app.task(name="app.tasks.asset_matching.match_assets_to_slots", bind=True)
def match_assets_to_slots(self, project_id: str) -> None:
    db = SessionLocal()
    try:
        blueprint = (
            db.query(Blueprint).filter(Blueprint.project_id == uuid.UUID(project_id)).first()
        )
        if blueprint is None or blueprint.source_video_s3_key is None:
            return

        slots = (
            db.query(AssetSlot)
            .filter(AssetSlot.blueprint_id == blueprint.id)
            .order_by(AssetSlot.slot_index)
            .all()
        )
        assets = (
            db.query(UserAsset)
            .filter(
                UserAsset.project_id == uuid.UUID(project_id),
                UserAsset.upload_status == UploadStatus.ready,
            )
            .all()
        )
        if not slots or not assets:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            # --- Step 1: embed + face-detect every uploaded asset ---
            for asset in assets:
                if asset.clip_embedding is not None:
                    continue  # already processed on a previous run

                local_path = str(Path(tmpdir) / f"asset_{asset.id}")
                download_file_from_s3(asset.s3_key, local_path)
                is_video = asset.asset_type == AssetType.video
                frame_bgr, meta = extract_frame_and_metadata(local_path, is_video)

                has_face, face_count = detect_faces(frame_bgr)
                embedding = embed_image(bgr_to_pil(frame_bgr))

                asset.width = meta["width"]
                asset.height = meta["height"]
                if meta["duration_seconds"] is not None:
                    asset.duration_seconds = meta["duration_seconds"]
                asset.has_face = has_face
                asset.face_count = face_count
                asset.clip_embedding = {"vector": embedding}

            db.commit()

            # --- Step 2: build each slot's target embedding from the reference video ---
            ref_local_path = str(Path(tmpdir) / "reference_video.mp4")
            download_file_from_s3(blueprint.source_video_s3_key, ref_local_path)

            cap = cv2.VideoCapture(ref_local_path)
            fps = blueprint.fps or 30.0
            slot_targets = {}
            try:
                for slot in slots:
                    midpoint = (slot.start_time_seconds + slot.end_time_seconds) / 2
                    frame_bgr = extract_frame_at_time(cap, midpoint, fps)
                    if frame_bgr is None:
                        continue
                    slot_has_face, _ = detect_faces(frame_bgr)
                    slot_embedding = embed_image(bgr_to_pil(frame_bgr))
                    slot_targets[slot.id] = {"embedding": slot_embedding, "has_face": slot_has_face}
            finally:
                cap.release()

        # --- Step 3: score every (slot, asset) pair, find the optimal assignment ---
        # Manually-assigned slots (Day 15's override) are never touched
        # by this task, and their assets are already spoken for -- both
        # are excluded from the pool the AI is allowed to reassign.
        manually_used_asset_ids = {s.matched_asset_id for s in slots if s.is_manual and s.matched_asset_id}
        assets = [a for a in assets if a.id not in manually_used_asset_ids]

        usable_slots = [s for s in slots if s.id in slot_targets and not s.is_manual]
        if not usable_slots or not assets:
            return

        # Clear stale matches from any previous run before assigning fresh
        # ones -- otherwise a slot that isn't part of this run's optimal
        # assignment could be left holding an outdated match. Manual
        # slots are excluded on purpose.
        for slot in slots:
            if not slot.is_manual:
                slot.matched_asset_id = None
                slot.match_confidence = None

        cost_matrix = np.zeros((len(usable_slots), len(assets)))
        similarity_matrix = np.zeros((len(usable_slots), len(assets)))

        for i, slot in enumerate(usable_slots):
            target = slot_targets[slot.id]
            expected_type = _slot_expected_asset_type(slot.slot_type)
            for j, asset in enumerate(assets):
                sim = cosine_similarity(target["embedding"], asset.clip_embedding["vector"])
                score = sim
                if asset.asset_type == expected_type:
                    score += TYPE_MATCH_BONUS
                if target["has_face"]:
                    score += FACE_MATCH_BONUS if asset.has_face else -FACE_MISMATCH_PENALTY
                similarity_matrix[i, j] = sim
                cost_matrix[i, j] = -score  # minimize cost == maximize score

        row_idx, col_idx = linear_sum_assignment(cost_matrix)

        for i, j in zip(row_idx, col_idx):
            slot = usable_slots[i]
            asset = assets[j]
            slot.matched_asset_id = asset.id
            slot.match_confidence = round(float(similarity_matrix[i, j]), 4)

        project = db.get(Project, uuid.UUID(project_id))
        if project is not None:
            project.status = ProjectStatus.matching

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
