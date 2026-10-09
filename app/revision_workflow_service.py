"""Disabled Phase 5A internal correction seam. Caller owns outer commit."""
import json
from copy import deepcopy
from uuid import uuid4
from sqlalchemy import inspect, select, update
from .models import *
from . import authorization_service as auth, package_service as packages, report_workflow_service as reports


def current_source(db,release_id):
    if db.get_bind().dialect.name!='postgresql':auth.fail('Düzeltme iş akışı PostgreSQL güvenlik denetimleri gerektirir.',409)
    release=db.get(ReportRelease,release_id)
    if not release:auth.fail('Yayımlanmış rapor sürümü bulunamadı.',404)
    reports.organization_lock(db,release.organization_id)
    db.scalar(select(ReportRelease).where(ReportRelease.id==release.id).with_for_update())
    latest=db.scalar(select(ReportRelease.id).where(ReportRelease.organization_id==release.organization_id,
        ReportRelease.resource_scope==release.resource_scope,ReportRelease.report_key==release.report_key)
        .order_by(ReportRelease.major.desc(),ReportRelease.minor.desc(),ReportRelease.id.desc()))
    if latest!=release.id:auth.fail('Güncel yayın sürümü değişti. Yeni sürümü açıp yeni bir düzeltme talebi oluşturun; talep otomatik taşınmaz.',409)
    candidate=db.get(ReportCandidate,release.candidate_id)
    if db.get(ReportCandidateState,candidate.id).state!='published':packages.conflict()
    if not candidate or (release.organization_id,release.resource_scope,release.report_key)!=(candidate.organization_id,candidate.resource_scope,candidate.report_key):packages.conflict()
    decision=db.get(ReportDecision,release.final_decision_id)
    if not decision or decision.candidate_id!=candidate.id or decision.action!='final_approve' or decision.candidate_sha256!=candidate.sha256:packages.conflict()
    if release.resource_scope=='performance_program':
        publication=db.get(Publication,release.publication_id)
        if release.activity_approval_id or not publication or publication.period_id!=candidate.period_id or publication.snapshot_json!=candidate.payload_json or publication.sha256!=candidate.payload_sha256:packages.conflict()
    else:
        freeze=db.get(ActivityReportApproval,release.activity_approval_id)
        if release.publication_id or not freeze or freeze.report_revision_id!=candidate.activity_revision_id or decision.activity_approval_id!=freeze.id:packages.conflict()
    reports.verify(db,candidate);reports.verify_artifact(db,release)
    return release,candidate


def source_package(db,release,candidate,department_id):
    auth.scope_department(db,release.organization_id,department_id,lock=True)
    pairs=db.execute(select(DirectoratePackage,PackageRevision).join(PackageRevision,PackageRevision.package_id==DirectoratePackage.id)
        .join(CandidatePackage,CandidatePackage.package_revision_id==PackageRevision.id)
        .where(CandidatePackage.candidate_id==candidate.id,DirectoratePackage.department_id==department_id)).all()
    if len(pairs)!=1:auth.fail('Müdürlüğünüz bu yayımlanmış raporun paket kapsamında değil.',403)
    pkg,rev=pairs[0]
    pkg=db.scalar(select(DirectoratePackage).where(DirectoratePackage.id==pkg.id).with_for_update().execution_options(populate_existing=True))
    return pkg,rev


def member(db,actor,org,dep):
    actor=auth.active_actor(db,actor)
    if actor.role!='department':auth.fail('Talep/düzeltme için aktif müdürlük hesabı ve görevlendirmesi gerekir.')
    m=auth.active_membership(db,actor.id,org,dep)
    if not m or m.role_code not in {'department_editor','department_director'}:auth.fail('Müdürlüğün aktif veri girişçisi veya müdürü görevlendirmesi gerekir.')
    return m


def strategy(db,actor):
    actor=auth.active_actor(db,actor)
    if actor.role!='strategy':auth.fail('Bu talep işlemini Strateji yapmalıdır.')


