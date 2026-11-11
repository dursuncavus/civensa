#!/usr/bin/env python3
"""2027 ONAYLI ilk yüklemesini düzeltilmiş kitapla atomik, korumalı değiştirme."""
from collections import Counter, defaultdict
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import first_load_live as live
from scripts.clear_preprint_2027 import CATALOGUE, catalogue_state, digest, encoded, batch_state
from sqlalchemy import select, text, or_
from sqlalchemy.orm import Session

from app.first_load_sources import PREVIOUS_2027_BOOK, READ_ONLY_AUDITS

OLD_BOOK = live.BOOK.with_name(PREVIOUS_2027_BOOK[0])
OLD_SHA256 = PREVIOUS_2027_BOOK[1]
CONFIRMATION = '2027 KITABINI DUZELTILMIS KITAPLA DEGISTIR'
ACTION = 'approved_book_2027_replaced'
# Child before parent. Shared catalogue and historical import/audit rows stay.
FIELDS = ('indicator_values', 'indicators', 'activity_cost_values', 'activity_catalogue_links',
          'activities', 'economic_values', 'department_cost_values', 'submission_events',
          'submissions', 'subprogram_scopes', 'department_scopes', 'report_cards')
CONTENT = (*CATALOGUE, *FIELDS)


def verify_old_book():
    data = OLD_BOOK.read_bytes()
    if hashlib.sha256(data).hexdigest() != OLD_SHA256:
        raise live.Refusal('ONAYLI kaynak SHA256 uyuşmuyor; 0 satır yazıldı. Sorumluya bildirin.')
    with TemporaryDirectory(prefix='civ214_onayli_') as directory:
        path = Path(directory) / OLD_BOOK.name
        path.write_bytes(data)
        return live.parse_book(path)[0]


