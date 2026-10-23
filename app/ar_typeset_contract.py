"""ar-typeset/1: canonical UTF-8 and a flat registry of stable typesetting items."""
import copy
import hashlib
import json
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from zoneinfo import ZoneInfo

from .ar_typeset_source import require_keys

SCHEMA_VERSION = 'ar-typeset/1'
NUMBER_FIELDS = {'value', 'actual', 'amount', 'previous', 'initial', 'added', 'deducted', 'entered_final',
    'cancelled', 'carried', 'estimate', 'refunds', 'final', 'net', 'rate', 'pp_budget', 'lower_rate',
    'upper_rate', 'count', 'area', 'total', 'verified', 'missing', 'number', 'percentage',
    'delta', 'achievement_percent'}
REFERENCE_FIELDS = {'id', 'department_id', 'organization_id', 'period_id', 'year', 'document_id',
    'publication_id', 'pp_publication_id', 'import_id', 'program_id', 'subprogram_id', 'card_id',
    'parent_id', 'definition_version', 'revision_id', 'approval_id', 'copied_from_id',
    'copied_from_approval_id', 'edited_by', 'source_revision', 'revision', 'position', 'depth'}


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def number(value):
    if value is None:
        return {'exact': None, 'display': '—'}
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError('Dizgi verisindeki sayı sonlu değil. İlgili rapor değerini kontrol edin.')
    exact = format(decimal, 'f')
    display = format(decimal, ',f').replace(',', '_').replace('.', ',').replace('_', '.')
    return {'exact': exact, 'display': display}


