"""add data pipeline columns to jobs

Revision ID: a4f9c2b8d3e1
Revises: e3ec0556e251
Create Date: 2026-03-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4f9c2b8d3e1"
down_revision: Union[str, Sequence[str], None] = "e3ec0556e251"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 2 data pipeline columns to jobs table."""
    op.add_column("jobs", sa.Column("prompt", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("data_sources", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("resolution_method", sa.String(50), nullable=True))
    op.add_column("jobs", sa.Column("analysis_mode", sa.String(20), nullable=True))
    op.add_column("jobs", sa.Column("assumptions", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("cached_data_keys", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove Phase 2 data pipeline columns from jobs table."""
    op.drop_column("jobs", "cached_data_keys")
    op.drop_column("jobs", "assumptions")
    op.drop_column("jobs", "analysis_mode")
    op.drop_column("jobs", "resolution_method")
    op.drop_column("jobs", "data_sources")
    op.drop_column("jobs", "prompt")
