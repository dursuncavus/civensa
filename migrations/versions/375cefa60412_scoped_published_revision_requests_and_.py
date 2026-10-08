"""Scoped published revision requests and correction grants

Revision ID: 375cefa60412
Revises: 264bdce59301
Create Date: 2026-10-08 22:21:40.808074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '375cefa60412'
down_revision: Union[str, Sequence[str], None] = '264bdce59301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('revision_correction_cycles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_release_id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('source_package_revision_id', sa.Integer(), nullable=False),
    sa.Column('opening_revision_id', sa.Integer(), nullable=False),
    sa.Column('workflow_event_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['opening_revision_id'], ['package_revisions.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['directorate_packages.id'], ),
    sa.ForeignKeyConstraint(['source_package_revision_id'], ['package_revisions.id'], ),
    sa.ForeignKeyConstraint(['source_release_id'], ['report_releases.id'], ),
    sa.ForeignKeyConstraint(['workflow_event_id'], ['workflow_events.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_release_id', 'package_id', name='uq_revision_cycle'),
    sa.UniqueConstraint('workflow_event_id')
    )
    op.create_table('revision_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_release_id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.Column('requester_user_id', sa.Integer(), nullable=False),
    sa.Column('requester_membership_id', sa.Integer(), nullable=False),
    sa.Column('source_package_revision_id', sa.Integer(), nullable=False),
    sa.Column('patches_json', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('evidence_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(reason))>0', name='ck_revision_request_reason'),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['requester_membership_id'], ['directorate_memberships.id'], ),
    sa.ForeignKeyConstraint(['requester_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['source_package_revision_id'], ['package_revisions.id'], ),
    sa.ForeignKeyConstraint(['source_release_id'], ['report_releases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('revision_edit_grants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('source_release_id', sa.Integer(), nullable=False),
    sa.Column('department_id', sa.Integer(), nullable=False),
    sa.Column('cycle_id', sa.Integer(), nullable=False),
    sa.Column('membership_ids_json', sa.Text(), nullable=False),
    sa.Column('paths_json', sa.Text(), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('formal_basis', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(formal_basis))>0', name='ck_revision_grant_basis'),
    sa.CheckConstraint('start_at<end_at', name='ck_revision_grant_time'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['cycle_id'], ['revision_correction_cycles.id'], ),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.ForeignKeyConstraint(['request_id'], ['revision_requests.id'], ),
    sa.ForeignKeyConstraint(['source_release_id'], ['report_releases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('request_id')
    )
    op.create_table('revision_request_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('workflow_event_id', sa.Integer(), nullable=False),
    sa.Column('from_state', sa.String(length=20), nullable=False),
    sa.Column('to_state', sa.String(length=20), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['request_id'], ['revision_requests.id'], ),
    sa.ForeignKeyConstraint(['workflow_event_id'], ['workflow_events.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('request_id', 'version', name='uq_revision_request_event_version'),
    sa.UniqueConstraint('workflow_event_id')
    )
    op.create_table('revision_request_states',
    sa.Column('request_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=20), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.CheckConstraint("state IN ('requested','accepted','rejected','cancelled','editing','stale')", name='ck_revision_request_state'),
    sa.ForeignKeyConstraint(['request_id'], ['revision_requests.id'], ),
    sa.PrimaryKeyConstraint('request_id')
    )
    op.add_column('field_change_events', sa.Column('revision_request_id', sa.Integer(), nullable=True))
    if op.get_bind().dialect.name=='postgresql':
        op.create_foreign_key('fk_field_change_revision_request', 'field_change_events', 'revision_requests', ['revision_request_id'], ['id'])

    guards()


def downgrade():
    raise RuntimeError("Revision correction history cannot be discarded")


def guards():
    tables=('revision_requests','revision_request_events','revision_correction_cycles','revision_edit_grants')
    if op.get_bind().dialect.name=='postgresql':
        for table in tables:
            op.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION civensa_auth_immutable()")
        for statement in SQL.split("--SPLIT--"):
            op.execute(statement)
        for table, fn, operations in (("revision_requests","request","INSERT"),("revision_request_states","state","INSERT OR UPDATE OR DELETE"),("revision_edit_grants","grant","INSERT"),("revision_correction_cycles","cycle","INSERT"),("package_revisions","edit","INSERT"),("directorate_packages","projection","UPDATE")):
            op.execute(f"CREATE TRIGGER revision_guard_{table} BEFORE {operations} ON {table} FOR EACH ROW EXECUTE FUNCTION civensa_revision_{fn}_guard()")
    else:
        for table in tables:
            for action in ("UPDATE","DELETE"):
                op.execute(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Immutable correction history'); END")

SQL = r"""CREATE FUNCTION civensa_revision_projection_guard() RETURNS trigger AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM revision_correction_cycles WHERE package_id=OLD.id) AND
 (NEW.state<>'returned' OR NEW.current_revision<>OLD.current_revision+1) THEN RAISE EXCEPTION 'Correction workspace requires grant edits; reapproval is not enabled'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;
