"""CIV-198 oracle: unchanged readers from fa55cdba (before query optimizations).

Keep this implementation independent of the optimized snapshot readers. Pure
formatting/finance helpers and model definitions are shared; all SQL/read paths
below are copied from the parent revision.
"""
import json
from collections import defaultdict
from decimal import Decimal
from sqlalchemy import select, or_
from app.models import (Activity, ActivityCatalogueLink, ActivityCostValue,
    ActivityResponsibility, Department, DepartmentCostValue, DepartmentScope,
    EconomicValue, Indicator, OfficialActivity, Program, ReportCard, ReportSection,
    ReportingPeriod, StructureChange, StructureChangeCancellation,
    StructureChangeLink, Submission, SubProgram)
from app.program_service import (activity_source_disagreements, cost_columns,
    source_total_message)
from app.value_labels import value_kind_label
from app.numbers import format_number



def period_name(db, period_id, department):
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period_id, DepartmentScope.department_id == department.id))
    if scope and scope.display_name:
        return scope.display_name
    period = db.get(ReportingPeriod, period_id)
    return name_for_year(db, period.year, department)


def name_for_year(db, year, department):
    """Resolve a year's name from live structure decisions, without a period scope."""
    for change in live_changes(db):
        old = json.loads(change.snapshot_json)['before']['departments'].get(str(department.id))
        if old and year < change.effective_date.year:
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


def rows(db, model, period_id, department_id=None):
    stmt = select(model).where(model.period_id == period_id)
    if department_id is not None: stmt = stmt.where(model.department_id == department_id)
    return db.scalars(stmt.order_by(model.id)).all()


def record(obj):
    result = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        if isinstance(value, Decimal): value = format(value, 'f')
        elif hasattr(value, 'isoformat'): value = value.isoformat()
        result[col.name] = value
    return result


def department_snapshot(db, period_id, department_id):
    dept = db.get(Department, department_id)
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period_id, DepartmentScope.department_id == department_id))
    cards = rows(db, ReportCard, period_id, department_id)
    indicators = rows(db, Indicator, period_id, department_id)
    activities = rows(db, Activity, period_id, department_id)
    def named(row):
        data = record(row)
        sp = db.get(SubProgram, row.subprogram_id) if row.subprogram_id else None
        data['subprogram'] = sp.name if sp else ''
        data['program'] = sp.program.name if sp else ''
        return data
    return {'department_id': department_id, 'department': period_name(db, period_id, dept),
        'scope': record(scope) if scope else None,
        'period': db.get(ReportingPeriod, period_id).year,
        'cards': [named(c) for c in sorted(cards, key=lambda c: (c.position, c.id))],
        'indicators': [dict(named(i), values=[record(v) for v in i.values]) for i in indicators],
        'activities': [dict(named(a), costs=[record(v) for v in a.cost_values], official_ids=list(db.scalars(select(ActivityCatalogueLink.official_activity_id).where(ActivityCatalogueLink.activity_id==a.id)).all())) for a in activities],
        'department_costs': [record(v) for v in rows(db, DepartmentCostValue, period_id, department_id)],
        'economics': [record(v) for v in rows(db, EconomicValue, period_id, department_id)]}


def period_departments(db, period_id):
    """Active departments plus inactive departments with history in this period."""
    historical = [Department.id.in_(select(model.department_id).where(model.period_id == period_id))
                  for model in (DepartmentScope, ReportCard, Indicator, Activity, DepartmentCostValue, EconomicValue, Submission)]
    historical.append(Department.id.in_(select(ActivityResponsibility.department_id).join(
        OfficialActivity, OfficialActivity.id == ActivityResponsibility.official_activity_id).where(OfficialActivity.period_id == period_id)))
    period = db.get(ReportingPeriod, period_id)
    return [d for d in db.scalars(select(Department).where(or_(Department.is_active.is_(True), *historical)).order_by(Department.name)).all()
            if department_in_year(db, d, period.year)]


