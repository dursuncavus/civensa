"""CIV-044: require personal passwords for newly issued credentials.

Downgrade preserves the flag and its values, like the additive CIV-025 fields.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c044a1b2c3d4'
down_revision = 'c031b1a2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    if 'must_change_password' not in {c['name'] for c in sa.inspect(op.get_bind()).get_columns('users')}:
        op.add_column('users', sa.Column('must_change_password', sa.Boolean(),
                                        nullable=False, server_default=sa.false()))


def downgrade():
    # A rollback must not erase a pending password change or user data.
    pass
