"""S3B atomic successor publication and audited terminal applied requests."""
from alembic import op
import sqlalchemy as sa
revision='6a8fcbd93745'
down_revision='597efbc82634'
branch_labels=depends_on=None


def upgrade():
    with op.batch_alter_table('revision_request_states') as batch:
        batch.drop_constraint('ck_revision_request_state',type_='check')
        batch.create_check_constraint('ck_revision_request_state',"state IN ('requested','accepted','rejected','cancelled','editing','stale','applied','closed_no_change')")
    if op.get_bind().dialect.name=='postgresql':
        op.execute(PARTICIPATES)
        op.execute(CANDIDATE)
        op.execute('CREATE TRIGGER activity_initial_candidate_guard BEFORE INSERT ON report_candidates FOR EACH ROW EXECUTE FUNCTION civensa_activity_initial_candidate_guard()')
        op.execute(STATE)
        op.execute(PUBLICATION)
        op.execute(DEFERRED)
        op.execute('CREATE CONSTRAINT TRIGGER activity_release_completion_guard AFTER INSERT ON report_releases DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION civensa_activity_release_completion_guard()')
        op.execute(PUBLISHED)
        op.execute('CREATE TRIGGER report_published_release_guard BEFORE UPDATE ON report_candidate_states FOR EACH ROW EXECUTE FUNCTION civensa_report_published_release_guard()')
        op.execute('CREATE TRIGGER activity_successor_publication_guard BEFORE INSERT ON report_releases FOR EACH ROW EXECUTE FUNCTION civensa_successor_publication_guard()')
    else:
        op.execute("CREATE TRIGGER revision_applied_guard BEFORE UPDATE ON revision_request_states WHEN NEW.state IN ('applied','closed_no_change') BEGIN SELECT RAISE(ABORT,'Applied publication requires PostgreSQL'); END")


def downgrade():
    raise RuntimeError('Applied publication history cannot be discarded')


PARTICIPATES=r"""CREATE FUNCTION civensa_successor_request_participates(cid integer,rid integer) RETURNS boolean AS $$
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
 AND sc.manifest_json::jsonb->'correction_request_grants' @> jsonb_build_array(jsonb_build_object('request_id',r.id,'grant_id',g.id,'cycle_id',c.id))
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

STATE=r"""CREATE OR REPLACE FUNCTION civensa_revision_state_guard() RETURNS trigger AS $$
DECLARE r revision_requests%ROWTYPE; ev record;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Request history cannot be deleted'; END IF;
 IF TG_OP='INSERT' THEN
 IF NEW.state<>'requested' OR NEW.version<>0 THEN RAISE EXCEPTION 'Invalid initial request state'; END IF; RETURN NEW; END IF;
 SELECT * INTO r FROM revision_requests WHERE id=OLD.request_id;
 PERFORM 1 FROM organizations WHERE id=r.organization_id FOR UPDATE;
 PERFORM 1 FROM report_releases WHERE id=r.source_release_id FOR UPDATE;
 IF NEW.request_id<>OLD.request_id OR NEW.version<>OLD.version+1 OR NOT
 ((OLD.state='requested' AND NEW.state IN ('accepted','rejected','cancelled')) OR (OLD.state='accepted' AND NEW.state='editing') OR (OLD.state='editing' AND NEW.state='applied') OR (OLD.state IN ('accepted','editing') AND NEW.state='closed_no_change')) THEN RAISE EXCEPTION 'Illegal revision state transition'; END IF;
 SELECT e.*,u.role,u.is_active INTO ev FROM revision_request_events re JOIN workflow_events e ON e.id=re.workflow_event_id JOIN users u ON u.id=e.actor_user_id
 WHERE re.request_id=r.id AND re.version=NEW.version AND re.from_state=OLD.state AND re.to_state=NEW.state
 AND e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.organization_id=r.organization_id AND e.department_id=r.department_id
 AND (e.context_json::jsonb->>'version')::integer=NEW.version AND e.context_json::jsonb->>'from_state'=OLD.state AND e.context_json::jsonb->>'to_state'=NEW.state;
 IF NOT FOUND OR NOT ev.is_active OR ev.event_type<>'revision_'||NEW.state OR
 (NEW.state='cancelled' AND (ev.actor_user_id<>r.requester_user_id OR length(trim(ev.reason))=0)) OR
 (NEW.state IN ('accepted','rejected','editing','applied','closed_no_change') AND ev.role<>'strategy') OR (NEW.state IN ('rejected','closed_no_change') AND length(trim(ev.reason))=0) THEN RAISE EXCEPTION 'Missing authorized revision audit'; END IF;
 IF NEW.state IN ('accepted','editing','closed_no_change') AND NOT civensa_revision_current(r.source_release_id) THEN RAISE EXCEPTION 'Stale source release'; END IF;
 IF NEW.state='accepted' AND EXISTS(SELECT 1 FROM revision_requests other JOIN revision_request_states s ON s.request_id=other.id,
 jsonb_array_elements(other.patches_json::jsonb) a,jsonb_array_elements(r.patches_json::jsonb) b
 WHERE other.id<>r.id AND other.source_release_id=r.source_release_id AND other.department_id=r.department_id
 AND s.state IN ('accepted','editing') AND a->'path'=b->'path') THEN RAISE EXCEPTION 'Overlapping accepted revision cells'; END IF;
 IF NEW.state='editing' AND NOT EXISTS(SELECT 1 FROM revision_edit_grants g WHERE g.request_id=r.id) THEN RAISE EXCEPTION 'Missing scoped grant'; END IF;
 IF NEW.state='closed_no_change' AND (ev.context_json::jsonb->>'request_id' IS DISTINCT FROM r.id::text OR ev.context_json::jsonb->>'source_release_id' IS DISTINCT FROM r.source_release_id::text) THEN RAISE EXCEPTION 'Invalid closure provenance'; END IF;
 IF NEW.state='applied' THEN
 IF ev.context_json::jsonb->>'request_id' IS DISTINCT FROM r.id::text
 OR ev.context_json::jsonb->>'source_release_id' IS DISTINCT FROM r.source_release_id::text
 OR ev.context_json::jsonb->>'predecessor_release_id' IS DISTINCT FROM r.source_release_id::text
 OR NOT EXISTS(SELECT 1 FROM report_releases sr JOIN report_candidates sc ON sc.id=sr.candidate_id
 JOIN report_candidate_states cs ON cs.candidate_id=sc.id JOIN report_release_successions edge ON edge.successor_release_id=sr.id
 JOIN workflow_events pe ON pe.id=sr.workflow_event_id
 JOIN revision_edit_grants g ON g.request_id=r.id
 WHERE sr.id=(ev.context_json::jsonb->>'successor_release_id')::integer
 AND sc.id=(ev.context_json::jsonb->>'successor_candidate_id')::integer
 AND sc.sha256=ev.context_json::jsonb->>'successor_candidate_sha256'
 AND cs.state='published' AND sr.organization_id=r.organization_id AND sr.resource_scope='activity_report'
 AND edge.predecessor_release_id=r.source_release_id AND edge.workflow_event_id=pe.id
 AND pe.event_type='publish_report' AND pe.actor_user_id=ev.actor_user_id
 AND NOT EXISTS(SELECT 1 FROM final_authority_assignments current_authority
 WHERE current_authority.organization_id=sr.organization_id AND current_authority.active AND current_authority.user_id=pe.actor_user_id)
 AND pe.resource_id=sc.id::text AND pe.resource_type='report_candidate'
 AND g.id=(ev.context_json::jsonb->>'grant_id')::integer
 AND g.cycle_id=(ev.context_json::jsonb->>'correction_cycle_id')::integer
 AND civensa_successor_request_participates(sc.id,r.id)) THEN RAISE EXCEPTION 'Invalid applied publication provenance'; END IF;
 END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

