"""Render slide dictionaries without querying or changing report data."""
import base64
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..numbers import format_number, parse_number
from .middleware import DECK_POLICY

APP = Path(__file__).resolve().parents[1]
MAX_BYTES = 3_000_000
SLIDE_TYPES = {'cover', 'map', 'separator', 'kpi', 'chart', 'table', 'bullets', 'quote', 'closing', 'scorecard', 'budget', 'photo', 'before_after', 'spot', 'feature'}


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


def numeric_columns(headers, rows):
    """Infer alignment from the whole table, so continuation pages agree."""
    result = []
    for column in range(len(headers)):
        known = False
        valid = True
        for row in rows:
            cell = row[column] if column < len(row) else None
            try:
                value = parse_number(cell)
            except ValueError:
                valid = False
                break
            if value is not None:
                known = True
        result.append(known and valid)
    return result


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
            alignment = numeric_columns(slide['headers'], slide['rows'])
        elif kind == 'scorecard':
            groups = pages(slide['rows'], 6)
        elif kind == 'bullets':
            groups = pages(slide['bullets'], 5)
        if kind == 'kpi' and not 2 <= len(slide['figures']) <= 8:
            raise ValueError('Özet rakam slaytında 2–8 rakam olmalı.')
        for index, group in enumerate(groups, 1):
            item = dict(slide)
            item.setdefault('note', slide.get('source', ''))
            if kind == 'table':
                item['rows'] = [[text(cell) for cell in row] for row in group]
                item['numeric_columns'] = alignment
                item['continuation'] = f'Tablo {index}/{len(groups)}' if len(groups) > 1 else ''
                # Last row finishes in <= 1.5 s, regardless of row count.
                step = min(150, 1150 // max(1, len(group) - 1))
                item['row_delays'] = [i * step for i in range(len(group))]
            elif kind == 'scorecard':
                item['rows'] = [dict(row, popup_id=f'popup-{len(result)}-{i}') for i, row in enumerate(group)]
                item['continuation'] = f'Tablo {index}/{len(groups)}' if len(groups) > 1 else ''
            elif kind == 'bullets':
                item['bullets'] = [text(value) for value in group]
                item['continuation'] = f'{index}/{len(groups)}' if len(groups) > 1 else ''
            elif kind == 'kpi':
                item['figures'] = [dict(figure,
                    decimals=2 if figure.get('money') else min(6, max(0, -Decimal(str(figure['value'])).as_tuple().exponent))
                    if figure['value'] is not None else 0,
                    display=format_number(figure['value'], money=figure.get('money', False)))
                    for figure in slide['figures']]
            elif kind == 'chart':
                item['series'] = [dict(series,
                    values=[float(value) if value is not None else None for value in series['values']],
                    display=[format_number(value, money=slide.get('money', False)) for value in series['values']])
                    for series in slide['series']]
                horizontal = slide['variant'] in {'horizontal', 'stacked'}
                item['height'] = max(240, min(640, 64 * len(slide['categories']))) if horizontal else 640
                if horizontal:
                    def rank(column):
                        known = [series['values'][column] for series in item['series']
                                 if series['values'][column] is not None]
                        return bool(known), sum(known)
                    # Multi-series horizontal bars follow their combined value;
                    # missing observations remain missing, including all-null rows.
                    order = sorted(range(len(slide['categories'])), key=rank, reverse=True)
                    item['categories'] = [slide['categories'][column] for column in order]
                    item['series'] = [dict(series,
                        values=[series['values'][column] for column in order],
                        display=[series['display'][column] for column in order]) for series in item['series']]
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


def render_deck(slides, *, title, code, max_bytes=MAX_BYTES):
    env = Environment(loader=FileSystemLoader(APP / 'templates' / 'sunum'),
                      autoescape=select_autoescape(['html']))
    content = env.get_template('deck.html').render(
        slides=prepare_slides(slides), title=title, code=code, csp=DECK_POLICY,
        has_photos=any(s['type'] in {'photo', 'before_after'} for s in slides),
        has_highlights=any(s['type'] in {'spot', 'feature'} for s in slides), **assets()).encode('utf-8')
    if len(content) > max_bytes:
        raise DeckTooLarge(f'Sunum dosyası {max_bytes // 1_000_000} MB sınırını aşıyor.')
    return content
