"""A1-P1 workflow activation blockers: guards for F1, F2, F3, F5 and K-7.

PostgreSQL (CREATE OR REPLACE of the current definitions, plus new guards):
- F1: report_state_guard gains final_approved -> returned_to_strategy, only for
  an unpublished Activity successor candidate, by the CURRENT non-Strategy final
  authority with a reasoned, exact final_return decision; report_binding_guard requires the
  decision assignment and its user to be active; closed_no_change is refused
  while a live successor lists the request.
- F2: activity_report_revisions / activity_report_approvals insert guards. A
  report with any candidate or release accepts a new revision only as a
  candidate materialization (immediately refused while a candidate is live);
  a candidate-bound revision accepts a freeze only from the current final
  authority's exact final_approve decision. Pre-workflow reports (no candidate,
  no release) are unchanged; existing rows are never re-checked.
- F3: deviation.corrective_action is semantic; only the derived difference-v1
  keys are excluded from participation/survival; correction edits may change
  no other deviation key.
- F1 backstop: a deferred check refuses an Activity successor whose listed
  participant has no semantic net correction. A surviving closed_no_change
  edit stays a publication refusal so the return/reopen exit can revert it.
- F5: a delegation of an inactive director no longer suppresses primary
  director authority in civensa_correction_decision_authorized; deactivating a
  director membership with an unterminated delegation is refused.
- K-7: review/return/approval of a correction package verifies historical edit
  authorization (civensa_correction_lineage_authorized) instead of a live
  grant; return copies no longer need a live grant; renewal no longer needs a
  returned successor attempt, only no live successor.
SQLite keeps the existing history guards (no table rebuild) and adds the
strongest F2 insert guards it can express; the deferred final-decision binding
is PostgreSQL only.
"""
from alembic import op
revision='c5e8a1f0b247'
down_revision='e69c04e721a5'
branch_labels=depends_on=None


def upgrade():
    if op.get_bind().dialect.name=='postgresql':
        for sql in (HELPERS,LINEAGE,FINAL_RETURN,STATE,BINDING,PARTICIPATES,SURVIVES,AUTHORITY,PROJECTION,EDIT,RENEWAL,REQUEST_STATE,OWNER):
            op.execute(sql)
        op.execute('CREATE TRIGGER activity_revision_live_owner BEFORE INSERT ON activity_report_revisions FOR EACH ROW EXECUTE FUNCTION civensa_activity_revision_owner_guard()')
        op.execute('CREATE CONSTRAINT TRIGGER activity_revision_owner AFTER INSERT ON activity_report_revisions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION civensa_activity_revision_owner_guard()')
        op.execute('CREATE TRIGGER activity_approval_owner BEFORE INSERT ON activity_report_approvals FOR EACH ROW EXECUTE FUNCTION civensa_activity_approval_owner_guard()')
        op.execute('CREATE CONSTRAINT TRIGGER activity_approval_decision AFTER INSERT ON activity_report_approvals DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION civensa_activity_approval_owner_guard()')
        op.execute(PARTICIPATION)
        op.execute('CREATE CONSTRAINT TRIGGER activity_successor_participation AFTER INSERT ON report_candidates DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION civensa_successor_participation_check()')
        op.execute(DIRECTOR)
        op.execute('CREATE TRIGGER director_deactivation_delegation BEFORE UPDATE ON directorate_memberships FOR EACH ROW EXECUTE FUNCTION civensa_director_deactivation_guard()')
    else:
        # New triggers only; no batch_alter_table, so no existing SQLite trigger is dropped.
        # SQLite cannot defer: a revision is refused while a live candidate or a
        # release exists (no SQLite workflow path materializes then: successors
        # need PostgreSQL); after a return the application layer refuses.
        op.execute(f"""CREATE TRIGGER activity_revision_owner BEFORE INSERT ON activity_report_revisions WHEN {SQLITE_LIVE.format(report='NEW.report_id')}
            BEGIN SELECT RAISE(ABORT,'Workflow-managed Activity report rejects legacy revision'); END""")
        op.execute(f"""CREATE TRIGGER activity_approval_owner BEFORE INSERT ON activity_report_approvals WHEN
            (EXISTS(SELECT 1 FROM report_candidates c WHERE c.activity_revision_id=NEW.report_revision_id) AND NOT EXISTS(
              SELECT 1 FROM report_candidates c JOIN report_candidate_states s ON s.candidate_id=c.id
              JOIN final_authority_assignments a ON a.organization_id=c.organization_id AND a.active=1 AND a.user_id=NEW.created_by
              JOIN users u ON u.id=a.user_id AND u.is_active=1
              JOIN workflow_events e ON e.resource_type='report_candidate' AND e.resource_id=CAST(c.id AS TEXT) AND e.event_type='final_approve'
              WHERE c.activity_revision_id=NEW.report_revision_id AND s.state='final_review' AND e.actor_user_id=NEW.created_by
              AND e.organization_id=c.organization_id AND json_extract(e.context_json,'$.sha256')=c.sha256
              AND json_extract(e.context_json,'$.from_state')='final_review' AND json_extract(e.context_json,'$.to_state')='final_approved'
              AND json_extract(e.context_json,'$.version')=s.version+1))
            OR (NOT EXISTS(SELECT 1 FROM report_candidates c WHERE c.activity_revision_id=NEW.report_revision_id)
              AND {SQLITE_MANAGED.format(report='(SELECT report_id FROM activity_report_revisions WHERE id=NEW.report_revision_id)')})
            BEGIN SELECT RAISE(ABORT,'Workflow-managed Activity report rejects legacy approval'); END""")
        op.execute("""CREATE TRIGGER director_deactivation_delegation BEFORE UPDATE ON directorate_memberships WHEN
            OLD.active=1 AND NEW.active=0 AND OLD.role_code='department_director' AND EXISTS(SELECT 1 FROM authority_delegations a
            WHERE a.director_membership_id=OLD.id AND a.active=1 AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id))
            BEGIN SELECT RAISE(ABORT,'Director delegation must be terminated with the director membership'); END""")


