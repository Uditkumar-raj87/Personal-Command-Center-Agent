"""add review logs and audit fields

Revision ID: 0001_review_logs
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_review_logs"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(120), nullable=False, server_default="development-user"),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("energy_level", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("priority_tag", sa.String(30), nullable=False, server_default="ROUTINE"),
        sa.Column("status", sa.String(30), nullable=False, server_default="INBOX"),
        sa.Column("source", sa.String(30), nullable=False, server_default="MANUAL_NOTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tasks_owner_id", "tasks", ["owner_id"])
    op.create_table(
        "review_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("owner_id", sa.String(120), nullable=False, server_default="development-user"),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_logs")
    op.drop_index("ix_tasks_owner_id", table_name="tasks")
    op.drop_table("tasks")