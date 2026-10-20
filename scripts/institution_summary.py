"""Read-only institution checks for the first-load rehearsal, never the importer.

Table selection uses printed headings. Page and ID are evidence only. Arithmetic
uses Decimal and fails closed for absent, ambiguous or unreadable source cells.
"""
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import re

from app.data_importer import _label_key, _value_kind
from app.numbers import format_number, source_cell
from app.program_service import ECONOMIC_CATEGORIES


TABLE_NAMES = {
    'economic': 'Ekonomik kod / program grupları',
    'share': 'Müdürlük bütçeleri ve toplam bütçeye oranı',
    'detail': 'Ekonomik kod / program ve faaliyet ayrıntısı',
}
ZERO = Decimal(0)


def table_kind(table):
    rows = table['rows']
    if not rows or not rows[0]:
        return None
    first = _label_key(rows[0][0])
    headings = ' '.join(_label_key(c) for row in rows[:2] for c in row)
    if first == 'mudurlukadi' and 'oran' in headings:
        return 'share'
    if first == 'ekonomikkod':
        return 'economic' if 'hizmetprogram' in headings or 'programdisi' in headings else 'detail'
    return None


def read_number(raw, *, money=True):
    value = source_cell(raw, money=money)['number']
    return Decimal(value) if value is not None else None


def complete_sum(values):
    values = list(values)
    return sum(values, ZERO) if values and all(v is not None for v in values) else None


def programme_key(label):
    # Normalize only the generic suffix, not different programme taxonomies.
    return re.sub(r'programi?$', '', _label_key(label))


def at(table, row, column):
    rows = table['rows']
    return rows[row][column] if row is not None and row < len(rows) and column < len(rows[row]) else None


def cell_reference(table, row, column, **context):
    raw = at(table, row, column)
    return dict(page=table.get('page', '?'), table=table.get('id', '?'),
                row=row + 1, column=column + 1, label=at(table, row, 0), raw=raw,
                amount=read_number(raw), **context)


def source_table(parsed, number):
    source = parsed.get('source_tables', {}).get(str(number), {})
    rehearsal = parsed.get('rehearsal_tables', {}).get(str(number), {})
    return dict(id=source.get('id', f'Word T{number}'), page=source.get('page', '?'),
                rows=rehearsal.get('book') if rehearsal.get('book') is not None else rehearsal.get('word', []))


def card_reference(parsed, department, block):
    source = source_table(parsed, block.get('table_number'))
    def row_number(label):
        return next((i + 1 for i, row in enumerate(source['rows']) if _label_key(row[0]) == label), '—')
    return dict(department=department.get('name', '—'), page=source['page'], table=source['id'],
                programme=block['program'], subprogramme=block.get('subprogram', '—'),
                programme_row=row_number('programadi'), subprogramme_row=row_number('altprogramadi'))


def physical_cell(value):
    return value['table'], value['row'], value['column']


def finding(table, check, row, column, computed, *, note='', tolerance=ZERO, printed=None,
            failure_class='UNKNOWN', contributors=(), printed_components=(), basis=''):
    raw = at(table, row, column) if printed is None else printed
    value = read_number(raw, money=not check.startswith('Yüzde'))
    difference = value - computed if value is not None and computed is not None else None
    status = 'PASS' if difference is not None and abs(difference) <= tolerance else 'FAIL'
    classification = failure_class if status == 'FAIL' else None
    if classification == 'BOOK' and difference is None:
        classification = 'UNKNOWN'  # An unreadable amount is not arithmetic proof.
    years = [int(match[0]) for text in (table['rows'][0][:column + 1] if table['rows'] else [])
             if (match := re.search(r'20\d{2}', str(text or '')))]
    return dict(status=status, classification=classification, table_kind=table['kind'],
                check=check, page=table.get('page', '?'), table=table.get('id', '?'),
                name=TABLE_NAMES[table['kind']], row=row + 1 if row is not None else '—',
                label=at(table, row, 0) or '—', column=column + 1, printed=value,
                raw=raw, computed=computed, difference=difference, note=note,
                year=years[-1] if years else None,
                column_header=at(table, 0 if table['kind'] == 'share' else 1, column),
                contributors=list(contributors), printed_components=list(printed_components),
                coverage_basis=basis)


def missing(table, label, note):
    result = finding(table, 'Okuma / kapsam', None, 0, None, note=note, failure_class='CHECK')
    result['label'] = label
    return result


