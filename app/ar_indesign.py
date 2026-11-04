"""ar-typeset/1 → InDesign Tagged Text in the 2025 Faaliyet Raporu book styles (CIV-179, AR-13).

Pure function: the only input is a verified ar-typeset/1 contract. Output bytes are
UTF-16LE with BOM and the <UNICODE-WIN> header, so InDesign's File > Place applies
the book's own paragraph, table and cell styles (Publication Definition).
Style names come from docs/activity-report/source/2025-faaliyet-raporu.idml.
"""
import re

PROFILE = '2025-faaliyet-raporu'
STYLE = {
    'chapter': 'BOLUM BASLİK',
    'heading': 'arabaslik stun 2',
    'subheading': 'Arabaslik stun',
    'body': 'Metin',
    'caption': 'TABLO',
    'table': 'TABLO 1',
    'head_cell': 'tablo başlık',
    'body_cell': 'tablo yazı',
    'total_cell': 'tablo sonuç',
}
# Unit chapters follow the 2025 book's department chapter headings.
UNIT_TITLES = {
    'I.B': 'Yetki, Görev ve Sorumluluklar',
    'I.C': 'Müdürlüğe İlişkin Bilgiler',
    'II.B': 'Müdürlüğün Amaç ve Hedefleri',
    'III': 'Faaliyetlere İlişkin Bilgi ve Değerlendirmeler',
}
UNIT_HIDDEN = {'I', 'II'}
EMPTY_STATUSES = {'empty', 'not_applicable'}
SKIPPED_KINDS = {'resource_groups', 'department_totals', 'activity_costs'}
NUMBERING = re.compile(r'^\s*(?:[IVX]+|[A-Z]|\d+|[ivx]+)[-.)]\s*')


def escape(text):
    text = '' if text is None else str(text)
    text = text.replace('\\', '\\\\').replace('<', '\\<').replace('>', '\\>')
    # A line break inside stored text becomes a forced line break, not a new paragraph.
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<0x000A>')


def tr_upper(text):
    return (text or '').replace('i', 'İ').replace('ı', 'I').upper()


def plain_title(title):
    return NUMBERING.sub('', title or '').strip()


def cell_text(value):
    if isinstance(value, dict):
        if 'display' in value:
            return '' if value.get('exact') is None and value['display'] == '—' else value['display']
        if 'value' in value:
            return cell_text(value['value'])
        return ''
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Evet' if value else 'Hayır'
    return str(value)


class Writer:
    def __init__(self, contract):
        self.contract = contract
        self.parts = []
        self.table_number = 0
        self.rows = {r['id']: r for r in contract['rows']}
        self.indicators = {i['id']: i for i in contract['indicators']}
        self.activities = {a['id']: a for a in contract['activities']}
        self.tables = {t['id']: t for t in contract['tables']}

    def para(self, style, text):
        self.parts.append(f'<ParaStyle:{escape(style)}>{escape(text)}\r\n')

    def table(self, title, header, body, total=None, keep_header_only=False):
        if not body and not keep_header_only:
            return
        self.table_number += 1
        self.para(STYLE['caption'], f'Tablo {self.table_number}: {title}')
        rows = [header] + body + ([total] if total else [])
        cols = len(header)
        out = [f'<ParaStyle:{escape(STYLE["body"])}><TableStyle:{escape(STYLE["table"])}>'
               f'<TableStart:{len(rows)},{cols}:1:0<tCellDefaultCellType:Text>>']
        out += ['<ColStart:>'] * cols
        for index, row in enumerate(rows):
            cell = STYLE['head_cell'] if index == 0 else (
                STYLE['total_cell'] if total and index == len(rows) - 1 else STYLE['body_cell'])
            paragraph = STYLE['head_cell'] if index == 0 else STYLE['body_cell']
            out.append('<RowStart:>')
            for value in (list(row) + [''] * cols)[:cols]:
                out.append(f'<CellStyle:{escape(cell)}><StylePriority:1><CellStart:1,1>'
                           f'<ParaStyle:{escape(paragraph)}>{escape(value)}<CellEnd:>')
            out.append('<RowEnd:>')
        out.append('<TableEnd:>\r\n')
        self.parts.append(''.join(out))

    def columns(self, table):
        return [(c[0], c[1]) for c in table.get('columns') or []
                if not (c[0].endswith('_id') or c[0] == 'id')]

    def render_table(self, table, title):
        kind = table['kind']
        if kind in SKIPPED_KINDS:
            return
        if kind == 'section':
            rows = [[cell_text(v) for v in self.rows[r]['values']] for r in table['row_ids']]
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [''] * (width - len(r)) for r in rows]
                # A one-row free table is still saved content (validate_blocks accepts it).
                self.table(title, rows[0], rows[1:], keep_header_only=True)
            return
        if kind == 'indicators':
            year = self.contract['document'].get('year')
            body = []
            for rid in table['row_ids']:
                v = self.indicators[rid]['values']
                target = next((t for t in v.get('targets', []) if t.get('year') == year), None)
                actual = cell_text(v.get('actual')) or 'Kayıt yok'
                rate = cell_text((v.get('deviation') or {}).get('achievement_percent'))
                body.append([v.get('name', ''), v.get('unit', ''), cell_text(target['value']) if target else '',
                             actual, rate, v.get('explanation') or ''])
            self.table(table['title'], ['Performans Göstergesi', 'Birim', f'{year} Hedef', 'Gerçekleşme',
                                        'Gerçekleşme Oranı (%)', 'Açıklama'], body)
            return
        if kind == 'activities':
            body = []
            for rid in table['row_ids']:
                data = self.activities[rid]['values'].get('data', {})
                body.append([data.get('program', ''), data.get('subprogram', ''), data.get('name', '')])
            self.table(table['title'], ['Program', 'Alt Program', 'Faaliyet'], body)
            return
        columns = self.columns(table)
        if not columns:
            return
        body = [[cell_text(self.rows[r]['values'].get(key)) for key, _ in columns] for r in table['row_ids']]
        total = None
        totals = table.get('totals') or {}
        if body and totals:
            total = ['Toplam' if i == 0 else cell_text(totals.get(key)) for i, (key, _) in enumerate(columns)]
        self.table(table['title'], [label for _, label in columns], body, total)


