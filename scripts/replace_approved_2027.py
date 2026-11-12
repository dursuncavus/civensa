#!/usr/bin/env python3
"""2027 ONAYLI ilk yüklemesini düzeltilmiş kitapla atomik, korumalı değiştirme."""
from collections import Counter, defaultdict
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
import os
import re
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

ACCOUNT_AUDITS = frozenset({'login', 'self_password_change', 'user_create', 'user_activate',
    'user_deactivate', 'user_password_reset', 'user_change', 'user_position_change',
    'user_permission_change', 'user_is_active_change', 'user_can_submit_change',
    'user_bulk_create_item', 'user_bulk_create', 'user_bulk_create_revert'})

OLD_BOOK = live.BOOK.with_name(PREVIOUS_2027_BOOK[0])
OLD_SHA256 = PREVIOUS_2027_BOOK[1]
CONFIRMATION = '2027 KITABINI DUZELTILMIS KITAPLA DEGISTIR'
ACTION = 'approved_book_2027_replaced'
# Child before parent. Historical import/audit rows stay. D-466: the 2027-only
# catalogue is replaced too (after FIELDS, child before parent).
FIELDS = ('indicator_values', 'indicators', 'activity_cost_values', 'activity_catalogue_links',
          'activities', 'economic_values', 'department_cost_values', 'submission_events',
          'submissions', 'subprogram_scopes', 'department_scopes', 'report_cards')
CONTENT = (*CATALOGUE, *FIELDS)
CATALOGUE_DELETE = ('activity_responsibilities', 'official_activities', 'subprograms', 'programs')
assert set(CATALOGUE_DELETE) == set(CATALOGUE)


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
    """ID-independent full row multisets; preserve nulls, source text and FK content.

    Programme/subprogramme parents are identified by name only (CIV-217)."""
    from app.db import Base
    from sqlalchemy import Numeric
    indexes = {name: {r['id']: r for r in values} for name, values in rows.items()
               if 'id' in Base.metadata.tables[name].c}

    @lru_cache(None)
    def parent(name, identity):
        row = indexes.get(name, {}).get(identity)
        if row is None:
            return ['eksik/harici', identity]
        # CIV-217: content rows point to a programme/subprogramme by its identity
        # (names). Their texts are catalogue facts, compared and listed separately;
        # an old text must not make every child row of 27 directorates differ.
        if name == 'programs':
            return ['program', row['name']]
        if name == 'subprograms':
            return ['subprogram', parent('programs', row['program_id']), row['name']]
        return digest(normalize(name, row))

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
    from app.db import Base
    tables = Base.metadata.tables

    def table_of(entity_type):
        # Audit entity types are singular model names; tables are plural.
        name = aliases.get(entity_type, entity_type)
        for candidate in (name, name + 's', name[:-1] + 'ies' if name.endswith('y') else None):
            if candidate in tables:
                return candidate
        return None

    def other_period(log):
        """An extant row this plan does not own belongs to another period (CIV-217)."""
        table = table_of(log.entity_type)
        if table is None or table in {'departments', 'users', 'organizations'} or 'id' not in tables[table].c:
            return False
        if log.entity_id in all_owned.get(table, set()):
            return False
        return db.scalar(select(tables[table].c.id).where(tables[table].c.id == log.entity_id)) is not None

    for log in db.scalars(select(AuditLog).where(AuditLog.created_at >= first).order_by(AuditLog.id)):
        if log.id in marker_ids:
            continue
        # Exact read-only actions only. Unknown actions are never presumed safe.
        if (log.action, log.entity_type) in READ_ONLY_AUDITS:
            continue
        # Account administration is not PP content (same list as the CIV-058 clear).
        if log.action in ACCOUNT_AUDITS and log.entity_type in {'user', 'user_batch'}:
            continue
        # The PP edit hook names the period it changed: "period_id=<n>".
        if (log.action == 'pp_data_change' and log.entity_type == 'department'
                and re.fullmatch(r'period_id=\d+', log.details or '') and log.details != 'period_id=2'):
            continue
        if log.action in {'catalogue_create', 'catalogue_link'} and other_period(log):
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
        # A known extant entity of another period can be excluded, never an
        # unknown/deleted entity, department-only write or mapping-batch audit.
        if other_period(log):
            continue
        refusals.append(f'2027 veya dönemi belirsiz denetim kaydı #{log.id}: yazma geçmişi var; sorumluya bildirin.')
    return refusals


