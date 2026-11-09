"""Presentation grouping for the existing release-check evidence; no gate changes."""
from collections import OrderedDict


def release_groups(items):
    departments = OrderedDict()
    shared = []
    for item in items:
        check_id = item['id'].split(':')
        observed = item['evidence'].get('observed') or {}
        department_id = observed.get('department_id') if isinstance(observed, dict) else None
        if len(check_id) == 3 and check_id[0] == 'publication' and check_id[1] in {'scope', 'data', 'approval'}:
            department_id = int(check_id[2])
        if department_id is None:
            shared.append(item)
            continue
        name = (observed.get('label') if isinstance(observed, dict) else None) or item['label'].split(':', 1)[0]
        group = departments.setdefault(department_id, dict(id=department_id, name=name, items=[]))
        group['items'].append(item)
    return dict(departments=list(departments.values()), shared=shared)


def financial_groups(financial, names, code):
    groups = OrderedDict((name, dict(name=name, figures=[], missing=[])) for name in names.values())
    for figure in financial.get('pp_planned_figures', []):
        group = groups.setdefault(figure['department'], dict(name=figure['department'], figures=[], missing=[]))
        group['figures'].append(figure)
    shared = []
    for slot, messages in financial.get('missing', {}).items():
        if code not in {slot, 'III.A'}:
            continue
        for message in messages:
            for name, group in groups.items():
                if message.startswith(name + ':'):
                    group['missing'].append(message)
                    break
            else:
                shared.append(message)
    return dict(departments=list(groups.values()), shared=shared)
