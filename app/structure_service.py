"""CIV-027: append-only decisions, period names and explicit work routing.

All mutations are synchronous. Callers read request bodies before acquiring locks.
"""
import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from .models import (Activity, ActivityCatalogueLink, ActivityResponsibility, AuditLog,
    Department, DepartmentScope, Indicator, OfficialActivity, Organization, ReportCard,
    ReportingPeriod, ReportSection, StructureChange, StructureChangeCancellation, StructureChangeLink,
    StructureChangeTransfer, Submission)
from .master_data_service import audit_change, check_department_name, name_value

KINDS = {'RENAMED': 'Ad değişikliği', 'MERGED': 'Birleşme', 'SPLIT': 'Bölünme', 'CLOSED': 'Kapanış', 'CREATED': 'Yeni müdürlük'}
JOURNAL = (StructureChange, StructureChangeLink, StructureChangeTransfer, StructureChangeCancellation)
PROFILE_FIELDS = ('display_name', 'status', 'reason', 'budget_code', 'active_from', 'active_to')


@event.listens_for(Session, 'before_flush')
def immutable_decisions(db, context, instances):
    for row in list(db.dirty) + list(db.deleted):
        if isinstance(row, JOURNAL) and (row in db.deleted or db.is_modified(row)):
            raise HTTPException(409, f'Kurum yapısı kaydı #{row.id} değiştirilemez veya silinemez. Kurum Yapısı ekranında gerekçeli iptal kaydı oluşturun.')


def integer(value, label):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise HTTPException(422, f'{label} geçersiz. Kurum Yapısı ekranında mevcut kaydı seçin.') from None


def day(value, label, optional=False):
    if optional and not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        raise HTTPException(422, f'{label} geçersiz. {label} alanına yıl-ay-gün biçiminde geçerli bir tarih girin.') from None


def encoded(fields):
    return {key: value.isoformat() if isinstance(value, date) else value for key, value in fields.items()}


def profile_data(scope):
    return encoded({key: getattr(scope, key) for key in PROFILE_FIELDS})


def period_name(db, period_id, department):
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period_id, DepartmentScope.department_id == department.id))
    if scope and scope.display_name:
        return scope.display_name
    period = db.get(ReportingPeriod, period_id)
    for change in live_changes(db):
        old = json.loads(change.snapshot_json)['before']['departments'].get(str(department.id))
        if old and period.year < change.effective_date.year:
            return old['name']
    return department.name


def live_changes(db):
    return db.scalars(select(StructureChange).where(~StructureChange.id.in_(select(StructureChangeCancellation.change_id))).order_by(StructureChange.effective_date, StructureChange.id)).all()


def links_for(db, change_id):
    return db.scalars(select(StructureChangeLink).where(StructureChangeLink.change_id == change_id).order_by(StructureChangeLink.id)).all()


def department_in_year(db, department, year):
    """Exclude future creations and prior closures, while retaining closure-year AR."""
    for change in live_changes(db):
        links = links_for(db, change.id)
        before = json.loads(change.snapshot_json)['before']['departments']
        if str(department.id) in before and before[str(department.id)] is None and change.effective_date.year > year:
            return False
        if change.change_type in {'MERGED', 'SPLIT', 'CLOSED'} and change.effective_date.year < year:
            if any(link.from_department_id == department.id for link in links):
                return False
    return True


def work_items(db, period_id):
    result = []
    for model, kind in ((Activity, 'activity'), (Indicator, 'indicator')):
        for row in db.scalars(select(model).where(model.period_id == period_id).order_by(model.id)):
            result.append(dict(key=f'{kind}_{row.id}_{row.department_id}', kind=kind, id=row.id,
                               department_id=row.department_id, name=row.name))
    for row, did in db.execute(select(OfficialActivity, ActivityResponsibility.department_id).join(
            ActivityResponsibility, ActivityResponsibility.official_activity_id == OfficialActivity.id).where(OfficialActivity.period_id == period_id)):
        result.append(dict(key=f'official_{row.id}_{did}', kind='official', id=row.id, department_id=did, name=row.name))
    return result


def lock_organization(db, organization_id):
    org = db.scalar(select(Organization).where(Organization.id == organization_id).with_for_update())
    if not org:
        raise HTTPException(422, 'Kurum bulunamadı. Kurum Yapısı ekranında mevcut kurumu seçin.')


