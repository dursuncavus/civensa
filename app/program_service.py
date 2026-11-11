"""Report cards, exact finance, completeness checks and immutable snapshots."""
from datetime import datetime, UTC
from .serialization import json_dumps
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import select, or_, union_all, inspect
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import set_committed_value
from fastapi import HTTPException
from .pp_errors import pp_error
from .models import (ReportCard, Indicator, IndicatorValue, Activity, ActivityCostValue,
    DepartmentCostValue, EconomicValue, DepartmentScope, Department, Program, SubProgram,
    ReportingPeriod, ReportSection, OfficialActivity, ActivityResponsibility, ActivityCatalogueLink,
    Submission, SubmissionEvent, AuditLog)
from .numbers import parse_number, format_number
from .value_labels import value_kind_label, funding_label
import json
from .structure_service import structure_read_scope

ECONOMIC_CATEGORIES = {
    'personnel': 'Personel Giderleri', 'sgk': 'Sosyal Güvenlik Kurumuna Devlet Primi Giderleri',
    'goods_services': 'Mal ve Hizmet Alım Giderleri', 'interest': 'Faiz Giderleri',
    'current_transfers': 'Cari Transferler', 'capital': 'Sermaye Giderleri',
    'capital_transfers': 'Sermaye Transferleri', 'lending': 'Borç Verme', 'reserve': 'Yedek Ödenekler'}
PROGRAM_GROUPS = {'service': 'Hizmet Programları', 'management': 'Yönetim ve Destek Programı', 'outside_program': 'Program Dışı Giderler', 'unallocated': 'Program Grubu Belirlenmeli'}


def save_catalogue_entry(db, period_id, values, department_ids, actor, obj=None, source=None):
    """Shared catalogue write path. Caller owns the transaction; audit is atomic."""
    if not db.get(ReportingPeriod, period_id):
        raise pp_error(404, 'Katalog dönemi bulunamadı. Raporlama dönemi seçimini kontrol edin.', 'period_id')
    ids = set(department_ids)
    if not ids or any(not db.get(Department, did) for did in ids):
        raise HTTPException(422, 'Geçerli sorumlu birimleri seçin.')
    if any(not str(values.get(f, '')).strip() for f in ('program_name', 'subprogram_name', 'code', 'name')):
        raise HTTPException(422, 'Katalog kod/ad alanları zorunlu.')
    if obj and obj.period_id != period_id:
        raise pp_error(403, 'Katalog kaydı bu döneme ait değil. Kaydın dönemini seçip yeniden deneyin.', 'id')
    existing = {r.department_id: r for r in db.scalars(select(ActivityResponsibility).where(
        ActivityResponsibility.official_activity_id == obj.id))} if obj else {}
    linked = set(db.scalars(select(Activity.department_id).join(ActivityCatalogueLink,
        ActivityCatalogueLink.activity_id == Activity.id).where(
        ActivityCatalogueLink.official_activity_id == obj.id))) if obj else set()
    if not linked.issubset(ids):
        raise HTTPException(409, 'Bağlı yerel faaliyetlerin sorumlu birimini kaldırmadan önce bağlantıyı düzenleyin.')
    changed = obj is None or ids != existing.keys() or any(getattr(obj, f) != v for f, v in values.items())
    if obj is None:
        obj = OfficialActivity(period_id=period_id, **values)
        db.add(obj)
        db.flush()
    else:
        for field, value in values.items():
            setattr(obj, field, value)
    for did, responsibility in existing.items():
        if did not in ids:
            db.delete(responsibility)
    for did in ids - existing.keys():
        db.add(ActivityResponsibility(official_activity_id=obj.id, department_id=did))
    if changed:
        db.add(AuditLog(user_id=actor.id, action='catalogue_create', entity_type='official_activity',
                        entity_id=obj.id, details=json_dumps({'values': values,
                            'department_ids': sorted(ids), 'source': source})))
    return obj


def save_activity_catalogue_links(db, activity, official_ids, actor, source=None):
    ids = set(official_ids)
    for oid in ids:
        official = db.get(OfficialActivity, oid)
        responsible = db.scalar(select(ActivityResponsibility.id).where(
            ActivityResponsibility.official_activity_id == oid,
            ActivityResponsibility.department_id == activity.department_id))
        if not official or official.period_id != activity.period_id or not responsible:
            raise HTTPException(422, 'Katalog faaliyeti bu dönem ve sorumlu birime ait olmalı.')
    existing = {link.official_activity_id: link for link in db.scalars(select(ActivityCatalogueLink).where(
        ActivityCatalogueLink.activity_id == activity.id))}
    for oid, link in existing.items():
        if oid not in ids:
            db.delete(link)
    for oid in ids - existing.keys():
        db.add(ActivityCatalogueLink(activity_id=activity.id, official_activity_id=oid))
    if ids != existing.keys():
        db.add(AuditLog(user_id=actor.id, action='catalogue_link', entity_type='activity',
                        entity_id=activity.id, details=json_dumps({'official_ids': sorted(ids), 'source': source})))


def cost_columns(year):
    return [(year-1, 'budget'), (year-1, 'midyear_spend'), (year-1, 'year_end_estimate'),
            (year, 'budget'), (year+1, 'forecast'), (year+2, 'forecast')]


def economic_columns(year):
    return [c for c in cost_columns(year) if c[1] != 'year_end_estimate']


def historical_no_data(value, year):
    return (value is not None and value.year == year - 1
            and value.value_kind in {'budget', 'midyear_spend', 'year_end_estimate'}
            and value.state == 'not_applicable' and value.amount is None
            and value.raw_text.strip() in {'-', '–', '—'})


VALUE_KIND_LABELS = {"budget": "Bütçe", "midyear_spend": "Haziran Sonu Harcama",
                     "year_end_estimate": "Yıl Sonu Harcama Tahmini", "forecast": "Tahmin"}


def activity_source_disagreements(activity):
    rows = {(v.year, v.value_kind, v.funding_type): v for v in activity.cost_values}
    result = {}
    for total in activity.cost_values:
        resolution = json.loads(total.source_resolution_json or '{}')
        if total.funding_type != "total" or total.source_amount is None or any(k != 'budget_reallocation_delta' for k in resolution):
            continue
        inside = rows.get((total.year, total.value_kind, "inside"))
        outside = rows.get((total.year, total.value_kind, "outside"))
        computed = inside.amount + outside.amount if inside and outside and inside.amount is not None and outside.amount is not None else None
        if computed is not None:
            computed -= Decimal(resolution.get('budget_reallocation_delta', '0'))
        if total.source_amount != computed:
            result[f"{total.year}:{total.value_kind}"] = {"source_total": total.source_amount, "computed_total": computed}
    return result


