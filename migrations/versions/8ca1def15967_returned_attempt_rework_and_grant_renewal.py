"""S3C-2 immutable returned attempts, explicit rework and grant renewal."""
from alembic import op
import sqlalchemy as sa
revision='8ca1def15967'
down_revision='7b90cde04856'
branch_labels=depends_on=None


def upgrade():
    op.create_table('revision_edit_grant_renewals',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('original_grant_id',sa.Integer(),sa.ForeignKey('revision_edit_grants.id'),nullable=False),
        sa.Column('request_id',sa.Integer(),sa.ForeignKey('revision_requests.id'),nullable=False),
        sa.Column('cycle_id',sa.Integer(),sa.ForeignKey('revision_correction_cycles.id'),nullable=False),
        sa.Column('source_release_id',sa.Integer(),sa.ForeignKey('report_releases.id'),nullable=False),
        sa.Column('paths_json',sa.Text(),nullable=False),
        sa.Column('start_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('end_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('created_by',sa.Integer(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('workflow_event_id',sa.Integer(),sa.ForeignKey('workflow_events.id'),nullable=False,unique=True),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.current_timestamp(),nullable=False),
        sa.CheckConstraint('start_at<end_at',name='ck_renewal_time'),sa.CheckConstraint('length(trim(reason))>0',name='ck_renewal_reason'))
    with op.batch_alter_table('package_decisions') as batch:
        batch.drop_constraint('ck_package_decision_action',type_='check')
        batch.create_check_constraint('ck_package_decision_action',"action IN ('submit_to_director','director_approve','director_return','director_reopen','strategy_approve','strategy_return','strategy_reopen')")
    if op.get_bind().dialect.name=='postgresql':
        op.execute(HELPERS)
        op.execute(RENEWAL)
        op.execute('CREATE TRIGGER immutable_revision_edit_grant_renewals BEFORE UPDATE OR DELETE ON revision_edit_grant_renewals FOR EACH ROW EXECUTE FUNCTION civensa_auth_immutable()')
        op.execute('CREATE TRIGGER renewal_guard BEFORE INSERT ON revision_edit_grant_renewals FOR EACH ROW EXECUTE FUNCTION civensa_renewal_guard()')
        op.execute('DROP INDEX uq_activity_successor_release')
        op.execute("CREATE UNIQUE INDEX uq_activity_successor_first ON report_candidates ((manifest_json::jsonb->>'predecessor_release_id')) WHERE manifest_json::jsonb ? 'predecessor_release_id' AND NOT manifest_json::jsonb ? 'reworks_candidate_id'")
        op.execute("CREATE UNIQUE INDEX uq_activity_successor_rework ON report_candidates ((manifest_json::jsonb->>'reworks_candidate_id')) WHERE manifest_json::jsonb ? 'reworks_candidate_id'")
        for sql in (ASSEMBLY,AUTHORITY,PROJECTION,EDIT,COMPLETION,PARTICIPATES,PUBLICATION):op.execute(sql)
        op.execute(FREEZE)
        op.execute(REOPEN_DECISION)
        op.execute('CREATE TRIGGER strategy_reopen_decision_guard BEFORE INSERT ON package_decisions FOR EACH ROW EXECUTE FUNCTION civensa_strategy_reopen_decision_guard()')
        op.execute('CREATE TRIGGER correction_cycle_live_guard BEFORE INSERT ON revision_correction_cycles FOR EACH ROW EXECUTE FUNCTION civensa_correction_live_guard()')
        op.execute('CREATE TRIGGER correction_grant_live_guard BEFORE INSERT ON revision_edit_grants FOR EACH ROW EXECUTE FUNCTION civensa_correction_live_guard()')
        op.execute(STATE_INSERT)
        op.execute('CREATE TRIGGER report_state_initial_guard BEFORE INSERT ON report_candidate_states FOR EACH ROW EXECUTE FUNCTION civensa_report_state_initial_guard()')
    else:
        for action in ('UPDATE','DELETE'):
            op.execute(f"CREATE TRIGGER immutable_renewals_{action.lower()} BEFORE {action} ON revision_edit_grant_renewals BEGIN SELECT RAISE(ABORT,'Immutable renewal history'); END")
        op.execute("CREATE TRIGGER renewal_guard BEFORE INSERT ON revision_edit_grant_renewals BEGIN SELECT RAISE(ABORT,'Renewal requires PostgreSQL'); END")
        op.execute("CREATE TRIGGER strategy_reopen_decision_guard BEFORE INSERT ON package_decisions WHEN NEW.action='strategy_reopen' BEGIN SELECT RAISE(ABORT,'Reopen requires PostgreSQL'); END")
        op.execute("CREATE TRIGGER report_state_initial_guard BEFORE INSERT ON report_candidate_states WHEN NEW.state<>'assembling' OR NEW.version<>0 BEGIN SELECT RAISE(ABORT,'Invalid initial candidate state'); END")


def downgrade():
    raise RuntimeError('Returned attempt and renewal history cannot be discarded')


HELPERS=r"""CREATE FUNCTION civensa_live_successor(rid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM report_candidates c JOIN report_candidate_states s ON s.candidate_id=c.id
 WHERE c.manifest_json::jsonb->>'predecessor_release_id'=rid::text AND s.state IN ('assembling','final_review','final_approved'));
$$ LANGUAGE sql VOLATILE;
CREATE FUNCTION civensa_returned_attempt(cid integer,rid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM report_candidates c JOIN report_candidate_states s ON s.candidate_id=c.id
 JOIN report_decisions d ON d.candidate_id=c.id JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE c.id=cid AND c.manifest_json::jsonb->>'predecessor_release_id'=rid::text AND s.state='returned_to_strategy'
 AND d.action='final_return' AND d.candidate_sha256=c.sha256 AND e.event_type='final_return'
 AND e.resource_type='report_candidate' AND e.resource_id=c.id::text AND e.organization_id=c.organization_id
 AND e.context_json::jsonb->>'sha256'=c.sha256 AND length(trim(e.reason))>0);
$$ LANGUAGE sql VOLATILE;
CREATE FUNCTION civensa_latest_returned(rid integer) RETURNS boolean AS $$
 SELECT civensa_returned_attempt((SELECT c.id FROM report_candidates c JOIN report_releases r ON r.id=rid
 WHERE (c.organization_id,c.resource_scope,c.report_key)=(r.organization_id,r.resource_scope,r.report_key)
 ORDER BY c.sequence DESC LIMIT 1),rid);
$$ LANGUAGE sql VOLATILE;
CREATE FUNCTION civensa_grant_paths(gid integer) RETURNS text AS $$
 SELECT CASE WHEN g.start_at<=clock_timestamp() AND clock_timestamp()<g.end_at THEN g.paths_json ELSE
 (SELECT n.paths_json FROM revision_edit_grant_renewals n WHERE n.original_grant_id=g.id
 AND n.start_at<=clock_timestamp() AND clock_timestamp()<n.end_at ORDER BY n.id DESC LIMIT 1) END
 FROM revision_edit_grants g WHERE g.id=gid;
$$ LANGUAGE sql VOLATILE;"""

RENEWAL=r"""CREATE FUNCTION civensa_renewal_guard() RETURNS trigger AS $$
DECLARE g revision_edit_grants%ROWTYPE; r revision_requests%ROWTYPE;
BEGIN
 SELECT * INTO r FROM revision_requests WHERE id=NEW.request_id;
 PERFORM 1 FROM organizations WHERE id=r.organization_id FOR UPDATE;
 SELECT * INTO g FROM revision_edit_grants WHERE id=NEW.original_grant_id;
 IF g.id IS NULL OR (NEW.request_id,NEW.cycle_id,NEW.source_release_id) IS DISTINCT FROM (g.request_id,g.cycle_id,g.source_release_id)
 OR g.end_at>clock_timestamp() OR NOT civensa_revision_current(g.source_release_id) OR NOT civensa_latest_returned(g.source_release_id)
 OR NOT EXISTS(SELECT 1 FROM revision_request_states s JOIN revision_correction_cycles c ON c.id=g.cycle_id
 JOIN directorate_packages p ON p.id=c.package_id WHERE s.request_id=r.id AND s.state='editing'
 AND p.state IN ('returned','director_review','strategy_review','strategy_approved') AND c.source_release_id=g.source_release_id)
 THEN RAISE EXCEPTION 'Renewal source/request/cycle is not reworkable'; END IF;
 IF jsonb_typeof(NEW.paths_json::jsonb) IS DISTINCT FROM 'array' OR jsonb_array_length(NEW.paths_json::jsonb)=0
 OR jsonb_array_length(NEW.paths_json::jsonb)<>(SELECT count(DISTINCT value) FROM jsonb_array_elements(NEW.paths_json::jsonb))
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(NEW.paths_json::jsonb) p WHERE NOT g.paths_json::jsonb @> jsonb_build_array(p))
 THEN RAISE EXCEPTION 'Renewal cannot broaden primary grant'; END IF;
 IF EXISTS(SELECT 1 FROM revision_edit_grant_renewals n WHERE n.original_grant_id=g.id
 AND n.start_at<NEW.end_at AND NEW.start_at<n.end_at) OR civensa_grant_paths(g.id) IS NOT NULL
 THEN RAISE EXCEPTION 'Renewal overlaps active authority'; END IF;
 IF NOT EXISTS(SELECT 1 FROM workflow_events e JOIN users u ON u.id=e.actor_user_id
 WHERE e.id=NEW.workflow_event_id AND e.event_type='correction_grant_renewed' AND u.is_active AND u.role='strategy'
 AND e.actor_user_id=NEW.created_by AND e.organization_id=r.organization_id AND e.department_id=r.department_id
 AND e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.reason=NEW.reason
 AND e.context_json::jsonb->>'original_grant_id'=g.id::text AND e.context_json::jsonb->>'cycle_id'=g.cycle_id::text
 AND e.context_json::jsonb->>'source_release_id'=g.source_release_id::text AND e.context_json::jsonb->>'request_id'=r.id::text
 AND e.context_json::jsonb->'paths'=NEW.paths_json::jsonb
 AND (e.context_json::jsonb->>'start_at')::timestamptz=NEW.start_at AND (e.context_json::jsonb->>'end_at')::timestamptz=NEW.end_at)
 THEN RAISE EXCEPTION 'Missing exact Strategy renewal audit'; END IF;
 NEW.created_at=clock_timestamp(); RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

ASSEMBLY=r"""CREATE OR REPLACE FUNCTION civensa_activity_successor_guard() RETURNS trigger AS $$
DECLARE m jsonb; p report_releases%ROWTYPE; pc report_candidates%ROWTYPE; source activity_report_revisions%ROWTYPE; dst activity_report_revisions%ROWTYPE; attempt report_candidates%ROWTYPE; b jsonb; old jsonb; cy revision_correction_cycles%ROWTYPE; pkg directorate_packages%ROWTYPE;
BEGIN
 m=NEW.manifest_json::jsonb;
 IF NOT (m ? 'predecessor_release_id') THEN RETURN NEW; END IF;
 SELECT * INTO p FROM report_releases WHERE id=(m->>'predecessor_release_id')::integer;
 PERFORM 1 FROM organizations WHERE id=p.organization_id FOR UPDATE;
 SELECT * INTO pc FROM report_candidates WHERE id=p.candidate_id;
 SELECT * INTO source FROM activity_report_revisions WHERE id=pc.activity_revision_id;
 SELECT * INTO dst FROM activity_report_revisions WHERE id=NEW.activity_revision_id;
 SELECT * INTO attempt FROM report_candidates WHERE (organization_id,resource_scope,report_key)=(pc.organization_id,pc.resource_scope,pc.report_key) ORDER BY sequence DESC LIMIT 1;
 IF m ? 'reworks_candidate_id' THEN
 IF attempt.id IS DISTINCT FROM (m->>'reworks_candidate_id')::integer OR NOT civensa_returned_attempt(attempt.id,p.id)
 OR m->>'reworks_candidate_sha256' IS DISTINCT FROM attempt.sha256 THEN RAISE EXCEPTION 'Invalid latest returned rework attempt'; END IF;
 SELECT * INTO source FROM activity_report_revisions WHERE id=attempt.activity_revision_id;
 ELSIF attempt.id IS DISTINCT FROM pc.id OR m ? 'reworks_candidate_sha256' THEN RAISE EXCEPTION 'Successor attempt already exists'; END IF;
 IF NOT EXISTS(SELECT 1 FROM activity_reports WHERE id=source.report_id AND current_revision=dst.revision)
 OR EXISTS(SELECT 1 FROM activity_report_revisions WHERE report_id=source.report_id AND revision>dst.revision)
 THEN RAISE EXCEPTION 'Unrelated Activity revision after returned attempt'; END IF;
 IF p.id IS NULL OR NEW.resource_scope<>'activity_report' OR NOT civensa_revision_current(p.id)
 OR (NEW.organization_id,NEW.resource_scope,NEW.report_key,NEW.period_id) IS DISTINCT FROM (pc.organization_id,pc.resource_scope,pc.report_key,pc.period_id)
 OR NEW.predecessor_candidate_id IS DISTINCT FROM pc.id OR NEW.sequence<>attempt.sequence+1
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

AUTHORITY=r"""CREATE OR REPLACE FUNCTION civensa_correction_decision_authorized(did integer,pid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 JOIN package_revisions r ON r.id=d.package_revision_id JOIN directorate_packages p ON p.id=r.package_id
 JOIN users u ON u.id=e.actor_user_id
 WHERE d.id=did AND p.id=pid AND r.revision=p.current_revision AND d.from_state=p.state
 AND r.sha256=encode(sha256(convert_to(r.content_json,'UTF8')),'hex') AND d.snapshot_sha256=r.sha256
 AND e.organization_id=p.organization_id AND e.department_id=p.department_id AND u.is_active
 AND e.context_json::jsonb->>'from_state'=d.from_state AND e.context_json::jsonb->>'to_state'=d.to_state
 AND e.context_json::jsonb->>'delegation_id' IS NOT DISTINCT FROM d.delegation_id::text
 AND ((d.action IN ('strategy_approve','strategy_return','strategy_reopen') AND u.role='strategy' AND d.delegation_id IS NULL)
 OR (u.role='department' AND u.department_id=p.department_id
 AND EXISTS(SELECT 1 FROM directorate_memberships m WHERE m.user_id=u.id AND m.active
 AND m.organization_id=p.organization_id AND m.department_id=p.department_id
 AND m.role_code IN ('department_editor','department_director'))
 AND EXISTS(SELECT 1 FROM directorate_memberships dm JOIN users du ON du.id=dm.user_id
 WHERE dm.organization_id=p.organization_id AND dm.department_id=p.department_id AND dm.active
 AND dm.role_code='department_director' AND du.is_active
 AND ((d.action='submit_to_director' AND d.delegation_id IS NULL)
 OR (d.action IN ('director_approve','director_return','director_reopen')
 AND ((d.delegation_id IS NULL AND dm.user_id=u.id AND NOT EXISTS(
 SELECT 1 FROM authority_delegations a WHERE a.organization_id=p.organization_id AND a.department_id=p.department_id
 AND a.active AND a.start_at<=clock_timestamp() AND clock_timestamp()<a.end_at
 AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id)))
 OR EXISTS(SELECT 1 FROM authority_delegations a JOIN directorate_memberships m ON m.id=a.delegate_membership_id
 WHERE a.id=d.delegation_id AND a.organization_id=p.organization_id AND a.department_id=p.department_id
 AND a.director_membership_id=dm.id AND a.active AND a.start_at<=clock_timestamp() AND clock_timestamp()<a.end_at
 AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id)
 AND m.active AND m.user_id=u.id AND m.organization_id=p.organization_id AND m.department_id=p.department_id AND m.role_code='department_editor'))))))))
$$ LANGUAGE sql VOLATILE;"""

PROJECTION=r"""CREATE OR REPLACE FUNCTION civensa_revision_projection_guard() RETURNS trigger AS $$
DECLARE c revision_correction_cycles%ROWTYPE; prior package_revisions%ROWTYPE; next package_revisions%ROWTYPE;
BEGIN
 SELECT * INTO c FROM revision_correction_cycles WHERE package_id=OLD.id ORDER BY id DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;
 PERFORM 1 FROM organizations WHERE id=OLD.organization_id FOR UPDATE;
 IF NOT civensa_revision_current(c.source_release_id) THEN
 SELECT * INTO prior FROM package_revisions WHERE package_id=OLD.id AND revision=OLD.current_revision;
 SELECT * INTO next FROM package_revisions WHERE package_id=OLD.id AND revision=NEW.current_revision;
 IF OLD.state='strategy_approved' AND NEW.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND next.previous_revision_id=prior.id AND next.content_json=prior.content_json AND next.sha256=prior.sha256
 AND NOT civensa_live_successor(c.source_release_id) AND civensa_latest_returned(c.source_release_id)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.action='strategy_reopen' AND d.from_state=OLD.state AND d.to_state=NEW.state
 AND civensa_correction_decision_authorized(d.id,OLD.id) AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.current_revision::text
 AND length(trim(e.reason))>0) THEN RETURN NEW; END IF;
 IF OLD.state='strategy_approved' AND NEW.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND NEW.version=OLD.version+1 AND next.previous_revision_id=prior.id
 AND civensa_correction_opening_release(next.package_id,next.previous_revision_id,next.revision,next.content_json,next.sha256,next.created_by) IS NOT NULL
 THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Stale correction cycle';
 END IF;
 SELECT * INTO prior FROM package_revisions WHERE package_id=OLD.id AND revision=OLD.current_revision;
 SELECT * INTO next FROM package_revisions WHERE package_id=OLD.id AND revision=NEW.current_revision;
 IF OLD.state='strategy_approved' AND NEW.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND next.previous_revision_id=prior.id AND next.content_json=prior.content_json AND next.sha256=prior.sha256
 AND NOT civensa_live_successor(c.source_release_id) AND civensa_latest_returned(c.source_release_id)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.action='strategy_reopen' AND d.from_state=OLD.state AND d.to_state=NEW.state
 AND civensa_correction_decision_authorized(d.id,OLD.id) AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.current_revision::text
 AND length(trim(e.reason))>0) THEN RETURN NEW; END IF;
 IF NEW.state='returned' AND OLD.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND next.previous_revision_id=prior.id AND next.content_json<>prior.content_json THEN RETURN NEW; END IF;
 IF NOT EXISTS(SELECT 1 FROM revision_edit_grants g JOIN revision_request_states s ON s.request_id=g.request_id
 WHERE g.cycle_id=c.id AND s.state='editing' AND civensa_grant_paths(g.id) IS NOT NULL)
 THEN RAISE EXCEPTION 'No active correction grant'; END IF;
 IF NOT EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.snapshot_sha256=prior.sha256
 AND d.from_state=OLD.state AND d.to_state=NEW.state
 AND civensa_correction_decision_authorized(d.id,OLD.id)
 AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text
 AND e.context_json::jsonb->>'revision_id'=prior.id::text AND e.context_json::jsonb->>'sha256'=prior.sha256
 AND ((d.action='submit_to_director' AND OLD.state='returned' AND NEW.state='director_review' AND NEW.current_revision=OLD.current_revision)
 OR (d.action='director_approve' AND OLD.state='director_review' AND NEW.state='strategy_review' AND NEW.current_revision=OLD.current_revision)
 OR (d.action='strategy_approve' AND OLD.state='strategy_review' AND NEW.state='strategy_approved' AND NEW.current_revision=OLD.current_revision)
 OR (d.action IN ('director_return','director_reopen') AND OLD.state='director_review' AND NEW.state='returned'
 AND NEW.current_revision=OLD.current_revision+1 AND next.previous_revision_id=prior.id AND next.content_json=prior.content_json AND next.sha256=prior.sha256)
 OR (d.action='strategy_return' AND OLD.state='strategy_review' AND NEW.state='returned'
 AND NEW.current_revision=OLD.current_revision+1 AND next.previous_revision_id=prior.id AND next.content_json=prior.content_json AND next.sha256=prior.sha256)))
 THEN RAISE EXCEPTION 'Missing exact correction transition decision/audit'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

EDIT=r"""CREATE OR REPLACE FUNCTION civensa_revision_edit_guard() RETURNS trigger AS $$
DECLARE c record; g record; prior package_revisions%ROWTYPE; change jsonb; path jsonb; authorized boolean; entry jsonb; target numeric; actual numeric; expected jsonb;
BEGIN
 SELECT cy.* INTO c FROM revision_correction_cycles cy JOIN report_releases r ON r.id=cy.source_release_id
 WHERE cy.package_id=NEW.package_id ORDER BY cy.id DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_releases WHERE id=c.source_release_id) FOR UPDATE;
 IF NOT civensa_revision_current(c.source_release_id) THEN
 IF civensa_correction_opening_release(NEW.package_id,NEW.previous_revision_id,NEW.revision,NEW.content_json,NEW.sha256,NEW.created_by) IS NOT NULL
 THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Stale correction cycle';
 END IF;
 SELECT * INTO prior FROM package_revisions WHERE id=NEW.previous_revision_id;
 IF NEW.content_json=prior.content_json AND NEW.sha256=prior.sha256 AND NEW.package_id=prior.package_id AND NEW.revision=prior.revision+1
 AND NOT civensa_live_successor(c.source_release_id) AND civensa_latest_returned(c.source_release_id)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id JOIN directorate_packages p ON p.id=NEW.package_id
 WHERE d.package_revision_id=prior.id AND d.action='strategy_reopen' AND d.from_state='strategy_approved' AND p.state=d.from_state AND d.to_state='returned'
 AND civensa_correction_decision_authorized(d.id,p.id) AND e.actor_user_id=NEW.created_by AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=p.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.revision::text AND length(trim(e.reason))>0) THEN RETURN NEW; END IF;

 IF NEW.content_json=prior.content_json AND NEW.sha256=prior.sha256 AND NEW.package_id=prior.package_id AND NEW.revision=prior.revision+1
 AND EXISTS(SELECT 1 FROM revision_edit_grants gr JOIN revision_request_states st ON st.request_id=gr.request_id
 WHERE gr.cycle_id=c.id AND st.state='editing' AND civensa_grant_paths(gr.id) IS NOT NULL)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 JOIN directorate_packages p ON p.id=NEW.package_id
 WHERE d.package_revision_id=prior.id AND d.snapshot_sha256=prior.sha256 AND civensa_correction_decision_authorized(d.id,p.id) AND d.from_state=p.state AND d.to_state='returned'
 AND d.action IN ('director_return','director_reopen','strategy_return') AND e.actor_user_id=NEW.created_by
 AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=p.version::text
 AND e.context_json::jsonb->>'returned_revision'=NEW.revision::text AND length(trim(e.reason))>0) THEN RETURN NEW; END IF;
 SELECT gr.*,civensa_grant_paths(gr.id) effective_paths,r.organization_id,r.department_id,e.id AS event_id,e.reason,e.context_json,m.role_code INTO g
 FROM revision_edit_grants gr JOIN revision_requests r ON r.id=gr.request_id JOIN revision_request_states st ON st.request_id=r.id
 JOIN workflow_events e ON e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.event_type='correction_edit'
 JOIN directorate_memberships m ON m.id=(e.context_json::jsonb->>'membership_id')::integer JOIN users u ON u.id=m.user_id
 WHERE gr.cycle_id=c.id AND e.actor_user_id=NEW.created_by AND (e.context_json::jsonb->>'grant_id')::integer=gr.id
 AND (e.context_json::jsonb->>'next_revision')::integer=NEW.revision AND e.context_json::jsonb->>'next_sha256'=NEW.sha256
 AND st.state='editing' AND civensa_grant_paths(gr.id) IS NOT NULL
 AND ((gr.start_at<=clock_timestamp() AND clock_timestamp()<gr.end_at AND e.context_json::jsonb->>'renewal_id' IS NULL)
 OR EXISTS(SELECT 1 FROM revision_edit_grant_renewals n WHERE n.original_grant_id=gr.id AND n.id::text=e.context_json::jsonb->>'renewal_id'
 AND n.start_at<=clock_timestamp() AND clock_timestamp()<n.end_at))
 AND m.user_id=NEW.created_by AND m.active AND u.is_active AND u.role='department' AND m.department_id=r.department_id AND m.organization_id=r.organization_id
 AND gr.membership_ids_json::jsonb @> jsonb_build_array(m.id) ORDER BY e.id DESC LIMIT 1 FOR UPDATE OF m,u;
 IF NOT FOUND OR g.effective_paths IS NULL OR (g.role_code='department_director' AND length(trim(g.reason))=0) THEN RAISE EXCEPTION 'Missing active scoped correction authorization/audit'; END IF;
 SELECT * INTO prior FROM package_revisions WHERE id=NEW.previous_revision_id;
 IF prior.package_id<>NEW.package_id OR NEW.revision<>prior.revision+1 OR (g.context_json::jsonb->>'previous_revision_id')::integer<>prior.id
 OR NEW.sha256<>encode(sha256(convert_to(NEW.content_json,'UTF8')),'hex') THEN RAISE EXCEPTION 'Correction revision/hash mismatch'; END IF;
 IF prior.content_json::jsonb=NEW.content_json::jsonb THEN RAISE EXCEPTION 'No correction change'; END IF;
 FOR change IN SELECT * FROM civensa_revision_changes(prior.content_json::jsonb,NEW.content_json::jsonb) LOOP
 IF NOT EXISTS(SELECT 1 FROM field_change_events f WHERE f.workflow_event_id=g.event_id AND f.revision_request_id=g.request_id
 AND f.field_key::jsonb=change
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> ARRAY(SELECT jsonb_array_elements_text(change)),'null'::jsonb)
 AND f.new_json::jsonb=coalesce(NEW.content_json::jsonb #> ARRAY(SELECT jsonb_array_elements_text(change)),'null'::jsonb)) THEN RAISE EXCEPTION 'Missing exact correction field history'; END IF;
 authorized=false;
 FOR path IN SELECT value FROM jsonb_array_elements(g.effective_paths::jsonb) LOOP
 IF change @> path AND (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(change) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path THEN authorized=true; EXIT; END IF;
 END LOOP;
 -- Derived Activity calculation fields are recomputed below, never arbitrary user fields.
 IF NOT authorized AND NOT (change->>0='entries' AND change->>2='deviation' AND change->>3 IN ('delta','achievement_percent','calculation_rule_version','target_definition_revision_id')) THEN RAISE EXCEPTION 'Correction exceeds granted cell scope'; END IF;
 END LOOP;
 IF prior.content_json::jsonb ? 'entries' THEN
 FOR entry IN SELECT value FROM jsonb_array_elements(NEW.content_json::jsonb->'entries') LOOP
 actual=(entry->>'value')::numeric; target=NULL;
 IF jsonb_array_length(entry->'definition'->'targets')=1 AND entry->'definition'->'targets'->0->>'state'='verified' THEN target=(entry->'definition'->'targets'->0->>'value')::numeric; END IF;
 IF entry->>'state'='verified' AND actual IS NULL OR entry->>'state'='missing' AND actual IS NOT NULL OR entry->>'state' NOT IN ('verified','needs_review','missing') THEN RAISE EXCEPTION 'Invalid realization state/value'; END IF;
 IF entry->>'state'='verified' AND jsonb_array_length(entry->'evidence')=0 THEN RAISE EXCEPTION 'Verified correction requires evidence'; END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(entry->'evidence') ev WHERE coalesce(trim(ev->>'title'),'')='' OR coalesce(trim(ev->>'locator'),'')='' OR coalesce(trim(ev->>'source_revision'),'')='') THEN RAISE EXCEPTION 'Incomplete evidence'; END IF;
 IF entry->'deviation'->>'calculation_rule_version'<>'difference-v1' OR (entry->'deviation'->>'target_definition_revision_id')::integer<>(entry->>'definition_revision_id')::integer
 OR entry->'deviation'->>'achievement_percent' IS NOT NULL OR (entry->'deviation'->>'delta')::numeric IS DISTINCT FROM (CASE WHEN entry->>'state'='verified' THEN actual-target ELSE NULL END) THEN RAISE EXCEPTION 'Invalid calculated deviation'; END IF;
 END LOOP;
 END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

COMPLETION=r"""CREATE OR REPLACE FUNCTION civensa_correction_opening_complete() RETURNS trigger AS $$
DECLARE opening package_revisions%ROWTYPE;
BEGIN
 IF TG_TABLE_NAME='package_revisions' THEN opening=NEW;
 ELSE
 SELECT * INTO opening FROM package_revisions WHERE package_id=NEW.id AND revision=NEW.current_revision;
 IF EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=opening.previous_revision_id AND d.action='strategy_reopen'
 AND e.context_json::jsonb->>'returned_revision'=opening.revision::text AND e.context_json::jsonb->>'expected_version'=OLD.version::text)
 THEN RETURN NEW; END IF;
 END IF;
 IF NOT EXISTS(WITH RECURSIVE chain AS (SELECT r.* FROM directorate_packages p JOIN package_revisions r ON r.package_id=p.id AND r.revision=p.current_revision
 WHERE p.id=opening.package_id UNION ALL SELECT parent.* FROM package_revisions parent JOIN chain child ON child.previous_revision_id=parent.id)
 SELECT 1 FROM chain WHERE id=opening.id)
 THEN RAISE EXCEPTION 'Correction opening projection left behind'; END IF;
 -- The projection/request may have advanced by commit. Bind immutable opening
 -- facts to the release current when the server-timestamped copy was inserted.
 IF NOT EXISTS(SELECT 1 FROM revision_correction_cycles c JOIN report_releases r ON r.id=c.source_release_id
 JOIN candidate_packages binding ON binding.candidate_id=r.candidate_id AND binding.package_revision_id=c.source_package_revision_id
 JOIN package_revisions src ON src.id=binding.package_revision_id
 JOIN workflow_events e ON e.id=c.workflow_event_id JOIN revision_requests req ON req.id=(e.context_json::jsonb->>'request_id')::integer
 WHERE c.package_id=opening.package_id AND c.opening_revision_id=opening.id AND c.source_package_revision_id=opening.previous_revision_id
 AND src.package_id=opening.package_id AND opening.revision=src.revision+1 AND opening.content_json=src.content_json AND opening.sha256=src.sha256
 AND binding.sha256=src.sha256 AND r.created_at<=opening.created_at
 AND NOT EXISTS(SELECT 1 FROM report_releases newer WHERE newer.organization_id=r.organization_id AND newer.resource_scope=r.resource_scope
 AND newer.report_key=r.report_key AND (newer.major,newer.minor,newer.id)>(r.major,r.minor,r.id) AND newer.created_at<=opening.created_at)
 AND e.event_type='correction_opened' AND e.resource_type='revision_request' AND e.resource_id=req.id::text
 AND e.actor_user_id=opening.created_by AND e.created_at<=opening.created_at
 AND req.source_release_id=r.id AND req.source_package_revision_id=src.id AND e.organization_id=req.organization_id AND e.department_id=req.department_id
 AND e.context_json::jsonb->>'request_id'=req.id::text AND e.context_json::jsonb->>'source_release_id'=r.id::text
 AND e.context_json::jsonb->>'package_id'=opening.package_id::text AND e.context_json::jsonb->>'source_package_revision_id'=src.id::text)
 THEN RAISE EXCEPTION 'Correction opening requires its exact current-release cycle at commit'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

PUBLICATION=r"""CREATE OR REPLACE FUNCTION civensa_successor_publication_guard() RETURNS trigger AS $$
DECLARE sc report_candidates%ROWTYPE; p report_releases%ROWTYPE; m jsonb; ev workflow_events%ROWTYPE;
BEGIN
 IF NEW.resource_scope<>'activity_report' THEN RETURN NEW; END IF;
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 SELECT * INTO sc FROM report_candidates WHERE id=NEW.candidate_id; m=sc.manifest_json::jsonb;
 IF NOT (m ? 'predecessor_release_id') THEN
 IF NEW.major<>1 OR NEW.minor<>0 OR EXISTS(SELECT 1 FROM report_releases WHERE organization_id=NEW.organization_id AND resource_scope=NEW.resource_scope AND report_key=NEW.report_key)
 THEN RAISE EXCEPTION 'Activity successor requires explicit lineage'; END IF;
 RETURN NEW; END IF;
 SELECT * INTO p FROM report_releases WHERE id=(m->>'predecessor_release_id')::integer;
 IF p.id IS NULL OR NOT civensa_revision_current(p.id) OR
 (p.organization_id,p.resource_scope,p.report_key,p.major) IS DISTINCT FROM (NEW.organization_id,NEW.resource_scope,NEW.report_key,NEW.major)
 OR NEW.minor<>p.minor+1 OR sc.predecessor_candidate_id IS DISTINCT FROM p.candidate_id
 OR m->>'predecessor_candidate_sha256' IS DISTINCT FROM (SELECT sha256 FROM report_candidates WHERE id=p.candidate_id)
 THEN RAISE EXCEPTION 'Stale or mismatched immediate predecessor'; END IF;
 IF m->'correction_cycle_ids' IS DISTINCT FROM (SELECT jsonb_agg(id ORDER BY id) FROM revision_correction_cycles WHERE source_release_id=p.id) THEN RAISE EXCEPTION 'Successor cycle set changed'; END IF;
 SELECT * INTO ev FROM workflow_events WHERE id=NEW.workflow_event_id;
 IF NOT EXISTS(SELECT 1 FROM report_candidate_states WHERE candidate_id=sc.id AND state='final_approved')
 OR ev.id IS NULL OR ev.event_type<>'publish_report' OR ev.resource_type<>'report_candidate' OR ev.resource_id<>sc.id::text
 OR NOT EXISTS(SELECT 1 FROM users WHERE id=ev.actor_user_id AND is_active AND role='strategy')
 OR EXISTS(SELECT 1 FROM final_authority_assignments current_authority
 WHERE current_authority.organization_id=NEW.organization_id AND current_authority.active AND current_authority.user_id=ev.actor_user_id)
 OR NOT EXISTS(SELECT 1 FROM report_decisions d JOIN final_authority_assignments a ON a.id=d.assignment_id
 WHERE d.id=NEW.final_decision_id AND d.candidate_id=sc.id AND d.candidate_sha256=sc.sha256 AND d.action='final_approve'
 AND a.active AND a.organization_id=sc.organization_id)
 THEN RAISE EXCEPTION 'Missing current authorized successor publication'; END IF;
 IF EXISTS(SELECT 1 FROM candidate_packages b JOIN package_revisions rev ON rev.id=b.package_revision_id
 JOIN directorate_packages pkg ON pkg.id=rev.package_id JOIN package_decisions d ON d.id=b.strategy_decision_id
 JOIN workflow_events e ON e.id=d.workflow_event_id WHERE b.candidate_id=sc.id AND
 (pkg.state<>'strategy_approved' OR pkg.current_revision<>rev.revision OR b.sha256<>rev.sha256
 OR d.action<>'strategy_approve' OR d.package_revision_id<>rev.id OR d.snapshot_sha256<>rev.sha256
 OR e.event_type<>'strategy_approve' OR e.resource_type<>'directorate_package' OR e.resource_id<>pkg.id::text
 OR e.context_json::jsonb->>'revision_id' IS DISTINCT FROM rev.id::text OR e.context_json::jsonb->>'sha256' IS DISTINCT FROM rev.sha256))
 THEN RAISE EXCEPTION 'Successor package snapshot moved'; END IF;
 IF EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states st ON st.request_id=r.id
 WHERE r.source_release_id=p.id AND st.state='closed_no_change' AND civensa_successor_request_participates(sc.id,r.id))
 THEN RAISE EXCEPTION 'closed_no_change request participates in successor'; END IF;
 IF NOT EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states st ON st.request_id=r.id WHERE r.source_release_id=p.id AND st.state='editing' AND civensa_successor_request_participates(sc.id,r.id))
 OR jsonb_typeof(m->'correction_request_grants') IS DISTINCT FROM 'array' OR jsonb_array_length(m->'correction_request_grants')=0
 OR EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states s ON s.request_id=r.id
 WHERE r.source_release_id=p.id AND s.state NOT IN ('rejected','cancelled','stale','closed_no_change')
 AND (s.state<>'editing' OR NOT civensa_successor_request_participates(sc.id,r.id)))
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(m->'correction_request_grants') b
 WHERE NOT EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states s ON s.request_id=r.id
 WHERE r.id=(b->>'request_id')::integer AND r.source_release_id=p.id AND (s.state='closed_no_change' OR (s.state='editing' AND civensa_successor_request_participates(sc.id,r.id)))))
 THEN RAISE EXCEPTION 'Unresolved or unedited successor requests'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

