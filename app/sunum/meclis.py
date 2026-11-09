"""Council-only scorecard and economic distribution from immutable report facts."""
from decimal import Decimal, ROUND_FLOOR

from ..activity_financial_service import EXPENSE_CODES
from ..numbers import format_number
from .engine import text
from .recipes import complete_sum, number, indicator_comparison, indicator_name

# Pending confirmation by Strateji; compare unrounded rates at the boundaries.
STATUS_THRESHOLDS = ((Decimal(90), 'Hedefte', 'ok'), (Decimal(70), 'Yakın', 'w'),
                     (Decimal(0), 'Geride', 'bad'))
BUDGET_COLORS = ('#1e6b65', '#4f8f88', '#86b3ad', '#b7d3cf', '#c9ded9', '#dfe9e7')
# Council wording from the approved design; codes retain the report's meaning.
BUDGET_NAMES = {'01': 'Personel giderleri', '02': 'Sosyal güvenlik primleri',
    '03': 'Mal ve hizmet alımı', '04': 'Faiz', '05': 'Cari transferler',
    '06': 'Sermaye giderleri', '07': 'Sermaye transferi', '08': 'Borç verme', '09': 'Yedek ödenekler'}
BUDGET_DESTINATIONS = {'01': 'Personel giderlerine', '02': 'Sosyal güvenlik primlerine',
    '03': 'Mal ve hizmet alımına', '04': 'Faize', '05': 'Cari transferlere',
    '06': 'Yatırımlara (sermaye giderleri)', '07': 'Sermaye transferine',
    '08': 'Borç vermeye', '09': 'Yedek ödeneklere'}


def one_decimal(value):
    """Keep Turkish grouping and exactly one decimal through the number formatter."""
    return format_number(value.quantize(Decimal('.1')), money=True)[:-1] if value is not None else '—'


def status(value):
    if value is not None:
        for threshold, label, css in STATUS_THRESHOLDS:
            if value >= threshold:
                return label, css
    return '', ''


def scorecard(sources):
    """Compare directions in approved core facts, grouped by unit.

    ReportCard.strategic_link is free text, absent from the approved core. Never
    join current cards to historical approvals or guess goals from their names.
    Older frozen facts without direction retain the higher-is-better rule.
    """
    rows = []
    for unit in sources:
        measured, met, missed = 0, 0, []
        for indicator in unit.get('core', {}).get('indicators', []):
            targets = indicator.get('targets', [])
            target = number(targets[0].get('value')) if len(targets) == 1 and targets[0].get('state') == 'verified' else None
            actual = number(indicator.get('actual')) if indicator.get('actual_state') == 'verified' else None
            if target is None or actual is None:
                continue
            measured += 1
            is_met, ratio = indicator_comparison(actual, target, indicator.get('direction', 'higher'))
            if is_met:
                met += 1
            else:
                explanation = indicator.get('explanation', '')
                correction = indicator.get('deviation', {}).get('corrective_action', '')
                reason = '\n'.join(value.strip() for value in (explanation, correction)
                                   if isinstance(value, str) and value.strip())
                missed.append(dict(name=indicator_name(indicator), department=text(unit.get('department')),
                    target=format_number(target), actual=format_number(actual),
                    ratio='%' + one_decimal(ratio.quantize(Decimal('.01'))) if ratio is not None else '—',
                    css=status(ratio.quantize(Decimal('.01')) if ratio is not None else None)[1], reason=text(reason)))
        value = Decimal(met) / measured * 100 if measured else None
        label, css = status(value)
        rows.append(dict(code=text(unit.get('department_id')), name=text(unit.get('department')),
            measured=measured, met=met, measured_display=format_number(measured), met_display=format_number(met),
            missed_display=format_number(len(missed)), rate=value, percentage='%' + one_decimal(value) if value is not None else '—',
            width=float(value) if value is not None else 0, status=label, css=css, missed=missed,
            expandable=label in {'Yakın', 'Geride'}))
    return rows


def budget_distribution(payload):
    """Return complete expenditure only; shares use largest-remainder tenths.

    Group economic subcodes at level one, then merge shares below 5%. Rounding
    allocates the remaining 0.1 TL units by descending fractional remainder,
    with category order breaking ties, so displayed boxes sum to 100.0 TL.
    """
    budget = payload.get('financial', {}).get('tables', {}).get('expenditure', {})
    rows = budget.get('rows', [])
    total = complete_sum(row.get('actual') for row in rows)
    declared = budget.get('totals', {}).get('actual', {})
    expected = {unit['department_id'] for unit in payload.get('unit_manifest', []) + payload.get('missing_units', [])}
    expected.update(unit['department_id'] for unit in budget.get('by_department', []))
    present = {row.get('department_id') for row in rows}
    if (total is None or total <= 0 or declared.get('missing', 0) or not expected <= present
            or number(declared.get('value')) != total):
        return None
    categories = {}
    for row in rows:
        code = str(row.get('economic_code', '')).split('.')[0]
        actual = number(row.get('actual'))
        if code not in EXPENSE_CODES or actual < 0:
            return None
        categories[code] = categories.get(code, Decimal(0)) + actual
    ordered = sorted(categories.items(), key=lambda item: (-item[1], item[0]))
    named = [(BUDGET_NAMES[code], value) for code, value in ordered if value * 100 >= total * 5]
    other = [(BUDGET_NAMES[code].lower(), value) for code, value in ordered if value * 100 < total * 5]
    if other:
        named.append(('Diğer (' + ', '.join(name for name, _ in other) + ')', sum(value for _, value in other)))
    exact = [value / total * 1000 for _, value in named]
    tenths = [int(value.to_integral_value(rounding=ROUND_FLOOR)) for value in exact]
    for index in sorted(range(len(exact)), key=lambda i: exact[i] - tenths[i], reverse=True)[:1000 - sum(tenths)]:
        tenths[index] += 1
    boxes = [dict(name=name, value=float(value), share=tenths[i] / 10,
                  display=one_decimal(Decimal(tenths[i]) / 10), color=BUDGET_COLORS[min(i, len(BUDGET_COLORS)-1)])
             for i, (name, value) in enumerate(named)]
    # Side labels are the three largest original economic categories.
    displays = {box['name']: box['display'] for box in boxes}
    top = [dict(name=BUDGET_DESTINATIONS[code], display=displays.get(BUDGET_NAMES[code], one_decimal(value / total * 100)), color=BUDGET_COLORS[i])
           for i, (code, value) in enumerate(ordered[:3])]
    return dict(boxes=boxes, top=top, total=format_number(total, money=True))
