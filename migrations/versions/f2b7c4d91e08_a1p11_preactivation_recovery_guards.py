"""A1-P1.1 pre-activation recovery paths: R10 initial-candidate return/rework and TE-1 direct cycle reopen.

PostgreSQL (one coherent forward migration on c5e8a1f0b247; existing rows are never re-checked):
- R10: civensa_final_approved_return now also admits an unpublished INITIAL
  Activity candidate (no release for the candidate or its report); the same
  current, active, non-Strategy final authority and reasoned exact decision.
  civensa_activity_initial_candidate_guard binds every new initial Activity
  candidate to its lineage: a first candidate has sequence 1 and no
  predecessor/rework keys; any later initial candidate reworks EXACTLY the
  report's latest candidate, which must be a returned initial attempt
  (civensa_returned_initial_attempt), with predecessor_candidate_id, sequence+1,
  manifest reworks_candidate_id/sha256, the same source and required
  departments, and a fresh materialization directly after the attempt's.
  strategy_reopen of a package with no correction cycle is admitted only as an
  audited initial-rework reopen (civensa_initial_rework_reopen), and a new
  BEFORE UPDATE guard refuses any other move of a candidate-bound, unpublished
  initial Activity package out of strategy_approved.
- TE-1: strategy_reopen of a correction package is admitted either after a
  returned successor attempt (S3C-2, unchanged) or by an audited direct reopen
  for a NEW accepted, not yet granted request of the same cycle
  (civensa_direct_cycle_reopen: correction_cycle_reopened event + exact
  strategy_reopen decision). The decision, projection and exact-copy revision
  guards accept exactly these two provenances. The direct reopen is refused while
  another accepted/editing request claims an overlapping cell.
- SEC-A1: one Activity revision belongs to at most one candidate (partial unique
  index); a final decision's freeze must sit on its candidate's revision and a
  release must carry exactly its final decision's freeze.
- SEC-B1: a grant joins only a returned (editable) correction package.
- SEC-1/DB-1/WF-1: a candidate-bound, unpublished initial Activity package never
  moves or changes revision without its exact audited decision or an edit while
  returned; an initial candidate binds each package's current approved revision
  exactly as its manifest lists it and is complete (state, event, bindings) at
  commit (deferred constraint trigger).
SQLite: a unique index and new triggers only (no table rebuild): initial
Activity candidate lineage, terminal returned/published candidate states, an
exact final_return decision before any release of the report for
final_approved -> returned_to_strategy, and the release freeze binding. Package
reopen stays PostgreSQL-only (existing 'Reopen requires PostgreSQL' trigger).
"""
from alembic import op
revision='f2b7c4d91e08'
down_revision='c5e8a1f0b247'
branch_labels=depends_on=None


