"""create jobs table

Revision ID: e3ec0556e251
Revises: 6f82ac72c104
Create Date: 2026-03-23 14:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3ec0556e251"
down_revision: Union[str, Sequence[str], None] = "6f82ac72c104"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column(
            "stage",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("r_script", sa.Text(), nullable=True),
        sa.Column("result_stdout", sa.Text(), nullable=True),
        sa.Column("result_stderr", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("jobs")
