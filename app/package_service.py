"""Disabled Phase 3 backend. No routes, CLI activation or live-row write-through.

Package content is a working copy derived from real scoped sources. Every edit
creates an immutable revision; decisions bind only that copy, never mutable rows.
Caller owns commit. All mutations, audit and mandatory notices share a savepoint.
"""
import json
from decimal import Decimal
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from . import authorization_service as auth
from .activity_contract_service import digest, parse_actual
from .models import (DirectoratePackage, PackageRevision, PackageDecision, ReportingPeriod,
    DirectorateMembership, User, ActivityReportRevision, ActivityReport, ActivityReportApproval,
    WorkflowEvent, Notification, NotificationRecipient, FieldChangeEvent, ReportIndicator,
    PublicationIndicatorBinding, IndicatorDefinitionRevision)

TRANSITIONS = {
    'submit_to_director': ('editable', 'director_review'),
    'director_approve': ('director_review', 'strategy_review'),
    'director_return': ('director_review', 'returned'),
    'director_reopen': ('director_review', 'returned'),
    'strategy_reopen': ('strategy_approved', 'returned'),
    'strategy_return': ('strategy_review', 'returned'),
    'strategy_approve': ('strategy_review', 'strategy_approved'),
}


def conflict():
    auth.fail('Paket sürümü veya içeriği değişti. Güncel paketi açıp işlemi yeniden yapın.', 409)


def revision(db, package):
    row = db.scalar(select(PackageRevision).where(PackageRevision.package_id == package.id,
        PackageRevision.revision == package.current_revision))
    if not row or digest(row.content_json) != row.sha256:
        auth.fail('Paket içeriğinin bütünlüğü doğrulanamadı. İşlemi durdurup yöneticinize bildirin.', 409)
    return row


def locked(db, actor, package_id, action, expected_version, expected_hash):
    package = db.get(DirectoratePackage, package_id)
    if not package:
        auth.fail('Müdürlük paketi bulunamadı.', 404)
    # Only published corrections acquire the organization lock, via current_source.
    # Resolve that context before the ordinary department/package/user lock path.
    from .revision_workflow_service import correction_context, require_correction_authority
    cycle=correction_context(db,package,validate_grant=False)
    # Same lock order as membership/delegation changes; refresh after waiting.
    auth.scope_department(db, package.organization_id, package.department_id, lock=True)
    package = db.scalar(select(DirectoratePackage).where(DirectoratePackage.id == package_id)
        .with_for_update().execution_options(populate_existing=True))
    user_ids = list(db.scalars(select(DirectorateMembership.user_id).where(
        DirectorateMembership.department_id == package.department_id, DirectorateMembership.active.is_(True))))
    user_ids.append(actor.id)
    list(db.scalars(select(User).where(User.id.in_(user_ids)).order_by(User.id).with_for_update()
        .execution_options(populate_existing=True)))
    if not auth.package_eligibility(db, actor, 'read_package', package):
        auth.fail('Bu müdürlüğün özel paketine erişim yetkiniz yok.')
    current = revision(db, package)
    if package.version != expected_version or current.sha256 != expected_hash:
        conflict()
    if not auth.package_eligibility(db, actor, action, package):
        auth.fail('Bu paket aşamasında seçilen işlemi yapmaya yetkiniz yok. Güncel aşamayı ve görevlendirmenizi kontrol edin.')
    if cycle:
        # Keep stale-version/authority checks ahead of correction authority as before.
        if action!='strategy_reopen':require_correction_authority(db,cycle,package)
        if action=='edit_draft':auth.fail('Yayımlanmış düzeltmeleri yalnız alan izni üzerinden düzenleyin.')
        return package,current
    if package.resource_scope == 'activity_report':
        source=db.get(ActivityReportRevision,package.report_revision_id)
        report=db.scalar(select(ActivityReport).where(ActivityReport.id==source.report_id).with_for_update().execution_options(populate_existing=True))
        if not report or report.current_revision!=source.revision or db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id==source.id)):
            auth.fail('Kaynak faaliyet raporu artık güncel veya düzenlenebilir değil. Güncel rapor revizyonu için yeni paket oluşturun.',409)
    else:
        period=db.scalar(select(ReportingPeriod).where(ReportingPeriod.id==package.period_id).with_for_update().execution_options(populate_existing=True))
        if not period or period.status in {'published','archived'}:
            auth.fail('Kaynak performans dönemi artık düzenlenebilir değil.',409)
    return package, current


