"""initial schema: users, projects, blueprints, asset_slots, user_assets, render_jobs

Revision ID: 0001
Revises:
Create Date: 2026-07-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Needed once for UUID default generation in Postgres.
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_tier", sa.String(50), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---------- projects ----------
    project_status = postgresql.ENUM(
        "pending", "downloading", "analyzing", "blueprint_ready", "awaiting_assets",
        "matching", "rendering", "completed", "failed",
        name="project_status",
        create_type=False,
    )
    source_platform = postgresql.ENUM("instagram", "youtube", "other", name="source_platform", create_type=False)
    project_status.create(op.get_bind(), checkfirst=True)
    source_platform.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_platform", source_platform, nullable=False),
        sa.Column("status", project_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    # ---------- user_assets ----------
    asset_type = postgresql.ENUM("photo", "video", name="asset_type", create_type=False)
    upload_status = postgresql.ENUM("uploading", "processing", "ready", "failed", name="upload_status", create_type=False)
    asset_type.create(op.get_bind(), checkfirst=True)
    upload_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.String(512), nullable=False),
        sa.Column("asset_type", asset_type, nullable=False),
        sa.Column("upload_status", upload_status, nullable=False, server_default="uploading"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("clip_embedding", postgresql.JSONB(), nullable=True),
        sa.Column("has_face", sa.Boolean(), nullable=True),
        sa.Column("face_count", sa.Integer(), nullable=True),
        sa.Column("dominant_colors", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_assets_user_id", "user_assets", ["user_id"])
    op.create_index("ix_user_assets_project_id", "user_assets", ["project_id"])

    # ---------- blueprints ----------
    blueprint_status = postgresql.ENUM("pending", "processing", "completed", "failed", name="blueprint_status", create_type=False)
    blueprint_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "blueprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", blueprint_status, nullable=False, server_default="pending"),
        sa.Column("source_video_s3_key", sa.String(512), nullable=True),
        sa.Column("source_duration_seconds", sa.Float(), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("resolution_width", sa.Integer(), nullable=True),
        sa.Column("resolution_height", sa.Integer(), nullable=True),
        sa.Column("scene_cuts", postgresql.JSONB(), nullable=True),
        sa.Column("beat_map", postgresql.JSONB(), nullable=True),
        sa.Column("transitions", postgresql.JSONB(), nullable=True),
        sa.Column("camera_movements", postgresql.JSONB(), nullable=True),
        sa.Column("color_grading_profile", postgresql.JSONB(), nullable=True),
        sa.Column("audio_stem_s3_keys", postgresql.JSONB(), nullable=True),
        sa.Column("transcript", postgresql.JSONB(), nullable=True),
        sa.Column("raw_analysis_s3_key", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_blueprints_project_id", "blueprints", ["project_id"], unique=True)

    # ---------- asset_slots ----------
    slot_type = postgresql.ENUM("video_clip", "photo", "text_overlay", "motion_graphic", name="slot_type", create_type=False)
    slot_orientation = postgresql.ENUM("portrait", "landscape", "square", "any", name="slot_orientation", create_type=False)
    slot_type.create(op.get_bind(), checkfirst=True)
    slot_orientation.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "asset_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("blueprint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.Column("start_time_seconds", sa.Float(), nullable=False),
        sa.Column("end_time_seconds", sa.Float(), nullable=False),
        sa.Column("slot_type", slot_type, nullable=False),
        sa.Column("required_orientation", slot_orientation, nullable=False, server_default="any"),
        sa.Column("camera_movement_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("matched_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_confidence", sa.Float(), nullable=True),
        sa.Column("fallback_text_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_asset_slots_blueprint_id", "asset_slots", ["blueprint_id"])

    # ---------- render_jobs ----------
    render_job_status = postgresql.ENUM("queued", "processing", "completed", "failed", name="render_job_status", create_type=False)
    render_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "render_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("status", render_job_status, nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_s3_key", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_render_jobs_project_id", "render_jobs", ["project_id"])
    op.create_index("ix_render_jobs_celery_task_id", "render_jobs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_table("render_jobs")
    op.drop_table("asset_slots")
    op.drop_table("blueprints")
    op.drop_table("user_assets")
    op.drop_table("projects")
    op.drop_table("users")

    for enum_name in (
        "render_job_status", "slot_orientation", "slot_type", "blueprint_status",
        "upload_status", "asset_type", "project_status", "source_platform",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