def year_groups(table):
    """Require the complete, repeated heading block for every printed year."""
    rows = table['rows']
    expected = (['hizmetprogramlaritoplam', 'yonetimvedestekprogrami', 'programdisigiderler', 'toplam']
                if table['kind'] == 'economic' else ['butceicitl', 'butcedisitl', 'toplamtl'])
    if len(rows) < 3:
        raise ValueError('Başlık veya veri satırları eksik; kaynak tabloyu kontrol edin.')
    width = len(expected)
    groups = []
    seen = set()
    for start in range(1, len(rows[0]), width):
        year_text = str(rows[0][start] or '')
        match = re.fullmatch(r'20\d{2}', year_text)
        columns = list(range(start, start + width))
        headers = [_label_key(at(table, 1, c)) for c in columns]
        if not match or headers != expected or int(year_text) in seen:
            raise ValueError('Yıl / bileşen / toplam başlıkları eksik veya yinelenmiş; kaynak tabloyu kontrol edin.')
        seen.add(int(year_text))
        groups.append((int(year_text), columns[:-1], columns[-1]))
    if not groups or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('Tablo sütunları eksik; kaynak tabloyu kontrol edin.')
    return groups


def row_checks(table, groups):
    return [finding(table, 'Satır toplamı', row, total,
                    complete_sum(read_number(at(table, row, c)) for c in components),
                    note=f'{year}: bileşen sütunları ' + ', '.join(str(c + 1) for c in components),
                    failure_class='BOOK',
                    contributors=[cell_reference(table, row, c) for c in components],
                    printed_components=[cell_reference(table, row, c) for c in components],
                    basis='Aynı basılı satırdaki bileşenler; başka tablo veya dağılım kullanılmadı.')
            for row in range(2, len(table['rows'])) for year, components, total in groups]


def column_checks(table, coverage, columns):
    """Coverage lists direct children only, so nested subtotals are not doubled."""
    return [finding(table, 'Sütun toplamı', total, column,
                    complete_sum(read_number(at(table, r, column)) for r in children),
                    note='Kapsanan satırlar: ' + ', '.join(str(r + 1) for r in children),
                    failure_class='BOOK',
                    contributors=[cell_reference(table, r, column) for r in children],
                    printed_components=[cell_reference(table, r, column) for r in children],
                    basis='Basılı hiyerarşinin doğrudan alt satırları birer kez; alt toplam ve onun ayrıntısı birlikte toplanmadı.')
            for total, children in coverage.items() for column in columns]


def total_row(table, prefix, findings):
    matches = [r for r, row in enumerate(table['rows']) if _label_key(row[0]).startswith(prefix)]
    if len(matches) != 1:
        findings.append(missing(table, prefix, 'Tekil toplam satırı bulunamadı; kaynak tabloyu kontrol edin.'))
        return None
    return matches[0]


def category_key(label):
    names = {_label_key(v): k for k, v in ECONOMIC_CATEGORIES.items()}
    names.update({_label_key(v[:-4] + 'i'): k for k, v in ECONOMIC_CATEGORIES.items() if v.endswith('leri')})
    names['sosyalguvenlikkurumunadevletprimigiderler'] = 'sgk'
    names.update(dict(zip(('01', '02', '03', '04', '05', '06', '07', '08', '09'), ECONOMIC_CATEGORIES)))
    return names.get(_label_key(label))


def unique_contributions(records):
    """A physical source cell contributes once, even if several cards refer to it."""
    unique = {}
    for index, record in enumerate(records):
        key = physical_cell(record) if isinstance(record['row'], int) and isinstance(record['column'], int) else ('missing', index)
        if key not in unique:
            unique[key] = dict(record, cards=list(record.get('cards', [])), references=1)
            continue
        previous = unique[key]
        previous['references'] += 1
        if previous['amount'] != record['amount'] or previous.get('raw') != record.get('raw'):
            previous['amount'] = None  # Conflicting representations are never reconciled.
            previous['source_consistent'] = False
        if previous.get('program_group') != record.get('program_group'):
            previous['program_group'] = 'unallocated'
        for card in record.get('cards', []):
            if card not in previous['cards']:
                previous['cards'].append(card)
    return list(unique.values())


