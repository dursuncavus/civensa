"""CIV-063 immutable indicator evidence versions and frozen manifests.

Database binary storage matches AR financial statements. Downgrade refuses any
populated evidence tables rather than discard files or approval history.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c063a1b2c3d4'
down_revision = 'c048a1b2c3d4'
branch_labels = None
depends_on = None
TABLES = ('activity_evidence_files', 'activity_evidence_freezes')


def upgrade():
    op.create_table('activity_evidence_files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('actual_revision_id', sa.Integer(), sa.ForeignKey('actual_revisions.id'), nullable=False),
        sa.Column('report_indicator_id', sa.Integer(), sa.ForeignKey('report_indicators.id'), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(200), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('report_indicator_id', 'source_id', 'version', name='uq_activity_evidence_version'),
        sa.CheckConstraint('version > 0', name='ck_activity_evidence_version'))
    op.create_index('ix_activity_evidence_files_actual_revision_id', 'activity_evidence_files', ['actual_revision_id'])
    op.create_table('activity_evidence_freezes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('report_revision_id', sa.Integer(), sa.ForeignKey('activity_report_revisions.id'), nullable=False, unique=True),
        sa.Column('manifest_json', sa.Text(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False))
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civ063_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Kanıt dosyası veya dondurulmuş ek listesi değiştirilemez; yeni sürüm oluşturun.'; END $$""")
        for table in TABLES:
            op.execute(f'CREATE TRIGGER civ063_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ063_immutable()')
    else:
        for table in TABLES:
            for action in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER civ063_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Kanıt geçmişi değiştirilemez.'); END")


def downgrade():
    for table in TABLES:
        if op.get_bind().execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
            raise RuntimeError('Kanıt dosyası veya onay geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    for table in reversed(TABLES):
        op.drop_table(table)
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ063_immutable()')