def source_rows(parsed, department_ids, pid=2):
    """Pure value signatures, never trial writes. Reuse importer identity/review rules.

    Synthetic IDs are only references inside this in-memory row graph; signatures
    replace them with parent content. Scalar defaults are read from model metadata
    so newly introduced non-inert fields cannot silently escape comparison.
    """
    from app.db import Base
    from app.import_service import (consolidate_source_departments, department_key, _clean,
                                    _membership_block_index, _link_subprograms)
    from app.data_importer import _activity_identity
    from app.program_service import mark_source_disagreements
    rows = {name: [] for name in CONTENT}

    def add(table_name, **values):
        table = Base.metadata.tables[table_name]
        row = {c.name: c.default.arg if c.default is not None and c.default.is_scalar else None
               for c in table.columns}
        if 'id' in table.c:
            row['id'] = len(rows[table_name]) + 1
        if 'period_id' in table.c:
            row['period_id'] = pid
        row.update(values)
        rows[table_name].append(row)
        return row

    programs, subs, officials, responsibilities, links = {}, {}, {}, set(), set()
    for source in consolidate_source_departments(parsed)['departments']:
        did = department_ids[department_key(source['name'])]
        add('submissions', department_id=did)
        block_subs, cards = [], []
        for position, block in enumerate(source['blocks'], 1):
            pn = _clean(block.get('program', '')) or 'Program adı belirtilmedi'
            sn = _clean(block.get('subprogram', '')) or 'Alt program adı belirtilmedi'
            if pn not in programs:
                programs[pn] = add('programs', name=pn)
            key = (pn, sn)
            if key not in subs:
                subs[key] = add('subprograms', program_id=programs[pn]['id'], name=sn,
                                rationale=_clean(block.get('rationale', '')), goal=_clean(block.get('goal', '')))
            else:
                for field in ('rationale', 'goal'):
                    if not _clean(subs[key][field]):
                        subs[key][field] = _clean(block.get(field, ''))
            sp = subs[key]
            block_subs.append(SimpleNamespace(id=sp['id']))
            meta = block.get('metadata') or (block.get('indicators') or [{}])[0]
            card = add('report_cards', department_id=did, subprogram_id=sp['id'], position=position,
                       source_title=block.get('source_title') or f'2027/{position}',
                       administration=block.get('administration') or source['name'],
                       rationale=block.get('rationale', ''), goal=block.get('goal', ''),
                       **{k: meta.get(k, '') for k in ('explanation', 'calculation_method', 'data_source', 'responsible')})
            cards.append(card)
            for item in block.get('indicators', []):
                ind = add('indicators', department_id=did, subprogram_id=sp['id'], card_id=card['id'],
                          **{k: _clean(item.get(k, '')) for k in ('name', 'unit', 'explanation', 'calculation_method', 'data_source')})
                seen = set()
                for v in item.get('values', []):
                    key = (v.get('year'), v.get('kind'))
                    amount = v.get('value')
                    if (key[0] is None or not key[1] or key in seen
                            or (amount is None and v.get('state') != 'needs_review')):
                        continue
                    seen.add(key)
                    add('indicator_values', indicator_id=ind['id'], year=int(key[0]), value_kind=str(key[1]),
                        value=amount, raw_text=v.get('raw_text', str(amount)), state=v.get('state', 'verified'))
        activities = source.get('activities', [])
        sub_links = _link_subprograms(block_subs, len(activities), activities, source['blocks'])
        local_activities = []
        for item, sub in zip(activities, sub_links):
            ci = _membership_block_index(item, source['blocks'])
            card_id = cards[ci]['id'] if ci is not None else (
                cards[0]['id'] if len(cards) == 1 and 'source_memberships' not in item else None)
            act = add('activities', department_id=did, subprogram_id=sub.id if sub else None,
                      card_id=card_id, name=_clean(item.get('name', '')) or _clean(item.get('official_name', '')) or 'Faaliyet adı belirtilmedi',
                      explanation=_clean(item.get('explanation', '')))
            local_activities.append(act)
            costs, seen = [], set()
            for v in item.get('costs', []):
                key = (v.get('year'), v.get('kind'), v.get('funding_type', 'total'))
                amount = v.get('amount')
                if (key[0] is None or not key[1] or key in seen
                        or (amount is None and v.get('state') not in {'needs_review', 'not_applicable'})):
                    continue
                seen.add(key)
                costs.append(add('activity_cost_values', activity_id=act['id'], year=int(key[0]),
                    value_kind=str(key[1]), funding_type=str(key[2]), amount=amount,
                    raw_text=v.get('raw_text', str(amount)), state=v.get('state', 'verified'),
                    source_amount=amount if key[2] == 'total' else None,
                    source_raw_text=v.get('raw_text', '') if key[2] == 'total' else ''))
            objects = [SimpleNamespace(**{**v, 'amount': None if v['amount'] is None else Decimal(str(v['amount'])),
                       'source_amount': None if v['source_amount'] is None else Decimal(str(v['source_amount']))}) for v in costs]
            mark_source_disagreements(SimpleNamespace(cost_values=objects))
            for row, obj in zip(costs, objects):
                row['state'] = obj.state
        seen = set()
        for v in source.get('personnel', []):
            key = (v.get('year'), v.get('kind'))
            amount = v.get('amount')
            if (key[0] is None or not key[1] or key in seen
                    or (amount is None and v.get('state') not in {'needs_review', 'not_applicable'})):
                continue
            seen.add(key)
            add('department_cost_values', department_id=did, year=int(key[0]), value_kind=str(key[1]),
                amount=amount, raw_text=v.get('raw_text', ''), state=v.get('state', 'verified'))
        cards_by_table = {b.get('table_number'): c for b, c in zip(source['blocks'], cards)}
        economics = {}
        for table in source.get('economic_tables', []):
            source_cards = [cards_by_table[n] for n in table['block_table_numbers'] if n in cards_by_table]
            context = {k: table[k] for k in ('categories', 'totals', 'block_table_numbers')}
            context['card_ids'] = [c['id'] for c in source_cards]
            for v in table['values']:
                key = tuple(v[k] for k in ('year', 'kind', 'category', 'program_group', 'funding_type'))
                if key in economics:
                    row = economics[key]
                    row.update(amount=None, state='needs_review', issue='Aynı ekonomik hücre birden fazla kaynak tabloda bulunuyor; kaynakları karşılaştırın.')
                    row['raw_text'] += ' / ' + v['raw_text']
                    continue
                row = add('economic_values', department_id=did, year=v['year'], value_kind=v['kind'],
                    **{k: v[k] for k in ('category', 'program_group', 'funding_type', 'raw_text', 'state')},
                    amount=v['amount'], issue=v.get('issue', ''), source_card_id=source_cards[-1]['id'] if source_cards else None,
                    source_table_number=table['table_number'], source_context_json=encoded(context))
                if len(source_cards) != len(table['block_table_numbers']):
                    row['state'] = 'needs_review'
                    row['issue'] = (row['issue'] + ' Kaynak program bloklarının müdürlük kapsamını kontrol edin.').strip()
                economics[key] = row
        for block in source['blocks']:
            for member in block.get('activity_memberships', []):
                identity = _activity_identity(member['name'])
                values = dict(program_code='', program_name=block['program'].strip(), subprogram_code='',
                              subprogram_name=block['subprogram'].strip(), code=identity[1], name=member['name'].strip())
                key = tuple(values.values())
                if key not in officials:
                    officials[key] = add('official_activities', **values)
                oid = officials[key]['id']
                if (oid, did) not in responsibilities:
                    add('activity_responsibilities', official_activity_id=oid, department_id=did)
                    responsibilities.add((oid, did))
                for act in local_activities:
                    if _activity_identity(act['name']) == identity and (act['id'], oid) not in links:
                        add('activity_catalogue_links', activity_id=act['id'], official_activity_id=oid)
                        links.add((act['id'], oid))
    return rows


