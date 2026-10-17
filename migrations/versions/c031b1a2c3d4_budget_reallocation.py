"""CIV-031 audited budget reallocation (additive, non-destructive rollback)."""
from alembic import op
import sqlalchemy as sa

revision = 'c031b1a2c3d4'
down_revision = 'b0262027a001'
branch_labels = depends_on = None


def upgrade():
    bind = op.get_bind()
    if 'contract_bound' not in {c['name'] for c in sa.inspect(bind).get_columns('activities')}:
        op.add_column('activities', sa.Column('contract_bound', sa.Boolean(), nullable=False, server_default=sa.false()))
    if 'authority_kind' not in {c['name'] for c in sa.inspect(bind).get_columns('authority_delegations')}:
        op.add_column('authority_delegations', sa.Column('authority_kind', sa.String(40), nullable=False, server_default='director_approval'))
    if 'budget_operations' not in sa.inspect(bind).get_table_names():
        op.create_table('budget_operations',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
            sa.Column('period_id', sa.Integer(), sa.ForeignKey('reporting_periods.id'), nullable=False),
            sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('delegation_id', sa.Integer(), sa.ForeignKey('authority_delegations.id'), nullable=True),
            sa.Column('reverses_id', sa.Integer(), sa.ForeignKey('budget_operations.id'), nullable=True, unique=True),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('value_kind', sa.String(50), nullable=False),
            sa.Column('phase', sa.String(30), nullable=False),
            sa.Column('reference_type', sa.String(50), nullable=False),
            sa.Column('reference_date', sa.String(10), nullable=False),
            sa.Column('reference_number', sa.String(100), nullable=False),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('request_json', sa.Text(), nullable=False),
            sa.Column('preview_json', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        op.create_table('budget_operation_lines',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('operation_id', sa.Integer(), sa.ForeignKey('budget_operations.id'), nullable=False),
            sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
            sa.Column('value_table', sa.String(30), nullable=False),
            sa.Column('value_id', sa.Integer(), nullable=False),
            sa.Column('label', sa.Text(), nullable=False),
            sa.Column('funding_type', sa.String(30), nullable=False),
            sa.Column('before', sa.Numeric(22, 2), nullable=False),
            sa.Column('after', sa.Numeric(22, 2), nullable=False),
            sa.Column('before_json', sa.Text(), nullable=False),
            sa.Column('after_json', sa.Text(), nullable=False))
        op.create_index('ix_budget_operation_lines_operation_id', 'budget_operation_lines', ['operation_id'])
    if bind.dialect.name == 'postgresql':
        op.execute("""CREATE OR REPLACE FUNCTION civensa_budget_immutable() RETURNS trigger AS $$
          BEGIN RAISE EXCEPTION 'Bütçe aktarma geçmişi değiştirilemez; yeni telafi işlemi oluşturun.'; END;
          $$ LANGUAGE plpgsql""")
        for table in ('budget_operations', 'budget_operation_lines'):
            op.execute(f'DROP TRIGGER IF EXISTS immutable_{table} ON {table}')
            op.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civensa_budget_immutable()')
        # Existing package authority guards must never interpret a correction-only
        # grant as a director approval delegation. Retain all other guard logic.
        definitions = bind.execute(sa.text("SELECT p.oid, pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=current_schema() AND p.proname LIKE 'civensa_%' AND p.prokind='f'")).all()
        for _, definition in definitions:
            updated = definition.replace('authority_delegations a WHERE a.organization_id', "authority_delegations a WHERE a.authority_kind='director_approval' AND a.organization_id")
            updated = updated.replace('WHERE a.department_id=p.department_id', "WHERE a.authority_kind='director_approval' AND a.department_id=p.department_id")
            updated = updated.replace('WHERE a.id=d.delegation_id', "WHERE a.authority_kind='director_approval' AND a.id=d.delegation_id")
            if updated != definition:
                op.execute(updated)
        # Base runtime grants are intentionally restricted. New history is append-only.
        for role in ('civensa_app',):
            if bind.execute(sa.text('SELECT 1 FROM pg_roles WHERE rolname=:role'), {'role': role}).first():
                op.execute(f'GRANT SELECT, INSERT ON budget_operations, budget_operation_lines TO {role}')
                op.execute(f'GRANT USAGE, SELECT ON SEQUENCE budget_operations_id_seq, budget_operation_lines_id_seq TO {role}')
    else:
        for table in ('budget_operations', 'budget_operation_lines'):
            for action in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'Bütçe aktarma geçmişi değiştirilemez.'); END")
        for name, definition in bind.execute(sa.text("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%authority_delegations%'")).all():
            updated = definition.replace('authority_delegations a WHERE a.organization_id', "authority_delegations a WHERE a.authority_kind='director_approval' AND a.organization_id")
            updated = updated.replace('WHERE a.id=d.delegation_id', "WHERE a.authority_kind='director_approval' AND a.id=d.delegation_id")
            if updated != definition:
                op.execute(f'DROP TRIGGER "{name}"')
                op.execute(updated)
        # SQLite's old grant guard enumerates columns instead of comparing JSON.
        op.execute("""CREATE TRIGGER IF NOT EXISTS guard_delegation_kind BEFORE UPDATE ON authority_delegations
          WHEN NEW.authority_kind <> OLD.authority_kind BEGIN SELECT RAISE(ABORT, 'Yetki devri türü değiştirilemez.'); END""")


def downgrade():
    # Keep amounts, flags, grants, audit records, triggers and columns. A code
    # rollback cannot discard financial evidence. Re-upgrade is idempotent.
    pass