def mark_source_disagreements(activity):
    conflicts = activity_source_disagreements(activity)
    for total in activity.cost_values:
        if total.funding_type == "total" and f"{total.year}:{total.value_kind}" in conflicts:
            total.state = "needs_review"


def source_total_message(activity, year, kind, source, computed):
    return (f"{activity.name} · {year} · {VALUE_KIND_LABELS.get(kind, kind)}: "
            f"kaynak toplamı {format_number(source, money=True)}, "
            f"hesaplanan toplam {format_number(computed, money=True)}. "
            "Kaynak toplamı korunuyor. Bütçe içi ve dışını kaynakla eşitleyin veya ‘Hesaplanan toplamı kullan’ "
            "seçeneğini en az 10 karakterlik gerekçeyle onaylayın.")


def save_activity_costs(db, activity, year, data, actor=None):
    existing = {(v.year, v.value_kind, v.funding_type): v for v in activity.cost_values}
    pending = []
    # Validate the entire request before changing any finance row or adding audit entries.
    for y, kind in cost_columns(year):
        prefix = f'cost_{y}_{kind}'
        if not any(k in data for k in [prefix, prefix+'_inside', prefix+'_outside', prefix+'_use_computed']):
            continue
        values = {}
        for funding in ['inside', 'outside']:
            key = prefix+'_'+funding
            if key in data:
                try:
                    values[funding] = parse_number(data[key], money=True)
                except ValueError as exc:
                    raise pp_error(422, f'{activity.name} / {y}: Finansman tutarı geçersiz. Türkçe sayı biçiminde girin (ör. 1.250,50).', key) from None
            else:
                row = existing.get((y, kind, funding))
                values[funding] = row.amount if row else None
        if prefix in data and prefix+'_inside' not in data and prefix+'_outside' not in data:
            try:
                total = parse_number(data[prefix], money=True)
            except ValueError as exc:
                raise pp_error(422, f'{activity.name} / {y}: Toplam tutar geçersiz. Bütçe içi ve dışını ayrı girin.', prefix+'_inside') from None
            old = existing.get((y, kind, 'total'))
            if total is not None and (old is None or total != old.amount):
                raise pp_error(422, f'{activity.name} / {y}: Bütçe içi ve bütçe dışı tutarları ayrı girin.', prefix+'_inside')
            if total is None:
                values = {'inside': None, 'outside': None}
        if (values['inside'] is None) != (values['outside'] is None):
            raise pp_error(422, f'{activity.name} / {y}: Bütçe içi ve dışını birlikte girin; kaynak yoksa açıkça 0 yazın.', prefix+('_inside' if values['inside'] is None else '_outside'))
        values['total'] = values['inside'] + values['outside'] if values['inside'] is not None else None
        total_row = existing.get((y, kind, 'total'))
        decision = None
        resolution = json.loads(total_row.source_resolution_json or '{}') if total_row else {}
        adjusted_total = values['total'] - Decimal(resolution.get('budget_reallocation_delta', '0')) if values['total'] is not None else None
        if total_row and total_row.source_amount is not None and not any(k != 'budget_reallocation_delta' for k in resolution) and adjusted_total != total_row.source_amount:
            message = source_total_message(activity, y, kind, total_row.source_amount, adjusted_total)
            if resolution.get('budget_reallocation_delta'):
                message += ' Karşılaştırılan toplamdan onaylı aktarma etkisi çıkarılmıştır.'
            confirmation = data.get(prefix+'_use_computed')
            if confirmation is not True and confirmation not in ('true', 'on'):
                raise pp_error(422, message, prefix+'_inside')
            reason = data.get(prefix+'_reason')
            if not isinstance(reason, str) or len(reason.strip()) < 10:
                raise pp_error(422, message + ' Karar gerekçesi en az 10 karakter olmalı.', prefix+'_reason')
            if actor is None or values['total'] is None:
                raise pp_error(422, message, prefix+'_inside')
            decision = {"actor": actor.id, "time": datetime.now(UTC).isoformat(), "activity": activity.id,
                        "activity_name": activity.name, "year": y, "kind": kind,
                        "source_total": str(total_row.source_amount), "source_raw_text": total_row.source_raw_text,
                        "new_total": str(values['total']), "reason": reason.strip()}
        pending.append((y, kind, values, decision))
    for y, kind, values, decision in pending:
        if decision:
            total_row = existing[y, kind, 'total']
            total_row.source_resolution_json = json_dumps(decision, ensure_ascii=False)
            db.add(AuditLog(user_id=actor.id, action='activity_source_total_decision', entity_type='activity',
                            entity_id=activity.id, details=json_dumps(decision, ensure_ascii=False)))
        for funding, amount in values.items():
            row = existing.get((y, kind, funding))
            if row and row.state != "verified" and (amount is None or amount == row.amount):
                # A matching source split or an explicit decision verifies its total.
                if funding != 'total' or row.source_amount is None or (amount != row.source_amount and not decision):
                    continue
            if amount is None:
                if row: db.delete(row)
            elif row:
                row.amount = amount; row.state = 'verified'; row.raw_text = row.raw_text or str(amount)
            else:
                db.add(ActivityCostValue(activity_id=activity.id, year=y, value_kind=kind,
                    funding_type=funding, amount=amount, state='verified', raw_text=str(amount)))


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


def _load_snapshot_values(db, owners, model, foreign_key, relationship):
    """Batch the original per-owner SELECTs without changing year ties.

    A selectinload's single ORDER BY year can reorder equal-year values on
    PostgreSQL. Keep each legacy WHERE/ORDER BY in its own subquery, then
    concatenate the results in one round trip (bounded for SQLite's UNION
    limit). Already-loaded collections keep their original session semantics.
    """
    if db.dispatch.do_orm_execute:
        # A caller's ORM adapter may defer columns or inject loader criteria.
        # A fixed UNION projection cannot honor those rewrites: leave the
        # original relationship loader in charge in such sessions.
        return
    pending = [owner for owner in owners if relationship in inspect(owner).unloaded]
    for offset in range(0, len(pending), 200):
        batch = pending[offset:offset + 200]
        statements = [select(select(model).where(getattr(model, foreign_key) == owner.id)
            .order_by(model.year).subquery()) for owner in batch]
        grouped = defaultdict(list)
        for value in db.scalars(select(model).from_statement(union_all(*statements))):
            grouped[getattr(value, foreign_key)].append(value)
        for owner in batch:
            set_committed_value(owner, relationship, grouped[owner.id])