def signatures(rows, *, grouped=False):
    """ID-independent full row multisets; preserve nulls, source text and FK content."""
    from app.db import Base
    from sqlalchemy import Numeric
    indexes = {name: {r['id']: r for r in values} for name, values in rows.items()
               if 'id' in Base.metadata.tables[name].c}

    @lru_cache(None)
    def parent(name, identity):
        row = indexes.get(name, {}).get(identity)
        return digest(normalize(name, row)) if row is not None else ['eksik/harici', identity]

    def normalize(name, row):
        result = {}
        for column in Base.metadata.tables[name].columns:
            key = column.name
            if key == 'id' or key in {'created_at', 'updated_at'}:
                continue
            value = row[key]
            if value is not None:
                for fk in column.foreign_keys:
                    if fk.column.table.name in rows:
                        value = parent(fk.column.table.name, value)
                if isinstance(column.type, Numeric):
                    numeric = Decimal(str(value)).quantize(Decimal(1).scaleb(-column.type.scale))
                    # PostgreSQL NUMERIC stores both signed zero forms as zero;
                    # the exact printed spelling remains protected in raw_text.
                    value = str(abs(numeric) if numeric == 0 else numeric)
                if key == 'source_context_json':
                    value = json.loads(value)
                    value['card_ids'] = [parent('report_cards', i) for i in value.get('card_ids', [])]
            result[key] = value
        return result

    @lru_cache(None)
    def parent_department(name, identity):
        row = indexes.get(name, {}).get(identity)
        return department(name, row) if row is not None else None

    def department(name, row):
        if 'department_id' in row:
            return row['department_id']
        for column in Base.metadata.tables[name].columns:
            for fk in column.foreign_keys:
                parent_name = fk.column.table.name
                if parent_name in indexes and row[column.name] is not None:
                    did = parent_department(parent_name, row[column.name])
                    if did is not None:
                        return did
        return None

    if grouped:
        groups = defaultdict(lambda: {name: Counter() for name in rows})
        for name, values in rows.items():
            for row in values:
                groups[department(name, row)][name][encoded(normalize(name, row))] += 1
        return groups
    return {name: Counter(encoded(normalize(name, row)) for row in values) for name, values in rows.items()}


