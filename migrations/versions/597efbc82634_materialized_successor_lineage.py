"""S3A append-only release lineage and materialized successor assembly guard."""
from alembic import op
import sqlalchemy as sa
revision='597efbc82634'
down_revision='486dfab71523'
branch_labels=depends_on=None


def upgrade():
    op.create_table('report_release_successions',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('predecessor_release_id',sa.Integer(),sa.ForeignKey('report_releases.id'),nullable=False,unique=True),
        sa.Column('successor_release_id',sa.Integer(),sa.ForeignKey('report_releases.id'),nullable=False,unique=True),
        sa.Column('predecessor_candidate_sha256',sa.String(64),nullable=False),
        sa.Column('successor_candidate_sha256',sa.String(64),nullable=False),
        sa.Column('workflow_event_id',sa.Integer(),sa.ForeignKey('workflow_events.id'),nullable=False,unique=True),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.current_timestamp(),nullable=False),
        sa.CheckConstraint('predecessor_release_id<>successor_release_id',name='ck_release_succession_distinct'))
    if op.get_bind().dialect.name=='postgresql':
        op.execute('CREATE TRIGGER immutable_report_release_successions BEFORE UPDATE OR DELETE ON report_release_successions FOR EACH ROW EXECUTE FUNCTION civensa_auth_immutable()')
        op.execute('CREATE TRIGGER timestamp_report_release_successions BEFORE INSERT ON report_release_successions FOR EACH ROW EXECUTE FUNCTION civensa_auth_server_timestamp()')
        op.execute(LINEAGE)
        op.execute('CREATE TRIGGER release_succession_guard BEFORE INSERT ON report_release_successions FOR EACH ROW EXECUTE FUNCTION civensa_release_succession_guard()')
        op.execute("CREATE UNIQUE INDEX uq_activity_successor_release ON report_candidates ((manifest_json::jsonb->>'predecessor_release_id')) WHERE manifest_json::jsonb ? 'predecessor_release_id'")
        op.execute(ASSEMBLY)
        op.execute('CREATE TRIGGER activity_successor_guard BEFORE INSERT ON report_candidates FOR EACH ROW EXECUTE FUNCTION civensa_activity_successor_guard()')
    else:
        for action in ('UPDATE','DELETE'):
            op.execute(f"CREATE TRIGGER immutable_report_release_successions_{action.lower()} BEFORE {action} ON report_release_successions BEGIN SELECT RAISE(ABORT,'Immutable release lineage'); END")
        # Successor assembly itself requires migrated PostgreSQL, like corrections.
        op.execute("CREATE TRIGGER activity_successor_guard BEFORE INSERT ON report_candidates WHEN json_type(NEW.manifest_json,'$.predecessor_release_id') IS NOT NULL BEGIN SELECT RAISE(ABORT,'Successor requires PostgreSQL'); END")
        op.execute("CREATE TRIGGER release_succession_guard BEFORE INSERT ON report_release_successions BEGIN SELECT RAISE(ABORT,'Release lineage requires PostgreSQL'); END")


def downgrade():
    raise RuntimeError('Successor/lineage history cannot be discarded')


