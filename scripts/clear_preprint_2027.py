"""CIV-058: fail-closed pre-print removal; CLI lives in first_load_live.py."""
from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from scripts.first_load_live import HEAD, LOCK, MARKER, Refusal, require_head

ACTION = 'preprint_2027_cleared'
CONFIRMATION = '2027 ON BASKI TASLAGINI SIL'
# D-131 / owner's 20 October inventory. Never absorb a later import automatically.
BATCH_STATES = {3: 'preview', 4: 'applied', 5: 'applied', 6: 'reverted',
                7: 'applied', 8: 'applied', 9: 'applied', 10: 'applied'}
FIELDS = ('indicator_values', 'indicators', 'activity_cost_values', 'activity_catalogue_links',
          'activities', 'department_cost_values', 'submission_events', 'submissions', 'subprogram_scopes', 'department_scopes')
CATALOGUE = ('programs', 'subprograms', 'official_activities', 'activity_responsibilities')


def refuse(reason):
    raise Refusal(reason + '; 0 satır yazıldı. Sorumluya bildirin; korumayı aşmayın.')


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def catalogue_state(db, period_id):
    from app.models import Program, SubProgram, OfficialActivity, ActivityResponsibility
    result = {}
    for model in (Program, SubProgram, OfficialActivity, ActivityResponsibility):
        table = model.__table__
        condition = (model.official_activity_id.in_(select(OfficialActivity.id).where(
            OfficialActivity.period_id == period_id)) if model is ActivityResponsibility
            else model.period_id == period_id)
        rows = [dict(row) for row in db.execute(select(table).where(condition)).mappings()]
        result[table.name] = dict(count=len(rows), sha256=digest(sorted(rows, key=encoded)))
    return result


def batch_state(batch):
    return {c.name: getattr(batch, c.name) for c in batch.__table__.columns if c.name != 'status'}


def clearance(db, period_id):
    """Only the loader calls this: retained catalogue/batches need this exact receipt."""
    from app.models import AuditLog, ImportBatch
    logs = db.scalars(select(AuditLog).where(AuditLog.action == ACTION,
        AuditLog.entity_type == 'reporting_period', AuditLog.entity_id == period_id)).all()
    if not logs:
        return False
    if len(logs) != 1:
        refuse('2027 temizleme denetim izi tekil değil')
    try:
        details = json.loads(logs[0].details)
        batches = db.scalars(select(ImportBatch).where(ImportBatch.period_id == period_id)).all()
        actual = {str(b.id): digest(batch_state(b)) for b in batches}
        valid = (details['version'] == 2 and details['decision'] == 'D-135' and details['year'] == 2027
                 and details['head'] == HEAD and set(actual) == set(map(str, BATCH_STATES))
                 and all(b.status == 'superseded' for b in batches)
                 and details['batches'] == actual
                 and details['retained_catalogue'] == catalogue_state(db, period_id))
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        refuse('2027 temizleme sonrası paket/katalog veya denetim izi değişmiş')
    return True


def base_context(db, organization_id, actor_id):
    from app.models import Organization, User, ReportingPeriod, AuditLog
    require_head(db)
    orgs = db.scalars(select(Organization)).all()
    if len(orgs) != 1 or orgs[0].id != organization_id:
        refuse('Tek kurum ve doğru --organization-id gerekli')
    actor = db.get(User, actor_id)
    if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
        refuse('--actor-id etkin Strateji/yönetici kullanıcısı olmalıdır')
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
    if not period or period.status not in {'draft', 'active'} or period.template_status != 'verified':
        refuse('2027 dönemi açık ve şablonu doğrulanmış olmalıdır')
    if db.scalar(select(AuditLog.id).where(AuditLog.action == MARKER).limit(1)):
        refuse('first_load_department ilk yükleme işareti var; ön baskı temizlenemez')
    return period


