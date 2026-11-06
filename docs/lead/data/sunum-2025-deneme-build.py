"""2025 İdare meclis sunumu (hall test) — real Civensa engine, data from the printed 2025 FR (IDML).

Run: python3 build.py <repo> <photo_dir> <out.html>
"""
import io, json, sys, types, base64, logging
from decimal import Decimal
from pathlib import Path

REPO, PHOTOS, OUT = map(Path, sys.argv[1:4])
sys.path.insert(0, str(REPO))
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Light stubs: the deck path does not need the web/db stack.
fin = types.ModuleType('app.activity_financial_service')
fin.EXPENSE_CODES = {f'0{i}': '' for i in range(1, 10)}
sys.modules['app.activity_financial_service'] = fin
if 'starlette.datastructures' not in sys.modules:
    try:
        import starlette.datastructures  # noqa
    except ImportError:
        sd = types.ModuleType('starlette.datastructures'); sd.MutableHeaders = object
        sys.modules['starlette'] = types.ModuleType('starlette'); sys.modules['starlette.datastructures'] = sd

from app.sunum.recipes_idare import idare_activity_report
from app.sunum.meclis import budget_distribution
from app.sunum.engine import render_deck
from app.numbers import parse_number, format_number
from scripts.book_to_load_docx import extract_tables
from PIL import Image, ImageOps

IDML = REPO / 'docs/activity-report/source/2025-faaliyet-raporu.idml'
tables = extract_tables(IDML)


def table(page, head):
    found = [t for t in tables if t['page'] == page and t['rows'][0][0].startswith(head)]
    assert len(found) == 1, (page, head, len(found))
    return found[0]['rows']


def money(raw):
    raw = raw.strip()
    if raw in {'0', '0.00', '0,00'}:
        return Decimal(0)
    if ',' not in raw:          # "1.500.000.000" — thousands dots only
        return Decimal(raw.replace('.', ''))
    return Decimal(raw.replace('.', '').replace(',', '.'))


def title_tr(s):
    low = s.replace('I', 'ı').replace('İ', 'i').lower()
    words = []
    for w in low.split():
        if w in {'ve'}:
            words.append(w); continue
        first = w[0]
        first = {'i': 'İ', 'ı': 'I'}.get(first, first.upper())
        words.append(first + w[1:])
    return ' '.join(words)


# --- Budget by department (p.257) -------------------------------------------
dept_rows = table('257', 'MÜDÜRLÜK ADI')[1:]
total_row = dept_rows.pop()
assert total_row[0] == 'TOPLAM'
units, exp_rows = [], []
for i, (name, initial, final, actual) in enumerate(dept_rows, 1):
    dep = dict(department_id=i, department=title_tr(name))
    units.append(dep)
    exp_rows.append(dict(department_id=i, department=dep['department'],
                         final=money(final), actual=money(actual)))
s_final = sum(r['final'] for r in exp_rows); s_actual = sum(r['actual'] for r in exp_rows)
assert s_actual == money(total_row[3]), (s_actual, total_row[3])
print('Müdürlük harcama toplamı tutuyor:', format_number(s_actual, money=True), '| ödenek', format_number(s_final, money=True),
      'kitap', total_row[2])

# --- Budget by economic code (p.257) -----------------------------------------
eco = [t['rows'] for t in tables if t['page'] == '257' and t['rows'][0][1] == 'GİDERİN TÜRÜ'][0]
eco = [r for r in eco if r[1].startswith(('Personel', 'SGK', 'Mal', 'Faiz', 'Cari', 'Sermaye', 'Borç', 'Yedek'))
       or r[0] == 'TOPLAM']
eco_rows = [dict(department_id=None, economic_code=r[0], final=money(r[3]), actual=money(r[4])) for r in eco if r[0] != 'TOPLAM']
eco_total = [r for r in eco if r[0] == 'TOPLAM'][0]
assert sum(r['actual'] for r in eco_rows) == money(eco_total[4])
assert money(eco_total[4]) == s_actual

# --- Sections ---------------------------------------------------------------
duties = [  # 5393 s. Kanun md.14(a) hizmet alanları, kitap s.27 sırasıyla
    'İmar, su ve kanalizasyon, ulaşım gibi kentsel altyapı hizmetleri',
    'Coğrafi ve kent bilgi sistemleri, çevrenin korunması ve çevre sağlığı',
    'Temizlik ve katı atık, zabıta, acil yardım ve kurtarma hizmetleri',
    'Ağaçlandırma, park ve yeşil alanlar, konut hizmetleri',
    'Kültür ve sanat, gençlik ve spor, sosyal hizmet ve yardım',
]
goals = []
for t in tables:
    if t['page'] in {'24', '25', '26'} and t['rows'][0][1] == '→':
        for r in t['rows']:
            if r[0].startswith('S.A.'):
                goals.append((r[0], r[1]))
goals.sort()
strategy = [f'{code.replace("S.A.", "Amaç ")} · {text}' for code, text in goals]

