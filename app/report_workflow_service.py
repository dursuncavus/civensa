"""Disabled Phase 4 internal backend; callers own commit, no runtime routes."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
import json
from uuid import uuid4
from sqlalchemy import select, update, func
from .models import *
from . import authorization_service as auth, package_service as packages, activity_contract_service as contract
from . import activity_reference_service as references
from .program_service import record

# S4: reference-aware successors stay OFF until readers resolve references (separate slice).
ACTIVITY_REFERENCE_SUCCESSORS=False


def canonical(value):return contract.canonical(value)
def hash_content(payload,manifest):return contract.digest(canonical({'manifest':json.loads(manifest),'payload':json.loads(payload)}))

def organization_lock(db,organization_id):
    row=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    if not row:auth.fail('Kurum bulunamadı.',404)
    return row

def assignment(db,org):
    return db.scalar(select(FinalAuthorityAssignment).join(User,User.id==FinalAuthorityAssignment.user_id)
        .where(FinalAuthorityAssignment.organization_id==org,FinalAuthorityAssignment.active.is_(True),User.is_active.is_(True)))

def allowed(db,actor,action,org,state):
    if not auth.report_workflow_eligibility(db,actor,action,org,state):auth.fail('Bu rapor aşaması için güncel yetkiniz yok.')

def event_notice(db,actor,candidate,action,state,to_state,version,reason=''):
    event=WorkflowEvent(actor_user_id=actor.id,actor_snapshot_json=auth.actor_snapshot(db,actor,candidate.organization_id),
        organization_id=candidate.organization_id,department_id=None,event_type=action,resource_type='report_candidate',
        resource_id=str(candidate.id),context_json=auth.encode({'candidate_id':candidate.id,'sha256':candidate.sha256,
            'from_state':state,'to_state':to_state,'version':version}),reason=reason,source='manual',correlation_id=str(uuid4()))
    db.add(event);db.flush()
    recipients=set(db.scalars(select(User.id).where(User.role=='strategy',User.is_active.is_(True))))
    authority=assignment(db,candidate.organization_id)
    if to_state=='final_review':
        if not authority:auth.fail('Nihai onaycı görevlendirmesi yok. Resmî atamayı kaydedin.',409)
        recipients.add(authority.user_id)
    if not recipients:auth.fail('Zorunlu iç bildirim alıcısı bulunamadı.',409)
    notice=Notification(role='strategy',department_id=None,event_type=action,message=f'Rapor adayı #{candidate.id}: {to_state}. {reason}'[:500],link='',delivery_mode='recipients')
    db.add(notice);db.flush()
    for uid in recipients:db.add(NotificationRecipient(notification_id=notice.id,user_id=uid))
    db.flush();return event


def move(db,projection,to_state):
    result=db.execute(update(ReportCandidateState).where(ReportCandidateState.candidate_id==projection.candidate_id,
        ReportCandidateState.version==projection.version).values(state=to_state,version=projection.version+1))
    if result.rowcount!=1:packages.conflict()
    db.refresh(projection)


def locked(db,actor,organization_id,candidate_id,action,expected_version,expected_hash):
    organization_lock(db,organization_id)
    candidate=db.get(ReportCandidate,candidate_id)
    if not candidate or candidate.organization_id!=organization_id:auth.fail('Rapor adayı bu kuruma ait değil.')
    state=db.scalar(select(ReportCandidateState).where(ReportCandidateState.candidate_id==candidate.id).with_for_update().execution_options(populate_existing=True))
    authority=assignment(db,organization_id)
    ids=[actor.id]+([authority.user_id] if authority else [])
    list(db.scalars(select(User).where(User.id.in_(ids)).order_by(User.id).with_for_update().execution_options(populate_existing=True)))
    allowed(db,actor,action,organization_id,state.state)
    if state.version!=expected_version or candidate.sha256!=expected_hash:packages.conflict()
    verify(db,candidate)
    if candidate.activity_revision_id and state.state!='published':
        revision=db.get(ActivityReportRevision,candidate.activity_revision_id)
        report=db.scalar(select(ActivityReport).where(ActivityReport.id==revision.report_id).with_for_update().execution_options(populate_existing=True))
        if report.current_revision!=revision.revision:packages.conflict()
    return candidate,state


def verify(db,candidate):
    activity_payload=activity_candidate_payload(candidate) if candidate.resource_scope=='activity_report' else None
    if contract.digest(candidate.payload_json)!=candidate.payload_sha256 or hash_content(candidate.payload_json,candidate.manifest_json)!=candidate.sha256:packages.conflict()
    manifest=json.loads(candidate.manifest_json)
    if 'predecessor_release_id' in manifest:verify_activity_successor(db,candidate,manifest)
    elif 'reworks_candidate_id' in manifest or 'reworks_candidate_sha256' in manifest:verify_initial_rework(db,candidate,manifest)
    bindings=db.scalars(select(CandidatePackage).where(CandidatePackage.candidate_id==candidate.id).order_by(CandidatePackage.id)).all()
    if len(bindings)!=len(manifest['packages']):packages.conflict()
    sources=[];departments=set()
    for binding,expected in zip(bindings,manifest['packages']):
        rev=db.get(PackageRevision,binding.package_revision_id)
        if not rev:packages.conflict()
        pkg=db.get(DirectoratePackage,rev.package_id)
        decision=db.get(PackageDecision,binding.strategy_decision_id)
        if not pkg or not decision:packages.conflict()
        if (binding.package_revision_id!=expected['revision_id'] or binding.strategy_decision_id!=expected['decision_id']
            or binding.sha256!=expected['sha256'] or rev.sha256!=binding.sha256 or contract.digest(rev.content_json)!=rev.sha256
            or decision.action!='strategy_approve' or decision.package_revision_id!=rev.id or decision.snapshot_sha256!=rev.sha256
            or pkg.organization_id!=candidate.organization_id or pkg.period_id!=candidate.period_id or pkg.resource_scope!=candidate.resource_scope
            or pkg.source_key!=str(manifest['source_id'])):packages.conflict()
        if expected['package_id']!=pkg.id or expected['department_id']!=pkg.department_id or expected['strategy_event_id']!=decision.workflow_event_id or pkg.department_id in departments:packages.conflict()
        strategy_event=db.get(WorkflowEvent,decision.workflow_event_id)
        if (not strategy_event or strategy_event.event_type!='strategy_approve'
            or strategy_event.resource_type!='directorate_package' or strategy_event.resource_id!=str(pkg.id)
            or strategy_event.organization_id!=pkg.organization_id or strategy_event.department_id!=pkg.department_id):packages.conflict()
        context=json.loads(strategy_event.context_json)
        if context.get('revision_id')!=rev.id or context.get('sha256')!=rev.sha256:packages.conflict()
        # Current state/revision are assembly gates, never historical integrity gates.
        departments.add(pkg.department_id);sources.append(json.loads(rev.content_json))
        packages.validate_package_approval(db,pkg,rev)
    if sorted(departments)!=manifest['required_department_ids']:packages.conflict()
    assembled=activity_payload if candidate.resource_scope=='activity_report' else json.loads(candidate.payload_json)
    if candidate.resource_scope=='performance_program':
        actual={d['department_id']:d for d in assembled['departments']}
        if len(actual)!=len(sources):packages.conflict()
        for source in sources:
            expected=deepcopy(source);expected.pop('validation_context')
            current=deepcopy(actual.get(expected['department_id']))
            if not current:packages.conflict()
            for collection in (expected['indicators'],current['indicators']):
                for row in collection:
                    for key in ('persistent_indicator_id','indicator_id','definition_revision_id'):row.pop(key,None)
            if expected!=current:packages.conflict()
    else:
        expected=[e for source in sources for e in source['entries']]
        realization_keys=activity_realization_keys(assembled)
        current=[{k:v for k,v in e.items() if k not in realization_keys} for e in assembled['entries']]
        if current!=expected:packages.conflict()
    if candidate.resource_scope=='activity_report':verify_materialization(db,candidate)
    else:
        payload=json.loads(candidate.payload_json)
        for row in contract.snapshot_rows(payload).values():
            definition=db.get(IndicatorDefinitionRevision,row['definition_revision_id'])
            if not definition or definition.indicator_id!=row['indicator_id'] or definition.sha256!=contract.digest(definition.definition_json) or definition.definition_json!=canonical(contract.definition_payload(row,payload['period'],contract.publication_contract_version(payload))):packages.conflict()
    return manifest


def program_payload(db,actor,period,departments):
    # The same canonical schema as book_snapshot, assembled solely from frozen packages.
    departments=deepcopy(departments);catalogue={};groups=defaultdict(Decimal);economic=defaultdict(Decimal)
    for dept in departments:
        context=dept.pop('validation_context')
        for official in context['officials']:
            item=catalogue.setdefault(official['id'],dict(official,departments=[]))
            if any(item.get(k)!=v for k,v in official.items()):auth.fail('Paket katalog sürümleri uyuşmuyor.',409)
            if official['id'] in context['responsible_ids']:item['departments'].append(dept['department_id'])
        if dept['scope']['status']=='excluded':continue
        for v in dept['economics']:
            if v['year']>=period.year:economic[(v['category'],v['year'],v['program_group'],v['funding_type'])]+=Decimal(v['amount'])
        for a in dept['activities']:
            for v in a['costs']:
                if v['year']>=period.year and v['amount'] is not None:groups[(a['program'],a['subprogram'],a['id'],a['name'],v['year'],v['funding_type'])]+=Decimal(v['amount'])
    # Strategy-owned report-wide metadata is captured once before final review.
    global_catalogue=db.scalars(select(OfficialActivity).where(OfficialActivity.period_id==period.id).order_by(OfficialActivity.id)).all()
    sections=db.scalars(select(ReportSection).where(ReportSection.period_id==period.id).order_by(ReportSection.position,ReportSection.id)).all()
    if not sections or not global_catalogue:auth.fail('Genel bilgi bölümleri ve sorumlu birim kataloğunu hazırlayın.',409)
    for official in global_catalogue:
        frozen=record(official)
        if official.id in catalogue and any(catalogue[official.id].get(k)!=v for k,v in frozen.items()):
            auth.fail('Onaylı paketin katalog sürümü değişmiş. Güncel onaylı paketleri seçin.',409)
        dept_ids=sorted(db.scalars(select(ActivityResponsibility.department_id).where(ActivityResponsibility.official_activity_id==official.id)).all())
        if official.id not in catalogue:catalogue[official.id]=dict(frozen,departments=dept_ids)
    departments.sort(key=lambda d:(d['scope']['position'],d['department_id']))
    payload={'schema_version':'5.0','period':period.year,'departments':departments,
        'sections':[record(s) for s in sections],
        'catalogue':[dict(item,departments=sorted(set(item['departments']))) for _,item in sorted(catalogue.items())],
        'economics':[{'category':k[0],'year':k[1],'program_group':k[2],'funding_type':k[3],'amount':str(v)} for k,v in sorted(economic.items())],
        'program_costs':[{'program':k[0],'subprogram':k[1],'activity_id':k[2],'name':k[3],'year':k[4],'funding_type':k[5],'amount':str(v)} for k,v in sorted(groups.items())]}
    # Explicit period-row identity only; never match names/codes or read live values.
    seen=set();definitions={}
    for row in contract.snapshot_rows(payload).values():
        live=db.get(Indicator,row['id'])
        if not live or live.period_id!=period.id or live.department_id!=row['department_id']:packages.conflict()
        identity=row.get('persistent_indicator_id') or contract.ensure_identity(db,live)
        identity_row=db.get(IndicatorIdentity,identity)
        if live.persistent_indicator_id!=identity or identity in seen or not identity_row or identity_row.organization_id!=db.get(Department,row['department_id']).organization_id:packages.conflict()
        seen.add(identity)
        definitions[row['id']]=contract.make_definition(db,identity,period.id,row,period.year,actor,contract.CURRENT_DEFINITION_CONTRACT)
    for dept in payload['departments']:
        for row in dept['indicators']:
            definition=definitions[row['id']]
            row.update(indicator_id=definition.indicator_id,persistent_indicator_id=definition.indicator_id,definition_revision_id=definition.id)
    payload.update(activity_contract_version=contract.CURRENT_DEFINITION_CONTRACT,definition_contract_version=contract.CURRENT_DEFINITION_CONTRACT)
    return payload


def materialize(db,actor,source,contents,lineage=None,expected_revision=None):
    """lineage=(predecessor release, its candidate) writes activity-candidate-2; None keeps v1 exactly."""
    if lineage and not references.canonical_contents(contents):lineage=None
    report=db.scalar(select(ActivityReport).where(ActivityReport.id==source.report_id).with_for_update().execution_options(populate_existing=True))
    # A1-F2: re-check under the report lock; a legacy write that committed
    # after the caller's unlocked check must not become this candidate's base.
    if expected_revision is not None and report.current_revision!=expected_revision:packages.conflict()
    new=ActivityReportRevision(report_id=report.id,revision=report.current_revision+1,publication_id=source.publication_id,
        publication_sha256=source.publication_sha256,contract_version=source.contract_version,previous_revision_id=db.scalar(select(ActivityReportRevision.id).where(ActivityReportRevision.report_id==report.id,ActivityReportRevision.revision==report.current_revision)),
        diff_json='[]',revision_reason='Onaylı müdürlük paketlerinden nihai rapor adayı oluşturuldu.',created_by=actor.id)
    db.add(new);db.flush();report.current_revision=new.revision;report.lock_version+=1;db.flush()
    entries=[]
    for content in contents:
        for entry in content['entries']:
            old=db.get(ReportIndicator,entry['report_indicator_id'])
            ri=ReportIndicator(report_revision_id=new.id,publication_binding_id=old.publication_binding_id);db.add(ri);db.flush()
            if lineage:
                entries.append(references.realize(db,actor,new,ri,entry,*lineage));continue
            actual=ActualRevision(report_indicator_id=ri.id,revision=1,supersedes_id=None,value=contract.parse_actual(entry['value']),
                raw_text=entry['value'] or '',state=entry['state'],evidence_json=canonical(entry['evidence']),
                explanation=entry['explanation'],deviation_json=canonical(entry['deviation']),created_by=actor.id)
            db.add(actual);db.flush()
            entries.append(dict(entry,materialized_report_indicator_id=ri.id,materialized_actual_revision_id=actual.id))
    return new,{'schema_version':references.CANDIDATE_V2 if lineage else references.CANDIDATE_V1,'report_revision_id':new.id,'publication_id':source.publication_id,
        'publication_sha256':source.publication_sha256,'contract_version':source.contract_version,'entries':entries}


def activity_realization_keys(payload):
    """Only the schema's own realization keys may be excluded from package comparison."""
    if (not isinstance(payload,dict) or not isinstance(payload.get('schema_version'),str)
        or payload['schema_version'] not in references.REALIZATION_KEYS):packages.conflict()
    return set(references.REALIZATION_KEYS[payload['schema_version']])