def save_change(db, actor, form):
    if actor.role != 'strategy':
        raise HTTPException(403, 'Kurum yapısı kaydı yalnızca Strateji tarafından oluşturulabilir. Strateji birimine başvurun.')
    oid = integer(form.get('organization_id'), 'Kurum'); lock_organization(db, oid)
    kind = form.get('change_type')
    if kind not in KINDS:
        raise HTTPException(422, 'Yapı değişikliği türü geçersiz. Ad değişikliği, birleşme, bölünme, kapanış veya yeni müdürlük seçin.')
    effective = day(form.get('effective_date'), 'Yürürlük tarihi')
    decision_date = day(form.get('council_decision_date'), 'Meclis karar tarihi')
    decision_no = name_value(form.get('council_decision_no'), 'Meclis karar no', 200)
    if decision_date > effective:
        raise HTTPException(422, 'Meclis karar tarihi yürürlük tarihinden sonra olamaz. İki tarih alanını meclis kararıyla karşılaştırıp düzeltin.')
    pid = integer(form.get('period_id'), 'Kaynak dönem')
    period = db.get(ReportingPeriod, pid)
    if not period or period.year > effective.year:
        raise HTTPException(422, 'Kaynak dönem bulunamadı veya yürürlük yılından sonra. Aktarılacak kayıtların önceki/aynı yıl dönemini seçin.')
    old_ids = sorted({integer(x, 'Eski müdürlük') for x in form.getlist('from_department_ids')})
    to_ids = sorted({integer(x, 'Devralan müdürlük') for x in form.getlist('to_department_ids')})
    new_names = [name_value(x, 'Yeni müdürlük adı', 200) for x in str(form.get('new_names', '')).splitlines() if x.strip()]
    if kind == 'RENAMED':
        if len(old_ids) != 1 or to_ids or new_names:
            raise HTTPException(422, 'Ad değişikliği için tek eski müdürlük seçilmeli. Devralan/yeni müdürlük alanlarını boşaltıp yeni adı girin.')
        new_name = name_value(form.get('new_name'), 'Yeni ad', 200)
    valid = {'MERGED': bool(old_ids) and len(to_ids) + len(new_names) == 1 and (len(old_ids) >= 2 or bool(to_ids)),
             'SPLIT': len(old_ids) == 1 and len(to_ids) + len(new_names) >= 2,
             'CLOSED': len(old_ids) == 1,
             'CREATED': not old_ids and not to_ids and bool(new_names), 'RENAMED': True}
    if not valid[kind] or set(old_ids) & set(to_ids):
        raise HTTPException(422, 'Eski/yeni müdürlük seçimi değişiklik türüne uymuyor. Birleşmede kapanacak müdürlükleri ve tek devralanı seçin (yeni devralan oluşturulacaksa en az iki eski gerekir); bölünmede tek eski ve en az iki devralan; kapanışta tek eski; oluşturmada yalnız yeni ad seçin.')
    departments = {}
    for did in sorted(set(old_ids + to_ids)):
        row = db.get(Department, did, populate_existing=True)
        if not row or row.organization_id != oid or not department_in_year(db, row, effective.year):
            raise HTTPException(422, f'Müdürlük #{did} bu kurum/yürürlük yılına ait etkin bir kayıt değil. Kurumu, tarihi ve müdürlük seçimini düzeltin.')
        departments[did] = row
    if any(not departments[did].is_active for did in to_ids):
        raise HTTPException(422, 'Devralan müdürlük pasif. Etkin bir devralan seçin veya yeni müdürlük adı girin.')
    for change in live_changes(db):
        if any(link.from_department_id in old_ids or link.to_department_id in old_ids + to_ids for link in links_for(db, change.id)):
            if change.effective_date > effective or (change.change_type in {'CLOSED','SPLIT','MERGED'} and any(l.from_department_id in old_ids + to_ids for l in links_for(db, change.id))):
                raise HTTPException(409, f'Müdürlük için yapı kararı #{change.id} zaten var. Önce bu kararı kontrol edin; hatalıysa gerekçeli iptal kaydı oluşturun.')
    before = {'departments': {}, 'profiles': {}}
    after = {'departments': {}, 'profiles': {}}
    for did, row in departments.items():
        before['departments'][str(did)] = {'name': row.name, 'is_active': row.is_active}
    tokens = {str(did): did for did in to_ids}
    for index, name in enumerate(new_names):
        check_department_name(db, oid, name)
        row = Department(organization_id=oid, name=name, is_active=True); db.add(row); db.flush()
        departments[row.id] = row; to_ids.append(row.id); tokens[f'new:{index}'] = row.id
        before['departments'][str(row.id)] = None
    if kind == 'RENAMED':
        row = departments[old_ids[0]]; check_department_name(db, oid, new_name, row.id)
    # Earlier profiles stay untouched; period_name resolves their old fallback
    # from this decision when an explicit historical profile does not exist.
    periods = db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year)).all()
    for did, row in departments.items():
        original = before['departments'][str(did)]
        for p in periods:
            if p.year < effective.year:
                continue
            scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == p.id, DepartmentScope.department_id == did))
            key = f'{p.id}:{did}'; before['profiles'][key] = profile_data(scope) if scope else None
            if not scope:
                scope = DepartmentScope(period_id=p.id, department_id=did, display_name=row.name, status='required', reason='')
                db.add(scope); db.flush()
            if not scope.display_name:
                scope.display_name = row.name
            if p.year >= effective.year:
                if kind == 'RENAMED' and did in old_ids:
                    scope.display_name = new_name
                if kind in {'CLOSED','MERGED','SPLIT'} and did in old_ids:
                    if p.year == effective.year:
                        scope.active_to = effective  # Inclusive: annual work remains in AR.
                        scope.status = 'required'
                    else:
                        scope.status = 'excluded'; scope.reason = f'Yapı değişikliği · Meclis kararı {decision_no}'
                        scope.active_to = effective
                if did in to_ids:
                    scope.status = 'required'
                if original is None:
                    scope.active_from = effective
            after['profiles'][key] = profile_data(scope)
            if before['profiles'][key] != after['profiles'][key]:
                audit_change(db, actor, 'structure_profile', scope, before['profiles'][key], after['profiles'][key])
        if kind == 'RENAMED' and did in old_ids:
            row.name = new_name
        if kind in {'CLOSED','MERGED','SPLIT'} and did in old_ids:
            row.is_active = False
        after['departments'][str(did)] = {'name': row.name, 'is_active': row.is_active}
        if original != after['departments'][str(did)]:
            audit_change(db, actor, 'structure_department', row, original, after['departments'][str(did)])
    change = StructureChange(change_type=kind, effective_date=effective, council_decision_no=decision_no,
        council_decision_date=decision_date, note=str(form.get('note','')).strip(), created_by=actor.id,
        snapshot_json=json.dumps({'before': before, 'after': after}, ensure_ascii=False))
    db.add(change); db.flush()
    audit_change(db, actor, 'structure_change', change, None, encoded({c.name: getattr(change, c.name) for c in change.__table__.columns if c.name != 'created_at'}))
    pairs = [(old, new) for old in old_ids for new in to_ids] if old_ids and to_ids else [(old, old if kind == 'RENAMED' else None) for old in old_ids] if old_ids else [(None,new) for new in to_ids]
    for old, new in pairs:
        link = StructureChangeLink(change_id=change.id, from_department_id=old, to_department_id=new); db.add(link)
        audit_change(db, actor, 'structure_link', link, None, {'change_id': change.id, 'from_department_id': old, 'to_department_id': new})
    available = {item['key']: item for item in work_items(db, pid)}
    for field, receiver in form.items():
        if field == 'transfer_note' or not field.startswith('transfer_') or not receiver:
            continue
        if len(form.getlist(field)) != 1:
            raise HTTPException(422, f'Aktarım kaydı {field} için birden fazla devralan gönderildi. Her iş için tek devralan müdürlük seçin.')
        item = available.get(field[len('transfer_'):])
        to_id = tokens.get(str(receiver))
        if kind not in {'MERGED','SPLIT','CLOSED'} or not item or item['department_id'] not in old_ids or to_id not in to_ids:
            raise HTTPException(422, f'Aktarım kaydı {field} seçilen eski/yeni müdürlüklerle uyuşmuyor. Kaynak dönemi ve devralan müdürlüğü yeniden seçin.')
        fields = {'official_activity_id': None, 'indicator_id': None, 'activity_id': None}
        if item['kind'] == 'indicator':
            from .activity_contract_service import ensure_identity
            fields['indicator_id'] = ensure_identity(db, db.get(Indicator, item['id']))
        else:
            fields['official_activity_id' if item['kind'] == 'official' else 'activity_id'] = item['id']
        transfer = StructureChangeTransfer(change_id=change.id, from_department_id=item['department_id'], to_department_id=to_id, note=str(form.get('transfer_note','')).strip(), **fields)
        db.add(transfer)
        audit_change(db, actor, 'structure_transfer', transfer, None, dict(change_id=change.id, from_department_id=item['department_id'], to_department_id=to_id, note=transfer.note, **fields))
    db.flush()
    return change


