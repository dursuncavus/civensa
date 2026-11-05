"""Numbers offered to editors and resolved again from the rendered report only."""
from collections import Counter
from decimal import Decimal
from hashlib import sha256

from ..numbers import format_number
from .recipes import complete_sum, number, rate


def staff_values(payload):
    units = {u['department_id']: u for u in payload.get('unit_manifest', [])}
    groups = {dep: [] for dep in units}
    names = {dep: u.get('department') for dep, u in units.items()}
    rows = payload.get('resources', {}).get('employment', {}).get('rows', [])
    for row in rows:
        dep = row.get('department_id')
        if dep is not None:
            groups.setdefault(dep, []).append(row.get('count'))
            names.setdefault(dep, row.get('department'))
    values = [(dep, names[dep], complete_sum(items)) for dep, items in groups.items()]
    total = complete_sum(value for _, _, value in values)
    if any(row.get('department_id') is None for row in rows) or payload.get('missing_units'):
        total = None
    return total, values


def budget_values(payload):
    budget = payload.get('financial', {}).get('tables', {}).get('expenditure', {})
    rows, totals = budget.get('rows', []), budget.get('totals', {})
    final = complete_sum(row.get('final') for row in rows)
    actual = complete_sum(row.get('actual') for row in rows)
    if any(totals.get(key, {}).get('missing', 0) for key in ('final', 'actual')):
        final = actual = None
    scale = Decimal(1_000_000) if final is not None and actual is not None and max(abs(final), abs(actual)) >= 1_000_000 else Decimal(1)
    return final, actual, scale


def spending_values(payload):
    budget = payload.get('financial', {}).get('tables', {}).get('expenditure', {})
    rows = budget.get('rows', [])
    units = payload.get('unit_manifest', [])
    names = {u['department_id']: u.get('department') for u in units}
    groups = {}
    for row in rows:
        dep = row.get('department_id')
        if dep is not None:
            groups.setdefault(dep, []).append(row.get('actual'))
            names.setdefault(dep, row.get('department'))
    expected = {u['department_id'] for u in units + payload.get('missing_units', []) + budget.get('by_department', [])}
    values = [(dep, names[dep], complete_sum(items)) for dep, items in groups.items()]
    if (values and expected <= groups.keys() and all(v is not None for _, _, v in values)
            and all(row.get('department_id') is not None for row in rows)
            and not budget.get('totals', {}).get('actual', {}).get('missing', 0)):
        return values
    return []


def facts(payload, unit_sources):
    """No stored or typed numbers; missing, ambiguous and unverified facts vanish.

    Money values and units are scaled together. The shared budget scale matches
    the existing KPI; unit spending uses millions from one million TL onward.
    """
    sections = {s['code']: s for s in payload.get('sections', [])}
    report = f"{payload['year']} Faaliyet Raporu · {payload.get('organization', 'İdare')}"
    result = []

    def add(key, label, dep, value, unit, code, *, money=False, scale=Decimal(1)):
        if value is None:
            return
        value = Decimal(value) / scale
        result.append(dict(key=key, label=label, department_id=dep, value=value,
            unit=unit, display=format_number(value, money=money),
            source=f"{report} · {sections.get(code, {}).get('title', code)}"))

    total, staff = staff_values(payload)
    add('org:staff_total', 'Toplam personel', None, total, 'kişi', 'I.C.4')
    final, actual, scale = budget_values(payload)
    unit = 'milyon TL' if scale > 1 else 'TL'
    if final is not None and actual is not None:
        add('org:budget_final', 'Kesinleşen ödenek', None, final, unit, 'III.A.1', money=True, scale=scale)
        add('org:budget_actual', 'Yıl sonu harcama', None, actual, unit, 'III.A.1', money=True, scale=scale)
        add('org:budget_rate', 'Bütçe gerçekleşme oranı', None, rate(actual, final), 'yüzde', 'III.A.1')
    for dep, name, value in staff:
        add(f'unit:{dep}:staff', f'{name} · Personel', dep, value, 'kişi', 'I.C.4')
    for dep, name, value in spending_values(payload):
        scale = Decimal(1_000_000) if abs(value) >= 1_000_000 else Decimal(1)
        add(f'unit:{dep}:spending', f'{name} · Harcama', dep, value,
            'milyon TL' if scale > 1 else 'TL', 'III.A.1', money=True, scale=scale)
    # Count across all sources too, so duplicate source entries cannot offer an
    # ambiguous identity. Names are exact; never trim or normalize the identity.
    counts = Counter((u['department_id'], i.get('name')) for u in unit_sources
        for i in u.get('core', {}).get('indicators', []) if u.get('department_id') is not None)
    for source in unit_sources:
        dep = source.get('department_id')
        if dep is None:
            continue
        for indicator in source.get('core', {}).get('indicators', []):
            name = indicator.get('name')
            if not isinstance(name, str) or not name or counts[dep, name] != 1 or indicator.get('actual_state') != 'verified':
                continue
            key = f'ind:{dep}:{sha256(name.encode("utf-8")).hexdigest()[:16]}:actual'
            value = number(indicator.get('actual'))
            unit = indicator.get('unit') or ''
            money = unit == 'TL'
            scale = Decimal(1_000_000) if money and value is not None and abs(value) >= 1_000_000 else Decimal(1)
            add(key, name, dep, value, 'milyon TL' if scale > 1 else unit, 'III.B.2.i', money=money, scale=scale)
    return result