def downgrade():
    raise RuntimeError('A1-P1 workflow activation guards cannot be discarded')


SQLITE_LIVE="""(EXISTS(SELECT 1 FROM activity_reports rp JOIN report_releases r ON r.organization_id=rp.organization_id
              AND r.resource_scope='activity_report' AND r.report_key=CAST(rp.id AS TEXT) WHERE rp.id={report})
            OR EXISTS(SELECT 1 FROM activity_reports rp JOIN report_candidates c ON c.organization_id=rp.organization_id
              AND c.resource_scope='activity_report' AND c.report_key=CAST(rp.id AS TEXT)
              JOIN report_candidate_states s ON s.candidate_id=c.id WHERE rp.id={report} AND s.state IN ('assembling','final_review','final_approved')))"""
SQLITE_MANAGED="""(EXISTS(SELECT 1 FROM activity_reports rp JOIN report_releases r ON r.organization_id=rp.organization_id
              AND r.resource_scope='activity_report' AND r.report_key=CAST(rp.id AS TEXT) WHERE rp.id={report})
            OR EXISTS(SELECT 1 FROM activity_reports rp JOIN report_candidates c ON c.organization_id=rp.organization_id
              AND c.resource_scope='activity_report' AND c.report_key=CAST(rp.id AS TEXT) WHERE rp.id={report}))"""


# Mirrors revision_workflow_service.DERIVED_DEVIATION_KEYS / net_changed().
HELPERS=r"""CREATE FUNCTION civensa_derived_deviation_key(k jsonb) RETURNS boolean AS $$
 SELECT jsonb_array_length(k)>=4 AND k->>0='entries' AND k->>2='deviation'
 AND k->>3 IN ('achievement_percent','calculation_rule_version','delta','target_definition_revision_id');
$$ LANGUAGE sql IMMUTABLE;
CREATE FUNCTION civensa_net_value(k jsonb,v jsonb) RETURNS jsonb AS $$
 SELECT CASE WHEN jsonb_array_length(k)=3 AND k->>0='entries' AND k->>2='deviation' AND jsonb_typeof(v)='object'
 THEN v-ARRAY['achievement_percent','calculation_rule_version','delta','target_definition_revision_id'] ELSE coalesce(v,'null'::jsonb) END;
$$ LANGUAGE sql IMMUTABLE;
CREATE FUNCTION civensa_activity_report_managed(rid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM activity_reports rp JOIN report_releases r ON r.organization_id=rp.organization_id
 AND r.resource_scope='activity_report' AND r.report_key=rp.id::text WHERE rp.id=rid)
 OR EXISTS(SELECT 1 FROM activity_reports rp JOIN report_candidates c ON c.organization_id=rp.organization_id
 AND c.resource_scope='activity_report' AND c.report_key=rp.id::text WHERE rp.id=rid);
$$ LANGUAGE sql;"""