--SPLIT--
CREATE FUNCTION civensa_revision_current(rid integer) RETURNS boolean AS $$
 SELECT EXISTS(SELECT 1 FROM report_releases r JOIN report_candidate_states s ON s.candidate_id=r.candidate_id
 WHERE r.id=rid AND s.state='published' AND NOT EXISTS(SELECT 1 FROM report_releases n
 WHERE n.organization_id=r.organization_id AND n.resource_scope=r.resource_scope AND n.report_key=r.report_key
 AND (n.major,n.minor,n.id)>(r.major,r.minor,r.id)))
$$ LANGUAGE sql VOLATILE;

--SPLIT--
CREATE FUNCTION civensa_revision_editable(doc jsonb, scope text, p jsonb) RETURNS boolean AS $$
DECLARE section text; field text; idx integer; subidx integer; row jsonb; parts text[];
BEGIN
 IF jsonb_typeof(p)<>'array' OR jsonb_array_length(p) NOT IN (3,5) THEN RETURN false; END IF;
 section=p->>0; field=p->>(jsonb_array_length(p)-1);
 IF jsonb_typeof(p->0)<>'string' OR jsonb_typeof(p->1)<>'number' OR (p->>1)!~'^[0-9]+$' THEN RETURN false; END IF;
 idx=(p->>1)::integer; row=doc->section->idx;
 IF row IS NULL OR jsonb_typeof(row)<>'object' THEN RETURN false; END IF;
 IF scope='activity_report' THEN
   RETURN jsonb_array_length(p)=3 AND section='entries' AND field IN ('value','state','evidence','explanation','deviation') AND row ? field;
 END IF;
 IF jsonb_array_length(p)=5 THEN
   IF NOT ((section='indicators' AND p->>2='values') OR (section='activities' AND p->>2='costs'))
     OR jsonb_typeof(p->3)<>'number' OR (p->>3)!~'^[0-9]+$' THEN RETURN false; END IF;
   subidx=(p->>3)::integer; row=row->(p->>2)->subidx;
   RETURN row IS NOT NULL AND row ? field AND (field IN ('raw_text','state') OR (section='indicators' AND field='value') OR (section='activities' AND field='amount'));
 END IF;
 RETURN row ? field AND ((section='cards' AND field IN ('explanation','calculation_method','data_source','footnote','goal','rationale','responsible','service_area','strategic_link'))
 OR (section='indicators' AND field IN ('name','unit','explanation','calculation_method','data_source','code'))
 OR (section='activities' AND field IN ('name','explanation','code'))
 OR (section='department_costs' AND field IN ('amount','raw_text','state')) OR (section='economics' AND field='amount'));
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_request_guard() RETURNS trigger AS $$
DECLARE src record; patch jsonb; seen jsonb='[]';
BEGIN
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 PERFORM 1 FROM report_releases WHERE id=NEW.source_release_id FOR UPDATE;
 SELECT r.organization_id,p.department_id,p.resource_scope,pr.content_json INTO src
 FROM report_releases r JOIN candidate_packages b ON b.candidate_id=r.candidate_id
 JOIN package_revisions pr ON pr.id=b.package_revision_id JOIN directorate_packages p ON p.id=pr.package_id
 WHERE r.id=NEW.source_release_id AND pr.id=NEW.source_package_revision_id;
 IF NOT FOUND OR src.organization_id<>NEW.organization_id OR src.department_id<>NEW.department_id OR NOT civensa_revision_current(NEW.source_release_id)
 OR NOT EXISTS(SELECT 1 FROM directorate_memberships m JOIN users u ON u.id=m.user_id WHERE m.id=NEW.requester_membership_id
 AND m.user_id=NEW.requester_user_id AND m.organization_id=NEW.organization_id AND m.department_id=NEW.department_id
 AND m.active AND u.is_active AND u.role='department' AND m.role_code IN ('department_editor','department_director')) THEN
 RAISE EXCEPTION 'Revision request scope/authority/current release mismatch'; END IF;
 IF jsonb_typeof(NEW.patches_json::jsonb)<>'array' OR jsonb_array_length(NEW.patches_json::jsonb) NOT BETWEEN 1 AND 100 THEN RAISE EXCEPTION 'Invalid revision fields'; END IF;
 FOR patch IN SELECT value FROM jsonb_array_elements(NEW.patches_json::jsonb) LOOP
 IF NOT civensa_revision_editable(src.content_json::jsonb,src.resource_scope,patch->'path') OR seen @> jsonb_build_array(patch->'path') THEN RAISE EXCEPTION 'Invalid or duplicate revision path'; END IF;
 seen=seen||jsonb_build_array(patch->'path');
 END LOOP;
 NEW.created_at=clock_timestamp(); RETURN NEW;
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_state_guard() RETURNS trigger AS $$
DECLARE r revision_requests%ROWTYPE; ev record;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Request history cannot be deleted'; END IF;
 IF TG_OP='INSERT' THEN
 IF NEW.state<>'requested' OR NEW.version<>0 THEN RAISE EXCEPTION 'Invalid initial request state'; END IF; RETURN NEW; END IF;
 SELECT * INTO r FROM revision_requests WHERE id=OLD.request_id;
 PERFORM 1 FROM organizations WHERE id=r.organization_id FOR UPDATE;
 PERFORM 1 FROM report_releases WHERE id=r.source_release_id FOR UPDATE;
 IF NEW.request_id<>OLD.request_id OR NEW.version<>OLD.version+1 OR NOT
 ((OLD.state='requested' AND NEW.state IN ('accepted','rejected','cancelled')) OR (OLD.state='accepted' AND NEW.state='editing')) THEN RAISE EXCEPTION 'Illegal revision state transition'; END IF;
 SELECT e.*,u.role,u.is_active INTO ev FROM revision_request_events re JOIN workflow_events e ON e.id=re.workflow_event_id JOIN users u ON u.id=e.actor_user_id
 WHERE re.request_id=r.id AND re.version=NEW.version AND re.from_state=OLD.state AND re.to_state=NEW.state
 AND e.resource_type='revision_request' AND e.resource_id=r.id::text AND e.organization_id=r.organization_id AND e.department_id=r.department_id
 AND (e.context_json::jsonb->>'version')::integer=NEW.version AND e.context_json::jsonb->>'from_state'=OLD.state AND e.context_json::jsonb->>'to_state'=NEW.state;
 IF NOT FOUND OR NOT ev.is_active OR ev.event_type<>'revision_'||NEW.state OR
 (NEW.state='cancelled' AND (ev.actor_user_id<>r.requester_user_id OR length(trim(ev.reason))=0)) OR
 (NEW.state IN ('accepted','rejected','editing') AND ev.role<>'strategy') OR (NEW.state='rejected' AND length(trim(ev.reason))=0) THEN RAISE EXCEPTION 'Missing authorized revision audit'; END IF;
 IF NEW.state IN ('accepted','editing') AND NOT civensa_revision_current(r.source_release_id) THEN RAISE EXCEPTION 'Stale source release'; END IF;
 IF NEW.state='accepted' AND EXISTS(SELECT 1 FROM revision_requests other JOIN revision_request_states s ON s.request_id=other.id,
 jsonb_array_elements(other.patches_json::jsonb) a,jsonb_array_elements(r.patches_json::jsonb) b
 WHERE other.id<>r.id AND other.source_release_id=r.source_release_id AND other.department_id=r.department_id
 AND s.state IN ('accepted','editing') AND a->'path'=b->'path') THEN RAISE EXCEPTION 'Overlapping accepted revision cells'; END IF;
 IF NEW.state='editing' AND NOT EXISTS(SELECT 1 FROM revision_edit_grants g WHERE g.request_id=r.id) THEN RAISE EXCEPTION 'Missing scoped grant'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_grant_guard() RETURNS trigger AS $$
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
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_cycle_guard() RETURNS trigger AS $$
BEGIN
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_releases WHERE id=NEW.source_release_id) FOR UPDATE;
 IF NOT civensa_revision_current(NEW.source_release_id) THEN RAISE EXCEPTION 'Stale correction source'; END IF;
 IF NOT EXISTS(SELECT 1 FROM report_releases r JOIN candidate_packages b ON b.candidate_id=r.candidate_id
 JOIN package_revisions src ON src.id=b.package_revision_id JOIN package_revisions dst ON dst.id=NEW.opening_revision_id
 JOIN workflow_events e ON e.id=NEW.workflow_event_id JOIN users u ON u.id=e.actor_user_id
 JOIN revision_requests req ON req.id=(e.context_json::jsonb->>'request_id')::integer
 JOIN revision_request_states rst ON rst.request_id=req.id
 WHERE r.id=NEW.source_release_id AND src.id=NEW.source_package_revision_id AND src.package_id=NEW.package_id
 AND dst.package_id=src.package_id AND dst.previous_revision_id=src.id AND dst.revision=src.revision+1 AND dst.content_json=src.content_json AND dst.sha256=src.sha256
 AND req.source_release_id=r.id AND req.source_package_revision_id=src.id AND rst.state='accepted'
 AND e.organization_id=req.organization_id AND e.department_id=req.department_id
 AND e.event_type='correction_opened' AND u.is_active AND u.role='strategy'
 AND (e.context_json::jsonb->>'source_release_id')::integer=r.id) THEN RAISE EXCEPTION 'Invalid correction source/provenance'; END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_changes(a jsonb,b jsonb,p jsonb DEFAULT '[]') RETURNS SETOF jsonb AS $$
