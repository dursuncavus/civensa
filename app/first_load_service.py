"""Book-derived first-load catalogue; no commits, UI or database creation here."""
from collections import defaultdict
import hashlib
import json

from sqlalchemy import select

from .data_importer import _activity_identity
from .import_service import consolidate_source_departments, department_key
from .models import (Activity, ActivityCatalogueLink, ActivityResponsibility, Department,
                     OfficialActivity, ReportingPeriod, Submission)
from .program_service import save_activity_catalogue_links, save_catalogue_entry


def period_rows_hash(db, year=2027, parts=False):
    """Hash period ownership, including historical values owned by 2027 rows.

    Core reads observe flushed SQL/trigger changes rather than the identity map.
    No user/credential rows enter the snapshot. Shared departments are protected
    too: 2026 must use the existing structure without renaming it.
    """
    from sqlalchemy import or_
    from .db import Base
    tables = Base.metadata.tables
    periods = select(ReportingPeriod.id).where(ReportingPeriod.year == year)
    conditions = {name: table.c.period_id.in_(periods) for name, table in tables.items()
                  if 'period_id' in table.c}
    conditions['reporting_periods'] = tables['reporting_periods'].c.year == year
    conditions['departments'] = True
    for child, parent, field in (
        ('indicator_values', 'indicators', 'indicator_id'),
        ('activity_cost_values', 'activities', 'activity_id'),
        ('activity_responsibilities', 'official_activities', 'official_activity_id'),
        ('subprogram_scopes', 'department_scopes', 'scope_id'),
    ):
        conditions[child] = tables[child].c[field].in_(
            select(tables[parent].c.id).where(conditions[parent]))
    links = tables['activity_catalogue_links']
    conditions['activity_catalogue_links'] = or_(
        links.c.activity_id.in_(select(Activity.id).where(Activity.period_id.in_(periods))),
        links.c.official_activity_id.in_(select(OfficialActivity.id).where(OfficialActivity.period_id.in_(periods))))
    snapshot = {}
    for name, condition in sorted(conditions.items()):
        table = tables[name]
        rows = db.execute(select(table).where(condition).order_by(*table.primary_key.columns)).mappings()
        snapshot[name] = [dict(row) for row in rows]
    if parts:
        # D-396 diagnostics: per-table row count + digest; names are schema only.
        return {name: (len(rows), hashlib.sha256(json.dumps(rows, sort_keys=True, default=str,
                ensure_ascii=False).encode()).hexdigest()) for name, rows in snapshot.items()}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, default=str,
                                     ensure_ascii=False).encode()).hexdigest()


def changed_tables(before, after):
    """Names of tables whose per-table digest differs (both from parts=True)."""
    return sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))


def apply_first_load_batch(db, batch, actor):
    period = db.get(ReportingPeriod, batch.period_id)
    if not period or period.year != 2026:
        return _apply_first_load_batch(db, batch, actor)
    # Savepoint makes refusal atomic even if the caller catches it and commits.
    with db.begin_nested():
        before = period_rows_hash(db, parts=True)
        result = _apply_first_load_batch(db, batch, actor)
        db.flush()
        after = period_rows_hash(db, parts=True)
        if after != before:
            error = ValueError('2027 satırları değişecekti; 0 satır yazıldı. 2026 yüklemesi geri alındı; sorumluya bildirin.')
            error.changed_tables = changed_tables(before, after)
            raise error
        return result


def _apply_first_load_batch(db, batch, actor):
    """The shared dry-run/live write path; caller owns the transaction.

    D-111: keep importer cell states and draft submissions. Department validation
    is diagnostic; structural import/catalogue guards still apply unchanged.
    """
    import json
    from .import_service import apply_import_batch
    from .program_service import validate_department

    parsed = json.loads(batch.payload_json)
    if db.get(ReportingPeriod, batch.period_id).year == 2026:
        from .import_service import build_department_plan
        plan = build_department_plan(db, parsed)
        bad = [m['source_name'] for m in plan['mappings']
               if m['action'] != 'match' or m['confidence'] != 1]
        if bad:
            raise ValueError('2026 için tekil mevcut müdürlük eşleşmesi gerekli: ' + ', '.join(bad))
    applied = apply_import_batch(db, batch)
    if db.get(ReportingPeriod, batch.period_id).year == 2026:
        from .models import DepartmentScope
        names = parsed.get('book_department_names', {})
        for source in parsed['departments']:
            mapping = next(m for m in plan['mappings'] if department_key(m['source_name']) == department_key(source['name']))
            department = db.get(Department, mapping['department_id'])
            book_name = names.get(source['name'])
            if not book_name:
                raise ValueError(f"{source['name']}: 2026 Sorumlu İdare adı eksik; onaylı kitaptan yeniden plan alın.")
            scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == batch.period_id,
                                                           DepartmentScope.department_id == department.id))
            if scope is None:
                scope = DepartmentScope(period_id=batch.period_id, department_id=department.id)
                db.add(scope)
            scope.display_name = book_name if book_name != department.name else ''
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
    if period.year == 2026:
        return _load_2026_catalogue(db, period_id, parsed, actor)
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