def recipients(db, package, destination):
    members = db.scalars(select(DirectorateMembership).join(User, User.id == DirectorateMembership.user_id)
        .where(DirectorateMembership.department_id == package.department_id,
            DirectorateMembership.active.is_(True), User.is_active.is_(True))).all()
    if destination == 'strategy_review':
        result = set(db.scalars(select(User.id).where(User.role == 'strategy', User.is_active.is_(True))))
    elif destination == 'director_review':
        delegated = auth.active_delegation(db, package.organization_id, package.department_id)
        selected = [m for m in members if m.id == delegated.delegate_membership_id] if delegated else [m for m in members if m.role_code == 'department_director']
        result = {m.user_id for m in selected}
    else:
        result = {m.user_id for m in members}
    if not result:
        auth.fail('Zorunlu bildirim için aktif alıcı bulunamadı. Görevlendirmeleri kontrol edin.', 409)
    return result


def notice(db, package, event, destination):
    row = Notification(role='department', department_id=package.department_id,
        event_type=event.event_type, message=f'Müdürlük paketi #{package.id}: {destination}. {event.reason}'[:500],
        link='', delivery_mode='recipients')
    db.add(row); db.flush()
    for user_id in recipients(db, package, destination):
        db.add(NotificationRecipient(notification_id=row.id, user_id=user_id))
    db.flush()


def history_event(db, actor, package, action, context, reason=''):
    row = WorkflowEvent(actor_user_id=actor.id, actor_snapshot_json=auth.actor_snapshot(db, actor, package.organization_id),
        organization_id=package.organization_id, department_id=package.department_id,
        event_type=action, resource_type='directorate_package', resource_id=str(package.id),
        context_json=auth.encode(context), reason=reason, source='manual', correlation_id=str(uuid4()))
    db.add(row); db.flush()
    return row


def append_revision(db, package, actor, content_json, previous=None, reason=''):
    row = PackageRevision(package_id=package.id, revision=package.current_revision + (1 if previous else 0),
        previous_revision_id=previous.id if previous else None, content_json=content_json,
        sha256=digest(content_json), created_by=actor.id, reason=reason)
    db.add(row); db.flush()
    return row


def move(db, package, expected_version, state, current_revision):
    result = db.execute(update(DirectoratePackage).where(DirectoratePackage.id == package.id,
        DirectoratePackage.version == expected_version).values(state=state,
            current_revision=current_revision, version=expected_version + 1))
    if result.rowcount != 1:
        conflict()
    db.refresh(package)


def create_package(db, actor, organization_id, department_id, resource_scope, source_id):
    actor = auth.active_actor(db, actor)
    auth.scope_department(db, organization_id, department_id, lock=True)
    if actor.role != 'department' or actor.department_id != department_id or not auth.active_membership(db, actor.id, organization_id, department_id):
        auth.fail('Paket oluşturmak için müdürlüğün aktif görevlendirmesi gerekir.')
    if resource_scope == 'performance_program':
        period = db.get(ReportingPeriod, source_id)
        if not period or period.status in {'published','archived'}:
            auth.fail('Düzenlenebilir performans dönemi bulunamadı.',409)
        from .program_service import department_package_snapshot
        content = department_package_snapshot(db, period.id, department_id)
        period_id, report_revision_id = period.id, None
    elif resource_scope == 'activity_report':
        from .activity_contract_service import report_data
        source = db.get(ActivityReportRevision, source_id)
        report = db.get(ActivityReport, source.report_id) if source else None
        if not report or report.organization_id != organization_id or report.current_revision != source.revision or db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id == source.id)):
            auth.fail('Güncel, onaylanmamış faaliyet raporu revizyonunu seçin.',409)
        data = report_data(db, actor, source.id)
        content = {'publication_id': source.publication_id, 'publication_sha256': source.publication_sha256,
            'report_revision_id': source.id, 'entries': []}
        for item in data['indicators']:
            latest = item['actuals'][-1] if item['actuals'] else None
            content['entries'].append({'report_indicator_id': item['report_indicator_id'],
                'definition_revision_id': item['definition_revision_id'], 'definition': item['definition'],
                'source_actual_revision_id': latest['id'] if latest else None,
                'value': latest['value'] if latest else None, 'state': latest['state'] if latest else 'missing',
                'evidence': latest['evidence'] if latest else [], 'explanation': latest['explanation'] if latest else '',
                'deviation': latest['deviation'] if latest else {}})
        for entry in content['entries']:
            validate_actual(entry)
        if not content['entries']:
            auth.fail('Bu raporda müdürlüğünüze ait gösterge bulunamadı.',422)
        period_id, report_revision_id = report.period_id, source.id
    else:
        auth.fail('Paket türü tanınmıyor.',422)
    key = str(source_id)
    if db.scalar(select(DirectoratePackage.id).where(DirectoratePackage.department_id == department_id,
        DirectoratePackage.resource_scope == resource_scope, DirectoratePackage.source_key == key)):
        auth.fail('Bu kaynak için müdürlük paketi zaten var. Mevcut paketi açın.',409)
    with db.begin_nested():
        package = DirectoratePackage(organization_id=organization_id, department_id=department_id,
            resource_scope=resource_scope, source_key=key, period_id=period_id, report_revision_id=report_revision_id,
            state='draft', version=0, current_revision=1)
        db.add(package); db.flush()
        current = append_revision(db, package, actor, auth.encode(content))
        event = history_event(db, actor, package, 'package_created', {'revision_id':current.id,'sha256':current.sha256})
        notice(db, package, event, 'draft')
    return package