PUBLICATION=r"""CREATE FUNCTION civensa_successor_publication_guard() RETURNS trigger AS $$
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
 IF ev.id IS NULL OR ev.event_type<>'publish_report' OR ev.resource_type<>'report_candidate' OR ev.resource_id<>sc.id::text
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


CANDIDATE=r"""CREATE FUNCTION civensa_activity_initial_candidate_guard() RETURNS trigger AS $$
BEGIN
 IF NEW.resource_scope='activity_report' THEN
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 IF NOT (NEW.manifest_json::jsonb ? 'predecessor_release_id') AND EXISTS(SELECT 1 FROM report_releases
 WHERE organization_id=NEW.organization_id AND resource_scope='activity_report' AND report_key=NEW.report_key)
 THEN RAISE EXCEPTION 'Published Activity requires explicit successor assembly'; END IF;
 END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


DEFERRED=r"""CREATE FUNCTION civensa_activity_release_completion_guard() RETURNS trigger AS $$
DECLARE m jsonb;
BEGIN
 IF NEW.resource_scope<>'activity_report' THEN RETURN NEW; END IF;
 SELECT manifest_json::jsonb INTO m FROM report_candidates WHERE id=NEW.candidate_id;
 IF m ? 'predecessor_release_id' AND (SELECT count(*) FROM report_release_successions
 WHERE successor_release_id=NEW.id AND predecessor_release_id=(m->>'predecessor_release_id')::integer AND workflow_event_id=NEW.workflow_event_id)<>1
 THEN RAISE EXCEPTION 'Successor release requires exactly one immutable succession'; END IF;
 IF NOT EXISTS(SELECT 1 FROM report_candidate_states WHERE candidate_id=NEW.candidate_id AND state='published')
 THEN RAISE EXCEPTION 'Release must atomically publish candidate'; END IF;
 IF m ? 'predecessor_release_id' AND EXISTS(SELECT 1 FROM revision_requests r JOIN revision_request_states st ON st.request_id=r.id
 WHERE r.source_release_id=(m->>'predecessor_release_id')::integer AND st.state NOT IN ('applied','closed_no_change','rejected','cancelled','stale'))
 THEN RAISE EXCEPTION 'Successor publication must atomically resolve requests'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


PUBLISHED=r"""CREATE FUNCTION civensa_report_published_release_guard() RETURNS trigger AS $$
DECLARE m jsonb;
BEGIN
 IF NEW.state<>'published' THEN RETURN NEW; END IF;
 SELECT manifest_json::jsonb INTO m FROM report_candidates WHERE id=NEW.candidate_id;
 IF NOT EXISTS(SELECT 1 FROM report_releases r JOIN workflow_events e ON e.id=r.workflow_event_id
 WHERE r.candidate_id=NEW.candidate_id AND e.event_type='publish_report' AND e.resource_type='report_candidate'
 AND e.resource_id=NEW.candidate_id::text AND e.context_json::jsonb->>'from_state'=OLD.state
 AND e.context_json::jsonb->>'to_state'='published' AND e.context_json::jsonb->>'version'=NEW.version::text
 AND (NOT (m ? 'predecessor_release_id') OR EXISTS(SELECT 1 FROM report_release_successions edge
 WHERE edge.successor_release_id=r.id AND edge.predecessor_release_id=(m->>'predecessor_release_id')::integer AND edge.workflow_event_id=e.id)))
 THEN RAISE EXCEPTION 'Published state requires exact release and successor lineage'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""
