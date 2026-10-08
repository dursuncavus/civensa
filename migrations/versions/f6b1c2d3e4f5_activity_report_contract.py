"""Add immutable indicator definitions and publication-bound activity report revisions."""
from alembic import op
import sqlalchemy as sa

revision = 'f6b1c2d3e4f5'
down_revision = 'e5a0b1c2d3e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('activity_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('current_revision', sa.Integer(), nullable=False),
    sa.Column('lock_version', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'period_id', name='uq_activity_report_org_period')
    )
    op.create_table('indicator_identities',
    sa.Column('indicator_id', sa.String(length=36), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('indicator_id')
    )
    op.create_table('indicator_definition_revisions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('indicator_id', sa.String(length=36), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('definition_json', sa.Text(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['indicator_id'], ['indicator_identities.indicator_id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['reporting_periods.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('indicator_id', 'revision', name='uq_indicator_definition_revision')
    )
    op.create_table('activity_report_revisions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('publication_id', sa.Integer(), nullable=False),
    sa.Column('publication_sha256', sa.String(length=64), nullable=False),
    sa.Column('contract_version', sa.String(length=20), nullable=False),
    sa.Column('previous_revision_id', sa.Integer(), nullable=True),
    sa.Column('diff_json', sa.Text(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['previous_revision_id'], ['activity_report_revisions.id'], ),
    sa.ForeignKeyConstraint(['publication_id'], ['publications.id'], ),
    sa.ForeignKeyConstraint(['report_id'], ['activity_reports.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_id', 'revision', name='uq_activity_report_revision')
    )
    op.create_table('publication_indicator_bindings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('publication_id', sa.Integer(), nullable=False),
    sa.Column('snapshot_indicator_id', sa.Integer(), nullable=False),
    sa.Column('definition_revision_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['definition_revision_id'], ['indicator_definition_revisions.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['publication_id'], ['publications.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('publication_id', 'snapshot_indicator_id', name='uq_publication_indicator_binding')
    )
    op.create_table('activity_report_approvals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_revision_id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['report_revision_id'], ['activity_report_revisions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_revision_id')
    )
    op.create_table('report_indicators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_revision_id', sa.Integer(), nullable=False),
    sa.Column('publication_binding_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['publication_binding_id'], ['publication_indicator_bindings.id'], ),
    sa.ForeignKeyConstraint(['report_revision_id'], ['activity_report_revisions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_revision_id', 'publication_binding_id', name='uq_report_indicator')
    )
    op.create_table('actual_revisions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_indicator_id', sa.Integer(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('supersedes_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.Numeric(precision=26, scale=6), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('state', sa.String(length=30), nullable=False),
    sa.Column('evidence_json', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('deviation_json', sa.Text(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['report_indicator_id'], ['report_indicators.id'], ),
    sa.ForeignKeyConstraint(['supersedes_id'], ['actual_revisions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_indicator_id', 'revision', name='uq_actual_revision')
    )
    with op.batch_alter_table('indicators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('persistent_indicator_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_indicator_persistent_identity', 'indicator_identities', ['persistent_indicator_id'], ['indicator_id'])
        batch_op.create_unique_constraint('uq_period_persistent_indicator', ['period_id', 'persistent_indicator_id'])
    # Also protect immutable history from bulk SQL, which bypasses ORM events.
    tables = ('publications', 'indicator_identities', 'indicator_definition_revisions',
              'publication_indicator_bindings', 'activity_report_revisions',
              'report_indicators', 'actual_revisions', 'activity_report_approvals')
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION civensa_immutable_revision() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Geçmiş sürüm değiştirilemez; yeni revizyon oluşturun.';
            END; $$ LANGUAGE plpgsql""")
        for table in tables:
            op.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} '
                       'FOR EACH ROW EXECUTE FUNCTION civensa_immutable_revision()')
    elif op.get_bind().dialect.name == 'sqlite':
        for table in tables:
            for action in ('UPDATE', 'DELETE'):
                op.execute(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} "
                           "BEGIN SELECT RAISE(ABORT, 'Geçmiş sürüm değiştirilemez; yeni revizyon oluşturun.'); END")
    # An approved report cannot gain new actuals through direct SQL either.
    frozen_actual = """SELECT 1 FROM report_indicators ri
        JOIN activity_report_revisions rr ON rr.id=ri.report_revision_id
        JOIN activity_reports r ON r.id=rr.report_id
        LEFT JOIN activity_report_approvals a ON a.report_revision_id=rr.id
        WHERE ri.id=NEW.report_indicator_id
          AND (a.id IS NOT NULL OR rr.revision <> r.current_revision)"""
    frozen_member = """SELECT 1 FROM activity_report_approvals a
        WHERE a.report_revision_id=NEW.report_revision_id"""
    for table, query in (('actual_revisions', frozen_actual), ('report_indicators', frozen_member)):
        if op.get_bind().dialect.name == 'postgresql':
            op.execute(f"""CREATE FUNCTION guard_insert_{table}() RETURNS trigger AS $$
                BEGIN IF EXISTS ({query}) THEN
                RAISE EXCEPTION 'Onaylı veya geçmiş rapora kayıt eklenemez; yeni revizyon oluşturun.';
                END IF; RETURN NEW; END; $$ LANGUAGE plpgsql""")
            op.execute(f'CREATE TRIGGER guard_insert_{table} BEFORE INSERT ON {table} '
                       f'FOR EACH ROW EXECUTE FUNCTION guard_insert_{table}()')
        elif op.get_bind().dialect.name == 'sqlite':
            op.execute(f"CREATE TRIGGER guard_insert_{table} BEFORE INSERT ON {table} WHEN EXISTS ({query}) "
                       "BEGIN SELECT RAISE(ABORT, 'Onaylı veya geçmiş rapora kayıt eklenemez; yeni revizyon oluşturun.'); END")


def downgrade():
    raise RuntimeError('Revizyon geçmişini kaybetmemek için geçiş öncesi yedeği ayrı veritabanına geri yükleyin.')
