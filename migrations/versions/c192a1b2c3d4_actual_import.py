"""CIV-192 stored indicator actual import previews."""
from alembic import op
import sqlalchemy as sa

revision = 'c192a1b2c3d4'
down_revision = 'c185a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('actual_imports',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('report_revision_id', sa.Integer, sa.ForeignKey('activity_report_revisions.id'), nullable=False),
        sa.Column('actor_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_sha256', sa.String(64), nullable=False),
        sa.Column('preview_json', sa.Text, nullable=False),
        sa.Column('result_json', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False))
    op.create_index('ix_actual_imports_report_revision_id', 'actual_imports', ['report_revision_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT EXISTS (SELECT 1 FROM actual_imports)')).scalar():
        raise RuntimeError('İçe aktarma kayıtları var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('actual_imports')
