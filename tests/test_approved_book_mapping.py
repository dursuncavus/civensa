"""CIV-178: recorded mappings are the only allowed approved-book difference."""
import csv
import io
import json

import pytest
from sqlalchemy import select

from app.models import Activity, ActivityCostValue, AuditLog, Publication, ReportCard, SubProgram
from app.program_service import approved_book_provenance
from test_approved_book_publication import approved_books, walk, period, publish

pytestmark = pytest.mark.postgres


def pending(db, pid):
    return db.scalar(select(Activity).where(Activity.period_id == pid,
        Activity.subprogram_id.is_(None)).order_by(Activity.id))


def choices(db, activity):
    return db.scalars(select(SubProgram).join(ReportCard, ReportCard.subprogram_id == SubProgram.id)
        .where(ReportCard.period_id == activity.period_id,
               ReportCard.department_id == activity.department_id)
        .order_by(SubProgram.id).distinct()).all()


def apply_csv(client, token, pid, activity, subprogram):
    # Use the real export, including its exact Turkish names and header format.
    reader = csv.DictReader(io.StringIO(client.get('/api/activity-mappings/export.csv',
        params={'period_id': pid}).content.decode('utf-8-sig')))
    row = next(row for row in reader if int(row['Faaliyet ID']) == activity.id)
    row['Seçilecek Program / Alt Program'] = f'{subprogram.program.name} / {subprogram.name}'
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerow(row)
    response = client.post('/api/activity-mappings/import-apply',
        data={'csrf_token': token, 'period_id': pid},
        files={'file': ('mapping.csv', stream.getvalue().encode('utf-8-sig'), 'text/csv')})
    assert response.status_code == 200, response.text[:1200]
    assert response.json()['updated'] == 1
    return response.json()['batch_id']


def bulk(client, token, pid, activity, subprogram):
    response = client.post('/api/activity-mappings/bulk', headers={'X-CSRF-Token': token},
        json={'period_id': pid, 'assignments': [dict(activity_id=activity.id, subprogram_id=subprogram.id)]})
    assert response.status_code == 200, response.text[:1200]
    assert response.json()['updated'] == 1


def revert(client, token, pid, batch):
    response = client.post(f'/api/activity-mappings/batches/{batch}/revert',
        data={'csrf_token': token, 'period_id': pid})
    assert response.status_code == 200, response.text[:1200]


@pytest.mark.parametrize('route', ['csv', 'bulk'])
def test_recorded_mapping_publishes_and_seals_compact_proof(walk, route):
    db, client, _, _, _, token = walk
    pid = period(db).id
    activity = pending(db, pid)
    subprogram = choices(db, activity)[0]
    batches = [apply_csv(client, token, pid, activity, subprogram)] if route == 'csv' else []
    if route == 'bulk':
        bulk(client, token, pid, activity, subprogram)
    assert publish(client, token, pid).status_code == 303
    publication = db.scalar(select(Publication).where(Publication.period_id == pid))
    expected = dict(count=1, batch_ids=batches)
    assert json.loads(publication.snapshot_json)['activity_mapping'] == expected
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'publication_approved_book',
        AuditLog.entity_id == publication.id))
    assert json.loads(audit.details)['activity_mapping'] == expected


def test_reverted_mapping_has_zero_count_and_reapply_uses_new_batch(walk):
    db, client, _, _, _, token = walk
    pid = period(db).id
    activity = pending(db, pid)
    subprogram = choices(db, activity)[0]
    first = apply_csv(client, token, pid, activity, subprogram)
    revert(client, token, pid, first)
    assert approved_book_provenance(db, pid)['activity_mapping'] == dict(count=0, batch_ids=[])
    second = apply_csv(client, token, pid, activity, subprogram)
    assert approved_book_provenance(db, pid)['activity_mapping'] == dict(count=1, batch_ids=[second])
    revert(client, token, pid, second)
    assert publish(client, token, pid).status_code == 303
    publication = db.scalar(select(Publication).where(Publication.period_id == pid))
    assert json.loads(publication.snapshot_json)['activity_mapping'] == dict(count=0, batch_ids=[])


def test_only_active_batch_ids_are_recorded(walk):
    db, client, _, _, _, token = walk
    pid = period(db).id
    activities = db.scalars(select(Activity).where(Activity.period_id == pid,
        Activity.subprogram_id.is_(None)).order_by(Activity.id).limit(2)).all()
    first, second = [apply_csv(client, token, pid, a, choices(db, a)[0]) for a in activities]
    revert(client, token, pid, first)
    assert approved_book_provenance(db, pid)['activity_mapping'] == dict(count=1, batch_ids=[second])
    bulk(client, token, pid, activities[1], choices(db, activities[1])[1])
    assert approved_book_provenance(db, pid)['activity_mapping'] == dict(count=1, batch_ids=[])


def test_book_membership_move_is_refused(walk):
    db, client, _, _, _, token = walk
    pid = period(db, 2027).id
    activity = db.scalar(select(Activity).where(Activity.period_id == pid,
        Activity.subprogram_id.is_not(None)).order_by(Activity.id))
    target = next(sp for sp in choices(db, activity) if sp.id != activity.subprogram_id)
    bulk(client, token, pid, activity, target)
    assert publish(client, token, pid).status_code == 409


@pytest.mark.parametrize('change', ['name', 'cost', 'missing_audit', 'wrong_target',
    'foreign_period', 'card', 'generic_update', 'changed_back', 'other_authorship'])
def test_mapping_does_not_hide_other_changes(walk, change):
    db, client, _, _, _, token = walk
    pid = period(db).id
    activity = pending(db, pid)
    subprogram = choices(db, activity)[0]
    batch = apply_csv(client, token, pid, activity, subprogram)
    if change == 'name':
        activity.name += ' değişti'
    elif change == 'cost':
        cost = db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == activity.id,
            ActivityCostValue.amount.is_not(None)))
        cost.amount += 1
    elif change == 'missing_audit':
        db.delete(db.scalar(select(AuditLog).where(AuditLog.action == 'activity_mapping_csv',
            AuditLog.entity_id == activity.id)))
    elif change == 'wrong_target':
        activity.subprogram_id = choices(db, activity)[1].id
    elif change == 'foreign_period':
        foreign = db.scalar(select(SubProgram).where(SubProgram.period_id != pid))
        activity.subprogram_id = foreign.id
        audit = db.scalar(select(AuditLog).where(AuditLog.action == 'activity_mapping_csv',
            AuditLog.entity_id == activity.id))
        audit.details = f'batch={batch};subprogram_id={foreign.id}'
    elif change == 'card':
        activity.card_id = db.scalar(select(ReportCard.id).where(ReportCard.period_id == pid,
            ReportCard.department_id == activity.department_id))
    elif change == 'generic_update':
        db.add(AuditLog(action='activity_update', entity_type='activity', entity_id=activity.id))
    elif change == 'changed_back':
        bulk(client, token, pid, activity, choices(db, activity)[1])
        activity.subprogram_id = subprogram.id
    elif change == 'other_authorship':
        actor_id = db.scalar(select(AuditLog.user_id).where(AuditLog.action == 'activity_mapping_csv',
            AuditLog.entity_id == activity.id))
        # Same scope/actor and adjacent audit IDs do not prove the same write.
        db.add(AuditLog(user_id=actor_id, action='pp_data_change', entity_type='department',
            entity_id=activity.department_id, details=f'period_id={pid}'))
    db.commit()
    assert publish(client, token, pid).status_code == 409
