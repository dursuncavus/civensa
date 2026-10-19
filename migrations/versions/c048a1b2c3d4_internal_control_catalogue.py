"""CIV-048 internal control catalogue and immutable Excel import history.

Downgrade retains catalogue/history data and guards; re-upgrade is idempotent.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c048a1b2c3d4'
down_revision = 'c044a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if 'ic_standards' not in tables:
        op.create_table('ic_standards',
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('component_code', sa.String(length=5), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('code')
        )
    if 'ic_imports' not in tables:
        op.create_table('ic_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_filename', sa.Text(), nullable=False),
        sa.Column('source_sha256', sa.String(length=64), nullable=False),
        sa.Column('source_json', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ic_unit_aliases' not in tables:
        op.create_table('ic_unit_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_name', sa.Text(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('body_name', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('(department_id IS NOT NULL AND body_name IS NULL) OR (department_id IS NULL AND body_name IS NOT NULL)', name='ck_ic_alias_target'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_name')
        )
    if 'ic_plans' not in tables:
        op.create_table('ic_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('start_year', sa.Integer(), nullable=False),
        sa.Column('end_year', sa.Integer(), nullable=False),
        sa.Column('version_label', sa.Text(), nullable=False),
        sa.Column('approval_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('source_filename', sa.Text(), nullable=False),
        sa.Column('source_sha256', sa.String(length=64), nullable=False),
        sa.Column('import_id', sa.Integer(), nullable=False),
        sa.Column('supersedes_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('draft','active','archived')", name='ck_ic_plan_status'),
        sa.CheckConstraint('start_year BETWEEN 1900 AND 2200 AND end_year BETWEEN start_year AND 2200', name='ck_ic_plan_years'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['import_id'], ['ic_imports.id'], ),
        sa.ForeignKeyConstraint(['supersedes_id'], ['ic_plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('import_id')
        )
        op.create_index('uq_ic_one_active_plan', 'ic_plans', ['status'], unique=True, postgresql_where=sa.text("status = 'active'"), sqlite_where=sa.text("status = 'active'"))
    if 'ic_conditions' not in tables:
        op.create_table('ic_conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('standard_code', sa.String(length=10), nullable=False),
        sa.Column('standard_title', sa.Text(), nullable=False),
        sa.Column('condition_code', sa.String(length=60), nullable=False),
        sa.Column('condition_code_raw', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('current_state_text', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['ic_plans.id'], ),
        sa.ForeignKeyConstraint(['standard_code'], ['ic_standards.code'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'plan_id', name='uq_ic_condition_plan'),
        sa.UniqueConstraint('plan_id', 'condition_code', name='uq_ic_condition_code')
        )
        op.create_index(op.f('ix_ic_conditions_plan_id'), 'ic_conditions', ['plan_id'], unique=False)
    if 'ic_import_audits' not in tables:
        op.create_table('ic_import_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('source_sha256', sa.String(length=64), nullable=False),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('report_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("result IN ('dry-run','commit','activation')", name='ck_ic_audit_result'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['import_id'], ['ic_imports.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['ic_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_ic_import_audits_import_id'), 'ic_import_audits', ['import_id'], unique=False)
    if 'ic_actions' not in tables:
        op.create_table('ic_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('condition_id', sa.Integer(), nullable=False),
        sa.Column('action_code', sa.String(length=60), nullable=False),
        sa.Column('action_code_raw', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('output_text', sa.Text(), nullable=False),
        sa.Column('start_raw', sa.Text(), nullable=False),
        sa.Column('due_raw', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('is_continuous', sa.Boolean(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['condition_id', 'plan_id'], ['ic_conditions.id', 'ic_conditions.plan_id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['ic_plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'action_code', name='uq_ic_action_code')
        )
        op.create_index(op.f('ix_ic_actions_condition_id'), 'ic_actions', ['condition_id'], unique=False)
        op.create_index(op.f('ix_ic_actions_plan_id'), 'ic_actions', ['plan_id'], unique=False)
    if 'ic_action_parties' not in tables:
        op.create_table('ic_action_parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('body_name', sa.Text(), nullable=True),
        sa.Column('all_departments', sa.Boolean(), nullable=False),
        sa.Column('raw_name', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.CheckConstraint("role IN ('responsible','cooperating')", name='ck_ic_party_role'),
        sa.CheckConstraint('(CASE WHEN department_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN body_name IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN all_departments THEN 1 ELSE 0 END) = 1', name='ck_ic_party_target'),
        sa.ForeignKeyConstraint(['action_id'], ['ic_actions.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_ic_action_parties_action_id'), 'ic_action_parties', ['action_id'], unique=False)
        op.create_index(op.f('ix_ic_action_parties_department_id'), 'ic_action_parties', ['department_id'], unique=False)
    for prefix, numbers in [('KOS', range(1, 5)), ('RDS', range(5, 7)), ('KFS', range(7, 13)), ('BİS', range(13, 17)), ('İS', range(17, 19))]:
        for number in numbers:
            op.get_bind().execute(sa.text('INSERT INTO ic_standards(code,component_code) VALUES (:code,:component) ON CONFLICT (code) DO NOTHING'),
                                  {'code': f'{prefix}{number}', 'component': prefix})
    install_guards()


def install_guards():
    immutable = ('ic_conditions', 'ic_actions', 'ic_action_parties', 'ic_unit_aliases', 'ic_imports', 'ic_import_audits')
    dialect = op.get_bind().dialect.name
    if dialect == 'postgresql':
        op.execute("""CREATE OR REPLACE FUNCTION ic_reject_history_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'İç kontrol geçmişi değiştirilemez; yeni sürüm yükleyin.'; END $$""")
        for table in immutable:
            op.execute(f'DROP TRIGGER IF EXISTS ic_history_guard ON {table}')
            op.execute(f'CREATE TRIGGER ic_history_guard BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION ic_reject_history_change()')
        op.execute("""CREATE OR REPLACE FUNCTION ic_plan_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'İç kontrol planı silinemez.'; END IF;
          IF (to_jsonb(NEW) - 'status') IS DISTINCT FROM (to_jsonb(OLD) - 'status')
             OR NOT ((OLD.status='draft' AND NEW.status='active') OR (OLD.status='active' AND NEW.status='archived')) THEN
            RAISE EXCEPTION 'İç kontrol planı değiştirilemez; yeni sürüm yükleyin.';
          END IF;
          RETURN NEW;
        END $$""")
        op.execute('DROP TRIGGER IF EXISTS ic_plan_guard ON ic_plans')
        op.execute('CREATE TRIGGER ic_plan_guard BEFORE UPDATE OR DELETE ON ic_plans FOR EACH ROW EXECUTE FUNCTION ic_plan_guard()')
        op.execute("""CREATE OR REPLACE FUNCTION ic_frozen_plan_insert() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target_plan integer;
        BEGIN
          IF TG_TABLE_NAME='ic_action_parties' THEN SELECT plan_id INTO target_plan FROM ic_actions WHERE id=NEW.action_id;
          ELSE target_plan := NEW.plan_id; END IF;
          IF EXISTS (SELECT 1 FROM ic_import_audits WHERE plan_id=target_plan AND result='commit') THEN
            RAISE EXCEPTION 'Kaydedilmiş plana kayıt eklenemez; yeni sürüm yükleyin.';
          END IF;
          RETURN NEW;
        END $$""")
        for table in ('ic_conditions', 'ic_actions', 'ic_action_parties'):
            op.execute(f'DROP TRIGGER IF EXISTS ic_frozen_insert ON {table}')
            op.execute(f'CREATE TRIGGER ic_frozen_insert BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION ic_frozen_plan_insert()')
    elif dialect == 'sqlite':
        for table in immutable:
            for action in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_{action.lower()}_guard BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'İç kontrol geçmişi değiştirilemez; yeni sürüm yükleyin.'); END")
        op.execute("CREATE TRIGGER IF NOT EXISTS ic_plan_delete_guard BEFORE DELETE ON ic_plans BEGIN SELECT RAISE(ABORT, 'İç kontrol planı silinemez.'); END")
        columns = [c['name'] for c in sa.inspect(op.get_bind()).get_columns('ic_plans') if c['name'] != 'status']
        changed = ' OR '.join(f'NEW.{c} IS NOT OLD.{c}' for c in columns)
        op.execute(f"""CREATE TRIGGER IF NOT EXISTS ic_plan_update_guard BEFORE UPDATE ON ic_plans
            WHEN ({changed}) OR NOT ((OLD.status='draft' AND NEW.status='active') OR (OLD.status='active' AND NEW.status='archived'))
            BEGIN SELECT RAISE(ABORT, 'İç kontrol planı değiştirilemez; yeni sürüm yükleyin.'); END""")
        for table, expr in [('ic_conditions', 'NEW.plan_id'), ('ic_actions', 'NEW.plan_id'),
                            ('ic_action_parties', '(SELECT plan_id FROM ic_actions WHERE id=NEW.action_id)')]:
            op.execute(f"""CREATE TRIGGER IF NOT EXISTS {table}_insert_guard BEFORE INSERT ON {table}
                WHEN EXISTS (SELECT 1 FROM ic_import_audits WHERE plan_id={expr} AND result='commit')
                BEGIN SELECT RAISE(ABORT, 'Kaydedilmiş plana kayıt eklenemez; yeni sürüm yükleyin.'); END""")


def downgrade():
    # Preserve imported municipal records, aliases, audit history and their guards.
    # The earlier application ignores ic_* tables. A later upgrade reuses them.
    pass