def activity_candidate_payload(candidate):
    """Validate the Activity verification boundary; no implicit schema default."""
    try:payload=json.loads(candidate.payload_json)
    except (TypeError,ValueError):packages.conflict()
    activity_realization_keys(payload)
    entries=payload.get('entries')
    if not isinstance(entries,list) or any(not isinstance(entry,dict) for entry in entries):packages.conflict()
    # Invalid identifiers must not reach database lookup/coercion as SQL errors.
    if type(payload.get('report_revision_id')) is not int:packages.conflict()
    if payload['schema_version']==references.CANDIDATE_V2:
        references.validate_v2_entries(candidate,payload);return payload
    for entry in entries:
        for key in ('materialized_report_indicator_id','materialized_actual_revision_id','definition_revision_id'):
            identifier=entry.get(key)
            if type(identifier) is not int or not 0<identifier<=2147483647:packages.conflict()
    return payload


def verify_materialization(db,candidate):
    payload=activity_candidate_payload(candidate)
    # Explicit schema dispatch; unknown schemas already failed in activity_candidate_payload.
    try:
        if payload['schema_version']==references.CANDIDATE_V2:references.verify_v2(db,candidate,payload)
        else:_verify_materialization_v1(db,candidate,payload)
    except (KeyError,TypeError,AttributeError,ValueError):packages.conflict()
    except auth.HTTPException as exc:
        if exc.status_code==422:packages.conflict()
        raise


