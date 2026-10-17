"""Rehearsal-only evidence: classify validation against book, Word and stored rows.

No validation result is removed or changed. Unknown errors and broken transfers
remain SYSTEM findings instead of being assumed to be source defects.
"""
from collections import Counter
from decimal import Decimal
import re

from app.data_importer import _clean, _label_key, _value_kind
from app.import_service import department_key
from app.program_service import ECONOMIC_CATEGORIES
from app.value_labels import value_kind_label, funding_label
from app.numbers import format_number


GROUPS = {
    'activity_value': 'Faaliyet kaynak tutarı doğrulama',
    'finance_missing': 'Eksik finansman',
    'activity_total': 'Faaliyet finansman toplam farkı',
    'indicator': 'Gösterge kaynak değeri',
    'explanation': 'Faaliyet açıklaması',
    'economic': 'Ekonomik kaynak/grup doğrulama',
    'program_group': 'Program Grubu Belirlenmeli',
    'cross_total': 'Çapraz maliyet/toplam farkı',
    'personnel': 'Personel/SGK toplam farkı',
    'unknown': 'Araştırılması gereken sistem/şablon/eşleme hatası',
}


def number(value):
    return Decimal(str(value)) if value is not None else None


def spec_in(error, values):
    return next(((v['year'], v['kind']) for v in values
                 if f"{v['year']} {value_kind_label(v['kind'])}" in error), None)