def upgrade():
    if op.get_bind().dialect.name=='postgresql':
        op.execute(UNIQUE_PRECHECK)
        op.execute(UNIQUE_REVISION)
        for sql in (HELPERS,FINAL_RETURN,INITIAL_CANDIDATE,REOPEN_DECISION,PROJECTION,EDIT,INITIAL_PACKAGE,BINDING,GRANT,INITIAL_BINDING,INITIAL_COMPLETE):
            op.execute(sql)
        op.execute('CREATE TRIGGER initial_rework_package_reopen BEFORE UPDATE ON directorate_packages FOR EACH ROW EXECUTE FUNCTION civensa_initial_package_reopen_guard()')
        op.execute('CREATE TRIGGER initial_candidate_package_current BEFORE INSERT ON candidate_packages FOR EACH ROW EXECUTE FUNCTION civensa_initial_candidate_binding_guard()')
        op.execute('CREATE CONSTRAINT TRIGGER initial_candidate_complete AFTER INSERT ON report_candidates DEFERRABLE INITIALLY DEFERRED '
                   'FOR EACH ROW EXECUTE FUNCTION civensa_initial_candidate_complete()')
    else:
        if op.get_bind().exec_driver_sql('SELECT activity_revision_id FROM report_candidates WHERE activity_revision_id IS NOT NULL GROUP BY activity_revision_id HAVING count(*)>1 LIMIT 1').first():
            raise RuntimeError('Two report candidates share one Activity revision; resolve before upgrading')
        op.execute(UNIQUE_REVISION)
        op.execute("""CREATE TRIGGER activity_release_freeze_binding BEFORE INSERT ON report_releases WHEN NEW.activity_approval_id IS NOT NULL
            AND NOT EXISTS(SELECT 1 FROM report_decisions d WHERE d.id=NEW.final_decision_id AND d.activity_approval_id=NEW.activity_approval_id)
            BEGIN SELECT RAISE(ABORT,'Activity release freeze must be its final decision freeze'); END""")
        op.execute(f"""CREATE TRIGGER activity_initial_rework_lineage BEFORE INSERT ON report_candidates WHEN
            NEW.resource_scope='activity_report' AND json_extract(NEW.manifest_json,'$.predecessor_release_id') IS NULL AND (CASE WHEN {SQLITE_LATEST}.id IS NULL
            THEN NEW.sequence<>1 OR NEW.predecessor_candidate_id IS NOT NULL OR json_type(NEW.manifest_json,'$.reworks_candidate_id') IS NOT NULL
              OR json_type(NEW.manifest_json,'$.reworks_candidate_sha256') IS NOT NULL
            ELSE 1 END)
            BEGIN SELECT RAISE(ABORT,'Invalid initial Activity candidate lineage'); END""".replace(f'{SQLITE_LATEST}.id IS NULL',
            "NOT EXISTS(SELECT 1 FROM report_candidates o WHERE o.organization_id=NEW.organization_id AND o.resource_scope=NEW.resource_scope AND o.report_key=NEW.report_key)")
            .replace('ELSE 1 END',f"""ELSE NOT EXISTS(SELECT 1 FROM {SQLITE_LATEST} latest JOIN report_candidate_states s ON s.candidate_id=latest.id
              JOIN report_decisions d ON d.candidate_id=latest.id AND d.action='final_return' AND d.candidate_sha256=latest.sha256
              WHERE s.state='returned_to_strategy' AND json_extract(latest.manifest_json,'$.predecessor_release_id') IS NULL
              AND NEW.predecessor_candidate_id=latest.id AND NEW.sequence=latest.sequence+1
              AND json_extract(NEW.manifest_json,'$.reworks_candidate_id')=latest.id
              AND json_extract(NEW.manifest_json,'$.reworks_candidate_sha256')=latest.sha256
              AND NEW.period_id IS latest.period_id
              AND json_extract(NEW.manifest_json,'$.source_id') IS json_extract(latest.manifest_json,'$.source_id')
              AND json_extract(NEW.manifest_json,'$.required_department_ids') IS json_extract(latest.manifest_json,'$.required_department_ids')
              AND EXISTS(SELECT 1 FROM activity_report_revisions dst JOIN activity_report_revisions src ON src.id=latest.activity_revision_id
                WHERE dst.id=NEW.activity_revision_id AND dst.previous_revision_id=src.id AND dst.report_id=src.report_id AND dst.revision=src.revision+1
                AND dst.publication_id IS src.publication_id)) END"""))
        op.execute("""CREATE TRIGGER report_state_terminal BEFORE UPDATE ON report_candidate_states WHEN OLD.state IN ('returned_to_strategy','published')
            BEGIN SELECT RAISE(ABORT,'Terminal report candidate state'); END""")
        op.execute("""CREATE TRIGGER report_state_final_return BEFORE UPDATE ON report_candidate_states WHEN
            OLD.state='final_approved' AND NEW.state='returned_to_strategy' AND (NOT EXISTS(SELECT 1 FROM report_candidates c
              JOIN report_decisions d ON d.candidate_id=c.id AND d.action='final_return' AND d.candidate_sha256=c.sha256
              JOIN workflow_events e ON e.id=d.workflow_event_id JOIN final_authority_assignments a ON a.id=d.assignment_id
              JOIN users u ON u.id=a.user_id
              WHERE c.id=OLD.candidate_id AND c.resource_scope='activity_report' AND a.active AND u.is_active AND u.role<>'strategy'
              AND a.organization_id=c.organization_id AND e.organization_id=c.organization_id
              AND e.actor_user_id=a.user_id AND e.event_type='final_return' AND length(trim(e.reason))>0)
              OR EXISTS(SELECT 1 FROM report_releases r JOIN report_candidates c ON c.id=OLD.candidate_id
                WHERE r.candidate_id=c.id OR (r.organization_id=c.organization_id AND r.resource_scope=c.resource_scope AND r.report_key=c.report_key
                AND json_extract(c.manifest_json,'$.predecessor_release_id') IS NULL)))
            BEGIN SELECT RAISE(ABORT,'Final-approved return requires an exact final_return decision before publication'); END""")


def downgrade():
    raise RuntimeError('A1-P1.1 recovery guards cannot be discarded')