# K-7: mirrors revision_workflow_service.authorized_edit()/verify_correction_lineage().
# A content change is authorized only by its exact correction_edit event, made
# inside the grant or the named renewal (never before the renewal existed; the
# event instant precedes the edit guard's clock check, the revision timestamp
# may legitimately fall after end_at), by a
# granted membership not yet deactivated, on granted paths (or derived leaves).
LINEAGE=r"""CREATE FUNCTION civensa_correction_edit_authorized(cyc integer,pid integer,nid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM revision_edit_grants g JOIN revision_requests r ON r.id=g.request_id
 JOIN revision_correction_cycles c ON c.id=g.cycle_id
 JOIN package_revisions prior ON prior.id=pid JOIN package_revisions nr ON nr.id=nid
 JOIN workflow_events e ON e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.event_type='correction_edit'
 JOIN directorate_memberships m ON m.id=(e.context_json::jsonb->>'membership_id')::integer
 LEFT JOIN revision_edit_grant_renewals n ON n.id=(e.context_json::jsonb->>'renewal_id')::integer
 WHERE g.cycle_id=cyc AND prior.package_id=c.package_id AND nr.package_id=c.package_id
 AND e.actor_user_id=nr.created_by AND e.organization_id=r.organization_id AND e.department_id=r.department_id
 AND e.context_json::jsonb->>'grant_id'=g.id::text AND e.context_json::jsonb->>'request_id'=r.id::text
 AND e.context_json::jsonb->>'package_id'=c.package_id::text
 AND e.context_json::jsonb->>'previous_revision_id'=prior.id::text AND e.context_json::jsonb->>'next_revision'=nr.revision::text
 AND e.context_json::jsonb->>'next_sha256'=nr.sha256 AND e.created_at<=nr.created_at
 AND m.user_id=e.actor_user_id AND m.organization_id=r.organization_id AND m.department_id=r.department_id
 AND g.membership_ids_json::jsonb @> jsonb_build_array(m.id)
 AND NOT EXISTS(SELECT 1 FROM membership_events me WHERE me.membership_id=m.id AND me.event_type='deactivated' AND me.created_at<=e.created_at)
 AND CASE WHEN e.context_json::jsonb->>'renewal_id' IS NULL THEN g.start_at<=e.created_at AND e.created_at<g.end_at
 ELSE n.id IS NOT NULL AND n.original_grant_id=g.id AND greatest(n.start_at,n.created_at)<=e.created_at AND e.created_at<n.end_at END
 AND NOT EXISTS(SELECT 1 FROM civensa_revision_changes(prior.content_json::jsonb,nr.content_json::jsonb) ch
 WHERE NOT EXISTS(SELECT 1 FROM field_change_events f WHERE f.workflow_event_id=e.id AND f.revision_request_id=r.id AND f.field_key::jsonb=ch
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> ARRAY(SELECT jsonb_array_elements_text(ch)),'null'::jsonb)
 AND f.new_json::jsonb=coalesce(nr.content_json::jsonb #> ARRAY(SELECT jsonb_array_elements_text(ch)),'null'::jsonb))
 OR NOT (civensa_derived_deviation_key(ch) OR EXISTS(SELECT 1 FROM jsonb_array_elements(CASE WHEN n.id IS NULL THEN g.paths_json ELSE n.paths_json END::jsonb) path
 WHERE (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(ch) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path))));
$$ LANGUAGE sql;
CREATE FUNCTION civensa_correction_lineage_authorized(cyc integer,rid integer) RETURNS boolean AS $$
DECLARE c revision_correction_cycles%ROWTYPE; cur package_revisions%ROWTYPE; prior package_revisions%ROWTYPE;
BEGIN
 SELECT * INTO c FROM revision_correction_cycles WHERE id=cyc;
 IF NOT FOUND THEN RETURN false; END IF;
 SELECT * INTO cur FROM package_revisions WHERE id=rid;
 IF NOT FOUND OR cur.package_id<>c.package_id THEN RETURN false; END IF;
 WHILE cur.id<>c.opening_revision_id LOOP
 SELECT * INTO prior FROM package_revisions WHERE id=cur.previous_revision_id;
 IF NOT FOUND OR prior.package_id<>c.package_id OR cur.revision<>prior.revision+1 THEN RETURN false; END IF;
 IF cur.content_json<>prior.content_json AND NOT civensa_correction_edit_authorized(c.id,prior.id,cur.id) THEN RETURN false; END IF;
 cur:=prior;
 END LOOP;
 RETURN cur.previous_revision_id=c.source_package_revision_id;
END; $$ LANGUAGE plpgsql;"""