def owned_rows(db, pid):
    """Follow every FK from the target period, including indirect IC/FR histories.

    Never interpret another domain's period_id as a reporting_period ID. The FK
    graph, not column spelling, defines ownership. Cross-period children are
    included and subsequently refused rather than deleted by cascade.
    """
    from app.db import Base
    tables = Base.metadata.tables
    found = {name: {} for name in tables}
    def absorb(name, condition):
        table = tables[name]
        changed = False
        for row in db.execute(select(table).where(condition)).mappings():
            key = tuple(row[c.name] for c in table.primary_key)
            if key not in found[name]:
                found[name][key] = dict(row)
                changed = True
        return changed
    absorb('reporting_periods', tables['reporting_periods'].c.id == pid)
    for name, table in tables.items():
        if name.startswith('ic_') and 'year' in table.c:
            absorb(name, table.c.year == 2027)
        if name.startswith('ic_') and {'start_year', 'end_year'} <= set(table.c.keys()):
            absorb(name, (table.c.start_year <= 2027) & (table.c.end_year >= 2027))
    changed = True
    while changed:
        changed = False
        for name, table in tables.items():
            conditions = []
            for fk in table.foreign_keys:
                values = {r[fk.column.name] for r in found[fk.column.table.name].values()}
                if values:
                    conditions.append(fk.parent.in_(values))
            if conditions:
                changed = absorb(name, or_(*conditions)) or changed
    return {name: list(values.values()) for name, values in found.items()}


def audit_refusals(db, owned, markers):
    from app.models import AuditLog
    if not markers:
        return ['2027 first_load_department denetim izleri eksik.']
    first = min(batch.created_at for _, batch in markers)
    marker_ids = {log.id for log, _ in markers}
    all_owned = {name: {r['id'] for r in rows if 'id' in r} for name, rows in owned.items()}
    aliases = {'reporting_period': 'reporting_periods', 'import_batch': 'import_batches',
               'official_activity': 'official_activities', 'activity': 'activities', 'indicator': 'indicators',
               'indicator_value': 'indicator_values', 'submission': 'submissions', 'report_card': 'report_cards'}
    refusals = []
    for log in db.scalars(select(AuditLog).where(AuditLog.created_at >= first).order_by(AuditLog.id)):
        if log.id in marker_ids:
            continue
        # Exact read-only actions only. Unknown actions are never presumed safe.
        if (log.action, log.entity_type) in READ_ONLY_AUDITS:
            continue
        if log.action in {'catalogue_create', 'catalogue_link'}:
            table = 'official_activities' if log.action == 'catalogue_create' else 'activities'
            if log.entity_type == ('official_activity' if log.action == 'catalogue_create' else 'activity'):
                for marker, batch in markers:
                    did = json.loads(marker.details)['department_id']
                    candidates = {r['id'] for r in owned['activities'] if r['department_id'] == did} if table == 'activities' else {
                        r['official_activity_id'] for r in owned['activity_responsibilities'] if r['department_id'] == did}
                    if batch.created_at <= log.created_at <= marker.created_at and log.entity_id in candidates:
                        break
                else:
                    refusals.append(f'2027 denetim kaydı #{log.id}: ilk yükleme dışı katalog işlemi; sorumluya bildirin.')
                continue
        table = aliases.get(log.entity_type, log.entity_type)
        # A known extant entity of another period can be excluded, never an
        # unknown/deleted entity, department-only write or mapping-batch audit.
        from app.db import Base
        t = Base.metadata.tables.get(table)
        if t is not None and 'id' in t.c and log.entity_id not in all_owned.get(table, set()):
            if table not in {'departments', 'users', 'organizations'}:
                if db.scalar(select(t.c.id).where(t.c.id == log.entity_id)) is not None:
                    continue
        refusals.append(f'2027 veya dönemi belirsiz denetim kaydı #{log.id}: yazma geçmişi var; sorumluya bildirin.')
    return refusals


