"""CIV-086 / D-190: stable editable-table keys; retain historical bytes."""
import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = 'c086a1b2c3d4'
down_revision = 'c084a1b2c3d4'
branch_labels = None
depends_on = None

KEY_TABLES = ('ar_section_table_keys', 'ar_section_row_keys', 'ar_statement_figure_keys')
MESSAGE = 'Dizgi anahtarı içeren sabit rapor kopyası var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.'


def default():
    if op.get_bind().dialect.name == 'postgresql':
        return sa.text('gen_random_uuid()::text')
    return sa.text("(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-a' || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))")


def change_column(table, parent, constraint, upgrade):
    bind = op.get_bind()
    triggers = bind.execute(sa.text("SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name=:table"),
                            {'table': table}).scalars().all() if bind.dialect.name == 'sqlite' else []
    # SQLite reflection omits unnamed CHECKs unless they are restated explicitly.
    checks = tuple(sa.CheckConstraint(check['sqltext']) for check in sa.inspect(bind).get_check_constraints(table)
                   if not check['name']) if bind.dialect.name == 'sqlite' else ()
    with op.batch_alter_table(table, table_args=checks) as batch:
        if upgrade:
            batch.add_column(sa.Column('stable_key', sa.String(36), nullable=False, server_default=default()))
            batch.create_unique_constraint(constraint, [*parent, 'stable_key'])
        else:
            batch.drop_constraint(constraint, type_='unique')
            batch.drop_column('stable_key')
    for trigger in triggers:
        # ADD COLUMN is native on some SQLite versions; batch recreation is not.
        name = trigger.split('TRIGGER ', 1)[1].split()[0]
        op.execute(f'DROP TRIGGER IF EXISTS {name}')
        op.execute(trigger)


def guards(install):
    pg = op.get_bind().dialect.name == 'postgresql'
    for table in KEY_TABLES:
        if pg:
            if install:
                op.execute(f'CREATE TRIGGER civ086_frozen BEFORE INSERT OR UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ037_frozen_content()')
                op.execute(f'CREATE TRIGGER civ086_no_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION civ037_immutable()')
            else:
                op.execute(f'DROP TRIGGER civ086_frozen ON {table}')
                op.execute(f'DROP TRIGGER civ086_no_truncate ON {table}')
        else:
            for action in ('INSERT', 'UPDATE', 'DELETE'):
                name = f'civ086_{table}_{action.lower()}'
                if not install:
                    op.execute(f'DROP TRIGGER {name}')
                    continue
                refs = 'NEW.document_id' if action == 'INSERT' else 'OLD.document_id' if action == 'DELETE' else 'OLD.document_id,NEW.document_id'
                # The c078 reopen policy, copied explicitly to keep this migration independent.
                op.execute(f'''CREATE TRIGGER {name} BEFORE {action} ON {table}
                  WHEN EXISTS (SELECT 1 FROM ar_document_freezes f JOIN ar_documents d ON d.id=f.document_id
                    WHERE f.document_id IN ({refs}) AND f.version=(SELECT max(n.version) FROM ar_document_freezes n WHERE n.document_id=f.document_id)
                    AND (d.department_id IS NOT NULL OR NOT EXISTS (SELECT 1 FROM ar_content_events e
                      WHERE e.document_id=f.document_id AND e.action='reopen' AND json_extract(e.after_json,'$.freeze_id')=f.id)))
                  BEGIN SELECT RAISE(ABORT, 'Onaylı faaliyet raporu veya denetim geçmişi değiştirilemez.'); END''')


def upgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('LOCK TABLE ar_documents, ar_section_contents, ar_resource_rows, ar_financial_entries, ar_financial_statements IN ACCESS EXCLUSIVE MODE')
    change_column('ar_resource_rows', ['document_id', 'table_kind'], 'uq_ar_resource_stable_key', True)
    change_column('ar_financial_entries', ['document_id', 'kind'], 'uq_ar_financial_stable_key', True)
    for table, field, parent, constraint in (
        ('ar_section_table_keys', 'content_id', 'ar_section_contents', 'uq_ar_section_table_key'),
        ('ar_section_row_keys', 'table_id', 'ar_section_table_keys', 'uq_ar_section_row_key'),
        ('ar_statement_figure_keys', 'statement_id', 'ar_financial_statements', 'uq_ar_statement_figure_key'),
    ):
        op.create_table(table,
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('ar_documents.id'), nullable=False),
            sa.Column(field, sa.Integer(), sa.ForeignKey(parent + '.id'), nullable=False),
            sa.Column('position', sa.Integer(), nullable=False),
            sa.Column('stable_key', sa.String(36), nullable=False, server_default=default()),
            sa.UniqueConstraint(field, 'stable_key', name=constraint))
    bind = op.get_bind()
    tables = sa.table('ar_section_table_keys', sa.column('id'), sa.column('document_id'),
                      sa.column('content_id'), sa.column('position'), sa.column('stable_key'))
    rows = sa.table('ar_section_row_keys', sa.column('document_id'), sa.column('table_id'),
                    sa.column('position'), sa.column('stable_key'))
    for content in bind.execute(sa.text('SELECT id, document_id, blocks_json FROM ar_section_contents')).mappings():
        try:blocks=json.loads(content['blocks_json'])
        except ValueError:blocks=[]
        for position, block in enumerate(blocks if isinstance(blocks,list) else []):
            if block.get('type') != 'table':
                continue
            key = str(uuid4())
            bind.execute(tables.insert().values(document_id=content['document_id'], content_id=content['id'],
                                               position=position, stable_key=key))
            table_id = bind.execute(sa.select(tables.c.id).where(tables.c.content_id == content['id'],
                                                              tables.c.stable_key == key)).scalar_one()
            for index, _ in enumerate(block['rows']):
                bind.execute(rows.insert().values(document_id=content['document_id'], table_id=table_id,
                                                  position=index, stable_key=str(uuid4())))
    figures = sa.table('ar_statement_figure_keys', sa.column('document_id'), sa.column('statement_id'),
                       sa.column('position'), sa.column('stable_key'))
    for statement in bind.execute(sa.text('SELECT id, document_id, figures_json FROM ar_financial_statements')).mappings():
        for index, _ in enumerate(json.loads(statement['figures_json'])):
            bind.execute(figures.insert().values(document_id=statement['document_id'], statement_id=statement['id'],
                                                 position=index, stable_key=str(uuid4())))
    guards(True)


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('LOCK TABLE ar_documents, ar_document_freezes, ar_unit_workflow_events, ar_resource_rows, ar_financial_entries, ar_section_contents, ar_section_table_keys, ar_section_row_keys, ar_statement_figure_keys IN ACCESS EXCLUSIVE MODE')
    for query in ('SELECT payload_json FROM ar_document_freezes',
                  "SELECT payload_json FROM ar_unit_workflow_events WHERE payload_json IS NOT NULL"):
        if any('_typeset' in json.loads(raw) for raw in bind.execute(sa.text(query)).scalars() if raw):
            raise RuntimeError(MESSAGE)
    guards(False)
    op.drop_table('ar_statement_figure_keys')
    op.drop_table('ar_section_row_keys')
    op.drop_table('ar_section_table_keys')
    change_column('ar_financial_entries', ['document_id', 'kind'], 'uq_ar_financial_stable_key', False)
    change_column('ar_resource_rows', ['document_id', 'table_kind'], 'uq_ar_resource_stable_key', False)