sections = [
    dict(code='I.B', title='Yetki, Görev ve Sorumluluklar', blocks=[dict(type='bullets', items=duties)]),
    dict(code='II.B', title='Stratejik Amaç ve Hedefler', blocks=[dict(type='bullets', items=strategy)]),
    dict(code='III.A.1', title='Mali Değerlendirme', blocks=[]),
    dict(code='I.C.4', title='İnsan Kaynakları', blocks=[]),
]

# --- 2025 indicators: 2026 PP book (2025 Planlanan vs 2025 Yıl Sonu Gerçekleşme Tahmini)
from scripts.book_to_load_docx import table_type
PP26 = REPO / 'tests/fixtures/first_load/source/2026-performans-programi_ONAYLI.idml'
cards = [t for t in extract_tables(PP26) if table_type(t) == 'card']
def num(raw):
    raw = (raw or '').strip()
    if not raw or any(ch in raw for ch in '*-–→↓') and not raw.lstrip('-').replace('.', '').replace(',', '').isdigit():
        return None
    try:
        return Decimal(raw.replace('.', '').replace(',', '.'))
    except Exception:
        return None
ind_units, next_id = {}, 1000
skipped = 0
for c in cards:
    rows = c['rows']
    unit_name = next(r[1] for r in rows if r[0] == 'İdare Birim Adı').split('/')[-1].strip()
    unit_name = {'Park Bahçeler Müdürlüğü': 'Park ve Bahçeler Müdürlüğü',
                 'Strateji Müdürlüğü': 'Strateji Geliştirme Müdürlüğü', 'Etüt Proje Müdürlüğü': 'Etüd Proje Müdürlüğü'}.get(unit_name, unit_name)
    head = next(i for i, r in enumerate(rows) if r[0] == 'Performans Göstergesi')
    for r in rows[head + 1:]:
        if r[0].startswith('Göstergeye İlişkin'):
            break
        name, unit, planned, estimate = r[0], r[2], num(r[3]), num(r[4])
        if planned is None or estimate is None:
            skipped += 1
            continue
        if unit_name not in ind_units:
            dep_id = next((u['department_id'] for u in units if u['department'].lower() == unit_name.lower()), None)
            if dep_id is None:
                dep_id, next_id = next_id, next_id + 1
            ind_units[unit_name] = dict(department_id=dep_id, department=unit_name, core=dict(indicators=[]))
        ind_units[unit_name]['core']['indicators'].append(dict(name=name, unit=unit, actual=str(estimate), actual_state='verified',
            targets=[dict(value=str(planned), state='verified')], explanation='', deviation={}))
indicator_sources = sorted(ind_units.values(), key=lambda u: u['department'])
print('gösterge:', sum(len(u['core']['indicators']) for u in indicator_sources), 'müdürlük:', len(indicator_sources),
      'atlanan (sayı değil):', skipped)

payload = dict(id='2025-idare-deneme', year=2025, organization='Büyükçekmece Belediyesi', department='İdare',
    department_id=None, frozen=False, sections=sections, unit_manifest=[], missing_units=[],
    unit_indicator_sources=indicator_sources,
    resources=dict(employment=dict(rows=[])),
    financial=dict(tables=dict(expenditure=dict(rows=exp_rows, by_department=[],
        totals=dict(final=dict(value=str(s_final), missing=0), actual=dict(value=str(s_actual), missing=0))))))

# --- Photos (SN-video/foto), resized like the service: 1600 px WebP q82, no EXIF
def webp(path):
    img = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    img.thumbnail((1600, 1600))
    buf = io.BytesIO(); img.save(buf, 'WEBP', quality=82)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

P = {p.stem: p for p in PHOTOS.glob('*.jpg')}
by_name = {u['department']: u['department_id'] for u in units}
def dep(name):
    return by_name[name]

photo_slides = [
    dict(type='photo', image=webp(P['01-ilce-gol-park']), title='Göl kıyısında park ve yeşil alanlar',
         meta='Park ve Bahçeler Müdürlüğü', source='Fotoğraf: Park ve Bahçeler Müdürlüğü'),
    dict(type='photo', image=webp(P['05-meydan-cadde']), title='Meydan ve cadde düzenlemeleri',
         meta='Fen İşleri Müdürlüğü', source='Fotoğraf: Fen İşleri Müdürlüğü'),
    dict(type='photo', image=webp(P['11-festival-bayraklar']), title='26. Uluslararası Kültür ve Sanat Festivali',
         meta='Kültür, Sanat ve Sosyal İşler Müdürlüğü', source='Fotoğraf: Kültür, Sanat ve Sosyal İşler Müdürlüğü'),
    dict(type='photo', image=webp(P['10-marina-gunbatimi']), title='Kıyı ve marina',
         meta='Büyükçekmece', source='Fotoğraf: Basın ve Yayın Müdürlüğü'),
]

# --- Highlights: words only; numbers come from the fact catalogue -----------
H = []
def hl(kind, key, dep_id, sentence, label='', context='', image=None):
    H.append(dict(id=len(H) + 1, kind=kind, fact_key=key, department_id=dep_id, department=None,
                  label=label, sentence=sentence, context=context, sort_order=len(H) + 1, image=image))
    if dep_id:
        H[-1]['department'] = next(u['department'] for u in units if u['department_id'] == dep_id)