def build_plan(db, old, new, *, organization_id, actor_id):
    from app.models import Organization, User, ReportingPeriod, Department, AuditLog, ImportBatch
    from app.import_service import department_key, build_department_plan
    live.require_head(db)
    orgs = list(db.scalars(select(Organization.id)))
    actor = db.get(User, actor_id)
    if orgs != [organization_id] or not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
        raise live.Refusal('Kurum veya etkin Strateji/yönetici kullanıcısı uyuşmuyor; 0 satır yazıldı. Numaraları doğrulatın.')
    period = db.get(ReportingPeriod, 2)
    if not period or period.year != 2027 or period.status not in {'draft', 'active'} or period.template_status != 'verified':
        raise live.Refusal('Dönem #2, açık ve şablonu doğrulanmış 2027 olmalıdır; 0 satır yazıldı. Sorumluya bildirin.')
    departments = list(db.scalars(select(Department)))
    mapping = {}
    for d in departments:
        key = department_key(d.name)
        if key in mapping:
            raise live.Refusal('Müdürlük eşleşmesi tekil değil; 0 satır yazıldı. Kurum yapısını sorumluya doğrulatın.')
        mapping[key] = d.id
    try:
        expected, corrected = source_rows(old, mapping), source_rows(new, mapping)
    except KeyError:
        raise live.Refusal('Kaynak müdürlük eşleşmesi eksik; 0 satır yazıldı. Kurum yapısını doğrulatın.') from None
    wanted, target = signatures(expected), signatures(corrected)
    owned = owned_rows(db, period.id)
    actual = {name: owned[name] for name in CONTENT}
    observed = signatures(actual)
    refusals, catalogue_diff = [], []
    for name in CATALOGUE:
        if wanted[name] != target[name]:
            catalogue_diff.append(dict(table=name, removed=list((wanted[name] - target[name]).elements()),
                                       added=list((target[name] - wanted[name]).elements())))
            refusals.append(f'2027 {name}: ONAYLI ve düzeltilmiş kitap katalogları farklı; katalog geçişini sorumluya planlatın.')
    # Compare each directorate separately, including children reached through FKs.
    actual_groups, expected_groups = signatures(actual, grouped=True), signatures(expected, grouped=True)
    for d in departments:
        actual_dept = actual_groups[d.id]
        expected_dept = expected_groups[d.id]
        for name in FIELDS:
            if actual_dept[name] != expected_dept[name]:
                refusals.append(f'2027 {name}: ONAYLI satır imzası uyuşmuyor (müdürlük #{d.id}: {d.name}); sorumluya bildirin.')
    for name in CATALOGUE:
        if observed[name] != wanted[name]:
            refusals.append(f'2027 {name}: mevcut katalog ONAYLI imzasıyla uyuşmuyor (kurum/genel); sorumluya bildirin.')
    allowed = {'reporting_periods', 'import_batches', *CONTENT}
    for name, rows in owned.items():
        if rows and name not in allowed:
            refusals.append(f'2027 {name}: ilk yükleme dışında {len(rows)} bağlı kayıt var (kayıtlar: ' + ', '.join(str(r.get('id', 'bileşik anahtar')) for r in rows) + '); sorumluya bildirin.')
    batches = {b.id: b for b in db.scalars(select(ImportBatch).where(ImportBatch.period_id == 2))}
    markers, traced = [], set()
    planned_old = build_department_plan(db, old)["parsed"]
    for log in db.scalars(select(AuditLog).where(AuditLog.action == live.MARKER, AuditLog.entity_type == 'import_batch')):
        if log.entity_id not in batches:
            continue
        batch = batches[log.entity_id]
        try:
            info = json.loads(log.details)
            did = info['department_id']
            source = next(s for s in planned_old['departments'] if mapping[department_key(s['name'])] == did)
            valid = (info['book_sha256'] == OLD_SHA256 and info['year'] == 2027 and did not in traced
                     and batch.status == 'applied' and batch.filename == OLD_BOOK.name
                     and json.loads(batch.payload_json) == live.department_payload(old, source)
                     and batch.applied_at is not None and batch.created_at <= batch.applied_at <= log.created_at)
            if not valid:
                raise ValueError
            traced.add(did)
            markers.append((log, batch))
        except (ValueError, KeyError, TypeError, StopIteration):
            refusals.append(f'2027 import_batches: paket #{batch.id} ONAYLI ilk yükleme kökeni uyuşmuyor; sorumluya bildirin.')
    expected_dids = {r['department_id'] for r in expected['submissions']}
    if traced != expected_dids:
        refusals.append('2027 import_batches: 34 müdürlüğün tekil ONAYLI ilk yükleme denetim izi eksik; sorumluya bildirin.')
    # Retain the prior CIV-058 archives only with their original immutable receipt.
    archive_logs = db.scalars(select(AuditLog).where(AuditLog.action == 'preprint_2027_cleared',
        AuditLog.entity_type == 'reporting_period', AuditLog.entity_id == 2)).all()
    archived = {}
    if len(archive_logs) == 1:
        try:
            receipt = json.loads(archive_logs[0].details)
            if receipt['version'] == 2 and receipt['year'] == 2027 and receipt['decision'] == 'D-135':
                archived = receipt['batches']
        except (KeyError, ValueError, TypeError):
            pass
    marked = {b.id for _, b in markers}
    for bid, batch in batches.items():
        if bid not in marked and not (batch.status == 'superseded' and archived.get(str(bid)) == digest(batch_state(batch))):
            refusals.append(f'2027 import_batches: paket #{bid} ilk yükleme dışında; sorumluya bildirin.')
    refusals.extend(audit_refusals(db, owned, markers))
    # The shared read-only publication provenance helper verifies the original
    # applied_hash/IDs (before catalogue links), not just equal row values.
    from app.program_service import approved_book_provenance
    if approved_book_provenance(db, 2) is None:
        refusals.append('2027 import_batches: özgün satır kimlikleri/uygulanmış paket özeti doğrulanamadı; sorumluya bildirin.')
    result = dict(mode='approved-load-replace-plan', old_sha256=OLD_SHA256, new_sha256=live.BOOK_SHA256,
        counts={name: dict(old=len(expected[name]), new=len(corrected[name])) for name in CONTENT},
        catalogue_differences=catalogue_diff, refusals=refusals,
        retained_catalogue=catalogue_state(db, 2))
    return result, actual, markers, corrected