def validate_actual(entry):
    number = parse_actual(entry['value'])
    state, evidence = entry['state'], entry['evidence']
    if state not in {'verified','missing','needs_review'} or (state=='verified' and number is None) or (state=='missing' and number is not None):
        auth.fail('Gerçekleşme ve veri durumu uyumsuz. Veri yoksa Eksik seçip alanı boş bırakın; boş değer sıfır değildir.',422)
    if not isinstance(evidence,list) or len(evidence)>30 or any(not isinstance(s,dict) or not all(isinstance(s.get(k),str) and s[k].strip() for k in ('title','locator','source_revision')) for s in evidence):
        auth.fail('Kaynak adı, konumu ve sabit kaynak sürümünü doldurun.',422)
    if state=='verified' and not evidence:
        auth.fail('Doğrulanmış gerçekleşme için en az bir tam kaynak ekleyin veya İncelenmeli seçin.',422)
    if not isinstance(entry['explanation'],str) or not isinstance(entry['deviation'],dict):
        auth.fail('Açıklama metin, sapma kaydı bir nesne olmalı.',422)
    if len(auth.encode(evidence))>50000 or len(entry['explanation'])>10000 or len(auth.encode(entry['deviation']))>10000:
        auth.fail('Kanıt, açıklama veya sapma kaydı çok uzun.',422)
    target = entry['definition']['targets']
    target_value = Decimal(str(target[0]['value'])) if len(target)==1 and target[0].get('state')=='verified' and target[0].get('value') is not None else None
    entry['deviation'].update(calculation_rule_version='difference-v1', target_definition_revision_id=entry['definition_revision_id'],
        delta=str(number-target_value) if state=='verified' and target_value is not None else None, achievement_percent=None)


# ID, scope, publication bindings and definitions cannot be patched.
PROGRAM_FIELDS = {
    'cards': {'explanation','calculation_method','data_source','footnote','goal','rationale','responsible','service_area','strategic_link'},
    'indicators': {'name','unit','explanation','calculation_method','data_source','code'},
    'activities': {'name','explanation','code'},
    'department_costs': {'amount','raw_text','state'}, 'economics': {'amount'},
}


