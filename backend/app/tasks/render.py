"""
Background render task. Runs in a Celery worker process, not the web
process, so a long render can't block API requests.

Day 17: real rendering replaces the Day 4 placeholder (which just
simulated progress with time.sleep to prove the job-queue plumbing
worked before the actual pipeline existed). Stitches every slot's
resolved source (a matched user asset, or a Day 16 gap-fill clip) in
blueprint order.

Day 18: transitions. Detects the transition type at each scene-cut
boundary from the reference video, persists it to blueprint.transitions
(populating a column that's existed since Day 2 but was never written
to), and applies it instead of always hard-cutting.

Day 19: beat sync + text overlays. Snaps each internal slot boundary
onto the nearest detected beat (within a small threshold -- see
app.services.beat_sync) so cuts land on the music, and burns in the
real on-screen text the reference video had at each point (Day 10's
OCR, via edit_blueprint.scenes[].text_overlays) onto the matching
real-footage segment at its original relative timing. Gap-fill
segments already carry their own text and are skipped for overlays.

Day 20: color grading. Extracts an overall color profile (tint,
saturation, contrast) from the reference video and applies it to every
segment -- matched footage and gap-fill alike -- so the whole output
reads as one consistent grade instead of each clip's own native
colors. Shares the same reference-video download used for Day 18's
transition detection (both need real frames from the source video, no
reason to pull it from S3 twice).
"""
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.asset_slot import AssetSlot
from app.models.blueprint import Blueprint
from app.models.project import Project, ProjectStatus
from app.models.render_job import RenderJob, RenderJobStatus
from app.models.user_asset import AssetType, UserAsset
from app.services.beat_sync import compute_beat_synced_boundaries
from app.services.color_grade import analyze_color_profile
from app.services.render import render_final_video
from app.services.s3 import download_file_from_s3, upload_file_to_s3
from app.services.transitions import detect_all_transitions

MIN_OVERLAY_OVERLAP_SECONDS = 0.1


def _ensure_reference_analysis(db, blueprint: Blueprint, slots: list) -> tuple:
    """Returns (transition_types, color_profile), computing and persisting
    whichever of blueprint.transitions / blueprint.color_grading_profile is
    still missing. Both need real frames from the reference video, so a
    single download is shared between them rather than fetching it twice."""
    boundary_count = len(slots) - 1
    existing_transitions = blueprint.transitions
    transitions_done = existing_transitions and len(existing_transitions.get("boundaries", [])) == boundary_count
    color_profile_done = bool(blueprint.color_grading_profile)

    if transitions_done and color_profile_done:
        return (
            [b["transition_type"] for b in existing_transitions["boundaries"]],
            blueprint.color_grading_profile,
        )

    # Deliberately uses the ORIGINAL scene boundaries (not beat-synced
    # ones) -- this is asking "what transition does the reference video
    # actually show at this cut", which doesn't move just because we've
    # decided to nudge our own render's cut point onto a nearby beat.
    boundary_times = [slots[i].end_time_seconds for i in range(boundary_count)]
    fps = blueprint.fps or 30.0

    with tempfile.TemporaryDirectory() as tmpdir:
        ref_path = str(Path(tmpdir) / "reference_video.mp4")
        download_file_from_s3(blueprint.source_video_s3_key, ref_path)
        cap = cv2.VideoCapture(ref_path)
        try:
            if transitions_done:
                transition_types = [b["transition_type"] for b in existing_transitions["boundaries"]]
            else:
                transition_types = detect_all_transitions(cap, boundary_times, fps)

            if color_profile_done:
                color_profile = blueprint.color_grading_profile
            else:
                color_profile = analyze_color_profile(cap)
        finally:
            cap.release()

    if not transitions_done:
        blueprint.transitions = {
            "boundaries": [
                {
                    "after_slot_index": slots[i].slot_index,
                    "boundary_time_seconds": boundary_times[i],
                    "transition_type": transition_types[i],
                }
                for i in range(boundary_count)
            ]
        }
    if not color_profile_done:
        blueprint.color_grading_profile = color_profile

    db.commit()
    return transition_types, color_profile


def _overlays_for_slot(scene: dict, adjusted_start: float, adjusted_duration: float) -> list:
    if not scene:
        return []

    overlays = []
    for ov in scene.get("text_overlays", []):
        rel_start = ov["start_time_seconds"] - adjusted_start
        rel_end = ov["end_time_seconds"] - adjusted_start
        clipped_start = max(rel_start, 0.0)
        clipped_end = min(rel_end, adjusted_duration)
        if clipped_end - clipped_start >= MIN_OVERLAY_OVERLAP_SECONDS:
            overlays.append({"text": ov["text"], "start": clipped_start, "end": clipped_end})
    return overlays


