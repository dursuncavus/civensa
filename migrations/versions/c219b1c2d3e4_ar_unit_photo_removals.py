"""Append-only removal decisions; original photo evidence remains intact."""
from alembic import op
import sqlalchemy as sa

revision = 'c219b1c2d3e4'
down_revision = 'c219a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ar_unit_photo_removals',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('ar_documents.id'), nullable=False),
        sa.Column('photo_id', sa.Integer, sa.ForeignKey('ar_unit_photos.id'), nullable=False, unique=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    if op.get_bind().dialect.name == 'postgresql':
        # Reuse the original document lock, workflow and freeze guard unchanged.
        op.execute('CREATE TRIGGER civ219_guard BEFORE INSERT OR UPDATE OR DELETE ON ar_unit_photo_removals '
                   'FOR EACH ROW EXECUTE FUNCTION civ219_guard()')
        op.execute("""CREATE FUNCTION civ219_removal_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP <> 'INSERT' THEN
                RAISE EXCEPTION 'Fotoğraf kaldırma kaydı değiştirilemez veya silinemez.';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM ar_unit_photos p JOIN ar_documents d ON d.id = p.document_id
                JOIN users u ON u.id = NEW.created_by
                WHERE p.id = NEW.photo_id AND p.document_id = NEW.document_id
                  AND u.role = 'department' AND u.department_id = d.department_id) THEN
                RAISE EXCEPTION 'Fotoğraf yalnız kendi müdürlüğünün raporundan kaldırılabilir.';
            END IF;
            RETURN NEW;
        END $$""")
        op.execute('CREATE TRIGGER civ219_removal_guard BEFORE INSERT OR UPDATE OR DELETE ON ar_unit_photo_removals '
                   'FOR EACH ROW EXECUTE FUNCTION civ219_removal_guard()')
        op.execute('CREATE TRIGGER civ219_no_truncate BEFORE TRUNCATE ON ar_unit_photo_removals '
                   'FOR EACH STATEMENT EXECUTE FUNCTION civ219_no_truncate()')


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ar_unit_photo_removals IN ACCESS EXCLUSIVE MODE')
    if op.get_bind().execute(sa.text('SELECT 1 FROM ar_unit_photo_removals LIMIT 1')).first():
        raise RuntimeError('Fotoğraf kaldırma verisi var; veriyi koruyan aktarım hazırlanmadan sürüm düşürülemez.')
    op.drop_table('ar_unit_photo_removals')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP FUNCTION civ219_removal_guard()')