def economic_contribution(parsed, department, source, category, spec):
    table = source_table(parsed, source.get('table_number'))
    rows = [r for r, values in enumerate(table['rows'][1:], 1)
            if category in {category_key(c) for c in values[:2]}]
    columns = [c for c, header in enumerate(table['rows'][0] if table['rows'] else [])
               if _value_kind(header) == spec]
    values = [v for v in source['values'] if (v['category'], v['year'], v['kind'], v['funding_type'])
              == (category, *spec, 'inside')]
    value = values[0] if len(values) == 1 else {}
    amount = Decimal(str(value['amount'])) if value.get('amount') is not None else None
    cards = [card_reference(parsed, department, b) for b in department['blocks']
             if b.get('table_number') in source.get('block_table_numbers', [])]
    context = dict(department=department.get('name', '—'), cards=cards,
                   program_group=value.get('program_group'), source_amount=amount)
    if len(rows) == len(columns) == 1:
        result = cell_reference(table, rows[0], columns[0], **context)
        # Preserve the importer's financing/unknown-value gates as well as the
        # physical book cell. A plausible raw number cannot bypass those gates.
        result['source_consistent'] = result['amount'] == amount
        if not result['source_consistent']:
            result['amount'] = None
        return result
    return dict(page=table['page'], table=table['id'], row='—', column='—',
                label=ECONOMIC_CATEGORIES[category], raw=value.get('raw_text'), amount=None,
                source_consistent=False, **context)


def economic_checks(table, groups, parsed):
    results = row_checks(table, groups)
    total = total_row(table, 'butceicitoplamkaynak', results)
    categories = {_label_key(label): key for key, label in ECONOMIC_CATEGORIES.items()}
    category_rows = {r: categories[_label_key(row[0])] for r, row in enumerate(table['rows'])
                     if _label_key(row[0]) in categories}
    if total is not None:
        children = list(range(2, total))
        columns = column_checks(table, {total: children}, range(1, len(table['rows'][0])))
        unknown = [r for r in children if r not in category_rows]
        if unknown:
            results.append(missing(table, 'Ekonomik kategoriler',
                                   'Tanınmayan kategori satırları: ' + ', '.join(str(r + 1) for r in unknown)))
            for f in columns:
                f['status'], f['classification'] = 'FAIL', 'CHECK'
                f['note'] += '; tanınmayan satırların toplam kapsamına girdiği doğrulanamadı.'
        results += columns
    for row, category in category_rows.items():
        for year, components, column in groups:
            if category == 'reserve':
                # This is an institution-only appropriation, never an inferred
                # directorate shortfall. Its arithmetic is checked above.
                continue
            kind = 'budget' if year == 2027 else 'forecast'
            records = []
            allocations = defaultdict(list)
            for department in parsed['departments']:
                for source in department.get('economic_tables', []):
                    # Omitted categories are outside the printed-cell sum;
                    # provided but unreadable cells remain unknown.
                    if category in source['categories']:
                        records.append(economic_contribution(parsed, department, source, category, (year, kind)))
            records = unique_contributions(records)
            contributors = [r['amount'] for r in records]
            if any(not d.get('economic_tables') for d in parsed['departments']):
                contributors.append(None)
            for value in records:
                amount = value['amount']
                for group in ('service', 'management', 'outside_program'):
                    known = value.get('program_group') in {'service', 'management', 'outside_program'}
                    allocations[group].append(
                        amount if value.get('program_group') == group else
                        ZERO if known or amount == ZERO else None)
            results.append(finding(table, 'Müdürlük ekonomik çapraz toplamı', row, column,
                                   complete_sum(contributors),
                                   contributors=records,
                                   failure_class='CHECK' if any(not r.get('source_consistent', True) for r in records) else 'UNKNOWN',
                                   printed_components=[cell_reference(table, row, c) for c in components],
                                   basis='Kurum hücresi aynı kategorinin basılı program-grubu sütunlarını kapsar. '
                                   'Müdürlük hesabı her ekonomik kaynak hücresini bir kez içerir; kart sayısı ile çarpılmaz.',
                                   note=f'{year}: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori={ECONOMIC_CATEGORIES[category]}. '
                                   'Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. '
                                   'Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). '
                                   'Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN).'))
            for group, col in zip(('service', 'management', 'outside_program'), components):
                complete = None not in contributors and bool(contributors)
                results.append(finding(table, 'Müdürlük program grubu çapraz toplamı', row, col,
                                       complete_sum(allocations[group]) if complete else None,
                                       contributors=records,
                                       printed_components=[cell_reference(table, row, col)],
                                       failure_class='CHECK' if not complete or None in allocations[group] else 'UNKNOWN',
                                       note=f'{year}: {at(table, 1, col)}. '
                                       'Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa '
                                       'hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN).'))
    return results