def audit_guard(db, period_id, cutoff, terminal_batch_id):
    """Unknown/deleted/department-only content targets fail closed, never guessed safe."""
    from app import models as m
    safe_user = {'login', 'self_password_change', 'user_create', 'user_activate',
                 'user_deactivate', 'user_password_reset', 'user_change',
                 'user_position_change', 'user_permission_change', 'user_is_active_change',
                 'user_can_submit_change',
                 'user_bulk_create_item', 'user_bulk_create', 'user_bulk_create_revert'}
    models = {'indicator': m.Indicator, 'indicators': m.Indicator,
              'activity': m.Activity, 'activities': m.Activity,
              'submission': m.Submission, 'report_card': m.ReportCard,
              'publication': m.Publication, 'report_section': m.ReportSection,
              'import_batch': m.ImportBatch, 'department_scope': m.DepartmentScope,
              'program': m.Program, 'subprogram': m.SubProgram,
              'economic_value': m.EconomicValue, 'economic_values': m.EconomicValue,
              'department_cost_values': m.DepartmentCostValue}
    for log in db.scalars(select(m.AuditLog).where(m.AuditLog.created_at >= cutoff)):
        if log.entity_type == 'department' or log.action == 'personnel_cost_update':
            refuse('Son ön baskı uygulamasından sonra personel maliyeti veya müdürlük denetim kaydı var')
        if (log.action in safe_user and log.entity_type in {'user', 'user_batch'}):
            continue
        if ((log.action == 'operations_backup_export' and log.entity_type == 'database')
                or (log.action == 'period_activate' and log.entity_type == 'reporting_period')
                or log.action == 'civ025_tracking_started'):
            continue
        # The terminal import's own audit is commonly a few milliseconds later.
        if (log.action == 'data_import_apply' and log.entity_type == 'import_batch'
                and log.entity_id == terminal_batch_id
                and log.created_at <= cutoff + timedelta(seconds=1)):
            continue
        model = models.get(log.entity_type)
        obj = db.get(model, log.entity_id) if model and log.entity_id else None
        if obj is not None and obj.period_id != period_id:
            continue
        if log.entity_type in {'indicator_value', 'indicator_values'}:
            obj = db.get(m.IndicatorValue, log.entity_id)
            parent = db.get(m.Indicator, obj.indicator_id) if obj else None
            if parent and parent.period_id != period_id:
                continue
        if log.entity_type == 'activity_cost_values':
            obj = db.get(m.ActivityCostValue, log.entity_id)
            parent = db.get(m.Activity, obj.activity_id) if obj else None
            if parent and parent.period_id != period_id:
                continue
        refuse('Son ön baskı uygulamasından sonra 2027 PP içerik düzenlemesi veya dönemi belirsiz denetim kaydı var')


def number(value, money=False):
    quantum = Decimal('.01') if money else Decimal('.000001')
    return None if value is None else str(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP).normalize())


def value_signature(row, money=False):
    amount = row.get('amount' if money else 'value')
    return (int(row['year']), row.get('kind', row.get('value_kind')),
            row.get('funding_type', 'total') if money else '',
            number(amount, money), row.get('raw_text', ''), row.get('state', 'verified'))


def source_values(rows, money=False):
    result, seen = [], set()
    for row in rows:
        year, kind = row.get('year'), row.get('kind')
        fund = row.get('funding_type', 'total') if money else ''
        amount = row.get('amount' if money else 'value')
        if (year is None or not kind or
                (amount is None and row.get('state') not in {'needs_review', 'not_applicable'})):
            continue
        key = (int(year), kind, fund)
        if key in seen:
            continue
        seen.add(key)
        row = dict(row, raw_text=row.get('raw_text', str(amount)))
        result.append(value_signature(row, money))
    return sorted(result, key=encoded)


def row_values(rows, money=False):
    return sorted((value_signature({c.name: getattr(v, c.name) for c in v.__table__.columns},
                                   money) for v in rows), key=encoded)


def archived_payload(payload):
    """Fill only the old importer's documented defaults, without editing the batch.

    Current preview review helpers require state. Legacy Word payloads predate
    that field; the write loops used verified, str(amount) for indicator/activity
    raw text, and empty raw text for personnel. Explicit fields stay untouched.
    """
    payload = deepcopy(payload)
    for department in payload['departments']:
        for block in department.get('blocks', []):
            for indicator in block.get('indicators', []):
                for row in indicator.get('values', []):
                    row.setdefault('state', 'verified')
                    row.setdefault('raw_text', str(row.get('value')))
        for activity in department.get('activities', []):
            for row in activity.get('costs', []):
                row.setdefault('state', 'verified')
                row.setdefault('raw_text', str(row.get('amount')))
        for row in department.get('personnel', []):
            row.setdefault('state', 'verified')
            row.setdefault('raw_text', '')
    return payload


