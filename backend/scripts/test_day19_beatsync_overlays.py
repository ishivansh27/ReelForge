"""
Day 19 end-to-end integration test: beat-synced cut boundaries + real
text-overlay burn-in, exercised through the actual `run_render_job`
Celery task (not a standalone unit test of render.py/beat_sync.py --
those were already verified standalone; this checks the wiring in
app/tasks/render.py itself).

Builds a small synthetic-but-DB-realistic project:
  - reference video: 3 hard-cut scenes (red/green/blue), 2s each
  - beat_map with one beat close to the 2.0s boundary (should snap)
    and one far from the 4.0s boundary (should NOT snap)
  - edit_blueprint.scenes with text_overlays on scenes 0 and 1 (real
    footage, should be burned in) and scene 2 (gap-fill, should be
    skipped -- gap-fill clips already carry their own text)
  - 2 matched video assets (yellow, cyan) for slots 0/1, one gap-fill
    clip already generated for slot 2

Run from backend/ with the venv active and Celery worker + FastAPI
already running:
    python scripts\\test_day19_beatsync_overlays.py

Cleans up its own S3 objects + DB rows at the end regardless of outcome.
"""
import sys
import time
import uuid

sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.asset_slot import AssetSlot, SlotOrientation, SlotType
from app.models.blueprint import Blueprint, BlueprintStatus
from app.models.project import Project, ProjectStatus, SourcePlatform
from app.models.render_job import RenderJob
from app.models.user import User
from app.models.user_asset import AssetType, UploadStatus, UserAsset
from app.services.s3 import download_file_from_s3, upload_file_to_s3
from app.tasks.render import run_render_job

LOCAL_DIR = "C:/Users/kesha/AppData/Local/Temp/day19test"

db = SessionLocal()
s3_keys_to_clean = []

