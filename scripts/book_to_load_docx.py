#!/usr/bin/env python3
"""Convert print IDML tables to the first-load Word format, without InDesign.

Usage: python scripts/book_to_load_docx.py BOOK.idml name_map.json OUT.docx
The adjacent OUT.docx.report.json records mapping and source table/page provenance.
Unplaced stories are reported, rather than treated as printed book data.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.first_load_sources import FIRST_LOAD_BOOKS

def norm(text):
    text = (text or '').replace('İ', 'i').replace('I', 'ı').lower()
    return re.sub(r'[^0-9a-zçğıöşü]+', '', text)


def table_type(table):
    first = norm(table['rows'][0][0]) if table['rows'] else ''
    for prefix, kind in [('bütçeyılı', 'card'), ('altprogramkapsamında', 'membership'),
                         ('faaliyetler', 'cost'), ('ekonomikad', 'economic')]:
        if first.startswith(prefix):
            return kind
    return 'other'


def extract_tables(path, *, excluded=None, reading_order=False):
    """Read the ZIP directly; retain the legacy span grid and print spread order."""
    with ZipFile(path) as archive:
        def xml(src):
            return ET.fromstring(archive.read(src))

        design = xml('designmap.xml')
        from scripts.idml_printed import story_locations
        stories, story_pages, spread_pages = story_locations(archive, design)
        positions = _story_positions(archive, design, story_pages) if reading_order else {}
        tables = []
        for story in stories:
            sid = story.get('Self')
            spread_index, page = story_pages.get(sid, (9999, '?'))
            for node in story.iter('Table'):
                ncols = int(node.attrib['ColumnCount'])
                nrows = sum(int(node.get(k, 0)) for k in ('BodyRowCount', 'HeaderRowCount', 'FooterRowCount'))
                rows = [[None] * ncols for _ in range(nrows)]
                for cell in node.findall('Cell'):
                    col, row = map(int, cell.attrib['Name'].split(':'))
                    rs, cs = int(cell.get('RowSpan', 1)), int(cell.get('ColumnSpan', 1))
                    parts = [n.text or '' if n.tag == 'Content' else ' '
                             for n in cell.iter() if n.tag in {'Content', 'Br'}]
                    rows[row][col] = re.sub(r'\s+', ' ', ''.join(parts)).strip()
                    for r in range(row, min(row + rs, nrows)):
                        for c in range(col, min(col + cs, ncols)):
                            if (r, c) != (row, col):
                                rows[r][c] = '→' if r == row else '↓'
                table = dict(id=node.get('Self'), story=sid, spread=spread_index, page=page, rows=rows)
                if reading_order and sid in story_pages:
                    if sid not in positions:
                        raise ValueError(f's.{page}: tablo okuma sırası belirlenemedi; yerleşimi kontrol edin.')
                    table['position'] = (*positions[sid], len(tables))
                if sid in story_pages:
                    tables.append(table)
                elif excluded is not None:
                    excluded.append(dict(table, spread_pages=spread_pages.get(sid, []),
                                         reason='pasteboard' if sid in spread_pages else 'unplaced'))
        return tables


def _story_positions(archive, design, story_pages):
    """Printed frame geometry, rather than export IDs, defines 2026 section order."""
    from scripts.idml_printed import IDENTITY, compose, transform, rectangle, intersects
    positions = {}
    for index, entry in enumerate(e for e in design if e.tag.endswith('Spread')
                                 and e.get('src', '').startswith('Spreads/')):
        pages, frames = {}, []
        def walk(node, parent=IDENTITY):
            matrix = compose(parent, transform(node))
            if node.tag == 'Page':
                top, left, bottom, right = map(float, node.get('GeometricBounds').split())
                pages[node.get('Name')] = rectangle([(left, top), (right, bottom)], matrix)
            if node.tag == 'TextFrame' and node.get('ParentStory'):
                points = [tuple(map(float, p.get('Anchor').split()))
                          for p in node.findall('./Properties//PathPointArray/PathPointType')]
                if points:
                    frames.append((node.get('ParentStory'), rectangle(points, matrix)))
            for child in node:
                walk(child, matrix)
        walk(ET.fromstring(archive.read(entry.get('src'))))
        for sid, bounds in frames:
            spread, page = story_pages.get(sid, (None, None))
            if spread == index and page in pages and intersects(bounds, pages[page]):
                position = (bounds[1], bounds[0])
                positions[sid] = min(positions.get(sid, position), position)
    return positions


GUIDANCE_2026 = {
    '*Alt program kapsamında ilgili mevzuata göre idareye verilen hangi görevlerin yürütüldüğü ve Kalkınma Planı, Stratejik Plan gibi üst politika belgelerinde yer alan hedeflerden hangilerine ulaşılmasına katkı sağlandığına ilişkin açıklamalara yer verilecektir.',
    '*Alt program hedefine ilişkin kısa ve öz bilgilere yer verilecektir.',
}


def prepare_2026_tables(extracted, names):
    """Associate named book sections before moving economic tables next to cards."""
    grouped, book_names, descriptions, dropped = {}, {}, [], []
    current = description_department = None
    unmapped = []
    for source in extracted:
        raw_names = ([r[1] for r in source['rows'] if norm(r[0]) == 'sorumluidare']
                     if table_type(source) == 'card' else
                     [source['rows'][0][1]] if norm(source['rows'][0][0]) == 'idarebirimadı' else [])
        unmapped.extend(f"s.{source['page']}: {(raw or '').split('/')[-1].strip()}" for raw in raw_names
                        if norm((raw or '').split('/')[-1]) not in names)
    if unmapped:
        raise ValueError('2026 müdürlük eşleşmesi yok: ' + '; '.join(sorted(set(unmapped)))
                         + '. Ad eşleme dosyasını sorumluya doğrulatın.')
    def mapped(raw, page):
        base = (raw or '').split('/')[-1].strip()
        if norm(base) not in names:
            raise ValueError(f's.{page}: müdürlük eşleşmesi yok: {base}. Ad eşleme dosyasını sorumluya doğrulatın.')
        return names[norm(base)]
    for source in sorted(extracted, key=lambda t: (int(t['page']), t['position'])):
        kind = table_type(source)
        rows = source['rows']
        if kind == 'card':
            responsible = [r[1] for r in rows if norm(r[0]) == 'sorumluidare']
            if len(responsible) != 1 or not responsible[0]:
                raise ValueError(f"s.{source['page']}: tek Sorumlu İdare gerekli; kartı kontrol edin.")
            current = mapped(responsible[0], source['page'])
            canonical = responsible[0].strip()
            if current in book_names and book_names[current] != canonical:
                raise ValueError(f'{current}: Sorumlu İdare adları çelişiyor; kitabı kontrol edin.')
            book_names[current] = canonical
            kept, source_rows = [], []
            for number, row in enumerate(rows, 1):
                full = row[1:] and all(c == '→' for c in row[1:])
                if full and row[0] in GUIDANCE_2026:
                    dropped.append(dict(page=source['page'], id=source['id'], row=number, text=row[0]))
                    continue
                if full and norm(row[0]) != 'performansgöstergeleri':
                    raise ValueError(f"s.{source['page']}: bilinmeyen tam satır: {row[0]}. Kaynağı sorumluya inceletin.")
                kept.append(row)
                source_rows.append(number)
            source = dict(source, rows=kept, source_rows=source_rows)
        elif norm(rows[0][0]) == 'idarebirimadı':
            fields = {norm(r[0]): r[1] for r in rows}
            description_department = mapped(fields['idarebirimadı'], source['page'])
            required = ('programadı', 'altprogramadı', 'faaliyetadı', 'açıklama')
            if any(not fields.get(k) for k in required):
                raise ValueError(f"s.{source['page']}: faaliyet açıklama tablosu eksik; kaynağı kontrol edin.")
            descriptions.append(dict(department=description_department, program=fields['programadı'],
                subprogram=fields['altprogramadı'], name=fields['faaliyetadı'], explanation=fields['açıklama'],
                page=source['page'], id=source['id']))
            continue
        elif kind == 'economic':
            if not description_department:
                raise ValueError(f"s.{source['page']}: ekonomik tablonun müdürlük başlığı yok.")
        elif kind != 'cost':
            continue
        department = description_department if kind == 'economic' else current
        if not department:
            raise ValueError(f"s.{source['page']}: {kind} tablosunun müdürlüğü yok.")
        grouped.setdefault(department, []).append(dict(source, department=department))
        if kind in {'card', 'cost', 'economic'}:
            from app.data_importer import _indicator_header_spec
            header = next((r for r in source['rows'] if norm(r[0]) == 'performansgöstergesi'), None) if kind == 'card' else rows[0]
            start = 3 if kind == 'card' else (2 if kind == 'economic' else 1)
            specs = [_indicator_header_spec(h or '') for h in header[start:]] if header else []
            if not specs or None in specs or len(set(specs)) != len(specs):
                raise ValueError(f"s.{source['page']}: başlık yıl/değer türü tekil değil; sütunları kontrol edin.")
    if set(grouped) != set(book_names) or any(d['department'] not in book_names for d in descriptions):
        raise ValueError('Kart, açıklama ve ekonomik tablo müdürlük kapsamları uyuşmuyor; kitabı kontrol edin.')
    return [t for group in grouped.values() for t in sorted(group, key=lambda t: {'card': 0, 'cost': 1, 'economic': 2}[table_type(t)])], book_names, descriptions, dropped


def generate_docx(idml, name_map, output, *, year=2027):
    mapping = json.loads(Path(name_map).read_text(encoding='utf-8'))
    names = {norm(k): v for k, v in mapping['map'].items()}
    names.update({norm(v): v for v in mapping['map'].values()})
    if year == 2026:
        extra = json.loads((Path(__file__).resolve().parents[1] / 'tests/fixtures/first_load/name_map_2026.json').read_text(encoding='utf-8'))
        names.update({norm(k): v for k, v in extra['map'].items()})
        names.update({norm(v): v for v in extra['map'].values()})
        names[norm('Yapı Kontrol Müdürlüğü')] = 'Yapı Kontrol Müdürlüğü'
    excluded = []
    extracted = extract_tables(idml, excluded=excluded, reading_order=year == 2026)
    kinds = {'card': 0, 'membership': 1, 'cost': 2, 'economic': 3}
    tables = [t for t in extracted if table_type(t) in kinds and t['page'] != '?']
    tables.sort(key=lambda t: (int(t['page']) if t['page'].isdigit() else 10**6,
                               t['spread'], kinds[table_type(t)], t['id']))
    card_pages = Counter(t['page'] for t in tables if table_type(t) == 'card')
    ambiguous = sorted(page for page, count in card_pages.items() if count > 1)
    if ambiguous and year == 2027:
        raise ValueError('Aynı sayfada birden fazla kart bulundu; faaliyet üyeliği sırası belirsiz. '
                         'Kitap kart yerleşimini kontrol edin: ' + ', '.join(ambiguous))
    report = dict(departments=[], unmapped=[], tables=[],
                  unplaced=[{'id': t['id'], 'type': table_type(t)} for t in excluded
                            if t['reason'] == 'unplaced' and table_type(t) in kinds],
                  non_printed=[dict(id=t['id'], story=t['story'], spread_pages=t['spread_pages'],
                                    header=t['rows'][0][:4] if t['rows'] else [], reason=t['reason'])
                               for t in excluded])
    if year == 2026:
        tables, book_names, descriptions, dropped = prepare_2026_tables(extracted, names)
        report.update(book_department_names=book_names, catalogue_descriptions=descriptions,
                      dropped_guidance=dropped)
    doc = Document()
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal'].font.size = Pt(9)
    current = None

    def system_name(raw):
        base = (raw or '').split('/')[-1].strip()
        if norm(base) not in names:
            report['unmapped'].append(raw)
        return names.get(norm(base), base)

    for source in tables:
        kind = table_type(source)
        rows = [list(row) for row in source['rows']]
        indicator_rows = set()
        if kind == 'card':
            for row in rows:
                if norm(row[0]).startswith(('idarebirim', 'sorumluidare')):
                    if year == 2027 or norm(row[0]).startswith('idarebirim'):
                        row[1] = source['department'] if year == 2026 else system_name(row[1])
            dept = next(row[1] for row in rows if norm(row[0]).startswith('idarebirim'))
            if dept != current:
                doc.add_heading(dept, level=2)
                current = dept
                report['departments'].append(dept)
            start = next(i for i, row in enumerate(rows) if (norm(row[0]) == 'performansgöstergesi'
                         if year == 2026 else (row[0] or '').startswith('Performans Göstergesi')))
            end = next((i for i, row in enumerate(rows) if norm(row[0]).startswith('göstergeyeilişkin')), len(rows))
            indicator_rows = set(range(start, end))
        provenance = dict(table_number=len(report['tables']) + 1, page=source['page'],
                          id=source['id'], type=kind, department=current)
        if year == 2026 and 'source_rows' in source:
            provenance['source_rows'] = source['source_rows']
        report['tables'].append(provenance)
        table = doc.add_table(rows=len(rows), cols=max(map(len, rows)))
        ncols = len(table.columns)
        cells = table._cells
        table.style = 'Table Grid'
        caption = OxmlElement('w:tblCaption')
        caption.set(qn('w:val'), json.dumps(provenance, ensure_ascii=False))
        table._tbl.tblPr.append(caption)
        for ri, row in enumerate(rows):
            col = 0
            while col < len(row):
                span = 1
                while col + span < len(row) and row[col + span] == '→':
                    span += 1
                cell = cells[ri * ncols + col]
                if span > 1 and ri not in indicator_rows:
                    cell = cell.merge(cells[ri * ncols + col + span - 1])
                cell.text = '' if row[col] in (None, '→', '↓') else row[col]
                col += span
        doc.add_paragraph('')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    report['unmapped'] = sorted(set(report['unmapped']))
    report['counts'] = dict(Counter(t['type'] for t in report['tables']))
    Path(str(output) + '.report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('idml', type=Path)
    parser.add_argument('name_map', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    report = generate_docx(args.idml, args.name_map, args.output)
    print(json.dumps({'counts': report['counts'], 'unmapped': report['unmapped'],
                      'unplaced': report['unplaced'], 'non_printed': report['non_printed']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