def cost_reconciliation(db, period_id, snapshots=None, *, include_historical=False):
    """One live-row calculation for screens, publication gates and frozen exports.

    Parent source totals are available only with complete ActivityCostValue source
    coverage. Never synthesize a source total from current amounts. Existing
    explicit source decisions and approved reallocations keep their semantics.
    """
    from app.activity_mapping_service import activity_mapping_states
    from types import SimpleNamespace
    period = db.get(ReportingPeriod, period_id)
    if snapshots is None:
        snapshots = [department_snapshot(db, period_id, d.id) for d in period_departments(db, period_id)]
    snapshots = sorted(snapshots, key=lambda d: ((d['scope'] or {}).get('position', 0), d['department_id']))
    departments = {d['department_id']: d for d in snapshots
                   if not d['scope'] or d['scope']['status'] != 'excluded'}
    activities = [a for d in departments.values() for a in d['activities']]
    programs = {p.id: p for p in rows(db, Program, period_id)}
    subprograms = {s.id: s for s in rows(db, SubProgram, period_id) if s.program_id in programs}
    cards = {c.id: c for c in rows(db, ReportCard, period_id)}
    states = activity_mapping_states(db, period_id)
    # Use the same serialized rows as the aggregate. Older frozen schema
    # adapters omit source fields; absence is a warning, never a new DB query.
    source_activities = {a['id']: SimpleNamespace(name=a['name'], cost_values=[SimpleNamespace(**{
        **v, 'amount': Decimal(v['amount']) if v['amount'] is not None else None,
        'source_amount': Decimal(v['source_amount']) if v.get('source_amount') is not None else None,
        'source_resolution_json': v.get('source_resolution_json', '{}'),
    }) for v in a['costs']]) for a in activities}
    conflicts = {aid: activity_source_disagreements(a) for aid, a in source_activities.items()}
    members = defaultdict(list)
    for did in departments:
        members['department_total', did] = []
    problems = {}
    for a in activities:
        members['department_total', a['department_id']].append(a)
        sp = subprograms.get(a['subprogram_id'])
        card = cards.get(a['card_id'])
        valid_card = card and card.department_id == a['department_id']
        valid = (states[a['id']]['ready'] and sp and valid_card
                 and card.subprogram_id == sp.id)
        if not valid:
            problems[a['id']] = (f"{departments[a['department_id']]['department']} / {a['name']}: "
                'program, alt program, kart veya katalog bağlantısı eksik ya da kapsamı uyuşmuyor. '
                'Faaliyet Eşleştirme ve Performans Kartları ekranlarında bağlantıları tamamlayın.')
        # A card can locate an incomplete activity, but cannot make it complete.
        inferred = subprograms.get(card.subprogram_id) if valid_card else None
        candidates = {s.id for s in (sp, inferred) if s}
        if not candidates:
            # No trustworthy programme attribution: every potential parent stays
            # incomplete. In particular, do not print a sum of the mapped subset.
            candidates = set(subprograms)
        for pid in sorted({subprograms[sid].program_id for sid in candidates}):
            members['program', pid].append(a)
        for sid in sorted(candidates):
            members['subprogram', sid].append(a)
            members['department', sid, a['department_id']].append(a)
        if not candidates:
            members['unmapped', a['department_id']].append(a)

    def make_rows(key, label, path, program_id=None, subprogram_id=None, department_id=None):
        group = members[key]
        result = []
        for year, kind in cost_columns(period.year)[0 if include_historical else 3:]:
            errors = list(dict.fromkeys(problems[a['id']] for a in group if a['id'] in problems))
            if not group and (departments[department_id]['scope'] or {}).get('status') != 'zero':
                errors.append(f'{path} / {year}: faaliyet kaydı yok; faaliyetleri ve maliyetlerini tamamlayın '
                    'veya gerekçeli sıfır bütçe kapsamını seçin.')
            values = [next((v for v in a['costs'] if
                (v['year'], v['value_kind'], v['funding_type']) == (year, kind, 'total')), None) for a in group]
            for a in group:
                finance = {v['funding_type']: v for v in a['costs']
                           if (v['year'], v['value_kind']) == (year, kind)}
                if (any(f not in finance or finance[f]['amount'] is None or finance[f]['state'] != 'verified'
                        for f in ('inside', 'outside', 'total'))
                    or Decimal(finance['inside']['amount']) + Decimal(finance['outside']['amount']) != Decimal(finance['total']['amount'])):
                    errors.append(f"{path} / {a['name']} / {year} {value_kind_label(kind)}: "
                        'maliyet bilgisi eksik, doğrulanmamış veya bütçe içi + dışı toplamı uyuşmuyor. '
                        'Faaliyet maliyetlerini kontrol edip tamamlayın.')
            complete = not errors
            amount = sum((Decimal(v['amount']) for v in values), Decimal(0)) if complete else None
            source_complete = bool(values) and not any(a['id'] in problems for a in group) and all(
                v and v.get('source_amount') is not None for v in values)
            source = sum((Decimal(v['source_amount']) for v in values), Decimal(0)) if source_complete else None
            warnings = []
            if not source_complete:
                warnings.append(f'{path} / {year} {value_kind_label(kind)}: kaynak toplamı yok '
                    '(tüm faaliyetleri kapsayan kaynak tutarı bulunmuyor). Kaynak belgeyi kontrol edin.')
            # Reuse the existing source decision / approved reallocation rules.
            for a in group:
                conflict = conflicts[a['id']].get(f'{year}:{kind}')
                if conflict:
                    computed = conflict['computed_total']; original = conflict['source_total']
                    difference = computed - original if computed is not None else None
                    errors.append(source_total_message(source_activities[a['id']], year, kind, original, computed)
                        + f' Fark: {format_number(difference, money=True)} TL. Kaynakla karşılaştırın.')
            difference = amount - source if amount is not None and source is not None else None
            if difference:
                # A nonzero raw difference can be explained by an explicit source
                # decision or an approved reallocation, never by silent correction.
                message = (f'{path} / {year} {value_kind_label(kind)}: hesaplanan toplam '
                    f'{format_number(amount, money=True)} TL, kaynak toplamı {format_number(source, money=True)} TL, '
                    f'fark {format_number(difference, money=True)} TL.')
                if any(conflicts[a['id']].get(f'{year}:{kind}') for a in group):
                    errors.append(message + ' Faaliyet tutarlarını kaynakla karşılaştırın.')
                else:
                    warnings.append(message + ' Gerekçeli kaynak kararı veya onaylı bütçe aktarması vardır; karar kayıtlarını inceleyin.')
            result.append(dict(level=key[0], program_id=program_id, subprogram_id=subprogram_id,
                department_id=department_id, label=label, path=path, year=year, value_kind=kind,
                activity_ids=sorted(a['id'] for a in group), complete=complete,
                amount=str(amount) if amount is not None else None,
                source_amount=str(source) if source is not None else None,
                difference=str(difference) if difference is not None else None,
                errors=errors, warnings=warnings,
                status='Yayın engeli' if errors else ('Uyarı' if warnings else 'Mutabık')))
        return result

    result = []
    for pid, program in sorted(programs.items(), key=lambda item: (item[1].name, item[0])):
        if ('program', pid) not in members:
            continue
        result.extend(make_rows(('program', pid), f'Program ara toplamı: {program.name}', program.name, pid))
        for sid, sp in sorted(subprograms.items(), key=lambda item: (item[1].name, item[0])):
            if sp.program_id != pid or ('subprogram', sid) not in members:
                continue
            path = f'{program.name} / {sp.name}'
            result.extend(make_rows(('subprogram', sid), f'Alt program ara toplamı: {sp.name}', path, pid, sid))
            for did, d in departments.items():
                if ('department', sid, did) in members:
                    result.extend(make_rows(('department', sid, did), f"Müdürlük ara toplamı: {d['department']}",
                        f"{path} / {d['department']}", pid, sid, did))
    for did, d in departments.items():
        if ('department_total', did) in members:
            result.extend(make_rows(('department_total', did), f"Müdürlük faaliyetleri toplamı: {d['department']}",
                d['department'], department_id=did))
        if ('unmapped', did) in members:
            result.extend(make_rows(('unmapped', did), f"Eşleştirme eksik: {d['department']}", d['department'], department_id=did))
    return result