# A1-F1 controlled recovery exit: only before publication, by the current active
# non-Strategy final authority, with a reasoned exact final_return decision.
FINAL_RETURN=r"""CREATE FUNCTION civensa_final_approved_return(cid integer,ver integer) RETURNS boolean AS $$
 SELECT NOT EXISTS(SELECT 1 FROM report_releases rr WHERE rr.candidate_id=cid)
 AND EXISTS(SELECT 1 FROM report_decisions d JOIN report_candidates c ON c.id=d.candidate_id
 JOIN workflow_events e ON e.id=d.workflow_event_id JOIN final_authority_assignments a ON a.id=d.assignment_id
 JOIN users u ON u.id=a.user_id
 WHERE d.candidate_id=cid AND d.action='final_return' AND d.candidate_sha256=c.sha256
 AND c.resource_scope='activity_report' AND c.manifest_json::jsonb ? 'predecessor_release_id'
 AND a.active AND u.is_active AND u.role<>'strategy' AND a.organization_id=c.organization_id
 AND e.actor_user_id=a.user_id AND e.event_type='final_return' AND e.resource_type='report_candidate'
 AND e.resource_id=cid::text AND e.organization_id=c.organization_id AND e.context_json::jsonb->>'sha256'=c.sha256
 AND e.context_json::jsonb->>'from_state'='final_approved' AND e.context_json::jsonb->>'to_state'='returned_to_strategy'
 AND (e.context_json::jsonb->>'version')::integer=ver AND length(trim(e.reason))>0);
$$ LANGUAGE sql;"""