def _verify_materialization_v1(db,candidate,payload):
    revision=db.get(ActivityReportRevision,candidate.activity_revision_id)
    report=db.get(ActivityReport,revision.report_id)
    if payload['report_revision_id']!=revision.id:packages.conflict()
    items=db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id==revision.id)).all()
    if {i.id for i in items}!={e['materialized_report_indicator_id'] for e in payload['entries']}:packages.conflict()
    for entry in payload['entries']:
        ri=db.get(ReportIndicator,entry['materialized_report_indicator_id']);a=db.get(ActualRevision,entry['materialized_actual_revision_id'])
        binding=db.get(PublicationIndicatorBinding,ri.publication_binding_id)
        actuals=db.scalars(select(ActualRevision).where(ActualRevision.report_indicator_id==ri.id)).all()
        if len(actuals)!=1 or a.report_indicator_id!=ri.id or a.value!=contract.parse_actual(entry['value']) or a.state!=entry['state'] or json.loads(a.evidence_json)!=entry['evidence'] or a.explanation!=entry['explanation'] or json.loads(a.deviation_json)!=entry['deviation'] or binding.definition_revision_id!=entry['definition_revision_id']:packages.conflict()


def assemble_candidate(db,actor,organization_id,resource_scope,source_id,package_ids,predecessor_candidate_id=None):
    organization_lock(db,organization_id);allowed(db,actor,'assemble_candidate',organization_id,'assembling')
    if not isinstance(package_ids,list) or len(package_ids)!=len(set(package_ids)):auth.fail('Yinelenen paket gönderilemez.',409)
    source=None
    if resource_scope=='performance_program':
        period=db.get(ReportingPeriod,source_id);key=str(source_id)
        required=set(db.scalars(select(Department.id).where(Department.organization_id==organization_id)))
        scopes=db.scalars(select(DepartmentScope).where(DepartmentScope.period_id==source_id,DepartmentScope.department_id.in_(required))).all()
        if {s.department_id for s in scopes}!=required:auth.fail('Her müdürlüğün dönem kapsamını açıkça belirtin.',409)
    elif resource_scope=='activity_report':
        source=db.get(ActivityReportRevision,source_id);report=db.get(ActivityReport,source.report_id) if source else None
        if not report or report.organization_id!=organization_id:auth.fail('Faaliyet raporu bu kuruma ait değil.')
        period=db.get(ReportingPeriod,report.period_id);key=str(report.id)
        if db.scalar(select(ReportRelease.id).where(ReportRelease.organization_id==organization_id,ReportRelease.resource_scope=='activity_report',ReportRelease.report_key==key)):
            auth.fail('Bu faaliyet raporu yayımlandı. Tam öncül yayını seçerek assemble_activity_successor yolunu kullanın.',409)
        required=set(db.scalars(select(PublicationIndicatorBinding.department_id).join(ReportIndicator,ReportIndicator.publication_binding_id==PublicationIndicatorBinding.id).where(ReportIndicator.report_revision_id==source.id)))
    else:auth.fail('Rapor türü tanınmıyor.',403)
    if not period or not required:auth.fail('Geçerli dönem ve zorunlu müdürlük kapsamı bulunamadı.',409)
    previous=db.scalar(select(ReportCandidate).where(ReportCandidate.organization_id==organization_id,ReportCandidate.resource_scope==resource_scope,ReportCandidate.report_key==key).order_by(ReportCandidate.sequence.desc()))
    if (previous.id if previous else None)!=predecessor_candidate_id:packages.conflict()
    if previous and db.get(ReportCandidateState,previous.id).state!='returned_to_strategy':auth.fail('Mevcut aday sonuçlanmadan yeni aday oluşturulamaz.',409)
    # A1-P1.1 R10: an initial Activity rework records the exact returned attempt it
    # reworks and continues the same source revision; the attempt stays immutable.
    rework=returned_initial_proof(db,previous) if previous and resource_scope=='activity_report' else None
    if rework and json.loads(rework.manifest_json).get('source_id')!=source_id:
        auth.fail('Yeniden çalışma, iade edilen adayın kaynak rapor revizyonundan yapılmalıdır. Aynı kaynağın onaylı müdürlük paketlerini seçin.',409)
    if source:
        current=db.get(ActivityReport,source.report_id)
        expected_revision=db.get(ActivityReportRevision,previous.activity_revision_id).revision if previous else source.revision
        if current.current_revision!=expected_revision or (not previous and db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id==source.id))):packages.conflict()
    selected=[];departments=set()
    # Same dept->package lock order as Phase 3; serialize shared report construction by org.
    for pid in sorted(package_ids):
        pkg=db.get(DirectoratePackage,pid)
        if not pkg or pkg.organization_id!=organization_id or pkg.period_id!=period.id or pkg.resource_scope!=resource_scope or pkg.source_key!=str(source_id):auth.fail('Paket farklı dönem / kurum / rapora ait.',409)
        auth.scope_department(db,organization_id,pkg.department_id,lock=True)
        pkg=db.scalar(select(DirectoratePackage).where(DirectoratePackage.id==pid).with_for_update().execution_options(populate_existing=True))
        if pkg.state!='strategy_approved' or pkg.department_id in departments:auth.fail('Her müdürlük için tek güncel Strateji onaylı paket gerekir.',409)
        departments.add(pkg.department_id);rev=packages.revision(db,pkg)
        decision=db.scalar(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id,PackageDecision.action=='strategy_approve',PackageDecision.snapshot_sha256==rev.sha256).order_by(PackageDecision.id.desc()))
        if not decision:auth.fail('Paketin tam sürümüne bağlı Strateji kararı bulunamadı.',409)
        packages.validate_package_approval(db,pkg,rev);selected.append((pkg,rev,decision))
    if departments!=required:auth.fail('Tüm zorunlu müdürlük paketlerini eksiksiz seçin.',409)
    with db.begin_nested():
        db.scalar(select(User).where(User.id==actor.id).with_for_update().execution_options(populate_existing=True))
        allowed(db,actor,'assemble_candidate',organization_id,'assembling')
        contents=[json.loads(r.content_json) for p,r,d in selected]
        if resource_scope=='performance_program':
            frozen_scopes={s.department_id:record(s) for s in db.scalars(select(DepartmentScope).where(DepartmentScope.period_id==period.id,DepartmentScope.department_id.in_(required)).with_for_update().execution_options(populate_existing=True))}
            if any(c['period']!=period.year or c['scope']!=frozen_scopes.get(c['department_id']) for c in contents):
                auth.fail('Paket kapsamı / dönem metaverisi değişmiş. Güncel kapsamın onaylı paketini seçin.',409)
        if source:
            new,payload=materialize(db,actor,source,contents,expected_revision=expected_revision)
            if not previous and db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id==source.id)):packages.conflict()
            activity_revision_id=new.id
        else:payload=program_payload(db,actor,period,contents);activity_revision_id=None
        manifest={'version':'report-manifest-1','organization_id':organization_id,'period_id':period.id,'resource_scope':resource_scope,
            'source_id':source_id,'required_department_ids':sorted(required),'packages':[{'package_id':p.id,'department_id':p.department_id,
                'revision_id':r.id,'sha256':r.sha256,'decision_id':d.id,'strategy_event_id':d.workflow_event_id} for p,r,d in selected]}
        if rework:manifest.update(reworks_candidate_id=rework.id,reworks_candidate_sha256=rework.sha256)
        raw=canonical(payload);mraw=canonical(manifest)
        candidate=ReportCandidate(organization_id=organization_id,period_id=period.id,resource_scope=resource_scope,report_key=key,
            sequence=previous.sequence+1 if previous else 1,predecessor_candidate_id=previous.id if previous else None,
            activity_revision_id=activity_revision_id,payload_json=raw,payload_sha256=contract.digest(raw),manifest_json=mraw,
            sha256=hash_content(raw,mraw),created_by=actor.id)
        db.add(candidate);db.flush();db.add(ReportCandidateState(candidate_id=candidate.id,state='assembling',version=0))
        for pkg,rev,decision in selected:db.add(CandidatePackage(candidate_id=candidate.id,package_revision_id=rev.id,strategy_decision_id=decision.id,sha256=rev.sha256))
        db.flush();event_notice(db,actor,candidate,'candidate_assembled','assembling','assembling',0)
        verify(db,candidate)
    return candidate