def fields(content,scope,patches,proposals=True):
    if not isinstance(patches,list) or not 1<=len(patches)<=100:auth.fail('1–100 geçerli alan belirtin.',422)
    result=[];seen=set()
    for patch in patches:
        if not isinstance(patch,dict) or set(patch)-{'path','value'} or 'path' not in patch:auth.fail('Alan yolu ve varsa önerilen değeri belirtin.',422)
        path=patch['path'];copy=deepcopy(content)
        # Resolve the exact frozen address, then run the existing edit allowlist.
        try:
            old=copy
            for key in path:old=old[key]
            packages.apply_patch(copy,scope,path,patch.get('value',deepcopy(old)))
            encoded=auth.encode(path);auth.encode(patch)
        except (TypeError,KeyError,IndexError,ValueError):auth.fail('Alan yolu/değeri geçersiz veya kaynak pakette yok.',422)
        if encoded in seen:auth.fail('Aynı alanı iki kez talep etmeyin.',422)
        seen.add(encoded);result.append(deepcopy(patch) if proposals else path)
    return sorted(result,key=lambda p:auth.encode(p['path'] if proposals else p))


def paths(request):return [p['path'] for p in json.loads(request.patches_json)]


def notify(db,request,action,ids):
    if not ids:auth.fail('Zorunlu iç bildirim alıcısı bulunamadı.',409)
    n=Notification(role='department',department_id=request.department_id,event_type=action,
        message=f'Düzeltme talebi #{request.id}: {action}',link='',delivery_mode='recipients')
    db.add(n);db.flush()
    for uid in sorted(ids):db.add(NotificationRecipient(notification_id=n.id,user_id=uid))
    db.flush()


def director_recipients(db,request):
    ids=set(db.scalars(select(User.id).join(DirectorateMembership,DirectorateMembership.user_id==User.id).where(
        DirectorateMembership.department_id==request.department_id,DirectorateMembership.organization_id==request.organization_id,
        DirectorateMembership.active.is_(True),DirectorateMembership.role_code=='department_director',User.is_active.is_(True))))
    if not ids:auth.fail('Zorunlu bildirim için aktif müdür görevlendirmesini kontrol edin.',409)
    ids.add(request.requester_user_id);return ids


def history(db,actor,request,action,context,reason=''):
    e=WorkflowEvent(actor_user_id=actor.id,actor_snapshot_json=auth.actor_snapshot(db,actor,request.organization_id),
        organization_id=request.organization_id,department_id=request.department_id,event_type=action,
        resource_type='revision_request',resource_id=str(request.id),context_json=auth.encode(dict(context,request_id=request.id,
        source_release_id=request.source_release_id)),reason=reason,source='manual',correlation_id=str(uuid4()))
    db.add(e);db.flush();return e


def transition(db,actor,request,state,to_state,reason=''):
    e=history(db,actor,request,'revision_'+to_state,{'from_state':state.state,'to_state':to_state,'version':state.version+1},reason)
    db.add(RevisionRequestEvent(request_id=request.id,workflow_event_id=e.id,from_state=state.state,to_state=to_state,version=state.version+1));db.flush()
    result=db.execute(update(RevisionRequestState).where(RevisionRequestState.request_id==request.id,
        RevisionRequestState.version==state.version).values(state=to_state,version=state.version+1))
    if result.rowcount!=1:packages.conflict()
    db.refresh(state)


def create_request(db,actor,source_release_id,department_id,patches,reason,evidence=None):
    release,candidate=current_source(db,source_release_id);m=member(db,actor,release.organization_id,department_id)
    pkg,rev=source_package(db,release,candidate,department_id)
    reason=auth.required(reason,'Düzeltme talebi gerekçesi');patches=fields(json.loads(rev.content_json),pkg.resource_scope,patches)
    try:ev=auth.encode(evidence if evidence is not None else [])
    except (TypeError,ValueError):auth.fail('Kanıt/kaynak bilgilerini geçerli JSON olarak belirtin.',422)
    if len(ev)>50000:auth.fail('Kanıt/kaynak bilgisi çok uzun.',422)
    with db.begin_nested():
        m=member(db,actor,release.organization_id,department_id)
        r=RevisionRequest(source_release_id=release.id,organization_id=release.organization_id,department_id=department_id,
            requester_user_id=actor.id,requester_membership_id=m.id,source_package_revision_id=rev.id,
            patches_json=auth.encode(patches),reason=reason,evidence_json=ev)
        db.add(r);db.flush();db.add(RevisionRequestState(request_id=r.id,state='requested',version=0));db.flush()
        e=history(db,actor,r,'revision_requested',{'version':0},reason)
        db.add(RevisionRequestEvent(request_id=r.id,workflow_event_id=e.id,from_state='',to_state='requested',version=0))
        notify(db,r,'revision_requested',set(db.scalars(select(User.id).where(User.role=='strategy',User.is_active.is_(True)))))
    return r


