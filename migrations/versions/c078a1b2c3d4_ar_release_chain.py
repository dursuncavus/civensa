"""CIV-078 retained idare releases and reasoned reopen events."""
from alembic import op
import sqlalchemy as sa

revision = 'c078a1b2c3d4'
down_revision = 'c079a1b2c3d4'
branch_labels = None
depends_on = None

MUTABLE = {
    'ar_documents': 'civ037_ar_documents_frozen',
    'ar_section_contents': 'civ037_ar_section_contents_frozen',
    'ar_resource_rows': 'civ037_ar_resource_rows_frozen',
    **{name: f'civ038_{name}_frozen' for name in (
        'ar_budget_rows', 'ar_financial_entries', 'ar_financial_policies',
        'ar_financial_statements', 'ar_financial_imports')},
    'ar_assurance_statements': 'civ029_assurance_frozen',
}
MESSAGE = 'Onaylı faaliyet raporu veya denetim geçmişi değiştirilemez.'


def active_freeze(alias, upgraded, postgres):
    condition = ''
    if upgraded:
        key = "(e.after_json::jsonb->>'freeze_id')::integer" if postgres else "json_extract(e.after_json, '$.freeze_id')"
        condition = f''' AND (d.department_id IS NOT NULL OR NOT EXISTS (
            SELECT 1 FROM ar_content_events e WHERE e.document_id=f.document_id
            AND e.action='reopen' AND {key}=f.id))'''
    return f'''EXISTS (SELECT 1 FROM ar_document_freezes f JOIN ar_documents d ON d.id=f.document_id
        WHERE f.document_id IN ({alias})
        {"AND f.version=(SELECT max(n.version) FROM ar_document_freezes n WHERE n.document_id=f.document_id)" if upgraded else ""}
        {condition})'''


def postgres_guard(upgraded):
    op.execute(f'''CREATE OR REPLACE FUNCTION civ037_frozen_content() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE old_id integer; new_id integer;
        BEGIN
          IF TG_TABLE_NAME = 'ar_documents' THEN
            IF TG_OP <> 'INSERT' THEN old_id := OLD.id; END IF;
            IF TG_OP <> 'DELETE' THEN new_id := NEW.id; END IF;
          ELSE
            IF TG_OP <> 'INSERT' THEN old_id := OLD.document_id; END IF;
            IF TG_OP <> 'DELETE' THEN new_id := NEW.document_id; END IF;
          END IF;
          IF {active_freeze('old_id,new_id', upgraded, True)} THEN
            RAISE EXCEPTION '{MESSAGE}';
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
        END $$''')


def sqlite_guards(upgraded, install):
    for table in MUTABLE:
        prefix = 'civ029_assurance' if table == 'ar_assurance_statements' else ('civ037_' if table in (
            'ar_documents', 'ar_section_contents', 'ar_resource_rows') else 'civ038_') + table
        field = 'id' if table == 'ar_documents' else 'document_id'
        for action in ('INSERT', 'UPDATE', 'DELETE'):
            name = f'{prefix}_{action.lower()}'
            if not install:
                op.execute(f'DROP TRIGGER {name}')
                continue
            refs = f'NEW.{field}' if action == 'INSERT' else f'OLD.{field}' if action == 'DELETE' else f'OLD.{field},NEW.{field}'
            op.execute(f'''CREATE TRIGGER {name} BEFORE {action} ON {table}
                WHEN {active_freeze(refs, upgraded, False)}
                BEGIN SELECT RAISE(ABORT, '{MESSAGE}'); END''')


def upgrade():
    pg = op.get_bind().dialect.name == 'postgresql'
    # A constant server default backfills without UPDATEing protected rows.
    op.add_column('ar_document_freezes', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    if not pg:sqlite_guards(False, False)
    with op.batch_alter_table('ar_document_freezes', naming_convention={'uq': 'uq_%(table_name)s_%(column_0_name)s'}) as batch:
        unique = sa.inspect(op.get_bind()).get_unique_constraints('ar_document_freezes')[0]
        batch.drop_constraint(unique['name'] or 'uq_ar_document_freezes_document_id', type_='unique')
        batch.create_unique_constraint('uq_ar_document_freezes_document_version', ['document_id', 'version'])
        batch.create_check_constraint('ck_ar_release_version', 'version > 0')
    if pg:
        postgres_guard(True)
        for table in ('ar_document_freezes', 'ar_content_events'):
            op.execute(f'CREATE TRIGGER civ078_no_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION civ037_immutable()')
    else:
        sqlite_guards(True, True)
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER civ037_ar_document_freezes_{action.lower()} BEFORE {action} ON ar_document_freezes BEGIN SELECT RAISE(ABORT, '{MESSAGE}'); END")


def downgrade():
    pg = op.get_bind().dialect.name == 'postgresql'
    if pg:op.execute('LOCK TABLE ar_documents, ar_document_freezes, ar_content_events IN ACCESS EXCLUSIVE MODE')
    bind = op.get_bind()
    if (bind.execute(sa.text('SELECT 1 FROM ar_document_freezes GROUP BY document_id HAVING count(*) > 1 LIMIT 1')).first()
            or bind.execute(sa.text("SELECT 1 FROM ar_content_events WHERE action='reopen' LIMIT 1")).first()):
        raise RuntimeError('İdare sürüm veya yeniden açma geçmişi var. Veriyi koruyan geçiş hazırlanmadan sürüm düşürülemez.')
    if pg:
        postgres_guard(False)
        for table in ('ar_document_freezes', 'ar_content_events'):
            op.execute(f'DROP TRIGGER civ078_no_truncate ON {table}')
    else:sqlite_guards(True, False)
    with op.batch_alter_table('ar_document_freezes') as batch:
        batch.drop_constraint('uq_ar_document_freezes_document_version', type_='unique')
        batch.drop_constraint('ck_ar_release_version', type_='check')
        batch.create_unique_constraint('ar_document_freezes_document_id_key', ['document_id'])
        batch.drop_column('version')
    if not pg:
        sqlite_guards(False, True)
        for action in ('UPDATE', 'DELETE'):
            op.execute(f"CREATE TRIGGER civ037_ar_document_freezes_{action.lower()} BEFORE {action} ON ar_document_freezes BEGIN SELECT RAISE(ABORT, '{MESSAGE}'); END")