def personnel_signature(row):
    return (int(row['year']), str(row.get('kind', row.get('value_kind'))),
            row.get('category', 'personnel_sgk'), number(row.get('amount'), True),
            row.get('raw_text', ''), row.get('state', 'verified'))


def source_personnel(rows):
    """Exactly the importer's seen_personnel loop: first eligible (year, kind)."""
    signatures, seen_personnel = [], set()
    for row in rows:
        key = (row.get('year'), row.get('kind'))
        amount = row.get('amount')
        if (key[0] is None or not key[1]
                or (amount is None and row.get('state') not in {'needs_review', 'not_applicable'})
                or key in seen_personnel):
            continue
        seen_personnel.add(key)
        signatures.append(personnel_signature(dict(row, category='personnel_sgk')))
    return Counter(signatures)


def check_personnel(db, did, source, period_id):
    from app.models import DepartmentCostValue
    rows = db.scalars(select(DepartmentCostValue).where(
        DepartmentCostValue.period_id == period_id, DepartmentCostValue.department_id == did)).all()
    actual = Counter(personnel_signature({c.name: getattr(row, c.name)
                                          for c in row.__table__.columns}) for row in rows)
    if actual != source_personnel(source.get('personnel', [])):
        refuse('2027 personel/SGK maliyet satırı arşiv paket planına izlenemiyor (eksik/fazla/değişmiş)')
    return [row.id for row in rows]


def check_department(db, did, source, period_id):
    """Compare full legacy content, multiplicities and child values with the archived plan."""
    from app.models import (Indicator, IndicatorValue, Activity, ActivityCostValue,
                            Program, SubProgram)
    from app.import_service import _clean
    subs = {sp.id: (_clean(p.name), _clean(sp.name)) for sp, p in db.execute(
        select(SubProgram, Program).join(Program).where(SubProgram.period_id == period_id,
                                                       Program.period_id == period_id))}
    expected_indicators = []
    for block in source['blocks']:
        membership = (_clean(block.get('program', '')) or 'Program adı belirtilmedi',
                      _clean(block.get('subprogram', '')) or 'Alt program adı belirtilmedi')
        for item in block.get('indicators', []):
            expected_indicators.append((
                membership, *(_clean(item.get(k, '')) for k in (
                    'name', 'unit', 'explanation', 'calculation_method', 'data_source')),
                source_values(item.get('values', []))))
    actual_indicators = []
    indicators = db.scalars(select(Indicator).where(Indicator.period_id == period_id,
                                                   Indicator.department_id == did)).all()
    for ind in indicators:
        if (ind.card_id is not None or ind.persistent_indicator_id is not None
                or ind.code or ind.position or ind.status != 'draft' or ind.subprogram_id not in subs):
            refuse('2027 gösterge satırı ön baskı planına izlenemiyor')
        values = db.scalars(select(IndicatorValue).where(IndicatorValue.indicator_id == ind.id)).all()
        actual_indicators.append((subs[ind.subprogram_id], ind.name, ind.unit, ind.explanation,
                                  ind.calculation_method, ind.data_source, row_values(values)))
    memberships = list(dict.fromkeys(
        (_clean(b.get('program', '')) or 'Program adı belirtilmedi',
         _clean(b.get('subprogram', '')) or 'Alt program adı belirtilmedi') for b in source['blocks']))
    membership = memberships[0] if len(memberships) == 1 else None
    expected_activities = [
        (membership, _clean(a.get('name', '')) or _clean(a.get('official_name', '')) or 'Faaliyet adı belirtilmedi',
         _clean(a.get('explanation', '')), source_values(a.get('costs', []), True))
        for a in source.get('activities', [])]
    activities = db.scalars(select(Activity).where(Activity.period_id == period_id,
                                                   Activity.department_id == did)).all()
    actual_activities = []
    for act in activities:
        if act.card_id is not None or act.code or act.position or act.contract_bound:
            refuse('2027 faaliyet satırı ön baskı planına izlenemiyor')
        if act.subprogram_id is not None and act.subprogram_id not in subs:
            refuse('2027 faaliyet alt programı dönem dışına bağlı')
        values = db.scalars(select(ActivityCostValue).where(ActivityCostValue.activity_id == act.id)).all()
        for value in values:
            # CIV-019 added source columns to old rows. Accept only inert defaults
            # or the exact source amount, never a subsequent resolution.
            if (value.source_resolution_json not in ('', '{}')
                    or value.source_amount not in (None, value.amount)
                    or value.source_raw_text not in ('', value.raw_text)):
                refuse('2027 faaliyet kaynak kararı ön baskı planına izlenemiyor')
        actual_activities.append((subs.get(act.subprogram_id), act.name, act.explanation,
                                  row_values(values, True)))
    if (Counter(map(encoded, actual_indicators)) != Counter(map(encoded, expected_indicators))
            or Counter(map(encoded, actual_activities)) != Counter(map(encoded, expected_activities))):
        refuse('2027 gösterge/faaliyet veya değer satırı son ön baskı paket planına izlenemiyor')
    return indicators, activities