def locked(db,actor,request_id,expected_version=None,current=True):
    r=db.get(RevisionRequest,request_id)
    if not r:auth.fail('Düzeltme talebi bulunamadı.',404)
    reports.organization_lock(db,r.organization_id)
    auth.scope_department(db,r.organization_id,r.department_id,lock=True)
    db.scalar(select(User).where(User.id==actor.id).with_for_update().execution_options(populate_existing=True));auth.active_actor(db,actor)
    if current:
        release,candidate=current_source(db,r.source_release_id);pkg,rev=source_package(db,release,candidate,r.department_id)
        if rev.id!=r.source_package_revision_id:packages.conflict()
        fields(json.loads(rev.content_json),pkg.resource_scope,json.loads(r.patches_json))
    state=db.scalar(select(RevisionRequestState).where(RevisionRequestState.request_id==r.id).with_for_update().execution_options(populate_existing=True))
    if expected_version is not None and state.version!=expected_version:packages.conflict()
    return r,state


def decide_request(db,actor,request_id,action,expected_version,reason=''):
    if action not in {'accept','reject','cancel'}:auth.fail('Talep işlemi tanınmıyor.')
    r,state=locked(db,actor,request_id,expected_version,current=action=='accept')
    if action=='cancel':
        if actor.id!=r.requester_user_id:auth.fail('Talebi yalnız talep sahibi iptal edebilir.')
        member(db,actor,r.organization_id,r.department_id);reason=auth.required(reason,'İptal gerekçesi')
    else:
        strategy(db,actor)
        if action=='reject':reason=auth.required(reason,'Ret gerekçesi')
    if state.state!='requested':auth.fail('Talep artık karar beklemiyor; güncel durumu açın.',409)
    if action=='accept':
        others=db.scalars(select(RevisionRequest).join(RevisionRequestState,RevisionRequestState.request_id==RevisionRequest.id).where(
            RevisionRequest.source_release_id==r.source_release_id,RevisionRequest.department_id==r.department_id,
            RevisionRequestState.state.in_(['accepted','editing']))).all()
        if any(set(map(auth.encode,paths(r))) & set(map(auth.encode,paths(other))) for other in others):auth.fail('Bu alan için kabul edilmiş/açık düzeltme var. Çakışan alanı çıkarın veya mevcut talebi inceleyin.',409)
    with db.begin_nested():
        transition(db,actor,r,state,{'accept':'accepted','reject':'rejected','cancel':'cancelled'}[action],reason)
        if action!='cancel':notify(db,r,'revision_'+action,director_recipients(db,r))
    return r


def active_participants(db,request,grant=None):
    """Mandatory recipients are active participants; a director is not required."""
    ids=set(db.scalars(select(User.id).join(DirectorateMembership,DirectorateMembership.user_id==User.id).where(
        DirectorateMembership.organization_id==request.organization_id,DirectorateMembership.department_id==request.department_id,
        DirectorateMembership.active.is_(True),User.is_active.is_(True))))
    if db.scalar(select(User.id).where(User.id==request.requester_user_id,User.is_active.is_(True))):ids.add(request.requester_user_id)
    if grant:
        ids.update(db.scalars(select(DirectorateMembership.user_id).join(User,User.id==DirectorateMembership.user_id).where(
            DirectorateMembership.id.in_(json.loads(grant.membership_ids_json)),DirectorateMembership.active.is_(True),User.is_active.is_(True))))
    return ids


def close_no_change(db,actor,request_id,expected_version,reason):
    """Explicit Strategy resolution; never reuse requester cancellation or stale."""
    request,state=locked(db,actor,request_id,expected_version);strategy(db,actor)
    reason=auth.required(reason,'Değişikliksiz kapatma gerekçesi')
    if state.state not in {'accepted','editing'}:auth.fail('Yalnız kabul edilmiş veya düzenlenen talep değişikliksiz kapatılabilir.',409)
    with db.begin_nested():
        transition(db,actor,request,state,'closed_no_change',reason)
        notify(db,request,'revision_closed_no_change',active_participants(db,request))
    return request