def _load_2026_catalogue(db, period_id, parsed, actor):
    """Description tuples define entries; only unique equal names define links."""
    from .data_importer import _label_key
    planned = {}
    departments = defaultdict(list)
    for department in db.scalars(select(Department)):
        departments[department_key(department.name)].append(department)
    for source in parsed.get('catalogue_descriptions', []):
        matches = departments[department_key(source['department'])]
        if len(matches) != 1:
            raise ValueError(f"{source['department']}: katalog için tekil müdürlük eşleşmesi gerekli.")
        submission = db.scalar(select(Submission).where(Submission.period_id == period_id,
                                                        Submission.department_id == matches[0].id))
        if submission and submission.status not in {'draft', 'returned'}:
            raise ValueError(f"{source['department']}: incelemedeki/onaylı paketin kataloğu değiştirilemez.")
        key = tuple(source[k].strip() for k in ('program', 'subprogram', 'name', 'explanation'))
        entry = planned.setdefault(key, dict(departments=set(), sources=[]))
        entry['departments'].add(matches[0].id)
        entry['sources'].append(source)
    # OfficialActivity has no description column. Preserve the complete source
    # tuple in the existing catalogue audit; the name hash is a technical key,
    # never an invented Ministry activity code (the code field is limited to 80).
    created = 0
    candidates = defaultdict(list)
    with db.begin_nested():
        for key, entry in planned.items():
            program, subprogram, name, explanation = key
            identity = hashlib.sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()
            values = dict(program_code='', program_name=program, subprogram_code='',
                          subprogram_name=subprogram, code='name:' + identity, name=name)
            matches = db.scalars(select(OfficialActivity).where(OfficialActivity.period_id == period_id,
                                      OfficialActivity.code == values['code'])).all()
            if len(matches) > 1:
                raise ValueError(f'{name}: yinelenen 2026 katalog kimliği; sorumluya bildirin.')
            existing = matches[0] if matches else None
            ids = set(db.scalars(select(ActivityResponsibility.department_id).where(
                ActivityResponsibility.official_activity_id == existing.id))) if existing else set()
            official = save_catalogue_entry(db, period_id, values, ids | entry['departments'], actor,
                                            obj=existing, source=entry['sources'])
            created += existing is None
        db.flush()
        for official, did in db.execute(select(OfficialActivity, ActivityResponsibility.department_id).join(
                ActivityResponsibility).where(OfficialActivity.period_id == period_id)):
            candidates[(did, _label_key(official.name))].append(official.id)
        activities = db.scalars(select(Activity).where(Activity.period_id == period_id,
            Activity.department_id.in_({did for e in planned.values() for did in e['departments']}))).all()
        local = defaultdict(list)
        for activity in activities:
            local[(activity.department_id, _label_key(activity.name))].append(activity)
        linked, unlinked = 0, []
        for activity in activities:
            key = (activity.department_id, _label_key(activity.name))
            ids = candidates[key]
            if len(ids) == len(local[key]) == 1:
                save_activity_catalogue_links(db, activity, ids, actor, source={'kind': 'first_load_2026_exact_name'})
                linked += 1
            else:
                department = db.get(Department, activity.department_id)
                unlinked.append(dict(department=department.name, name=activity.name,
                                     candidates=len(ids)))
    return dict(entries=len(planned), created_entries=created,
                responsibilities=sum(len(e['departments']) for e in planned.values()),
                links=linked, unlinked=unlinked)