@structure_read_scope
def department_snapshots(db, period_id, departments):
    """Load each period collection once, preserving the legacy row/key order."""
    from .structure_service import period_name
    departments = list(departments)
    ids = [department.id for department in departments]
    period = db.get(ReportingPeriod, period_id)
    scopes = {scope.department_id: scope for scope in db.scalars(select(DepartmentScope).where(
        DepartmentScope.period_id == period_id, DepartmentScope.department_id.in_(ids)))}
    grouped = {}
    for model in (ReportCard, Indicator, Activity, DepartmentCostValue, EconomicValue):
        stmt = select(model).where(model.period_id == period_id, model.department_id.in_(ids)).order_by(model.id)
        items = db.scalars(stmt).all()
        if model is Indicator:
            _load_snapshot_values(db, items, IndicatorValue, 'indicator_id', 'values')
        elif model is Activity:
            _load_snapshot_values(db, items, ActivityCostValue, 'activity_id', 'cost_values')
        by_department = defaultdict(list)
        for row in items:
            by_department[row.department_id].append(row)
        grouped[model] = by_department
    subprogram_ids = {row.subprogram_id for model in (ReportCard, Indicator, Activity)
                      for items in grouped[model].values() for row in items if row.subprogram_id}
    subprograms = {sp.id: sp for sp in db.scalars(select(SubProgram).where(
        SubProgram.id.in_(subprogram_ids)).options(joinedload(SubProgram.program)))}
    links = defaultdict(list)
    for aid, oid in db.execute(select(ActivityCatalogueLink.activity_id,
            ActivityCatalogueLink.official_activity_id).join(Activity).where(
                Activity.period_id == period_id, Activity.department_id.in_(ids))):
        links[aid].append(oid)

    def named(row):
        data = record(row)
        sp = subprograms.get(row.subprogram_id)
        data['subprogram'] = sp.name if sp else ''
        data['program'] = sp.program.name if sp else ''
        return data

    result = []
    for dept in departments:
        did = dept.id
        scope = scopes.get(did)
        result.append({'department_id': did, 'department': period_name(db, period_id, dept),
            'scope': record(scope) if scope else None, 'period': period.year,
            'cards': [named(c) for c in sorted(grouped[ReportCard][did], key=lambda c: (c.position, c.id))],
            'indicators': [dict(named(i), values=[record(v) for v in i.values]) for i in grouped[Indicator][did]],
            'activities': [dict(named(a), costs=[record(v) for v in a.cost_values], official_ids=links[a.id])
                           for a in grouped[Activity][did]],
            'department_costs': [record(v) for v in grouped[DepartmentCostValue][did]],
            'economics': [record(v) for v in grouped[EconomicValue][did]]})
    return result


def department_snapshot(db, period_id, department_id):
    return department_snapshots(db, period_id, [db.get(Department, department_id)])[0]


def validate_department(db, period_id, department_id):
    """Legacy live-row adapter; business rules are shared with package snapshots."""
    period = db.get(ReportingPeriod, period_id)
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period_id, DepartmentScope.department_id == department_id))
    indicators = db.scalars(select(Indicator).where(Indicator.period_id == period_id,
        Indicator.department_id == department_id).options(joinedload(Indicator.card)).order_by(Indicator.id)).all()
    activities = db.scalars(select(Activity).where(Activity.period_id == period_id,
        Activity.department_id == department_id).options(joinedload(Activity.card)).order_by(Activity.id)).all()
    _load_snapshot_values(db, indicators, IndicatorValue, 'indicator_id', 'values')
    _load_snapshot_values(db, activities, ActivityCostValue, 'activity_id', 'cost_values')
    cards = rows(db, ReportCard, period_id, department_id)
    economics = rows(db, EconomicValue, period_id, department_id)
    personnel_rows = rows(db, DepartmentCostValue, period_id, department_id)
    links = db.scalars(select(ActivityCatalogueLink).join(Activity).where(Activity.period_id == period_id, Activity.department_id == department_id)).all()
    links_by_activity = defaultdict(list)
    for link in links: links_by_activity[link.activity_id].append(link)
    official_ids = {link.official_activity_id for link in links}
    officials = {item.id: item for item in db.scalars(select(OfficialActivity).where(OfficialActivity.id.in_(official_ids))).all()} if official_ids else {}
    responsible_ids = set(db.scalars(select(ActivityResponsibility.official_activity_id).where(ActivityResponsibility.department_id == department_id, ActivityResponsibility.official_activity_id.in_(official_ids))).all()) if official_ids else set()
    subprograms = {c.subprogram_id: db.get(SubProgram, c.subprogram_id) for c in cards}
    return _validate_department_records(period_id, department_id, period.year, scope, indicators, activities,
        cards, economics, personnel_rows, links_by_activity, officials, responsible_ids, subprograms)


