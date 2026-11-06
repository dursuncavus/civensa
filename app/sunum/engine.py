"""Render slide dictionaries without querying or changing report data."""
import base64
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from math import ceil
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


# deck.html: 1920px slide, 120px side padding, fixed/equal table columns.
# Fira Sans at 28px (table/name), 20px (score subline), 40px (bullets).
# Reserve .58em per character (wide glyphs a full em), and wrap whole words:
# ceil(total characters / capacity) alone misses the unused ends of lines.
# A wrapped line adds only its line height, not a whole row (padding, borders,
# gaps stay once per row), so extra lines cost a fraction of a row unit
# (measured at 1920×1080: table 35/64 px, bullet 54/90; scorecards by height).
CHAR_EM = .58
EXTRA_LINE = {'table': .6, 'bullets': .6}
CONTENT_WIDTH = 1920 - 2 * 120
SCORE_NAME_WIDTH = CONTENT_WIDTH - 2 * 32 - 2 - 450 - 130 - 170 - 3 * 28
BULLET_WIDTH = 1500 - 56


def estimated_lines(value, width, font_size):
    capacity = max(1, int(width / (font_size * CHAR_EM)))
    lines, used = 1, 0
    for word in text(value).split():
        size = sum(1.0 / CHAR_EM if ch in 'WMwm@%&' else 1 for ch in word)
        if used and used + 1 + size <= capacity:
            used += 1 + size
        else:
            if used:
                lines += 1
            chunks = max(1, ceil(size / capacity))
            lines += chunks - 1
            used = size - (chunks - 1) * capacity
    return lines


def line_pages(items, maximum, estimate, budget=None):
    """Keep old row limits and spend at most `budget` single-row units per page.

    The budget defaults to the old row limit; bullets have more room under
    five single-line items (5 × 90 px of ~680 px), so they get a larger one.

    An oversized item is emitted intact, alone; pagination never truncates data.
    """
    budget = maximum if budget is None else budget
    result, group, used = [], [], 0
    for item in items:
        cost = estimate(item)
        if group and (len(group) == maximum or used + cost > budget):
            result.append(group)
            group, used = [], 0
        group.append(item)
        used += cost
    if group:
        result.append(group)
    return result


# meclis.css: rows are full size up to five; a sixth row switches the whole
# list to the compact layout (.score:has(.r:nth-child(6))). Heights in px,
# measured at 1920×1080: full row 104 (+36.4 per extra name line), compact
# row 81 (+31.2), subline 24 per extra line, gap 14. Five full single-line
# rows (576 px) are the most that clear the footer with summary and the
# "Tablo n/N" counter; a slide that needs no second page has no counter and
# may use that line too (e.g. six compact rows with two wrapped names, 619 px).
SCORE_HEIGHT = 590
SCORE_HEIGHT_ALONE = 625
SCORE_ROW = {False: (104, 36.4), True: (81, 31.2)}


def scorecard_lines(row):
    name = estimated_lines(row['name'], SCORE_NAME_WIDTH, 28)
    subline = f"{row.get('measured_display', '')} göstergenin {row.get('met_display', '')}'i hedefte"
    return name, estimated_lines(subline, SCORE_NAME_WIDTH, 20)


def scorecard_fits(rows, limit=SCORE_HEIGHT):
    compact = len(rows) >= 6
    base, extra = SCORE_ROW[compact]
    height = 14 * (len(rows) - 1)
    for row in rows:
        name, subline = scorecard_lines(row)
        height += base + extra * (name - 1) + 24 * (subline - 1)
    return height <= limit


def fit_pages(items, maximum, fits):
    """Largest group from the front that fits; its height depends on its size."""
    result, start = [], 0
    while start < len(items):
        size = next((k for k in range(min(maximum, len(items) - start), 0, -1)
                     if fits(items[start:start + k])), 1)
        result.append(items[start:start + size])
        start += size
    return result


def row_units(kind, lines):
    return 1 + EXTRA_LINE[kind] * (lines - 1)


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
            width = CONTENT_WIDTH / max(1, len(slide['headers'])) - 40
            groups = line_pages(slide['rows'], 10, lambda row: row_units('table', max(
                (estimated_lines(cell, width, 28) for cell in row), default=1)))
            alignment = numeric_columns(slide['headers'], slide['rows'])
        elif kind == 'scorecard':
            rows = slide['rows']
            alone = len(rows) <= 6 and scorecard_fits(rows, SCORE_HEIGHT_ALONE)
            groups = [rows] if alone and rows else fit_pages(rows, 6, scorecard_fits)
        elif kind == 'bullets':
            groups = line_pages(slide['bullets'], 5,
                                lambda value: row_units('bullets', estimated_lines(value, BULLET_WIDTH, 40)),
                                budget=7)
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
            elif kind == 'feature':
                item['compact'] = any(len(card['sentence']) > 140 or len(card['label']) > 24
                    or len(card.get('context') or '') > 55 for card in slide['cards'])
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