def own_content(section, writer):
    if section['values'].get('status') in EMPTY_STATUSES:
        return False
    if any(b.get('text', '').strip() or any(x.strip() for x in b.get('items', []))
           or (b.get('type') == 'table' and writer.tables[b['table_id']].get('row_ids'))
           for b in section['blocks']):
        return True
    return any(writer.tables[t]['kind'] not in SKIPPED_KINDS | {'section'} and writer.tables[t].get('row_ids')
               for t in section['table_ids'])


def printable(section, sections, writer):
    """A heading prints only when the section or a descendant (by EK-1 code) has content."""
    prefix = section['code'] + '.'
    return any(own_content(s, writer) for s in sections if s['code'] == section['code'] or s['code'].startswith(prefix))


def tagged_text(contract):
    """Return deterministic Tagged Text bytes for one ar-typeset/1 contract."""
    if contract.get('schema_version') != 'ar-typeset/1':
        raise ValueError('Desteklenmeyen dizgi sözleşmesi. ar-typeset/1 kullanın.')
    writer = Writer(contract)
    document = contract['document']
    unit = document['scope'] == 'birim'
    sections = sorted(contract['sections'], key=lambda s: (s['values'].get('position') or 0, s['code']))
    writer.parts.append('<UNICODE-WIN>\r\n<Version:19><FeatureSet:InDesign-Roman>')
    if unit:
        writer.para(STYLE['chapter'], tr_upper(document.get('department') or ''))
    if not contract.get('frozen'):
        writer.para(STYLE['body'], 'TASLAK — bu metin onaylı rapor sürümü değildir.')
    for section in sections:
        code, depth = section['code'], section['values'].get('depth') or 0
        if not printable(section, sections, writer):
            continue
        if unit:
            if code in UNIT_HIDDEN:
                pass
            elif code in UNIT_TITLES:
                writer.para(STYLE['heading'], UNIT_TITLES[code])
            else:
                writer.para(STYLE['heading'] if depth <= 1 and not code.startswith('III.') else STYLE['subheading'],
                            plain_title(section['title']))
        else:
            style = STYLE['chapter'] if depth == 0 else STYLE['heading'] if depth == 1 else STYLE['subheading']
            writer.para(style, plain_title(section['title']) if depth else tr_upper(plain_title(section['title'])))
        if section['values'].get('status') not in EMPTY_STATUSES:
            for block in section['blocks']:
                if block.get('type') == 'paragraph' and block.get('text', '').strip():
                    writer.para(STYLE['body'], block['text'])
                elif block.get('type') == 'bullets':
                    for item in block.get('items', []):
                        if item.strip():
                            writer.para(STYLE['body'], '• ' + item)
                elif block.get('type') == 'table':
                    writer.render_table(writer.tables[block['table_id']], plain_title(section['title']))
        for table_id in section['table_ids']:
            table = writer.tables[table_id]
            if table['kind'] != 'section':
                writer.render_table(table, table['title'])
    return '﻿'.encode('utf-16-le') + ''.join(writer.parts).encode('utf-16-le')


def filename(contract):
    document = contract['document']
    scope = 'idare' if document['scope'] == 'idare' else f"birim-{document.get('department_id')}"
    version = contract.get('release_version')
    return f"faaliyet-raporu-{document.get('year')}-{scope}-{version}-indesign.txt"
