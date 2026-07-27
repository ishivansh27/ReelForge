"""
projects table -- one row per "editing project" a user starts:
they paste a reference video URL, and everything else (blueprint,
uploaded assets, render job) hangs off this project.
"""
import enum
import uuid
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin


class SourcePlatform(str, enum.Enum):
    instagram = "instagram"
    youtube = "youtube"
    other = "other"


class ProjectStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    analyzing = "analyzing"
    blueprint_ready = "blueprint_ready"
    awaiting_assets = "awaiting_assets"
    matching = "matching"
    rendering = "rendering"
    completed = "completed"
    failed = "failed"


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_platform: Mapped[SourcePlatform] = mapped_column(
        Enum(SourcePlatform, name="source_platform"), nullable=False
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.pending,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="projects")
    blueprint: Mapped[Optional["Blueprint"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    assets: Mapped[List["UserAsset"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    render_jobs: Mapped[List["RenderJob"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.title} ({self.status})>"
