"""Resolve selected editorial words against this deck's own approved facts."""
import logging
from .engine import pages
from .facts import facts

logger = logging.getLogger(__name__)


def resolve_highlights(payload, highlights):
    if not highlights:
        return [], []
    catalogue = {f['key']: f for f in facts(payload, payload.get('unit_indicator_sources', []))}
    spots, cards = [], []
    for row in sorted(highlights, key=lambda r: (r['sort_order'], r['id'])):
        fact = catalogue.get(row['fact_key'])
        if fact is None or fact['department_id'] != row['department_id']:
            logger.info('Meclis sunumu %s: Öne çıkan %s rakamı raporda artık yok; slayt/kart atlandı.', payload.get('id'), row['id'])
            continue
        item = dict(fact, label=row['label'] or fact['unit'], sentence=row['sentence'],
            context=row['context'], department=row.get('department'), image=row.get('image'))
        item['decimals'] = len(fact['display'].split(',')[1]) if ',' in fact['display'] else 0
        if row['kind'] == 'spot':
            spots.append(dict(item, type='spot', dark=len(spots) % 2 == 1))
        elif row['kind'] == 'feature':
            cards.append(item)
    for i, spot in enumerate(spots, 1):
        spot['eyebrow'] = f'Yılın öne çıkanları · {i} / {len(spots)}'
    features = [dict(type='feature', title='Yılın öne çıkan işleri', eyebrow='Müdürlüklerimizden',
        cards=batch, source='Müdürlük bölümleri') for batch in pages(cards, 3)]
    return spots, features
