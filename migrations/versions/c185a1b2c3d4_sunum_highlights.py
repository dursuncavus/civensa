"""CIV-185: editorial selections outside approved report payloads."""
from alembic import op
import sqlalchemy as sa

revision = 'c185a1b2c3d4'
down_revision = 'c184a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sunum_highlights',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('kind', sa.String(7), nullable=False),
        sa.Column('department_id', sa.Integer, sa.ForeignKey('departments.id')),
        sa.Column('fact_key', sa.String(120), nullable=False),
        sa.Column('label', sa.String(40)),
        sa.Column('sentence', sa.String(180), nullable=False),
        sa.Column('context', sa.String(80)),
        sa.Column('photo_id', sa.Integer, sa.ForeignKey('sunum_photos.id', ondelete='SET NULL')),
        sa.Column('selected', sa.Boolean, nullable=False),
        sa.Column('sort_order', sa.Integer, nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.CheckConstraint("kind IN ('spot','feature') AND (kind != 'feature' OR department_id IS NOT NULL)", name='ck_sunum_highlight_kind'),
        sa.CheckConstraint("kind = 'feature' OR photo_id IS NULL", name='ck_sunum_highlight_photo'),
        sa.CheckConstraint('length(trim(sentence)) BETWEEN 1 AND 180', name='ck_sunum_highlight_sentence'))
    op.create_index('uq_sunum_highlight_feature', 'sunum_highlights', ['organization_id', 'year', 'department_id'],
        unique=True, postgresql_where=sa.text("kind = 'feature'"), sqlite_where=sa.text("kind = 'feature'"))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT EXISTS (SELECT 1 FROM sunum_highlights)')).scalar():
        raise RuntimeError('Sunum öne çıkanları var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('sunum_highlights')
