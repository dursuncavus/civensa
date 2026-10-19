"""CIV-029 locked assurance statement variables.

Revision ID: c0292027a001
Revises: c0382027a001
"""
from alembic import op
import sqlalchemy as sa

revision = 'c0292027a001'
down_revision = 'c0382027a001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ar_assurance_statements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('ar_documents.id'), nullable=False),
        sa.Column('code', sa.String(4), nullable=False),
        sa.Column('version_id', sa.String(80), nullable=False),
        sa.Column('file_sha256', sa.String(64), nullable=False),
        sa.Column('variables_json', sa.Text(), nullable=False),
        sa.UniqueConstraint('document_id', 'code'),
        sa.CheckConstraint("code IN ('EK-1','EK-2','EK-3')"))
    if op.get_bind().dialect.name == 'postgresql':
        # Reuse CIV-037's guard on both OLD and NEW document IDs.
        op.execute('''CREATE TRIGGER civ029_assurance_frozen
            BEFORE INSERT OR UPDATE OR DELETE ON ar_assurance_statements
            FOR EACH ROW EXECUTE FUNCTION civ037_frozen_content()''')
    else:
        for action in ('INSERT', 'UPDATE', 'DELETE'):
            refs = ['NEW.document_id'] if action == 'INSERT' else ['OLD.document_id'] if action == 'DELETE' else ['OLD.document_id', 'NEW.document_id']
            condition = ' OR '.join(f'document_id = {ref}' for ref in refs)
            op.execute(f"""CREATE TRIGGER civ029_assurance_{action.lower()}
                BEFORE {action} ON ar_assurance_statements
                WHEN EXISTS (SELECT 1 FROM ar_document_freezes WHERE {condition})
                BEGIN SELECT RAISE(ABORT, 'Onaylı faaliyet raporu beyanı değiştirilemez.'); END""")


def downgrade():
    if op.get_bind().execute(sa.text('SELECT 1 FROM ar_assurance_statements LIMIT 1')).first():
        raise RuntimeError('Güvence beyanı verisi var. Veriyi koruyan bir geçiş hazırlamadan sürüm düşürülemez.')
    op.drop_table('ar_assurance_statements')
