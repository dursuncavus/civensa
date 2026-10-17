"""CIV-018: department lifecycle and subprogramme responsibility via period scope.

Downgrade retains this additive schema and all data. Re-upgrade is idempotent.
No department name uniqueness constraint: legacy duplicates must survive.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b018a1c2d3e4'
down_revision = 'a6c006e9b241'
branch_labels = None
depends_on = None


def upgrade():
    schema = sa.inspect(op.get_bind())
    if 'is_active' not in {c['name'] for c in schema.get_columns('departments')}:
        op.add_column('departments', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    if not schema.has_table('subprogram_scopes'):
        op.create_table('subprogram_scopes',
            sa.Column('subprogram_id', sa.Integer(), sa.ForeignKey('subprograms.id'), primary_key=True),
            sa.Column('scope_id', sa.Integer(), sa.ForeignKey('department_scopes.id'), primary_key=True))


def downgrade():
    # Keep inactive state and responsibility assignments; older code ignores them.
    pass