FREEZE=r"""CREATE FUNCTION civensa_correction_live_guard() RETURNS trigger AS $$
BEGIN
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_releases WHERE id=NEW.source_release_id) FOR UPDATE;
 IF civensa_live_successor(NEW.source_release_id) THEN RAISE EXCEPTION 'Live successor freezes correction opening'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

STATE_INSERT=r"""CREATE FUNCTION civensa_report_state_initial_guard() RETURNS trigger AS $$
BEGIN
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_candidates WHERE id=NEW.candidate_id) FOR UPDATE;
 IF NEW.state<>'assembling' OR NEW.version<>0 THEN RAISE EXCEPTION 'Invalid initial candidate state'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

PARTICIPATES=r"""CREATE OR REPLACE FUNCTION civensa_successor_request_participates(cid integer,rid integer) RETURNS boolean AS $$
 WITH RECURSIVE lineage AS (
 SELECT rev.* FROM candidate_packages b JOIN package_revisions rev ON rev.id=b.package_revision_id WHERE b.candidate_id=cid
 UNION SELECT parent.* FROM package_revisions parent JOIN lineage child ON child.previous_revision_id=parent.id
 ), participant AS (
 SELECT r.id,r.organization_id,r.department_id,r.source_release_id,g.id grant_id,g.cycle_id,g.paths_json,g.membership_ids_json,c.package_id,c.opening_revision_id,
 source.content_json::jsonb source_content,bound.content_json::jsonb bound_content
 FROM revision_requests r JOIN revision_edit_grants g ON g.request_id=r.id JOIN revision_correction_cycles c ON c.id=g.cycle_id
 JOIN report_candidates sc ON sc.id=cid JOIN package_revisions source ON source.id=c.source_package_revision_id
 JOIN candidate_packages cb ON cb.candidate_id=cid JOIN package_revisions bound ON bound.id=cb.package_revision_id AND bound.package_id=c.package_id
 WHERE r.id=rid AND r.source_release_id=(sc.manifest_json::jsonb->>'predecessor_release_id')::integer
 AND c.source_release_id=r.source_release_id AND g.source_release_id=r.source_release_id
 AND sc.manifest_json::jsonb->'correction_cycle_ids' @> jsonb_build_array(c.id)
 AND (sc.manifest_json::jsonb->'correction_request_grants' @> jsonb_build_array(jsonb_build_object('request_id',r.id,'grant_id',g.id,'cycle_id',c.id)) OR EXISTS(SELECT 1 FROM revision_request_states closed WHERE closed.request_id=r.id AND closed.state='closed_no_change'))
 AND EXISTS(SELECT 1 FROM lineage l WHERE l.id=c.opening_revision_id)
 ) SELECT EXISTS(SELECT 1 FROM participant p
 JOIN workflow_events e ON e.resource_type='revision_request' AND e.resource_id=p.id::text
 JOIN field_change_events f ON f.workflow_event_id=e.id AND f.revision_request_id=p.id
 JOIN lineage l ON l.package_id=p.package_id JOIN package_revisions prior ON prior.id=l.previous_revision_id
 JOIN directorate_memberships member ON member.id=(e.context_json::jsonb->>'membership_id')::integer,
 jsonb_array_elements(p.paths_json::jsonb) path,
 LATERAL (SELECT ARRAY(SELECT jsonb_array_elements_text(f.field_key::jsonb)) keys) address
 WHERE e.event_type='correction_edit' AND e.organization_id=p.organization_id AND e.department_id=p.department_id
 AND e.context_json::jsonb->>'grant_id'=p.grant_id::text AND e.context_json::jsonb->>'request_id'=p.id::text
 AND e.context_json::jsonb->>'source_release_id'=p.source_release_id::text AND e.context_json::jsonb->>'package_id'=p.package_id::text
 AND l.previous_revision_id::text=e.context_json::jsonb->>'previous_revision_id'
 AND l.revision::text=e.context_json::jsonb->>'next_revision' AND l.sha256=e.context_json::jsonb->>'next_sha256'
 AND e.actor_user_id=l.created_by AND e.created_at<=l.created_at
 AND member.user_id=e.actor_user_id AND member.organization_id=p.organization_id AND member.department_id=p.department_id
 AND p.membership_ids_json::jsonb @> jsonb_build_array(member.id)
 AND l.id<>p.opening_revision_id AND (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(f.field_key::jsonb) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path AND NOT f.field_key::jsonb @> '["deviation"]'::jsonb
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (p.source_content #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE (p.source_content #> address.keys) IS DISTINCT FROM (p.bound_content #> address.keys) END
 AND f.previous_json::jsonb IS DISTINCT FROM f.new_json::jsonb
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> address.keys,'null'::jsonb) AND f.new_json::jsonb=coalesce(l.content_json::jsonb #> address.keys,'null'::jsonb));
 $$ LANGUAGE sql;"""


