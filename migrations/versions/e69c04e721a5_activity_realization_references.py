"""S4 immutable Activity unchanged-value references; reference-aware successor guard.

Adds activity_realization_references: one append-only row per successor
ReportIndicator whose content is unchanged against the IMMEDIATE predecessor
release. Such an indicator has no ActualRevision (XOR); its effective realization
is the terminal materialized source ActualRevision named by the reference.
The successor guard is the 8ca1def15967 body widened to accept exactly
(activity-candidate-1, materialized-successor-1) or
(activity-candidate-2, reference-successor-1); the v1 path is unchanged.
SQLite keeps history immutable and refuses references, like successors.
"""
from alembic import op
import sqlalchemy as sa
revision='e69c04e721a5'
down_revision='3942a5669b80'
branch_labels=depends_on=None


def upgrade():
    op.create_table('activity_realization_references',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('organization_id',sa.Integer(),sa.ForeignKey('organizations.id'),nullable=False),
        sa.Column('activity_report_id',sa.Integer(),sa.ForeignKey('activity_reports.id'),nullable=False),
        sa.Column('reporting_period_id',sa.Integer(),sa.ForeignKey('reporting_periods.id'),nullable=False),
        sa.Column('successor_report_revision_id',sa.Integer(),sa.ForeignKey('activity_report_revisions.id'),nullable=False),
        sa.Column('successor_report_indicator_id',sa.Integer(),sa.ForeignKey('report_indicators.id'),nullable=False,unique=True),
        sa.Column('predecessor_release_id',sa.Integer(),sa.ForeignKey('report_releases.id'),nullable=False),
        sa.Column('predecessor_candidate_id',sa.Integer(),sa.ForeignKey('report_candidates.id'),nullable=False),
        sa.Column('predecessor_report_indicator_id',sa.Integer(),sa.ForeignKey('report_indicators.id'),nullable=False),
        sa.Column('predecessor_reference_id',sa.Integer(),sa.ForeignKey('activity_realization_references.id'),nullable=True),
        sa.Column('source_release_id',sa.Integer(),sa.ForeignKey('report_releases.id'),nullable=False),
        sa.Column('source_report_indicator_id',sa.Integer(),sa.ForeignKey('report_indicators.id'),nullable=False),
        sa.Column('source_actual_revision_id',sa.Integer(),sa.ForeignKey('actual_revisions.id'),nullable=False),
        sa.Column('persistent_indicator_id',sa.String(36),sa.ForeignKey('indicator_identities.indicator_id'),nullable=False),
        sa.Column('definition_revision_id',sa.Integer(),sa.ForeignKey('indicator_definition_revisions.id'),nullable=False),
        sa.Column('content_sha256',sa.String(64),nullable=False),
        sa.Column('provenance_json',sa.Text(),nullable=False),
        sa.Column('reference_sha256',sa.String(64),nullable=False,unique=True),
        sa.Column('created_by',sa.Integer(),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.current_timestamp(),nullable=False),
        sa.CheckConstraint('length(content_sha256)=64 AND length(reference_sha256)=64',name='ck_activity_reference_hashes'),
        sa.CheckConstraint('successor_report_indicator_id<>source_report_indicator_id AND successor_report_indicator_id<>predecessor_report_indicator_id',name='ck_activity_reference_successor'),
        sa.CheckConstraint('(predecessor_reference_id IS NULL AND source_release_id=predecessor_release_id AND source_report_indicator_id=predecessor_report_indicator_id) OR (predecessor_reference_id IS NOT NULL AND source_release_id<>predecessor_release_id AND source_report_indicator_id<>predecessor_report_indicator_id)',name='ck_activity_reference_chain'))
    op.create_index('ix_activity_reference_successor_revision','activity_realization_references',['successor_report_revision_id'])
    if op.get_bind().dialect.name=='postgresql':
        op.execute('CREATE TRIGGER immutable_activity_realization_references BEFORE UPDATE OR DELETE ON activity_realization_references FOR EACH ROW EXECUTE FUNCTION civensa_auth_immutable()')
        op.execute('CREATE TRIGGER timestamp_activity_realization_references BEFORE INSERT ON activity_realization_references FOR EACH ROW EXECUTE FUNCTION civensa_auth_server_timestamp()')
        op.execute(REFERENCE)
        op.execute('CREATE TRIGGER activity_reference_guard BEFORE INSERT ON activity_realization_references FOR EACH ROW EXECUTE FUNCTION civensa_activity_reference_guard()')
        op.execute(XOR)
        op.execute('CREATE TRIGGER activity_reference_actual_xor BEFORE INSERT ON actual_revisions FOR EACH ROW EXECUTE FUNCTION civensa_activity_reference_actual_xor()')
        op.execute(ASSEMBLY)
    else:
        # New triggers only; no batch_alter_table, so no existing SQLite trigger is dropped.
        for action in ('UPDATE','DELETE'):
            op.execute(f"CREATE TRIGGER immutable_activity_realization_references_{action.lower()} BEFORE {action} ON activity_realization_references BEGIN SELECT RAISE(ABORT,'Immutable activity reference history'); END")
        op.execute("CREATE TRIGGER activity_reference_guard BEFORE INSERT ON activity_realization_references BEGIN SELECT RAISE(ABORT,'Activity references require PostgreSQL'); END")
        op.execute("""CREATE TRIGGER activity_reference_actual_xor BEFORE INSERT ON actual_revisions WHEN EXISTS
            (SELECT 1 FROM activity_realization_references WHERE successor_report_indicator_id=NEW.report_indicator_id)
            BEGIN SELECT RAISE(ABORT,'Report indicator is realized by a reference'); END""")