# WF-R10-RAW / SEC-A1: every materialization is a fresh revision, so one Activity
# revision (and its freeze) can belong to at most one candidate.
UNIQUE_PRECHECK=r"""DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM report_candidates WHERE activity_revision_id IS NOT NULL GROUP BY activity_revision_id HAVING count(*)>1)
 THEN RAISE EXCEPTION 'Two report candidates share one Activity revision; resolve before upgrading'; END IF;
END $$"""
UNIQUE_REVISION='CREATE UNIQUE INDEX uq_report_candidate_activity_revision ON report_candidates (activity_revision_id) WHERE activity_revision_id IS NOT NULL'


# The report's latest candidate (highest sequence), as a SQLite subquery.
SQLITE_LATEST="""(SELECT * FROM report_candidates o WHERE o.organization_id=NEW.organization_id AND o.resource_scope=NEW.resource_scope
              AND o.report_key=NEW.report_key ORDER BY o.sequence DESC LIMIT 1)"""


# R10: a returned, never-successor initial Activity attempt with its exact reasoned
# final_return (mirrors report_workflow_service.final_return_proof/returned_initial_proof).
# TE-1: an audited direct reopen of a correction cycle for a NEW accepted, ungranted
# request (mirrors revision_workflow_service.reopen_cycle).
HELPERS=r"""CREATE FUNCTION civensa_returned_initial_attempt(cid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM report_candidates c JOIN report_candidate_states s ON s.candidate_id=c.id
 JOIN report_decisions d ON d.candidate_id=c.id JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE c.id=cid AND c.resource_scope='activity_report' AND NOT (c.manifest_json::jsonb ? 'predecessor_release_id')
 AND s.state='returned_to_strategy' AND d.action='final_return' AND d.candidate_sha256=c.sha256 AND e.event_type='final_return'
 AND e.resource_type='report_candidate' AND e.resource_id=c.id::text AND e.organization_id=c.organization_id
 AND e.context_json::jsonb->>'sha256'=c.sha256 AND length(trim(e.reason))>0);
$$ LANGUAGE sql VOLATILE;
CREATE FUNCTION civensa_initial_rework_reopen(eid integer,revid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM workflow_events e JOIN users u ON u.id=e.actor_user_id
 JOIN package_revisions rev ON rev.id=revid JOIN directorate_packages p ON p.id=rev.package_id
 JOIN activity_report_revisions source ON source.id=p.report_revision_id JOIN activity_reports rp ON rp.id=source.report_id
 JOIN report_candidates c ON c.id=(e.context_json::jsonb->>'initial_rework_candidate_id')::integer
 JOIN activity_report_revisions mat ON mat.id=c.activity_revision_id
 WHERE e.id=eid AND e.event_type='strategy_reopen' AND e.resource_type='directorate_package' AND e.resource_id=p.id::text
 AND u.is_active AND u.role='strategy' AND e.organization_id=p.organization_id AND e.department_id=p.department_id
 AND length(trim(e.reason))>0 AND e.context_json::jsonb->>'initial_rework_candidate_sha256'=c.sha256
 AND p.resource_scope='activity_report' AND rp.organization_id=p.organization_id
 AND NOT EXISTS(SELECT 1 FROM revision_correction_cycles cy WHERE cy.package_id=p.id)
 AND NOT EXISTS(SELECT 1 FROM report_releases r WHERE r.organization_id=rp.organization_id AND r.resource_scope='activity_report' AND r.report_key=rp.id::text)
 AND c.organization_id=rp.organization_id AND c.resource_scope='activity_report' AND c.report_key=rp.id::text
 AND c.sequence=(SELECT max(o.sequence) FROM report_candidates o WHERE o.organization_id=c.organization_id
 AND o.resource_scope=c.resource_scope AND o.report_key=c.report_key)
 AND civensa_returned_initial_attempt(c.id) AND c.manifest_json::jsonb->'source_id'=to_jsonb(source.id)
 AND EXISTS(SELECT 1 FROM jsonb_array_elements(c.manifest_json::jsonb->'packages') b WHERE b->'package_id'=to_jsonb(p.id))
 AND mat.report_id=rp.id AND rp.current_revision=mat.revision);
$$ LANGUAGE sql VOLATILE;
CREATE FUNCTION civensa_direct_cycle_reopen(eid integer,revid integer,cyc integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM workflow_events pe JOIN revision_correction_cycles c ON c.id=cyc
 JOIN package_revisions rev ON rev.id=revid
 JOIN revision_requests q ON q.id=(pe.context_json::jsonb->>'reopen_request_id')::integer
 JOIN revision_request_states qs ON qs.request_id=q.id
 JOIN workflow_events re ON re.id=(pe.context_json::jsonb->>'reopen_event_id')::integer
 JOIN users u ON u.id=re.actor_user_id
 WHERE pe.id=eid AND pe.event_type='strategy_reopen' AND pe.resource_type='directorate_package' AND pe.resource_id=c.package_id::text
 AND rev.package_id=c.package_id AND pe.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND re.event_type='correction_cycle_reopened' AND re.resource_type='revision_request' AND re.resource_id=q.id::text
 AND re.id<pe.id AND re.actor_user_id=pe.actor_user_id AND u.is_active AND u.role='strategy'
 AND re.organization_id=q.organization_id AND re.department_id=q.department_id AND length(trim(re.reason))>0
 AND re.context_json::jsonb->>'request_id'=q.id::text AND re.context_json::jsonb->>'source_release_id'=c.source_release_id::text
 AND re.context_json::jsonb->>'cycle_id'=c.id::text AND re.context_json::jsonb->>'package_id'=c.package_id::text
 AND re.context_json::jsonb->>'previous_revision_id'=rev.id::text AND re.context_json::jsonb->>'previous_sha256'=rev.sha256
 AND q.source_release_id=c.source_release_id AND q.source_package_revision_id=c.source_package_revision_id
 AND qs.state='accepted' AND NOT EXISTS(SELECT 1 FROM revision_edit_grants g WHERE g.request_id=q.id)
 -- No other accepted/editing request of the release and department may claim an overlapping cell.
 AND NOT EXISTS(SELECT 1 FROM revision_requests o JOIN revision_request_states os ON os.request_id=o.id
 CROSS JOIN LATERAL jsonb_array_elements(o.patches_json::jsonb) op CROSS JOIN LATERAL jsonb_array_elements(q.patches_json::jsonb) qp
 WHERE o.source_release_id=q.source_release_id AND o.department_id=q.department_id AND o.id<>q.id
 AND os.state IN ('accepted','editing') AND op->'path'=qp->'path'));
$$ LANGUAGE sql VOLATILE;"""