hl('spot', 'org:budget_actual', None, 'Kaynaklarımızı ilçemizin ihtiyaçlarına yönelttik.', context='Yıl sonu bütçe harcaması')
hl('spot', 'org:budget_rate', None, 'Bütçemizi yıl boyunca planlı ve dengeli kullandık.', label='%',
   context='Kesinleşen ödeneğe göre gerçekleşme')
t_id = dep('Temizlik İşleri Müdürlüğü')
hl('spot', f'unit:{t_id}:spending', t_id, 'Temiz bir Büyükçekmece için temizlik hizmetlerine büyük kaynak ayırdık.',
   context='Temizlik İşleri Müdürlüğü harcaması')
for name, photo, sentence in [
        ('Fen İşleri Müdürlüğü', '05-meydan-cadde', 'Yollar, meydanlar ve altyapı için yıl boyunca sahadaydık.'),
        ('Park ve Bahçeler Müdürlüğü', '14-park-gol-genis', 'Parklarımızı ve yeşil alanlarımızı büyüttük, yeniledik.'),
        ('Kültür, Sanat ve Sosyal İşler Müdürlüğü', '04-festival-taksim', 'Festivallerle ilçemizi kültür ve sanatla buluşturduk.')]:
    d = dep(name)
    hl('feature', f'unit:{d}:spending', d, sentence, context='Müdürlük harcaması', image=webp(P[photo]))

slides = idare_activity_report(payload, photos=photo_slides, highlights=H)

# --- Additions with the same engine slide types (data exists only as İdare totals)
def find(title):
    return next(i for i, s in enumerate(slides) if s.get('title') == title)

budget_section = slides[find('Bütçe bir bakışta')]['section']
eyebrow = slides[find('Bütçe bir bakışta')]['eyebrow']
dist = budget_distribution(dict(payload, financial=dict(tables=dict(expenditure=dict(rows=eco_rows, by_department=[],
    totals=dict(actual=dict(value=str(s_actual), missing=0))))), unit_manifest=[], missing_units=[]))
assert dist, 'ekonomik dağılım hesaplanamadı'
src = '2025 Faaliyet Raporu · Büyükçekmece Belediyesi · Mali Değerlendirme'
slides.insert(find('Bütçe bir bakışta') + 1, dict(type='budget', title='Her 100 TL nereye harcandı?', year=2025,
    source=src, section=budget_section, eyebrow=eyebrow, **dist))

staff = table('35', 'Büyükçekmece Belediye Başkanlığı (2025)')[2]
org_section = slides[find('Görev alanımız')]['section']
org_eyebrow = slides[find('Görev alanımız')]['eyebrow']
slides.insert(find('Görev alanımız') + 1, dict(type='kpi', title='Kurumumuzun ekibi', section=org_section, eyebrow=org_eyebrow,
    figures=[dict(label='Toplam personel', value=parse_number(staff[5]), unit='kişi'),
             dict(label='Memur', value=parse_number(staff[1]), unit='kişi'),
             dict(label='İşçi', value=parse_number(staff[2]), unit='kişi'),
             dict(label='B.İ.T. personeli', value=parse_number(staff[4]), unit='kişi')],
    source='2025 Faaliyet Raporu · Büyükçekmece Belediyesi · İnsan Kaynakları'))

ESTIMATE = (' 2025 gerçekleşmesi olarak 2026 Performans Programı\'ndaki "2025 Yıl Sonu Gerçekleşme Tahmini", '
    'hedef olarak "2025 Planlanan" kullanıldı. Düşük olanın iyi olduğu göstergeler henüz ayrılmadı.')
for s_ in slides:
    if s_['type'] == 'scorecard':
        s_['note'] = s_['note'] + ESTIMATE
        s_['source'] = '2026 Performans Programı · 2025 Planlanan ve 2025 Yıl Sonu Gerçekleşme Tahmini'
    if s_.get('title') == 'Müdürlüklere göre gösterge özeti':
        s_['headers'] = ['Müdürlük', 'Gösterge sayısı', 'Tahmini girilen', 'Ortalama oran (%)']
        s_['source'] = '2026 Performans Programı · 2025 Planlanan ve 2025 Yıl Sonu Gerçekleşme Tahmini'

# Workaround (engine bug, CIV-186): wrapped names push 10-row table pages past the footer.
i = next(i for i, x in enumerate(slides) if x.get('title') == 'Müdürlüklere göre gösterge özeti')
t = slides.pop(i)
for k in range(0, len(t['rows']), 7):
    slides.insert(i + k // 7, dict(t, rows=t['rows'][k:k + 7]))

content = render_deck(slides, title='Büyükçekmece Belediyesi · 2025 Faaliyet Raporu meclis sunumu (deneme)',
                      code='DENEME', max_bytes=8_000_000)
OUT.write_bytes(content)
print('slaytlar:', len(slides), '| boyut:', len(content), 'B')
for s in slides:
    print(' -', s['type'], '|', s.get('title') or s.get('label') or '')