def verify_activity_successor(db,candidate,manifest):
    """Historical lineage verification never substitutes a newer release/package."""
    try:
        predecessor_id=manifest['predecessor_release_id']
        if type(predecessor_id) is not int or not 0<predecessor_id<=2147483647:packages.conflict()
        release=db.get(ReportRelease,predecessor_id)
        previous=db.get(ReportCandidate,release.candidate_id) if release else None
        if not previous or candidate.resource_scope!='activity_report':packages.conflict()
        parent=json.loads(previous.manifest_json)
        attempt=previous
        if 'reworks_candidate_id' in manifest:
            attempt=db.get(ReportCandidate,manifest['reworks_candidate_id'])
            if not attempt or attempt.sequence>=candidate.sequence or attempt.sha256!=manifest.get('reworks_candidate_sha256'):packages.conflict()
            returned_attempt_proof(db,attempt,release);verify(db,attempt)
        elif 'reworks_candidate_sha256' in manifest:packages.conflict()
        source=db.get(ActivityReportRevision,attempt.activity_revision_id)
        revision=db.get(ActivityReportRevision,candidate.activity_revision_id)
        if (manifest['successor_contract']!=references.SUCCESSOR_CONTRACTS[activity_candidate_payload(candidate)['schema_version']]
            or manifest['predecessor_candidate_sha256']!=previous.sha256
            or candidate.predecessor_candidate_id!=previous.id or candidate.sequence!=attempt.sequence+1
            or (candidate.organization_id,candidate.resource_scope,candidate.report_key,candidate.period_id)
               !=(release.organization_id,release.resource_scope,release.report_key,previous.period_id)
            or manifest['source_id']!=parent['source_id'] or manifest['required_department_ids']!=parent['required_department_ids']
            or revision.previous_revision_id!=source.id or revision.report_id!=source.report_id or revision.revision!=source.revision+1
            or revision.publication_id!=source.publication_id or revision.publication_sha256!=source.publication_sha256):packages.conflict()
        old={b['package_id']:b for b in parent['packages']}
        current={b['package_id']:b for b in manifest['packages']}
        if len(current)!=len(manifest['packages']) or set(current)!=set(old):packages.conflict()
        ids=manifest['correction_cycle_ids']
        if not isinstance(ids,list) or not ids or any(type(i) is not int for i in ids) or len(set(ids))!=len(ids):packages.conflict()
        cycles=list(db.scalars(select(RevisionCorrectionCycle).where(RevisionCorrectionCycle.id.in_(ids))))
        if len(cycles)!=len(ids) or any(c.source_release_id!=release.id or c.package_id not in current
            or c.source_package_revision_id!=old[c.package_id]['revision_id'] for c in cycles):packages.conflict()
        corrected={c.package_id:c for c in cycles}
        for pid,binding in current.items():
            if pid not in corrected:
                if binding!=old[pid]:packages.conflict()
                continue
            # Follow only immutable explicit parents back to this cycle's opening copy.
            cycle=corrected[pid];row=db.get(PackageRevision,binding['revision_id']);seen=set()
            while row and row.id!=cycle.opening_revision_id:
                if row.id in seen or row.package_id!=pid:packages.conflict()
                seen.add(row.id);row=db.get(PackageRevision,row.previous_revision_id)
            if not row or row.package_id!=pid or row.previous_revision_id!=cycle.source_package_revision_id:packages.conflict()
        verify(db,previous);verify_artifact(db,release)
    except (KeyError,TypeError,AttributeError,ValueError):packages.conflict()


def latest_successor_attempt(db,release):
    return db.scalar(select(ReportCandidate).where(ReportCandidate.organization_id==release.organization_id,
        ReportCandidate.resource_scope==release.resource_scope,ReportCandidate.report_key==release.report_key)
        .order_by(ReportCandidate.sequence.desc()))


def returned_attempt_proof(db,attempt,release):
    if json.loads(attempt.manifest_json).get('predecessor_release_id')!=release.id or not final_return_proof(db,attempt):packages.conflict()
    return attempt


def final_return_proof(db,attempt):
    """The attempt's exact, reasoned final_return decision (shared by both rework lineages)."""
    state=db.get(ReportCandidateState,attempt.id,populate_existing=True)
    decision=db.scalar(select(ReportDecision).where(ReportDecision.candidate_id==attempt.id,ReportDecision.action=='final_return'))
    ev=db.get(WorkflowEvent,decision.workflow_event_id) if decision else None
    return bool(state and state.state=='returned_to_strategy' and decision and decision.candidate_sha256==attempt.sha256 and ev
        and ev.event_type=='final_return' and ev.resource_type=='report_candidate' and ev.resource_id==str(attempt.id)
        and ev.organization_id==attempt.organization_id and ev.reason.strip() and json.loads(ev.context_json).get('sha256')==attempt.sha256)