def _validate_department_records(period_id, department_id, year, scope, indicators, activities,
        cards, economics, personnel_rows, links_by_activity, officials, responsible_ids, subprograms):
    from .main import indicator_issues
    errors = []; warnings = []
    if scope and scope.status in {'zero', 'excluded'}:
        if not scope.reason.strip(): errors.append('Kapsam istisnasının gerekçesi zorunlu.')
        personnel_scope=personnel_rows
        if any(v.amount for v in economics) or any(v.amount is None or v.amount!=0 or v.state!='verified' for v in personnel_scope) or indicators or activities or cards:
            errors.append('Sıfır/kapsam dışı müdürlükte veri var; kayıtları silmeden kapsamı kontrol edin.')
        return errors, warnings
    if not indicators: errors.append('Performans göstergesi yok.')
    if not cards: errors.append('Performans kartları hazırlanmalı; eski kayıtları kartlara açıkça atayın.')
    for c in cards:
        sp=subprograms.get(c.subprogram_id)
        if not sp or sp.period_id!=period_id:errors.append(f'Kart {c.id}: alt program dönemi uyuşmuyor.')
        for attr, label in [('rationale','Gerekçe'),('goal','Alt program hedefi'),('responsible','Sorumlu idare')]:
            if not getattr(c,attr).strip(): errors.append(f'Kart {c.source_title or c.id}: {label} eksik.')
    for i in indicators:
        errors.extend(f'{i.name}: {msg}' for msg in indicator_issues(i, year))
        for value in i.values:
            if value.value is None and value.raw_text.strip() in {'-', '–', '—'}:
                warnings.append(f'{i.name}: {value.year} {value_kind_label(value.value_kind)} kaynakta çizgi; müdürlükçe kontrol edilmeli.')
        if not i.card_id: errors.append(f'{i.name}: kart bağlantısı eksik.')
        elif i.card.department_id != department_id or i.card.period_id != period_id or i.card.subprogram_id != i.subprogram_id:
            errors.append(f'{i.name}: kart ve alt program kapsamı uyuşmuyor.')
        if 'sayısı' in i.name.lower() and ('%' in i.unit or 'oran' in i.unit.lower()):
            warnings.append(f'{i.name}: sayı/oran birimi müdürlükçe kontrol edilmeli.')
    required = cost_columns(year)[3:]
    totals = {c: Decimal(0) for c in required}
    complete = {c: bool(activities) for c in required}
    for a in activities:
        links = links_by_activity[a.id]
        if not links: errors.append(f'{a.name}: sorumlu harcama birimleri kataloğu bağlantısı eksik.')
        for link in links:
            official = officials.get(link.official_activity_id)
            if not official or official.period_id!=period_id or link.official_activity_id not in responsible_ids:errors.append(f'{a.name}: katalog kapsamı geçersiz.')
        if not a.card_id: errors.append(f'{a.name}: kart bağlantısı eksik.')
        elif a.card.department_id != department_id or a.card.period_id != period_id or a.card.subprogram_id != a.subprogram_id:
            errors.append(f'{a.name}: kart ve alt program kapsamı uyuşmuyor.')
        if not a.explanation.strip(): errors.append(f'{a.name}: faaliyet açıklaması eksik.')
        m = {(v.year,v.value_kind,v.funding_type): v for v in a.cost_values}
        for v in a.cost_values:
            historical_na = historical_no_data(v, year)
            if not historical_na and (v.state != 'verified' or v.amount is None):
                errors.append(f'{a.name}: {v.year} {value_kind_label(v.value_kind)} / {funding_label(v.funding_type)} kaynak tutarı doğrulanmalı.')
        for y,k in set(required) | {(v.year,v.value_kind) for v in a.cost_values}:
            vs = [m.get((y,k,f)) for f in ['total','inside','outside']]
            if all(historical_no_data(v, year) for v in vs):
                continue
            if any(v is None or v.amount is None for v in vs):
                errors.append(f'{a.name}: {y} {value_kind_label(k)} finansman bilgisi eksik.')
                if (y,k) in complete: complete[y,k] = False
            elif vs[0].amount != vs[1].amount + vs[2].amount:
                errors.append(f'{a.name}: {y} toplamı bütçe içi + dışı ile eşit değil.')
            if (y,k) in totals and vs[0] and vs[0].amount is not None: totals[y,k] += vs[0].amount
    card_ids = {card.id for card in cards}
    for v in economics:
        if getattr(v, 'source_card_id', None) and v.source_card_id not in card_ids:
            errors.append(f'{v.year}: ekonomik kaynak kartının müdürlük ve dönem kapsamı uyuşmuyor.')
        if (v.year,v.value_kind) not in economic_columns(year) or v.category not in ECONOMIC_CATEGORIES or v.program_group not in PROGRAM_GROUPS or v.funding_type not in {'inside','outside'} or (v.amount is not None and (not v.amount.is_finite() or v.amount<0)):errors.append('Ekonomik tablo boyut/tutar bilgisi geçersiz.')
        if getattr(v, 'state', 'verified') != 'verified' or v.amount is None or v.program_group == 'unallocated':
            errors.append(f'{v.year} {value_kind_label(v.value_kind)} / {ECONOMIC_CATEGORIES.get(v.category,"Ekonomik gider")} / {funding_label(v.funding_type)}: ekonomik kaynak tutarı ve program grubu doğrulanmalı.')
    personnel = {(v.year,v.value_kind): v for v in personnel_rows if v.category=='personnel_sgk'}
    for y,k in required:
        p = personnel.get((y,k)); ev = [v for v in economics if v.year==y and v.value_kind==k]
        if not p or p.amount is None or p.state!='verified': errors.append(f'{y}: personel ve SGK gideri eksik (yoksa 0 girin).')
        if not ev: errors.append(f'{y}: ekonomik tablo eksik.')
        for group in {v.program_group for v in economics}:
            for fund in ['inside','outside']:
                group_values = [v for v in ev if v.program_group==group and v.funding_type==fund]
                expected_categories = set(ECONOMIC_CATEGORIES)
                # A compact source table explicitly enumerates its applicable categories.
                # Keep omitted rows absent; an empty cell within a listed row is still reviewed.
                # Split rows preserve the imported compact-table scope. A zero
                # share is explicit evidence even though it creates no target row.
                split_contexts = []
                for source in ev:
                    if source.funding_type != fund or not getattr(source, 'source_table_number', None):
                        continue
                    try:
                        source_context = json.loads(source.source_context_json)
                        split = source_context.get('split_from', {})
                        if split.get('shares') and source.category in source_context.get('categories', []):
                            split_contexts.append((source, source_context))
                    except (ValueError, TypeError, AttributeError):
                        pass  # Existing scope validation below reports malformed contexts.
                scope_values = group_values or [v for v, _ in split_contexts]
                if scope_values and all(getattr(v, 'source_table_number', None) for v in scope_values):
                    try:
                        contexts = [json.loads(v.source_context_json) for v in scope_values]
                        if any(not set(c['card_ids']).issubset(card_ids) for c in contexts):
                            raise ValueError('scope')
                        expected_categories = set().union(*(set(c['categories']) for c in contexts))
                        if not expected_categories or not expected_categories.issubset(ECONOMIC_CATEGORIES):
                            raise ValueError('categories')
                    except (ValueError, TypeError, KeyError):
                        errors.append(f'{y}: ekonomik kaynak kapsamı eksik veya geçersiz; tabloyu kontrol edin.')
                explicit_zero_categories = set()
                for source, source_context in split_contexts:
                    try:
                        if (set(source_context['card_ids']).issubset(card_ids)
                                and Decimal(source_context['split_from']['shares'][group]) == 0):
                            explicit_zero_categories.add(source.category)
                    except (ValueError, TypeError, KeyError, ArithmeticError):
                        pass
                missing=expected_categories-{v.category for v in group_values}-explicit_zero_categories
                if missing:errors.append(f'{y}: {PROGRAM_GROUPS.get(group,group)} / {"Bütçe İçi" if fund=="inside" else "Bütçe Dışı"}: {len(missing)} ekonomik gider hücresi eksik (yoksa 0 girin).')
        if p and p.amount is not None and ev and all(v.amount is not None for v in ev):
            if complete[y,k] and totals[y,k] + p.amount != sum(v.amount for v in ev): errors.append(f'{y}: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.')
            econ_personnel = sum((v.amount for v in ev if v.category in {'personnel','sgk'}), Decimal(0))
            if econ_personnel != p.amount: errors.append(f'{y}: ekonomik personel/SGK satırları ortak tablodan farklı.')
            for fund in ['inside','outside']:
                activity_funds=[next((v for v in a.cost_values if (v.year,v.value_kind,v.funding_type)==(y,k,fund)),None) for a in activities]
                if all(v and v.amount is not None for v in activity_funds):
                    expected=sum((v.amount for v in activity_funds),Decimal(0))
                    actual=sum((v.amount for v in ev if v.funding_type==fund and v.category not in {'personnel','sgk'}),Decimal(0))
                    if expected!=actual:errors.append(f'{y}: {"bütçe içi" if fund=="inside" else "bütçe dışı"} faaliyet ve ekonomik toplamları uyuşmuyor.')
    return errors, warnings