def cancel_change(db, actor, change_id, note):
    if actor.role != 'strategy':
        raise HTTPException(403, 'Yapı kararını yalnızca Strateji iptal edebilir. Strateji birimine başvurun.')
    change = db.get(StructureChange, change_id)
    if not change:
        raise HTTPException(404, f'Yapı kararı #{change_id} bulunamadı. Kurum Yapısı listesini yenileyin.')
    snap = json.loads(change.snapshot_json)
    dids = [int(did) for did in snap['after']['departments']]
    oid = db.get(Department, dids[0]).organization_id; lock_organization(db, oid)
    if db.scalar(select(StructureChangeCancellation.id).where(StructureChangeCancellation.change_id == change_id)):
        raise HTTPException(409, f'Yapı kararı #{change_id} zaten iptal edilmiş. Geçmiş listesini kontrol edin.')
    note = name_value(note, 'İptal gerekçesi', 10000)
    copied_periods = [audit.entity_id for audit in db.scalars(select(AuditLog).where(AuditLog.action == 'structure_period_copy'))
                      if change_id in json.loads(audit.details)['new']['change_ids']]
    for later in live_changes(db):
        if later.id > change.id and any(l.from_department_id in dids or l.to_department_id in dids for l in links_for(db,later.id)):
            raise HTTPException(409, f'Yapı kararı #{change_id} sonrasında bağlantılı karar #{later.id} var. Önce sonraki kararı kontrol edip gerekirse iptal edin.')
    # Do not overwrite later edits or decisions. Compare all touched records.
    for did, expected in snap['after']['departments'].items():
        row = db.get(Department, int(did), populate_existing=True)
        if {'name': row.name, 'is_active': row.is_active} != expected:
            raise HTTPException(409, f'Müdürlük #{did} karar sonrasında değişmiş. Önce sonraki yapı kararını/alan değişikliğini kontrol edin ve gerekirse iptal edin.')
    for key, expected in snap['after']['profiles'].items():
        pid, did = map(int, key.split(':'))
        scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == pid, DepartmentScope.department_id == did).execution_options(populate_existing=True))
        if not scope or profile_data(scope) != expected:
            raise HTTPException(409, f'Dönem/müdürlük profili {key} karar sonrasında değişmiş. Sonraki değişikliği kontrol edip gerekirse önce onu iptal edin.')
    for did, old in snap['before']['departments'].items():
        row = db.get(Department, int(did))
        values = old or {'name': row.name, 'is_active': False}
        for key, value in values.items(): setattr(row, key, value)
        audit_change(db, actor, 'structure_department_cancel', row, snap['after']['departments'][did], values)
    for key, old in snap['before']['profiles'].items():
        pid, did = map(int, key.split(':'))
        scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == pid, DepartmentScope.department_id == did))
        if old is None:
            # Keep historical rows; newly-created directorates become excluded.
            old = dict(snap['after']['profiles'][key])
            dept_before = snap['before']['departments'][str(did)]
            old.update(display_name=dept_before['name'] if dept_before else old['display_name'], active_from=None, active_to=None)
            if dept_before is None: old.update(status='excluded', reason=f'Yapı kararı #{change_id} iptal edildi: {note}')
        for field, value in old.items():
            setattr(scope, field, day(value, field, True) if field in {'active_from','active_to'} else value)
        audit_change(db, actor, 'structure_profile_cancel', scope, snap['after']['profiles'][key], profile_data(scope))
    cancellation = StructureChangeCancellation(change_id=change_id, note=note, created_by=actor.id); db.add(cancellation)
    audit_change(db, actor, 'structure_cancel', cancellation, {'change_id': change_id, 'cancelled': False}, {'change_id': change_id, 'cancelled': True, 'note': note, 'copied_periods_preserved': copied_periods})
    return cancellation