def print_plan(result):
    print('2027 DÜZELTİLMİŞ KİTAPLA DEĞİŞTİRME PLANI · 0 satır yazıldı.')
    for name, counts in result['counts'].items():
        print(f'{name}: {counts["old"]} → {counts["new"]}')
    for difference in result['catalogue_differences']:
        print('Katalog farkı: ' + encoded(difference))
    for refusal in result['refusals']:
        print('ENGEL: ' + refusal)
    print(f'Reddedilen: {len(result["refusals"])}')


def execute(engine, old, new, *, organization_id, actor_id, apply=False, backup=None):
    from app.db import Base
    from app.models import AuditLog, ImportBatch, User, ReportingPeriod
    from app.first_load_service import apply_first_load_batch, load_all_models, period_rows_hash
    load_all_models()
    with engine.connect() as connection, Session(connection) as db:
        with db.begin():
            if not apply:
                db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
            else:
                if not db.scalar(text('SELECT pg_try_advisory_xact_lock(:key)'), {'key': live.LOCK}):
                    raise live.Refusal('Başka ilk yükleme/temizleme çalışıyor; 0 satır yazıldı. Tamamlanmasını bekleyin.')
                db.execute(text("SET LOCAL lock_timeout = '10s'"))
                names = ', '.join('"' + t.name + '"' for t in Base.metadata.sorted_tables)
                db.execute(text('LOCK TABLE ' + names + ' IN SHARE ROW EXCLUSIVE MODE'))
            result, rows, markers, expected = build_plan(db, old, new, organization_id=organization_id, actor_id=actor_id)
            print_plan(result)
            if not apply or result['refusals']:
                return result
            # All guards/locks precede the single confirmation. Nothing has been
            # changed; backup freshness is checked again after the owner types.
            live.verify_backup(backup)
            response = live.read_confirmation(f'Yazma onayı: {CONFIRMATION} yazın: ')
            if response != CONFIRMATION:
                raise live.Refusal('Değiştirme onayı uyuşmuyor; 0 satır yazıldı. Planı kontrol edip yeniden deneyin.')
            live.verify_backup(backup)
            protected = {year: period_rows_hash(db, year) for year in db.scalars(select(ReportingPeriod.year).where(ReportingPeriod.id != 2))}
            receipt = result['retained_catalogue']
            for name in FIELDS:
                table = Base.metadata.tables[name]
                if not rows[name]:
                    continue
                # Composite PK tables are included; never delete by a guessed ID.
                from sqlalchemy import and_
                conditions = [and_(*(c == row[c.name] for c in table.primary_key)) for row in rows[name]]
                removed = db.execute(table.delete().where(or_(*conditions))).rowcount
                if removed != len(rows[name]):
                    raise live.Refusal('Temizlenecek satırlar değişti; tüm işlem geri alındı. Sorumluya bildirin.')
            for _, batch in markers:
                batch.status = 'superseded'
            db.flush()
            # Hash receipt hand-off: validate the retained catalogue before EACH
            # shared loader call. The loader sees exactly the approved catalogue.
            actor = db.get(User, actor_id)
            validation = []
            for source in new['departments']:
                if catalogue_state(db, 2) != receipt:
                    raise live.Refusal('Korunan katalog özeti değişti; tüm işlem geri alındı. Sorumluya bildirin.')
                batch = ImportBatch(period_id=2, filename=live.BOOK.name, status='preview', created_by=actor_id,
                                    payload_json=json.dumps(live.department_payload(new, source), ensure_ascii=False))
                db.add(batch)
                db.flush()
                _, _, findings = apply_first_load_batch(db, batch, actor)
                validation.extend(findings)
                did = findings[0]['department_id']
                db.add(AuditLog(user_id=actor_id, action=live.MARKER, entity_type='import_batch', entity_id=batch.id,
                    details=encoded(dict(book_sha256=live.BOOK_SHA256, year=2027, department_id=did, validation_errors=findings))))
            db.flush()
            after = owned_rows(db, 2)
            if signatures({name: after[name] for name in CONTENT}) != signatures(expected):
                raise live.Refusal('Düzeltilmiş kitap son satır doğrulaması uyuşmuyor; tüm işlem geri alındı. Sorumluya bildirin.')
            if catalogue_state(db, 2) != receipt or any(period_rows_hash(db, year) != before for year, before in protected.items()):
                raise live.Refusal('Korunan katalog veya diğer dönem değişecekti; tüm işlem geri alındı. Sorumluya bildirin.')
            db.add(AuditLog(user_id=actor_id, action=ACTION, entity_type='reporting_period', entity_id=2,
                details=encoded(dict(year=2027, head=live.HEAD, old_sha256=OLD_SHA256, new_sha256=live.BOOK_SHA256,
                    counts=result['counts'], retained_catalogue=receipt, old_batch_ids=[b.id for _, b in markers]))))
            result.update(mode='approved-load-replace-apply', validation=validation)
        return result