def apply_patch(content, scope, path, value):
    if not isinstance(path,list) or len(path)<3 or not isinstance(path[0],str) or not isinstance(path[-1],str) or any(type(part) not in {str,int} for part in path):
        auth.fail('Düzenlenecek alan yolu geçersiz.',422)
    section, index = path[:2]
    if type(index) is not int or index<0 or section not in content or not isinstance(content[section],list) or index>=len(content[section]):
        auth.fail('Paketin gösterge / alanı bulunamadı.',422)
    row = content[section][index]
    if scope=='activity_report':
        if section!='entries' or len(path)!=3 or path[2] not in {'value','state','evidence','explanation','deviation'}:
            auth.fail('Bu rapor alanı düzenlenemez.',422)
        row[path[2]]=value
    else:
        field = path[-1]
        if len(path)==5 and (section,path[2]) in {('indicators','values'),('activities','costs')}:
            subindex=path[3]
            if type(subindex) is not int or subindex<0 or subindex>=len(row[path[2]]):auth.fail('Hedef / bütçe satırı bulunamadı.',422)
            row=row[path[2]][subindex]
            allowed={'value','raw_text','state'} if section=='indicators' else {'amount','raw_text','state'}
        elif len(path)==3:
            allowed=PROGRAM_FIELDS.get(section,set())
        else:allowed=set()
        if field not in allowed:auth.fail('Kimlik / bağlam alanı düzenlenemez.',422)
        if field in {'value','amount'}:
            number=parse_actual(value)
            if field=='amount' and number is not None and (abs(number)>=Decimal('1e20') or number.as_tuple().exponent < -2):
                auth.fail('Bütçe için en fazla iki ondalık basamak girin.',422)
            row[field]=str(number) if number is not None else None
        else:
            if not isinstance(value,str) or len(value)>10000:auth.fail('Bu alan için en fazla 10.000 karakterlik metin girin.',422)
            row[field]=value
        if 'state' in row and row['state'] not in {'verified','needs_review','missing'}:auth.fail('Veri durumu tanınmıyor.',422)


def edit_package(db, actor, package_id, expected_version, expected_hash, patches, reason=''):
    package,current=locked(db,actor,package_id,'edit_draft',expected_version,expected_hash)
    if not isinstance(patches,list) or not patches or len(patches)>100:auth.fail('1–100 alan değişikliği gönderin.',422)
    try:auth.encode(patches)
    except (ValueError,TypeError):auth.fail('Sayısal alanları ondalık metin olarak gönderin; alan değerlerini kontrol edin.',422)
    member=auth.active_membership(db,actor.id,package.organization_id,package.department_id)
    if member.role_code=='department_director':reason=auth.required(reason,'Müdür düzeltme gerekçesi')
    before=json.loads(current.content_json); after=json.loads(current.content_json)
    # Batch patches are validated together (blank/state and value/evidence are atomic).
    for patch in patches:
        if not isinstance(patch,dict) or set(patch)!={'path','value'}:auth.fail('Alan yolu ve yeni değer gönderin.',422)
        apply_patch(after,package.resource_scope,patch['path'],patch['value'])
    if package.resource_scope=='activity_report':
        for entry in after['entries']:validate_actual(entry)
    else:
        for section in ('indicators','activities','department_costs'):
            for row in after.get(section,[]):
                cells=row.get('values',row.get('costs',[row]))
                for cell in cells:
                    if 'state' in cell:
                        number=cell.get('value',cell.get('amount'))
                        if (cell['state']=='missing' and number is not None) or (cell['state']=='verified' and number is None):
                            auth.fail('Boş değer sıfır değildir. Sayı ve veri durumunu birlikte düzeltin.',422)
    changes=[]
    def collect(old,new,path):
        if old==new:return
        if isinstance(old,dict) and isinstance(new,dict):
            for key in sorted(old.keys() | new.keys()):
                collect(old.get(key),new.get(key),path+[key])
        elif isinstance(old,list) and isinstance(new,list) and len(old)==len(new):
            for index,(left,right) in enumerate(zip(old,new)):
                collect(left,right,path+[index])
        else:
            changes.append({'field_key':'.'.join(str(k) for k in path),'field_type':'json', 'old':old,'new':new})
    for section,rows in after.items():
        if isinstance(rows,list):
            for index,row in enumerate(rows):collect(before[section][index],row,[section,index])
    if not changes:auth.fail('Kaydedilecek alan değişikliği yok.',422)
    def mutate():
        new=append_revision(db,package,actor,auth.encode(after),current,reason)
        move(db,package,expected_version,package.state,new.revision)
        return new
    result,event=auth.atomic_change(db,actor,package.organization_id,package.department_id,'directorate_package',package.id,
        {'previous_revision_id':current.id,'previous_sha256':current.sha256,'next_revision':current.revision+1,'next_sha256':digest(auth.encode(after))},
        changes,mutate,reason=reason,recipients=recipients(db,package,'draft'))
    return result


