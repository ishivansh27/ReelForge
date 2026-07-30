"""
Response shape for presigned S3 download URLs -- lets the frontend
preview/play a reference video, uploaded asset, gap-fill clip, or
finished render without ever seeing raw AWS credentials.
"""
from pydantic import BaseModel


class MediaUrlOut(BaseModel):
    url: str
    expires_in: int
