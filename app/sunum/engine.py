"""Render slide dictionaries without querying or changing report data."""
import base64
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..numbers import format_number

APP = Path(__file__).resolve().parents[1]
MAX_BYTES = 3_000_000
SLIDE_TYPES = {'cover', 'map', 'separator', 'kpi', 'chart', 'table', 'bullets', 'quote', 'closing'}


class DeckTooLarge(ValueError):
    pass


def verification_code(payload, canonical_json):
    """Hash the exact canonical export.json bytes, including historical releases."""
    if not payload.get('frozen'):
        return 'TASLAK'
    short = sha256(canonical_json.encode('utf-8')).hexdigest()[:8].upper()
    return f'{short[:4]}-{short[4:]}'


def pages(items, limit):
    return [items[start:start + limit] for start in range(0, len(items), limit)]


def text(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return '—'
    if isinstance(value, (int, float, Decimal)):
        return format_number(value)
    return str(value)


def prepare_slides(slides):
    """Pagination and display strings belong to Python, never Jinja macros."""
    result = []
    for slide in slides:
        kind = slide['type']
        if kind not in SLIDE_TYPES:
            raise ValueError(f'Bilinmeyen slayt türü: {kind}')
        groups = [None]
        if kind == 'table':
            groups = pages(slide['rows'], 10)
        elif kind == 'bullets':
            groups = pages(slide['bullets'], 5)
        if kind == 'kpi' and not 2 <= len(slide['figures']) <= 8:
            raise ValueError('Özet rakam slaytında 2–8 rakam olmalı.')
        for index, group in enumerate(groups, 1):
            item = dict(slide)
            item.setdefault('note', slide.get('source', ''))
            if kind == 'table':
                item['rows'] = [[text(cell) for cell in row] for row in group]
                item['continuation'] = f'Tablo {index}/{len(groups)}'
                # Last row finishes in <= 1.5 s, regardless of row count.
                step = min(150, 1150 // max(1, len(group) - 1))
                item['row_delays'] = [i * step for i in range(len(group))]
            elif kind == 'bullets':
                item['bullets'] = [text(value) for value in group]
                item['continuation'] = f'{index}/{len(groups)}' if len(groups) > 1 else ''
            elif kind == 'kpi':
                item['figures'] = [dict(figure, display=format_number(
                    figure['value'], money=figure.get('money', False))) for figure in slide['figures']]
            elif kind == 'chart':
                item['series'] = [dict(series,
                    values=[float(value) if value is not None else None for value in series['values']],
                    display=[format_number(value, money=slide.get('money', False)) for value in series['values']])
                    for series in slide['series']]
            item['slide_id'] = item.get('id') or f'slide-{len(result)}'
            result.append(item)
    return result


@lru_cache(maxsize=1)
def assets():
    def read(path):
        return (APP / path).read_text(encoding='utf-8')

    def data_uri(path, mime):
        return f'data:{mime};base64,' + base64.b64encode((APP / path).read_bytes()).decode('ascii')

    fonts = []
    for weight in (400, 500, 600):
        for subset in ('latin', 'latin-ext'):
            fonts.append({'weight': weight, 'subset': subset, 'src': data_uri(
                f'static/design/fonts/fira-sans-{subset}-{weight}-normal.woff2', 'font/woff2')})
    return {
        'reset_css': read('static/vendor/reveal.js/reset.css'),
        'reveal_css': read('static/vendor/reveal.js/reveal.css'),
        'reveal_js': read('static/vendor/reveal.js/reveal.js'),
        'echarts_js': read('static/vendor/echarts/echarts.min.js'),
        'tokens': read('static/design/tokens.css'),
        'fonts': fonts,
        'logo': data_uri('static/brand/logo-beyaz.svg', 'image/svg+xml'),
    }


def render_deck(slides, *, title, code):
    env = Environment(loader=FileSystemLoader(APP / 'templates' / 'sunum'),
                      autoescape=select_autoescape(['html']))
    content = env.get_template('deck.html').render(
        slides=prepare_slides(slides), title=title, code=code, **assets()).encode('utf-8')
    if len(content) > MAX_BYTES:
        raise DeckTooLarge('Sunum dosyası 3 MB sınırını aşıyor.')
    return content
