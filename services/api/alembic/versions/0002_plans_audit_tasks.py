"""add persistent plans and audit records

Revision ID: 0002_plans_audit_tasks
Revises: 0001_review_logs
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_plans_audit_tasks"
down_revision = "0001_review_logs"


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(120), nullable=False, server_default="development-user"),
        sa.Column("planning_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("baseline_json", sa.Text(), nullable=False),
        sa.Column("proposal_json", sa.Text(), nullable=False),
        sa.Column("selected_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "audit_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("plans.id")),
        sa.Column("owner_id", sa.String(120), nullable=False, server_default="development-user"),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plans_owner_id", "plans", ["owner_id"])
    op.create_index("ix_audit_records_plan_id", "audit_records", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_records_plan_id", table_name="audit_records")
    op.drop_index("ix_plans_owner_id", table_name="plans")
    op.drop_table("audit_records")
    op.drop_table("plans")