# R10: c5e8a1f0b247 body; an initial Activity candidate qualifies while neither it nor its report is published.
FINAL_RETURN=r"""CREATE OR REPLACE FUNCTION civensa_final_approved_return(cid integer,ver integer) RETURNS boolean AS $$
 SELECT NOT EXISTS(SELECT 1 FROM report_releases rr WHERE rr.candidate_id=cid)
 AND EXISTS(SELECT 1 FROM report_decisions d JOIN report_candidates c ON c.id=d.candidate_id
 JOIN workflow_events e ON e.id=d.workflow_event_id JOIN final_authority_assignments a ON a.id=d.assignment_id
 JOIN users u ON u.id=a.user_id
 WHERE d.candidate_id=cid AND d.action='final_return' AND d.candidate_sha256=c.sha256
 AND c.resource_scope='activity_report' AND (c.manifest_json::jsonb ? 'predecessor_release_id'
 OR NOT EXISTS(SELECT 1 FROM report_releases rr WHERE rr.organization_id=c.organization_id
 AND rr.resource_scope='activity_report' AND rr.report_key=c.report_key))
 AND a.active AND u.is_active AND u.role<>'strategy' AND a.organization_id=c.organization_id
 AND e.actor_user_id=a.user_id AND e.event_type='final_return' AND e.resource_type='report_candidate'
 AND e.resource_id=cid::text AND e.organization_id=c.organization_id AND e.context_json::jsonb->>'sha256'=c.sha256
 AND e.context_json::jsonb->>'from_state'='final_approved' AND e.context_json::jsonb->>'to_state'='returned_to_strategy'
 AND (e.context_json::jsonb->>'version')::integer=ver AND length(trim(e.reason))>0);
$$ LANGUAGE sql;"""