def returned_initial_proof(db,attempt):
    """A1-P1.1 R10: a returned, never-published initial Activity attempt (no predecessor release)."""
    if (not attempt or attempt.resource_scope!='activity_report' or 'predecessor_release_id' in json.loads(attempt.manifest_json)
        or not final_return_proof(db,attempt)):packages.conflict()
    return attempt


def verify_initial_rework(db,candidate,manifest):
    """Historical lineage of an initial Activity rework: exactly the returned attempt it reworks."""
    try:
        attempt=db.get(ReportCandidate,manifest['reworks_candidate_id']) if type(manifest.get('reworks_candidate_id')) is int else None
        if not attempt or candidate.resource_scope!='activity_report' or attempt.sha256!=manifest.get('reworks_candidate_sha256'):packages.conflict()
        returned_initial_proof(db,attempt)
        parent=json.loads(attempt.manifest_json)
        source=db.get(ActivityReportRevision,attempt.activity_revision_id);revision=db.get(ActivityReportRevision,candidate.activity_revision_id)
        if (candidate.predecessor_candidate_id!=attempt.id or candidate.sequence!=attempt.sequence+1
            or (candidate.organization_id,candidate.resource_scope,candidate.report_key,candidate.period_id)
               !=(attempt.organization_id,attempt.resource_scope,attempt.report_key,attempt.period_id)
            or manifest['source_id']!=parent['source_id'] or manifest['required_department_ids']!=parent['required_department_ids']
            or {b['package_id'] for b in manifest['packages']}!={b['package_id'] for b in parent['packages']}
            or revision.previous_revision_id!=source.id or revision.report_id!=source.report_id or revision.revision!=source.revision+1
            or revision.publication_id!=source.publication_id or revision.publication_sha256!=source.publication_sha256):packages.conflict()
        verify(db,attempt)
    except (KeyError,TypeError,AttributeError,ValueError):packages.conflict()


def initial_rework_attempt(db,package):
    """A1-P1.1 R10: the latest returned initial attempt whose packages may be reworked, or None.

    Only before any release, only while that attempt is the report's latest
    candidate and its materialization is still the current report revision, and
    only for a package that attempt bound."""
    if package.resource_scope!='activity_report':return None
    source=db.get(ActivityReportRevision,package.report_revision_id)
    report=db.get(ActivityReport,source.report_id) if source else None
    if not report or report.organization_id!=package.organization_id:return None
    key=str(report.id)
    if db.scalar(select(ReportRelease.id).where(ReportRelease.organization_id==report.organization_id,
            ReportRelease.resource_scope=='activity_report',ReportRelease.report_key==key)):return None
    latest=db.scalar(select(ReportCandidate).where(ReportCandidate.organization_id==report.organization_id,
        ReportCandidate.resource_scope=='activity_report',ReportCandidate.report_key==key).order_by(ReportCandidate.sequence.desc()))
    if not latest:return None
    manifest=json.loads(latest.manifest_json)
    if ('predecessor_release_id' in manifest or manifest.get('source_id')!=source.id
        or package.id not in {b['package_id'] for b in manifest['packages']} or not final_return_proof(db,latest)):return None
    materialized=db.get(ActivityReportRevision,latest.activity_revision_id)
    if not materialized or report.current_revision!=materialized.revision:return None
    return latest


def require_returned_attempt(db,release_id):
    from .revision_workflow_service import current_source
    release,previous=current_source(db,release_id)
    attempt=latest_successor_attempt(db,release)
    if not attempt or attempt.id==previous.id:auth.fail('Yeniden çalışma için nihai iade edilmiş son ardıl aday gerekir.',409)
    return returned_attempt_proof(db,attempt,release)


