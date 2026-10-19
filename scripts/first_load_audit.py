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
        def source(group, cells, stored, details=error, key=None, **context):
            result.update(side='SOURCE', group=group, cells=cells, stored=stored, details=details,
                          key=key or error, **context)

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
                    result['record_name'] = indicator['name']
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
                book_refs = list(refs)
                group = 'program_group' if value['program_group'] == 'unallocated' else 'economic'
                if group == 'program_group':
                    programs = [b['program'] for b in department['blocks'] if b['table_number'] in table['block_table_numbers']]
                    groups = {'management' if _label_key(p).startswith('yonetimvedestekprogram') else 'service' for p in programs}
                    if len(groups) != 2:
                        return result
                    refs += self.program_cells(department)
                if any(r['cause'] == 'personnel_total_mismatch' for r in reasons):
                    common_refs = [self.cost_cell(v) for v in department['personnel'] if (v['year'], v['kind']) == spec]
                    refs += common_refs
                    book_refs += common_refs
                stored = [{k: v[k] for k in ('year', 'value_kind', 'category', 'funding_type', 'amount', 'raw_text', 'state', 'program_group')}
                          for v in snapshot['economics'] if (v['year'], v['value_kind'], v['category'], v['funding_type']) == (*spec, category, fund)]
                source(group, refs, stored, '\n'.join(dict.fromkeys(r['message'] for r in reasons)),
                       key=f"economic:{table['table_number']}:{spec}",
                       causes=reasons, economic=self.economic_context(table, spec, snapshot),
                       allocation_cell=dict(year=spec[0], kind=spec[1], category=category,
                                            funding_type=fund, amount=stored[0]['amount'] if stored else None,
                                            cells=self.economic_cells(table, spec, [ECONOMIC_CATEGORIES[category]])
                                            + (self.economic_cells(table, spec, ['BÜTÇE DIŞI TOPLAM KAYNAK']) if fund == 'outside' else [])),
                       book_cells=book_refs)
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
            def stored_activity_total(fund):
                amounts = [next((v['amount'] for v in a['costs'] if (v['year'], v['value_kind'], v['funding_type'])
                                 == (*spec, fund)), None) for a in snapshot['activities']]
                return sum((number(v) for v in amounts), Decimal(0)) if amounts and all(v is not None for v in amounts) else None
            common = [v for v in snapshot['department_costs'] if (v['year'], v['value_kind']) == spec
                      and v['category'] == 'personnel_sgk']
            summary = dict(year=year, activity_total=stored_activity_total('total'),
                           personnel=total(common), economic_total=total(stored),
                           economic_personnel=total(v for v in stored if v['category'] in {'personnel', 'sgk'}))
            for fund in ('inside', 'outside'):
                summary[f'activity_{fund}'] = stored_activity_total(fund)
                summary[f'economic_{fund}'] = total(v for v in stored if v['funding_type'] == fund
                                                    and v['category'] not in {'personnel', 'sgk'})
            def money(value):
                return format_number(value, money=True) if value is not None else 'Bilinmiyor'
            detail = (f"Faaliyet toplamı {money(summary['activity_total'])}; ortak personel/SGK "
                      f"{money(summary['personnel'])}; ekonomik kategori toplamı {money(summary['economic_total'])}; "
                      f"ekonomik personel/SGK {money(summary['economic_personnel'])} TL.")
            source(group, refs, [summary], error + ' ' + detail, key=f'{group}:{year}')
            return self.check_transfer(result)
        return result

    def economic_context(self, table, spec, snapshot):
        """Presentation data only; use stored raw cells and stored source totals."""
        from app.numbers import source_cell
        rows = [v for v in snapshot['economics'] if (v['year'], v['value_kind']) == spec
                and v.get('source_table_number') == table['table_number']]
        categories = []
        for value in rows:
            if value['funding_type'] != 'inside':
                continue
            categories.append(dict(category=value['category'], label=ECONOMIC_CATEGORIES[value['category']],
                amount=source_cell(value['raw_text'], money=True)['number'], raw_text=value['raw_text'],
                cells=self.economic_cells(table, spec, [ECONOMIC_CATEGORIES[value['category']]])))
        import json
        context = json.loads(rows[0].get('source_context_json') or '{}') if rows else {}
        total_labels = {'inside': 'BÜTÇE İÇİ TOPLAM KAYNAK', 'outside': 'BÜTÇE DIŞI TOPLAM KAYNAK',
                        'total': 'FAALİYET MALİYETİ TOPLAMI'}
        totals = {fund: dict(next((v for v in context.get('totals', {}).get(fund, [])
                                  if (v['year'], v['kind']) == spec), {}),
                             cells=self.economic_cells(table, spec, [total_labels[fund]]))
                  for fund in ('inside', 'outside', 'total')}
        personnel = [v['amount'] for v in snapshot['department_costs'] if (v['year'], v['value_kind']) == spec
                     and v['category'] == 'personnel_sgk']
        return dict(spec=spec, categories=categories, totals=totals,
                    personnel=sum((number(v) for v in personnel), Decimal(0))
                    if personnel and all(v is not None for v in personnel) else None)

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
    from scripts.institution_summary import audit_institution_tables
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
                institution=audit_institution_tables(parsed),
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


