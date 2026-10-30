"""CIV-074 append-only AR unit decisions and approved version snapshots."""
from alembic import op
import sqlalchemy as sa

revision = 'c074a1b2c3d4'
down_revision = 'c067a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ar_unit_workflow_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('ar_documents.id'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('from_status', sa.String(20), nullable=False),
        sa.Column('to_status', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('actor_name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_event_cursor', sa.Integer(), nullable=False),
        sa.Column('payload_json', sa.Text()),
        sa.Column('sha256', sa.String(64)),
        sa.UniqueConstraint('document_id', 'revision'),
        sa.CheckConstraint("(action = 'submit' AND from_status IN ('draft','returned') AND to_status = 'submitted') OR "
                           "(action = 'return' AND from_status = 'submitted' AND to_status = 'returned') OR "
                           "(action = 'approve' AND from_status = 'submitted' AND to_status = 'approved') OR "
                           "(action = 'reopen' AND from_status = 'approved' AND to_status = 'draft')"),
        sa.CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0"),
        sa.CheckConstraint('revision > 0 AND content_event_cursor >= 0'),
        sa.CheckConstraint("(action IN ('submit','approve') AND payload_json IS NOT NULL AND sha256 IS NOT NULL AND length(sha256) = 64) OR "
                           "(action IN ('return','reopen') AND payload_json IS NULL AND sha256 IS NULL)"))
    op.create_index('ix_ar_unit_workflow_events_document_id', 'ar_unit_workflow_events', ['document_id'])
    # A nullable inline reference works on both engines without rebuilding the
    # historical table (and therefore without replacing its existing guards).
    op.execute('ALTER TABLE ar_section_contents ADD COLUMN copied_from_approval_id INTEGER REFERENCES ar_unit_workflow_events(id)')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civ074_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Birim faaliyet raporu onay ve denetim geçmişi değiştirilemez; yeni geçiş ekleyin.'; END $$""")
        op.execute('CREATE TRIGGER civ074_immutable BEFORE UPDATE OR DELETE ON ar_unit_workflow_events FOR EACH ROW EXECUTE FUNCTION civ074_immutable()')
        op.execute('CREATE TRIGGER civ074_no_truncate BEFORE TRUNCATE ON ar_unit_workflow_events FOR EACH STATEMENT EXECUTE FUNCTION civ074_immutable()')
    else:
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER civ074_{action.lower()} BEFORE {action} ON ar_unit_workflow_events BEGIN SELECT RAISE(ABORT, 'Birim faaliyet raporu onay ve denetim geçmişi değiştirilemez.'); END")


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ar_unit_workflow_events IN ACCESS EXCLUSIVE MODE')
    if (op.get_bind().execute(sa.text('SELECT 1 FROM ar_unit_workflow_events LIMIT 1')).first() or
            op.get_bind().execute(sa.text('SELECT 1 FROM ar_section_contents WHERE copied_from_approval_id IS NOT NULL LIMIT 1')).first()):
        raise RuntimeError('Birim faaliyet raporu geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    op.drop_column('ar_section_contents', 'copied_from_approval_id')
    op.drop_table('ar_unit_workflow_events')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ074_immutable()')
