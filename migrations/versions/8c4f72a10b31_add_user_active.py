"""add user active status

Revision ID: 8c4f72a10b31
Revises: 290ef7e62102
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "8c4f72a10b31"
down_revision: Union[str, Sequence[str], None] = "290ef7e62102"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))

def downgrade() -> None:
    op.drop_column("users", "is_active")