def assemble_activity_successor(db,actor,organization_id,report_id,predecessor_release_id,package_ids):
    """Disabled workflow: successor assembly (references only behind ACTIVITY_REFERENCE_SUCCESSORS); caller owns commit."""
    organization_lock(db,organization_id)
    allowed(db,actor,'assemble_candidate',organization_id,'assembling')
    from .revision_workflow_service import current_source
    explicit=db.get(ReportRelease,predecessor_release_id)
    if not explicit or (explicit.organization_id,explicit.resource_scope,explicit.report_key)!=(organization_id,'activity_report',str(report_id)):
        auth.fail('Ardıl aday için aynı kurum ve raporun tam yayımlanmış öncül sürümünü seçin.',409)
    release,previous=current_source(db,predecessor_release_id)
    attempt=latest_successor_attempt(db,release)
    rework=returned_attempt_proof(db,attempt,release) if attempt.id!=previous.id else None
    source=db.get(ActivityReportRevision,(rework or previous).activity_revision_id)
    report=db.get(ActivityReport,report_id,populate_existing=True)
    if not report or report.organization_id!=organization_id or report.period_id!=previous.period_id or source.report_id!=report.id or report.current_revision!=source.revision:packages.conflict()
    parent=json.loads(previous.manifest_json);old={b['package_id']:b for b in parent['packages']}
    if not isinstance(package_ids,list) or any(type(i) is not int for i in package_ids) or len(set(package_ids))!=len(package_ids) or set(package_ids)!=set(old):
        auth.fail('Öncül yayının tüm müdürlük paketlerini tam kimlikleriyle seçin.',409)
    cycles=list(db.scalars(select(RevisionCorrectionCycle).where(RevisionCorrectionCycle.source_release_id==release.id)))
    if not cycles:auth.fail('Ardıl aday için öncüle bağlı düzeltme ve yeniden onay gerekir.',409)
    corrected={c.package_id:c for c in cycles};selected=[];departments=set()
    for pid in sorted(package_ids):
        pkg=db.get(DirectoratePackage,pid)
        if not pkg or (pkg.organization_id,pkg.resource_scope,pkg.period_id,pkg.source_key)!=(organization_id,'activity_report',previous.period_id,str(parent['source_id'])):packages.conflict()
        auth.scope_department(db,organization_id,pkg.department_id,lock=True)
        pkg=db.scalar(select(DirectoratePackage).where(DirectoratePackage.id==pid).with_for_update().execution_options(populate_existing=True))
        if pkg.state!='strategy_approved' or pkg.department_id in departments:
            auth.fail('Açık düzeltmeler hazır değil. Her seçilen paketi önce Müdür ve Strateji onayından geçirin.',409)
        departments.add(pkg.department_id);rev=packages.revision(db,pkg)
        if pid not in corrected and rev.id!=old[pid]['revision_id']:packages.conflict()
        if pid in corrected and corrected[pid].source_package_revision_id!=old[pid]['revision_id']:packages.conflict()
        decision=db.scalar(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id,
            PackageDecision.action=='strategy_approve',PackageDecision.snapshot_sha256==rev.sha256).order_by(PackageDecision.id.desc()))
        if not decision:auth.fail('Tam güncel paket revizyonu/hash için Strateji kararı bulunamadı.',409)
        strategy_event=db.get(WorkflowEvent,decision.workflow_event_id)
        if (decision.package_revision_id!=rev.id or decision.snapshot_sha256!=rev.sha256 or decision.action!='strategy_approve'
            or not strategy_event or strategy_event.event_type!='strategy_approve'
            or strategy_event.resource_type!='directorate_package' or strategy_event.resource_id!=str(pkg.id)
            or strategy_event.organization_id!=pkg.organization_id or strategy_event.department_id!=pkg.department_id):packages.conflict()
        try:context=json.loads(strategy_event.context_json)
        except (TypeError,ValueError):packages.conflict()
        if not isinstance(context,dict) or context.get('revision_id')!=rev.id or context.get('sha256')!=rev.sha256:packages.conflict()
        packages.validate_package_approval(db,pkg,rev);selected.append((pkg,rev,decision))
    if departments!=set(parent['required_department_ids']) or not set(corrected)<=set(package_ids):packages.conflict()
    pending=db.execute(select(RevisionRequest,RevisionRequestState).join(RevisionRequestState,RevisionRequestState.request_id==RevisionRequest.id)
        .where(RevisionRequest.source_release_id==release.id,RevisionRequestState.state.in_(['requested','accepted','editing']))).all()
    participant_grants=[]
    for request,state in pending:
        grant=db.scalar(select(RevisionEditGrant).where(RevisionEditGrant.request_id==request.id))
        if state.state!='editing' or not grant or grant.cycle_id not in {c.id for c in cycles}:
            auth.fail(f'Düzeltme talebi #{request.id} henüz ardıl adaya hazır değil. Talebi sonuçlandırın veya izin/düzeltme/onay adımlarını tamamlayın; otomatik taşıma yapılmaz.',409)
        participant_grants.append({'request_id':request.id,'grant_id':grant.id,'cycle_id':grant.cycle_id})
    successor_participation_gate(db,release,cycles,{p.id:r for p,r,d in selected},pending)
    with db.begin_nested():
        db.scalar(select(User).where(User.id==actor.id).with_for_update().execution_options(populate_existing=True))
        allowed(db,actor,'assemble_candidate',organization_id,'assembling')
        # Match initial assembly: org -> department/package/user -> report.
        report=db.scalar(select(ActivityReport).where(ActivityReport.id==report_id).with_for_update().execution_options(populate_existing=True))
        if report.current_revision!=source.revision:packages.conflict()
        # References bind to the published predecessor release only, never the returned attempt.
        new,payload=materialize(db,actor,source,[json.loads(r.content_json) for p,r,d in selected],
            (release,previous) if ACTIVITY_REFERENCE_SUCCESSORS else None)
        if new.previous_revision_id!=source.id:packages.conflict()
        manifest={'version':'report-manifest-1','organization_id':organization_id,'period_id':previous.period_id,
            'resource_scope':'activity_report','source_id':parent['source_id'],'required_department_ids':parent['required_department_ids'],
            'predecessor_release_id':release.id,'predecessor_candidate_sha256':previous.sha256,
            'successor_contract':references.SUCCESSOR_CONTRACTS[payload['schema_version']],'correction_cycle_ids':sorted(c.id for c in cycles),
            'correction_request_grants':sorted(participant_grants,key=lambda entry:entry['request_id']),
            'packages':[{'package_id':p.id,'department_id':p.department_id,'revision_id':r.id,'sha256':r.sha256,
                'decision_id':d.id,'strategy_event_id':d.workflow_event_id} for p,r,d in selected]}
        if rework:manifest.update(reworks_candidate_id=rework.id,reworks_candidate_sha256=rework.sha256)
        raw=canonical(payload);mraw=canonical(manifest)
        candidate=ReportCandidate(organization_id=organization_id,period_id=previous.period_id,resource_scope='activity_report',
            report_key=str(report.id),sequence=(rework or previous).sequence+1,predecessor_candidate_id=previous.id,activity_revision_id=new.id,
            payload_json=raw,payload_sha256=contract.digest(raw),manifest_json=mraw,sha256=hash_content(raw,mraw),created_by=actor.id)
        db.add(candidate);db.flush();db.add(ReportCandidateState(candidate_id=candidate.id,state='assembling',version=0))
        for pkg,rev,decision in selected:
            db.add(CandidatePackage(candidate_id=candidate.id,package_revision_id=rev.id,strategy_decision_id=decision.id,sha256=rev.sha256))
        db.flush();event_notice(db,actor,candidate,'candidate_assembled','assembling','assembling',0)
        verify(db,candidate)
    return candidate


def successor_participation_gate(db,release,cycles,bound,pending):
    """A1-F1 primary prevention: never create a successor around a net-zero participant.

    Every listed participant must carry its own semantic net correction. Strategy
    closes net-zero requests explicitly BEFORE assembly; nothing is closed automatically."""
    from . import revision_workflow_service as corrections
    by_id={c.id:c for c in cycles}
    for cycle in cycles:
        if cycle.package_id in bound:corrections.verify_correction_lineage(db,cycle,bound[cycle.package_id])
    empty=[]
    for request,state in pending:
        grant=db.scalar(select(RevisionEditGrant).where(RevisionEditGrant.request_id==request.id))
        cycle=by_id[grant.cycle_id]
        if cycle.package_id not in bound:packages.conflict()
        if not corrections.has_net_correction(db,request,grant,cycle,bound[cycle.package_id]):empty.append(request.id)
    if empty:
        names=', '.join(f'#{rid}' for rid in sorted(empty))
        auth.fail(f'Düzeltme talebi {names} izinli alanlarda net değişiklik içermiyor; ardıl aday oluşturulmadı. '
            'Talep sahibi düzeltmeyi tamamlamalı veya Strateji bu talepleri aday oluşturmadan önce gerekçeyle değişikliksiz kapatmalıdır.',409)
    # A surviving closed_no_change edit is refused at publication (S3C-2 B2),
    # not here: the returned candidate is the exit that reopens and reverts it.


def request_final_review(db,actor,org,candidate_id,version,sha):
    candidate,state=locked(db,actor,org,candidate_id,'request_final_review',version,sha)
    with db.begin_nested():
        event_notice(db,actor,candidate,'request_final_review',state.state,'final_review',state.version+1)
        move(db,state,'final_review')
    return state


