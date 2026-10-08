"""Disabled Phase 4 internal backend; callers own commit, no runtime routes."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
import json
from uuid import uuid4
from sqlalchemy import select, update, func
from .models import *
from . import authorization_service as auth, package_service as packages, activity_contract_service as contract
from .program_service import record


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
    if contract.digest(candidate.payload_json)!=candidate.payload_sha256 or hash_content(candidate.payload_json,candidate.manifest_json)!=candidate.sha256:packages.conflict()
    manifest=json.loads(candidate.manifest_json)
    bindings=db.scalars(select(CandidatePackage).where(CandidatePackage.candidate_id==candidate.id).order_by(CandidatePackage.id)).all()
    if len(bindings)!=len(manifest['packages']):packages.conflict()
    sources=[];departments=set()
    for binding,expected in zip(bindings,manifest['packages']):
        rev=db.get(PackageRevision,binding.package_revision_id);pkg=db.get(DirectoratePackage,rev.package_id)
        decision=db.get(PackageDecision,binding.strategy_decision_id)
        if (binding.package_revision_id!=expected['revision_id'] or binding.strategy_decision_id!=expected['decision_id']
            or binding.sha256!=expected['sha256'] or rev.sha256!=binding.sha256 or contract.digest(rev.content_json)!=rev.sha256
            or decision.action!='strategy_approve' or decision.package_revision_id!=rev.id or decision.snapshot_sha256!=rev.sha256
            or pkg.organization_id!=candidate.organization_id or pkg.period_id!=candidate.period_id or pkg.resource_scope!=candidate.resource_scope
            or pkg.state!='strategy_approved' or pkg.current_revision!=rev.revision):packages.conflict()
        if expected['package_id']!=pkg.id or expected['department_id']!=pkg.department_id or expected['strategy_event_id']!=decision.workflow_event_id or pkg.department_id in departments:packages.conflict()
        departments.add(pkg.department_id);sources.append(json.loads(rev.content_json))
        packages.validate_package_approval(db,pkg,rev)
    if sorted(departments)!=manifest['required_department_ids']:packages.conflict()
    assembled=json.loads(candidate.payload_json)
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
        current=[{k:v for k,v in e.items() if k not in {'materialized_report_indicator_id','materialized_actual_revision_id'}} for e in assembled['entries']]
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


def materialize(db,actor,source,contents):
    report=db.scalar(select(ActivityReport).where(ActivityReport.id==source.report_id).with_for_update().execution_options(populate_existing=True))
    new=ActivityReportRevision(report_id=report.id,revision=report.current_revision+1,publication_id=source.publication_id,
        publication_sha256=source.publication_sha256,contract_version=source.contract_version,previous_revision_id=db.scalar(select(ActivityReportRevision.id).where(ActivityReportRevision.report_id==report.id,ActivityReportRevision.revision==report.current_revision)),
        diff_json='[]',revision_reason='Onaylı müdürlük paketlerinden nihai rapor adayı oluşturuldu.',created_by=actor.id)
    db.add(new);db.flush();report.current_revision=new.revision;report.lock_version+=1;db.flush()
    entries=[]
    for content in contents:
        for entry in content['entries']:
            old=db.get(ReportIndicator,entry['report_indicator_id'])
            ri=ReportIndicator(report_revision_id=new.id,publication_binding_id=old.publication_binding_id);db.add(ri);db.flush()
            actual=ActualRevision(report_indicator_id=ri.id,revision=1,supersedes_id=None,value=contract.parse_actual(entry['value']),
                raw_text=entry['value'] or '',state=entry['state'],evidence_json=canonical(entry['evidence']),
                explanation=entry['explanation'],deviation_json=canonical(entry['deviation']),created_by=actor.id)
            db.add(actual);db.flush()
            entries.append(dict(entry,materialized_report_indicator_id=ri.id,materialized_actual_revision_id=actual.id))
    return new,{'schema_version':'activity-candidate-1','report_revision_id':new.id,'publication_id':source.publication_id,
        'publication_sha256':source.publication_sha256,'contract_version':source.contract_version,'entries':entries}


def verify_materialization(db,candidate):
    payload=json.loads(candidate.payload_json);revision=db.get(ActivityReportRevision,candidate.activity_revision_id)
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
        required=set(db.scalars(select(PublicationIndicatorBinding.department_id).join(ReportIndicator,ReportIndicator.publication_binding_id==PublicationIndicatorBinding.id).where(ReportIndicator.report_revision_id==source.id)))
    else:auth.fail('Rapor türü tanınmıyor.',403)
    if not period or not required:auth.fail('Geçerli dönem ve zorunlu müdürlük kapsamı bulunamadı.',409)
    previous=db.scalar(select(ReportCandidate).where(ReportCandidate.organization_id==organization_id,ReportCandidate.resource_scope==resource_scope,ReportCandidate.report_key==key).order_by(ReportCandidate.sequence.desc()))
    if (previous.id if previous else None)!=predecessor_candidate_id:packages.conflict()
    if previous and db.get(ReportCandidateState,previous.id).state!='returned_to_strategy':auth.fail('Mevcut aday sonuçlanmadan yeni aday oluşturulamaz.',409)
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
            new,payload=materialize(db,actor,source,contents);activity_revision_id=new.id
        else:payload=program_payload(db,actor,period,contents);activity_revision_id=None
        manifest={'version':'report-manifest-1','organization_id':organization_id,'period_id':period.id,'resource_scope':resource_scope,
            'source_id':source_id,'required_department_ids':sorted(required),'packages':[{'package_id':p.id,'department_id':p.department_id,
                'revision_id':r.id,'sha256':r.sha256,'decision_id':d.id,'strategy_event_id':d.workflow_event_id} for p,r,d in selected]}
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
    if state.state=='final_approved' and db.scalar(select(ReportDecision.id).where(ReportDecision.candidate_id==candidate.id,ReportDecision.action=='final_approve',ReportDecision.assignment_id==current.id)):auth.fail('Bu yetkili aynı adayı zaten onayladı.',409)
    with db.begin_nested():
        allowed(db,actor,action,org,state.state)
        approval=None
        if action=='final_approve' and candidate.activity_revision_id:
            approval=db.scalar(select(ActivityReportApproval).where(ActivityReportApproval.report_revision_id==candidate.activity_revision_id))
            if not approval:
                approval=ActivityReportApproval(report_revision_id=candidate.activity_revision_id,created_by=actor.id);db.add(approval);db.flush()
        destination='final_approved' if action=='final_approve' else 'returned_to_strategy'
        event=event_notice(db,actor,candidate,action,state.state,destination,state.version+1,reason)
        decision=ReportDecision(candidate_id=candidate.id,action=action,candidate_sha256=candidate.sha256,
            assignment_id=current.id,workflow_event_id=event.id,activity_approval_id=approval.id if approval else None)
        db.add(decision);db.flush();move(db,state,destination)
    return decision


def publish(db,actor,org,candidate_id,version,sha):
    candidate,state=locked(db,actor,org,candidate_id,'publish_report',version,sha)
    if state.state=='published':
        release=db.scalar(select(ReportRelease).where(ReportRelease.candidate_id==candidate.id));verify_artifact(db,release);return release
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
            resource_scope=candidate.resource_scope,report_key=candidate.report_key,major=1,minor=0,
            publication_id=pub.id if pub else None,activity_approval_id=approval.id if approval else None,workflow_event_id=event.id)
        db.add(release);db.flush()
        raw=canonical({'release_id':release.id,'version':'1.0','candidate_sha256':candidate.sha256,
            'final_decision_id':decision.id,'payload':json.loads(candidate.payload_json),'manifest':json.loads(candidate.manifest_json),
            'publication_id':release.publication_id,'activity_approval_id':release.activity_approval_id})
        db.add(ReportArtifact(release_id=release.id,artifact_type='canonical_json',object_version='1.0',serialization_version='canonical-json-utf8-v1',
            content_json=raw,sha256=contract.digest(raw),byte_size=len(raw.encode('utf-8'))))
        db.flush();move(db,state,'published');verify_artifact(db,release)
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
    return artifact


def candidate_detail(db,actor,org,candidate_id):
    candidate=db.get(ReportCandidate,candidate_id)
    if not candidate or candidate.organization_id!=org:auth.fail('Rapor adayı bu kuruma ait değil.')
    state=db.get(ReportCandidateState,candidate_id);allowed(db,actor,'view_candidate',org,state.state);verify(db,candidate)
    return {'candidate_id':candidate.id,'sha256':candidate.sha256,'state':state.state,'version':state.version,
        'payload':json.loads(candidate.payload_json),'manifest':json.loads(candidate.manifest_json)}