def money(value):
    return format_number(value, money=True) if value is not None else 'Bilinmiyor'


def sum_known(values):
    values = [number(value) for value in values]
    return sum(values, Decimal(0)) if values and all(v is not None for v in values) else None


def unique_sentences(texts):
    """Deduplicate sentences without splitting Turkish decimal/thousands notation."""
    sentences = []
    for text in texts:
        for sentence in re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])', text.strip()):
            if sentence and sentence not in sentences:
                sentences.append(sentence)
    return ' '.join(sentences)


def cell_address(cell):
    return f"s.{cell['page']}, tablo {cell['table']}, satır {cell['row']}, sütun {cell['column']}"


def empty_funding_action(amounts, by_fund):
    total = amounts.get('total')
    for missing, other in [('outside', 'inside'), ('inside', 'outside')]:
        value = by_fund.get(missing, {})
        if (not value.get('raw_text', '').strip() and amounts.get(missing) is None
                and total is not None and amounts.get(other) == total):
            label = funding_label(missing)
            source_label = {'outside': 'Bütçe dışı', 'inside': 'Bütçe içi'}[missing]
            return f'{label} hücresi boş. {source_label} kaynak yoksa 0,00 yazın.'
    return None


def finance_actions(values, cells):
    amounts = {v['funding_type']: number(v.get('source_amount') if v['funding_type'] == 'total'
                and v.get('source_amount') is not None else v.get('amount')) for v in values}
    conditional = empty_funding_action(amounts, {v['funding_type']: v for v in values})
    if conditional:
        return [conditional], []
    total = amounts.get('total')
    inside, outside = amounts.get('inside'), amounts.get('outside')
    if all(v is not None for v in (total, inside, outside)) and total != inside + outside:
        expected = inside + outside
        return [f'Toplam = Bütçe İçi + Bütçe Dışı olmalı: {money(inside)} + {money(outside)} = '
                f'{money(expected)}, kitapta {money(total)} yazıyor (fark {money(total - expected)}). '
                'Yanlış hücreyi düzeltin.'], []
    incomplete = [funding_label(fund) for fund in ('total', 'inside', 'outside') if amounts.get(fund) is None]
    addresses = '; '.join(cell_address(c) for c in cells)
    return [f'{addresses}: {", ".join(incomplete) or "finansman"} hücrelerini kaynak kayda göre doldurun. '
            'Toplam = Bütçe İçi + Bütçe Dışı olmalı; boş ve çizgi sıfır değildir.'], []