@celery_app.task(name="app.tasks.render.run_render_job", bind=True)
def run_render_job(self, render_job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(RenderJob, uuid.UUID(render_job_id))
        if job is None:
            return

        job.status = RenderJobStatus.processing
        job.celery_task_id = self.request.id
        job.started_at = datetime.now(timezone.utc)
        job.progress_percent = 0
        db.commit()

        blueprint = db.query(Blueprint).filter(Blueprint.project_id == job.project_id).first()
        if blueprint is None:
            raise ValueError("Blueprint not found for this project")

        slots = (
            db.query(AssetSlot)
            .filter(AssetSlot.blueprint_id == blueprint.id)
            .order_by(AssetSlot.slot_index)
            .all()
        )

        transition_types, color_profile = _ensure_reference_analysis(db, blueprint, slots)

        beat_times = (blueprint.beat_map or {}).get("beat_times_seconds", [])
        adjusted_boundaries = compute_beat_synced_boundaries(slots, beat_times)

        scenes_by_index = {s["scene_index"]: s for s in (blueprint.edit_blueprint or {}).get("scenes", [])}

        segments = []
        for slot, (adj_start, adj_end) in zip(slots, adjusted_boundaries):
            duration = adj_end - adj_start
            if slot.matched_asset_id:
                asset = db.get(UserAsset, slot.matched_asset_id)
                overlays = _overlays_for_slot(scenes_by_index.get(slot.slot_index), adj_start, duration)
                segments.append(
                    {
                        "s3_key": asset.s3_key,
                        "is_photo": asset.asset_type == AssetType.photo,
                        "duration": duration,
                        "overlays": overlays,
                    }
                )
            elif slot.gap_fill_s3_key:
                # Gap-fill clips already carry their own text -- no overlay burn-in.
                segments.append({"s3_key": slot.gap_fill_s3_key, "is_photo": False, "duration": duration})
            else:
                raise ValueError(
                    f"Slot #{slot.slot_index} has no matched asset or gap-fill clip -- run gap-fill generation first"
                )

        width = blueprint.resolution_width or 1080
        height = blueprint.resolution_height or 1920
        fps = blueprint.fps or 30.0

        project = db.get(Project, job.project_id)
        if project is not None:
            project.status = ProjectStatus.rendering
            db.commit()

        with tempfile.TemporaryDirectory() as tmpdir:
            local_segments = []
            for i, seg in enumerate(segments):
                ext = Path(seg["s3_key"]).suffix or (".jpg" if seg["is_photo"] else ".mp4")
                local_path = str(Path(tmpdir) / f"seg_{i}{ext}")
                download_file_from_s3(seg["s3_key"], local_path)
                local_segments.append(
                    {
                        "path": local_path,
                        "is_photo": seg["is_photo"],
                        "duration": seg["duration"],
                        "overlays": seg.get("overlays"),
                    }
                )

                job.progress_percent = int((i + 1) / len(segments) * 50)  # downloads: 0-50%
                db.commit()

            # Beat-sync only means anything against the reference's own
            # music, so the final render's soundtrack is the reference
            # video's audio track, not each matched clip's native audio
            # (mixing N different clips' own audio would fight the
            # beat-synced cut points instead of matching them).
            audio_source_path = None
            if (blueprint.beat_map or {}).get("has_audio") and blueprint.source_video_s3_key:
                audio_source_path = str(Path(tmpdir) / "reference_audio_source.mp4")
                download_file_from_s3(blueprint.source_video_s3_key, audio_source_path)

            output_path = str(Path(tmpdir) / "final_render.mp4")
            render_final_video(
                local_segments,
                width,
                height,
                fps,
                output_path,
                transitions=transition_types,
                color_profile=color_profile,
                audio_source_path=audio_source_path,
            )
            job.progress_percent = 90
            db.commit()

            key = f"projects/{job.project_id}/renders/{job.id}.mp4"
            upload_file_to_s3(output_path, key, content_type="video/mp4")

        job.status = RenderJobStatus.completed
        job.completed_at = datetime.now(timezone.utc)
        job.progress_percent = 100
        job.output_s3_key = key
        if project is not None:
            project.status = ProjectStatus.completed
        db.commit()

    except Exception as exc:
        db.rollback()
        job = db.get(RenderJob, uuid.UUID(render_job_id))
        if job is not None:
            job.status = RenderJobStatus.failed
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)

            # Without this, a render failure permanently strands the
            # project in "rendering" -- trigger_render's own status
            # gate would then reject every future retry attempt with
            # no way out. Reset it back to "matching" so the user can
            # fix the underlying issue (or just retry) and render again.
            project = db.get(Project, job.project_id)
            if project is not None:
                project.status = ProjectStatus.matching

            db.commit()
        raise

    finally:
        db.close()