# R10: the existing published-report refusal plus exact initial lineage for every new initial Activity candidate.
INITIAL_CANDIDATE=r"""CREATE OR REPLACE FUNCTION civensa_activity_initial_candidate_guard() RETURNS trigger AS $$
DECLARE m jsonb; latest report_candidates%ROWTYPE; parent jsonb; src activity_report_revisions%ROWTYPE; dst activity_report_revisions%ROWTYPE;
BEGIN
 IF NEW.resource_scope='activity_report' THEN
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 m=NEW.manifest_json::jsonb;
 IF NOT (m ? 'predecessor_release_id') AND EXISTS(SELECT 1 FROM report_releases
 WHERE organization_id=NEW.organization_id AND resource_scope='activity_report' AND report_key=NEW.report_key)
 THEN RAISE EXCEPTION 'Published Activity requires explicit successor assembly'; END IF;
 IF NOT (m ? 'predecessor_release_id') THEN
 SELECT * INTO latest FROM report_candidates WHERE organization_id=NEW.organization_id AND resource_scope=NEW.resource_scope
 AND report_key=NEW.report_key ORDER BY sequence DESC LIMIT 1;
 IF latest.id IS NULL THEN
 IF NEW.sequence IS DISTINCT FROM 1 OR NEW.predecessor_candidate_id IS NOT NULL OR m ? 'reworks_candidate_id' OR m ? 'reworks_candidate_sha256'
 THEN RAISE EXCEPTION 'Invalid first Activity candidate lineage'; END IF;
 ELSE
 parent=latest.manifest_json::jsonb;
 SELECT * INTO src FROM activity_report_revisions WHERE id=latest.activity_revision_id;
 SELECT * INTO dst FROM activity_report_revisions WHERE id=NEW.activity_revision_id;
 IF NEW.predecessor_candidate_id IS DISTINCT FROM latest.id OR NEW.sequence IS DISTINCT FROM latest.sequence+1
 OR m->'reworks_candidate_id' IS DISTINCT FROM to_jsonb(latest.id) OR m->>'reworks_candidate_sha256' IS DISTINCT FROM latest.sha256
 OR NOT civensa_returned_initial_attempt(latest.id) OR NEW.period_id IS DISTINCT FROM latest.period_id
 OR m->'source_id' IS DISTINCT FROM parent->'source_id' OR m->'required_department_ids' IS DISTINCT FROM parent->'required_department_ids'
 OR (SELECT coalesce(jsonb_agg(b->'package_id' ORDER BY (b->>'package_id')::integer),'[]') FROM jsonb_array_elements(m->'packages') b)
 IS DISTINCT FROM (SELECT coalesce(jsonb_agg(b->'package_id' ORDER BY (b->>'package_id')::integer),'[]') FROM jsonb_array_elements(parent->'packages') b)
 OR dst.id IS NULL OR src.id IS NULL OR dst.previous_revision_id IS DISTINCT FROM src.id OR dst.report_id IS DISTINCT FROM src.report_id
 OR dst.revision IS DISTINCT FROM src.revision+1 OR dst.publication_id IS DISTINCT FROM src.publication_id
 OR dst.publication_sha256 IS DISTINCT FROM src.publication_sha256
 THEN RAISE EXCEPTION 'Invalid initial Activity rework lineage'; END IF;
 END IF;
 END IF;
 END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


# 8ca1def15967 body plus the two new provenances: an initial-rework reopen (no
# cycle) and, for a cycle, an audited direct reopen next to the returned attempt.
REOPEN_DECISION=r"""CREATE OR REPLACE FUNCTION civensa_strategy_reopen_decision_guard() RETURNS trigger AS $$
DECLARE p directorate_packages%ROWTYPE; c revision_correction_cycles%ROWTYPE;
BEGIN
 IF NEW.action<>'strategy_reopen' THEN RETURN NEW; END IF;
 SELECT pkg.* INTO p FROM directorate_packages pkg JOIN package_revisions rev ON rev.package_id=pkg.id WHERE rev.id=NEW.package_revision_id;
 PERFORM 1 FROM organizations WHERE id=p.organization_id FOR UPDATE;
 SELECT * INTO c FROM revision_correction_cycles WHERE package_id=p.id ORDER BY id DESC LIMIT 1;
 IF c.id IS NULL THEN
 IF p.state<>'strategy_approved' OR NEW.from_state<>p.state OR NEW.to_state<>'returned' OR NEW.delegation_id IS NOT NULL
 OR NOT civensa_initial_rework_reopen(NEW.workflow_event_id,NEW.package_revision_id)
 THEN RAISE EXCEPTION 'strategy_reopen requires a returned unpublished initial attempt'; END IF;
 IF NOT EXISTS(SELECT 1 FROM workflow_events e JOIN package_revisions rev ON rev.id=NEW.package_revision_id
 WHERE e.id=NEW.workflow_event_id AND rev.revision=p.current_revision AND rev.sha256=NEW.snapshot_sha256
 AND rev.sha256=encode(sha256(convert_to(rev.content_json,'UTF8')),'hex')
 AND e.context_json::jsonb->>'revision_id'=rev.id::text AND e.context_json::jsonb->>'sha256'=rev.sha256
 AND e.context_json::jsonb->>'correction_cycle_id' IS NULL AND e.context_json::jsonb->>'expected_version'=p.version::text
 AND e.context_json::jsonb->>'from_state'=NEW.from_state AND e.context_json::jsonb->>'to_state'=NEW.to_state
 AND e.context_json::jsonb->>'delegation_id' IS NULL AND e.context_json::jsonb->>'returned_revision'=(rev.revision+1)::text)
 THEN RAISE EXCEPTION 'Missing exact Strategy reopen audit'; END IF;
 RETURN NEW;
 END IF;
 IF NOT civensa_revision_current(c.source_release_id) OR civensa_live_successor(c.source_release_id)
 OR NOT (civensa_latest_returned(c.source_release_id) OR civensa_direct_cycle_reopen(NEW.workflow_event_id,NEW.package_revision_id,c.id))
 OR p.state<>'strategy_approved' OR NEW.from_state<>p.state OR NEW.to_state<>'returned'
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