def transition(db, actor, package_id, action, expected_version, expected_hash, reason=''):
    if action not in TRANSITIONS:auth.fail('Paket işlemi tanınmıyor.',403)
    if action=='strategy_reopen':
        from .revision_workflow_service import correction_context
        target=db.get(DirectoratePackage,package_id)
        if not target:auth.fail('Paket bulunamadı.',404)
        cycle=correction_context(db,target,validate_grant=False)
        if not cycle:conflict()
        from .report_workflow_service import require_returned_attempt
        require_returned_attempt(db,cycle.source_release_id)
    package,current=locked(db,actor,package_id,action,expected_version,expected_hash)
    origin,destination=TRANSITIONS[action]
    if (origin=='editable' and package.state not in {'draft','returned'}) or (origin!='editable' and package.state!=origin):conflict()
    if action in {'director_return','director_reopen','strategy_return','strategy_reopen'}:reason=auth.required(reason,'Paket iade / düzeltme gerekçesi')
    content=json.loads(current.content_json)
    if action=='submit_to_director' and package.resource_scope=='activity_report':
        for entry in content['entries']:validate_actual(entry)
        # The submitted content must already include its canonical calculation.
        if auth.encode(content)!=current.content_json:conflict()
    if action in {'director_approve','strategy_approve'}:
        validate_package_approval(db,package,current)
    with db.begin_nested():
        decision_time=auth.server_now(db)
        if not auth.package_eligibility(db,actor,action,package,transition_time=decision_time):
            auth.fail('İşlem anındaki görevlendirme / vekâlet yetkiniz geçerli değil. Güncel yetkiyi kontrol edin.')
        delegation=auth.active_delegation(db,package.organization_id,package.department_id,at=decision_time) if action.startswith('director_') else None
        state_before=package.state
        from .revision_workflow_service import correction_context
        cycle=correction_context(db,package,validate_grant=action!='strategy_reopen')
        next_revision=current
        if destination=='returned' and not cycle:
            next_revision=append_revision(db,package,actor,current.content_json,current,reason)
        event=history_event(db,actor,package,action,{'revision_id':current.id,'sha256':current.sha256,
            'next_revision_id':None if cycle and destination=='returned' else next_revision.id,
            'next_revision':current.revision+1 if destination=='returned' else current.revision,'next_sha256':current.sha256,'from_state':state_before,'to_state':destination,
            'delegation_id':delegation.id if delegation else None,'decision_time':decision_time,
            'correction_cycle_id':cycle.id if cycle else None,'expected_version':expected_version,'returned_revision':current.revision+1 if cycle and destination=='returned' else None},reason)
        db.add(PackageDecision(package_revision_id=current.id,snapshot_sha256=current.sha256,action=action,
            from_state=state_before,to_state=destination,workflow_event_id=event.id,delegation_id=delegation.id if delegation else None))
        db.flush()
        if cycle and destination=='returned':
            next_revision=append_revision(db,package,actor,current.content_json,current,reason)
        move(db,package,expected_version,destination,next_revision.revision)
        notice(db,package,event,destination)
        db.flush()
    return package


def package_detail(db, actor, package_id):
    package=db.get(DirectoratePackage,package_id)
    if not package or not auth.package_eligibility(db,actor,'read_package',package):auth.fail('Bu müdürlüğün özel paketine erişim yetkiniz yok.')
    revisions=db.scalars(select(PackageRevision).where(PackageRevision.package_id==package.id).order_by(PackageRevision.revision)).all()
    if any(digest(r.content_json)!=r.sha256 for r in revisions):conflict()
    # Explicit actor snapshots expose Director edits to Strategy without a hidden role switch.
    events=db.scalars(select(WorkflowEvent).where(WorkflowEvent.resource_type=='directorate_package',WorkflowEvent.resource_id==str(package.id)).order_by(WorkflowEvent.id)).all()
    return {'id':package.id,'state':package.state,'version':package.version,'current_revision':package.current_revision,
        'revisions':[{'id':r.id,'revision':r.revision,'sha256':r.sha256,'content':json.loads(r.content_json),'previous_revision_id':r.previous_revision_id} for r in revisions],
        'events':[{'id':e.id,'action':e.event_type,'actor':json.loads(e.actor_snapshot_json),'context':json.loads(e.context_json),'reason':e.reason,
            'created_at':e.created_at.isoformat(),'changes':[{'field':c.field_key,'old':json.loads(c.previous_json),'new':json.loads(c.new_json)} for c in db.scalars(select(FieldChangeEvent).where(FieldChangeEvent.workflow_event_id==e.id))]} for e in events]}


