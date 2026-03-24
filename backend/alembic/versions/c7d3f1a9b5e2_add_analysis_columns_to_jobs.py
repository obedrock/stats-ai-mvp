"""add analysis columns to jobs

Revision ID: c7d3f1a9b5e2
Revises: b5e1a3c7d9f2
Create Date: 2026-03-24 00:02:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d3f1a9b5e2"
down_revision: Union[str, Sequence[str], None] = "b5e1a3c7d9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 3 analysis result columns to jobs table."""
    op.add_column("jobs", sa.Column("r_result_json", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("interpretation", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("follow_up_suggestions", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("error_explanation", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("suggested_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove Phase 3 analysis result columns from jobs table."""
    op.drop_column("jobs", "suggested_prompt")
    op.drop_column("jobs", "error_explanation")
    op.drop_column("jobs", "follow_up_suggestions")
    op.drop_column("jobs", "interpretation")
    op.drop_column("jobs", "r_result_json")