# TE-1: c5e8a1f0b247 body; the current-release strategy_reopen branch also accepts an audited direct reopen.
PROJECTION=r"""CREATE OR REPLACE FUNCTION civensa_revision_projection_guard()
 RETURNS trigger
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
 AND NOT civensa_live_successor(c.source_release_id)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.action='strategy_reopen' AND d.from_state=OLD.state AND d.to_state=NEW.state
 AND civensa_correction_decision_authorized(d.id,OLD.id) AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.current_revision::text
 AND length(trim(e.reason))>0
 -- A1-P1.1 TE-1: a returned successor attempt OR an audited direct reopen for a NEW accepted request.
 AND (civensa_latest_returned(c.source_release_id) OR civensa_direct_cycle_reopen(e.id,prior.id,c.id))) THEN RETURN NEW; END IF;
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
END; $$"""


# TE-1: c5e8a1f0b247 body; the exact-copy reopen revision accepts the same two provenances.
EDIT=r"""CREATE OR REPLACE FUNCTION civensa_revision_edit_guard()
 RETURNS trigger
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
 AND NOT civensa_live_successor(c.source_release_id)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id JOIN directorate_packages p ON p.id=NEW.package_id
 WHERE d.package_revision_id=prior.id AND d.action='strategy_reopen' AND d.from_state='strategy_approved' AND p.state=d.from_state AND d.to_state='returned'
 AND civensa_correction_decision_authorized(d.id,p.id) AND e.actor_user_id=NEW.created_by AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=p.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.revision::text AND length(trim(e.reason))>0
 -- A1-P1.1 TE-1: same two reopen provenances as the projection guard.
 AND (civensa_latest_returned(c.source_release_id) OR civensa_direct_cycle_reopen(e.id,prior.id,c.id))) THEN RETURN NEW; END IF;

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
END; $$"""


# R10 (+ SEC-1, DB-1): an unpublished initial Activity package bound by any
# candidate never moves without its exact audited decision. It leaves
# strategy_approved only through an audited initial-rework strategy_reopen with an
# exact-copy append-only revision; every other state change needs the exact
# package decision on its current revision; its revision/source change in place
# only by an edit while it is returned. Correction packages (cycle) and published
# reports keep their own guards.
INITIAL_PACKAGE=r"""CREATE FUNCTION civensa_initial_package_reopen_guard() RETURNS trigger AS $$
DECLARE prior package_revisions%ROWTYPE; next package_revisions%ROWTYPE;
BEGIN
 IF OLD.resource_scope<>'activity_report' THEN RETURN NEW; END IF;
 IF NEW.state=OLD.state AND NEW.current_revision=OLD.current_revision AND NEW.report_revision_id IS NOT DISTINCT FROM OLD.report_revision_id THEN RETURN NEW; END IF;
 IF EXISTS(SELECT 1 FROM revision_correction_cycles WHERE package_id=OLD.id) THEN RETURN NEW; END IF;
 IF NOT EXISTS(SELECT 1 FROM candidate_packages b JOIN package_revisions r ON r.id=b.package_revision_id WHERE r.package_id=OLD.id) THEN RETURN NEW; END IF;
 IF EXISTS(SELECT 1 FROM activity_report_revisions s JOIN report_releases r ON r.organization_id=OLD.organization_id
 AND r.resource_scope='activity_report' AND r.report_key=s.report_id::text WHERE s.id=OLD.report_revision_id) THEN RETURN NEW; END IF;
 IF NEW.report_revision_id IS DISTINCT FROM OLD.report_revision_id THEN RAISE EXCEPTION 'Candidate-bound package requires an audited initial rework reopen'; END IF;
 SELECT * INTO prior FROM package_revisions WHERE package_id=OLD.id AND revision=OLD.current_revision;
 SELECT * INTO next FROM package_revisions WHERE package_id=OLD.id AND revision=NEW.current_revision;
 IF OLD.state='strategy_approved' THEN
 IF NEW.state='returned' AND NEW.current_revision=OLD.current_revision+1 AND next.previous_revision_id=prior.id
 AND next.content_json=prior.content_json AND next.sha256=prior.sha256
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.snapshot_sha256=prior.sha256 AND d.action='strategy_reopen'
 AND d.from_state='strategy_approved' AND d.to_state='returned'
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text AND e.context_json::jsonb->>'returned_revision'=NEW.current_revision::text
 AND e.context_json::jsonb->>'next_revision_id'=next.id::text AND civensa_initial_rework_reopen(e.id,prior.id))
 THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Candidate-bound package requires an audited initial rework reopen';
 END IF;
 -- An edit of the reopened (returned) package: a new append-only revision, same state.
 IF NEW.state=OLD.state THEN
 IF OLD.state='returned' AND NEW.current_revision=OLD.current_revision+1 AND next.previous_revision_id=prior.id THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Candidate-bound package requires an audited initial rework reopen';
 END IF;
 -- Review transitions: the exact decision on the current revision; returns append an exact copy.
 IF EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 WHERE d.package_revision_id=prior.id AND d.snapshot_sha256=prior.sha256 AND d.from_state=OLD.state AND d.to_state=NEW.state
 AND e.context_json::jsonb->>'expected_version'=OLD.version::text AND e.resource_type='directorate_package' AND e.resource_id=OLD.id::text)
 AND (NEW.current_revision=OLD.current_revision OR (NEW.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND next.previous_revision_id=prior.id AND next.content_json=prior.content_json AND next.sha256=prior.sha256))
 THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Candidate-bound package transition requires its exact package decision';
END; $$ LANGUAGE plpgsql;"""


