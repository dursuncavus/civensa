"""Data-derived PP content inventory, reusable by a later release checklist.

The inventory comes from the general/performance contents and table families in
tests/fixtures/pp2027_source_no_media.docx (tables 1–28, 159–161), the printed
book's membership tables (scripts/book_to_load_docx.py::table_type), and the
structured outputs in app/book_export.py::blocks. It is a presence inventory,
not a financial validation or a publication gate. No status is persisted.
"""
import json
import re
import unicodedata
from collections import defaultdict

from sqlalchemy import select

from .models import (Activity, ActivityResponsibility, ActivityCostValue,
    DepartmentCostValue, EconomicValue, Indicator, IndicatorValue, OfficialActivity,
    ReportCard, ReportSection, ReportingPeriod)
from .pp_errors import pp_error

SOURCE = '2027 PP kaynak kitabının içindekiler ve tablo türleri; basılı kitap faaliyet üyeliği; Civensa kitap çıktısı.'

# Stable keys identify content families, never stored completion statuses.
SECTION_TYPES = (
    ('ataturk', 'Atatürk Resmi', ('atatürk resmi',)),
    ('anthem', 'İstiklal Marşı', ('istiklal marşı',)),
    ('address', 'Gençliğe Hitabe', ('gençliğe hitabe',)),
    ('contents', 'İçindekiler', ('içindekiler',)),
    ('table_list', 'Tablolar', ('tablolar',)),
    ('chart_list', 'Grafikler', ('grafikler',)),
    ('foreword', 'Başkan Sunuşu', ('başkan sunuşu', 'üst yönetici sunuşu', 'sunuş')),
    ('council', 'Meclis Üyeleri', ('2024 2028 dönemi meclis üyelerimiz', 'meclis üyelerimiz')),
    ('executive', 'Encümen Üyeleri', ('encümen üyelerimiz',)),
    ('deputies', 'Başkan Yardımcıları', ('başkan yardımcılarımız',)),
    ('advisors', 'Başkan Danışmanları', ('başkan danışmaları', 'başkan danışmanları')),
    ('directors', 'Birim Müdürleri', ('birim müdürlerimiz',)),
    ('authority', 'Yetki, Görev ve Sorumluluklar', ('yetki görev ve sorumluluklar',)),
    ('organization', 'Teşkilat Yapısı', ('teşkilat yapısı', 'örgüt yapısı')),
    ('physical', 'Fiziksel Kaynaklar', ('fiziksel kaynaklar', 'fiziki kaynaklar')),
    ('human', 'İnsan Kaynakları', ('insan kaynakları',)),
    ('general_other', 'Genel Bilgiler — Diğer Hususlar', ('genel bilgiler diğer hususlar',)),
    ('policies', 'Temel Politika ve Öncelikler', ('temel politika ve öncelikler',)),
    ('objectives', 'Amaç ve Hedefler', ('amaç ve hedefler', 'amaçlar ve hedefler')),
    ('mission', 'Misyon', ('misyon', 'misyonumuz', 'misyon ve vizyon')),
    ('vision', 'Vizyon', ('vizyon', 'vizyonumuz')),
    ('performance_other', 'Performans Bilgileri — Diğer Hususlar', ('performans bilgileri diğer hususlar',)),
)