def value_at(content,path):
    value=content
    try:
        for part in path:value=value[part]
    except (KeyError,IndexError,TypeError):return None
    return value


def net_changed(before,after,path):
    old=value_at(before,path);new=value_at(after,path)
    if len(path)==3 and path[0]=='entries' and path[2]=='value':
        # Equivalent decimal spellings are not a real changed actual. Preserve
        # blank/null versus zero; do not coerce missing values into zero.
        return packages.parse_actual(old)!=packages.parse_actual(new)
    return old!=new


def has_net_correction(db,request,grant,cycle,bound):
    """A granted business path must change net AND have this grant's edit proof."""
    source=db.get(PackageRevision,cycle.source_package_revision_id)
    before=json.loads(source.content_json);after=json.loads(bound.content_json)
    paths=[p for p in json.loads(grant.paths_json) if 'deviation' not in p and net_changed(before,after,p)]
    if not paths:return False
    lineage={};row=bound
    while row and row.id!=cycle.opening_revision_id:
        if row.id in lineage or row.package_id!=cycle.package_id:packages.conflict()
        lineage[row.id]=row;row=db.get(PackageRevision,row.previous_revision_id)
    if not row or row.previous_revision_id!=source.id:packages.conflict()
    changes=db.execute(select(WorkflowEvent,FieldChangeEvent).join(FieldChangeEvent,FieldChangeEvent.workflow_event_id==WorkflowEvent.id)
        .where(WorkflowEvent.event_type=='correction_edit',WorkflowEvent.resource_type=='revision_request',WorkflowEvent.resource_id==str(request.id),
            WorkflowEvent.organization_id==request.organization_id,WorkflowEvent.department_id==request.department_id,
            FieldChangeEvent.revision_request_id==request.id)).all()
    for event,change in changes:
        context=json.loads(event.context_json);path=json.loads(change.field_key)
        if not any(path[:len(p)]==p for p in paths) or 'deviation' in path or not net_changed(before,after,path) or context.get('grant_id')!=grant.id or context.get('package_id')!=cycle.package_id:continue
        if context.get('request_id')!=request.id or context.get('source_release_id')!=request.source_release_id:continue
        for revision in lineage.values():
            if (revision.previous_revision_id!=context.get('previous_revision_id') or revision.revision!=context.get('next_revision')
                or revision.sha256!=context.get('next_sha256')):continue
            membership=db.get(DirectorateMembership,context.get('membership_id'))
            if (event.actor_user_id!=revision.created_by or event.created_at>revision.created_at
                or not membership or membership.id not in json.loads(grant.membership_ids_json)
                or membership.user_id!=event.actor_user_id or membership.organization_id!=request.organization_id
                or membership.department_id!=request.department_id):continue
            prior=db.get(PackageRevision,revision.previous_revision_id)
            old=json.loads(change.previous_json);new=json.loads(change.new_json)
            if old!=new and old==value_at(json.loads(prior.content_json),path) and new==value_at(json.loads(revision.content_json),path):return True
    return False