def detail_coverage(table, results):
    activity_total = total_row(table, 'faaliyetmaliyetleriara', results)
    management = total_row(table, 'kurumsalgenelyonetimgiderleri', results)
    grand = total_row(table, 'geneltoplam', results)
    nodes = []
    end = activity_total if activity_total is not None else len(table['rows'])
    for r, row in enumerate(table['rows'][2:end], 2):
        match = re.match(r'^\((\d+(?:\.\d+)*)\)\s*(.+)', row[0] or '')
        if match:
            nodes.append((r, tuple(match[1].split('.'))))
    coverage = {}
    for index, (row, code) in enumerate(nodes):
        end = next((r for r, c in nodes[index + 1:] if len(c) <= len(code)),
                   activity_total if activity_total is not None else len(table['rows']))
        children = [r for r, c in nodes[index + 1:] if r < end and len(c) == len(code) + 1 and c[:-1] == code]
        coverage[row] = children or list(range(row + 1, end))
    roots = [r for r, code in nodes if len(code) == 1]
    if not roots:
        results.append(missing(table, 'Program / alt program', 'Kodlu program satırları okunamadı; kaynak tabloyu kontrol edin.'))
    codes = [code for _, code in nodes]
    if len(codes) != len(set(codes)) or any(len(code) > 1 and code[:-1] not in codes for code in codes):
        results.append(missing(table, 'Program / alt program kapsamı',
                               'Yinelenen kod veya eksik üst program; sütun kapsamı doğrulanamadı (CHECK).'))
    if activity_total is not None:
        coverage[activity_total] = roots
    if management is not None and grand is not None:
        coverage[management] = list(range(management + 1, grand))
    if grand is not None and activity_total is not None and management is not None:
        coverage[grand] = [activity_total, management]
    return coverage, roots


