"""CIV-197: append-only indicator direction metadata, separate from definitions."""
from alembic import op
import sqlalchemy as sa

revision = 'c197a1b2c3d4'
down_revision = 'c192a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('indicator_directions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('indicator_id', sa.String(36), sa.ForeignKey('indicator_identities.indicator_id'), nullable=False),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('direction', sa.String(6), nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.CheckConstraint("direction IN ('higher','lower')", name='ck_indicator_direction'),
        sa.CheckConstraint('length(trim(reason)) > 0', name='ck_indicator_direction_reason'))
    op.create_index('ix_indicator_direction_latest', 'indicator_directions', ['indicator_id', 'period_id', 'id'])
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civ197_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Gösterge yönü geçmişi değiştirilemez; yeni kayıt oluşturun.'; END $$""")
        op.execute('CREATE TRIGGER civ197_immutable BEFORE UPDATE OR DELETE ON indicator_directions '
                   'FOR EACH ROW EXECUTE FUNCTION civ197_immutable()')
        op.execute('CREATE TRIGGER civ197_no_truncate BEFORE TRUNCATE ON indicator_directions '
                   'FOR EACH STATEMENT EXECUTE FUNCTION civ197_immutable()')
    elif op.get_bind().dialect.name == 'sqlite':
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER civ197_{action.lower()} BEFORE {action} ON indicator_directions "
                       "BEGIN SELECT RAISE(ABORT, 'Gösterge yönü geçmişi değiştirilemez; yeni kayıt oluşturun.'); END")


def downgrade():
    if op.get_bind().execute(sa.text('SELECT EXISTS (SELECT 1 FROM indicator_directions)')).scalar():
        raise RuntimeError('Gösterge yönü geçmişi var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('indicator_directions')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ197_immutable()')