def downgrade():
    raise RuntimeError('Activity reference history cannot be discarded')


REFERENCE=r"""CREATE FUNCTION civensa_activity_reference_guard() RETURNS trigger AS $$
DECLARE pj jsonb; ri report_indicators%ROWTYPE; dst activity_report_revisions%ROWTYPE; rep activity_reports%ROWTYPE;
 p report_releases%ROWTYPE; pc report_candidates%ROWTYPE; prev activity_report_revisions%ROWTYPE; pri report_indicators%ROWTYPE;
 pe jsonb; pschema text; prior activity_realization_references%ROWTYPE;
 s report_releases%ROWTYPE; sc report_candidates%ROWTYPE; srev activity_report_revisions%ROWTYPE; sri report_indicators%ROWTYPE;
 a actual_revisions%ROWTYPE; d indicator_definition_revisions%ROWTYPE; n integer;
BEGIN
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 SELECT * INTO ri FROM report_indicators WHERE id=NEW.successor_report_indicator_id FOR UPDATE;
 SELECT * INTO dst FROM activity_report_revisions WHERE id=ri.report_revision_id;
 SELECT * INTO rep FROM activity_reports WHERE id=dst.report_id;
 IF ri.id IS NULL OR dst.id IS NULL OR rep.id IS NULL OR dst.id IS DISTINCT FROM NEW.successor_report_revision_id
 OR rep.id IS DISTINCT FROM NEW.activity_report_id OR rep.organization_id IS DISTINCT FROM NEW.organization_id
 OR rep.period_id IS DISTINCT FROM NEW.reporting_period_id OR rep.current_revision IS DISTINCT FROM dst.revision
 THEN RAISE EXCEPTION 'Activity reference successor scope mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM report_candidates WHERE activity_revision_id=dst.id) THEN RAISE EXCEPTION 'Candidate materialization is sealed'; END IF;
 IF EXISTS(SELECT 1 FROM actual_revisions WHERE report_indicator_id=ri.id) THEN RAISE EXCEPTION 'Report indicator is already materialized'; END IF;
 -- Immediate predecessor: the current published release of this report, never a returned attempt.
 SELECT * INTO p FROM report_releases WHERE id=NEW.predecessor_release_id;
 SELECT * INTO pc FROM report_candidates WHERE id=p.candidate_id;
 SELECT * INTO prev FROM activity_report_revisions WHERE id=pc.activity_revision_id;
 SELECT * INTO pri FROM report_indicators WHERE id=NEW.predecessor_report_indicator_id;
 IF p.id IS NULL OR pc.id IS NULL OR prev.id IS NULL OR pri.id IS NULL OR NOT civensa_revision_current(p.id)
 OR (p.organization_id,p.resource_scope,p.report_key) IS DISTINCT FROM (NEW.organization_id,'activity_report',rep.id::text)
 OR pc.id IS DISTINCT FROM NEW.predecessor_candidate_id OR pc.period_id IS DISTINCT FROM NEW.reporting_period_id
 OR NOT EXISTS(SELECT 1 FROM activity_report_approvals WHERE id=p.activity_approval_id AND report_revision_id=prev.id)
 OR prev.report_id IS DISTINCT FROM rep.id OR prev.revision>=dst.revision
 OR (prev.publication_id,prev.publication_sha256,prev.contract_version) IS DISTINCT FROM (dst.publication_id,dst.publication_sha256,dst.contract_version)
 OR pri.report_revision_id IS DISTINCT FROM prev.id OR pri.publication_binding_id IS DISTINCT FROM ri.publication_binding_id
 THEN RAISE EXCEPTION 'Activity reference requires the current immediate predecessor release'; END IF;
 pschema=pc.payload_json::jsonb->>'schema_version';
 SELECT count(*) INTO n FROM jsonb_array_elements(pc.payload_json::jsonb->'entries') x
 WHERE x.value->>CASE WHEN pschema='activity-candidate-1' THEN 'materialized_report_indicator_id' ELSE 'successor_report_indicator_id' END=pri.id::text;
 SELECT x.value INTO pe FROM jsonb_array_elements(pc.payload_json::jsonb->'entries') x
 WHERE x.value->>CASE WHEN pschema='activity-candidate-1' THEN 'materialized_report_indicator_id' ELSE 'successor_report_indicator_id' END=pri.id::text;
 IF n IS DISTINCT FROM 1 THEN RAISE EXCEPTION 'Predecessor release does not hold the indicator exactly once'; END IF;
 IF pschema='activity-candidate-1' OR (pschema='activity-candidate-2' AND pe#>>'{realization,mode}' IS NOT DISTINCT FROM 'materialized') THEN
 -- A materialized predecessor entry is its own source.
 IF NEW.predecessor_reference_id IS NOT NULL OR NEW.source_release_id IS DISTINCT FROM p.id
 OR NEW.source_report_indicator_id IS DISTINCT FROM pri.id
 OR NEW.source_actual_revision_id::text IS DISTINCT FROM COALESCE(pe->>'materialized_actual_revision_id',pe#>>'{realization,actual_revision_id}')
 OR (pschema='activity-candidate-2' AND pe#>>'{realization,content_sha256}' IS DISTINCT FROM NEW.content_sha256)
 THEN RAISE EXCEPTION 'Activity reference source must be the materialized predecessor'; END IF;
 ELSIF pschema='activity-candidate-2' AND pe#>>'{realization,mode}' IS NOT DISTINCT FROM 'reference' THEN
 -- A referencing predecessor entry is flattened to its own terminal materialized source.
 SELECT * INTO prior FROM activity_realization_references WHERE id=NEW.predecessor_reference_id;
 IF prior.id IS NULL OR prior.successor_report_indicator_id IS DISTINCT FROM pri.id
 OR prior.reference_sha256 IS DISTINCT FROM pe#>>'{realization,reference_sha256}'
 OR pe#>>'{realization,content_sha256}' IS DISTINCT FROM NEW.content_sha256
 OR (prior.source_release_id,prior.source_report_indicator_id,prior.source_actual_revision_id,prior.content_sha256,prior.persistent_indicator_id,prior.definition_revision_id)
 IS DISTINCT FROM (NEW.source_release_id,NEW.source_report_indicator_id,NEW.source_actual_revision_id,NEW.content_sha256,NEW.persistent_indicator_id,NEW.definition_revision_id)
 THEN RAISE EXCEPTION 'Activity reference chain must flatten to the predecessor reference source'; END IF;
 ELSE RAISE EXCEPTION 'Unsupported predecessor realization'; END IF;
 -- Terminal source: a materialized indicator of an older-or-same published release of this report.
 SELECT * INTO s FROM report_releases WHERE id=NEW.source_release_id;
 SELECT * INTO sc FROM report_candidates WHERE id=s.candidate_id;
 SELECT * INTO srev FROM activity_report_revisions WHERE id=sc.activity_revision_id;
 SELECT * INTO sri FROM report_indicators WHERE id=NEW.source_report_indicator_id;
 SELECT * INTO a FROM actual_revisions WHERE id=NEW.source_actual_revision_id;
 SELECT count(*) INTO n FROM jsonb_array_elements(sc.payload_json::jsonb->'entries') x
 WHERE (sc.payload_json::jsonb->>'schema_version'='activity-candidate-1' AND x.value->>'materialized_report_indicator_id'=sri.id::text
 AND x.value->>'materialized_actual_revision_id'=a.id::text)
 OR (sc.payload_json::jsonb->>'schema_version'='activity-candidate-2' AND x.value->>'successor_report_indicator_id'=sri.id::text
 AND x.value#>>'{realization,mode}'='materialized' AND x.value#>>'{realization,actual_revision_id}'=a.id::text);
 IF s.id IS NULL OR sc.id IS NULL OR srev.id IS NULL OR sri.id IS NULL OR a.id IS NULL
 OR (s.organization_id,s.resource_scope,s.report_key,s.major) IS DISTINCT FROM (p.organization_id,p.resource_scope,p.report_key,p.major)
 OR s.minor>p.minor OR NOT EXISTS(SELECT 1 FROM report_candidate_states WHERE candidate_id=sc.id AND state='published')
 OR NOT EXISTS(SELECT 1 FROM activity_report_approvals WHERE id=s.activity_approval_id AND report_revision_id=srev.id)
 OR srev.report_id IS DISTINCT FROM rep.id OR srev.revision>prev.revision
 OR (srev.publication_id,srev.publication_sha256,srev.contract_version) IS DISTINCT FROM (dst.publication_id,dst.publication_sha256,dst.contract_version)
 OR sri.report_revision_id IS DISTINCT FROM srev.id OR sri.publication_binding_id IS DISTINCT FROM ri.publication_binding_id
 OR a.report_indicator_id IS DISTINCT FROM sri.id OR n IS DISTINCT FROM 1
 OR (SELECT count(*) FROM actual_revisions WHERE report_indicator_id=sri.id)<>1
 THEN RAISE EXCEPTION 'Activity reference source is not a materialized published release indicator'; END IF;
 SELECT d2.* INTO d FROM publication_indicator_bindings b JOIN indicator_definition_revisions d2 ON d2.id=b.definition_revision_id
 WHERE b.id=ri.publication_binding_id;
 IF d.id IS NULL OR d.id IS DISTINCT FROM NEW.definition_revision_id OR d.indicator_id IS DISTINCT FROM NEW.persistent_indicator_id
 OR NOT EXISTS(SELECT 1 FROM indicator_identities WHERE indicator_id=d.indicator_id AND organization_id=NEW.organization_id)
 THEN RAISE EXCEPTION 'Activity reference definition binding mismatch'; END IF;
 -- Provenance JSON is the engine's canonical text; every indexed column must equal it.
 pj=NEW.provenance_json::jsonb;
 IF NEW.reference_sha256 IS DISTINCT FROM encode(sha256(convert_to(NEW.provenance_json,'UTF8')),'hex')
 OR pj->>'schema' IS DISTINCT FROM 'civensa.activity-unchanged-value-reference/v2'
 OR pj->>'calculation_rule_version' IS DISTINCT FROM 'difference-v1'
 OR pj->>'content_sha256' IS DISTINCT FROM NEW.content_sha256
 OR pj->'successor' IS DISTINCT FROM jsonb_build_object('organization_id',rep.organization_id,'activity_report_id',rep.id,
 'reporting_period_id',rep.period_id,'report_revision_id',dst.id,'report_revision_number',dst.revision,'report_indicator_id',ri.id)
 OR pj->'predecessor' IS DISTINCT FROM jsonb_build_object('release_id',p.id,'release_major',p.major,'release_minor',p.minor,
 'candidate_id',pc.id,'candidate_sha256',pc.sha256,'activity_approval_id',p.activity_approval_id,'report_revision_id',prev.id,
 'report_revision_number',prev.revision,'report_indicator_id',pri.id,
 'entry_mode',CASE WHEN prior.id IS NULL THEN 'materialized' ELSE 'reference' END,
 'materialized_actual_revision_id',CASE WHEN prior.id IS NULL THEN a.id END,
 'predecessor_reference_sha256',prior.reference_sha256,'content_sha256',NEW.content_sha256)
 OR pj->'source' IS DISTINCT FROM jsonb_build_object('release_id',s.id,'release_major',s.major,'release_minor',s.minor,
 'candidate_id',sc.id,'candidate_sha256',sc.sha256,'activity_approval_id',s.activity_approval_id,'report_revision_id',srev.id,
 'report_revision_number',srev.revision,'report_indicator_id',sri.id,'actual_revision_id',a.id)
 OR pj#>>'{binding,organization_id}' IS DISTINCT FROM rep.organization_id::text
 OR pj#>>'{binding,activity_report_id}' IS DISTINCT FROM rep.id::text
 OR pj#>>'{binding,reporting_period_id}' IS DISTINCT FROM rep.period_id::text
 OR pj#>>'{binding,persistent_indicator_id}' IS DISTINCT FROM NEW.persistent_indicator_id
 OR pj#>>'{binding,definition_revision_id}' IS DISTINCT FROM d.id::text
 OR pj#>>'{binding,definition_sha256}' IS DISTINCT FROM d.sha256
 OR pj#>>'{binding,publication_id}' IS DISTINCT FROM dst.publication_id::text
 OR pj#>>'{binding,publication_sha256}' IS DISTINCT FROM dst.publication_sha256
 OR pj#>>'{binding,contract_version}' IS DISTINCT FROM dst.contract_version
 THEN RAISE EXCEPTION 'Activity reference provenance mismatch'; END IF;
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=NEW.created_by AND is_active AND role='strategy')
 THEN RAISE EXCEPTION 'Activity reference requires an active Strategy actor'; END IF;
 NEW.created_at=clock_timestamp(); RETURN NEW;
END; $$ LANGUAGE plpgsql;"""

