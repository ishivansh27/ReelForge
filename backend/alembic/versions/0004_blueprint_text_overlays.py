"""add text_overlays to blueprints

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("blueprints", sa.Column("text_overlays", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("blueprints", "text_overlays")