class BookAudit:
    def __init__(self, parsed):
        self.parsed = parsed
        self.tables = parsed.get('rehearsal_tables', {})

    def cell(self, table, row, column):
        source = self.tables.get(str(table), {})
        word = source.get('word', [])
        book = source.get('book')
        def at(rows):
            return rows[row][column] if rows and row < len(rows) and column < len(rows[row]) else None
        return dict(table=source.get('original_number', table), page=source.get('page', '?'),
                    row=row+1, column=column+1, book=at(book), word=at(word), book_available=book is not None)

    def column(self, table, spec, header_row=0):
        rows = self.tables.get(str(table), {}).get('word', [])
        return next((i for i, text in enumerate(rows[header_row]) if _value_kind(text) == spec), None) if rows else None

    def cost_cell(self, value):
        table = value['table_number']
        col = self.column(table, (value['year'], value['kind']))
        return self.cell(table, value['row_number']-1, col) if col is not None else self.cell(table, 0, 0)

    def economic_cells(self, table, spec, categories=None):
        number = table['table_number']
        col = self.column(number, spec)
        if col is None:
            return [self.cell(number, 0, 0)]
        rows = self.tables.get(str(number), {}).get('word', [])
        # Include each category and each printed total, independently of the
        # parser's category lookup; this also exposes accidentally skipped rows.
        return [self.cell(number, i, col) for i in range(1, len(rows))
                if categories is None or any(_label_key(rows[i][0]).startswith(_label_key(label))
                    for label in categories)]

    def program_cells(self, department):
        cells = []
        for block in department['blocks']:
            table = block['table_number']
            rows = self.tables.get(str(table), {}).get('word', [])
            row = next((i for i, r in enumerate(rows) if _label_key(r[0]) == 'programadi'), None)
            if row is not None:
                cells.append(self.cell(table, row, 1))
        return cells

    def activity_stored(self, snapshot, activity, spec=None):
        record = next((a for a in snapshot['activities'] if a['name'] == activity['name']), None)
        if record is None:
            return [{'missing_activity': activity['name']}]
        if spec is None:
            return [{'activity': record['name'], 'explanation': record['explanation']}]
        values = [dict(activity=record['name'], **{k: v.get(k) for k in
                  ('year', 'value_kind', 'funding_type', 'amount', 'raw_text', 'state', 'source_amount')})
                  for v in record['costs'] if (v['year'], v['value_kind']) == spec]
        present = {v['funding_type'] for v in values}
        values += [dict(activity=record['name'], year=spec[0], value_kind=spec[1], funding_type=f,
                        amount=None, state='kayıt yok (kaynak boş)') for f in ('total', 'inside', 'outside') if f not in present]
        return values

    def classify(self, department, snapshot, error):
        result = dict(side='SYSTEM', group='unknown', error=error, details=error, cells=[], stored=[], key=error)
        def source(group, cells, stored, details=error, key=None):
            result.update(side='SOURCE', group=group, cells=cells, stored=stored, details=details,
                          key=key or error)

        activity = next((a for a in department['activities'] if error.startswith(a['name'] + ':')), None)
        if activity:
            spec = spec_in(error, activity['costs'])
            if 'faaliyet açıklaması eksik' in error:
                table = activity['costs'][0]['table_number']
                code = re.match(r'^\d+', activity['name'])
                rows = self.tables.get(str(table), {}).get('word', [])
                # The activity title plus all explanation titles with its code
                # establish whether the source actually supplies an explanation.
                refs = [self.cell(table, activity['costs'][0]['row_number']-1, 0)]
                refs += [self.cell(table, i, 0) for i, row in enumerate(rows)
                         if code and re.match(r'^\s*' + code[0] + r'[.\s)]', row[0])
                         and i >= activity['costs'][-1]['row_number']]
                if not activity.get('explanation'):
                    start = next((i for i, row in enumerate(rows) if _label_key(row[0]).startswith('faaliyetlereiliskin')), None)
                    if start is not None:
                        refs += [self.cell(table, start, 0), self.cell(table, len(rows)-1, 0)]
                    source('explanation', refs, self.activity_stored(snapshot, activity),
                           error + ' Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı.')
            elif 'toplamı bütçe içi + dışı' in error:
                year = int(re.search(r'20\d{2}', error)[0])
                spec = next((v['year'], v['kind']) for v in activity['costs'] if v['year'] == year)
                selected = [v for v in activity['costs'] if (v['year'], v['kind']) == spec]
                refs = [self.cost_cell(v) for v in selected]
                detail = '; '.join(f"{funding_label(v['funding_type'])} = «{v['raw_text'] or 'BOŞ'}»" for v in selected)
                source('activity_total', refs, self.activity_stored(snapshot, activity, spec),
                       error + ' Kaynak: ' + detail, key=f"activity:{activity['name']}:{spec}")
            elif spec and ('finansman bilgisi eksik' in error or 'kaynak tutarı doğrulanmalı' in error):
                refs = [self.cost_cell(v) for v in activity['costs'] if (v['year'], v['kind']) == spec]
                group = 'finance_missing' if 'finansman bilgisi eksik' in error else 'activity_value'
                source(group, refs, self.activity_stored(snapshot, activity, spec),
                       key=f"activity:{activity['name']}:{spec}")
            return self.check_transfer(result)

        for block_index, block in enumerate(department['blocks'], 1):
            for indicator in block['indicators']:
                if not error.startswith(indicator['name'] + ':'):
                    continue
                spec = spec_in(error, indicator['values'])
                table = block['table_number']
                rows = self.tables.get(str(table), {}).get('word', [])
                header = next((i for i, row in enumerate(rows) if any(_value_kind(t) == spec for t in row)), None)
                row = next((i for i, row in enumerate(rows) if _clean(row[0]) == indicator['name']), None)
                card = next((c for c in snapshot['cards'] if c['position'] == block_index), None)
                record = next((i for i in snapshot['indicators'] if i['name'] == indicator['name']
                               and card and i['card_id'] == card['id']), None)
                if spec and row is not None and header is not None and record:
                    col = self.column(table, spec, header)
                    stored = [{k: v[k] for k in ('year', 'value_kind', 'value', 'raw_text', 'state')}
                              for v in record['values'] if (v['year'], v['value_kind']) == spec]
                    source('indicator', [self.cell(table, row, col)], stored)
                return self.check_transfer(result)

        economics = department.get('economic_tables', [])
        values = [v for t in economics for v in t['values']]
        spec = spec_in(error, values)
        if 'ekonomik kaynak tutarı ve program grubu doğrulanmalı' in error and spec:
            category = next((c for c, label in ECONOMIC_CATEGORIES.items() if label + ' / ' in error), None)
            fund = next((f for f in ('inside', 'outside') if '/ ' + funding_label(f) + ':' in error), None)
            for table in economics:
                value = next((v for v in table['values'] if (v['year'], v['kind'], v['category'], v['funding_type'])
                              == (*spec, category, fund)), None)
                if not value:
                    continue
                reasons = value.get('review_causes', [])
                # No reason is not proof of a source defect: it may be a missing
                # seed, a mapping error or a new parser failure requiring investigation.
                known = {'source_cell_unverified', 'inside_total_mismatch', 'funding_total_mismatch',
                         'outside_funding_unsplit', 'program_group_unallocated', 'personnel_total_mismatch'}
                if not reasons or any(r['cause'] not in known for r in reasons):
                    return result
                refs = self.economic_cells(table, spec)
                group = 'program_group' if value['program_group'] == 'unallocated' else 'economic'
                if group == 'program_group':
                    programs = [b['program'] for b in department['blocks'] if b['table_number'] in table['block_table_numbers']]
                    groups = {'management' if _label_key(p).startswith('yonetimvedestekprogram') else 'service' for p in programs}
                    if len(groups) != 2:
                        return result
                    refs += self.program_cells(department)
                if any(r['cause'] == 'personnel_total_mismatch' for r in reasons):
                    refs += [self.cost_cell(v) for v in department['personnel'] if (v['year'], v['kind']) == spec]
                stored = [{k: v[k] for k in ('year', 'value_kind', 'category', 'funding_type', 'amount', 'raw_text', 'state', 'program_group')}
                          for v in snapshot['economics'] if (v['year'], v['value_kind'], v['category'], v['funding_type']) == (*spec, category, fund)]
                source(group, refs, stored, '\n'.join(dict.fromkeys(r['message'] for r in reasons)),
                       key=f"economic:{table['table_number']}:{spec}")
                return self.check_transfer(result)
        if 'toplamları uyuşmuyor' in error or 'personel/SGK satırları ortak tablodan farklı' in error:
            year = int(re.search(r'20\d{2}', error)[0])
            spec = (year, 'budget' if year == snapshot['period'] else 'forecast')
            personnel = [v for v in department['personnel'] if (v['year'], v['kind']) == spec]
            refs = [self.cost_cell(v) for v in personnel]
            group = 'personnel' if 'personel/SGK satırları' in error else 'cross_total'
            for table in economics:
                refs += self.economic_cells(table, spec)
            activities = [v for a in department['activities'] for v in a['costs']
                          if (v['year'], v['kind']) == spec]
            if group != 'personnel':
                refs += [self.cost_cell(v) for v in activities]
            stored = [{k: v[k] for k in ('category', 'funding_type', 'amount', 'raw_text', 'state')}
                      for v in snapshot['economics'] if (v['year'], v['value_kind']) == spec]
            def total(rows):
                vals = [number(v.get('amount')) for v in rows]
                return sum(vals, Decimal(0)) if vals and all(v is not None for v in vals) else None
            summary = dict(year=year, activity_total=total(v for v in activities if v['funding_type'] == 'total'),
                           personnel=total(personnel), economic_total=total(stored),
                           economic_personnel=total(v for v in stored if v['category'] in {'personnel', 'sgk'}))
            def money(value):
                return format_number(value, money=True) if value is not None else 'Bilinmiyor'
            detail = (f"Faaliyet toplamı {money(summary['activity_total'])}; ortak personel/SGK "
                      f"{money(summary['personnel'])}; ekonomik kategori toplamı {money(summary['economic_total'])}; "
                      f"ekonomik personel/SGK {money(summary['economic_personnel'])} TL.")
            source(group, refs, [summary], error + ' ' + detail, key=f'{group}:{year}')
            return self.check_transfer(result)
        return result

    def check_transfer(self, result):
        # A changed cell is a system failure even when the source also has an
        # arithmetic error. Do not relabel it SOURCE just because parsing worked.
        if not result['cells']:
            result['side'] = 'SYSTEM'
        for cell in result['cells']:
            if cell['book_available'] and cell['book'] not in {'→', '↓'} and _clean(cell['book']) != _clean(cell['word']):
                result['side'] = 'SYSTEM'
                result['details'] = 'Aynı hücrenin kitap ve Word metni farklı; üretici aktarımını kontrol edin.'
        return result

    def book_transfer_issues(self, department):
        refs = [self.cost_cell(v) for a in department['activities'] for v in a['costs']]
        refs += [self.cost_cell(v) for v in department['personnel']]
        for table in department.get('economic_tables', []):
            for spec in dict.fromkeys((v['year'], v['kind']) for v in table['values']):
                refs += self.economic_cells(table, spec)
        for block in department['blocks']:
            table = block['table_number']
            rows = self.tables.get(str(table), {}).get('word', [])
            for indicator in block['indicators']:
                row = next((i for i, row in enumerate(rows) if _clean(row[0]) == indicator['name']), None)
                for value in indicator['values']:
                    spec = (value['year'], value['kind'])
                    header = next((i for i, row in enumerate(rows) if any(_value_kind(t) == spec for t in row)), None)
                    if row is not None and header is not None:
                        refs.append(self.cell(table, row, self.column(table, spec, header)))
        return [f"s.{c['page']} T{c['table']} r{c['row']}c{c['column']}: kitap–Word aktarımı"
                for c in refs if c['book_available'] and c['book'] not in {'→', '↓'}
                and _clean(c['book']) != _clean(c['word'])]


