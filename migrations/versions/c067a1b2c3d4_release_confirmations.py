"""CIV-067 append-only, period/content-bound manual release evidence."""
from alembic import op
import sqlalchemy as sa

revision = 'c067a1b2c3d4'
down_revision = 'c063a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('release_confirmations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('period_id', sa.Integer(), sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('item_id', sa.String(40), nullable=False),
        sa.Column('context_sha256', sa.String(64), nullable=False),
        sa.Column('decision', sa.String(20), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('actor_name', sa.String(200), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("decision IN ('confirmed', 'revoked')", name='ck_release_confirmation_decision'))
    op.create_index('ix_release_confirmations_period_id', 'release_confirmations', ['period_id'])
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civ067_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Yayın onay geçmişi değiştirilemez; yeni kayıt ekleyin.'; END $$""")
        op.execute('CREATE TRIGGER civ067_immutable BEFORE UPDATE OR DELETE ON release_confirmations FOR EACH ROW EXECUTE FUNCTION civ067_immutable()')
        op.execute('CREATE TRIGGER civ067_no_truncate BEFORE TRUNCATE ON release_confirmations FOR EACH STATEMENT EXECUTE FUNCTION civ067_immutable()')
    else:
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER civ067_{action.lower()} BEFORE {action} ON release_confirmations BEGIN SELECT RAISE(ABORT, 'Yayın onay geçmişi değiştirilemez.'); END")


def downgrade():
    if op.get_bind().execute(sa.text('SELECT 1 FROM release_confirmations LIMIT 1')).first():
        raise RuntimeError('Yayın onay geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    op.drop_table('release_confirmations')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ067_immutable()')