XOR=r"""CREATE FUNCTION civensa_activity_reference_actual_xor() RETURNS trigger AS $$ BEGIN
 -- FOR SHARE waits for an uncommitted reference (the guard holds FOR UPDATE on the indicator).
 PERFORM 1 FROM report_indicators WHERE id=NEW.report_indicator_id FOR SHARE;
 IF EXISTS(SELECT 1 FROM activity_realization_references WHERE successor_report_indicator_id=NEW.report_indicator_id)
 THEN RAISE EXCEPTION 'Report indicator is realized by a reference'; END IF;
 RETURN NEW; END; $$ LANGUAGE plpgsql;"""

# 8ca1def15967 ASSEMBLY with only: the S4 organization lock + reference ownership checks, the schema/contract
# pair (v1 pair unchanged) and the activity-candidate-2 entry checks.
ASSEMBLY=r"""CREATE OR REPLACE FUNCTION civensa_activity_successor_guard() RETURNS trigger AS $$
DECLARE m jsonb; p report_releases%ROWTYPE; pc report_candidates%ROWTYPE; source activity_report_revisions%ROWTYPE; dst activity_report_revisions%ROWTYPE; attempt report_candidates%ROWTYPE; b jsonb; old jsonb; cy revision_correction_cycles%ROWTYPE; pkg directorate_packages%ROWTYPE;
 vpayload jsonb; ventry jsonb; vref activity_realization_references%ROWTYPE; vsrc actual_revisions%ROWTYPE;
BEGIN
 m=NEW.manifest_json::jsonb;
 -- S4: references belong only to an activity-candidate-2 successor of their own report revision.
 IF NEW.resource_scope='activity_report' THEN
 -- Same organization lock as the reference guard, so the ownership check sees committed references.
 PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
 vpayload=NEW.payload_json::jsonb;
 IF vpayload->>'schema_version' IS DISTINCT FROM 'activity-candidate-2'
 AND EXISTS(SELECT 1 FROM activity_realization_references WHERE successor_report_revision_id=NEW.activity_revision_id)
 THEN RAISE EXCEPTION 'Only a reference successor may own activity references'; END IF;
 IF NOT (m ? 'predecessor_release_id') AND vpayload->>'schema_version' IS NOT DISTINCT FROM 'activity-candidate-2'
 THEN RAISE EXCEPTION 'Reference successor requires explicit lineage'; END IF;
 END IF;
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
 OR m->>'predecessor_candidate_sha256' IS DISTINCT FROM pc.sha256
 OR m->'source_id' IS DISTINCT FROM pc.manifest_json::jsonb->'source_id'
 OR m->'required_department_ids' IS DISTINCT FROM pc.manifest_json::jsonb->'required_department_ids'
 OR dst.previous_revision_id IS DISTINCT FROM source.id OR dst.report_id IS DISTINCT FROM source.report_id OR dst.revision<>source.revision+1
 OR dst.publication_id IS DISTINCT FROM source.publication_id OR dst.publication_sha256 IS DISTINCT FROM source.publication_sha256
 OR (COALESCE(NEW.payload_json::jsonb->>'schema_version',''),COALESCE(m->>'successor_contract',''))
 NOT IN (('activity-candidate-1','materialized-successor-1'),('activity-candidate-2','reference-successor-1'))
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
 IF vpayload->>'schema_version'='activity-candidate-2' THEN
 IF vpayload ?| ARRAY['predecessor_release_id','predecessor_candidate_id','predecessor_candidate_sha256']
 OR vpayload->>'report_revision_id' IS DISTINCT FROM dst.id::text OR jsonb_typeof(vpayload->'entries') IS DISTINCT FROM 'array'
 OR jsonb_array_length(vpayload->'entries')<>(SELECT count(*) FROM report_indicators WHERE report_revision_id=dst.id)
 OR jsonb_array_length(vpayload->'entries')<>(SELECT count(DISTINCT value->>'successor_report_indicator_id') FROM jsonb_array_elements(vpayload->'entries'))
 OR EXISTS(SELECT 1 FROM jsonb_array_elements(vpayload->'entries') x WHERE NOT EXISTS(SELECT 1 FROM report_indicators i
 WHERE i.report_revision_id=dst.id AND i.id::text=x.value->>'successor_report_indicator_id'))
 THEN RAISE EXCEPTION 'Reference successor payload does not cover its report revision'; END IF;
 FOR ventry IN SELECT value FROM jsonb_array_elements(vpayload->'entries') LOOP
 IF ventry#>>'{realization,mode}' IS NOT DISTINCT FROM 'materialized' THEN
 IF (SELECT count(*) FROM actual_revisions WHERE report_indicator_id=(ventry->>'successor_report_indicator_id')::integer)<>1
 OR NOT EXISTS(SELECT 1 FROM actual_revisions WHERE id=(ventry#>>'{realization,actual_revision_id}')::integer
 AND report_indicator_id=(ventry->>'successor_report_indicator_id')::integer)
 OR EXISTS(SELECT 1 FROM activity_realization_references WHERE successor_report_indicator_id=(ventry->>'successor_report_indicator_id')::integer)
 THEN RAISE EXCEPTION 'Materialized successor entry mismatch'; END IF;
 ELSIF ventry#>>'{realization,mode}' IS NOT DISTINCT FROM 'reference' THEN
 SELECT * INTO vref FROM activity_realization_references WHERE successor_report_indicator_id=(ventry->>'successor_report_indicator_id')::integer;
 SELECT * INTO vsrc FROM actual_revisions WHERE id=vref.source_actual_revision_id;
 IF vref.id IS NULL OR vsrc.id IS NULL OR vref.successor_report_revision_id IS DISTINCT FROM dst.id
 OR vref.predecessor_release_id IS DISTINCT FROM p.id OR vref.predecessor_candidate_id IS DISTINCT FROM pc.id
 OR vref.reference_sha256 IS DISTINCT FROM ventry#>>'{realization,reference_sha256}'
 OR vref.source_release_id::text IS DISTINCT FROM ventry#>>'{realization,source_release_id}'
 OR vref.source_actual_revision_id::text IS DISTINCT FROM ventry#>>'{realization,source_actual_revision_id}'
 OR vref.content_sha256 IS DISTINCT FROM ventry#>>'{realization,content_sha256}'
 OR vref.definition_revision_id::text IS DISTINCT FROM ventry->>'definition_revision_id'
 OR EXISTS(SELECT 1 FROM actual_revisions WHERE report_indicator_id=vref.successor_report_indicator_id)
 OR NULLIF(ventry->>'value','')::numeric IS DISTINCT FROM vsrc.value OR ventry->>'state' IS DISTINCT FROM vsrc.state
 OR ventry->'evidence' IS DISTINCT FROM vsrc.evidence_json::jsonb OR ventry->>'explanation' IS DISTINCT FROM vsrc.explanation
 OR (ventry->'deviation')-'delta' IS DISTINCT FROM vsrc.deviation_json::jsonb-'delta'
 OR NULLIF(ventry#>>'{deviation,delta}','')::numeric IS DISTINCT FROM NULLIF(vsrc.deviation_json::jsonb->>'delta','')::numeric
 THEN RAISE EXCEPTION 'Reference successor entry is not unchanged source content'; END IF;
 ELSE RAISE EXCEPTION 'Unknown successor realization'; END IF;
 END LOOP;
 END IF;
 RETURN NEW;
END; $$ LANGUAGE plpgsql;"""