def build_plan(db, organization_id, actor_id):
    from app import models as m
    from app.import_service import build_department_plan, department_key, _clean
    period = base_context(db, organization_id, actor_id)
    pid = period.id
    for model, label in ((m.ReportCard, 'rapor kartı'), (m.EconomicValue, 'ekonomik değer'),
                         (m.Publication, 'yayın')):
        if db.scalar(select(model.id).where(model.period_id == pid).limit(1)):
            refuse('2027 ' + label + ' var; ön baskı temizlenemez')
    if db.scalar(select(m.DepartmentCostValue.id).where(m.DepartmentCostValue.period_id == pid,
            m.DepartmentCostValue.category != 'personnel_sgk').limit(1)):
        refuse('2027 müdürlük maliyetinde personnel_sgk dışında kategori var')
    submissions = db.scalars(select(m.Submission).where(m.Submission.period_id == pid)).all()
    if any(s.status != 'draft' for s in submissions):
        refuse('2027 teslim kaydı taslak (draft) değil')
    if clearance(db, pid):
        # A receipt is never a licence to delete rows introduced after clearing.
        for model in (m.Indicator, m.Activity, m.DepartmentCostValue, m.Submission, m.SubmissionEvent, m.DepartmentScope):
            if db.scalar(select(model).where(model.period_id == pid).limit(1)):
                refuse('Temizleme sonrası yeni 2027 satırı var')
        return period, dict(mode='clear-preprint-plan', counts={k: 0 for k in FIELDS},
                            departments=[], batches=[], already_cleared=True), {}
    batches = db.scalars(select(m.ImportBatch).where(m.ImportBatch.period_id == pid)).all()
    if {b.id: b.status for b in batches} != BATCH_STATES:
        refuse('2027 ön baskı paket envanteri D-131 ile uyuşmuyor (3–10)')
    if (any(b.created_at.date() != date(2026, 9, 21) for b in batches)
            or len({b.created_by for b in batches}) != 1 or batches[0].created_by is None):
        refuse('Ön baskı paket oluşturma zamanı/aktörü onaylı envanterle uyuşmuyor')
    applied = sorted((b for b in batches if b.status == 'applied'),
                     key=lambda b: (b.applied_at or b.created_at, b.id))
    if any(b.applied_at is None or b.applied_at.date() != date(2026, 9, 21)
           or b.created_at.date() != date(2026, 9, 21) for b in applied):
        refuse('Ön baskı paket uygulama zamanı onaylı 21 Eylül envanteriyle uyuşmuyor')
    audit_guard(db, pid, applied[-1].applied_at, applied[-1].id)
    # Rebuild archived plans without any write service or trial writes.
    sources, provenance, catalogue_sources = {}, {}, []
    for batch in applied:
        phase = 'snapshot'
        try:
            snapshot = json.loads(batch.snapshot_json)
            affected = {int(d['department_id']) for d in snapshot['departments']}
            affected.update(int(x) for x in snapshot['created_department_ids'])
            phase = 'arşiv planı'
            plan = build_department_plan(db, archived_payload(json.loads(batch.payload_json)),
                                         json.loads(batch.decisions_json or '[]'))
            if plan['unresolved'] or plan['unresolved_conflicts']:
                raise ValueError
            phase = 'müdürlük eşleştirmesi'
            mapping = {department_key(x['source_name']): x for x in plan['mappings']}
            matched = set()
            for source in plan['parsed']['departments']:
                catalogue_sources.append(source)
                item = mapping[department_key(source['name'])]
                did = item.get('department_id')
                if item['action'] != 'match' or item['confidence'] != 1:
                    raise ValueError
                if did not in affected:
                    continue  # preserve-existing imports did not touch this department
                sources[did], provenance[did] = source, batch.id
                matched.add(did)
            if matched != affected:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            refuse(f'Ön baskı paket #{batch.id} {phase} kökeni doğrulanamadı')
    # All retained period catalogue records must also occur in archived plans.
    programmes, subprogrammes = set(), set()
    for source in catalogue_sources:
        for block in source['blocks']:
            p = (_clean(block.get('program', '')) or 'Program adı belirtilmedi')
            sp = (_clean(block.get('subprogram', '')) or 'Alt program adı belirtilmedi')
            programmes.add(p)
            subprogrammes.add((p, sp))
    programs = db.scalars(select(m.Program).where(m.Program.period_id == pid)).all()
    program_names = {p.id: p.name for p in programs}
    if any(p.name not in programmes for p in programs):
        refuse('2027 program satırı ön baskı planına izlenemiyor')
    for sp in db.scalars(select(m.SubProgram).where(m.SubProgram.period_id == pid)):
        if (program_names.get(sp.program_id), sp.name) not in subprogrammes:
            refuse('2027 alt program satırı ön baskı planına izlenemiyor')
    # The approved legacy plans provide no creation proof for official entries.
    if db.scalar(select(m.OfficialActivity.id).where(m.OfficialActivity.period_id == pid).limit(1)):
        refuse('2027 resmî katalog satırının ön baskı paketinde oluşturulma izi yok')
    if db.scalar(select(m.SubProgramScope).where(
            m.SubProgramScope.subprogram_id.in_(select(m.SubProgram.id).where(
                m.SubProgram.period_id == pid))).limit(1)):
        refuse('2027 alt program kapsam bağlantısı ön baskı planına izlenemiyor')
    ids = {name: [] for name in FIELDS}
    counts, departments = Counter({k: 0 for k in FIELDS}), []
    target_dids = set()
    for model in (m.Indicator, m.Activity, m.DepartmentCostValue, m.Submission, m.DepartmentScope, m.SubmissionEvent):
        target_dids.update(db.scalars(select(model.department_id).where(model.period_id == pid)))
    if target_dids - sources.keys():
        refuse('2027 satırı ön baskı paket müdürlüklerine izlenemiyor')
    # The archived legacy plan/snapshot format carries no creation proof for
    # scopes/catalogue links. Never infer ownership from department membership.
    if db.scalar(select(m.DepartmentScope.id).where(m.DepartmentScope.period_id == pid).limit(1)):
        refuse('2027 kapsam/alt program bağlantısının ön baskı paketinde oluşturulma izi yok')
    # Include every traced department: deleting a whole personnel group cannot
    # hide missing archived rows merely by removing its last live row.
    target_dids.update(sources)
    for did in sorted(target_dids):
        indicators, activities = check_department(db, did, sources[did], pid)
        local = {k: [] for k in FIELDS}
        local['department_cost_values'] = check_personnel(db, did, sources[did], pid)
        local['indicators'] = [i.id for i in indicators]
        local['activities'] = [a.id for a in activities]
        local['indicator_values'] = list(db.scalars(select(m.IndicatorValue.id).where(
            m.IndicatorValue.indicator_id.in_(local['indicators']))))
        local['activity_cost_values'] = list(db.scalars(select(m.ActivityCostValue.id).where(
            m.ActivityCostValue.activity_id.in_(local['activities']))))
        if db.scalar(select(m.ActivityCatalogueLink).where(
                m.ActivityCatalogueLink.activity_id.in_(local['activities'])).limit(1)):
            refuse('2027 katalog bağlantısının ön baskı paketinde oluşturulma izi yok')
        subs = [s for s in submissions if s.department_id == did]
        if any(s.return_note or s.submitted_at or s.reviewed_at or s.revision for s in subs):
            refuse('2027 taslak teslim kaydında ön baskı dışı inceleme geçmişi var')
        local['submissions'] = [s.id for s in subs]
        events = db.scalars(select(m.SubmissionEvent).where(
            (m.SubmissionEvent.period_id == pid) | m.SubmissionEvent.submission_id.in_(local['submissions']))).all()
        events = [e for e in events if e.department_id == did or e.submission_id in local['submissions']]
        # The archived plans contain no workflow-event provenance. Unproven history is
        # deliberately not erased, even if the current submission says draft.
        if events:
            refuse('2027 teslim olayının ön baskı paketinde oluşturulma izi yok')
        for key, values in local.items():
            ids[key].extend(values)
        per_counts = {k: len(v) for k, v in local.items()}
        counts.update(per_counts)
        dept = db.get(m.Department, did)
        departments.append(dict(department_id=did, name=dept.name, batch_id=provenance[did],
                                counts=per_counts))
    # Other period-specific content is outside the legacy pre-print plan.
    allowed = {'reporting_periods', 'import_batches', *CATALOGUE, 'indicators', 'activities',
               'submissions', 'submission_events', 'department_scopes',
               'report_cards', 'economic_values', 'department_cost_values', 'publications'}
    from app.db import Base
    for table in Base.metadata.sorted_tables:
        if 'period_id' in table.c and table.name not in allowed:
            if db.scalar(select(table).where(table.c.period_id == pid).limit(1)):
                refuse('2027 ek dönem satırı ön baskı planına izlenemiyor')
    # Guard indirect/cross-period references too; never rely on a late FK error
    # after starting deletes, and never cascade into another period's history.
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            parent = fk.column.table.name
            if parent not in ids or not ids[parent]:
                continue
            condition = fk.parent.in_(ids[parent])
            if table.name in ids and 'id' in table.c and ids[table.name]:
                condition &= table.c.id.not_in(ids[table.name])
            if db.scalar(select(table).where(condition).limit(1)):
                refuse('2027 satırına ön baskı planı dışında bağlı kayıt var')
    return period, dict(mode='clear-preprint-plan', counts=dict(counts), departments=departments,
                        batches=sorted(BATCH_STATES), already_cleared=False), ids