def audit_results(parsed, results):
    audit = BookAudit(parsed)
    findings = []
    transfers = []
    for result in results:
        source = next((d for d in parsed['departments'] if department_key(d['name']) == department_key(result['name'])), None)
        if source is None:
            findings += [dict(department=result['name'], side='SYSTEM', group='unknown', error=e,
                             details=e, key=e, cells=[], stored=[]) for e in result['errors']]
            continue
        storage_errors = storage_issues(source, result['stored']) + audit.book_transfer_issues(source)
        if storage_errors:
            transfers.append(dict(department=result['name'], issues=storage_errors))
        for error in result['errors']:
            finding = dict(department=result['name'], **audit.classify(source, result['stored'], error))
            if storage_errors:
                finding.update(side='SYSTEM', details='Saklanan değer kaynak ayrıştırmasıyla uyuşmuyor: ' + '; '.join(storage_errors))
            findings.append(finding)
    findings.sort(key=lambda f: (f['department'], f['group'], f['error']))
    counts = Counter((f['side'], f['group']) for f in findings)
    return dict(findings=findings, transfers=transfers,
                counts=[dict(side=s, group=g, count=n) for (s, g), n in sorted(counts.items())])


def storage_issues(source, snapshot):
    """Check every imported number/raw cell, including departments with no errors."""
    issues = []
    def compare(values, stored, dimensions, field):
        indexed = {tuple(v.get(k) for k in dimensions): v for v in stored}
        for value in values:
            key = tuple(value.get('kind' if k == 'value_kind' else k) for k in dimensions)
            row = indexed.get(key)
            if row is None and value.get(field) is None and value.get('state') == 'missing':
                continue  # Importer's existing policy: genuinely blank rows remain absent.
            if row is None or number(row.get(field)) != number(value.get(field)) or row.get('raw_text', '') != value.get('raw_text', ''):
                issues.append(str(key))
    for activity in source['activities']:
        stored = next((a for a in snapshot['activities'] if a['name'] == activity['name']), None)
        if stored:
            compare(activity['costs'], stored['costs'], ('year', 'value_kind', 'funding_type'), 'amount')
            if stored['explanation'] != activity.get('explanation', ''):
                issues.append(activity['name'] + ': açıklama aktarımı')
        else:
            issues.append(activity['name'] + ': faaliyet aktarımı')
    for block_index, block in enumerate(source['blocks'], 1):
        card = next((c for c in snapshot['cards'] if c['position'] == block_index), None)
        for indicator in block['indicators']:
            stored = next((i for i in snapshot['indicators'] if i['name'] == indicator['name']
                           and card and i['card_id'] == card['id']), None)
            if stored:
                compare(indicator['values'], stored['values'], ('year', 'value_kind'), 'value')
            else:
                issues.append(indicator['name'] + ': gösterge aktarımı')
    compare(source['personnel'], snapshot['department_costs'], ('year', 'value_kind'), 'amount')
    compare([v for t in source.get('economic_tables', []) for v in t['values']], snapshot['economics'],
            ('year', 'value_kind', 'category', 'funding_type', 'program_group'), 'amount')
    return issues