try:
    email = f"test_day19_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=email, hashed_password="not_a_real_hash")
    db.add(user)
    db.flush()

    project = Project(
        user_id=user.id,
        title="Day 19 Beat Sync Test",
        source_url="https://instagram.com/reel/day19test",
        source_platform=SourcePlatform.instagram,
        status=ProjectStatus.matching,
    )
    db.add(project)
    db.flush()

    ref_key = f"projects/{project.id}/reference_video.mp4"
    upload_file_to_s3(f"{LOCAL_DIR}/reference_video.mp4", ref_key, content_type="video/mp4")
    s3_keys_to_clean.append(ref_key)

    blueprint = Blueprint(
        project_id=project.id,
        status=BlueprintStatus.completed,
        source_video_s3_key=ref_key,
        source_duration_seconds=6.0,
        fps=15.0,
        resolution_width=360,
        resolution_height=640,
        beat_map={"beat_times_seconds": [0.5, 1.1, 2.05, 3.4, 4.9]},
        edit_blueprint={
            "scenes": [
                {
                    "scene_index": 0,
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 2.0,
                    "text_overlays": [{"text": "Hello World", "start_time_seconds": 0.5, "end_time_seconds": 1.5}],
                },
                {
                    "scene_index": 1,
                    "start_time_seconds": 2.0,
                    "end_time_seconds": 4.0,
                    "text_overlays": [
                        {"text": "Second Overlay Text", "start_time_seconds": 2.5, "end_time_seconds": 3.2}
                    ],
                },
                {
                    "scene_index": 2,
                    "start_time_seconds": 4.0,
                    "end_time_seconds": 6.0,
                    # Deliberately present -- must NOT show up in the render,
                    # since slot 2 is a gap-fill slot (real footage rule
                    # only applies to matched_asset_id slots).
                    "text_overlays": [
                        {"text": "SHOULD NOT APPEAR", "start_time_seconds": 4.2, "end_time_seconds": 5.0}
                    ],
                },
            ]
        },
    )
    db.add(blueprint)
    db.flush()

    asset0_key = f"users/{user.id}/projects/{project.id}/assets/{uuid.uuid4()}.mp4"
    asset1_key = f"users/{user.id}/projects/{project.id}/assets/{uuid.uuid4()}.mp4"
    gapfill_key = f"projects/{project.id}/gapfill/slot2.mp4"
    upload_file_to_s3(f"{LOCAL_DIR}/asset0.mp4", asset0_key, content_type="video/mp4")
    upload_file_to_s3(f"{LOCAL_DIR}/asset1.mp4", asset1_key, content_type="video/mp4")
    upload_file_to_s3(f"{LOCAL_DIR}/gapfill_slot2.mp4", gapfill_key, content_type="video/mp4")
    s3_keys_to_clean += [asset0_key, asset1_key, gapfill_key]

    asset0 = UserAsset(
        user_id=user.id,
        project_id=project.id,
        s3_key=asset0_key,
        asset_type=AssetType.video,
        upload_status=UploadStatus.ready,
        duration_seconds=3.0,
        width=360,
        height=640,
    )
    asset1 = UserAsset(
        user_id=user.id,
        project_id=project.id,
        s3_key=asset1_key,
        asset_type=AssetType.video,
        upload_status=UploadStatus.ready,
        duration_seconds=3.0,
        width=360,
        height=640,
    )
    db.add_all([asset0, asset1])
    db.flush()

    slot0 = AssetSlot(
        blueprint_id=blueprint.id,
        slot_index=0,
        start_time_seconds=0.0,
        end_time_seconds=2.0,
        slot_type=SlotType.video_clip,
        required_orientation=SlotOrientation.any,
        matched_asset_id=asset0.id,
        match_confidence=0.9,
    )
    slot1 = AssetSlot(
        blueprint_id=blueprint.id,
        slot_index=1,
        start_time_seconds=2.0,
        end_time_seconds=4.0,
        slot_type=SlotType.video_clip,
        required_orientation=SlotOrientation.any,
        matched_asset_id=asset1.id,
        match_confidence=0.9,
    )
    slot2 = AssetSlot(
        blueprint_id=blueprint.id,
        slot_index=2,
        start_time_seconds=4.0,
        end_time_seconds=6.0,
        slot_type=SlotType.video_clip,
        required_orientation=SlotOrientation.any,
        gap_fill_s3_key=gapfill_key,
    )
    db.add_all([slot0, slot1, slot2])
    db.flush()

    job = RenderJob(project_id=project.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id
    print(f"Project: {project.id}")
    print(f"Beat times: {blueprint.beat_map['beat_times_seconds']}")
    print("Expected: boundary@2.0s snaps to 2.05s (within 0.3 threshold); boundary@4.0s stays (nearest beat 4.9 is 0.9s away)")
    print(f"Enqueuing render_job={job_id}...")

    async_result = run_render_job.delay(str(job_id))

    for _ in range(60):
        db.expire_all()
        row = db.get(RenderJob, job_id)
        print(f"  status={row.status.value:<10} progress={row.progress_percent:>3}%")
        if row.status.value in ("completed", "failed"):
            if row.status.value == "failed":
                print(f"  ERROR: {row.error_message}")
            else:
                print(f"  output_s3_key: {row.output_s3_key}")
                s3_keys_to_clean.append(row.output_s3_key)
                local_out = f"{LOCAL_DIR}/final_render_output.mp4"
                download_file_from_s3(row.output_s3_key, local_out)
                print(f"  Downloaded to: {local_out}")

                bp_check = db.get(Blueprint, blueprint.id)
                print(f"  Persisted transitions: {bp_check.transitions}")
            break
        time.sleep(1)

finally:
    print("\nCleaning up S3 objects...")
    from app.services.s3 import get_s3_client
    from app.core.config import settings

    client = get_s3_client()
    for key in s3_keys_to_clean:
        if not key:
            continue
        try:
            client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
            print(f"  deleted s3://{settings.S3_BUCKET_NAME}/{key}")
        except Exception as exc:
            print(f"  failed to delete {key}: {exc}")

    print("Cleaning up DB rows...")
    db.rollback()
    db.execute(__import__("sqlalchemy").text("DELETE FROM users WHERE email = :email"), {"email": email})
    db.commit()
    db.close()
    print("Done.")