def values(value, field=''):
    if field in REFERENCE_FIELDS or field.endswith('_id') or field.endswith('_ids'):
        return value
    if isinstance(value, dict):
        return {key: values(item, key) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [values(item, field) for item in value]
    if isinstance(value, bool) or field in REFERENCE_FIELDS:
        return value
    if isinstance(value, (int, float, Decimal)):
        return number(value)
    if field in NUMBER_FIELDS and (value is None or isinstance(value, str)):
        try:
            return number(value)
        except InvalidOperation:
            # Source text that is not a verified numeric field remains text.
            return value
    return value


def token(value):
    return quote(str(value), safe='')


def build_contract(payload, *, release_version='draft', source_sha256=None):
    """Pure builder. Its only input facts are the captured payload and release metadata."""
    require_keys(payload)
    captured = payload['_typeset']
    root = f"ar:{payload['id']}"
    sections, tables, rows, indicators, activities = [], [], [], [], []
    section_map = {s['code']: f"{root}:section:{token(s['code'])}" for s in payload['sections']}

    def table(identity, kind, section_code, title, columns, table_rows, identities, extra=None):
        if len(table_rows) != len(identities):
            from .activity_sections_service import fail
            fail('Dizgi satır anahtarları içerikle uyuşmuyor. Strateji ile rapor kaynağını kontrol edin.', 409)
        row_ids = []
        for raw, key in zip(table_rows, identities):
            row_id = f"{identity}:row:{key}"
            row_ids.append(row_id)
            item = {'id': row_id, 'table_id': identity, 'values': values(raw)}
            if kind == 'budget':
                for field in ('final', 'net', 'rate'):
                    if field in item['values']:
                        item['values'][field]['provenance'] = {'kind': 'computed'}
            if kind in {'resource_groups', 'department_totals'}:
                item['provenance'] = {'kind': 'computed'}
            if isinstance(raw, dict) and raw.get('import_id') is not None:
                item['provenance'] = {'kind': 'xlsx_import', 'import_id': raw['import_id']}
            rows.append(item)
        result = {'id': identity, 'kind': kind, 'section_id': section_map.get(section_code),
                  'title': title, 'columns': columns, 'row_ids': row_ids}
        if extra:
            result.update(values(extra))
            if 'totals' in extra:result['provenance']={'kind':'computed','fields':['totals']}
        tables.append(result)
        return identity

    for section in payload['sections']:
        code = section['code']
        item = {'id': section_map[code], 'code': code, 'title': section['title'],
                'values': values({k: v for k, v in section.items() if k != 'blocks'}), 'blocks': [], 'table_ids': []}
        keys = {t['position']: t for t in captured['sections'].get(code, [])}
        for position, block in enumerate(section['blocks']):
            if block['type'] == 'table':
                key = keys[position]
                identity = f"{item['id']}:table:{key['stable_key']}"
                table(identity, 'section', code, section['title'], [], block['rows'], key['rows'])
                item['table_ids'].append(identity)
                item['blocks'].append({'type': 'table', 'table_id': identity})
            else:
                item['blocks'].append(copy.deepcopy(block))
        if section.get('copied_from_id') or section.get('copied_from_approval_id'):
            item['provenance'] = {'kind': 'previous_year_copy',
                **{key: section[key] for key in ('copied_from_id', 'copied_from_approval_id') if section.get(key)}}
        elif section.get('edited_by') is not None:
            item['provenance'] = {'kind': 'manual', 'actor_id': section['edited_by']}
        sections.append(item)
    for kind, resource in payload.get('resources', {}).items():
        identity = f'{root}:resource:{token(kind)}'
        keys = [f"{r['document_id']}:{r['stable_key']}" for r in captured['resources'][kind]]
        table(identity, 'resource', resource.get('section_code'), resource['title'], resource['columns'],
              resource['rows'], keys, {'source_document_ids': sorted(r['id'] for r in resource.get('source_documents', [])),
                **{k: v for k, v in resource.items() if k not in {'rows', 'columns', 'title', 'section_code','groups','source_documents'}}})
        if resource.get('groups'):
            groups=resource['groups']
            table(identity+':groups','resource_groups',resource.get('section_code'),resource['title']+' — Tür toplamları',[],groups,
                [token(json.dumps([row['category'],row['ownership']],ensure_ascii=False,separators=(',',':'))) for row in groups],{'provenance':{'kind':'computed'}})
    financial = payload.get('financial', {})
    from .activity_financial_service import SLOTS, ENTRY_FIELDS
    budget_titles={'expenditure':'Gider — Ekonomik Kod','programme':'Gider — Program / Alt Program','revenue':'Gelir'}
    entry_titles={'assets':'Varlıklar ve Yükümlülükler','aid':'Yardım Yapılan Birlik ve Kuruluşlar','audit':'Malî Denetim Sonuçları','explanations':'Birim Sapma Açıklamaları'}
    from .activity_financial_service import budget_columns
    for kind, data in financial.get('tables', {}).items():
        table(f'{root}:budget:{token(kind)}', 'budget', 'III.A.1', budget_titles[kind], budget_columns(kind), data['rows'],
              [token(row['row_key']) for row in data['rows']], {k: v for k, v in data.items() if k not in {'rows','by_department'}})
        if data.get('by_department'):
            table(f'{root}:budget:{token(kind)}:departments','department_totals','III.A.1',budget_titles[kind]+' — Birim toplamları',[],data['by_department'],
                [str(row['department_id']) for row in data['by_department']],{'provenance':{'kind':'computed'}})
    for kind, data in financial.get('entries', {}).items():
        keys = [f"{r['document_id']}:{r['stable_key']}" for r in captured['entries'].get(kind, [])]
        table(f'{root}:financial:{token(kind)}', 'financial', SLOTS.get(kind.removesuffix('_directorates')),
              entry_titles[kind.removesuffix('_directorates')], ENTRY_FIELDS.get(kind.removesuffix('_directorates'), []), data, keys)
    for statement in financial.get('statements', []):
        table(f"{root}:statement:{statement['id']}", 'statement', 'III.A.2', statement['name'],
              [('label','Özet rakam'),('amount','Tutar')], statement['figures'],
              captured['figures'][str(statement['id'])], {'values':{k:v for k,v in statement.items() if k!='figures'}})
    for raw, key in zip(payload['core'].get('indicators', []), captured['indicators'], strict=True):
        item = {'id': f"{root}:indicator:{key['document_id']}:{token(key['indicator_id'])}",
            'section_id': section_map.get('III.B.2.i'), 'source': key, 'values': values(raw)}
        if raw.get('deviation', {}).get('calculation_rule_version') == 'difference-v1':
            item['values']['deviation']['delta']['provenance'] = {'kind': 'computed'}
        indicators.append(item)
    for activity in captured['activities']:
        identity=f"{root}:activity:{activity['department_id']}:{activity['data']['id']}"
        data=activity['data']
        item={'id':identity,'section_id':section_map.get('III.B.1'),
            'values':values({**activity,'data':{k:v for k,v in data.items() if k!='costs'}})}
        if data.get('costs'):
            cost_id=identity+':costs'
            table(cost_id,'activity_costs','III.B.1',data.get('name','Faaliyet')+' — Maliyetler',[],data['costs'],
                [str(row['id']) for row in data['costs']])
            item['cost_table_id']=cost_id
        activities.append(item)
    tables.append({'id':root+':indicators','kind':'indicators','section_id':section_map.get('III.B.2.i'),
        'title':'Gösterge Gerçekleşmeleri','row_ids':sorted(item['id'] for item in indicators)})
    tables.append({'id':root+':activities','kind':'activities','section_id':section_map.get('III.B.1'),
        'title':'Program, Alt Program ve Faaliyet Bilgileri','row_ids':sorted(item['id'] for item in activities)})
    for section in sections:
        section['table_ids'] = sorted(t['id'] for t in tables if t.get('section_id') == section['id'])
    stamp = datetime.fromisoformat(captured['generated_at'])
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    document = {'id': root, 'scope': 'birim' if payload['department_id'] else 'idare', 'year': payload['year'],
        'organization_id': payload['organization_id'], 'organization': payload['organization'],
        'department_id': payload['department_id'], 'department': payload['department'],
        'section_ids': sorted(section_map.values()), 'activity_ids': sorted(a['id'] for a in activities),
        'indicator_ids': sorted(i['id'] for i in indicators)}
    result = {'schema_version': SCHEMA_VERSION, 'document': document,
        'frozen': source_sha256 is not None,
        'release_version': release_version, 'generated_at': stamp.astimezone(ZoneInfo('Europe/Istanbul')).isoformat(),
        'source_sha256': source_sha256,
        'context': values({k: v for k, v in payload.items() if k not in {'sections', 'resources', 'core', 'financial', '_typeset', 'frozen'}}),
        'financial_context': values({k: v for k, v in financial.items() if k not in {'tables', 'entries', 'statements'}}),
        'core_context': values({k: v for k, v in payload['core'].items() if k != 'indicators'})}
    result['resource_source_context'] = values({kind: data.get('source_documents', []) for kind, data in payload.get('resources', {}).items()})
    manifest = {document['id']: sha256(document)}
    for name, items in [('sections', sections), ('tables', tables), ('rows', rows), ('activities', activities), ('indicators', indicators)]:
        result[name] = sorted(items, key=lambda item: item['id'])
        for item in items:
            if item['id'] in manifest:
                raise ValueError('Dizgi kimliği yinelenmiş. İlgili raporun anahtarlarını kontrol edin.')
            manifest[item['id']] = sha256(item)
    result['manifest'] = {'items': dict(sorted(manifest.items()))}
    result['manifest']['contract_sha256'] = sha256(result)
    return result


def export_bytes(payload, **metadata):
    return canonical_bytes(build_contract(payload, **metadata))


def verify_contract(contract):
    """Offline integrity check for consumers of the v1 contract."""
    try:
        if contract['schema_version'] != SCHEMA_VERSION:
            return False
        body = copy.deepcopy(contract)
        digest = body['manifest'].pop('contract_sha256')
        if sha256(body) != digest:
            return False
        items = [contract['document']] + [row for kind in ('sections','tables','rows','activities','indicators')
                                          for row in contract[kind]]
        registry = {row['id']: sha256(row) for row in items}
        row_ids = {row['id'] for kind in ('rows','indicators','activities') for row in contract[kind]}
        return (len(registry) == len(items) and registry == contract['manifest']['items']
                and all(set(table['row_ids']) <= row_ids for table in contract['tables']))
    except (KeyError, TypeError, ValueError):
        return False
