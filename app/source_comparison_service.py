"""Read-only PP source assertions. Import snapshots hold bindings, never balances.

A batch's original payload remains evidence after revert. Only applied batches
participate in comparison. New bindings use owner IDs so renames retain evidence
and deletions cannot accidentally match a different record by its name.
"""
import json
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import select

from .data_importer import _label_key
from .import_service import consolidate_source_departments, department_key, general_section_plan
from .models import (Activity, ActivityCostValue, Department, DepartmentCostValue,
                     EconomicValue, ImportBatch, Indicator, IndicatorValue,
                     ReportSection, User, BudgetOperation, BudgetOperationLine)
from .numbers import format_number, source_cell
from .program_service import (cost_reconciliation, department_snapshot, period_departments,
                              ECONOMIC_CATEGORIES, PROGRAM_GROUPS)
from .structure_service import period_name
from .value_labels import value_kind_label, funding_label

UNKNOWN = 'Bilinmiyor'
LEGACY_TOTALS = 'Kaynak toplamı bu içe aktarmada kaydedilmedi'


def _same(left, right):
    return left is not None and right is not None and Decimal(str(left)) == Decimal(str(right))


def _legacy_bindings(db, batch, payload):
    """Old batches have no ID map. Keep missing/ambiguous ownership explicit.

    Exact, unique department and record names provide a comparison target; no
    table, column, page or source total is reconstructed from current data.
    """
    result = []
    for source in consolidate_source_departments(payload)['departments']:
        departments = [d for d in db.scalars(select(Department))
                       if department_key(d.name) == department_key(source['name'])]
        did = departments[0].id if len(departments) == 1 else None
        def unique(model, name):
            if did is None:
                return None
            found = db.scalars(select(model.id).where(model.period_id == batch.period_id,
                model.department_id == did, model.name == name)).all()
            return found[0] if len(found) == 1 else None
        result.append(dict(department_id=did, source=source,
            indicator_ids=[[unique(Indicator, i['name']) for i in b['indicators']] for b in source['blocks']],
            activity_ids=[unique(Activity, a['name']) for a in source['activities']],
            economic_ids=list(db.scalars(select(EconomicValue.id).where(
                EconomicValue.period_id == batch.period_id, EconomicValue.department_id == did)))))
    return result


