"""Read-only institution checks for the first-load rehearsal, never the importer.

Table selection uses printed headings. Page and ID are evidence only. Arithmetic
uses Decimal and fails closed for absent, ambiguous or unreadable source cells.
"""
from collections import defaultdict
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


def finding(table, check, row, column, computed, *, note='', tolerance=ZERO, printed=None):
    raw = at(table, row, column) if printed is None else printed
    value = read_number(raw, money=not check.startswith('Yüzde'))
    difference = value - computed if value is not None and computed is not None else None
    return dict(status='PASS' if difference is not None and abs(difference) <= tolerance else 'FAIL',
                check=check, page=table.get('page', '?'), table=table.get('id', '?'),
                name=TABLE_NAMES[table['kind']], row=row + 1 if row is not None else '—',
                label=at(table, row, 0) or '—', column=column + 1, printed=value,
                raw=raw, computed=computed, difference=difference, note=note)


def missing(table, label, note):
    result = finding(table, 'Okuma / kapsam', None, 0, None, note=note)
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
                    note=f'{year}: bileşen sütunları ' + ', '.join(str(c + 1) for c in components))
            for row in range(2, len(table['rows'])) for year, components, total in groups]


def column_checks(table, coverage, columns):
    """Coverage lists direct children only, so nested subtotals are not doubled."""
    return [finding(table, 'Sütun toplamı', total, column,
                    complete_sum(read_number(at(table, r, column)) for r in children),
                    note='Kapsanan satırlar: ' + ', '.join(str(r + 1) for r in children))
            for total, children in coverage.items() for column in columns]


def total_row(table, prefix, findings):
    matches = [r for r, row in enumerate(table['rows']) if _label_key(row[0]).startswith(prefix)]
    if len(matches) != 1:
        findings.append(missing(table, prefix, 'Tekil toplam satırı bulunamadı; kaynak tabloyu kontrol edin.'))
        return None
    return matches[0]


def economic_checks(table, groups, parsed):
    results = row_checks(table, groups)
    total = total_row(table, 'butceicitoplamkaynak', results)
    categories = {_label_key(label): key for key, label in ECONOMIC_CATEGORIES.items()}
    category_rows = {r: categories[_label_key(row[0])] for r, row in enumerate(table['rows'])
                     if _label_key(row[0]) in categories}
    if total is not None:
        children = list(range(2, total))
        results += column_checks(table, {total: children}, range(1, len(table['rows'][0])))
        unknown = [r for r in children if r not in category_rows]
        if unknown:
            results.append(missing(table, 'Ekonomik kategoriler',
                                   'Tanınmayan kategori satırları: ' + ', '.join(str(r + 1) for r in unknown)))
    tables = [t for d in parsed['departments'] for t in d.get('economic_tables', [])]
    for row, category in category_rows.items():
        for year, components, column in groups:
            if category == 'reserve':
                # This is an institution-only appropriation, never an inferred
                # directorate shortfall. Its arithmetic is checked above.
                continue
            kind = 'budget' if year == 2027 else 'forecast'
            contributors = []
            allocations = defaultdict(list)
            if any(not d.get('economic_tables') for d in parsed['departments']):
                contributors.append(None)
            for source in tables:
                # Compact directorate tables do not provide every category.
                # Sum printed category cells only; report this scope explicitly.
                if category not in source['categories']:
                    continue
                values = [v for v in source['values'] if (v['category'], v['year'], v['kind'])
                          == (category, year, kind)]
                selected = [v for v in values if v['funding_type'] == 'inside']
                value = selected[0] if len(selected) == 1 else {}
                amount = Decimal(str(value['amount'])) if value.get('amount') is not None else None
                contributors.append(amount)
                for group in ('service', 'management', 'outside_program'):
                    known = value.get('program_group') in {'service', 'management', 'outside_program'}
                    allocations[group].append(
                        amount if value.get('program_group') == group else
                        ZERO if known or amount == ZERO else None)
            results.append(finding(table, 'Müdürlük ekonomik çapraz toplamı', row, column,
                                   complete_sum(contributors),
                                   note=f'{year}: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori={ECONOMIC_CATEGORIES[category]}. '
                                   'Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz.'))
            for group, col in zip(('service', 'management', 'outside_program'), components):
                complete = None not in contributors and bool(contributors)
                results.append(finding(table, 'Müdürlük program grubu çapraz toplamı', row, col,
                                       complete_sum(allocations[group]) if complete else None,
                                       note=f'{year}: {at(table, 1, col)}. '
                                       'Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa '
                                       'hesaplanamaz; paylaştırma yapılmadı.'))
    return results


