"""Enable only audited correction package reapproval; no release/runtime activation."""
from alembic import op
revision = '486dfab71523'
down_revision = '375cefa60412'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute(AUTHORITY)
        op.execute(PROJECTION)
        op.execute(EDIT)


def downgrade():
    raise RuntimeError('Correction reapproval history cannot be discarded')


PROJECTION = r"""CREATE OR REPLACE FUNCTION civensa_revision_projection_guard() RETURNS trigger AS $$
DECLARE c revision_correction_cycles%ROWTYPE; prior package_revisions%ROWTYPE; next package_revisions%ROWTYPE;
BEGIN
 SELECT * INTO c FROM revision_correction_cycles WHERE package_id=OLD.id ORDER BY id DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;
 IF NOT civensa_revision_current(c.source_release_id) THEN RAISE EXCEPTION 'Stale correction cycle'; END IF;
 SELECT * INTO prior FROM package_revisions WHERE package_id=OLD.id AND revision=OLD.current_revision;
 SELECT * INTO next FROM package_revisions WHERE package_id=OLD.id AND revision=NEW.current_revision;
 IF NEW.state='returned' AND OLD.state='returned' AND NEW.current_revision=OLD.current_revision+1
 AND next.previous_revision_id=prior.id AND next.content_json<>prior.content_json THEN RETURN NEW; END IF;
 IF NOT EXISTS(SELECT 1 FROM revision_edit_grants g JOIN revision_request_states s ON s.request_id=g.request_id
 WHERE g.cycle_id=c.id AND s.state='editing' AND g.start_at<=clock_timestamp() AND clock_timestamp()<g.end_at)
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

EDIT = r"""CREATE OR REPLACE FUNCTION civensa_revision_edit_guard() RETURNS trigger AS $$
DECLARE c record; g record; prior package_revisions%ROWTYPE; change jsonb; path jsonb; authorized boolean; entry jsonb; target numeric; actual numeric; expected jsonb;
BEGIN
 SELECT cy.* INTO c FROM revision_correction_cycles cy JOIN report_releases r ON r.id=cy.source_release_id
 WHERE cy.package_id=NEW.package_id ORDER BY cy.id DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_releases WHERE id=c.source_release_id) FOR UPDATE;
 IF NOT civensa_revision_current(c.source_release_id) THEN RAISE EXCEPTION 'Stale correction cycle'; END IF;
 SELECT * INTO prior FROM package_revisions WHERE id=NEW.previous_revision_id;
 IF NEW.content_json=prior.content_json AND NEW.sha256=prior.sha256 AND NEW.package_id=prior.package_id AND NEW.revision=prior.revision+1
 AND EXISTS(SELECT 1 FROM revision_edit_grants gr JOIN revision_request_states st ON st.request_id=gr.request_id
 WHERE gr.cycle_id=c.id AND st.state='editing' AND gr.start_at<=clock_timestamp() AND clock_timestamp()<gr.end_at)
 AND EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 JOIN directorate_packages p ON p.id=NEW.package_id
 WHERE d.package_revision_id=prior.id AND d.snapshot_sha256=prior.sha256 AND civensa_correction_decision_authorized(d.id,p.id) AND d.from_state=p.state AND d.to_state='returned'
 AND d.action IN ('director_return','director_reopen','strategy_return') AND e.actor_user_id=NEW.created_by
 AND e.context_json::jsonb->>'correction_cycle_id'=c.id::text
 AND e.context_json::jsonb->>'expected_version'=p.version::text
 AND e.context_json::jsonb->>'returned_revision'=NEW.revision::text AND length(trim(e.reason))>0) THEN RETURN NEW; END IF;
 SELECT gr.*,r.organization_id,r.department_id,e.id AS event_id,e.reason,e.context_json,m.role_code INTO g
 FROM revision_edit_grants gr JOIN revision_requests r ON r.id=gr.request_id JOIN revision_request_states st ON st.request_id=r.id
 JOIN workflow_events e ON e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.event_type='correction_edit'
 JOIN directorate_memberships m ON m.id=(e.context_json::jsonb->>'membership_id')::integer JOIN users u ON u.id=m.user_id
 WHERE gr.cycle_id=c.id AND e.actor_user_id=NEW.created_by AND (e.context_json::jsonb->>'grant_id')::integer=gr.id
 AND (e.context_json::jsonb->>'next_revision')::integer=NEW.revision AND e.context_json::jsonb->>'next_sha256'=NEW.sha256
 AND st.state='editing' AND gr.start_at<=clock_timestamp() AND clock_timestamp()<gr.end_at
 AND m.user_id=NEW.created_by AND m.active AND u.is_active AND u.role='department' AND m.department_id=r.department_id AND m.organization_id=r.organization_id
 AND gr.membership_ids_json::jsonb @> jsonb_build_array(m.id) ORDER BY e.id DESC LIMIT 1 FOR UPDATE OF m,u;
 IF NOT FOUND OR g.start_at>clock_timestamp() OR clock_timestamp()>=g.end_at OR (g.role_code='department_director' AND length(trim(g.reason))=0) THEN RAISE EXCEPTION 'Missing active scoped correction authorization/audit'; END IF;
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
 FOR path IN SELECT value FROM jsonb_array_elements(g.paths_json::jsonb) LOOP
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


# Used at the projection/copy boundary; authority is current, never inferred from
# contribution history or a client actor snapshot. An invalid delegate fails closed.
AUTHORITY = r"""CREATE FUNCTION civensa_correction_decision_authorized(did integer,pid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM package_decisions d JOIN workflow_events e ON e.id=d.workflow_event_id
 JOIN package_revisions r ON r.id=d.package_revision_id JOIN directorate_packages p ON p.id=r.package_id
 JOIN users u ON u.id=e.actor_user_id
 WHERE d.id=did AND p.id=pid AND r.revision=p.current_revision AND d.from_state=p.state
 AND r.sha256=encode(sha256(convert_to(r.content_json,'UTF8')),'hex') AND d.snapshot_sha256=r.sha256
 AND e.organization_id=p.organization_id AND e.department_id=p.department_id AND u.is_active
 AND e.context_json::jsonb->>'from_state'=d.from_state AND e.context_json::jsonb->>'to_state'=d.to_state
 AND e.context_json::jsonb->>'delegation_id' IS NOT DISTINCT FROM d.delegation_id::text
 AND ((d.action IN ('strategy_approve','strategy_return') AND u.role='strategy' AND d.delegation_id IS NULL)
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