def source_comparison(db, period_id, department_id=None):
    departments = {d.id: period_name(db, period_id, d) for d in db.scalars(select(Department))
                   if department_id is None or d.id == department_id}
    # Same calculator as CIV-069; a department's aggregate is restricted before
    # calculation, so programme parent rows cannot expose other departments.
    snapshots = [department_snapshot(db, period_id, d.id) for d in period_departments(db, period_id)
                 if department_id is None or d.id == department_id]
    reconciliation = cost_reconciliation(db, period_id, snapshots=snapshots, include_historical=True)
    records = []
    covered = set()
    source_locations = set()
    actors = {u.id: u.full_name for u in db.scalars(select(User))}
    operation_lines = {}
    for line, operation in db.execute(select(BudgetOperationLine, BudgetOperation).join(
            BudgetOperation).where(BudgetOperation.period_id == period_id).order_by(BudgetOperationLine.id)):
        if department_id is None or line.department_id == department_id:
            operation_lines.setdefault((line.value_table, line.value_id), []).append((line, operation))

    def decision_text(decision):
        if not decision:
            return ''
        return f"{decision.get('reason', '')} · {actors.get(decision.get('actor'), UNKNOWN)} · {decision.get('time') or UNKNOWN}"

    def recorded_change(source_amount, current):
        """Read existing source decisions and append-only budget lines.

        A reason explains only the recorded before→after chain ending at the
        current amount. Unrelated later changes cannot reuse that reason.
        """
        if current is None or source_amount is None:
            return None, ''
        baseline = source_amount
        reasons = []
        history = []
        resolution = json.loads(getattr(current, 'source_resolution_json', '{}') or '{}')
        if resolution.get('reason'):
            history.append(decision_text(resolution))
            if _same(resolution.get('source_total'), baseline):
                baseline = resolution.get('new_total')
                reasons.append(decision_text(resolution))
        for line, operation in operation_lines.get((current.__tablename__, current.id), []):
            proof = dict(reason=f'Bütçe aktarma kararı #{operation.id} / {operation.reference_number}: {operation.reason}',
                actor=operation.actor_id, time=operation.created_at.isoformat())
            history.append(decision_text(proof))
            if _same(line.before, baseline):
                baseline = line.after
                reasons.append(decision_text(proof))
        valid = reasons and _same(baseline, getattr(current, 'amount', None))
        decision = {'reason': ' | '.join(reasons), 'actor': None, 'time': None} if valid else None
        if valid:
            decision['formatted'] = decision['reason']
        return decision, 'Önceki karar güncel tutarı açıklamıyor: ' + ' | '.join(history) if history and not valid else ''

    def add(source, current, *, batch=None, payload=None, did=None, label='', model='', owner=None,
            note='', decision=None, present=None, money=True, department_name=None, incomplete=False):
        source = source or {}
        amount = source.get('amount', source.get('value'))
        stored = getattr(current, 'amount', getattr(current, 'value', None)) if current is not None else None
        state = getattr(current, 'state', 'verified')
        if present is None:
            present = current is not None
        if source.get('state') == 'needs_review':
            status = 'Fark var' if present else 'Kayıtta yok'
        elif amount is None:
            status = 'Kaynakta yok'
        elif not present or stored is None:
            status = 'Fark var' if incomplete and present else 'Kayıtta yok'
        elif _same(amount, stored) and state == 'verified':
            status = 'Eşleşiyor'
        elif decision and state == 'verified':
            status = 'Kararla değişti'
        else:
            status = 'Fark var'
        number = source.get('table_number')
        if batch and number and source.get('row_number') and source.get('column_number'):
            source_locations.add((batch.id, number, source['row_number'], source['column_number']))
        page = (payload or {}).get('source_tables', {}).get(str(number), {}).get('page')
        proof = decision.get('formatted') or decision_text(decision) if decision else ''
        difference = Decimal(str(stored)) - Decimal(str(amount)) if stored is not None and amount is not None else None
        if not note:
            if source.get('state') == 'needs_review':
                note = source.get('issue') or 'Kaynak hücre belirsiz veya doğrulanmamış. Kaynak belgeyi kontrol edin.'
            elif current is not None and (state != 'verified' or stored is None) and amount is not None:
                note = 'Güncel değer eksik veya doğrulanmamış. İlgili gösterge veya maliyet kaydını kontrol edin.'
            elif not batch:
                note = 'Bu güncel kaydın içe aktarmadan kaynak hücresi bulunamadı.'
        records.append(dict(department_id=did, department=departments.get(did, UNKNOWN) if did else department_name or 'Kurum',
            record=label, year=source.get('year'), kind=value_kind_label(source.get('kind', '')),
            funding=funding_label(source.get('funding_type', '')) if source.get('funding_type') else '',
            batch_id=batch.id if batch else None, document=batch.filename if batch else UNKNOWN,
            document_sha256=(payload or {}).get('document_sha256') or UNKNOWN,
            table=number or UNKNOWN, row=source.get('row_number') or UNKNOWN,
            column=source.get('column_number') or UNKNOWN, page=page or UNKNOWN,
            raw_text=source.get('raw_text', ''), source_amount=format_number(amount, money=money),
            stored_amount=format_number(stored, money=money), difference=format_number(difference, money=money),
            status=status, decision=proof, note=note or source.get('issue', ''), model=model, owner_id=owner))
        if current is not None and getattr(current, 'id', None) is not None:
            covered.add((model, current.id))

    def values(source):
        # Retain every repeated source occurrence, including rejected candidates.
        candidates = source.get('candidates') or []
        if not candidates:
            yield source
        else:
            for candidate in candidates:
                for location in candidate['locations']:
                    yield {**source, **location, 'amount': candidate['amount'], 'state': 'verified'}

    batches = db.scalars(select(ImportBatch).where(ImportBatch.period_id == period_id,
        ImportBatch.status == 'applied').order_by(ImportBatch.id)).all()
    notices = []
    for batch in batches:
        payload = json.loads(batch.payload_json)
        snapshot = json.loads(batch.snapshot_json or '{}')
        evidence = snapshot.get('source_comparison')
        bindings = evidence['departments'] if evidence else _legacy_bindings(db, batch, payload)
        decisions = json.loads(batch.decisions_json or '[]')
        for binding in bindings:
            did = binding['department_id']
            if department_id is not None and did != department_id:
                continue
            source = binding['source']
            departments.setdefault(did, source['name'])
            if not payload.get('source_assertion_version'):
                notices.append(f'{batch.filename} · {departments.get(did, UNKNOWN)}: {LEGACY_TOTALS}')
            def emit(source_value, current, label, model, owner=None, **kwargs):
                for occurrence in values(source_value):
                    decision = kwargs.get('decision')
                    note = kwargs.get('note', '')
                    if not evidence and current is None:
                        kwargs['present'] = True
                        kwargs['incomplete'] = True
                        note = (note + ' Eski içe aktarmada kayıt kimliği saklanmadı; güncel kayıt eşleştirmesi Bilinmiyor. Kaynak ve kayıt kimliklerini kontrol edin.').strip()
                    # An import decision applies only to its exact candidates and
                    # chosen stored amount. A later unexplained edit stays red.
                    for item in reversed(decisions):
                        if (item.get('candidates') == source_value.get('candidates')
                            and item.get('candidates')):
                            if current is not None and _same(getattr(current, 'amount', None), item.get('chosen_amount')):
                                decision = item
                            elif not decision:
                                note = (note + ' Önceki kaynak seçimi güncel tutarı açıklamıyor: ' + decision_text(item)).strip()
                            break
                    add(occurrence, current, batch=batch, payload=payload, did=did, label=label,
                        model=model, owner=owner, department_name=source['name'], **{**kwargs, 'decision': decision, 'note': note})

            for index, block in enumerate(source.get('blocks', [])):
                ids = binding['indicator_ids'][index]
                for item, iid in zip(block['indicators'], ids):
                    indicator = db.get(Indicator, iid) if iid else None
                    valid = indicator and indicator.period_id == period_id and indicator.department_id == did
                    for value in item['values']:
                        current = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == iid,
                            IndicatorValue.year == value['year'], IndicatorValue.value_kind == value['kind'])) if valid else None
                        emit({'table_number': block.get('table_number'), **value}, current,
                             f"Gösterge: {item['name']}", 'indicator', iid, money=False)

            for item, aid in zip(source.get('activities', []), binding['activity_ids']):
                activity = db.get(Activity, aid) if aid else None
                valid = activity and activity.period_id == period_id and activity.department_id == did
                for value in item['costs']:
                    current = db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == aid,
                        ActivityCostValue.year == value['year'], ActivityCostValue.value_kind == value['kind'],
                        ActivityCostValue.funding_type == value.get('funding_type', 'total'))) if valid else None
                    # Show existing PP-09/PP-10 decisions, validate their current
                    # result instead of treating any historical reason as a waiver.
                    decision, note = recorded_change(value.get('amount'), current)
                    emit(value, current, f"Faaliyet: {item['name']}", 'activity', aid, decision=decision, note=note)

            for value in source.get('personnel', []):
                current = db.scalar(select(DepartmentCostValue).where(DepartmentCostValue.period_id == period_id,
                    DepartmentCostValue.department_id == did, DepartmentCostValue.year == value['year'],
                    DepartmentCostValue.value_kind == value['kind'], DepartmentCostValue.category == 'personnel_sgk'))
                emit(value, current, 'Personel ve SGK Giderleri', 'personnel', did)

            economic = [v for v in db.scalars(select(EconomicValue).where(
                EconomicValue.period_id == period_id, EconomicValue.department_id == did))
                if v.id in binding['economic_ids'] or json.loads(v.source_context_json or '{}').get(
                    'split_from', {}).get('original_id') in binding['economic_ids']]
            for table in source.get('economic_tables', []):
                assertions = table.get('source_assertions')
                if assertions is None:
                    # Older payloads retain raw category cells and source totals.
                    assertions = [{**v, 'amount': source_cell(v.get('raw_text'), money=True)['number']}
                        for v in table['values'] if v['funding_type'] == 'inside']
                    assertions += [{**v, 'category': None, 'funding_type': fund, 'label': 'Ekonomik toplam'}
                        for fund, rows in table['totals'].items() for v in rows]
                for value in assertions:
                    matches = [v for v in economic if v.source_table_number == table['table_number'] and
                        (v.year, v.value_kind) == (value['year'], value['kind']) and
                        (not value.get('category') or v.category == value['category']) and
                        (value['funding_type'] == 'total' or v.funding_type == value['funding_type'])]
                    complete = bool(matches) and all(v.amount is not None and v.state == 'verified' for v in matches)
                    current = SimpleNamespace(amount=sum((v.amount for v in matches), Decimal(0)) if complete else None,
                        state='verified' if complete else 'needs_review') if matches else None
                    splits = [json.loads(v.source_context_json or '{}').get('split_from') for v in matches]
                    proofs = list(dict.fromkeys(decision_text(s) for s in splits if s))
                    note = 'Program grubu dağılım kararı: ' + ' | '.join(proofs) if proofs else ''
                    emit({'table_number': table['table_number'], **value}, current,
                        f"Ekonomik sınıflandırma: {value.get('label') or ECONOMIC_CATEGORIES.get(value.get('category'), 'Toplam')}", 'economic', did, note=note)
                    covered.update(('economic', v.id) for v in matches)

            for value in source.get('total_assertions', []):
                # A single department table compares all current department
                # activities, including additions. With several source tables,
                # require an exact known CIV-069 group; never guess a programme.
                ids = sorted(aid for item, aid in zip(source['activities'], binding['activity_ids']) if
                    any(v.get('table_number') == value['table_number'] for v in item['costs']) and aid)
                tables = {v.get('table_number') for item in source['activities'] for v in item['costs']}
                department_scope = len(tables) == 1
                subtotal = next((r for r in reconciliation if ids and r['department_id'] == did and
                    (r['level'] == 'department_total' if department_scope else r['activity_ids'] == ids) and
                    (r['year'], r['value_kind']) == (value['year'], value['kind'])), None)
                amount = subtotal['amount'] if subtotal else None
                label_key = _label_key(value['label'])
                known_scope = label_key in {'toplam', 'geneltoplam', 'geneltoplami', 'genelbutce', 'genelbutcetoplami'}
                baseline = subtotal['source_amount'] if subtotal else None
                proofs = []
                explained = bool(subtotal)
                for current in db.scalars(select(ActivityCostValue).where(ActivityCostValue.activity_id.in_(ids),
                        ActivityCostValue.year == value['year'], ActivityCostValue.value_kind == value['kind'],
                        ActivityCostValue.funding_type == 'total')):
                    decision, _ = recorded_change(current.source_amount, current)
                    if not _same(current.source_amount, current.amount):
                        explained = explained and bool(decision)
                        if decision:
                            proofs.append(decision['formatted'])
                note = 'Güncel faaliyet toplamı: ortak maliyet mutabakatı.'
                if _label_key(value['label']).startswith(('genelbutce', 'geneltoplam')):
                    personnel = db.scalar(select(DepartmentCostValue).where(DepartmentCostValue.period_id == period_id,
                        DepartmentCostValue.department_id == did, DepartmentCostValue.year == value['year'],
                        DepartmentCostValue.value_kind == value['kind'], DepartmentCostValue.category == 'personnel_sgk'))
                    amount = Decimal(amount) + personnel.amount if amount is not None and personnel and personnel.amount is not None and personnel.state == 'verified' else None
                    original = next((v.get('amount') for v in source.get('personnel', []) if
                        (v['year'], v['kind']) == (value['year'], value['kind'])), None)
                    baseline = Decimal(baseline) + Decimal(original) if baseline is not None and original is not None else None
                    explained = explained and personnel is not None and _same(original, personnel.amount)
                    note = 'Güncel faaliyet toplamı + ayrı Personel ve SGK kaydı.'
                current = SimpleNamespace(amount=amount, state='verified' if amount is not None else 'needs_review')
                if not known_scope:
                    current.amount = None
                    current.state = 'needs_review'
                    note = 'Kaynak toplamının kapsamı Bilinmiyor. Kaynak satırının faaliyet ve personel kapsamını Strateji Geliştirme birimiyle kontrol edin.'
                if amount is None:
                    note += ' Kapsam veya tutar eksik; kısmi toplam gösterilmedi. Faaliyet bağlantılarını ve maliyetlerini kontrol edin.'
                decision = {'formatted': ' | '.join(dict.fromkeys(proofs))} if explained and proofs and _same(baseline, value.get('amount')) else None
                present = bool(subtotal and subtotal['activity_ids']) or any(db.get(Activity, aid) for aid in ids)
                emit(value, current, f"Kaynak toplamı: {value['label']}", 'total', did,
                    note=note, decision=decision, present=present, incomplete=True)

        # Institutional table amounts are visible to Strategy only. Keep exact
        # source cells, including numbers in tables that were retained as a conflict.
        if department_id is None:
            sections = evidence.get('sections', []) if evidence else [
                {'source': item, 'id': next(iter(item['target_ids']), None)}
                for item in general_section_plan(db, payload, period_id)]
            for binding in sections:
                section = binding['source']
                if section['kind'] != 'table':
                    continue
                target = db.get(ReportSection, binding['id']) if binding['id'] else None
                grid = json.loads(target.content_json).get('rows', []) if target and target.period_id == period_id else []
                for ri, cells in enumerate(section['content']['rows']):
                    for ci, raw in enumerate(cells):
                        cell = source_cell(raw)
                        if cell['number'] is None:
                            continue
                        now = source_cell(grid[ri][ci]) if ri < len(grid) and ci < len(grid[ri]) else None
                        current = SimpleNamespace(value=now['number'], state=now['state']) if now else None
                        add({'value': cell['number'], 'raw_text': raw, 'state': cell['state'],
                             'table_number': section['content'].get('source', {}).get('table_number'),
                             'row_number': ri+1, 'column_number': ci+1}, current, batch=batch, payload=payload,
                            label=section['title'], model='section', owner=binding['id'], money=False)
                        covered.add(('section', binding['id'], ri, ci))
            for value in payload.get('unmapped_source_cells', []):
                if (batch.id, value['table_number'], value['row_number'], value['column_number']) in source_locations:
                    continue
                add(value, None, batch=batch, payload=payload, label=value['label'], model='unmapped',
                    money=False, note='Kaynak sayısal hücresi yapılandırılmış bir kayıtla eşleştirilmedi. Kaynak tabloyu ve Kitap Bölümlerini kontrol edin.')

    # Every current value also participates, even without an imported source.
    for model, owner_model, fk, field, tag, title in (
        (IndicatorValue, Indicator, 'indicator_id', 'value', 'indicator', 'Gösterge'),
        (ActivityCostValue, Activity, 'activity_id', 'amount', 'activity', 'Faaliyet'),
    ):
        for current, owner in db.execute(select(model, owner_model).join(owner_model).where(owner_model.period_id == period_id)):
            if (department_id is not None and owner.department_id != department_id) or (tag, current.id) in covered:
                continue
            add({'year': current.year, 'kind': current.value_kind, 'funding_type': getattr(current, 'funding_type', '')},
                current, did=owner.department_id, label=f'{title}: {owner.name}', model=tag, owner=owner.id,
                money=field == 'amount')
    for model, tag, title in ((DepartmentCostValue, 'personnel', 'Personel ve SGK Giderleri'),
                              (EconomicValue, 'economic', 'Ekonomik sınıflandırma')):
        for current in db.scalars(select(model).where(model.period_id == period_id)):
            if (department_id is not None and current.department_id != department_id) or (tag, current.id) in covered:
                continue
            add({'year': current.year, 'kind': current.value_kind, 'funding_type': getattr(current, 'funding_type', '')},
                current, did=current.department_id, label=(f'{title}: {ECONOMIC_CATEGORIES.get(current.category, UNKNOWN)} / '
                    f'{PROGRAM_GROUPS.get(current.program_group, UNKNOWN)}' if tag == 'economic' else title),
                model=tag, owner=current.department_id)
    # Empty newly entered records are still visible; an absent value collection
    # must not make a user's entire activity/indicator disappear from the screen.
    owners_seen = {(r['model'], r['owner_id']) for r in records}
    for model, value_model, foreign_key, tag, title in (
        (Indicator, IndicatorValue, 'indicator_id', 'indicator', 'Gösterge'),
        (Activity, ActivityCostValue, 'activity_id', 'activity', 'Faaliyet'),
    ):
        for owner in db.scalars(select(model).where(model.period_id == period_id,
                ~model.id.in_(select(getattr(value_model, foreign_key))))):
            if (department_id is not None and owner.department_id != department_id) or (tag, owner.id) in owners_seen:
                continue
            add(None, None, did=owner.department_id, label=f'{title}: {owner.name}', model=tag, owner=owner.id,
                note='Bu güncel kaydın kaynak hücresi bulunamadı; güncel değerleri de henüz girilmemiş.')
    if department_id is None:
        for section in db.scalars(select(ReportSection).where(ReportSection.period_id == period_id, ReportSection.kind == 'table')):
            for ri, cells in enumerate(json.loads(section.content_json).get('rows', [])):
                for ci, raw in enumerate(cells):
                    value = source_cell(raw)
                    if value['number'] is None or ('section', section.id, ri, ci) in covered:
                        continue
                    add(None, SimpleNamespace(value=value['number'], state=value['state']),
                        label=section.title, model='section', owner=section.id, money=False)
    return {'rows': records, 'notices': list(dict.fromkeys(notices)), 'reconciliation': reconciliation}