def main(argv=None):
    parser = live.SafeParser(description=__doc__)
    parser._optionals.title = 'Seçenekler'
    parser._actions[0].help = 'Bu yardım metnini göster ve çık'
    parser.add_argument('--organization-id', type=int, required=True, help='Kurum numarası')
    parser.add_argument('--actor-id', type=int, required=True, help='Etkin Strateji/yönetici kullanıcısının numarası')
    parser.add_argument('--apply', action='store_true', help='Plan, yedek ve terminal onayından sonra atomik değiştir')
    parser.add_argument('--backup', type=Path, help='Doğrulanmış, 60 dakikadan yeni .dump yedeği')
    args = parser.parse_args(argv)
    try:
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with live.environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = live.target_url()
            old, new = verify_old_book(), live.verify_book(live.BOOK)
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                result = execute(engine, old, new, organization_id=args.organization_id,
                                 actor_id=args.actor_id, apply=args.apply, backup=args.backup)
            finally:
                engine.dispose()
        if result['refusals']:
            print('DURDU: Plan engelleri var; 0 satır yazıldı. Sorumluya bildirin.', file=sys.stderr)
            return 1
        print('2027 düzeltilmiş kitapla değiştirildi; işlem bütünüyle tamamlandı.' if args.apply else 'PLAN tamamlandı; 0 satır yazıldı.')
        return 0
    except live.Refusal as exc:
        print('DURDU: ' + str(exc), file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print('DURDU: İşlem kesildi; açık işlem geri alındı. Yeniden salt okunur plan alın.', file=sys.stderr)
    except Exception as exc:
        print(f'DURDU: İşlem tamamlanamadı ({live.failure_detail(exc)}); açık işlem geri alındı. Bağlantı/dosya ayrıntıları gizlendi; sorumluya bildirin.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
