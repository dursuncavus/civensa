"""S3C-2 repairs: restore SQLite package_decisions guards; closed_no_change blocks only surviving edits.

8ca1def15967 rebuilt package_decisions through batch_alter_table. On SQLite that
copy-and-move drops the table's M153 triggers, so they are recreated verbatim
here. A follow-up revision (not an in-place edit of 8ca1) also repairs SQLite and
PostgreSQL databases that already ran 8ca1.
"""
from alembic import op
revision='3942a5669b80'
down_revision='8ca1def15967'
branch_labels=depends_on=None


def upgrade():
    if op.get_bind().dialect.name=='postgresql':
        op.execute(SURVIVES)
        op.execute(PUBLICATION)
    else:
        # Verbatim from 153acbd48290; DROP first so only the exact definitions remain.
        for action in ('UPDATE','DELETE'):
            op.execute(f'DROP TRIGGER IF EXISTS immutable_package_decisions_{action.lower()}')
            op.execute(f"CREATE TRIGGER immutable_package_decisions_{action.lower()} BEFORE {action} ON package_decisions BEGIN SELECT RAISE(ABORT,'Immutable package history'); END")
        op.execute('DROP TRIGGER IF EXISTS package_decision_binding')
        op.execute("""CREATE TRIGGER package_decision_binding BEFORE INSERT ON package_decisions WHEN NOT EXISTS
            (SELECT 1 FROM package_revisions r JOIN workflow_events e ON e.id=NEW.workflow_event_id
             WHERE r.id=NEW.package_revision_id AND r.sha256=NEW.snapshot_sha256 AND e.resource_type='directorate_package'
             AND e.resource_id=CAST(r.package_id AS TEXT) AND e.event_type=NEW.action)
            BEGIN SELECT RAISE(ABORT,'Decision snapshot/event binding mismatch'); END""")


def downgrade():
    raise RuntimeError('Package decision guards and closed_no_change survival cannot be discarded')


# Closed-request-only survival. Same provenance as civensa_successor_request_participates,
# plus, for a scalar edit: it is the last lineage change at its address and equals the
# bound value. Container-level edits keep the conservative touch rule. Applied
# provenance keeps using civensa_successor_request_participates unchanged.
SURVIVES=r"""CREATE FUNCTION civensa_closed_request_survives(cid integer,rid integer) RETURNS boolean AS $$
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
 AND l.id<>p.opening_revision_id AND (SELECT jsonb_agg(value ORDER BY ord) FROM jsonb_array_elements(f.field_key::jsonb) WITH ORDINALITY a(value,ord) WHERE ord<=jsonb_array_length(path))=path AND NOT f.field_key::jsonb @> '["deviation"]'::jsonb
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (p.source_content #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE (p.source_content #> address.keys) IS DISTINCT FROM (p.bound_content #> address.keys) END
 AND f.previous_json::jsonb IS DISTINCT FROM f.new_json::jsonb
 AND f.previous_json::jsonb=coalesce(prior.content_json::jsonb #> address.keys,'null'::jsonb) AND f.new_json::jsonb=coalesce(l.content_json::jsonb #> address.keys,'null'::jsonb)
 AND (jsonb_typeof(f.previous_json::jsonb) IN ('object','array') OR jsonb_typeof(f.new_json::jsonb) IN ('object','array')
 OR (NOT CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (l.content_json::jsonb #>> address.keys)::numeric IS DISTINCT FROM (p.bound_content #>> address.keys)::numeric ELSE (l.content_json::jsonb #> address.keys) IS DISTINCT FROM (p.bound_content #> address.keys) END
 AND NOT EXISTS(SELECT 1 FROM lineage later WHERE later.package_id=l.package_id AND later.revision>l.revision
 AND CASE WHEN jsonb_array_length(f.field_key::jsonb)=3 AND f.field_key::jsonb->>0='entries' AND f.field_key::jsonb->>2='value' THEN (l.content_json::jsonb #>> address.keys)::numeric IS DISTINCT FROM (later.content_json::jsonb #>> address.keys)::numeric ELSE (l.content_json::jsonb #> address.keys) IS DISTINCT FROM (later.content_json::jsonb #> address.keys) END))));
 $$ LANGUAGE sql;"""

# 8ca1's guard with only the closed_no_change clause switched to survival.
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
 WHERE r.source_release_id=p.id AND st.state='closed_no_change' AND civensa_closed_request_survives(sc.id,r.id))
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