def closure_notes(db, period_id, user, organization_id=None):
    period = db.get(ReportingPeriod, period_id) if period_id else None
    if not period: return []
    result = []
    for change in live_changes(db):
        if change.effective_date.year != period.year or change.change_type not in {'MERGED','SPLIT','CLOSED'}: continue
        links = links_for(db, change.id)
        for did in sorted({l.from_department_id for l in links if l.from_department_id}):
            dept = db.get(Department, did)
            if organization_id and dept.organization_id != organization_id: continue
            if user.role == 'department' and user.department_id != did: continue
            receivers = sorted({period_name(db, period_id, db.get(Department,l.to_department_id)) for l in links if l.from_department_id == did and l.to_department_id})
            message = f'Bu müdürlük {change.effective_date.strftime("%d.%m.%Y")} tarihinde kapandı/birleşti; '
            message += f'görevleri {", ".join(receivers)} müdürlüğüne devredildi' if receivers else 'devralan müdürlük belirtilmedi; görev aktarımını Strateji birimine kontrol ettirin'
            message += f' (Meclis kararı {change.council_decision_no}).'
            result.append({'department_id': did, 'department': period_name(db, period_id, dept), 'message': message})
    return result


def routing(db, base_id, target_year):
    """Return explicit (kind, record, source) routes for decisions in this copy."""
    routes, closed, used = {}, set(), []
    base_year = db.get(ReportingPeriod, base_id).year
    for change in live_changes(db):
        if change.effective_date.year <= target_year:
            used.append(change.id)
        if change.change_type not in {'CLOSED','SPLIT','MERGED'} or not base_year <= change.effective_date.year <= target_year:
            continue
        closed.update(l.from_department_id for l in links_for(db, change.id) if l.from_department_id)
        for transfer in db.scalars(select(StructureChangeTransfer).where(StructureChangeTransfer.change_id == change.id)):
            kind, rid = ('indicator', transfer.indicator_id) if transfer.indicator_id else ('activity', transfer.activity_id) if transfer.activity_id else ('official', transfer.official_activity_id)
            routes[kind, rid, transfer.from_department_id] = transfer.to_department_id
    return routes, closed, used