def catalogue_review(owned, expected):
    """CIV-217: split live 2027 programmes/subprogrammes into ONAYLI rows and unused leftovers.

    Live 2027 still holds catalogue rows retained by the D-135 preprint clear: an
    older programme list nobody references, and subprogrammes whose texts the
    30 Oct load kept (it never overwrites existing texts). Every ONAYLI identity
    (programme name, subprogramme name) must exist; any other row is accepted for
    deletion only when no record of any table references it. Old texts are listed.
    """
    from app.db import Base
    refusals, leftovers, stale = [], [], []
    programs = {r['id']: r for r in owned['programs']}
    expected_programs = {r['id']: r for r in expected['programs']}
    wanted_programs = {r['name'] for r in expected['programs']}
    wanted_subprograms = {(expected_programs[r['program_id']]['name'], r['name']): r for r in expected['subprograms']}
    references = Counter()
    for name, rows in owned.items():
        if name in {'programs', 'subprograms'}:
            continue
        for column in Base.metadata.tables[name].columns:
            for fk in column.foreign_keys:
                if fk.column.table.name in {'programs', 'subprograms'}:
                    references.update((fk.column.table.name, r[column.name]) for r in rows if r.get(column.name) is not None)
    seen_programs, seen_subprograms, kept_programs = set(), set(), set()
    for row in sorted(owned['subprograms'], key=lambda r: r['id']):
        identity = (programs.get(row['program_id'], {}).get('name'), row['name'])
        source = wanted_subprograms.get(identity)
        if source is not None:
            seen_subprograms.add(identity)
            kept_programs.add(row['program_id'])
            for field in ('rationale', 'goal'):
                if (row[field] or '') != (source[field] or ''):
                    stale.append(dict(id=row['id'], name=row['name'], field=field, live=row[field], approved=source[field]))
        elif references[('subprograms', row['id'])]:
            refusals.append(f'2027 subprograms: kayıt #{row["id"]} ONAYLI kitapta yok ama başka kayıtlar ona bağlı; sorumluya bildirin.')
            kept_programs.add(row['program_id'])
        else:
            leftovers.append(dict(table='subprograms', id=row['id'], name=row['name']))
    for row in sorted(owned['programs'], key=lambda r: r['id']):
        if row['name'] in wanted_programs:
            seen_programs.add(row['name'])
        elif references[('programs', row['id'])] or row['id'] in kept_programs:
            refusals.append(f'2027 programs: kayıt #{row["id"]} ONAYLI kitapta yok ama başka kayıtlar ona bağlı; sorumluya bildirin.')
        else:
            leftovers.append(dict(table='programs', id=row['id'], name=row['name']))
    if seen_programs != wanted_programs or set(wanted_subprograms) != seen_subprograms:
        refusals.append('2027 programs/subprograms: ONAYLI katalog satırı canlıda eksik; sorumluya bildirin.')
    return refusals, leftovers, stale


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
    # D-466: catalogue differences are expected parts of the corrected book. They
    # are listed for the operator and replaced in the same transaction.
    for name in CATALOGUE:
        if wanted[name] != target[name]:
            catalogue_diff.append(dict(table=name, removed=sorted((wanted[name] - target[name]).elements()),
                                       added=sorted((target[name] - wanted[name]).elements())))
    # D-466 guard: every 2027 content row must belong to period #2 and point only
    # to 2027 content (or shared organisation rows). A row of another period that
    # references a 2027 row, or a 2027 row that references another period, blocks.
    from app.db import Base
    owned_ids = {name: {r['id'] for r in owned[name] if 'id' in r} for name in CONTENT}
    for name in CONTENT:
        table = Base.metadata.tables[name]
        for row in owned[name]:
            if 'period_id' in table.c and row['period_id'] != period.id:
                refusals.append(f'2027 {name}: kayıt #{row.get("id")} başka döneme ({row["period_id"]}) ait ama 2027 kaydına bağlı; dönemler arası bağ var, sorumluya bildirin.')
                continue
            for column in table.columns:
                for fk in column.foreign_keys:
                    parent = fk.column.table.name
                    value = row[column.name]
                    if parent in CONTENT and value is not None and value not in owned_ids[parent]:
                        refusals.append(f'2027 {name}: kayıt #{row.get("id")} başka dönemin {parent} kaydına (#{value}) bağlı; dönemler arası bağ var, sorumluya bildirin.')
    # Compare each directorate separately, including children reached through FKs.
    actual_groups, expected_groups = signatures(actual, grouped=True), signatures(expected, grouped=True)
    for d in departments:
        actual_dept = actual_groups[d.id]
        expected_dept = expected_groups[d.id]
        for name in FIELDS:
            if actual_dept[name] != expected_dept[name]:
                refusals.append(f'2027 {name}: ONAYLI satır imzası uyuşmuyor (müdürlük #{d.id}: {d.name}); sorumluya bildirin.')
    for name in ('official_activities', 'activity_responsibilities'):
        if observed[name] != wanted[name]:
            refusals.append(f'2027 {name}: mevcut katalog ONAYLI imzasıyla uyuşmuyor (kurum/genel); sorumluya bildirin.')
    catalogue_refusals, leftovers, stale = catalogue_review(owned, expected)
    refusals.extend(catalogue_refusals)
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
    # CIV-217: approved_book_provenance() recomputes each batch's applied_hash with
    # today's serializer, so it can never verify a load made by older code after
    # later migrations (the live 30 Oct load). Provenance here is the per-batch
    # marker/payload check above plus the per-directorate content signatures.
    result = dict(mode='approved-load-replace-plan', old_sha256=OLD_SHA256, new_sha256=live.BOOK_SHA256,
        counts={name: dict(old=len(expected[name]), new=len(corrected[name])) for name in CONTENT},
        catalogue_differences=catalogue_diff, refusals=refusals,
        leftover_catalogue=leftovers, stale_catalogue_texts=stale,
        catalogue_before=catalogue_state(db, 2))
    return result, actual, markers, corrected


