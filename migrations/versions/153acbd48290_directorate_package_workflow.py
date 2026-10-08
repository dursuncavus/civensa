"""Disabled Phase 3 package snapshots and decision history (additive only)."""
from alembic import op
import sqlalchemy as sa
revision = '153acbd48290'
down_revision = '0429caba7123'
branch_labels = depends_on = None


def upgrade():
    op.create_table('directorate_packages',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('organization_id',sa.Integer(),sa.ForeignKey('organizations.id'),nullable=False),
        sa.Column('department_id',sa.Integer(),sa.ForeignKey('departments.id'),nullable=False),
        sa.Column('resource_scope',sa.String(30),nullable=False),
        sa.Column('period_id',sa.Integer(),sa.ForeignKey('reporting_periods.id'),nullable=False),
        sa.Column('report_revision_id',sa.Integer(),sa.ForeignKey('activity_report_revisions.id'),nullable=True),
        sa.Column('source_key',sa.String(100),nullable=False),
        sa.Column('state',sa.String(30),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),sa.Column('current_revision',sa.Integer(),nullable=False),
        sa.UniqueConstraint('department_id','resource_scope','source_key',name='uq_directorate_package_source'),
        sa.CheckConstraint("resource_scope IN ('performance_program','activity_report')",name='ck_package_scope'),
        sa.CheckConstraint("state IN ('draft','returned','director_review','strategy_review','strategy_approved')",name='ck_package_state'),
        sa.CheckConstraint("(resource_scope='performance_program' AND report_revision_id IS NULL) OR (resource_scope='activity_report' AND report_revision_id IS NOT NULL)",name='ck_package_source'))
    op.create_table('package_revisions',
        sa.Column('id',sa.Integer(),primary_key=True),sa.Column('package_id',sa.Integer(),sa.ForeignKey('directorate_packages.id'),nullable=False),
        sa.Column('revision',sa.Integer(),nullable=False),sa.Column('previous_revision_id',sa.Integer(),sa.ForeignKey('package_revisions.id'),nullable=True),
        sa.Column('content_json',sa.Text(),nullable=False),sa.Column('sha256',sa.String(64),nullable=False),
        sa.Column('created_by',sa.Integer(),sa.ForeignKey('users.id'),nullable=False),sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.current_timestamp(),nullable=False),
        sa.UniqueConstraint('package_id','revision',name='uq_package_revision'))
    op.create_table('package_decisions',
        sa.Column('id',sa.Integer(),primary_key=True),sa.Column('package_revision_id',sa.Integer(),sa.ForeignKey('package_revisions.id'),nullable=False),
        sa.Column('snapshot_sha256',sa.String(64),nullable=False),sa.Column('action',sa.String(40),nullable=False),
        sa.Column('from_state',sa.String(30),nullable=False),sa.Column('to_state',sa.String(30),nullable=False),
        sa.Column('workflow_event_id',sa.Integer(),sa.ForeignKey('workflow_events.id'),nullable=False,unique=True),
        sa.Column('delegation_id',sa.Integer(),sa.ForeignKey('authority_delegations.id'),nullable=True),
        sa.CheckConstraint("action IN ('submit_to_director','director_approve','director_return','director_reopen','strategy_approve','strategy_return')",name='ck_package_decision_action'))
    if op.get_bind().dialect.name=='postgresql':
        for table in ('package_revisions','package_decisions'):
            op.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civensa_auth_immutable()')
        op.execute('CREATE TRIGGER timestamp_package_revisions BEFORE INSERT ON package_revisions FOR EACH ROW EXECUTE FUNCTION civensa_auth_server_timestamp()')
        op.execute("""CREATE FUNCTION civensa_package_identity() RETURNS trigger AS $$
        BEGIN
          IF TG_OP='DELETE' OR (to_jsonb(OLD)-ARRAY['state','version','current_revision']) IS DISTINCT FROM
            (to_jsonb(NEW)-ARRAY['state','version','current_revision']) OR NEW.version<>OLD.version+1
            OR NEW.current_revision NOT IN (OLD.current_revision,OLD.current_revision+1) THEN
            RAISE EXCEPTION 'Package identity/history cannot be overwritten';
          END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql""")
        op.execute('CREATE TRIGGER package_identity BEFORE UPDATE OR DELETE ON directorate_packages FOR EACH ROW EXECUTE FUNCTION civensa_package_identity()')
        op.execute("""CREATE FUNCTION civensa_package_decision_binding() RETURNS trigger AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM package_revisions r JOIN workflow_events e ON e.id=NEW.workflow_event_id
            WHERE r.id=NEW.package_revision_id AND r.sha256=NEW.snapshot_sha256
              AND e.resource_type='directorate_package' AND e.resource_id=r.package_id::text
              AND e.event_type=NEW.action) THEN RAISE EXCEPTION 'Decision snapshot/event binding mismatch'; END IF;
          RETURN NEW;
        END; $$ LANGUAGE plpgsql""")
        op.execute('CREATE TRIGGER package_decision_binding BEFORE INSERT ON package_decisions FOR EACH ROW EXECUTE FUNCTION civensa_package_decision_binding()')
    else:
        for table in ('package_revisions','package_decisions'):
            for action in ('UPDATE','DELETE'):
                op.execute(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Immutable package history'); END")
        op.execute("""CREATE TRIGGER package_identity BEFORE UPDATE ON directorate_packages WHEN
            NEW.organization_id<>OLD.organization_id OR NEW.department_id<>OLD.department_id OR NEW.resource_scope<>OLD.resource_scope
            OR NEW.period_id<>OLD.period_id OR NEW.report_revision_id IS NOT OLD.report_revision_id OR NEW.source_key<>OLD.source_key
            OR NEW.version<>OLD.version+1 OR NEW.current_revision NOT IN (OLD.current_revision,OLD.current_revision+1)
            BEGIN SELECT RAISE(ABORT,'Immutable package identity'); END""")
        op.execute("CREATE TRIGGER package_delete BEFORE DELETE ON directorate_packages BEGIN SELECT RAISE(ABORT,'Immutable package history'); END")
        op.execute("""CREATE TRIGGER package_decision_binding BEFORE INSERT ON package_decisions WHEN NOT EXISTS
            (SELECT 1 FROM package_revisions r JOIN workflow_events e ON e.id=NEW.workflow_event_id
             WHERE r.id=NEW.package_revision_id AND r.sha256=NEW.snapshot_sha256 AND e.resource_type='directorate_package'
             AND e.resource_id=CAST(r.package_id AS TEXT) AND e.event_type=NEW.action)
            BEGIN SELECT RAISE(ABORT,'Decision snapshot/event binding mismatch'); END""")


def downgrade():
    raise RuntimeError('Package history cannot be discarded; use a reviewed forward migration.')