def unresolved_work(db, base_id, target_year):
    routes, closed, _ = routing(db, base_id, target_year)
    result = []
    for item in work_items(db, base_id):
        rid = db.get(Indicator,item['id']).persistent_indicator_id if item['kind'] == 'indicator' else item['id']
        if item['department_id'] in closed and (item['kind'], rid, item['department_id']) not in routes:
            result.append(item)
    return result


def copy_general_sections(db, actor, base, period):
    """Explicit carry-forward; existing target records are never replaced.

    Audit links identify a previously copied section even after its title changes.
    Organization -> target period is also the import/manual section lock order.
    """
    from .pp_errors import pp_error
    from .pp_manifest import section_identity
    if actor.role != 'strategy':
        raise pp_error(403)
    if base.id == period.id:
        raise pp_error(422, 'Kaynak ve hedef dönem aynı. Bölüm kopyalamak için farklı bir kaynak dönem seçin.', 'period_id')
    for oid in db.scalars(select(Organization.id).order_by(Organization.id)):
        lock_organization(db, oid)
    from .master_data_service import period_record
    period_record(db, period.id)
    targets = db.scalars(select(ReportSection).where(ReportSection.period_id == period.id)
                         .order_by(ReportSection.position, ReportSection.id)
                         .execution_options(populate_existing=True)).all()
    history = db.scalars(select(AuditLog).where(AuditLog.action == 'section_period_copy',
        AuditLog.entity_type == 'reporting_periods', AuditLog.entity_id == period.id).order_by(AuditLog.id)).all()
    previous = [json.loads(row.details)['new'] for row in history]
    previous = [row for row in previous if row['base_period_id'] == base.id]
    links = {int(k): v for row in previous for k, v in row['links'].items()}
    by_id = {row.id: row for row in targets}
    consumed = set()
    result = {'base_period_id': base.id, 'copied': 0, 'kept': 0, 'conflicts': [], 'links': dict(links)}
    for source in db.scalars(select(ReportSection).where(ReportSection.period_id == base.id)
                             .order_by(ReportSection.position, ReportSection.id)):
        matches = [by_id[links[source.id]]] if source.id in links and links[source.id] in by_id else [
            row for row in targets if row.id not in consumed and section_identity(row) == section_identity(source)][:1]
        if matches:
            consumed.update(row.id for row in matches)
            result['kept'] += len(matches)
            result['links'][source.id] = matches[0].id
            if len(matches) > 1 or any((row.title, row.kind, row.position, row.content_json) !=
                    (source.title, source.kind, source.position, source.content_json) for row in matches):
                result['conflicts'].append({'source_id': source.id, 'title': source.title,
                    'target_ids': [row.id for row in matches],
                    'message': f'“{source.title}” hedef dönemde farklı içerik taşıyor. Mevcut bölüm korundu; Kitap Bölümleri ekranında iki dönemi karşılaştırın.'})
            continue
        row = ReportSection(period_id=period.id, title=source.title, kind=source.kind,
                            position=source.position, content_json=source.content_json)
        db.add(row); db.flush()
        targets.append(row); by_id[row.id] = row
        result['links'][source.id] = row.id
        consumed.add(row.id)
        result['copied'] += 1
    # A repeated action with the same result writes neither data nor duplicate evidence.
    if result['copied'] or not previous or previous[-1]['conflicts'] != result['conflicts']:
        audit_change(db, actor, 'section_period_copy', period, None, result)
    return result