def detail_coverage(table, results):
    activity_total = total_row(table, 'faaliyetmaliyetleriara', results)
    management = total_row(table, 'kurumsalgenelyonetimgiderleri', results)
    grand = total_row(table, 'geneltoplam', results)
    nodes = []
    for r, row in enumerate(table['rows'][2:], 2):
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
    if activity_total is not None:
        coverage[activity_total] = roots
    if management is not None and grand is not None:
        coverage[management] = list(range(management + 1, grand))
    if grand is not None and activity_total is not None and management is not None:
        coverage[grand] = [activity_total, management]
    return coverage, roots


def programme_amounts(parsed):
    """Use membership amount cells linked to parsed cards, without cost guesses."""
    amounts = defaultdict(list)
    for department in parsed['departments']:
        for block in department['blocks']:
            members = block.get('activity_memberships', [])
            if not members:
                for spec in ((2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')):
                    amounts[(programme_key(block['program']), *spec)].append(None)
                continue
            for member in members:
                source = parsed.get('rehearsal_tables', {}).get(str(member['table_number']), {})
                rows = source.get('book') or source.get('word', [])
                columns = defaultdict(list)
                for col, header in enumerate(rows[1] if len(rows) > 1 else []):
                    if spec := _value_kind(header):
                        columns[spec].append(col)
                for spec in ((2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')):
                    cols = columns[spec]
                    r = member['row_number'] - 1
                    raw = rows[r][cols[0]] if len(cols) == 1 and r < len(rows) and cols[0] < len(rows[r]) else None
                    amounts[(programme_key(block['program']), *spec)].append(read_number(raw))
    return amounts


def detail_checks(table, groups, parsed):
    results = row_checks(table, groups)
    coverage, roots = detail_coverage(table, results)
    results += column_checks(table, coverage, range(1, len(table['rows'][0])))
    amounts = programme_amounts(parsed)
    matched = set()
    for row in roots:
        label = re.sub(r'^\([\d.]+\)\s*', '', at(table, row, 0))
        matched.add(programme_key(label))
        for year, _, total in groups:
            spec = (programme_key(label), year, 'budget' if year == 2027 else 'forecast')
            results.append(finding(table, 'Müdürlük program çapraz toplamı', row, total,
                                   complete_sum(amounts.get(spec, [])),
                                   note=f'{year}: kartlara bağlı üyelik tablolarındaki program tutarları; '
                                   'ekonomik kategoriler programlara paylaştırılmadı. '
                                   f"Katkı hücresi: {len(amounts.get(spec, []))}."))
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
                       note='Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır.')
        # Quantization, instead of a symmetric epsilon, gives exact half-way
        # boundaries the same ROUND_HALF_UP treatment as printed percentages.
        item['status'] = ('PASS' if ratio is not None and item['printed'] is not None
                          and item['printed'] == ratio.quantize(unit, rounding=ROUND_HALF_UP) else 'FAIL')
        results.append(item)
    percentages = complete_sum(read_number(at(table, r, 2), money=False) for r in rows)
    tolerance = sum((percentage_unit(at(table, r, 2)) / 2 for r in rows), ZERO)
    results.append(finding(table, 'Yüzdeler toplamı', total, 2, percentages,
                           note=f'Yuvarlama toleransı: {format_number(tolerance)}; hesaplanan = satır yüzdeleri toplamı.',
                           tolerance=tolerance))
    # The grand row's own ratio check above independently requires 100, so an
    # equally wrong printed grand percentage cannot legitimize the row sum.
    return results


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
    return dict(findings=results, tables=inventory, reserves=reserves)
