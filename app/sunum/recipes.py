"""FR müdürlük sunumu v1: only facts present in the exported report."""
from decimal import Decimal, InvalidOperation
import logging

from ..numbers import format_number, parse_number
from .engine import pages, text

logger = logging.getLogger(__name__)


def number(value):
    if value is None or isinstance(value, bool) or value == '':
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def complete_sum(values):
    values = [number(value) for value in values]
    return sum(values, Decimal(0)) if values and all(v is not None for v in values) else None


def lines(section):
    result = []
    for block in section.get('blocks', []):
        if block['type'] == 'bullets':
            result.extend(block['items'])
        elif block['type'] == 'paragraph':
            result.extend(line.strip() for line in block['text'].splitlines() if line.strip())
    return result


def rate(actual, target):
    return (actual / target * 100).quantize(Decimal('.01')) if actual is not None and target is not None and target > 0 else None


def activity_report(payload):
    """Return slide dictionaries; skipped sources are recorded only in the log."""
    report = f"{payload['year']} Faaliyet Raporu · {payload['department']}"
    sections = {section['code']: section for section in payload.get('sections', [])}
    groups = []

    def missing(label):
        # No record text or financial values in logs.
        logger.info('Faaliyet raporu %s: Bu raporda %s bilgisi yok; ilgili slayt atlandı.', payload.get('id'), label)

    def source(code):
        return f"{report} · {sections.get(code, {}).get('title', code)}"

    def add_group(title, subtitle, content):
        if content:
            groups.append({'title': title, 'subtitle': subtitle, 'content': content})

    content = []
    duties = lines(sections.get('I.B', {}))[:5]
    if duties:
        content.append(dict(type='bullets', title='Görev alanımız', bullets=duties, source=source('I.B')))
    else:
        missing('yetki, görev ve sorumluluk')
    staff = payload.get('resources', {}).get('employment', {}).get('rows', [])
    known = [row for row in staff if number(row.get('count')) is not None]
    if known:
        figures = []
        total = complete_sum(row.get('count') for row in staff)
        if total is not None:
            figures.append(dict(label='Toplam personel', value=total, unit='kişi'))
        elif staff:
            missing('eksiksiz toplam personel')
        figures.extend(dict(label=text(row.get('category')), value=number(row['count']), unit='kişi') for row in known[:7])
        if len(figures) >= 2:
            content.append(dict(type='kpi', title='Ekibimiz', figures=figures, source=source('I.C.4')))
        else:
            missing('en az iki personel rakamı')
        for batch in pages(known, 10):
            content.append(dict(type='chart', title='İstihdam türüne göre personel', variant='horizontal', unit='kişi',
                categories=[text(row.get('category')) for row in batch],
                series=[dict(name='Kişi sayısı', values=[float(number(row['count'])) for row in batch])], source=source('I.C.4')))
    else:
        missing('personel')
    buildings = payload.get('resources', {}).get('buildings', {}).get('rows', [])
    if buildings:
        content.append(dict(type='table', title='Binalar ve hizmet birimleri',
            headers=['Adı', 'Türü', 'Adres / mahalle', 'Alan (m²)', 'Mülkiyet'],
            rows=[[text(row.get('name')), text(row.get('category')), text(row.get('address')),
                   format_number(row.get('area')), text(row.get('ownership'))] for row in buildings], source=source('I.C.1')))
    else:
        missing('bina ve hizmet birimi')
    strategy = lines(sections.get('II.B', {}))
    if strategy:
        for batch in pages(strategy, 2):
            content.append(dict(type='quote', title='Stratejik planda yerimiz', quotes=batch, source=source('II.B')))
    else:
        missing('stratejik amaç ve hedef')
    add_group('Müdürlüğümüz', 'Görev, ekip, hedef', content)

    content = []
    budget = payload.get('financial', {}).get('tables', {}).get('expenditure', {})
    rows = budget.get('rows', [])
    # Economic and programme classifications describe the same money; use economic
    # rows only. Any blank observation prevents a misleading partial total.
    final = complete_sum(row.get('final') for row in rows)
    actual = complete_sum(row.get('actual') for row in rows)
    totals = budget.get('totals', {})
    if any(totals.get(key, {}).get('missing', 0) for key in ('final', 'actual')):
        final = actual = None
    if final is not None and actual is not None:
        scale = Decimal(1_000_000) if max(abs(final), abs(actual)) >= 1_000_000 else Decimal(1)
        unit = 'milyon TL' if scale > 1 else 'TL'
        content.append(dict(type='kpi', title='Bütçe bir bakışta', source=source('III.A.1'), figures=[
            dict(label='Bütçe gerçekleşme oranı', value=rate(actual, final), unit='yüzde'),
            dict(label='Kesinleşen ödenek', value=final / scale, unit=unit, money=True),
            dict(label='Yıl sonu harcama', value=actual / scale, unit=unit, money=True)]))
        labels, values = [], []
        initial = complete_sum(row.get('initial') for row in rows)
        if initial is not None and not totals.get('initial', {}).get('missing', 0):
            labels.append('Başlangıç ödeneği')
            values.append(float(initial / scale))
        labels.extend(['Kesinleşen ödenek', 'Yıl sonu harcama'])
        values.extend([float(final / scale), float(actual / scale)])
        content.append(dict(type='chart', title='Ödenekten harcamaya', variant='bar', money=True, unit=unit,
            categories=labels, series=[dict(name=unit, values=values)], source=source('III.A.1')))
    else:
        missing('eksiksiz bütçe')
    add_group('Bütçe', 'Ödenek, harcama', content)

    content = []
    # Existing FR activity facts are authored as EK-1 tables, not a separate model
    # in this payload. Preserve every column; do not infer cost/status from prose.
    for block in sections.get('III.B.1', {}).get('blocks', []):
        if block['type'] == 'table' and len(block['rows']) > 1:
            table = block['rows']
            headers = table[0]
            numeric_columns = [i for i, header in enumerate(headers) if any(word in header.casefold()
                for word in ('maliyet', 'tutar', 'harcama', 'cost'))]
            body = []
            for row in table[1:]:
                cells = [text(value) for value in row]
                for i in numeric_columns:
                    try:
                        cells[i] = format_number(parse_number(row[i], money=True), money=True)
                    except ValueError:
                        pass  # Unverified source text is never silently reinterpreted.
                body.append(cells)
            content.append(dict(type='table', title='Faaliyetlerimiz', headers=headers, rows=body, source=source('III.B.1')))
    if not content:
        missing('faaliyet tablosu')
    indicators = payload.get('core', {}).get('indicators', [])
    if indicators:
        body = []
        for indicator in indicators:
            targets = indicator.get('targets', [])
            verified = [number(target.get('value')) if target.get('state') == 'verified' else None for target in targets]
            target = verified[0] if len(verified) == 1 else None
            actual = number(indicator.get('actual')) if indicator.get('actual_state') == 'verified' else None
            target_text = '; '.join(format_number(value) for value in verified) or '—'
            body.append([text(indicator.get('name')), target_text, format_number(actual), format_number(rate(actual, target))])
        content.append(dict(type='table', title='Gösterge gerçekleşmeleri',
            headers=['Gösterge', 'Hedef', 'Gerçekleşen', 'Oran (%)'], rows=body, source=source('III.B.2.i')))
    else:
        missing('gösterge')
    add_group('Faaliyetler ve göstergeler', 'Çalışmalar, sonuçlar', content)

    slides = [dict(type='cover', department=payload['department'], year=payload['year'],
        organization=payload.get('organization', ''), subtitle='Başkanlık sunumu', source=report)]
    tiles = [dict(id=f'bolum-{i}', tile_id=f't{i}', number=str(i), title=group['title'], subtitle=group['subtitle'])
             for i, group in enumerate(groups, 1)]
    if tiles:
        slides.append(dict(type='map', id='harita', title=f"{payload['year']} yılına bakış", tiles=tiles, source=report))
    for group, tile in zip(groups, tiles):
        slides.append(dict(type='separator', **tile, section=tile['tile_id'], source=report))
        for slide in group['content']:
            slides.append(dict(slide, section=tile['tile_id'], eyebrow=f"{tile['number']} · {tile['title']}"))
    slides.append(dict(type='closing', title='Teşekkür ederiz', subtitle=report, source=report))
    return slides
