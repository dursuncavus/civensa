"""CIV-219 directorate guide tables and activity photos."""
from alembic import op
import sqlalchemy as sa

revision = 'c219a1b2c3d4'
down_revision = 'c197a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ar_unit_tables',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('ar_documents.id'), nullable=False),
        sa.Column('kind', sa.String(2), nullable=False),
        sa.Column('payload_json', sa.Text, nullable=False),
        sa.UniqueConstraint('document_id', 'kind'),
        sa.CheckConstraint("kind IN ('1','2','7','8')"))
    op.create_table('ar_unit_photos',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('ar_documents.id'), nullable=False),
        sa.Column('activity_key', sa.String(80), nullable=False),
        sa.Column('caption', sa.Text, nullable=False),
        sa.Column('filename', sa.String(200), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('file_data', sa.LargeBinary, nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False))
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civ219_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE doc_id integer; status text;
        BEGIN
            IF TG_TABLE_NAME = 'ar_unit_photos' AND TG_OP <> 'INSERT' THEN
                RAISE EXCEPTION 'Faaliyet fotoğrafı değiştirilemez; yeni fotoğraf yükleyin.';
            END IF;
            IF TG_OP = 'DELETE' THEN doc_id := OLD.document_id; ELSE doc_id := NEW.document_id; END IF;
            IF TG_OP = 'UPDATE' AND NEW.document_id <> OLD.document_id THEN
                RAISE EXCEPTION 'Birim tablosu başka rapora taşınamaz.';
            END IF;
            PERFORM id FROM ar_documents WHERE id = doc_id AND department_id IS NOT NULL FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'Birim raporu seçin.'; END IF;
            SELECT to_status INTO status FROM ar_unit_workflow_events
                WHERE document_id = doc_id ORDER BY id DESC LIMIT 1;
            IF status IN ('submitted','approved') OR EXISTS (
                SELECT 1 FROM ar_document_freezes WHERE document_id = doc_id) THEN
                RAISE EXCEPTION 'İncelemedeki veya onaylı birim raporu değiştirilemez.';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
        END $$""")
        for table in ('ar_unit_tables', 'ar_unit_photos'):
            op.execute(f'CREATE TRIGGER civ219_guard BEFORE INSERT OR UPDATE OR DELETE ON {table} '
                       'FOR EACH ROW EXECUTE FUNCTION civ219_guard()')
        op.execute("""CREATE FUNCTION civ219_no_truncate() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Birim raporu tabloları topluca silinemez.'; END $$""")
        for table in ('ar_unit_tables', 'ar_unit_photos'):
            op.execute(f'CREATE TRIGGER civ219_no_truncate BEFORE TRUNCATE ON {table} '
                       'FOR EACH STATEMENT EXECUTE FUNCTION civ219_no_truncate()')


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ar_unit_tables, ar_unit_photos IN ACCESS EXCLUSIVE MODE')
    for table in ('ar_unit_tables', 'ar_unit_photos'):
        if op.get_bind().execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
            raise RuntimeError('Birim raporu verisi var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('ar_unit_photos')
    op.drop_table('ar_unit_tables')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ219_guard()')
        op.execute('DROP FUNCTION civ219_no_truncate()')
