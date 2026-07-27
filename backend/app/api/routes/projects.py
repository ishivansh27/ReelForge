"""
Project endpoints: create a project from a reference video URL (kicks
off the download in the background) and check on its status.
"""
import uuid
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.asset_slot import AssetSlot
from app.models.blueprint import Blueprint
from app.models.project import Project, ProjectStatus, SourcePlatform
from app.models.render_job import RenderJob
from app.models.user import User
from app.models.user_asset import UploadStatus, UserAsset
from app.schemas.asset_slot import AssetSlotAssignRequest, AssetSlotOut
from app.schemas.blueprint import BlueprintOut
from app.schemas.project import ProjectCreate, ProjectOut
from app.schemas.render_job import RenderJobOut
from app.schemas.user_asset import UserAssetOut
from app.tasks.asset_matching import match_assets_to_slots
from app.tasks.download import download_reference_video
from app.tasks.gap_fill import generate_gap_fills
from app.tasks.render import run_render_job

router = APIRouter(prefix="/projects", tags=["projects"])


def _detect_source_platform(url: str) -> SourcePlatform:
    host = urlparse(url).netloc.lower()
    if "instagram.com" in host or host == "instagr.am":
        return SourcePlatform.instagram
    if "youtube.com" in host or host == "youtu.be":
        return SourcePlatform.youtube
    return SourcePlatform.other


def _to_asset_slot_out(s: AssetSlot) -> AssetSlotOut:
    return AssetSlotOut(
        id=s.id,
        slot_index=s.slot_index,
        start_time_seconds=s.start_time_seconds,
        end_time_seconds=s.end_time_seconds,
        duration_seconds=s.end_time_seconds - s.start_time_seconds,
        slot_type=s.slot_type,
        required_orientation=s.required_orientation,
        camera_movement_type=s.camera_movement_type,
        description=s.description,
        matched_asset_id=s.matched_asset_id,
        match_confidence=s.match_confidence,
        is_manual=s.is_manual,
        gap_fill_s3_key=s.gap_fill_s3_key,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_url = str(payload.source_url)
    platform = _detect_source_platform(source_url)

    project = Project(
        user_id=current_user.id,
        title=f"Untitled project ({platform.value})",
        source_url=source_url,
        source_platform=platform,
        status=ProjectStatus.pending,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    download_reference_video.delay(str(project.id))

    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{project_id}/blueprint", response_model=BlueprintOut)
def get_project_blueprint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    blueprint = db.query(Blueprint).filter(Blueprint.project_id == project_id).first()
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blueprint not created yet")
    return blueprint


@router.get("/{project_id}/asset-requirements", response_model=list[AssetSlotOut])
def get_asset_requirements(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    blueprint = db.query(Blueprint).filter(Blueprint.project_id == project_id).first()
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blueprint not created yet")

    slots = (
        db.query(AssetSlot)
        .filter(AssetSlot.blueprint_id == blueprint.id)
        .order_by(AssetSlot.slot_index)
        .all()
    )
    if not slots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset requirements not generated yet"
        )

    return [_to_asset_slot_out(s) for s in slots]


@router.get("/{project_id}/assets", response_model=list[UserAssetOut])
def get_project_assets(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return (
        db.query(UserAsset)
        .filter(UserAsset.project_id == project_id)
        .order_by(UserAsset.created_at)
        .all()
    )


@router.post("/{project_id}/match-assets", status_code=status.HTTP_202_ACCEPTED)
def trigger_asset_matching(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.status not in (ProjectStatus.awaiting_assets, ProjectStatus.matching):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project isn't ready for matching yet (status: {project.status.value})",
        )

    ready_count = (
        db.query(UserAsset)
        .filter(UserAsset.project_id == project_id, UserAsset.upload_status == UploadStatus.ready)
        .count()
    )
    if ready_count == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No uploaded assets to match yet")

    match_assets_to_slots.delay(str(project_id))
    return {"detail": "Asset matching started"}


@router.patch("/{project_id}/asset-requirements/{slot_id}", response_model=AssetSlotOut)
def override_asset_slot(
    project_id: uuid.UUID,
    slot_id: uuid.UUID,
    payload: AssetSlotAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    blueprint = db.query(Blueprint).filter(Blueprint.project_id == project_id).first()
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blueprint not created yet")

    slot = db.get(AssetSlot, slot_id)
    if slot is None or slot.blueprint_id != blueprint.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    if payload.asset_id is None:
        # Clear the override -- hand the slot back to AI matching.
        slot.matched_asset_id = None
        slot.match_confidence = None
        slot.is_manual = False
    else:
        asset = db.get(UserAsset, payload.asset_id)
        if asset is None or asset.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found in this project"
            )
        if asset.upload_status != UploadStatus.ready:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset is not ready yet (upload not confirmed)",
            )

        # Enforce one-asset-per-slot: if this asset is currently sitting
        # in a different slot (manual or AI-matched), free it up first.
        other_slots = (
            db.query(AssetSlot)
            .filter(
                AssetSlot.blueprint_id == blueprint.id,
                AssetSlot.matched_asset_id == asset.id,
                AssetSlot.id != slot.id,
            )
            .all()
        )
        for other in other_slots:
            other.matched_asset_id = None
            other.match_confidence = None
            other.is_manual = False

        slot.matched_asset_id = asset.id
        slot.match_confidence = None  # manually chosen, not AI-scored
        slot.is_manual = True

    db.commit()
    db.refresh(slot)
    return _to_asset_slot_out(slot)


@router.post("/{project_id}/generate-gap-fills", status_code=status.HTTP_202_ACCEPTED)
def trigger_gap_fill(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.status != ProjectStatus.matching:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run asset matching before generating gap-fills (status: {project.status.value})",
        )

    generate_gap_fills.delay(str(project_id))
    return {"detail": "Gap-fill generation started"}


@router.post("/{project_id}/render", response_model=RenderJobOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_render(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.status != ProjectStatus.matching:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project isn't ready to render yet (status: {project.status.value})",
        )

    blueprint = db.query(Blueprint).filter(Blueprint.project_id == project_id).first()
    if blueprint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blueprint not created yet")

    slots = db.query(AssetSlot).filter(AssetSlot.blueprint_id == blueprint.id).all()
    unresolved = [s.slot_index for s in slots if not s.matched_asset_id and not s.gap_fill_s3_key]
    if unresolved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slots {sorted(unresolved)} have no matched asset or gap-fill clip -- run gap-fill generation first",
        )

    job = RenderJob(project_id=project_id)
    db.add(job)
    db.commit()
    db.refresh(job)

    run_render_job.delay(str(job.id))
    return job


@router.get("/{project_id}/render-jobs", response_model=list[RenderJobOut])
def list_render_jobs(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return (
        db.query(RenderJob)
        .filter(RenderJob.project_id == project_id)
        .order_by(RenderJob.created_at.desc())
        .all()
    )