# DB-1: an initial Activity candidate binds each package's CURRENT Strategy-approved
# revision, exactly as listed in its manifest (successors keep their own check).
INITIAL_BINDING=r"""CREATE FUNCTION civensa_initial_candidate_binding_guard() RETURNS trigger AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM report_candidates c WHERE c.id=NEW.candidate_id AND c.resource_scope='activity_report'
 AND NOT (c.manifest_json::jsonb ? 'predecessor_release_id')) THEN RETURN NEW; END IF;
 IF NOT EXISTS(SELECT 1 FROM report_candidates c JOIN package_revisions r ON r.id=NEW.package_revision_id
 JOIN directorate_packages p ON p.id=r.package_id
 JOIN jsonb_array_elements(c.manifest_json::jsonb->'packages') b ON (b->>'package_id')::integer=p.id
 WHERE c.id=NEW.candidate_id AND p.state='strategy_approved' AND p.current_revision=r.revision
 AND (b->>'revision_id')::integer=r.id AND b->>'sha256'=r.sha256)
 THEN RAISE EXCEPTION 'Initial candidate must bind the current approved package revision of its manifest'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""


# WF-1: at commit a new initial Activity candidate is complete: its assembling state,
# its candidate_assembled event and exactly the manifest's package bindings, one
# package per required department; a first candidate materializes the revision
# right after its source (a rework's materialization is checked by the lineage guard).
INITIAL_COMPLETE=r"""CREATE FUNCTION civensa_initial_candidate_complete() RETURNS trigger AS $$
DECLARE m jsonb;
BEGIN
 m=NEW.manifest_json::jsonb;
 IF NEW.resource_scope<>'activity_report' OR m ? 'predecessor_release_id' THEN RETURN NULL; END IF;
 IF jsonb_array_length(coalesce(m->'packages','[]'))=0
 OR (SELECT jsonb_agg(DISTINCT (b->>'department_id')::integer ORDER BY (b->>'department_id')::integer) FROM jsonb_array_elements(m->'packages') b)
    IS DISTINCT FROM m->'required_department_ids'
 OR jsonb_array_length(m->'packages')<>jsonb_array_length(coalesce(m->'required_department_ids','[]'))
 OR (NEW.predecessor_candidate_id IS NULL AND NOT EXISTS(SELECT 1 FROM activity_report_revisions dst
    JOIN activity_report_revisions src ON src.id=(m->>'source_id')::integer
    WHERE dst.id=NEW.activity_revision_id AND dst.previous_revision_id=src.id AND dst.report_id=src.report_id AND dst.revision=src.revision+1))
 THEN RAISE EXCEPTION 'Initial Activity candidate is incomplete at commit'; END IF;
 IF NOT EXISTS(SELECT 1 FROM report_candidate_states s WHERE s.candidate_id=NEW.id)
 OR NOT EXISTS(SELECT 1 FROM workflow_events e WHERE e.resource_type='report_candidate' AND e.resource_id=NEW.id::text
 AND e.event_type='candidate_assembled' AND e.organization_id=NEW.organization_id AND e.context_json::jsonb->>'sha256'=NEW.sha256)
 OR (SELECT count(*) FROM candidate_packages b WHERE b.candidate_id=NEW.id)<>jsonb_array_length(coalesce(m->'packages','[]'))
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(m->'packages','[]')) b WHERE NOT EXISTS(SELECT 1 FROM candidate_packages cp
 WHERE cp.candidate_id=NEW.id AND cp.package_revision_id=(b->>'revision_id')::integer AND cp.sha256=b->>'sha256'))
 THEN RAISE EXCEPTION 'Initial Activity candidate is incomplete at commit'; END IF;
 RETURN NULL;