@structure_read_scope
def period_departments(db, period_id):
    """Active departments plus inactive departments with history in this period."""
    historical = [Department.id.in_(select(model.department_id).where(model.period_id == period_id))
                  for model in (DepartmentScope, ReportCard, Indicator, Activity, DepartmentCostValue, EconomicValue, Submission)]
    historical.append(Department.id.in_(select(ActivityResponsibility.department_id).join(
        OfficialActivity, OfficialActivity.id == ActivityResponsibility.official_activity_id).where(OfficialActivity.period_id == period_id)))
    from .structure_service import department_in_year
    period = db.get(ReportingPeriod, period_id)
    return [d for d in db.scalars(select(Department).where(or_(Department.is_active.is_(True), *historical)).order_by(Department.name)).all()
            if department_in_year(db, d, period.year)]


@structure_read_scope
def cost_reconciliation(db, period_id, snapshots=None, *, include_historical=False):
    """One live-row calculation for screens, publication gates and frozen exports.

    Parent source totals are available only with complete ActivityCostValue source
    coverage. Never synthesize a source total from current amounts. Existing
    explicit source decisions and approved reallocations keep their semantics.
    """
    from .activity_mapping_service import activity_mapping_states
    from types import SimpleNamespace
    period = db.get(ReportingPeriod, period_id)
    if snapshots is None:
        snapshots = department_snapshots(db, period_id, period_departments(db, period_id))
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


@structure_read_scope
def publication_checks(db, period_id):
    """Read-only gates shared by publication and the release checklist."""
    checks = []
    for dept in period_departments(db, period_id):
        scope = db.scalar(select(DepartmentScope).where(
            DepartmentScope.department_id == dept.id, DepartmentScope.period_id == period_id))
        checks.append(dict(id=f'scope:{dept.id}', label=f'{dept.name}: dönem kapsamı',
            source='program_service.publication_checks / DepartmentScope',
            observed=record(scope) if scope else None,
            errors=[] if scope else [f'{dept.name}: dönem kapsamı belirtilmeli.']))
        if not scope:
            continue
        issues, _ = validate_department(db, period_id, dept.id)
        checks.append(dict(id=f'data:{dept.id}', label=f'{dept.name}: kayıt ve toplam doğrulaması',
            source='program_service.validate_department', observed=dict(department_id=dept.id),
            errors=[f'{dept.name}: {e}' for e in issues]))
        if scope.status == 'required':
            sub = db.scalar(select(Submission).where(
                Submission.department_id == dept.id, Submission.period_id == period_id))
            decision = db.scalar(select(SubmissionEvent).where(
                SubmissionEvent.submission_id == sub.id, SubmissionEvent.event_type == 'approve',
                SubmissionEvent.revision == sub.revision).order_by(SubmissionEvent.id.desc())) if sub else None
            checks.append(dict(id=f'approval:{dept.id}', label=f'{dept.name}: Strateji onayı',
                source='Submission.status / submission_decision',
                observed=dict(submission=record(sub) if sub else None,
                    approval_event_id=decision.id if decision else None,
                    approver=decision.actor.full_name if decision and decision.actor else None,
                    approver_id=decision.actor_user_id if decision else None),
                errors=[] if sub and sub.status == 'approved' else [f'{dept.name}: onay eksik.']))
    for model, key, label, error in (
        (ReportSection, 'sections', 'Kitabın genel bilgi bölümleri', 'Kitabın genel bilgi bölümleri hazırlanmalı.'),
        (OfficialActivity, 'catalogue', 'Sorumlu harcama birimleri kataloğu', 'Sorumlu harcama birimleri kataloğu hazırlanmalı.'),
    ):
        records = rows(db, model, period_id)
        checks.append(dict(id=key, label=label, source=f'{model.__name__} / publication_checks',
                           observed=dict(record_ids=[r.id for r in records]), errors=[] if records else [error]))
    for index, subtotal in enumerate(cost_reconciliation(db, period_id)):
        checks.append(dict(id=f'subtotal:{index}', label=f"{subtotal['path']} / {subtotal['year']}: maliyet ara toplamı",
            source='program_service.cost_reconciliation / ActivityCostValue.source_amount',
            observed=subtotal, errors=subtotal['errors'], warnings=subtotal['warnings']))
    return checks


