"""Council presentation from İdare facts and its pinned approved unit sources."""
from decimal import Decimal
import logging

from ..numbers import format_number
from .engine import pages, text
from .recipes import complete_sum, lines, number, rate
from .meclis import budget_distribution, one_decimal, scorecard

logger = logging.getLogger(__name__)


def idare_activity_report(payload):
    """Return the council recipe without changing report facts or the engine.

    The route supplies ``unit_indicator_sources`` from the exact approval IDs in
    unit_manifest: the export's flattened core.indicators has no unit identity.
    Older releases without those pinned sources must omit the summary.
    """
    report = f"{payload['year']} Faaliyet Raporu · {payload.get('organization', 'İdare')}"
    sections = {section['code']: section for section in payload.get('sections', [])}
    groups = []

    def missing(label):
        logger.info('Faaliyet raporu %s: Bu raporda %s bilgisi yok; ilgili slayt atlandı.', payload.get('id'), label)

    def source(code):
        return f"{report} · {sections.get(code, {}).get('title', code)}"

    def add_group(title, subtitle, content):
        if content:
            groups.append(dict(title=title, subtitle=subtitle, content=content))

    content = []
    duties = lines(sections.get('I.B', {}))[:5]
    if duties:
        content.append(dict(type='bullets', title='Görev alanımız', bullets=duties, source=source('I.B')))
    else:
        missing('yetki, görev ve sorumluluk')
    strategy = lines(sections.get('II.B', {}))
    if strategy:
        for batch in pages(strategy, 2):
            content.append(dict(type='quote', title='Stratejik amaç ve hedeflerimiz', quotes=batch, source=source('II.B')))
    else:
        missing('stratejik amaç ve hedef')

    units = {unit['department_id']: unit for unit in payload.get('unit_manifest', [])}
    staff = payload.get('resources', {}).get('employment', {}).get('rows', [])
    staff_groups = {dep: [] for dep in units}
    staff_names = {dep: unit.get('department') for dep, unit in units.items()}
    for row in staff:
        dep = row.get('department_id')
        if dep is not None:
            staff_groups.setdefault(dep, []).append(row.get('count'))
            staff_names.setdefault(dep, row.get('department'))
    staff_values = [(staff_names[dep], complete_sum(values)) for dep, values in staff_groups.items()]
    total = complete_sum(value for _, value in staff_values)
    # Unattributed rows or unapproved units make an institution total incomplete.
    if any(row.get('department_id') is None for row in staff) or payload.get('missing_units'):
        total = None
    if total is not None:
        content.append(dict(type='kpi', title='Kurumumuzun ekibi', figures=[
            dict(label='Toplam personel', value=total, unit='kişi'),
            dict(label='Personel verisi bulunan müdürlük', value=len(staff_values), unit='müdürlük')], source=source('I.C.4')))
    else:
        missing('eksiksiz toplam personel')
    if any(value is not None for _, value in staff_values):
        staff_values.sort(key=lambda item: (item[1] is not None, item[1] or Decimal(0)), reverse=True)
        for batch in pages(staff_values, 10):
            content.append(dict(type='chart', title='Müdürlüklere göre personel', variant='horizontal', unit='kişi',
                categories=[text(name) for name, _ in batch],
                series=[dict(name='Kişi sayısı', values=[value for _, value in batch])], source=source('I.C.4')))
    else:
        missing('müdürlüklere göre personel')
    add_group('Kurumumuz', 'Görev, ekip, hedef', content)

    content = []
    budget = payload.get('financial', {}).get('tables', {}).get('expenditure', {})
    rows, totals = budget.get('rows', []), budget.get('totals', {})
    final = complete_sum(row.get('final') for row in rows)
    actual = complete_sum(row.get('actual') for row in rows)
    if any(totals.get(key, {}).get('missing', 0) for key in ('final', 'actual')):
        final = actual = None
    if final is not None and actual is not None:
        scale = Decimal(1_000_000) if max(abs(final), abs(actual)) >= 1_000_000 else Decimal(1)
        unit = 'milyon TL' if scale > 1 else 'TL'
        content.append(dict(type='kpi', title='Bütçe bir bakışta', figures=[
            dict(label='Kesinleşen ödenek', value=final / scale, unit=unit, money=True),
            dict(label='Yıl sonu harcama', value=actual / scale, unit=unit, money=True),
            dict(label='Bütçe gerçekleşme oranı', value=rate(actual, final), unit='yüzde')], source=source('III.A.1')))
    else:
        missing('eksiksiz bütçe')
    distribution = budget_distribution(payload)
    if distribution:
        content.append(dict(type='budget', title='Her 100 TL nereye harcandı?', year=payload['year'],
            **distribution, source=source('III.A.1')))
    else:
        missing('ekonomik sınıflandırmaya göre eksiksiz harcama dağılımı')
    # Use economic rows only; programme rows classify the same expenditure.
    spending = {}
    names = {dep: unit.get('department') for dep, unit in units.items()}
    for row in rows:
        dep = row.get('department_id')
        if dep is not None:
            spending.setdefault(dep, []).append(row.get('actual'))
            names.setdefault(dep, row.get('department'))
    expected = set(units) | {unit['department_id'] for unit in payload.get('missing_units', [])}
    expected.update(unit['department_id'] for unit in budget.get('by_department', []))
    spending_values = [(dep, complete_sum(values)) for dep, values in spending.items()]
    if (spending_values and expected <= spending.keys()
            and all(value is not None for _, value in spending_values)
            and all(row.get('department_id') is not None for row in rows)
            and not totals.get('actual', {}).get('missing', 0)):
        spending_values.sort(key=lambda item: item[1], reverse=True)
        for batch in pages(spending_values, 10):
            content.append(dict(type='chart', title='Müdürlüklere göre harcama', variant='horizontal', unit='TL', money=True,
                categories=[text(names[dep]) for dep, _ in batch],
                series=[dict(name='Harcama', values=[value for _, value in batch])], source=source('III.A.1')))
    else:
        missing('müdürlüklere göre eksiksiz harcama')
    add_group('Bütçe', 'Ödenek, harcama', content)

    content = []
    scores = scorecard(payload.get('unit_indicator_sources', []))
    if scores and any(unit.get('core', {}).get('indicators') for unit in payload.get('unit_indicator_sources', [])):
        content.append(dict(type='scorecard', title='Müdürlükler hedeflerine ne kadar yaklaştı?', rows=scores,
            summary=[dict(css=css, count=sum(row['status'] == label for row in scores), label=description)
                     for label, css, description in [('Hedefte', 'ok', 'müdürlük hedefte'),
                         ('Yakın', 'w', 'müdürlük hedefe yakın'), ('Geride', 'bad', 'müdürlük geride')]],
            source=source('III.B.2.i'), note='Müdürlüklere göre karne. Gerçekleşen ≥ hedef, hedefte sayılır. '
                'Eşikler: %90 Hedefte, %70 Yakın; Strateji tarafından kesinleştirilecek.'))
        for item in content[-1]['summary']:
            item['display'] = format_number(item['count'])
    summary = []
    for unit in payload.get('unit_indicator_sources', []):
        indicators = unit.get('core', {}).get('indicators', [])
        verified, ratios = [], []
        for indicator in indicators:
            actual = number(indicator.get('actual')) if indicator.get('actual_state') == 'verified' else None
            if actual is None:
                continue
            verified.append(actual)
            targets = indicator.get('targets', [])
            target = number(targets[0].get('value')) if len(targets) == 1 and targets[0].get('state') == 'verified' else None
            if target is not None and target > 0:
                ratios.append(actual / target)
        summary.append([text(unit.get('department')), format_number(len(indicators) if indicators else None),
            format_number(len(verified) if verified else None),
            one_decimal(rate(sum(ratios), Decimal(len(ratios))) if ratios else None)])
    if summary and any(unit.get('core', {}).get('indicators') for unit in payload.get('unit_indicator_sources', [])):
        content.append(dict(type='table', title='Müdürlüklere göre gösterge özeti',
            headers=['Müdürlük', 'Gösterge sayısı', 'Gerçekleşmesi girilen', 'Ortalama oran (%)'],
            rows=summary, source=source('III.B.2.i')))
    else:
        missing('müdürlüklere göre doğrulanmış gösterge')
    add_group('Göstergeler', 'Müdürlüklerin sonuçları', content)

    slides = [dict(type='cover', department=payload.get('organization') or 'İdare', year=payload['year'],
        organization=payload.get('organization', ''), subtitle='Meclis sunumu', source=report)]
    tiles = [dict(id=f'bolum-{i}', tile_id=f't{i}', number=str(i), title=group['title'], subtitle=group['subtitle'])
             for i, group in enumerate(groups, 1)]
    if tiles:
        slides.append(dict(type='map', id='harita', title=f"{payload['year']} yılına bakış", tiles=tiles, source=report))
    for group, tile in zip(groups, tiles):
        slides.append(dict(type='separator', **tile, section=tile['tile_id'], source=report))
        for slide in group['content']:
            slides.append(dict(slide, section=tile['tile_id'], eyebrow=f"{tile['number']} · {tile['title']}"))
    if payload.get('missing_units'):
        slides.append(dict(type='bullets', title='Henüz onaylanmamış birimler',
            bullets=[text(unit.get('department')) for unit in payload['missing_units']], source=report))
    slides.append(dict(type='closing', title='Teşekkür ederiz', subtitle=report, source=report))
    return slides