def copy_period_work(db, actor, base, period, sub_map):
    copy_general_sections(db, actor, base, period)
    prior = db.scalar(select(AuditLog).where(AuditLog.action == 'structure_period_copy',
        AuditLog.entity_type == 'reporting_periods', AuditLog.entity_id == period.id).order_by(AuditLog.id.desc()))
    if prior:
        from .pp_errors import pp_error
        previous = json.loads(prior.details)['new']
        if previous['base_period_id'] != base.id:
            raise pp_error(409, 'Hedef dönemin yapısı başka bir dönemden kopyalanmış. Genel bölümler için Kitap Bölümleri ekranındaki kopyalama işlemini kullanın.', 'period_id')
        return previous['untransferred']
    routes, closed, used = routing(db, base.id, period.year)
    departments = db.scalars(select(Department).order_by(Department.id)).all()
    eligible = {d.id for d in departments if d.is_active and department_in_year(db,d,period.year)}
    # A closure recorded for a later year must not suppress earlier-year copies.
    for change in live_changes(db):
        if change.effective_date.year > period.year and change.change_type in {'CLOSED','MERGED','SPLIT'}:
            eligible.update(l.from_department_id for l in links_for(db,change.id) if l.from_department_id)
    for change in live_changes(db):
        if change.effective_date.year == period.year and change.change_type in {'CLOSED','MERGED','SPLIT'}:
            eligible.update(l.from_department_id for l in links_for(db,change.id) if l.from_department_id)
    eligible = {did for did in eligible if department_in_year(db, db.get(Department,did), period.year)}
    def receiver(kind, row, did):
        rid = row.persistent_indicator_id if kind == 'indicator' else row.id
        if did in closed:
            dest = routes.get((kind, rid, did))
            if dest and dest not in eligible:
                raise HTTPException(409, f'{row.name} kaydının devralan müdürlüğü #{dest} yeni dönemde etkin değil. Kurum Yapısı kararlarını kontrol edin; aktarımı düzeltin.')
            return dest
        return did if did in eligible else None
    card_map = {}
    def copy_card(card_id, did):
        if not card_id: return None
        key = card_id, did
        if key not in card_map:
            old = db.get(ReportCard, card_id)
            fields = {c.name:getattr(old,c.name) for c in ReportCard.__table__.columns if c.name not in {'id','period_id','department_id','subprogram_id','source_title'}}
            card = ReportCard(period_id=period.id, department_id=did, subprogram_id=sub_map[old.subprogram_id], source_title=f'{period.year}/{old.position}', **fields)
            db.add(card); db.flush(); card_map[key] = card.id
        return card_map[key]
    # Preserve empty cards only for departments continuing without restructuring.
    for old in db.scalars(select(ReportCard).where(ReportCard.period_id == base.id)).all():
        if old.department_id in eligible and old.department_id not in closed:
            copy_card(old.id, old.department_id)
    for old in db.scalars(select(Indicator).where(Indicator.period_id == base.id)).all():
        did = receiver('indicator',old,old.department_id)
        if did:
            from .activity_contract_service import ensure_identity
            identity_id = ensure_identity(db, old)
            new = Indicator(period_id=period.id, department_id=did, subprogram_id=sub_map[old.subprogram_id],
                card_id=copy_card(old.card_id,did), persistent_indicator_id=identity_id, code=old.code,
                position=old.position, name=old.name, unit=old.unit, explanation=old.explanation,
                calculation_method=old.calculation_method, data_source=old.data_source, status='draft')
            db.add(new)
    act_map = {}
    for old in db.scalars(select(Activity).where(Activity.period_id == base.id)).all():
        did = receiver('activity',old,old.department_id)
        if did:
            new = Activity(period_id=period.id, department_id=did, subprogram_id=sub_map.get(old.subprogram_id),
                card_id=copy_card(old.card_id,did), code=old.code, position=old.position, name=old.name, explanation=old.explanation)
            db.add(new); db.flush(); act_map[old.id] = new
    official_map = {}
    for old in db.scalars(select(OfficialActivity).where(OfficialActivity.period_id == base.id)).all():
        dids = {receiver('official',old,did) for did in db.scalars(select(ActivityResponsibility.department_id).where(ActivityResponsibility.official_activity_id == old.id))}
        dids.discard(None)
        if not dids: continue
        fields = {c.name:getattr(old,c.name) for c in OfficialActivity.__table__.columns if c.name not in {'id','period_id'}}
        new = OfficialActivity(period_id=period.id, **fields); db.add(new); db.flush(); official_map[old.id] = new.id
        for did in sorted(dids): db.add(ActivityResponsibility(official_activity_id=new.id, department_id=did))
    for old in db.scalars(select(ActivityCatalogueLink).where(ActivityCatalogueLink.activity_id.in_(act_map))).all():
        if old.official_activity_id in official_map:
            # Keep a catalogue link only when both records were routed to the same receiver.
            new_act = act_map[old.activity_id]; new_official = official_map[old.official_activity_id]
            db.flush()
            if db.scalar(select(ActivityResponsibility.id).where(ActivityResponsibility.official_activity_id == new_official, ActivityResponsibility.department_id == new_act.department_id)):
                db.add(ActivityCatalogueLink(activity_id=new_act.id, official_activity_id=new_official))
    for dept in departments:
        if dept.id not in eligible: continue
        old = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == base.id, DepartmentScope.department_id == dept.id))
        fields = profile_data(old) if old else dict(display_name=dept.name, status='required', reason='', budget_code=None, active_from=None, active_to=None)
        fields.update(active_from=None, active_to=None)
        if dept.id in routes.values(): fields['status'] = 'required'
        for change in live_changes(db):
            if change.effective_date.year == period.year and change.change_type in {'CLOSED','MERGED','SPLIT'} and any(l.from_department_id == dept.id for l in links_for(db,change.id)):
                fields.update(active_to=change.effective_date, status='required')
        # Use decisions/profile of the target year when one already exists; newly
        # created period has no profile yet, so derive future renames explicitly.
        for change in live_changes(db):
            if change.change_type == 'RENAMED' and change.effective_date.year <= period.year and any(l.from_department_id == dept.id for l in links_for(db,change.id)):
                fields['display_name'] = json.loads(change.snapshot_json)['after']['departments'][str(dept.id)]['name']
            if change.effective_date.year == period.year:
                before = json.loads(change.snapshot_json)['before']['departments']
                if str(dept.id) in before and before[str(dept.id)] is None:
                    fields['active_from'] = change.effective_date
        db.add(DepartmentScope(period_id=period.id, department_id=dept.id, **fields))
        db.add(Submission(period_id=period.id,department_id=dept.id,status='draft'))
    missing = unresolved_work(db,base.id,period.year)
    audit_change(db,actor,'structure_period_copy',period,None,{'base_period_id':base.id,'change_ids':used,'untransferred':missing})
    return missing