# A1-F2: BEFORE rejects a revision while a live candidate exists (no workflow
# path materializes then); the deferred row re-checks at commit that a revision
# of a managed report (live candidate or release) is a candidate's own
# materialization. Approvals: a candidate-bound freeze needs the current final
# authority's exact final_approve event (BEFORE) and its decision (deferred).
OWNER=r"""CREATE FUNCTION civensa_activity_revision_owner_guard() RETURNS trigger AS $$
BEGIN
 PERFORM 1 FROM activity_reports WHERE id=NEW.report_id FOR UPDATE;
 IF TG_WHEN='BEFORE' THEN
 IF EXISTS(SELECT 1 FROM activity_reports rp JOIN report_candidates c ON c.organization_id=rp.organization_id
 AND c.resource_scope='activity_report' AND c.report_key=rp.id::text JOIN report_candidate_states s ON s.candidate_id=c.id
 WHERE rp.id=NEW.report_id AND s.state IN ('assembling','final_review','final_approved'))
 THEN RAISE EXCEPTION 'Workflow-managed Activity report rejects legacy revision'; END IF;
 RETURN NEW;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM report_candidates c JOIN activity_reports rp ON rp.id=NEW.report_id
 JOIN report_candidate_states s ON s.candidate_id=c.id WHERE c.activity_revision_id=NEW.id
 AND c.organization_id=rp.organization_id AND c.resource_scope='activity_report' AND c.report_key=rp.id::text)
 AND civensa_activity_report_managed(NEW.report_id)
 THEN RAISE EXCEPTION 'Workflow-managed Activity report rejects legacy revision'; END IF;
 RETURN NULL;
END; $$ LANGUAGE plpgsql;
CREATE FUNCTION civensa_activity_approval_owner_guard() RETURNS trigger AS $$
DECLARE rep integer;
BEGIN
 SELECT report_id INTO rep FROM activity_report_revisions WHERE id=NEW.report_revision_id;
 PERFORM 1 FROM activity_reports WHERE id=rep FOR UPDATE;
 IF TG_WHEN='BEFORE' THEN
 IF EXISTS(SELECT 1 FROM report_candidates c WHERE c.activity_revision_id=NEW.report_revision_id) THEN
 IF NOT EXISTS(SELECT 1 FROM report_candidates c JOIN report_candidate_states s ON s.candidate_id=c.id
 JOIN final_authority_assignments a ON a.organization_id=c.organization_id AND a.active AND a.user_id=NEW.created_by
 JOIN users u ON u.id=a.user_id AND u.is_active
 JOIN workflow_events e ON e.resource_type='report_candidate' AND e.resource_id=c.id::text AND e.event_type='final_approve'
 WHERE c.activity_revision_id=NEW.report_revision_id AND s.state='final_review' AND e.actor_user_id=NEW.created_by
 AND e.organization_id=c.organization_id AND e.context_json::jsonb->>'sha256'=c.sha256
 AND e.context_json::jsonb->>'from_state'='final_review' AND e.context_json::jsonb->>'to_state'='final_approved'
 AND (e.context_json::jsonb->>'version')::integer=s.version+1)
 THEN RAISE EXCEPTION 'Candidate freeze requires the current final authority decision'; END IF;
 ELSIF civensa_activity_report_managed(rep) THEN RAISE EXCEPTION 'Workflow-managed Activity report rejects legacy approval'; END IF;
 RETURN NEW;
 END IF;
 IF EXISTS(SELECT 1 FROM report_candidates c WHERE c.activity_revision_id=NEW.report_revision_id)
 AND NOT EXISTS(SELECT 1 FROM report_decisions d JOIN report_candidates c ON c.id=d.candidate_id
 JOIN final_authority_assignments a ON a.id=d.assignment_id
 WHERE d.activity_approval_id=NEW.id AND d.action='final_approve' AND c.activity_revision_id=NEW.report_revision_id AND a.user_id=NEW.created_by)
 THEN RAISE EXCEPTION 'Candidate freeze is not bound to its final decision'; END IF;
 RETURN NULL;
END; $$ LANGUAGE plpgsql;"""


# A1-F1 primary prevention backstop: at commit every listed participant of an
# Activity successor carries its own semantic net correction (same function as
# publication). A surviving closed_no_change edit is left to publication.
PARTICIPATION=r"""CREATE FUNCTION civensa_successor_participation_check() RETURNS trigger AS $$
DECLARE m jsonb;
BEGIN
 m=NEW.manifest_json::jsonb;
 IF NEW.resource_scope<>'activity_report' OR NOT (m ? 'predecessor_release_id') THEN RETURN NULL; END IF;
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 -- An empty participant list keeps its pre-A1-P1 behaviour (publication refuses it).
 IF jsonb_typeof(m->'correction_request_grants') IS DISTINCT FROM 'array'
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(m->'correction_request_grants') b WHERE NOT EXISTS(
 SELECT 1 FROM revision_requests r JOIN revision_request_states st ON st.request_id=r.id
 WHERE r.id=(b->>'request_id')::integer AND r.source_release_id=(m->>'predecessor_release_id')::integer
 -- Deferred: a same-transaction publication may already have applied the request.
 AND (st.state='editing' OR (st.state='applied' AND EXISTS(SELECT 1 FROM report_releases rr WHERE rr.candidate_id=NEW.id)))
 AND civensa_successor_request_participates(NEW.id,r.id)))
 THEN RAISE EXCEPTION 'Successor participant has no semantic net correction'; END IF;
 -- A surviving closed_no_change edit stays a publication refusal (S3C-2 B2):
 -- refusing it here would remove the return/reopen exit that reverts it.
 RETURN NULL;
END; $$ LANGUAGE plpgsql;"""