def open_grant(db,actor,request_id,expected_version,allowlist,membership_ids,start_at,end_at,formal_basis):
    r,state=locked(db,actor,request_id,expected_version);strategy(db,actor)
    if state.state!='accepted':auth.fail('Düzenleme izni için önce talebi kabul edin.',409)
    if (not allowlist or len({auth.encode(p) for p in allowlist})!=len(allowlist)
        or not set(map(auth.encode,allowlist))<=set(map(auth.encode,paths(r)))):auth.fail('İzin yalnız talep edilen alanları veya bir alt kümesini kapsayabilir.',422)
    if not membership_ids or len(set(membership_ids))!=len(membership_ids):auth.fail('Aktif müdürlük görevlendirmelerini seçin.',422)
    members=list(db.scalars(select(DirectorateMembership).where(DirectorateMembership.id.in_(membership_ids)).with_for_update().execution_options(populate_existing=True)))
    if len(members)!=len(membership_ids) or any(not m.active or m.organization_id!=r.organization_id or m.department_id!=r.department_id or m.role_code not in {'department_editor','department_director'} or not db.get(User,m.user_id).is_active for m in members):auth.fail('İzin alıcıları aynı müdürlüğün aktif görevlendirmeleri olmalıdır.',422)
    if start_at.tzinfo is None or end_at.tzinfo is None or start_at>=end_at:auth.fail('Saat dilimiyle geçerli izin başlangıcı/bitişi belirtin.',422)
    basis=auth.required(formal_basis,'İzin dayanağı')
    source=db.get(PackageRevision,r.source_package_revision_id);pkg=db.get(DirectoratePackage,source.package_id)
    with db.begin_nested():
        cycle=db.scalar(select(RevisionCorrectionCycle).where(RevisionCorrectionCycle.source_release_id==r.source_release_id,RevisionCorrectionCycle.package_id==pkg.id))
        if not cycle:
            if pkg.current_revision!=source.revision or pkg.state!='strategy_approved':auth.fail('Paketin güncel düzeltme dalı uyuşmuyor; işlem durduruldu.',409)
            e=history(db,actor,r,'correction_opened',{'package_id':pkg.id,'source_package_revision_id':source.id},basis)
            new=packages.append_revision(db,pkg,actor,source.content_json,source,basis)
            packages.move(db,pkg,pkg.version,'returned',new.revision)
            cycle=RevisionCorrectionCycle(source_release_id=r.source_release_id,package_id=pkg.id,source_package_revision_id=source.id,
                opening_revision_id=new.id,workflow_event_id=e.id);db.add(cycle);db.flush()
        elif pkg.state!='returned':auth.fail('Düzeltme paketi artık düzenlenebilir aşamada değil.',409)
        grant=RevisionEditGrant(request_id=r.id,source_release_id=r.source_release_id,department_id=r.department_id,cycle_id=cycle.id,
            membership_ids_json=auth.encode(sorted(membership_ids)),paths_json=auth.encode(sorted(allowlist,key=auth.encode)),
            start_at=start_at,end_at=end_at,created_by=actor.id,formal_basis=basis)
        db.add(grant);db.flush();transition(db,actor,r,state,'editing',basis)
        notify(db,r,'revision_granted',{m.user_id for m in members}|director_recipients(db,r))
    return grant


def edit_under_grant(db,actor,grant_id,expected_version,expected_hash,patches,reason=''):
    grant=db.get(RevisionEditGrant,grant_id)
    if not grant:auth.fail('Düzeltme izni bulunamadı.',403)
    r,state=locked(db,actor,grant.request_id);cycle=db.get(RevisionCorrectionCycle,grant.cycle_id)
    pkg=db.get(DirectoratePackage,cycle.package_id);m=member(db,actor,r.organization_id,r.department_id)
    db.scalar(select(DirectorateMembership).where(DirectorateMembership.id==m.id).with_for_update().execution_options(populate_existing=True))
    now=auth.server_now(db)
    if state.state!='editing' or not m.active or m.id not in json.loads(grant.membership_ids_json) or not grant.start_at<=now<grant.end_at:auth.fail('Düzenleme izni henüz başlamadı, sona erdi veya görevlendirmeniz kapsam dışında. Stratejiyle izin durumunu kontrol edin.')
    current=packages.revision(db,pkg)
    if pkg.state!='returned' or pkg.version!=expected_version or current.sha256!=expected_hash:packages.conflict()
    validated=fields(json.loads(current.content_json),pkg.resource_scope,patches)
    if any('value' not in p for p in validated) or not set(auth.encode(p['path']) for p in validated)<=set(map(auth.encode,json.loads(grant.paths_json))):auth.fail('Yalnız bu izinde belirtilen alanları düzenleyebilirsiniz.',403)
    if m.role_code=='department_director':reason=auth.required(reason,'Müdür düzeltme gerekçesi')
    before=json.loads(current.content_json);after=deepcopy(before)
    for patch in validated:packages.apply_patch(after,pkg.resource_scope,patch['path'],patch['value'])
    if pkg.resource_scope=='activity_report':
        for entry in after['entries']:
            number=packages.parse_actual(entry['value']);entry['value']=str(number) if number is not None else None
            packages.validate_actual(entry)
    else:
        for section in ('indicators','activities','department_costs'):
            for row in after.get(section,[]):
                for cell in row.get('values',row.get('costs',[row])):
                    if 'state' in cell:
                        number=cell.get('value',cell.get('amount'))
                        if (cell['state']=='missing' and number is not None) or (cell['state']=='verified' and number is None):auth.fail('Boş değer sıfır değildir. Sayı ve veri durumunu birlikte düzeltin.',422)
    changes=[]
    def collect(old,new,path):
        if old==new:return
        if isinstance(old,dict) and isinstance(new,dict):
            for key in sorted(old.keys()|new.keys()):collect(old.get(key),new.get(key),path+[key])
        elif isinstance(old,list) and isinstance(new,list) and len(old)==len(new):
            for index,(left,right) in enumerate(zip(old,new)):collect(left,right,path+[index])
        else:changes.append((path,old,new))
    collect(before,after,[])
    if not changes:auth.fail('Kaydedilecek alan değişikliği yok.',422)
    raw=auth.encode(after)
    with db.begin_nested():
        e=history(db,actor,r,'correction_edit',{'grant_id':grant.id,'membership_id':m.id,'package_id':pkg.id,
            'previous_revision_id':current.id,'next_revision':pkg.current_revision+1,'next_sha256':packages.digest(raw)},reason)
        for path,old,new in changes:
            db.add(FieldChangeEvent(workflow_event_id=e.id,revision_request_id=r.id,field_key=auth.encode(path),field_type='json',previous_json=auth.encode(old),new_json=auth.encode(new)))
        db.flush()
        new=packages.append_revision(db,pkg,actor,raw,current,reason);packages.move(db,pkg,expected_version,'returned',new.revision)
    return new