def validate_package_approval(db, package, current):
    """Approve only exact immutable content; independent at both control layers."""
    if digest(current.content_json) != current.sha256:
        conflict()
    content = json.loads(current.content_json)
    if package.resource_scope == 'performance_program':
        from .program_service import validate_department_snapshot
        errors, _ = validate_department_snapshot(content,package.period_id,package.department_id)
        blockers = [{'field':'performance_program','message':error} for error in errors]
    elif package.resource_scope == 'activity_report':
        blockers = activity_package_approval_blockers(db,package,content)
    else:
        auth.fail('Paket türü tanınmıyor.',403)
    if blockers:
        auth.fail({'message':'Paket onaylanmadı. Aşağıdaki alanları düzeltip yeni revizyonu yeniden gönderin.',
            'package_id':package.id,'revision_id':current.id,'sha256':current.sha256,'blockers':blockers},409)


def activity_package_approval_blockers(db, package, content):
    # Read only immutable report bindings/definitions, never ActualRevision or live targets.
    expected = db.execute(select(ReportIndicator,PublicationIndicatorBinding,IndicatorDefinitionRevision)
        .join(PublicationIndicatorBinding,ReportIndicator.publication_binding_id==PublicationIndicatorBinding.id)
        .join(IndicatorDefinitionRevision,PublicationIndicatorBinding.definition_revision_id==IndicatorDefinitionRevision.id)
        .where(ReportIndicator.report_revision_id==package.report_revision_id,
            PublicationIndicatorBinding.department_id==package.department_id)).all()
    source=db.get(ActivityReportRevision,package.report_revision_id)
    if not source or content.get('report_revision_id')!=source.id or content.get('publication_id')!=source.publication_id or content.get('publication_sha256')!=source.publication_sha256:
        return [{'field':'publication','message':'Paketin sabit rapor / yayın bağlantısı uyuşmuyor. Doğru yayın sürümünden geçerli paket oluşturun.'}]
    definitions = {item.id:definition for item,binding,definition in expected}
    blockers=[]
    entries=content.get('entries')
    if not isinstance(entries,list) or not entries or any(not isinstance(e,dict) or type(e.get('report_indicator_id')) is not int for e in entries):
        return [{'field':'entries','message':'Müdürlüğün tüm zorunlu rapor göstergelerini içeren geçerli paket oluşturun.'}]
    ids=[e['report_indicator_id'] for e in entries]
    if len(ids)!=len(set(ids)) or set(ids)!=set(definitions):
        return [{'field':'entries','message':'Zorunlu göstergeler eksik, yinelenmiş veya kapsam dışı. Tüm bağlı göstergeleri içeren paket oluşturun.'}]
    for entry in entries:
        definition=definitions[entry['report_indicator_id']]
        frozen=json.loads(definition.definition_json)
        name=frozen.get('name',str(entry['report_indicator_id']))
        def block(message,field):
            blockers.append({'indicator':name,'report_indicator_id':entry['report_indicator_id'],'field':field,'message':message})
        if (digest(definition.definition_json)!=definition.sha256 or entry.get('definition_revision_id')!=definition.id or entry.get('definition')!=frozen):
            block('Sabit gösterge tanımı / hedef bağlantısı uyuşmuyor. Doğru yayın sürümünden geçerli paket oluşturun.','definition');continue
        try:
            copy=json.loads(auth.encode(entry))
            validate_actual(copy)  # existing numeric/evidence rules and recomputed difference-v1
            if copy['state']!='verified' or parse_actual(copy['value']) is None:
                block('Doğrulanmış sayısal gerçekleşme ve tam dayanak kaynağı girin. Boş değer sıfır değildir.','value/state')
            calculated=copy['deviation']
            stored=entry['deviation']
            keys=('calculation_rule_version','target_definition_revision_id','delta','achievement_percent')
            if any(stored.get(key)!=calculated[key] for key in keys):
                block('Hedef farkı sabit tanıma göre uyuşmuyor. Gerçekleşmeyi yeni revizyonda kaydedip farkı yeniden hesaplatın.','deviation')
            delta=calculated['delta']
            if delta is not None and Decimal(delta)!=0 and not copy['explanation'].strip():
                block('Hedef ile gerçekleşme farkını açıklayın.','explanation')
        except HTTPException as exc:
            block(str(exc.detail),'actual/evidence')
        except (KeyError,TypeError,ValueError,AttributeError):
            block('Gerçekleşme, kaynak ve sapma alanları eksik / geçersiz. Alanları kontrol edip yeni revizyon kaydedin.','actual/evidence')
    return blockers