@structure_read_scope
def book_snapshot(db, period_id):
    period = db.get(ReportingPeriod, period_id)
    departments = period_departments(db, period_id)
    snapshots = department_snapshots(db, period_id, departments)
    snapshots.sort(key=lambda d: ((d['scope'] or {}).get('position',0),d['department_id']))
    catalogue = []
    responsibilities = defaultdict(list)
    for oid, did in db.execute(select(ActivityResponsibility.official_activity_id,
            ActivityResponsibility.department_id).join(OfficialActivity).where(OfficialActivity.period_id == period_id)):
        responsibilities[oid].append(did)
    for item in rows(db, OfficialActivity, period_id):
        item_data = record(item)
        item_data['departments'] = responsibilities[item.id]
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


def validate_department_snapshot(content, period_id, department_id):
    """Run the same business rules on frozen content only; never query live rows."""
    from types import SimpleNamespace as Row
    from decimal import InvalidOperation
    try:
        context = content['validation_context']
        if context['version'] != 'department-validation-v1' or context['period_id'] != period_id or context['department_id'] != department_id or content['department_id'] != department_id:
            raise ValueError('scope')
        def hydrate(data, numeric=()):
            data = dict(data)
            for key in numeric:
                value = data[key]
                if value is not None:
                    if not isinstance(value, (str,int)) or isinstance(value,bool):raise ValueError('number')
                    data[key] = Decimal(value)
                    if not data[key].is_finite():raise ValueError('number')
            return Row(**data)
        cards = [hydrate(c) for c in content['cards']]
        by_card = {c.id:c for c in cards}
        indicators=[];activities=[]
        for data in content['indicators']:
            row=hydrate(data);row.values=[hydrate(v,('value',)) for v in data['values']];row.card=by_card.get(row.card_id)
            indicators.append(row)
        links_by_activity=defaultdict(list)
        for data in content['activities']:
            row=hydrate(data);row.cost_values=[hydrate(v,('amount',)) for v in data['costs']];row.card=by_card.get(row.card_id)
            activities.append(row)
            links_by_activity[row.id]=[Row(official_activity_id=oid) for oid in data['official_ids']]
        economics=[hydrate(v,('amount',)) for v in content['economics']]
        personnel=[hydrate(v,('amount',)) for v in content['department_costs']]
        subprograms={r['id']:hydrate(r) for r in context['subprograms']}
        officials={r['id']:hydrate(r) for r in context['officials']}
        scope=hydrate(content['scope']) if content['scope'] else None
        # Fail closed on malformed identities; these are source integrity checks, not new business policy.
        scoped=cards+indicators+activities+economics+personnel+([scope] if scope else [])
        if any(r.period_id!=period_id or r.department_id!=department_id for r in scoped):raise ValueError('scope')
        if any(r.card_id and r.card is None for r in indicators+activities):raise ValueError('card')
        return _validate_department_records(period_id,department_id,content['period'],scope,indicators,activities,
            cards,economics,personnel,links_by_activity,officials,set(context['responsible_ids']),subprograms)
    except (KeyError,TypeError,ValueError,AttributeError,InvalidOperation):
        return ['Paketin sabit kapsam / alan bilgisi eksik veya geçersiz. Geçerli kaynakla yeni paket oluşturun; kimlik ve mali alanları kontrol edin.'], []


def _approved_book_mapping_view(current, source, audits, load_id, subprogram_ids):
    """Replay only recorded mappings, then restore the loader's hash view.

    This mutates the serialized copy, never Activity rows. The sealed applied_hash
    remains the final proof of the reconstructed baseline, including row IDs.
    """
    from types import SimpleNamespace
    from .import_service import _link_subprograms, _membership_block_index

    cards = current['cards']  # loader creates cards/activities in source order
    items = source['activities']
    if len(current['activities']) != len(items) or len(cards) != len(source['blocks']):
        raise ValueError('load shape')
    loaded_links = _link_subprograms(
        [SimpleNamespace(id=c['subprogram_id']) for c in cards], len(items), items, source['blocks'])
    states = {}
    for row, item, link in zip(current['activities'], items, loaded_links):
        if link is not None:
            continue  # Book memberships must never acquire a mapping exception.
        index = _membership_block_index(item, source['blocks'])
        card_id = (cards[index]['id'] if index is not None else
                   cards[0]['id'] if len(cards) == 1 and 'source_memberships' not in item else None)
        states[row['id']] = dict(row=row, load_card=card_id, card=card_id,
                                 subprogram=None, batch=None, touched=False)
    allowed_audits = set()
    batches = {}
    for audit in audits:
        if audit.id <= load_id:
            continue
        if audit.action in {'activity_mapping', 'activity_mapping_csv'}:
            if audit.entity_type != 'activity' or audit.entity_id not in states:
                continue
            state = states[audit.entity_id]
            parts = [part.split('=') for part in audit.details.split(';')]
            details = dict(parts)
            csv = audit.action == 'activity_mapping_csv'
            if len(parts) != len(details) or set(details) != ({'batch', 'subprogram_id'} if csv else {'subprogram_id'}):
                raise ValueError('mapping audit')
            subprogram = int(details['subprogram_id'])
            if subprogram not in subprogram_ids:
                raise ValueError('mapping period')
            batch = details.get('batch')
            if csv:
                if (len(batch) != 16 or any(c not in '0123456789abcdef' for c in batch)
                        or state['subprogram'] is not None):
                    raise ValueError('mapping batch')
                batches.setdefault(batch, []).append((audit.entity_id, subprogram))
            card = next((c for c in cards if c['id'] == state['card']), None)
            if card and card['subprogram_id'] != subprogram:
                state['card'] = None
            state.update(subprogram=subprogram, batch=batch, touched=True)
            allowed_audits.add(audit.id)
        elif audit.action == 'activity_mapping_csv_revert' and audit.entity_type == 'mapping_batch':
            details = dict(part.split('=', 1) for part in audit.details.split(';'))
            reverted = batches.pop(details['batch'], [])
            for activity_id, target in reverted:
                state = states[activity_id]
                if state['subprogram'] != target:
                    raise ValueError('revert target')
                # The revert route clears both fields, even a retained load card.
                state.update(subprogram=None, card=None, batch=None)
            if reverted:
                allowed_audits.add(audit.id)
    mapped_count = 0
    active_batches = set()
    for state in states.values():
        if not state['touched']:
            continue
        row = state['row']
        if (row['subprogram_id'], row['card_id']) != (state['subprogram'], state['card']):
            raise ValueError('unrecorded mapping change')
        if state['subprogram'] is not None:
            mapped_count += 1
            if state['batch']:
                active_batches.add(state['batch'])
        row.update(subprogram_id=None, card_id=state['load_card'])
    return allowed_audits, mapped_count, active_batches