def correction_context(db,package,*,validate_grant=True):
    """Select an explicit current release cycle; never relax ordinary source gates."""
    # Older populated checkpoints have no correction seam; ordinary source gates
    # still apply. Never catch a failed authorization/integrity query as a fallback.
    if not inspect(db.connection()).has_table('revision_correction_cycles'):return None
    if not db.scalar(select(RevisionCorrectionCycle.id).where(RevisionCorrectionCycle.package_id==package.id).limit(1)):return None
    # Historical cycles establish correction scope, never authorization. Resolve
    # this package's report key before selecting a cycle under the org lock.
    reports.organization_lock(db,package.organization_id)
    if package.resource_scope=='activity_report':
        source=db.get(ActivityReportRevision,package.report_revision_id)
        if not source:packages.conflict()
        report_key=str(source.report_id)
    else:report_key=str(package.period_id)
    release_id=db.scalar(select(ReportRelease.id).where(ReportRelease.organization_id==package.organization_id,
        ReportRelease.resource_scope==package.resource_scope,ReportRelease.report_key==report_key)
        .order_by(ReportRelease.major.desc(),ReportRelease.minor.desc(),ReportRelease.id.desc()))
    if not release_id or not db.get(ReportRelease,release_id):packages.conflict()
    release,candidate=current_source(db,release_id)
    cycle=db.scalar(select(RevisionCorrectionCycle).where(RevisionCorrectionCycle.source_release_id==release.id,
        RevisionCorrectionCycle.package_id==package.id))
    if not cycle:auth.fail('Paket yayımlandı; güncel sürüm için yeni düzeltme talebi açın.',409)
    bound=db.scalar(select(CandidatePackage).where(CandidatePackage.candidate_id==candidate.id,
        CandidatePackage.package_revision_id==cycle.source_package_revision_id))
    if not bound:packages.conflict()
    if validate_grant:require_correction_grant(db,cycle)
    return cycle


def require_correction_grant(db,cycle):
    """Recheck grant time without reacquiring the correction organization lock."""
    now=auth.server_now(db)
    grants=db.scalars(select(RevisionEditGrant).join(RevisionRequestState,RevisionRequestState.request_id==RevisionEditGrant.request_id)
        .where(RevisionEditGrant.cycle_id==cycle.id,RevisionRequestState.state=='editing',
            RevisionEditGrant.start_at<=now,RevisionEditGrant.end_at>now)).all()
    if not grants:auth.fail('Düzeltme izni etkin değil. Stratejiden güncel alan iznini kontrol etmesini isteyin.',409)
