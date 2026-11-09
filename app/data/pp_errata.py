"""Read-time FR projection. Never write to PP rows or frozen PP publications."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

ERRATA_PATH = Path(__file__).with_suffix('.json')


def errata_entries(year):
    """The repository is the only editor; no UI/API write path exists."""
    return [entry for entry in json.loads(ERRATA_PATH.read_text(encoding='utf-8'))['entries']
            if entry['year'] == year]


def _sum(rows):
    # A missing row set or any blank cell must not turn into a zero total.
    if not rows or any(row.get('amount') is None for row in rows):
        return None
    return sum((Decimal(str(row['amount'])) for row in rows), Decimal(0))


def apply_pp_errata(payload):
    """Return an independent FR view, with total-only errata and unchanged lines.

    All FR planned-cost/economic readers use this boundary. PP readers must use
    the original payload. Unknown line allocation is never spread over categories,
    programmes or funding sources. Existing review states are retained.
    """
    result = deepcopy(payload)
    year = payload.get('period')
    if year != 2026:
        result['planned_figures'] = []
        return result
    entries = errata_entries(year)
    figures = []
    for department in result.get('departments', []):
        if (department.get('scope') or {}).get('status') == 'excluded':
            continue
        # Prefer the publication's period name; it is part of the printed book.
        name = (department.get('scope') or {}).get('display_name') or department['department']
        for value_year in range(year, year + 3):
            kind = 'budget' if value_year == year else 'forecast'
            current = lambda row: row.get('year') == value_year and row.get('value_kind') == kind
            activities = department.get('activities', [])
            costs = [row for activity in activities
                     for row in activity.get('costs', []) if current(row) and row.get('funding_type') == 'total']
            personnel = [row for row in department.get('department_costs', [])
                         if current(row) and row.get('category') == 'personnel_sgk']
            economics = [row for row in department.get('economics', []) if current(row)]
            # Both components are necessary for a complete cost table total.
            cost_amount = (_sum(costs + personnel)
                           if activities and len(costs) == len(activities) and len(personnel) == 1 else None)
            for table, rows, amount in [('cost', costs + personnel, cost_amount),
                                        ('economic', economics, _sum(economics))]:
                figure = dict(department_id=department['department_id'], department=name,
                    year=value_year, table=table, amount=amount, stored_amount=amount,
                    errata=[], needs_review=any(row.get('state', 'verified') != 'verified' for row in rows))
                if table == 'economic':
                    figure['sources'] = {fund: _sum([row for row in economics if row.get('funding_type') == fund])
                                         for fund in ('inside', 'outside')}
                for entry in entries:
                    if (entry['department'], entry['value_year'], entry['table'], entry['field']) != (name, value_year, table, 'total'):
                        continue
                    expected = Decimal(entry.get('stored_total', entry['printed_value']))
                    if amount is None or amount != expected:
                        figure['errata_warning'] = (f"BELİRSİZ: {entry['item_id']} / {name} / {value_year}: "
                            'saklanan toplam düzeltme kaydıyla eşleşmiyor. Strateji kaynak satırları kontrol etmelidir.')
                        continue
                    if entry.get('printed_context'):
                        try:
                            contexts = [json.loads(row.get('source_context_json') or '{}') for row in economics]
                            if any(not isinstance(context, dict) for context in contexts):
                                contexts = []
                        except (ValueError, TypeError):
                            contexts = []
                        if not any(cell.get('year') == value_year and cell.get('kind') == kind
                                   and cell.get('raw_text') == entry['printed_context']
                                   for context in contexts for cell in context.get('totals', {}).get('total', [])):
                            figure['errata_warning'] = (f"BELİRSİZ: {entry['item_id']} / {name} / {value_year}: "
                                'basılı toplamın kaynak bağlamı eşleşmiyor. Strateji kaynak tabloyu kontrol etmelidir.')
                            continue
                    figure['amount'] = Decimal(entry['corrected_value'])
                    figure['errata'].append(dict(entry,
                        marker=f"Düzeltildi ({entry['item_id']}, s.{entry['page']})"))
                figures.append(figure)
    result['planned_figures'] = figures
    return result