def execute(engine, *, organization_id, actor_id, apply=False, before_write=None):
    """One READ ONLY snapshot for plan; one locked transaction for the entire apply."""
    from app.models import AuditLog, ImportBatch
    from app.db import Base
    with engine.connect() as connection:
        with Session(connection) as db:
            with db.begin():
                if not apply:
                    db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
                else:
                    if not db.scalar(text('SELECT pg_try_advisory_xact_lock(:key)'), {'key': LOCK}):
                        refuse('Başka ilk yükleme/temizleme çalışıyor')
                    db.execute(text("SET LOCAL lock_timeout = '10s'"))
                    # Cover ordinary application writers and inserts into guard tables,
                    # including audit/batches/catalogue. Lock BEFORE all guard reads.
                    names = ', '.join('"' + t.name + '"' for t in Base.metadata.sorted_tables)
                    db.execute(text('LOCK TABLE ' + names + ' IN SHARE ROW EXCLUSIVE MODE'))
                period, result, ids = build_plan(db, organization_id, actor_id)
                if not apply or result['already_cleared']:
                    return result
                if before_write is not None:
                    before_write()  # Recheck backup freshness after every guard/lock wait.
                for name in FIELDS:
                    table = Base.metadata.tables[name]
                    if ids[name]:
                        removed = db.execute(table.delete().where(table.c.id.in_(ids[name]))).rowcount
                        if removed != result['counts'][name]:
                            refuse('Temizlenecek satır sayısı işlem içinde değişti')
                batches = db.scalars(select(ImportBatch).where(ImportBatch.period_id == period.id)).all()
                for batch in batches:
                    batch.status = 'superseded'
                db.flush()
                receipt = dict(version=2, year=2027, head=HEAD, decision='D-135',
                               counts=result['counts'],
                               batches={str(b.id): digest(batch_state(b)) for b in batches},
                               retained_catalogue=catalogue_state(db, period.id))
                db.add(AuditLog(user_id=actor_id, action=ACTION, entity_type='reporting_period',
                                entity_id=period.id, details=encoded(receipt)))
                result['mode'] = 'clear-preprint-apply'
                return result