# A1-F5: the supported deactivation terminates the director's delegations in the
# same transaction before the membership row changes; a raw deactivation that
# leaves one active is refused (history is never edited, only appended).
DIRECTOR=r"""CREATE FUNCTION civensa_director_deactivation_guard() RETURNS trigger AS $$
BEGIN
 IF OLD.active AND NOT NEW.active AND OLD.role_code='department_director' AND EXISTS(SELECT 1 FROM authority_delegations a
 WHERE a.director_membership_id=OLD.id AND a.active AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id))
 THEN RAISE EXCEPTION 'Director delegation must be terminated with the director membership'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


# A1-F1: 264bdce59301 transition list plus the controlled final_approved -> returned_to_strategy exit.
STATE=r"""CREATE OR REPLACE FUNCTION report_state_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN
          IF TG_OP='DELETE' OR NEW.candidate_id<>OLD.candidate_id OR NEW.version<>OLD.version+1
            OR NOT ((OLD.state='assembling' AND NEW.state='final_review') OR
              (OLD.state='final_review' AND NEW.state IN ('returned_to_strategy','final_approved')) OR
              (OLD.state='final_approved' AND NEW.state IN ('final_approved','published')) OR
              (OLD.state='final_approved' AND NEW.state='returned_to_strategy' AND civensa_final_approved_return(OLD.candidate_id,NEW.version)))
            OR NOT EXISTS(SELECT 1 FROM workflow_events e WHERE e.resource_type='report_candidate'
              AND e.resource_id=OLD.candidate_id::text AND e.context_json::jsonb->>'from_state'=OLD.state
              AND e.context_json::jsonb->>'to_state'=NEW.state AND (e.context_json::jsonb->>'version')::int=NEW.version)
            THEN RAISE EXCEPTION 'Unaudited/invalid report state transition'; END IF; RETURN NEW; END; $$;"""


# A1-F1: a final decision binds only an active assignment of an active user.
BINDING=r"""CREATE OR REPLACE FUNCTION report_binding_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN
          IF TG_TABLE_NAME='report_candidates' THEN
            IF NEW.payload_sha256<>encode(sha256(convert_to(NEW.payload_json,'UTF8')),'hex') OR
               NEW.sha256<>encode(sha256(convert_to('{"manifest":'||NEW.manifest_json||',"payload":'||NEW.payload_json||'}','UTF8')),'hex')
               THEN RAISE EXCEPTION 'Candidate hash mismatch'; END IF;
          ELSIF TG_TABLE_NAME='candidate_packages' THEN
            IF NOT EXISTS(SELECT 1 FROM package_revisions r JOIN package_decisions d ON d.id=NEW.strategy_decision_id
              WHERE r.id=NEW.package_revision_id AND r.sha256=NEW.sha256 AND d.package_revision_id=r.id
              AND d.snapshot_sha256=r.sha256 AND d.action='strategy_approve') THEN RAISE EXCEPTION 'Package binding mismatch'; END IF;
          ELSIF TG_TABLE_NAME='report_decisions' THEN
            IF NOT EXISTS(SELECT 1 FROM report_candidates c JOIN final_authority_assignments a ON a.id=NEW.assignment_id
              JOIN users au ON au.id=a.user_id
              JOIN workflow_events e ON e.id=NEW.workflow_event_id WHERE c.id=NEW.candidate_id AND c.sha256=NEW.candidate_sha256
              AND a.organization_id=c.organization_id AND a.active AND au.is_active AND e.actor_user_id=a.user_id AND e.resource_type='report_candidate'
              AND e.resource_id=c.id::text AND e.event_type=NEW.action) THEN RAISE EXCEPTION 'Final decision binding mismatch'; END IF;
          ELSIF TG_TABLE_NAME='report_artifacts' THEN
            IF NEW.sha256<>encode(sha256(convert_to(NEW.content_json,'UTF8')),'hex') OR NEW.byte_size<>octet_length(convert_to(NEW.content_json,'UTF8'))
              THEN RAISE EXCEPTION 'Artifact bytes/hash mismatch'; END IF;
          ELSIF TG_TABLE_NAME='report_releases' THEN
            IF NOT EXISTS(SELECT 1 FROM report_candidates c JOIN report_decisions d ON d.id=NEW.final_decision_id
                JOIN final_authority_assignments a ON a.id=d.assignment_id JOIN users u ON u.id=a.user_id
                WHERE c.id=NEW.candidate_id AND d.candidate_id=c.id AND d.action='final_approve'
                AND d.candidate_sha256=c.sha256 AND a.active AND u.is_active AND a.organization_id=c.organization_id
                AND NEW.organization_id=c.organization_id AND NEW.resource_scope=c.resource_scope AND NEW.report_key=c.report_key)
                THEN RAISE EXCEPTION 'Release authority/content mismatch'; END IF;
            IF NEW.publication_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM publications p JOIN report_candidates c ON c.id=NEW.candidate_id
                WHERE p.id=NEW.publication_id AND p.snapshot_json=c.payload_json AND p.sha256=c.payload_sha256 AND p.period_id=c.period_id)
                THEN RAISE EXCEPTION 'Publication candidate mismatch'; END IF;
            IF NEW.activity_approval_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM activity_report_approvals a JOIN report_candidates c ON c.id=NEW.candidate_id
                WHERE a.id=NEW.activity_approval_id AND a.report_revision_id=c.activity_revision_id)
                THEN RAISE EXCEPTION 'Activity freeze mismatch'; END IF;
          END IF; RETURN NEW; END; $$;"""


# A1-F3: 8ca1def15967 body; only derived deviation leaves are excluded, the deviation container compares without them.
PARTICIPATES=r"""CREATE OR REPLACE FUNCTION civensa_successor_request_participates(cid integer, rid integer) RETURNS boolean
    LANGUAGE sql
    AS $$
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
 AND l.id<>p.opening_revision_id AND (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(f.field_key::jsonb) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path AND NOT civensa_derived_deviation_key(f.field_key::jsonb)
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (p.source_content #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE civensa_net_value(f.field_key::jsonb,p.source_content #> address.keys) IS DISTINCT FROM civensa_net_value(f.field_key::jsonb,p.bound_content #> address.keys) END
 AND f.previous_json::jsonb IS DISTINCT FROM f.new_json::jsonb
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> address.keys,'null'::jsonb) AND f.new_json::jsonb=coalesce(l.content_json::jsonb #> address.keys,'null'::jsonb));
 $$;"""


# A1-F3: 3942a5669b80 body with the same deviation semantics.
SURVIVES=r"""CREATE OR REPLACE FUNCTION civensa_closed_request_survives(cid integer, rid integer) RETURNS boolean
    LANGUAGE sql
    AS $$
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
 AND EXISTS(SELECT 1 FROM revision_request_states closed WHERE closed.request_id=r.id AND closed.state='closed_no_change')
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
 AND l.id<>p.opening_revision_id AND (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(f.field_key::jsonb) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path AND NOT civensa_derived_deviation_key(f.field_key::jsonb)
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (p.source_content #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE civensa_net_value(f.field_key::jsonb,p.source_content #> address.keys) IS DISTINCT FROM civensa_net_value(f.field_key::jsonb,p.bound_content #> address.keys) END
 AND f.previous_json::jsonb IS DISTINCT FROM f.new_json::jsonb
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> address.keys,'null'::jsonb) AND f.new_json::jsonb=coalesce(l.content_json::jsonb #> address.keys,'null'::jsonb)
 AND (jsonb_typeof(f.previous_json::jsonb) IN ('object','array') OR jsonb_typeof(f.new_json::jsonb) IN ('object','array')
 OR (NOT CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (l.content_json::jsonb #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE civensa_net_value(f.field_key::jsonb,l.content_json::jsonb #> address.keys) IS DISTINCT FROM civensa_net_value(f.field_key::jsonb,p.bound_content #> address.keys) END
 AND NOT EXISTS(SELECT 1 FROM lineage later WHERE later.package_id=l.package_id AND later.revision>l.revision
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (l.content_json::jsonb #>> address.keys)::numeric IS DISTINCT FROM (later.content_json::jsonb #>> address.keys)::numeric ELSE civensa_net_value(f.field_key::jsonb,l.content_json::jsonb #> address.keys) IS DISTINCT FROM civensa_net_value(f.field_key::jsonb,later.content_json::jsonb #> address.keys) END))));
 $$;"""


# A1-F5: 8ca1def15967 body; a delegation suppresses primary authority only while its own director membership/user is active.
AUTHORITY=r"""CREATE OR REPLACE FUNCTION civensa_correction_decision_authorized(did integer, pid integer) RETURNS boolean
    LANGUAGE sql
    AS $$
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
 AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id)
 AND EXISTS(SELECT 1 FROM directorate_memberships od JOIN users ou ON ou.id=od.user_id WHERE od.id=a.director_membership_id
 AND od.active AND ou.is_active AND od.role_code='department_director' AND od.organization_id=p.organization_id AND od.department_id=p.department_id)))
 OR EXISTS(SELECT 1 FROM authority_delegations a JOIN directorate_memberships m ON m.id=a.delegate_membership_id
 WHERE a.id=d.delegation_id AND a.organization_id=p.organization_id AND a.department_id=p.department_id
 AND a.director_membership_id=dm.id AND a.active AND a.start_at<=clock_timestamp() AND clock_timestamp()<a.end_at
 AND NOT EXISTS(SELECT 1 FROM delegation_revocations v WHERE v.delegation_id=a.id)
 AND m.active AND m.user_id=u.id AND m.organization_id=p.organization_id AND m.department_id=p.department_id AND m.role_code='department_editor'))))))))