def finding_actions(finding):
    """Use structured cause IDs and stored amounts; never parse cause prose."""
    group, cells, stored = finding['group'], finding['cells'], finding['stored']
    actions, notes = [], []
    causes = finding.get('causes', [])
    economic = finding.get('economic', {})
    categories, totals = economic.get('categories', []), economic.get('totals', {})
    for cause in dict.fromkeys(c['cause'] for c in causes):
        if cause == 'program_group_unallocated':
            continue  # Allocation is never a book correction.
        if cause == 'inside_total_mismatch':
            amount = sum_known(c['amount'] for c in categories)
            total = number(totals.get('inside', {}).get('amount'))
            if amount is not None and total is not None:
                actions.append(f'Kategori satırlarının toplamı {money(amount)}, Bütçe İçi Toplam {money(total)} '
                               f'(fark {money(total - amount)}). Yanlış satırı veya toplamı düzeltin.')
                for category in categories:
                    if number(category['amount']) == total:
                        rows = ', '.join(str(c['row']) for c in category['cells'])
                        notes.append(f"Not: satır {rows} ({category['label']}) toplamla aynı değeri taşıyor.")
                continue
        elif cause == 'funding_total_mismatch':
            values = [dict(funding_type=fund, **totals.get(fund, {})) for fund in ('total', 'inside', 'outside')]
            mapped, extra = finance_actions(values, cells)
            actions += mapped; notes += extra
            continue
        elif cause == 'personnel_total_mismatch':
            personnel = sum_known(c['amount'] for c in categories if c['category'] in {'personnel', 'sgk'})
            common = number(economic.get('personnel'))
            if personnel is not None and common is not None:
                actions.append(f'Ekonomik personel/SGK {money(personnel)}, ortak personel/SGK {money(common)} '
                               f'(fark {money(personnel - common)}). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.')
                continue
        elif cause == 'source_cell_unverified':
            conditional = empty_funding_action({fund: number(v.get('amount')) for fund, v in totals.items()}, totals)
            if conditional:
                actions.append(conditional)
            for fund, value in totals.items():
                if not conditional and (value.get('amount') is None or value.get('state') != 'verified'):
                    labels = {'inside': 'Bütçe İçi Toplam', 'outside': 'Bütçe Dışı Toplam', 'total': 'Faaliyet Maliyeti Toplamı'}
                    addresses = '; '.join(cell_address(c) for c in value.get('cells') or cells)
                    actions.append(f"{addresses}: {labels[fund]} = «{value.get('raw_text') or 'BOŞ'}». "
                                   'Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.')
            for category in categories:
                if category['amount'] is None:
                    addresses = '; '.join(cell_address(c) for c in category['cells'] or cells)
                    actions.append(f"{addresses}: {category['label']} = «{category['raw_text'] or 'BOŞ'}». "
                                   'Bu kategoriye ait sayısal tutarı kaynak kayda göre kitaba girin.')
            if actions:
                continue
        elif cause == 'outside_funding_unsplit':
            outside = number(totals.get('outside', {}).get('amount'))
            addresses = '; '.join(cell_address(c) for c in cells)
            actions.append(f'{addresses}: Bütçe Dışı Toplam {money(outside)}. Ekonomik kategorilerin bütçe içi/dışı '
                           'tutarlarını ayrı belirtin; kategori toplamları bu finansman toplamlarını sağlamalı.')
            continue
        addresses = '; '.join(cell_address(c) for c in cells)
        actions.append(f'{addresses}: {cause} nedeniyle tutar açık ve toplamlarla tutarlı değil. '
                       'Kaynak satır ve toplamları karşılaştırıp sayısal hücreleri düzeltin.')
    if causes:
        return actions, notes
    if group in {'activity_total', 'activity_value', 'finance_missing'}:
        return finance_actions(stored, cells)
    if group == 'indicator':
        raw = str(stored[0].get('raw_text', '') if stored else '')
        if re.fullmatch(r'[+-]?\d+,\d{3}', raw):
            return [f'Değer belirsiz: ondalık mı ({raw}) binlik mi ({raw.replace(",", ".")})? '
                    'Doğru yazımı kitaba girin.'], []
    if group == 'explanation':
        return ["Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin."], []
    if group in {'cross_total', 'personnel'} and stored:
        summary = stored[0]
        if group == 'cross_total':
            activity, personnel, total = (number(summary.get(k)) for k in ('activity_total', 'personnel', 'economic_total'))
            if all(v is not None for v in (activity, personnel, total)):
                expected = activity + personnel
                actions = [f'Faaliyet maliyetleri toplamı {money(activity)} + ortak personel/SGK {money(personnel)} '
                           f'= {money(expected)} olmalı; ekonomik tablo toplamı {money(total)} (fark {money(total - expected)}). '
                           'Hangi tablonun yanlış olduğunu Strateji ile belirleyin.']
                for fund in ('inside', 'outside'):
                    a, e = number(summary.get(f'activity_{fund}')), number(summary.get(f'economic_{fund}'))
                    if a is not None and e is not None and a != e:
                        actions.append(f'{funding_label(fund)} faaliyet toplamı {money(a)}, ekonomik personel/SGK hariç '
                                       f'toplam {money(e)} (fark {money(e - a)}). İki tabloda bu finansman tutarları eşit olmalı.')
                return actions, []
        else:
            personnel, common = number(summary.get('economic_personnel')), number(summary.get('personnel'))
            if personnel is not None and common is not None:
                return [f'Ekonomik personel/SGK {money(personnel)}, ortak personel/SGK {money(common)} '
                        f'(fark {money(personnel - common)}). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.'], []
    addresses = '; '.join(cell_address(c) for c in cells)
    return [f'{addresses}: {GROUPS.get(group, group)} alanını kaynak kayda göre tamamlayın. '
            'Beklenen kural: açık sayısal değer, eksiksiz açıklama ve kaynak toplamlarıyla tutarlılık.'], []


