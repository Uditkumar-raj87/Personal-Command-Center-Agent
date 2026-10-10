"""add development user scope

Revision ID: 0003_user_scope
Revises: 0002_plans_audit_tasks
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_user_scope"
down_revision = "0002_plans_audit_tasks"


def upgrade() -> None:
    op.add_column("tasks", sa.Column("user_id", sa.String(120), nullable=False, server_default="development-user"))
    op.add_column("plans", sa.Column("user_id", sa.String(120), nullable=False, server_default="development-user"))


def downgrade() -> None:
    op.drop_column("plans", "user_id")
    op.drop_column("tasks", "user_id")