$$;"""


# K-7: 8ca1def15967 body; historical lineage authorization replaces the live-grant requirement for review transitions.
PROJECTION=r"""CREATE OR REPLACE FUNCTION civensa_revision_projection_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
 -- K-7: a grant authorizes the edit, not the later review. Every content change
 -- since the opening must have been authorized when it was made.
 IF NOT civensa_correction_lineage_authorized(c.id,prior.id)
 THEN RAISE EXCEPTION 'Correction lineage is not historically authorized'; END IF;
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
END; $$;"""


# K-7/A1-F3: 8ca1def15967 body; return copies need no live grant; only corrective_action is correctable inside deviation.
EDIT=r"""CREATE OR REPLACE FUNCTION civensa_revision_edit_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
 IF NOT authorized AND NOT civensa_derived_deviation_key(change) THEN RAISE EXCEPTION 'Correction exceeds granted cell scope'; END IF;
 -- A1-F3: inside deviation only corrective_action is user content.
 IF jsonb_array_length(change)>=4 AND change->>0='entries' AND change->>2='deviation' AND change->>3<>'corrective_action'
 AND NOT civensa_derived_deviation_key(change) THEN RAISE EXCEPTION 'Deviation field is not correctable'; END IF;
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
END; $$;"""


# K-7: 8ca1def15967 body; renewal needs no returned successor attempt, only no live successor.
RENEWAL=r"""CREATE OR REPLACE FUNCTION civensa_renewal_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE g revision_edit_grants%ROWTYPE; r revision_requests%ROWTYPE;
BEGIN
 SELECT * INTO r FROM revision_requests WHERE id=NEW.request_id;
 PERFORM 1 FROM organizations WHERE id=r.organization_id FOR UPDATE;
 SELECT * INTO g FROM revision_edit_grants WHERE id=NEW.original_grant_id;
 IF g.id IS NULL OR (NEW.request_id,NEW.cycle_id,NEW.source_release_id) IS DISTINCT FROM (g.request_id,g.cycle_id,g.source_release_id)
 OR g.end_at>clock_timestamp() OR NOT civensa_revision_current(g.source_release_id) OR civensa_live_successor(g.source_release_id)
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
END; $$;"""


# A1-F1: 6a8fcbd93745 body; closed_no_change is refused while a live successor lists the request.
REQUEST_STATE=r"""CREATE OR REPLACE FUNCTION civensa_revision_state_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
 IF NEW.state='closed_no_change' AND EXISTS(SELECT 1 FROM report_candidates lc JOIN report_candidate_states ls ON ls.candidate_id=lc.id
 WHERE ls.state IN ('assembling','final_review','final_approved')
 AND lc.manifest_json::jsonb->>'predecessor_release_id'=r.source_release_id::text
 AND lc.manifest_json::jsonb->'correction_request_grants' @> jsonb_build_array(jsonb_build_object('request_id',r.id)))
 THEN RAISE EXCEPTION 'Live successor lists this correction request'; END IF;
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
END; $$;"""
