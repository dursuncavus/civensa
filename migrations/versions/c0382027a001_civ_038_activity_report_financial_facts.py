"""CIV-038 activity report financial facts

Revision ID: c0382027a001
Revises: c0372027a001
Create Date: 2026-10-17 09:44:43.324817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0382027a001'
down_revision: Union[str, Sequence[str], None] = 'c0372027a001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ar_financial_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('payload_json', sa.Text(), nullable=False),
    sa.CheckConstraint("kind IN ('assets','aid','audit','explanations')"),
    sa.ForeignKeyConstraint(['document_id'], ['ar_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ar_financial_entries_document_id'), 'ar_financial_entries', ['document_id'], unique=False)
    op.create_table('ar_financial_imports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('preview_json', sa.Text(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['ar_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ar_financial_imports_document_id'), 'ar_financial_imports', ['document_id'], unique=False)
    op.create_table('ar_financial_policies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('lower_rate', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('upper_rate', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.CheckConstraint('lower_rate IS NULL OR lower_rate >= 0'),
    sa.CheckConstraint('lower_rate IS NULL OR upper_rate IS NULL OR lower_rate <= upper_rate'),
    sa.CheckConstraint('upper_rate IS NULL OR upper_rate >= 0'),
    sa.ForeignKeyConstraint(['document_id'], ['ar_documents.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id')
    )
    op.create_table('ar_financial_statements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('period', sa.String(length=200), nullable=False),
    sa.Column('statement_date', sa.String(length=10), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('figures_json', sa.Text(), nullable=False),
    sa.Column('filename', sa.String(length=200), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['ar_documents.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'name')
    )
    op.create_index(op.f('ix_ar_financial_statements_document_id'), 'ar_financial_statements', ['document_id'], unique=False)
    op.create_table('ar_budget_rows',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('row_key', sa.String(length=150), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=True),
    sa.Column('economic_code', sa.String(length=5), nullable=False),
    sa.Column('program_id', sa.Integer(), nullable=True),
    sa.Column('subprogram_id', sa.Integer(), nullable=True),
    sa.Column('initial', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('added', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('deducted', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('entered_final', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('actual', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('cancelled', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('carried', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('estimate', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('refunds', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('import_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("(kind = 'revenue' AND department_id IS NULL AND program_id IS NULL AND subprogram_id IS NULL) OR (kind = 'expenditure' AND department_id IS NOT NULL AND program_id IS NULL AND subprogram_id IS NULL) OR (kind = 'programme' AND department_id IS NOT NULL AND program_id IS NOT NULL)"),
    sa.CheckConstraint("kind IN ('expenditure','programme','revenue')"),
    sa.CheckConstraint('actual IS NULL OR actual >= 0'),
    sa.CheckConstraint('added IS NULL OR added >= 0'),
    sa.CheckConstraint('cancelled IS NULL OR cancelled >= 0'),
    sa.CheckConstraint('carried IS NULL OR carried >= 0'),
    sa.CheckConstraint('deducted IS NULL OR deducted >= 0'),
    sa.CheckConstraint('entered_final IS NULL OR entered_final >= 0'),
    sa.CheckConstraint('estimate IS NULL OR estimate >= 0'),
    sa.CheckConstraint('initial IS NULL OR initial >= 0'),
    sa.CheckConstraint('refunds IS NULL OR refunds >= 0'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['ar_documents.id'], ),
    sa.ForeignKeyConstraint(['import_id'], ['ar_financial_imports.id'], ),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
    sa.ForeignKeyConstraint(['subprogram_id'], ['subprograms.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'kind', 'row_key')
    )
    op.create_index(op.f('ix_ar_budget_rows_document_id'), 'ar_budget_rows', ['document_id'], unique=False)
    # Seed required statement slots for existing yearly idare reports.
    op.execute("""INSERT INTO ar_financial_statements
        (document_id,name,period,statement_date,explanation,figures_json,filename,sha256)
        SELECT id, 'Bilanço', '', '', '', '[]', '', '' FROM ar_documents WHERE scope='idare'
        UNION ALL
        SELECT id, 'Faaliyet Sonuçları Tablosu', '', '', '', '[]', '', '' FROM ar_documents WHERE scope='idare'""")
    install_guards()


def downgrade() -> None:
    """Downgrade schema."""
    bind=op.get_bind()
    for table in TABLES:
        if bind.execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
            raise RuntimeError('Malî bilgi veya içe aktarma geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    op.drop_index(op.f('ix_ar_budget_rows_document_id'), table_name='ar_budget_rows')
    op.drop_table('ar_budget_rows')
    op.drop_index(op.f('ix_ar_financial_statements_document_id'), table_name='ar_financial_statements')
    op.drop_table('ar_financial_statements')
    op.drop_table('ar_financial_policies')
    op.drop_index(op.f('ix_ar_financial_imports_document_id'), table_name='ar_financial_imports')
    op.drop_table('ar_financial_imports')
    op.drop_index(op.f('ix_ar_financial_entries_document_id'), table_name='ar_financial_entries')
    op.drop_table('ar_financial_entries')

TABLES = ('ar_budget_rows','ar_financial_entries','ar_financial_policies','ar_financial_statements','ar_financial_imports')


def install_guards():
    bind=op.get_bind()
    message='Onaylı faaliyet raporu veya denetim geçmişi değiştirilemez.'
    for table in TABLES:
        if bind.dialect.name=='postgresql':
            op.execute(f'CREATE TRIGGER civ038_{table}_frozen BEFORE INSERT OR UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ037_frozen_content()')
            if table=='ar_financial_imports':
                op.execute(f'CREATE TRIGGER civ038_import_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ037_immutable()')
        else:
            for action in ('INSERT','UPDATE','DELETE'):
                refs=['NEW.document_id'] if action=='INSERT' else ['OLD.document_id'] if action=='DELETE' else ['OLD.document_id','NEW.document_id']
                condition=' OR '.join(f'document_id={ref}' for ref in refs)
                op.execute(f"CREATE TRIGGER civ038_{table}_{action.lower()} BEFORE {action} ON {table} WHEN EXISTS (SELECT 1 FROM ar_document_freezes WHERE {condition}) BEGIN SELECT RAISE(ABORT, '{message}'); END")
            if table=='ar_financial_imports':
                for action in ('UPDATE','DELETE'):
                    op.execute(f"CREATE TRIGGER civ038_import_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, '{message}'); END")
