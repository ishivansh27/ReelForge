"""
Direct-to-S3 upload endpoints.

1. Client calls POST /uploads/presign -- we create a `uploading`
   UserAsset row and hand back a presigned PUT URL.
2. Client PUTs the file straight to S3 (never touches our server).
3. Client calls POST /uploads/{asset_id}/confirm -- we independently
   verify the object exists in S3 (HeadObject) before trusting it and
   flip the row to `ready`.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.user_asset import UploadStatus, UserAsset
from app.schemas.upload import ConfirmUploadResponse, PresignUploadRequest, PresignUploadResponse
from app.services.s3 import (
    ALLOWED_CONTENT_TYPES,
    UPLOAD_URL_EXPIRE_SECONDS,
    build_s3_key,
    generate_presigned_put,
    head_object,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Statuses reached before Day 12's asset_slots exist -- uploading here
# would be accepted into the DB but have nothing to eventually match
# against, which is more confusing than just rejecting it up front.
_NOT_READY_FOR_UPLOADS = {
    ProjectStatus.pending,
    ProjectStatus.downloading,
    ProjectStatus.analyzing,
    ProjectStatus.blueprint_ready,
}


def _get_owned_project(db: Session, project_id: uuid.UUID, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/presign", response_model=PresignUploadResponse, status_code=status.HTTP_201_CREATED)
def presign_upload(
    payload: PresignUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_owned_project(db, payload.project_id, current_user)

    if project.status in _NOT_READY_FOR_UPLOADS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project isn't ready for uploads yet (status: {project.status.value})",
        )
    if project.status == ProjectStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Project failed analysis, cannot upload assets"
        )

    allowed = ALLOWED_CONTENT_TYPES[payload.asset_type.value]
    if payload.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"content_type '{payload.content_type}' not allowed for "
                f"{payload.asset_type.value}; expected one of {sorted(allowed)}"
            ),
        )

    s3_key = build_s3_key(current_user.id, payload.project_id, payload.filename)

    asset = UserAsset(
        user_id=current_user.id,
        project_id=payload.project_id,
        s3_key=s3_key,
        asset_type=payload.asset_type,
        upload_status=UploadStatus.uploading,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    upload_url = generate_presigned_put(s3_key, payload.content_type)

    return PresignUploadResponse(
        asset_id=asset.id,
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=UPLOAD_URL_EXPIRE_SECONDS,
    )


@router.post("/{asset_id}/confirm", response_model=ConfirmUploadResponse)
def confirm_upload(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = db.get(UserAsset, asset_id)
    if asset is None or asset.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    meta = head_object(asset.s3_key)
    if meta is None:
        asset.upload_status = UploadStatus.failed
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File not found in S3 -- upload may not have completed",
        )

    asset.upload_status = UploadStatus.ready
    asset.file_size_bytes = meta["ContentLength"]
    db.commit()

    return ConfirmUploadResponse(
        asset_id=asset.id,
        upload_status=asset.upload_status,
        file_size_bytes=asset.file_size_bytes,
    )