def final_decision(db,actor,org,candidate_id,action,version,sha,reason=''):
    if action not in {'final_approve','final_return'}:auth.fail('Nihai işlem tanınmıyor.')
    candidate,state=locked(db,actor,org,candidate_id,action,version,sha);current=assignment(db,org)
    if action=='final_return':reason=auth.required(reason,'Nihai iade gerekçesi')
    # A1-F1: Strategy never exercises the recovery exit, even when it formally
    # holds the assignment (same separation as publication).
    if action=='final_return' and state.state=='final_approved' and actor.role=='strategy':
        auth.fail('Nihai onaylı adayı yalnız görevli nihai onaycı iade edebilir; Strateji bu işlemi yapamaz.')
    # A1-P1.1 R10: the exit serves Activity candidates only. A first candidate is
    # reworked on the initial lineage (reworks_candidate_id), a successor on S3C-2.
    if action=='final_return' and state.state=='final_approved':
        if candidate.resource_scope!='activity_report':
            auth.fail('Nihai onaylı Performans Programı adayı iade edilemez; yalnız Faaliyet Raporu adayı nihai onaydan sonra iade edilebilir.',409)
        # WF-3: the rework needs the PostgreSQL-only package reopen; never strand a returned first candidate elsewhere.
        if 'predecessor_release_id' not in json.loads(candidate.manifest_json) and db.get_bind().dialect.name!='postgresql':
            auth.fail('Nihai onaylı ilk adayın iadesi ve yeniden çalışması PostgreSQL güvenlik denetimleri gerektirir.',409)
        if 'predecessor_release_id' not in json.loads(candidate.manifest_json) and db.scalar(select(ReportRelease.id).where(
                ReportRelease.organization_id==org,ReportRelease.resource_scope=='activity_report',ReportRelease.report_key==candidate.report_key)):
            auth.fail('Bu Faaliyet Raporu yayımlandı; yayımlanmamış ilk aday artık iade edilemez. Yayımlanmış sürüm için düzeltme talebi açın.',409)
    if action=='final_approve' and state.state=='final_approved' and db.scalar(select(ReportDecision.id).where(ReportDecision.candidate_id==candidate.id,ReportDecision.action=='final_approve',ReportDecision.assignment_id==current.id)):auth.fail('Bu yetkili aynı adayı zaten onayladı.',409)
    # A1-F1 recovery exit: final_approved -> final_return only before publication.
    if action=='final_return' and db.scalar(select(ReportRelease.id).where(ReportRelease.candidate_id==candidate.id)):
        auth.fail('Yayımlanmış rapor adayı iade edilemez. Yayımlanmış sürüm için düzeltme talebi açın.',409)
    approval=None
    if action=='final_approve' and candidate.activity_revision_id:
        # A1-F2: only this candidate's own earlier final approval may be reused
        # (same candidate, changed assignment); any other freeze fails closed.
        approval=db.scalar(select(ActivityReportApproval).where(ActivityReportApproval.report_revision_id==candidate.activity_revision_id))
        if approval and not db.scalar(select(ReportDecision.id).where(ReportDecision.candidate_id==candidate.id,
                ReportDecision.action=='final_approve',ReportDecision.activity_approval_id==approval.id)):
            auth.fail('Aday rapor revizyonunda nihai onaycı kararı dışında oluşturulmuş bir onay kaydı var; bu onay devralınmaz. '
                'Adayı nihai onaycı iade etsin ve Strateji yeni aday oluştursun.',409)
    with db.begin_nested():
        allowed(db,actor,action,org,state.state)
        destination='final_approved' if action=='final_approve' else 'returned_to_strategy'
        # The freeze is created after its exact final_approve event so the
        # database can bind it to the current final authority (A1-F2).
        event=event_notice(db,actor,candidate,action,state.state,destination,state.version+1,reason)
        if action=='final_approve' and candidate.activity_revision_id and not approval:
            approval=ActivityReportApproval(report_revision_id=candidate.activity_revision_id,created_by=actor.id);db.add(approval);db.flush()
        decision=ReportDecision(candidate_id=candidate.id,action=action,candidate_sha256=candidate.sha256,
            assignment_id=current.id,workflow_event_id=event.id,activity_approval_id=approval.id if approval else None)
        db.add(decision);db.flush();move(db,state,destination)
    return decision


def successor_publication_context(db,candidate,manifest):
    """Current gates only: historical verification deliberately stays immutable."""
    from . import revision_workflow_service as corrections
    predecessor,previous=corrections.current_source(db,manifest['predecessor_release_id'])
    verify_activity_successor(db,candidate,manifest)
    cycles=set(db.scalars(select(RevisionCorrectionCycle.id).where(RevisionCorrectionCycle.source_release_id==predecessor.id)))
    if cycles!=set(manifest['correction_cycle_ids']):
        auth.fail('Öncülün düzeltme döngüleri aday oluşturulduktan sonra değişti; tam döngü kümesi eşleşmelidir.',409)
    bound={}
    for binding in db.scalars(select(CandidatePackage).where(CandidatePackage.candidate_id==candidate.id)):
        revision=db.get(PackageRevision,binding.package_revision_id)
        pkg=db.get(DirectoratePackage,revision.package_id,populate_existing=True)
        current=packages.revision(db,pkg)
        if pkg.state!='strategy_approved' or current.id!=revision.id or current.sha256!=binding.sha256:
            auth.fail('Paket aday oluşturulduktan sonra değişti. Tam güncel yeniden onaylı revizyonla açıkça yeni ardıl aday oluşturun.',409)
        bound[pkg.id]=revision
    for closed in db.scalars(select(RevisionRequest).join(RevisionRequestState,RevisionRequestState.request_id==RevisionRequest.id)
        .where(RevisionRequest.source_release_id==predecessor.id,RevisionRequestState.state=='closed_no_change')):
        grant=db.scalar(select(RevisionEditGrant).where(RevisionEditGrant.request_id==closed.id))
        cycle=db.get(RevisionCorrectionCycle,grant.cycle_id) if grant else None
        if cycle and cycle.package_id in bound and corrections.closed_request_survives(db,closed,grant,cycle,bound[cycle.package_id]):
            auth.fail('closed_no_change talebi ardıl içeriğe katkı yapamaz.',409)
    participants=manifest.get('correction_request_grants')
    if not isinstance(participants,list) or not participants:packages.conflict()
    represented={}
    for entry in participants:
        if not isinstance(entry,dict) or set(entry)!={'request_id','grant_id','cycle_id'} or any(type(v) is not int for v in entry.values()):packages.conflict()
        if entry['request_id'] in represented:packages.conflict()
        represented[entry['request_id']]=entry
    pending=db.execute(select(RevisionRequest,RevisionRequestState).join(RevisionRequestState,RevisionRequestState.request_id==RevisionRequest.id)
        .where(RevisionRequest.source_release_id==predecessor.id,RevisionRequestState.state.not_in(['rejected','cancelled','stale','closed_no_change']))).all()
    represented_open=set()
    for rid in represented:
        request=db.get(RevisionRequest,rid);state=db.get(RevisionRequestState,rid,populate_existing=True)
        if not request or request.source_release_id!=predecessor.id or not state:packages.conflict()
        if state.state=='closed_no_change':
            grant=db.get(RevisionEditGrant,represented[rid]['grant_id'])
            cycle=db.get(RevisionCorrectionCycle,represented[rid]['cycle_id'])
            if not grant or not cycle or grant.request_id!=rid or grant.cycle_id!=cycle.id or cycle.package_id not in bound:packages.conflict()
            if corrections.closed_request_survives(db,request,grant,cycle,bound[cycle.package_id]):
                auth.fail('closed_no_change talebi ardıl içeriğe katkı yapamaz.',409)
        else:represented_open.add(rid)
    if not pending or {q.id for q,s in pending}!=represented_open:
        auth.fail('Öncüle bağlı yeni veya temsil edilmeyen düzeltme işleri var. Her talebi açıkça sonuçlandırın; otomatik taşıma yapılmaz.',409)
    result=[]
    for request,state in pending:
        entry=represented[request.id];grant=db.get(RevisionEditGrant,entry['grant_id']);cycle=db.get(RevisionCorrectionCycle,entry['cycle_id'])
        if (state.state!='editing' or not grant or not cycle or grant.request_id!=request.id or grant.cycle_id!=cycle.id
            or grant.source_release_id!=predecessor.id or cycle.source_release_id!=predecessor.id
            or cycle.id not in manifest['correction_cycle_ids'] or cycle.package_id not in bound):packages.conflict()
        if not corrections.has_net_correction(db,request,grant,cycle,bound[cycle.package_id]):
            auth.fail(f'Talep #{request.id} için izinli alanda net değişiklik ve tam düzeltme kökeni yok. Strateji talebi gerekçeyle closed_no_change olarak kapatmalıdır.',409)
        result.append((request,state,grant))
    return predecessor,previous,result


