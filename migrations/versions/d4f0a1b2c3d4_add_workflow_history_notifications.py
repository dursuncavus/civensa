"""add workflow history and notifications

Revision ID: d4f0a1b2c3d4
Revises: 8c4f72a10b31
"""
from alembic import op
import sqlalchemy as sa

revision = "d4f0a1b2c3d4"
down_revision = "8c4f72a10b31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("submissions", sa.Column("revision", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "submission_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("period_id", sa.Integer(), sa.ForeignKey("reporting_periods.id"), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_submission_events_submission_created", "submission_events", ["submission_id", "created_at"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("link", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_recipient", "notifications", ["role", "department_id", "is_read"])


def downgrade():
    op.drop_index("ix_notifications_recipient", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_submission_events_submission_created", table_name="submission_events")
    op.drop_table("submission_events")
    op.drop_column("submissions", "revision")
