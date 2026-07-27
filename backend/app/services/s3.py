"""
S3 helpers for direct-to-bucket uploads.

Flow: client asks us for a presigned PUT URL -> client uploads the
file straight to S3 (never touches our server) -> client tells us it's
done -> we call head_object to independently confirm the file is
really there (and get its real size) before trusting the upload.

generate_presigned_url() is a local signing operation (SigV4) -- it
does not call AWS, so this module works even before real credentials
are configured. head_object() *does* call AWS and needs real creds
(or a mocked S3 in tests).
"""
import os
import uuid
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

UPLOAD_URL_EXPIRE_SECONDS = 15 * 60
DOWNLOAD_URL_EXPIRE_SECONDS = 60 * 60

ALLOWED_CONTENT_TYPES = {
    "photo": {"image/jpeg", "image/png", "image/webp", "image/heic"},
    "video": {"video/mp4", "video/quicktime", "video/webm"},
}


def get_s3_client():
    # Not cached on purpose: created fresh per call so tests can swap in
    # mocked AWS credentials/region without needing a process restart.
    #
    # botocore resolves the client's *internal* endpoint to the correct
    # region (e.g. s3.ap-south-1.amazonaws.com) even without this, but
    # generate_presigned_url() has a long-standing quirk where it bakes
    # the bare global host (bucket.s3.amazonaws.com) into the signed
    # URL for virtual-hosted-style requests outside us-east-1. AWS then
    # rejects that URL outright (AuthorizationQueryParametersError)
    # because the signature's region doesn't match the host it lands
    # on. Passing endpoint_url explicitly forces the correct regional
    # host into the generated URL. Harmless for us-east-1 and for a
    # custom S3_ENDPOINT_URL (which takes priority below).
    #
    # Once endpoint_url is set explicitly, "auto" addressing stops
    # picking virtual-hosted-style on its own -- so we must say so
    # explicitly too. Path-style is only for a local/custom endpoint
    # (e.g. moto), never for real AWS: it's deprecated there for any
    # bucket created after Sept 2020.
    if settings.S3_ENDPOINT_URL:
        endpoint_url = settings.S3_ENDPOINT_URL
        addressing_style = "path"
    else:
        endpoint_url = f"https://s3.{settings.AWS_REGION}.amazonaws.com"
        addressing_style = "virtual"

    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=endpoint_url,
        # Passed explicitly rather than relying on boto3's default
        # credential chain (which looks for AWS_ACCESS_KEY_ID etc. as
        # real OS environment variables) -- our settings come from
        # .env via pydantic-settings, which does not export them to
        # os.environ, so the default chain would silently find nothing.
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    )


def build_s3_key(user_id: uuid.UUID, project_id: uuid.UUID, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"users/{user_id}/projects/{project_id}/assets/{uuid.uuid4()}{ext}"


def build_reference_video_key(project_id: uuid.UUID, ext: str) -> str:
    return f"projects/{project_id}/reference_video{ext}"


def upload_file_to_s3(local_path: str, key: str, content_type: str) -> None:
    # Server-side upload: the Celery worker already has the file on disk
    # (just downloaded it via yt-dlp), so it uploads directly -- unlike
    # the presigned-URL flow above, which is for a browser uploading a
    # user's own asset straight to S3 without the file passing through
    # our server at all.
    client = get_s3_client()
    client.upload_file(
        local_path,
        settings.S3_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def download_file_from_s3(key: str, local_path: str) -> None:
    # Server-side download: analysis tasks (scene detection, audio
    # analysis, etc.) need the reference video back on local disk to
    # run OpenCV/librosa/etc. over it.
    client = get_s3_client()
    client.download_file(settings.S3_BUCKET_NAME, key, local_path)


def generate_presigned_put(key: str, content_type: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key, "ContentType": content_type},
        ExpiresIn=UPLOAD_URL_EXPIRE_SECONDS,
    )


def generate_presigned_get(key: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=DOWNLOAD_URL_EXPIRE_SECONDS,
    )


def head_object(key: str) -> Optional[dict]:
    client = get_s3_client()
    try:
        return client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return None
        raise
