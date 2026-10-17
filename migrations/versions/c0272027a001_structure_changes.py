"""CIV-027: period profiles and append-only institution structure decisions.

All additive schema and evidence survive downgrade; upgrade is idempotent.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c0272027a001'
down_revision = 'b0262027a001'
branch_labels = depends_on = None

TABLES = ('structure_changes', 'structure_change_links', 'structure_change_transfers', 'structure_change_cancellations')


def upgrade():
    connection = op.get_bind()
    schema = sa.inspect(connection)
    columns = {c['name'] for c in schema.get_columns('department_scopes')}
    for name, kind in [('budget_code', sa.Text()), ('active_from', sa.Date()), ('active_to', sa.Date())]:
        if name not in columns:
            op.add_column('department_scopes', sa.Column(name, kind, nullable=True))
    # Freeze existing period names before any current Department name changes.
    connection.execute(sa.text("UPDATE department_scopes SET display_name = (SELECT name FROM departments WHERE departments.id = department_scopes.department_id) WHERE display_name IS NULL OR display_name = ''"))
    if not schema.has_table('structure_changes'):
        op.create_table('structure_changes',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('change_type', sa.String(20), nullable=False),
            sa.Column('effective_date', sa.Date(), nullable=False),
            sa.Column('council_decision_no', sa.String(200), nullable=False),
            sa.Column('council_decision_date', sa.Date(), nullable=False),
            sa.Column('note', sa.Text(), nullable=False),
            sa.Column('snapshot_json', sa.Text(), nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint("change_type IN ('RENAMED','MERGED','SPLIT','CLOSED','CREATED')", name='ck_structure_change_type'))
        op.create_table('structure_change_links',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('change_id', sa.Integer(), sa.ForeignKey('structure_changes.id'), nullable=False),
            sa.Column('from_department_id', sa.Integer(), sa.ForeignKey('departments.id')),
            sa.Column('to_department_id', sa.Integer(), sa.ForeignKey('departments.id')),
            sa.CheckConstraint('from_department_id IS NOT NULL OR to_department_id IS NOT NULL', name='ck_structure_link_endpoint'))
        op.create_table('structure_change_transfers',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('change_id', sa.Integer(), sa.ForeignKey('structure_changes.id'), nullable=False),
            sa.Column('from_department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
            sa.Column('to_department_id', sa.Integer(), sa.ForeignKey('departments.id'), nullable=False),
            sa.Column('official_activity_id', sa.Integer(), sa.ForeignKey('official_activities.id')),
            sa.Column('indicator_id', sa.String(36), sa.ForeignKey('indicator_identities.indicator_id')),
            sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id')),
            sa.Column('note', sa.Text(), nullable=False),
            sa.CheckConstraint('(CASE WHEN official_activity_id IS NULL THEN 0 ELSE 1 END + CASE WHEN indicator_id IS NULL THEN 0 ELSE 1 END + CASE WHEN activity_id IS NULL THEN 0 ELSE 1 END) = 1', name='ck_structure_transfer_one_record'),
            sa.CheckConstraint('from_department_id <> to_department_id', name='ck_structure_transfer_receiver'),
            sa.UniqueConstraint('change_id', 'from_department_id', 'official_activity_id', name='uq_structure_transfer_official'),
            sa.UniqueConstraint('change_id', 'from_department_id', 'indicator_id', name='uq_structure_transfer_indicator'),
            sa.UniqueConstraint('change_id', 'from_department_id', 'activity_id', name='uq_structure_transfer_activity'))
        op.create_table('structure_change_cancellations',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('change_id', sa.Integer(), sa.ForeignKey('structure_changes.id'), nullable=False, unique=True),
            sa.Column('note', sa.Text(), nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False))
    if connection.dialect.name == 'postgresql':
        op.execute("""CREATE OR REPLACE FUNCTION civ027_immutable() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Kurum yapısı kaydı değiştirilemez veya silinemez. Kurum Yapısı ekranında gerekçeli iptal kaydı oluşturun.'; END;
            $$ LANGUAGE plpgsql""")
        for table in TABLES:
            op.execute(f'DROP TRIGGER IF EXISTS civ027_immutable ON {table}')
            op.execute(f'CREATE TRIGGER civ027_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civ027_immutable()')
    elif connection.dialect.name == 'sqlite':
        for table in TABLES:
            for operation in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER IF NOT EXISTS civ027_{table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'Kurum yapısı kaydı silinemez/değiştirilemez; gerekçeli iptal kaydı oluşturun.'); END")


def downgrade():
    # Older versions ignore additive columns/tables. Never discard decisions,
    # transfers, cancellations, names, or the guards protecting this evidence.
    pass
