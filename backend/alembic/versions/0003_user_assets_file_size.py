"""add file_size_bytes to user_assets

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_assets", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_assets", "file_size_bytes")