def approved_book_provenance(db, period_id):
    """Read existing CLI provenance; fail closed without establishing a new baseline.

    ImportBatch.applied_hash predates the first-load catalogue and 2026 scopes.
    Recreate that hash view only after checking those additions against their
    durable source/audit records. User membership is unrelated to PP content.
    """
    import hashlib
    from .models import ImportBatch, Publication, SubProgramScope
    from .import_service import _serialize_department_state, _clean
    from .first_load_sources import FIRST_LOAD_BOOKS, recognized_source, active_first_loads, READ_ONLY_AUDITS
    period = db.get(ReportingPeriod, period_id)
    if not period or period.year not in FIRST_LOAD_BOOKS:
        return None
    if db.scalar(select(Publication.id).where(Publication.period_id == period_id)):
        return None
    loads = active_first_loads(db, period_id)
    if loads is None or len(loads) != {2026: 33, 2027: 34}[period.year]:
        return None
    try:
        source = recognized_source(period.year, json.loads(loads[0][0].details)['book_sha256'])
        if source is None:
            return None
        filename, book_sha256 = source
        departments = {}
        sections = {}
        expected_programs = set()
        expected_subprograms = {}
        mapping_audits = db.scalars(select(AuditLog).where(AuditLog.id > loads[0][0].id,
            AuditLog.action.in_(['activity_mapping', 'activity_mapping_csv', 'activity_mapping_csv_revert']))
            .order_by(AuditLog.id)).all()
        subprogram_ids = set(db.scalars(select(SubProgram.id).where(SubProgram.period_id == period_id)))
        allowed_mapping_audits = set()
        mapping_departments = defaultdict(set)
        mapped_count = 0
        mapping_batches = set()
        for audit, batch in loads:
            proof = json.loads(audit.details)
            payload = json.loads(batch.payload_json)
            snapshot = json.loads(batch.snapshot_json)
            did = proof['department_id']
            if (did in departments or proof['year'] != period.year
                    or proof['book_sha256'] != book_sha256 or batch.filename != filename
                    or batch.status != 'applied' or not batch.applied_at or not batch.applied_hash
                    or payload['summary']['source_years'] != [period.year]
                    or len(payload['departments']) != 1):
                return None
            source = payload['departments'][0]
            current = _serialize_department_state(db, did, period_id)
            if not current['department_name'] or current['department_name'] != source['name']:
                return None
            # The pre-import snapshot records existing users before the CLI ran.
            previous = next((d for d in snapshot['departments'] if d['department_id'] == did), {})
            current['user_ids'] = previous.get('user_ids', [])
            if previous.get('cards') or previous.get('activities') or previous.get('indicators'):
                return None
            if period.year == 2026:
                scope = current['scope']
                display = payload['book_department_names'][source['name']]
                expected = dict(period_id=period_id, department_id=did, position=0,
                    display_name=display if display != current['department_name'] else '',
                    budget_code=None, active_from=None, active_to=None, status='required', reason='')
                if len(scope) != 1 or {k:v for k,v in scope[0].items() if k != 'id'} != expected:
                    return None
                current['scope'] = previous.get('scope', [])
            departments[did] = audit.id
            # Both first-load catalogue implementations add links after applied_hash.
            current['catalogue_links'] = previous.get('catalogue_links', [])
            allowed, count, batches = _approved_book_mapping_view(
                current, source, mapping_audits, audit.id, subprogram_ids)
            allowed_mapping_audits.update(allowed)
            for mapping_id in allowed:
                mapping_departments[mapping_id].add(did)
            mapped_count += count
            mapping_batches.update(batches)
            raw = json_dumps([current], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            current_hash = hashlib.sha256(raw.encode()).hexdigest()
            created_sections = snapshot.get('created_sections', [])
            if 'created_sections' in snapshot:
                raw = json_dumps([current_hash, created_sections], ensure_ascii=False, sort_keys=True)
                current_hash = hashlib.sha256(raw.encode()).hexdigest()
            if current_hash != batch.applied_hash:
                return None
            sections.update({row['id']:row for row in created_sections})
            for block in source['blocks']:
                program = _clean(block.get('program')) or 'Program adı belirtilmedi'
                subprogram = _clean(block.get('subprogram')) or 'Alt program adı belirtilmedi'
                expected_programs.add(program)
                fields = expected_subprograms.setdefault((program, subprogram), ['', ''])
                for index, field in enumerate(('rationale', 'goal')):
                    if not fields[index]:
                        fields[index] = _clean(block.get(field))
        if {row.name for row in rows(db, Program, period_id)} != expected_programs:
            return None
        programs = {row.id:row.name for row in rows(db, Program, period_id)}
        actual_subprograms = {(programs[row.program_id], row.name):[row.rationale, row.goal]
                             for row in rows(db, SubProgram, period_id)}
        if actual_subprograms != expected_subprograms:
            return None
        if {row.id:record(row) for row in rows(db, ReportSection, period_id)} != sections:
            return None
        scopes = rows(db, DepartmentScope, period_id)
        if {s.department_id for s in scopes} != (set(departments) if period.year == 2026 else set()):
            return None
        if db.scalar(select(SubProgramScope.scope_id).where(SubProgramScope.scope_id.in_([s.id for s in scopes]))):
            return None
        # Last catalogue audit before completion holds the cumulative membership.
        last_load = loads[-1][0].id
        catalogue = rows(db, OfficialActivity, period_id)
        if not catalogue:
            return None
        originals = {}
        links = {}
        # D-466: a verified 2027 replacement rebuilt the catalogue. Catalogue
        # audits of the superseded ONAYLI load describe deleted rows; read only
        # those written after the last superseded load marker.
        active_ids = {a.id for a, _ in loads}
        floor = max((a.id for a in db.scalars(select(AuditLog).join(ImportBatch,
            ImportBatch.id == AuditLog.entity_id).where(AuditLog.action == 'first_load_department',
            AuditLog.entity_type == 'import_batch', ImportBatch.period_id == period_id))
            if a.id not in active_ids), default=0)
        for audit in db.scalars(select(AuditLog).where(AuditLog.id <= last_load, AuditLog.id > floor,
                AuditLog.action.in_(['catalogue_create', 'catalogue_link'])).order_by(AuditLog.id)):
            data = json.loads(audit.details)
            if audit.action == 'catalogue_create' and data.get('source'):
                originals[audit.entity_id] = data
            elif audit.action == 'catalogue_link' and (data.get('source') or {}).get('kind') in {
                    'first_load_book_membership', 'first_load_2026_exact_name'}:
                links[audit.entity_id] = data['official_ids']
        for item in catalogue:
            original = originals.get(item.id)
            if not original or any(getattr(item, key) != value for key,value in original['values'].items()):
                return None
            ids = set(db.scalars(select(ActivityResponsibility.department_id).where(
                ActivityResponsibility.official_activity_id == item.id)))
            if ids != set(original['department_ids']):
                return None
        catalogue_ids = {item.id for item in catalogue}
        # Catch deleted catalogue rows too, including entries with no local link.
        expected_catalogue_ids = {key for key,value in originals.items()
                                  if set(value['department_ids']) & departments.keys()
                                  and db.scalar(select(OfficialActivity.id).where(
                                      OfficialActivity.id == key, OfficialActivity.period_id != period_id)) is None}
        if catalogue_ids != expected_catalogue_ids:
            return None
        activities = rows(db, Activity, period_id)
        for activity in activities:
            actual = set(db.scalars(select(ActivityCatalogueLink.official_activity_id).where(
                ActivityCatalogueLink.activity_id == activity.id)))
            if actual != set(links.get(activity.id, [])):
                return None
        for model in (ReportCard, Indicator, Activity, DepartmentCostValue, EconomicValue):
            if any(row.department_id not in departments for row in rows(db, model, period_id)):
                return None
        if any(row.code or row.position or row.contract_bound for row in activities):
            return None
        # Hashes detect current differences; audit also detects edits later undone.
        owners = {}
        for model, singular in ((ReportCard, 'report_card'), (Indicator, 'indicator'),
                (Activity, 'activity'), (DepartmentCostValue, 'department_cost_value'),
                (EconomicValue, 'economic_value'), (DepartmentScope, 'department_scope'),
                (Program, 'program'), (SubProgram, 'subprogram'), (ReportSection, 'report_section'),
                (OfficialActivity, 'official_activity'), (ImportBatch, 'import_batch')):
            for row in rows(db, model, period_id):
                cutoff = departments.get(getattr(row, 'department_id', None), last_load)
                for name in (model.__tablename__, singular):
                    owners[(name, row.id)] = cutoff
        for singular, model in [('indicator_value', IndicatorValue), ('activity_cost_value', ActivityCostValue)]:
            parent = Indicator if model is IndicatorValue else Activity
            field = model.indicator_id if model is IndicatorValue else model.activity_id
            for child, owner in db.execute(select(model, parent).join(parent, field == parent.id)
                    .where(parent.period_id == period_id)):
                owners[(singular, child.id)] = departments[owner.department_id]
                owners[(model.__tablename__, child.id)] = departments[owner.department_id]
        # The mapping routes also trigger CIV-025's department authorship hook.
        # Audit timestamps/adjacency cannot prove which write caused that row.
        # PostgreSQL xmin ties it to the recorded mapping's inserting transaction;
        # scope and actor must match too. Other databases fail closed here.
        authorship_transactions = set()
        audit_transactions = {}
        if allowed_mapping_audits and db.get_bind().dialect.name == 'postgresql':
            from sqlalchemy import literal_column
            audit_transactions = {aid: (actor, transaction) for aid, actor, transaction in db.execute(
                select(AuditLog.id, AuditLog.user_id, literal_column('xmin::text')).where(
                    AuditLog.id.in_(allowed_mapping_audits) | (
                        (AuditLog.action == 'pp_data_change') &
                        (AuditLog.entity_type == 'department') &
                        AuditLog.entity_id.in_(departments) &
                        (AuditLog.details == f'period_id={period_id}'))))}
            # A dump/restore can reinsert unrelated audit rows in one transaction.
            # Such a transaction cannot establish mapping-only authorship proof.
            mapping_transactions = {audit_transactions[aid][1] for aid in allowed_mapping_audits}
            ambiguous_transactions = set()
            for event, transaction in db.execute(select(AuditLog, literal_column('xmin::text')).where(
                    literal_column('xmin::text').in_(mapping_transactions))):
                if event.id not in allowed_mapping_audits and not (
                        event.action == 'pp_data_change' and event.entity_type == 'department'
                        and event.entity_id in departments and event.details == f'period_id={period_id}'):
                    ambiguous_transactions.add(transaction)
            for mapping_id, dids in mapping_departments.items():
                actor, transaction = audit_transactions[mapping_id]
                if actor is not None and transaction not in ambiguous_transactions:
                    authorship_transactions.update((did, actor, transaction) for did in dids)
        for audit in db.scalars(select(AuditLog).where(AuditLog.id > min(departments.values()))):
            if (audit.action, audit.entity_type) in READ_ONLY_AUDITS:
                continue
            if audit.action == 'first_load_department':
                continue
            # active_first_loads already validated this single atomic receipt.
            if (audit.action == 'approved_book_2027_replaced'
                    and audit.entity_type == 'reporting_period' and audit.entity_id == period_id):
                continue
            if audit.id in allowed_mapping_audits:
                continue
            if (audit.action == 'pp_data_change' and audit.entity_type == 'department'
                    and audit.details == f'period_id={period_id}'
                    and (audit.entity_id, *audit_transactions.get(audit.id, (None, None)))
                        in authorship_transactions):
                continue
            cutoff = owners.get((audit.entity_type, audit.entity_id))
            if audit.entity_type in {'department', 'departments'} and audit.entity_id in departments:
                cutoff = departments[audit.entity_id]
            if audit.entity_type in {'reporting_periods', 'reporting_period'} and audit.entity_id == period_id:
                cutoff = last_load
            if cutoff is not None and audit.id > cutoff:
                return None
        return dict(basis='approved_book', book_sha256=book_sha256,
                    load_reference=[dict(audit_id=a.id, batch_id=b.id) for a,b in loads],
                    activity_mapping=dict(count=mapped_count, batch_ids=sorted(mapping_batches)))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