LINEAGE=r"""CREATE FUNCTION civensa_release_succession_guard() RETURNS trigger AS $$
DECLARE p report_releases%ROWTYPE; s report_releases%ROWTYPE;
BEGIN
 SELECT * INTO p FROM report_releases WHERE id=NEW.predecessor_release_id;
 SELECT * INTO s FROM report_releases WHERE id=NEW.successor_release_id;
 PERFORM 1 FROM organizations WHERE id=p.organization_id FOR UPDATE;
 IF p.id IS NULL OR s.id IS NULL OR p.id=s.id OR
 (p.organization_id,p.resource_scope,p.report_key,p.major) IS DISTINCT FROM (s.organization_id,s.resource_scope,s.report_key,s.major)
 OR s.minor<>p.minor+1 THEN RAISE EXCEPTION 'Invalid immediate release lineage/version'; END IF;
 IF NOT EXISTS(SELECT 1 FROM report_candidates pc JOIN report_candidates sc ON sc.id=s.candidate_id
 JOIN workflow_events e ON e.id=s.workflow_event_id
 WHERE pc.id=p.candidate_id AND sc.predecessor_candidate_id=pc.id
 AND pc.sha256=NEW.predecessor_candidate_sha256 AND sc.sha256=NEW.successor_candidate_sha256
 AND sc.manifest_json::jsonb->>'predecessor_release_id'=p.id::text
 AND sc.manifest_json::jsonb->>'predecessor_candidate_sha256'=pc.sha256
 AND NEW.workflow_event_id=s.workflow_event_id AND e.resource_type='report_candidate' AND e.resource_id=sc.id::text
 AND e.event_type='publish_report') THEN RAISE EXCEPTION 'Release lineage provenance mismatch'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


ASSEMBLY=r"""CREATE FUNCTION civensa_activity_successor_guard() RETURNS trigger AS $$
DECLARE m jsonb; p report_releases%ROWTYPE; pc report_candidates%ROWTYPE; source activity_report_revisions%ROWTYPE; dst activity_report_revisions%ROWTYPE; b jsonb; old jsonb; cy revision_correction_cycles%ROWTYPE; pkg directorate_packages%ROWTYPE;
BEGIN
 m=NEW.manifest_json::jsonb;
 IF NOT (m ? 'predecessor_release_id') THEN RETURN NEW; END IF;
 SELECT * INTO p FROM report_releases WHERE id=(m->>'predecessor_release_id')::integer;
 PERFORM 1 FROM organizations WHERE id=p.organization_id FOR UPDATE;
 SELECT * INTO pc FROM report_candidates WHERE id=p.candidate_id;
 SELECT * INTO source FROM activity_report_revisions WHERE id=pc.activity_revision_id;
 SELECT * INTO dst FROM activity_report_revisions WHERE id=NEW.activity_revision_id;
 IF p.id IS NULL OR NEW.resource_scope<>'activity_report' OR NOT civensa_revision_current(p.id)
 OR (NEW.organization_id,NEW.resource_scope,NEW.report_key,NEW.period_id) IS DISTINCT FROM (pc.organization_id,pc.resource_scope,pc.report_key,pc.period_id)
 OR NEW.predecessor_candidate_id IS DISTINCT FROM pc.id OR NEW.sequence<>pc.sequence+1
 OR m->>'successor_contract' IS DISTINCT FROM 'materialized-successor-1'
 OR m->>'predecessor_candidate_sha256' IS DISTINCT FROM pc.sha256
 OR m->'source_id' IS DISTINCT FROM pc.manifest_json::jsonb->'source_id'
 OR m->'required_department_ids' IS DISTINCT FROM pc.manifest_json::jsonb->'required_department_ids'
 OR dst.previous_revision_id IS DISTINCT FROM source.id OR dst.report_id IS DISTINCT FROM source.report_id OR dst.revision<>source.revision+1
 OR dst.publication_id IS DISTINCT FROM source.publication_id OR dst.publication_sha256 IS DISTINCT FROM source.publication_sha256
 OR NEW.payload_json::jsonb->>'schema_version' IS DISTINCT FROM 'activity-candidate-1'
 OR jsonb_typeof(m->'correction_cycle_ids') IS DISTINCT FROM 'array' OR jsonb_array_length(m->'correction_cycle_ids')=0
 OR jsonb_array_length(m->'packages')<>jsonb_array_length(pc.manifest_json::jsonb->'packages')
 OR jsonb_array_length(m->'packages')<>(SELECT count(DISTINCT value->>'package_id') FROM jsonb_array_elements(m->'packages'))
 OR m->'correction_cycle_ids' IS DISTINCT FROM (SELECT jsonb_agg(id ORDER BY id) FROM revision_correction_cycles WHERE source_release_id=p.id)
 THEN RAISE EXCEPTION 'Invalid/current materialized successor predecessor'; END IF;
 FOR b IN SELECT value FROM jsonb_array_elements(m->'packages') LOOP
   SELECT value INTO old FROM jsonb_array_elements(pc.manifest_json::jsonb->'packages') WHERE value->'package_id'=b->'package_id';
   SELECT * INTO pkg FROM directorate_packages WHERE id=(b->>'package_id')::integer;
   PERFORM 1 FROM departments WHERE id=pkg.department_id FOR UPDATE;
   PERFORM 1 FROM directorate_packages WHERE id=pkg.id FOR UPDATE;
   IF old IS NULL OR old->'department_id' IS DISTINCT FROM b->'department_id' OR pkg.state<>'strategy_approved'
   OR NOT EXISTS(SELECT 1 FROM package_revisions r JOIN package_decisions d ON d.id=(b->>'decision_id')::integer
   JOIN workflow_events e ON e.id=d.workflow_event_id
   WHERE r.id=(b->>'revision_id')::integer AND r.package_id=pkg.id AND r.revision=pkg.current_revision
   AND r.sha256=b->>'sha256' AND d.package_revision_id=r.id AND d.snapshot_sha256=r.sha256 AND d.action='strategy_approve'
   AND e.id=(b->>'strategy_event_id')::integer AND e.context_json::jsonb->>'revision_id'=r.id::text AND e.context_json::jsonb->>'sha256'=r.sha256)
   THEN RAISE EXCEPTION 'Successor exact approved package mismatch'; END IF;
   SELECT * INTO cy FROM revision_correction_cycles WHERE source_release_id=p.id AND package_id=pkg.id;
   IF cy.id IS NULL AND old IS DISTINCT FROM b
   OR cy.id IS NOT NULL AND (cy.source_package_revision_id<>(old->>'revision_id')::integer OR NOT m->'correction_cycle_ids' @> jsonb_build_array(cy.id))
   THEN RAISE EXCEPTION 'Successor correction provenance mismatch'; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states st ON st.request_id=r.id
 LEFT JOIN revision_edit_grants g ON g.request_id=r.id LEFT JOIN revision_correction_cycles pending_cycle ON pending_cycle.id=g.cycle_id
 LEFT JOIN directorate_packages pending_package ON pending_package.id=pending_cycle.package_id
 WHERE r.source_release_id=p.id AND st.state IN ('requested','accepted','editing')
 AND (st.state<>'editing' OR pending_cycle.id IS NULL OR pending_package.state<>'strategy_approved' OR NOT m->'correction_cycle_ids' @> jsonb_build_array(pending_cycle.id)))
 THEN RAISE EXCEPTION 'Other predecessor correction work is not ready'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""
