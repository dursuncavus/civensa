"""Book-derived first-load catalogue; no commits, UI or database creation here."""
from collections import defaultdict

from sqlalchemy import select

from .data_importer import _activity_identity
from .import_service import consolidate_source_departments, department_key
from .models import (Activity, ActivityCatalogueLink, ActivityResponsibility, Department,
                     OfficialActivity, ReportingPeriod, Submission)
from .program_service import save_activity_catalogue_links, save_catalogue_entry


def apply_first_load_batch(db, batch, actor):
    """The shared dry-run/live write path; caller owns the transaction.

    D-111: keep importer cell states and draft submissions. Department validation
    is diagnostic; structural import/catalogue guards still apply unchanged.
    """
    import json
    from .import_service import apply_import_batch
    from .program_service import validate_department

    parsed = json.loads(batch.payload_json)
    applied = apply_import_batch(db, batch)
    catalogue = load_first_load_catalogue(db, batch.period_id, parsed, actor)
    validations = []
    keys = {department_key(d['name']) for d in parsed['departments']}
    for department in db.scalars(select(Department).order_by(Department.name)):
        if department_key(department.name) in keys:
            errors, warnings = validate_department(db, batch.period_id, department.id)
            validations.append(dict(department_id=department.id, name=department.name,
                                    errors=errors, warnings=warnings))
    return applied, catalogue, validations


def load_first_load_catalogue(db, period_id, parsed, actor):
    """Add exact book entries/responsibilities/links idempotently, with service audit.

    Codes of programmes/subprogrammes are absent from the card source: leave them
    blank. Activity codes are local to the card; entry identity includes its name.
    Existing responsibilities and links are preserved. The caller commits all
    import + catalogue changes together, or rolls them back together.
    """
    if actor.role not in {'strategy', 'admin'}:
        raise ValueError('İlk yükleme kataloğunu Strateji kullanıcısı yüklemelidir.')
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.id == period_id).with_for_update())
    if not period or period.status not in {'draft', 'active'}:
        raise ValueError('İlk yükleme için açık bir dönem seçin.')
    departments = defaultdict(list)
    for department in db.scalars(select(Department)):
        departments[department_key(department.name)].append(department)
    planned = {}
    for source in consolidate_source_departments(parsed)['departments']:
        if not any('activity_memberships' in b for b in source['blocks']):
            continue
        matches = departments[department_key(source['name'])]
        if len(matches) != 1:
            raise ValueError(f"{source['name']}: katalog için tekil müdürlük eşleşmesi gerekli.")
        department = matches[0]
        submission = db.scalar(select(Submission).where(Submission.period_id == period_id,
                                                        Submission.department_id == department.id))
        if submission and submission.status not in {'draft', 'returned'}:
            raise ValueError(f'{department.name}: incelemedeki/onaylı paketin kataloğu değiştirilemez.')
        activities = defaultdict(list)
        for activity in db.scalars(select(Activity).where(Activity.period_id == period_id,
                                                          Activity.department_id == department.id)):
            activities[_activity_identity(activity.name)].append(activity)
        for block in source['blocks']:
            for member in block.get('activity_memberships', []):
                identity = _activity_identity(member['name'])
                matches = activities[identity]
                if len(matches) > 1 or identity[0] != 'code':
                    raise ValueError(f"{department.name} / {member['name']}: katalog için tekil kodlu faaliyet gerekli.")
                values = dict(program_code='', program_name=block['program'].strip(),
                              subprogram_code='', subprogram_name=block['subprogram'].strip(),
                              code=identity[1], name=member['name'].strip())
                key = tuple(values.values())
                entry = planned.setdefault(key, dict(values=values, departments=set(), activities=set(), sources=[]))
                entry['departments'].add(department.id)
                if matches:
                    entry['activities'].add(matches[0].id)
                entry['sources'].append(dict(department=department.name, **member,
                    page=parsed.get('source_tables', {}).get(str(member['table_number']), {}).get('page')))
    # Resolve every existing entry before any writes: duplicates need a human decision.
    for entry in planned.values():
        matches = db.scalars(select(OfficialActivity).where(OfficialActivity.period_id == period_id,
            *(getattr(OfficialActivity, field) == value for field, value in entry['values'].items()))).all()
        if len(matches) > 1:
            raise ValueError(f"{entry['values']['name']}: yinelenen resmî katalog kaydını kontrol edin.")
        entry['existing'] = matches[0] if matches else None
    new_entries = sum(entry['existing'] is None for entry in planned.values())
    links = defaultdict(set)
    with db.begin_nested():
        for entry in planned.values():
            existing = entry['existing']
            ids = set(db.scalars(select(ActivityResponsibility.department_id).where(
                ActivityResponsibility.official_activity_id == existing.id))) if existing else set()
            official = save_catalogue_entry(db, period_id, entry['values'], ids | entry['departments'],
                                            actor, obj=existing, source=entry['sources'])
            for aid in entry['activities']:
                links[aid].add(official.id)
        db.flush()  # Responsibilities must exist before the shared link validator runs.
        for aid, ids in links.items():
            existing = set(db.scalars(select(ActivityCatalogueLink.official_activity_id).where(
                ActivityCatalogueLink.activity_id == aid)))
            save_activity_catalogue_links(db, db.get(Activity, aid), existing | ids, actor,
                                          source={'kind': 'first_load_book_membership'})
    return dict(entries=len(planned), created_entries=new_entries,
                responsibilities=sum(len(e['departments']) for e in planned.values()),
                links=sum(map(len, links.values())))
