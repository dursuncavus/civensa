"""Generate the Civensa import Word file from the final book's IDML tables.

Usage: python gen.py tables.json name_map.json out.docx
- Uses only card tables (BÜTÇE YILI ...), department cost tables (Faaliyetler ...) and economic tables.
- Small per-card activity tables are skipped: by the owner's rule their values equal the department table.
- Department names are replaced with the system names from name_map.json.
"""
import json, re, sys
from docx import Document
from docx.shared import Pt

T = json.load(open(sys.argv[1])); NAME_MAP = json.load(open(sys.argv[2])); OUT = sys.argv[3]

def low(s): return (s or '').replace('İ', 'i').replace('I', 'ı').lower()
def norm(s): return re.sub(r'[^0-9a-zçğıöşü]+', '', low(s).replace('i̇', 'i'))
NMAP = {norm(k): v for k, v in NAME_MAP['map'].items()}

def typ(t):
    f = (t['rows'][0][0] or '') if t['rows'] else ''
    if f.startswith('BÜTÇE YILI'): return 'CARD'
    if f.startswith('Alt Program Kapsamında'): return 'SMALL'
    if f.startswith('Faaliyetler'): return 'BIG'
    if f.startswith('Ekonomik Ad'): return 'ECON'
    return 'OTHER'

def pnum(p):
    try: return int(p)
    except: return 10**6

tables = [t for t in T if t['page'] != '?' and typ(t) in ('CARD', 'BIG', 'ECON')]
tables.sort(key=lambda t: (pnum(t['page']), t['spread']))

doc = Document()
style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(9)
report = {'departments': [], 'unmapped': []}
current = None

def sysname(raw):
    raw = (raw or '').strip()
    base = raw.split('/')[-1].strip()
    v = NMAP.get(norm(base))
    if v is None:
        report['unmapped'].append(raw)
        return base
    return v

def write_table(rows, indicator_rows=()):
    ncols = max(len(r) for r in rows)
    tb = doc.add_table(rows=len(rows), cols=ncols)
    tb.style = 'Table Grid'
    for ri, row in enumerate(rows):
        c = 0
        while c < ncols:
            val = row[c] if c < len(row) else ''
            if val in ('→', '↓', None):
                val = ''
            # horizontal span: following '→' cells
            span = 1
            while c + span < ncols and (row[c + span] if c + span < len(row) else '') == '→':
                span += 1
            cell = tb.cell(ri, c)
            if span > 1 and ri not in indicator_rows:
                cell = cell.merge(tb.cell(ri, c + span - 1))
            cell.text = val
            c += span
    doc.add_paragraph('')

for t in tables:
    ty = typ(t); rows = [list(r) for r in t['rows']]
    if ty == 'CARD':
        for r in rows:
            lab = low((r[0] or '').strip())
            if lab.startswith('idare/birim') or lab.startswith('sorumlu idare'):
                r[1] = sysname(r[1])
        dept = next(r[1] for r in rows if low((r[0] or '')).startswith('idare/birim'))
        if dept != current:
            doc.add_heading(dept, level=2); current = dept
            report['departments'].append(dept)
        # indicator rows (header + data) are written without the name/unit merge so the
        # importer reads the unit from its own column
        hi = next(i for i, r in enumerate(rows) if (r[0] or '').startswith('Performans Göstergesi'))
        end = next((i for i, r in enumerate(rows) if low(r[0] or '').startswith('göstergeye ilişkin')), len(rows))
        write_table(rows, indicator_rows=set(range(hi, end)))
    else:
        write_table(rows)

doc.save(OUT)
json.dump(report, open(OUT + '.report.json', 'w'), ensure_ascii=False, indent=1)
print('departments', len(report['departments']), 'unmapped', sorted(set(report['unmapped'])))