def book_snapshot(db, period_id):
    period = db.get(ReportingPeriod, period_id)
    departments = period_departments(db, period_id)
    snapshots = [department_snapshot(db,period_id,d.id) for d in departments]
    snapshots.sort(key=lambda d: ((d['scope'] or {}).get('position',0),d['department_id']))
    catalogue = []
    for item in rows(db, OfficialActivity, period_id):
        item_data = record(item)
        item_data['departments'] = [r.department_id for r in db.scalars(select(ActivityResponsibility).where(ActivityResponsibility.official_activity_id==item.id)).all()]
        catalogue.append(item_data)
    groups = defaultdict(Decimal); economic = defaultdict(Decimal)
    for d in snapshots:
        if d['scope'] and d['scope']['status']=='excluded': continue
        for v in d['economics']:
            if v['year']>=period.year and v['amount'] is not None:
                economic[(v['category'],v['year'],v['program_group'],v['funding_type'])] += Decimal(v['amount'])
        for a in d['activities']:
            for v in a['costs']:
                if v['year']>=period.year and v['amount'] is not None:
                    groups[(a['program'],a['subprogram'],a['id'],a['name'],v['year'],v['funding_type'])] += Decimal(v['amount'])
    return {'schema_version':'5.0','period':period.year,'departments':snapshots,
        'sections':[record(s) for s in sorted(rows(db,ReportSection,period_id),key=lambda s:(s.position,s.id))],
        'catalogue':catalogue,
        'cost_reconciliation':cost_reconciliation(db, period_id, snapshots),
        'economics':[{'category':k[0],'year':k[1],'program_group':k[2],'funding_type':k[3],'amount':str(v)} for k,v in sorted(economic.items())],
        'program_costs':[{'program':k[0],'subprogram':k[1],'activity_id':k[2],'name':k[3],'year':k[4],'funding_type':k[5],'amount':str(v)} for k,v in sorted(groups.items())]}


def department_package_snapshot(db, period_id, department_id):
    """Freeze relationship facts used by validation, without changing publication formats."""
    content = department_snapshot(db, period_id, department_id)
    subprogram_ids = {c['subprogram_id'] for c in content['cards']}
    official_ids = {oid for a in content['activities'] for oid in a['official_ids']}
    content['validation_context'] = {
        'version': 'department-validation-v1', 'period_id': period_id, 'department_id': department_id,
        'subprograms': [record(row) for row in db.scalars(select(SubProgram).where(SubProgram.id.in_(subprogram_ids)).order_by(SubProgram.id))],
        'officials': [record(row) for row in db.scalars(select(OfficialActivity).where(OfficialActivity.id.in_(official_ids)).order_by(OfficialActivity.id))],
        'responsible_ids': sorted(db.scalars(select(ActivityResponsibility.official_activity_id).where(
            ActivityResponsibility.department_id == department_id, ActivityResponsibility.official_activity_id.in_(official_ids))).all()),
    }
    return content