# General institutional tables are editable ReportSection(kind=table) records.
TABLE_TYPES = (
    ('legislation', 'Kanun ve Yönetmelikler', ('kanun ve yönetmelik adı',)),
    ('hardware', 'Donanım Tablosu', ('donanım tablosu',)),
    ('peripherals', 'Çevre Birimleri Donanımı', ('çevre birimleri donanımı',)),
    ('e_municipality', 'e-Belediye Hizmetleri', ('e belediye hizmetlerimiz', 'e belediye hizmetleri')),
    ('mobile', 'Kurumsal Mobil Uygulamalar', ('kurumsal mobil uygulamalarımız', 'kurumsal mobil uygulamalar')),
    ('web', 'Kurumsal Web Siteleri', ('kurumsal web sitelerimiz', 'kurumsal web siteleri')),
    ('ybs', 'Kent Bilgi Sistemi Hizmetleri', ('kent bilgi sistemi hizmetleri',)),
    ('cbs', 'Coğrafi Bilgi Sistemi Hizmetleri', ('coğrafi bilgi sistemi hizmetleri',)),
    ('e_government', 'e-Devlet Hizmetleri', ('e devlet hizmetlerimiz', 'e devlet hizmetleri')),
    ('buildings', 'Belediyece Kullanılan Binalar', ('belediyemizce kullanılan binalar', 'belediyece kullanılan binalar')),
    ('schools', 'Belediye Mülkiyetindeki Cami ve Okullar', ('belediyemiz mülkiyetindeki cami ve okullar', 'belediye mülkiyetindeki cami ve okullar')),
    ('mukhtar', 'Muhtarlık Binaları', ('muhtarlık binaları',)),
    ('rented', 'Kiralanan Yerler', ('belediyemizce kiralanan yerler', 'kiralanan yerler')),
    ('vehicles_new', 'Satın Alınacak Taşıtlar (T-1)', ('satın alınacak taşıtları gösterir', 'satın alınacak taşıtlar')),
    ('vehicles', 'Mevcut Taşıtlar (T-2)', ('mevcut taşıtları gösterir', 'mevcut taşıtlar')),
    ('staff', 'Yıllara Göre Kadro Dağılımı', ('belediyenin yıllara göre mavcut kadro dağılımı', 'yıllara göre kadro dağılımı')),
    ('gender', 'Cinsiyete Göre Personel Dağılımı', ('cinsiyete göre personel dağılımı',)),
    ('age', 'Personelin Yaş Durumu', ('yaş durumu', 'personelin yaş durumu')),
    ('education', 'Personelin Öğrenim Durumu', ('öğrenim durumu', 'personelin öğrenim durumu')),
    ('staff_class', 'Memur Kadrolarının Sınıf Dağılımı', ('memur kadrolarının sınıf dağılımı',)),
    ('population', 'Yıllara Göre Nüfus', ('büyükçekmece nüfusu', 'yıllara göre nüfus')),
    ('neighborhood', 'Mahallelere Göre Nüfus', ('mahalle adı toplam nüfus', 'mahallelere göre nüfus')),
    ('municipal_duties', 'Büyükşehir ve İlçe Belediyesi Görev Dağılımı', ('büyükşehir büyükşehir ilçe', 'büyükşehir ve ilçe belediyesi görev dağılımı')),
    ('policy_documents', 'Politika Belgeleri', ('politika belgesi adı', 'politika belgeleri')),
    ('strategic_objectives', 'Stratejik Amaçlar', ('stratejik amaçlar',)),
    ('strategic_links', 'Program / Alt Program Hedefleri ve Stratejik Plan İlişkisi', ('alt program adı alt program hedefleri', 'program alt program hedefleri ve stratejik plan ilişkisi')),
    ('resource_totals', 'İdarenin Toplam Kaynak İhtiyacı', ('idarenin toplam kaynak ihtiyacı', 'ekonomik sınıflandırma düzeyinde', 'hizmet programları toplam')),
    ('department_budget', 'Müdürlüklere Göre Bütçe Dağılımı', ('müdürlüklere göre bütçe dağılımı', 'müdürlük adı toplam', 'müdürlükler bazında dağılımları')),
    ('program_budget', 'Program, Alt Program ve Faaliyet Maliyetleri', ('program sınıflandırması', 'program alt program ve faaliyet maliyetleri')),
    ('economic_distribution', 'Bütçenin Ekonomik Sınıflandırmaya Göre Dağılımı', ('bütçenin ekonomik sınıflandırmaya göre',)),
)
STRUCTURED_TYPES = (
    ('cards', 'Performans Göstergeleri'),
    ('membership', 'Alt Program Kapsamında Yürütülecek Faaliyetler'),
    ('costs', 'Faaliyet Maliyetleri'),
    ('activity_explanations', 'Faaliyetlere İlişkin Açıklamalar'),
    ('personnel', 'Personel ve SGK Giderleri'),
    ('economics', 'Ekonomik Sınıflandırma'),
    ('catalogue', 'Faaliyetlerden Sorumlu Harcama Birimleri'),
)


