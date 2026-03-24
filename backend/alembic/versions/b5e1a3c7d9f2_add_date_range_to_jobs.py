"""add date_range to jobs

Revision ID: b5e1a3c7d9f2
Revises: a4f9c2b8d3e1
Create Date: 2026-03-24 00:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5e1a3c7d9f2"
down_revision: Union[str, Sequence[str], None] = "a4f9c2b8d3e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add date_range column to jobs table."""
    op.add_column("jobs", sa.Column("date_range", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove date_range column from jobs table."""
    op.drop_column("jobs", "date_range")
