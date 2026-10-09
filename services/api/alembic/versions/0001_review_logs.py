"""add review logs and audit fields

Revision ID: 0001_review_logs
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_review_logs"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "review_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_logs")