def normalized_title(text):
    text = str(text or '').lower().replace('ı', 'i')
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9]+', ' ', text).strip()
    text = re.sub(r'^(?:tablo\s+\d+\s*|[ivx]+\s+|[a-e]\s+|\d{1,2}\s+)', '', text)
    return text.strip()


def section_type(title, context='general'):
    key = normalized_title(title)
    if key in {'genel bilgiler', 'performans bilgileri', 'performans bilgisi', 'idarenin toplam kaynak ihtiyaci'}:
        return {'genel bilgiler':'general', 'performans bilgileri':'performance',
                'performans bilgisi':'performance_content', 'idarenin toplam kaynak ihtiyaci':'resource_totals'}[key]
    if key == 'diger hususlar':
        return f'{context}_other'
    for code, label, aliases in SECTION_TYPES:
        if key in {normalized_title(label), *(normalized_title(a) for a in aliases)}:
            return code
    # The supplied book extends this heading with its staffing policy/year.
    if key.startswith('insan kaynaklari istihdam politikasi'):
        return 'human'
    if re.fullmatch(r'20\d{2} 20\d{2} donemi meclis uyelerimiz', key):
        return 'council'
    return None


def table_type(title):
    key = normalized_title(title)
    for code, label, aliases in TABLE_TYPES:
        if any(normalized_title(alias) in key for alias in (label, *aliases)):
            return code
    if all(part in key for part in ('program', 'alt program', 'faaliyet')) and 'sorumlu' in key:
        return 'catalogue'
    return None


def section_payload(section):
    try:
        result = json.loads(section.content_json)
        return result if isinstance(result, dict) else {}
    except (ValueError, TypeError):
        return {}


def section_identity(section):
    payload = section_payload(section)
    context = 'performance' if payload.get('placement') == 'after' else 'general'
    return (section.kind, section_type(section.title, context) or table_type(section.title) or normalized_title(section.title),
            payload.get('placement', 'before'))


def section_has_content(section):
    payload = section_payload(section)
    if section.kind == 'image':
        return bool(payload.get('data'))
    if section.kind == 'table':
        # Header-only tables have no substantive rows.
        return any(any(str(cell or '').strip() for cell in row)
                   for row in payload.get('rows', [])[payload.get('header_rows', 1):])
    return bool(str(payload.get('text', '')).strip())