END; $$ LANGUAGE plpgsql;"""


# SEC-A1: 264bdce59301 body; a decision's freeze must sit on its candidate's
# revision, and a release must carry exactly its final decision's freeze.
BINDING=r"""CREATE OR REPLACE FUNCTION report_binding_guard() RETURNS trigger LANGUAGE plpgsql AS $function$ BEGIN
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
            -- A1-P1.1 SEC-A1: a freeze belongs to the candidate's own materialized revision.
            IF NEW.activity_approval_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM activity_report_approvals ap JOIN report_candidates c ON c.id=NEW.candidate_id
              WHERE ap.id=NEW.activity_approval_id AND ap.report_revision_id=c.activity_revision_id) THEN RAISE EXCEPTION 'Final decision freeze mismatch'; END IF;
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
            -- A1-P1.1 SEC-A1: the released freeze is exactly the final decision's freeze.
            IF NEW.activity_approval_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM report_decisions d
                WHERE d.id=NEW.final_decision_id AND d.activity_approval_id=NEW.activity_approval_id)
                THEN RAISE EXCEPTION 'Activity release freeze must be its final decision freeze'; END IF;
          END IF; RETURN NEW; END; $function$"""


# SEC-B1: 375cefa60412 body; a grant only joins a package that is editable
# (returned) now, so no grant waits on an approved package for a later reopen.
GRANT=r"""CREATE OR REPLACE FUNCTION civensa_revision_grant_guard() RETURNS trigger LANGUAGE plpgsql AS $function$
DECLARE r revision_requests%ROWTYPE; c revision_correction_cycles%ROWTYPE; p jsonb; mid jsonb;
BEGIN
 SELECT * INTO r FROM revision_requests WHERE id=NEW.request_id;
 PERFORM 1 FROM organizations WHERE id=r.organization_id FOR UPDATE;
 PERFORM 1 FROM report_releases WHERE id=r.source_release_id FOR UPDATE;
 SELECT * INTO c FROM revision_correction_cycles WHERE id=NEW.cycle_id;
 IF NEW.source_release_id<>r.source_release_id OR NEW.department_id<>r.department_id OR c.source_release_id<>r.source_release_id
 OR c.source_package_revision_id<>r.source_package_revision_id OR NOT civensa_revision_current(r.source_release_id)
 OR NOT EXISTS(SELECT 1 FROM revision_request_states WHERE request_id=r.id AND state='accepted')
 OR NOT EXISTS(SELECT 1 FROM users WHERE id=NEW.created_by AND is_active AND role='strategy') THEN RAISE EXCEPTION 'Grant scope/state mismatch'; END IF;
 -- A1-P1.1 SEC-B1
 IF NOT EXISTS(SELECT 1 FROM directorate_packages WHERE id=c.package_id AND state='returned') THEN RAISE EXCEPTION 'Grant requires an editable (returned) correction package'; END IF;
 IF jsonb_typeof(NEW.paths_json::jsonb)<>'array' OR jsonb_array_length(NEW.paths_json::jsonb)=0 OR jsonb_typeof(NEW.membership_ids_json::jsonb)<>'array' OR jsonb_array_length(NEW.membership_ids_json::jsonb)=0 THEN RAISE EXCEPTION 'Empty grant scope'; END IF;
 FOR p IN SELECT value FROM jsonb_array_elements(NEW.paths_json::jsonb) LOOP
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(r.patches_json::jsonb) a WHERE a->'path'=p) THEN RAISE EXCEPTION 'Grant exceeds request'; END IF;
 END LOOP;
 FOR mid IN SELECT value FROM jsonb_array_elements(NEW.membership_ids_json::jsonb) LOOP
 IF NOT EXISTS(SELECT 1 FROM directorate_memberships m JOIN users u ON u.id=m.user_id WHERE m.id=mid::text::integer
 AND m.organization_id=r.organization_id AND m.department_id=r.department_id AND m.active AND u.is_active AND u.role='department'
 AND m.role_code IN ('department_editor','department_director')) THEN RAISE EXCEPTION 'Invalid grant membership'; END IF;
 END LOOP;
 NEW.created_at=clock_timestamp(); RETURN NEW;
END; $function$"""