def print_plan(result):
    print('2027 DÜZELTİLMİŞ KİTAPLA DEĞİŞTİRME PLANI · 0 satır yazıldı.')
    for name, counts in result['counts'].items():
        print(f'{name}: {counts["old"]} → {counts["new"]}')
    labels = {'programs': 'Program', 'subprograms': 'Alt program',
              'official_activities': 'Resmî faaliyet', 'activity_responsibilities': 'Sorumlu birim bağı'}
    # Responsibilities reference their official activity by content digest.
    officials = {digest(json.loads(r)): json.loads(r) for d in result['catalogue_differences']
                 if d['table'] == 'official_activities' for r in (*d['removed'], *d['added'])}
    for difference in result['catalogue_differences']:
        label = labels[difference['table']]
        print(f'Katalog farkı · {label}: {len(difference["removed"])} kaldırılacak, {len(difference["added"])} eklenecek.')
        for line in catalogue_lines(difference, officials):
            print(line)
    leftovers = result.get('leftover_catalogue', [])
    if leftovers:
        programs = sum(1 for r in leftovers if r['table'] == 'programs')
        print(f'Kullanılmayan eski katalog · {programs} program, {len(leftovers) - programs} alt program '
              'silinecek (hiçbir kayıt bağlı değil).')
        for row in leftovers:
            print(f'  - {"Program" if row["table"] == "programs" else "Alt program"} #{row["id"]}: {_short(row["name"], 80)}')
    stale = result.get('stale_catalogue_texts', [])
    if stale:
        print(f'Eski alt program metni · {len(stale)} alan ONAYLI metninden farklı; düzeltilmiş kitap metni yazılacak.')
        for row in stale:
            before, after = _changed_window(row['live'], row['approved'])
            label = 'Gerekçe' if row['field'] == 'rationale' else 'Amaç'
            print(f'  ~ Alt program #{row["id"]} {_short(row["name"], 50)} · {label}: canlı "{before}" · ONAYLI "{after}"')
    for refusal in result['refusals']:
        print('ENGEL: ' + refusal)
    print(f'Reddedilen: {len(result["refusals"])}')