def publish(db,actor,org,candidate_id,version,sha):
    candidate,state=locked(db,actor,org,candidate_id,'publish_report',version,sha)
    manifest=json.loads(candidate.manifest_json)
    if state.state=='published':
        release=db.scalar(select(ReportRelease).where(ReportRelease.candidate_id==candidate.id));verify_artifact(db,release);return release
    predecessor=previous=None;participants=[]
    if 'predecessor_release_id' in manifest:
        predecessor,previous,participants=successor_publication_context(db,candidate,manifest)
    elif candidate.resource_scope=='activity_report' and db.scalar(select(ReportRelease.id).where(ReportRelease.organization_id==org,ReportRelease.resource_scope=='activity_report',ReportRelease.report_key==candidate.report_key)):
        auth.fail('Yayımlanmış faaliyet raporu için tam ardıl soy bağı gerekir; assemble_activity_successor kullanın.',409)
    current=assignment(db,org)
    decision=db.scalar(select(ReportDecision).where(ReportDecision.candidate_id==candidate.id,ReportDecision.action=='final_approve').order_by(ReportDecision.id.desc()))
    if not current or not decision or decision.assignment_id!=current.id or decision.candidate_sha256!=candidate.sha256:auth.fail('Güncel nihai onaycı bu değişmemiş adayı yeniden onaylamalı.',409)
    with db.begin_nested():
        allowed(db,actor,'publish_report',org,state.state)
        pub=None;approval=None
        if candidate.resource_scope=='performance_program':
            db.scalar(select(ReportingPeriod).where(ReportingPeriod.id==candidate.period_id).with_for_update())
            number=(db.scalar(select(func.max(Publication.version)).where(Publication.period_id==candidate.period_id)) or 0)+1
            pub=Publication(period_id=candidate.period_id,version=number,snapshot_json=candidate.payload_json,
                sha256=candidate.payload_sha256,created_by=actor.id);db.add(pub);db.flush()
            definitions={row['id']:db.get(IndicatorDefinitionRevision,row['definition_revision_id']) for row in contract.snapshot_rows(json.loads(candidate.payload_json)).values()}
            contract.attach_publication_definitions(db,pub,definitions,actor)
        else:
            approval=db.get(ActivityReportApproval,decision.activity_approval_id)
            if not approval or approval.report_revision_id!=candidate.activity_revision_id:packages.conflict()
        event=event_notice(db,actor,candidate,'publish_report',state.state,'published',state.version+1)
        release=ReportRelease(candidate_id=candidate.id,final_decision_id=decision.id,organization_id=org,
            resource_scope=candidate.resource_scope,report_key=candidate.report_key,major=predecessor.major if predecessor else 1,minor=predecessor.minor+1 if predecessor else 0,
            publication_id=pub.id if pub else None,activity_approval_id=approval.id if approval else None,workflow_event_id=event.id)
        db.add(release);db.flush()
        release_version=f'{release.major}.{release.minor}'
        if predecessor:
            db.add(ReportReleaseSuccession(predecessor_release_id=predecessor.id,successor_release_id=release.id,
                predecessor_candidate_sha256=previous.sha256,successor_candidate_sha256=candidate.sha256,workflow_event_id=event.id))
            db.flush()
        raw=canonical({'release_id':release.id,'version':release_version,'candidate_sha256':candidate.sha256,
            'final_decision_id':decision.id,'payload':json.loads(candidate.payload_json),'manifest':json.loads(candidate.manifest_json),
            'publication_id':release.publication_id,'activity_approval_id':release.activity_approval_id})
        db.add(ReportArtifact(release_id=release.id,artifact_type='canonical_json',object_version='1.0',serialization_version='canonical-json-utf8-v1',
            content_json=raw,sha256=contract.digest(raw),byte_size=len(raw.encode('utf-8'))))
        db.flush();move(db,state,'published');verify_artifact(db,release)
        from . import revision_workflow_service as corrections
        for request,projection,grant in participants:
            context={'predecessor_release_id':predecessor.id,'successor_release_id':release.id,
                'successor_candidate_id':candidate.id,'successor_candidate_sha256':candidate.sha256,'correction_cycle_id':grant.cycle_id,
                'grant_id':grant.id,'from_state':'editing','to_state':'applied','version':projection.version+1}
            applied=corrections.history(db,actor,request,'revision_applied',context)
            db.add(RevisionRequestEvent(request_id=request.id,workflow_event_id=applied.id,from_state='editing',to_state='applied',version=projection.version+1));db.flush()
            changed=db.execute(update(RevisionRequestState).where(RevisionRequestState.request_id==request.id,RevisionRequestState.version==projection.version,RevisionRequestState.state=='editing').values(state='applied',version=projection.version+1))
            if changed.rowcount!=1:packages.conflict()
            db.refresh(projection)
            recipients=corrections.active_participants(db,request,grant)
            corrections.notify(db,request,'revision_applied',recipients)
    return release


def verify_artifact(db,release):
    if not release:packages.conflict()
    artifact=db.scalar(select(ReportArtifact).where(ReportArtifact.release_id==release.id))
    candidate=db.get(ReportCandidate,release.candidate_id)
    if not artifact or contract.digest(artifact.content_json)!=artifact.sha256 or len(artifact.content_json.encode('utf-8'))!=artifact.byte_size:packages.conflict()
    expected=canonical({'release_id':release.id,'version':f'{release.major}.{release.minor}','candidate_sha256':candidate.sha256,
        'final_decision_id':release.final_decision_id,'payload':json.loads(candidate.payload_json),'manifest':json.loads(candidate.manifest_json),
        'publication_id':release.publication_id,'activity_approval_id':release.activity_approval_id})
    if artifact.content_json!=expected or artifact.artifact_type!='canonical_json' or artifact.object_version!='1.0' or artifact.serialization_version!='canonical-json-utf8-v1':packages.conflict()
    manifest=json.loads(candidate.manifest_json)
    if 'predecessor_release_id' in manifest:
        lineage=db.scalar(select(ReportReleaseSuccession).where(ReportReleaseSuccession.successor_release_id==release.id))
        predecessor=db.get(ReportRelease,manifest['predecessor_release_id'])
        previous=db.get(ReportCandidate,predecessor.candidate_id) if predecessor else None
        if (not lineage or not previous or lineage.predecessor_release_id!=predecessor.id
            or lineage.predecessor_candidate_sha256!=previous.sha256 or lineage.successor_candidate_sha256!=candidate.sha256
            or lineage.workflow_event_id!=release.workflow_event_id or release.major!=predecessor.major or release.minor!=predecessor.minor+1):packages.conflict()
    return artifact


def candidate_detail(db,actor,org,candidate_id):
    candidate=db.get(ReportCandidate,candidate_id)
    if not candidate or candidate.organization_id!=org:auth.fail('Rapor adayı bu kuruma ait değil.')
    state=db.get(ReportCandidateState,candidate_id);allowed(db,actor,'view_candidate',org,state.state);verify(db,candidate)
    return {'candidate_id':candidate.id,'sha256':candidate.sha256,'state':state.state,'version':state.version,
        'payload':json.loads(candidate.payload_json),'manifest':json.loads(candidate.manifest_json)}