def finding_title(finding):
    if finding.get('economic'):
        year, kind = finding['economic']['spec']
        return f'Ekonomik tablo · {year} {value_kind_label(kind)}'
    stored = finding.get('stored', [])
    record = stored[0] if stored else {}
    title = record.get('activity') or finding.get('record_name') or GROUPS[finding['group']]
    if record.get('year'):
        kind = record.get('value_kind')
        title += f" · {record['year']}" + (f' {value_kind_label(kind)}' if kind else '')
    return title


def checklist(parsed, results, audit):
    """Split presentation without changing or double-counting a validator message.

    Mixed messages count as book messages once; their allocation cell is also
    shown in the separate work list but is not counted a second time.
    """
    book_items, allocations = {}, {}
    book_messages = allocation_messages = mixed_messages = 0
    for finding in audit['findings']:
        if finding['side'] != 'SOURCE':
            continue
        causes = finding.get('causes', [])
        allocation = any(c['cause'] == 'program_group_unallocated' for c in causes)
        book_causes = [c for c in causes if c['cause'] != 'program_group_unallocated']
        if allocation:
            department = allocations.setdefault(finding['department'], dict(cells=[], messages=0))
            department['messages'] += 1
            if finding.get('allocation_cell') not in department['cells']:
                department['cells'].append(finding['allocation_cell'])
        if allocation and not book_causes:
            allocation_messages += 1
            continue
        book_messages += 1
        mixed_messages += bool(allocation)
        display = dict(finding)
        if allocation:
            display.update(causes=book_causes, group='economic', cells=finding['book_cells'])
        actions, notes = finding_actions(display)
        key = (finding['department'], finding['key'])
        item = book_items.setdefault(key, dict(department=finding['department'], title=finding_title(display),
                                              cells=[], actions=[], notes=[], messages=[]))
        item['actions'] += actions
        item['notes'] += notes
        item['messages'].append(finding['error'])
        for value in display['cells']:
            if value not in item['cells']:
                item['cells'].append(value)
    trace = BookAudit(parsed)
    for issue in parsed.get('membership_issues', []):
        match = re.search(r'Tablo (\d+), satır (\d+): (.+?) / ', issue)
        if match:
            cell = trace.cell(int(match[1]), int(match[2])-1, 0)
            book_items[(match[3], issue)] = dict(department=match[3], title=issue, cells=[cell], messages=[], notes=[],
                actions=[f'{cell_address(cell)}: bu faaliyet kodunun müdürlük faaliyet/maliyet tablosundaki karşılığını '
                         'kaynak kayda göre ekleyin veya yanlış üyelik satırını düzeltin. Üyelik ve maliyet kaydı tekil eşleşmeli.'])
    for item in book_items.values():
        item['action'] = unique_sentences(item.pop('actions'))
        item['note'] = unique_sentences(item.pop('notes'))
    for name, allocation in allocations.items():
        source = next(d for d in parsed['departments'] if department_key(d['name']) == department_key(name))
        allocation['cards'] = [dict(program=b['program'], subprogram=b['subprogram'], title=b.get('source_title', ''),
            group='Yönetim ve Destek' if _label_key(b['program']).startswith('yonetimvedestekprogram') else 'Hizmet')
            for b in source['blocks']]
    system_count = sum(f['side'] == 'SYSTEM' for f in audit['findings'])
    only_allocation = [name for name in allocations if not any(i['department'] == name for i in book_items.values())
                       and not any(f['department'] == name and f['side'] == 'SYSTEM' for f in audit['findings'])
                       and not any(t['department'] == name for t in audit['transfers'])]
    return dict(items=list(book_items.values()), allocations=allocations, book_messages=book_messages,
                allocation_messages=allocation_messages, mixed_messages=mixed_messages,
                only_allocation=only_allocation,
                clean=not(system_count or audit['transfers'] or book_items or parsed.get('excluded_source_tables')))