def completion_manifest(db, period_id):
    """Return Turkish name/status/count/fix URL for every official content family.

    Tamam = substantive content; Boş = records without content; Eksik = no records.
    Zero is content. Counts are records (tables, sections, cards or values), never
    amounts. Financial completeness and approval remain separate checks.
    """
    period = db.get(ReportingPeriod, period_id)
    if period is None:
        raise pp_error(404)
    builder = f'/report-builder?period_id={period_id}'
    groups = defaultdict(list)
    sections = db.scalars(select(ReportSection).where(ReportSection.period_id == period_id)
                           .order_by(ReportSection.position, ReportSection.id)).all()
    extras = []
    for section in sections:
        payload = section_payload(section)
        context = 'performance' if payload.get('placement') == 'after' else 'general'
        code = section_type(section.title.removesuffix(' — Görsel'), context) if section.kind != 'table' else table_type(section.title)
        if section.kind == 'table' and not code:
            code = table_type(' '.join(str(c) for r in payload.get('rows', [])[:3] for c in r))
        if code:
            groups[code].append(section)
            if normalized_title(section.title) == 'misyon ve vizyon':
                groups['vision'].append(section)
        else:
            extras.append(section)
    rows = []

    def add(code, name, records, populated, href=builder, kind='Tablo'):
        rows.append(dict(key=code, name=name, status='Tamam' if populated else 'Boş' if records else 'Eksik',
                         count=len(records), href=href, kind=kind))

    for code, label, _ in (*SECTION_TYPES, *TABLE_TYPES):
        records = groups[code]
        add(code, label, records, any(section_has_content(s) for s in records),
            builder + (f'#section-{records[0].id}' if records else '#book-sections'),
            'Bölüm' if code in {s[0] for s in SECTION_TYPES} else 'Tablo')
    for section in extras:
        add(f'section-{section.id}', section.title, [section], section_has_content(section),
            f'{builder}#section-{section.id}', 'Tablo' if section.kind == 'table' else 'Bölüm')

    def period_rows(model):
        return db.scalars(select(model).where(model.period_id == period_id)).all()

    cards, indicators, activities = period_rows(ReportCard), period_rows(Indicator), period_rows(Activity)
    indicator_ids = [i.id for i in indicators]
    activity_ids = [a.id for a in activities]
    ivals = db.scalars(select(IndicatorValue).where(IndicatorValue.indicator_id.in_(indicator_ids))).all()
    costs = db.scalars(select(ActivityCostValue).where(ActivityCostValue.activity_id.in_(activity_ids))).all()
    personnel, economics, catalogue = period_rows(DepartmentCostValue), period_rows(EconomicValue), period_rows(OfficialActivity)
    personnel = [v for v in personnel if v.category == 'personnel_sgk']
    responsible_ids = set(db.scalars(select(ActivityResponsibility.official_activity_id).where(
        ActivityResponsibility.official_activity_id.in_([c.id for c in catalogue]))))
    populated_indicators = {i.id for i in indicators if i.card_id in {c.id for c in cards}}
    values = {
        'cards': (cards, any(v.value is not None and v.indicator_id in populated_indicators for v in ivals)),
        'membership': (activities, any(a.card_id and a.subprogram_id for a in activities)),
        'costs': (activities, any(v.amount is not None for v in costs)),
        'activity_explanations': (activities, any(a.explanation.strip() for a in activities)),
        'personnel': (personnel, any(v.amount is not None for v in personnel)),
        'economics': (economics, any(v.amount is not None for v in economics)),
        'catalogue': (catalogue or groups['catalogue'], any(c.id in responsible_ids and c.name.strip()
            for c in catalogue) or any(section_has_content(s) for s in groups['catalogue'])),
    }
    for code, name in STRUCTURED_TYPES:
        records, populated = values[code]
        href = f'/activity-mapping?period_id={period_id}' if code == 'membership' else builder + '#catalogue' if code == 'catalogue' else builder + '#department-scope'
        if records and code not in {'membership', 'catalogue'}:
            screen = 'program' if code in {'cards', 'economics'} else 'department'
            href = f'/{screen}/{records[0].department_id}?period_id={period_id}'
        # A table with rows but no linked values is present and empty, not missing.
        add(code, name, records, populated, href)
    # Aggregate tables can also be generated from structured data, as in book_export.
    future = [v for v in economics if period.year <= v.year <= period.year + 2 and
              v.value_kind == ('budget' if v.year == period.year else 'forecast')]
    budget = [v for v in future if v.year == period.year]
    derived = {'resource_totals': future, 'department_budget': budget,
               'program_budget': [v for v in costs if v.activity_id in {a.id for a in activities if a.subprogram_id}
                    and period.year <= v.year <= period.year + 2 and v.value_kind == ('budget' if v.year == period.year else 'forecast')],
               'economic_distribution': budget}
    for row in rows:
        records = derived.get(row['key'], [])
        if row['status'] != 'Tamam' and records:
            department_id = (next(a.department_id for a in activities if a.id == records[0].activity_id)
                             if row['key'] == 'program_budget' else records[0].department_id)
            row.update(status='Tamam' if any(v.amount is not None for v in records) else 'Boş',
                       count=len(records), href=f'/program/{department_id}?period_id={period_id}')
    # Official parent sections are derived from their children, never placeholders.
    for code, name, child_codes in (
        ('general', 'Genel Bilgiler', {'authority', 'organization', 'physical', 'human', 'general_other'}),
        ('performance', 'Performans Bilgileri', {'policies', 'objectives', 'mission', 'vision', 'cards', 'resource_totals', 'performance_other'}),
        ('performance_content', 'Performans Bilgisi', {'cards', 'membership', 'costs'}),
    ):
        children = [r for r in rows if r['key'] in child_codes]
        direct = groups[code]
        rows.append(dict(key=code, name=name, kind='Bölüm', count=len(direct) + sum(r['count'] for r in children),
                         status='Tamam' if any(r['status'] == 'Tamam' for r in children) or any(section_has_content(s) for s in direct) else
                                'Boş' if direct or any(r['count'] for r in children) else 'Eksik', href=builder))
    return {'period_id': period.id, 'year': period.year, 'source': SOURCE, 'rows': rows}
