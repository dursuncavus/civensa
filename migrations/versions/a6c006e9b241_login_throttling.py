"""CIV-006: persistent failed-login attempts.

Revision ID: a6c006e9b241
Revises: f2b7c4d91e08
"""
from alembic import op
import sqlalchemy as sa

revision = "a6c006e9b241"
down_revision = "f2b7c4d91e08"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_key", sa.String(64), nullable=False),
        sa.Column("ip_key", sa.String(64), nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email_cleared", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("email_locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_login_attempts_email_time", "login_attempts", ["email_key", "failed_at"])
    op.create_index("ix_login_attempts_ip_time", "login_attempts", ["ip_key", "failed_at"])
    op.create_index("ix_login_attempts_failed_at", "login_attempts", ["failed_at"])


def downgrade():
    # Only CIV-006 throttle state is discarded; all other data/guards survive.
    op.drop_table("login_attempts")