def _short(value, limit=90):
    value = ' '.join(str(value or '').split())
    return value if len(value) <= limit else value[:limit - 1] + '…'


def _changed_window(old, new, width=30):
    """The differing middle of two texts, with a little context on each side."""
    old, new = ' '.join(str(old or '').split()), ' '.join(str(new or '').split())
    start = next((i for i, (x, y) in enumerate(zip(old, new)) if x != y), min(len(old), len(new)))
    tail = 0
    while tail < min(len(old), len(new)) - start and old[-1 - tail] == new[-1 - tail]:
        tail += 1
    def window(text):
        left = text[max(0, start - width):start]
        changed = text[start:len(text) - tail]
        # A whitespace-only change (e.g. the D-465 space after "AÇIKLAMA:") stays visible.
        middle = 'boşluk' if changed and not changed.strip() else _short(changed, 120)
        right = text[len(text) - tail:len(text) - tail + width]
        return (('…' if start > width else '') + left + '[' + middle + ']' + right
                + ('…' if tail > width else ''))
    return window(old), window(new)


def catalogue_lines(difference, officials):
    """Human-readable Turkish lines for one table's catalogue difference."""
    name = difference['table']
    removed = [json.loads(r) for r in difference['removed']]
    added = [json.loads(r) for r in difference['added']]
    lines = []
    if name == 'subprograms':
        # Same programme/name on both sides: show only the changed text.
        for old in list(removed):
            new = next((r for r in added if r['name'] == old['name'] and r['program_id'] == old['program_id']), None)
            if new is None:
                continue
            removed.remove(old)
            added.remove(new)
            for field, label in (('rationale', 'Gerekçe'), ('goal', 'Amaç')):
                if old[field] != new[field]:
                    before, after = _changed_window(old[field], new[field])
                    lines.append(f'  ~ Alt program: {_short(old["name"], 60)} · {label}: "{before}" → "{after}"')
    def describe(row):
        if name == 'programs':
            return f'Program: {_short(row.get("name"))}'
        if name == 'subprograms':
            return f'Alt program: {_short(row.get("name"), 60)} · Gerekçe: {_short(row.get("rationale"), 70)}'
        if name == 'official_activities':
            return f'{_short(row.get("subprogram_name"), 50)} / {_short(row.get("name"), 80)}'
        official = officials.get(row.get('official_activity_id'))
        what = describe_official(official) if official else 'resmî faaliyet özeti ' + str(row.get('official_activity_id'))[:12]
        return f'Müdürlük #{row.get("department_id")} sorumluluğu: {what}'
    def describe_official(row):
        return f'{_short(row.get("subprogram_name"), 40)} / {_short(row.get("name"), 60)}'
    lines += [f'  - {describe(r)}' for r in removed] + [f'  + {describe(r)}' for r in added]
    return lines


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
            for name in (*FIELDS, *CATALOGUE_DELETE):
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
            # D-466: the loader rebuilds the 2027 catalogue from the corrected book
            # alone. Every table lock is held, so nothing else can write meanwhile.
            if any(state['count'] for state in catalogue_state(db, 2).values()):
                raise live.Refusal('2027 kataloğu tam temizlenemedi; tüm işlem geri alındı. Sorumluya bildirin.')
            actor = db.get(User, actor_id)
            validation = []
            for source in new['departments']:
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
            if any(period_rows_hash(db, year) != before for year, before in protected.items()):
                raise live.Refusal('Diğer dönem değişecekti; tüm işlem geri alındı. Sorumluya bildirin.')
            db.add(AuditLog(user_id=actor_id, action=ACTION, entity_type='reporting_period', entity_id=2,
                details=encoded(dict(year=2027, head=live.HEAD, old_sha256=OLD_SHA256, new_sha256=live.BOOK_SHA256,
                    counts=result['counts'], decision='D-466',
                    catalogue_before=result['catalogue_before'], catalogue_after=catalogue_state(db, 2),
                    leftover_catalogue=result['leftover_catalogue'],
                    stale_catalogue_texts=[dict(id=r['id'], field=r['field']) for r in result['stale_catalogue_texts']],
                    old_batch_ids=[b.id for _, b in markers]))))
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