DECLARE k text; i integer;
BEGIN
 IF a IS NOT DISTINCT FROM b THEN RETURN; END IF;
 IF jsonb_typeof(a)='object' AND jsonb_typeof(b)='object' THEN
 FOR k IN SELECT jsonb_object_keys(a||b) LOOP RETURN QUERY SELECT * FROM civensa_revision_changes(a->k,b->k,p||jsonb_build_array(k)); END LOOP;
 ELSIF jsonb_typeof(a)='array' AND jsonb_typeof(b)='array' AND jsonb_array_length(a)=jsonb_array_length(b) THEN
 FOR i IN 0..jsonb_array_length(a)-1 LOOP RETURN QUERY SELECT * FROM civensa_revision_changes(a->i,b->i,p||jsonb_build_array(i)); END LOOP;
 ELSE RETURN NEXT p; END IF;
END; $$ LANGUAGE plpgsql;

--SPLIT--
CREATE FUNCTION civensa_revision_edit_guard() RETURNS trigger AS $$
DECLARE c record; g record; prior package_revisions%ROWTYPE; change jsonb; path jsonb; authorized boolean; entry jsonb; target numeric; actual numeric; expected jsonb;
BEGIN
 SELECT cy.* INTO c FROM revision_correction_cycles cy JOIN report_releases r ON r.id=cy.source_release_id
 WHERE cy.package_id=NEW.package_id ORDER BY cy.id DESC LIMIT 1;
 IF NOT FOUND THEN RETURN NEW; END IF;
 PERFORM 1 FROM organizations WHERE id=(SELECT organization_id FROM report_releases WHERE id=c.source_release_id) FOR UPDATE;
 IF NOT civensa_revision_current(c.source_release_id) THEN RAISE EXCEPTION 'Stale correction cycle'; END IF;
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
END; $$ LANGUAGE plpgsql;
"""
