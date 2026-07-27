"""add gap_fill_s3_key to asset_slots

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("asset_slots", sa.Column("gap_fill_s3_key", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("asset_slots", "gap_fill_s3_key")