def programme_contributions(parsed):
    """Retain the physical membership cells and every referring card."""
    amounts = defaultdict(list)
    shared = defaultdict(set)
    for department in parsed['departments']:
        for block in department['blocks']:
            members = block.get('activity_memberships', [])
            card = card_reference(parsed, department, block)
            programme = programme_key(block['program'])
            if not members:
                for spec in ((2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')):
                    amounts[(programme, *spec)].append(dict(
                        department=department.get('name', '—'), cards=[card], page=card['page'],
                        table=card['table'], row='—', column='—', label=None, raw=None, amount=None))
                continue
            for member in members:
                source = source_table(parsed, member['table_number'])
                rows = source['rows']
                columns = defaultdict(list)
                for col, header in enumerate(rows[1] if len(rows) > 1 else []):
                    if spec := _value_kind(header):
                        columns[spec].append(col)
                for spec in ((2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')):
                    cols = columns[spec]
                    r = member['row_number'] - 1
                    context = dict(department=department.get('name', '—'), cards=[card])
                    if len(cols) == 1 and r < len(rows) and cols[0] < len(rows[r]):
                        record = cell_reference(source, r, cols[0], scope_proven=True, **context)
                        shared[physical_cell(record)].add(programme)
                    else:
                        record = dict(page=source['page'], table=source['id'], row=r + 1, column='—',
                                      label=member.get('name'), raw=None, amount=None, scope_proven=False, **context)
                    amounts[(programme, *spec)].append(record)
    return {key: [dict(r, shared_programmes=sorted(shared[physical_cell(r)]))
                  for r in unique_contributions(records)] for key, records in amounts.items()}


def activity_key(label):
    return _label_key(re.sub(r'^\s*\d+[.)\s]+', '', label or ''))


def leaf_rows(coverage, row):
    if row not in coverage:
        return [row]
    return [leaf for child in coverage[row] for leaf in leaf_rows(coverage, child)]


def detail_checks(table, groups, parsed):
    results = row_checks(table, groups)
    coverage, roots = detail_coverage(table, results)
    coverage_invalid = any(f['label'] == 'Program / alt program kapsamı' for f in results)
    columns = column_checks(table, coverage, range(1, len(table['rows'][0])))
    for f in columns:
        if _label_key(f['label']).startswith('faaliyetmaliyetleriara'):
            f['coverage_basis'] = (
                'Ara toplamdan önceki kapalı program bloğunun birinci düzey (n) satırları birer kez toplanır. '
                'İkinci düzey (n.m) satırları ve faaliyetler bunların içinde olduğundan ayrıca eklenmez. '
                'Sonraki Kurumsal Genel Yönetim Giderleri ve Genel Toplam bu ara toplamın dışında tutulur.')
    if coverage_invalid:
        for f in columns:
            f['status'], f['classification'] = 'FAIL', 'CHECK'
            f['note'] += '; program kodları kapsamı tekil olarak belirlemiyor.'
    results += columns
    amounts = programme_contributions(parsed)
    matched = set()
    for row in roots:
        label = re.sub(r'^\([\d.]+\)\s*', '', at(table, row, 0))
        matched.add(programme_key(label))
        for year, _, total in groups:
            spec = (programme_key(label), year, 'budget' if year == 2027 else 'forecast')
            records = amounts.get(spec, [])
            leaves = leaf_rows(coverage, row)
            summary_names = Counter(activity_key(at(table, r, 0)) for r in leaves)
            source_names = Counter(activity_key(r['label']) for r in records)
            summary_only = summary_names - source_names
            source_only = source_names - summary_names
            comparable = (bool(records) and bool(leaves) and not coverage_invalid
                          and summary_names == source_names
                          and all(r.get('scope_proven', False) for r in records)
                          and all(len(r.get('shared_programmes', [])) <= 1 for r in records))
            result = finding(table, 'Müdürlük program çapraz toplamı', row, total,
                                   complete_sum(r['amount'] for r in records),
                                   contributors=records,
                                   printed_components=[cell_reference(table, r, total) for r in coverage.get(row, [])],
                                   failure_class='UNKNOWN' if comparable else 'CHECK',
                                   basis='Basılı program toplamı kodlu alt programlarını; alt programlar kendi faaliyet satırlarını kapsar. '
                                   'Müdürlük hesabı ise aynı program adıyla etiketlenmiş üyelik hücrelerini kapsar. '
                                   'Bu iki faaliyet kümesi tekil ve aynı olmadıkça eşitlik doğrulanmaz.',
                                   note=f'{year}: kartlara bağlı üyelik tablolarındaki program tutarları; '
                                   'ekonomik kategoriler programlara paylaştırılmadı. '
                                   f'Katkı hücresi: {len(records)}. '
                                   + ('Faaliyet kapsamları eşleşiyor; sayısal fark olursa hangi basılı kaynağın yanlış olduğu belirlenemez (UNKNOWN).'
                                      if comparable else 'Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); '
                                      'hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir.'))
            result['printed_leaves'] = [cell_reference(table, r, total) for r in leaves]
            result['coverage'] = dict(comparable=comparable, summary_only=list(summary_only.elements()),
                                      directorate_only=list(source_only.elements()))
            if not comparable:
                # An accidental numeric equality must never certify unlike scopes.
                result['status'], result['classification'] = 'FAIL', 'CHECK'
            results.append(result)
    for key in sorted({key[0] for key in amounts} - matched):
        labels = sorted({b['program'] for d in parsed['departments'] for b in d['blocks']
                         if programme_key(b['program']) == key})
        results.append(missing(table, '; '.join(labels),
                               'Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; '
                               'taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi.'))
        results[-1]['check'] = 'Program adı eşlemesi'
    return results


def percentage_unit(raw):
    text = str(raw or '').strip().rstrip('%').strip()
    decimals = len(text.rsplit(',', 1)[1]) if ',' in text else 0
    return Decimal(1).scaleb(-decimals)


def share_checks(table):
    results = []
    if len(table['rows'][0]) != 3 or not re.search(r'20\d{2}', str(at(table, 0, 1))):
        return [missing(table, 'Başlık', 'Yıl / tutar / oran sütunları okunamadı; kaynak tabloyu kontrol edin.')]
    total = total_row(table, 'toplam', results)
    if total is None:
        return results
    rows = list(range(1, total))
    grand = read_number(at(table, total, 1))
    results += column_checks(table, {total: rows}, [1])
    for row in [*rows, total]:
        amount = read_number(at(table, row, 1))
        ratio = amount / grand * 100 if amount is not None and grand is not None and grand > 0 else None
        unit = percentage_unit(at(table, row, 2))
        item = finding(table, 'Yüzde oranı', row, 2, ratio,
                       note='Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır.',
                       failure_class='BOOK',
                       contributors=[cell_reference(table, row, 1), cell_reference(table, total, 1)],
                       printed_components=[cell_reference(table, row, 1), cell_reference(table, total, 1)])
        # Quantization, instead of a symmetric epsilon, gives exact half-way
        # boundaries the same ROUND_HALF_UP treatment as printed percentages.
        item['status'] = ('PASS' if ratio is not None and item['printed'] is not None
                          and item['printed'] == ratio.quantize(unit, rounding=ROUND_HALF_UP) else 'FAIL')
        item['classification'] = None if item['status'] == 'PASS' else ('BOOK' if ratio is not None else 'UNKNOWN')
        results.append(item)
    percentages = complete_sum(read_number(at(table, r, 2), money=False) for r in rows)
    tolerance = sum((percentage_unit(at(table, r, 2)) / 2 for r in rows), ZERO)
    results.append(finding(table, 'Yüzdeler toplamı', total, 2, percentages,
                           note=f'Yuvarlama toleransı: {format_number(tolerance)}; hesaplanan = satır yüzdeleri toplamı.',
                           tolerance=tolerance, failure_class='BOOK',
                           contributors=[cell_reference(table, r, 2) for r in rows],
                           printed_components=[cell_reference(table, r, 2) for r in rows]))
    # The grand row's own ratio check above independently requires 100, so an
    # equally wrong printed grand percentage cannot legitimize the row sum.
    return results


def review_evidence(findings):
    """Select the lead's nine cells by semantic role, never page or table ID."""
    selected = []
    for f in findings:
        label = _label_key(f['label'])
        if (f['check'] == 'Müdürlük program çapraz toplamı'
                and programme_key(re.sub(r'^\([\d.]+\)\s*', '', f['label'])) == programme_key('Yönetim ve Destek Programı')):
            selected.append(f)
        elif f['check'] == 'Müdürlük ekonomik çapraz toplamı' and (
                label == _label_key(ECONOMIC_CATEGORIES['goods_services']) and f['year'] in (2028, 2029)
                or label == _label_key(ECONOMIC_CATEGORIES['capital']) and f['year'] == 2028):
            selected.append(f)
        elif (f['check'] == 'Sütun toplamı' and label.startswith('faaliyetmaliyetleriara')
              and _label_key(f['column_header']) == 'butceicitl'):
            selected.append(f)
    return selected


def audit_institution_tables(parsed):
    results = []
    inventory = []
    reserves = []
    sources = parsed.get('institution_tables', [])
    for kind, name in TABLE_NAMES.items():
        tables = [dict(t, kind=kind) for t in sources if table_kind(t) == kind]
        if not tables:
            table = dict(kind=kind, rows=[], id='—', page='?')
            results.append(missing(table, name, 'Tablo bulunamadı; IDML kaynağındaki başlıkları kontrol edin. '
                                   'Üretilen yükleme Word dosyası kurum özetlerini içermez.'))
        for table in tables:
            inventory.append(dict(name=name, id=table['id'], page=table['page']))
            if table.get('page') == '?':
                results.append(missing(table, name, 'Tablo basılı sayfaya bağlı değil; kaynak yerleşimini kontrol edin.'))
                continue
            try:
                if kind == 'share':
                    results += share_checks(table)
                else:
                    groups = year_groups(table)
                    if kind == 'economic':
                        for row, values in enumerate(table['rows']):
                            if _label_key(values[0]) == 'yedekodenekler':
                                for year, components, total in groups:
                                    reserves.append(dict(page=table['page'], table=table['id'], row=row + 1,
                                                         year=year, values=[at(table, row, c) for c in [*components, total]]))
                    results += (economic_checks if kind == 'economic' else detail_checks)(table, groups, parsed)
            except (ValueError, TypeError, IndexError, KeyError):
                results.append(missing(table, name, 'Başlık / satır yapısı okunamadı; kaynak tabloyu kontrol edin.'))
    for f in results:
        if f['status'] == 'PASS':
            f['classification'] = None
        assert f['status'] != 'FAIL' or f['classification'] in {'BOOK', 'CHECK', 'UNKNOWN'}
    counts = Counter(f['classification'] for f in results if f['status'] == 'FAIL')
    return dict(findings=results, tables=inventory, reserves=reserves,
                classes={k: counts[k] for k in ('BOOK', 'CHECK', 'UNKNOWN')},
                evidence=review_evidence(results))