REOPEN_DECISION=r"""CREATE FUNCTION civensa_strategy_reopen_decision_guard() RETURNS trigger AS $$
DECLARE p directorate_packages%ROWTYPE; c revision_correction_cycles%ROWTYPE;
BEGIN
 IF NEW.action<>'strategy_reopen' THEN RETURN NEW; END IF;
 SELECT pkg.* INTO p FROM directorate_packages pkg JOIN package_revisions rev ON rev.package_id=pkg.id WHERE rev.id=NEW.package_revision_id;
 PERFORM 1 FROM organizations WHERE id=p.organization_id FOR UPDATE;
 SELECT * INTO c FROM revision_correction_cycles WHERE package_id=p.id ORDER BY id DESC LIMIT 1;
 IF c.id IS NULL OR NOT civensa_revision_current(c.source_release_id) OR civensa_live_successor(c.source_release_id)
 OR NOT civensa_latest_returned(c.source_release_id) OR p.state<>'strategy_approved'
 OR NEW.from_state<>p.state OR NEW.to_state<>'returned'
 THEN RAISE EXCEPTION 'strategy_reopen requires current returned successor'; END IF;
 IF NOT EXISTS(SELECT 1 FROM workflow_events e JOIN users u ON u.id=e.actor_user_id JOIN package_revisions rev ON rev.id=NEW.package_revision_id
 WHERE e.id=NEW.workflow_event_id AND u.is_active AND u.role='strategy' AND NEW.delegation_id IS NULL
 AND e.organization_id=p.organization_id AND e.department_id=p.department_id AND e.event_type='strategy_reopen'
 AND e.resource_type='directorate_package' AND e.resource_id=p.id::text AND length(trim(e.reason))>0
 AND rev.revision=p.current_revision AND rev.sha256=NEW.snapshot_sha256 AND rev.sha256=encode(sha256(convert_to(rev.content_json,'UTF8')),'hex')
 AND e.context_json::jsonb->>'revision_id'=rev.id::text AND e.context_json::jsonb->>'sha256'=rev.sha256
 AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text AND e.context_json::jsonb->>'expected_version'=p.version::text
 AND e.context_json::jsonb->>'from_state'=NEW.from_state AND e.context_json::jsonb->>'to_state'=NEW.to_state
 AND e.context_json::jsonb->>'delegation_id' IS NULL AND e.context_json::jsonb->>'returned_revision'=(rev.revision+1)::text)
 THEN RAISE EXCEPTION 'Missing exact Strategy reopen audit'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""
