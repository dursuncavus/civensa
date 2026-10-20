"""PP-08: an activity is mapped only after all three links are present."""
import csv
import io

import pytest
from sqlalchemy import delete

from app.main import app, require_user
from app.models import Activity, ActivityCatalogueLink, AuditLog, ReportingPeriod

pytestmark = pytest.mark.postgres


@pytest.fixture
def strategy_client(client, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    return client


def remove_link(db, activity, kind):
    if kind == 'catalogue':
        db.execute(delete(ActivityCatalogueLink).where(ActivityCatalogueLink.activity_id == activity.id))
    else:
        setattr(activity, kind + '_id', None)
    db.commit()


@pytest.mark.parametrize('kind', ['subprogram', 'card', 'catalogue', None])
def test_queue_requires_all_three_links(strategy_client, db, sample, kind):
    db.add(AuditLog(user_id=sample['user'].id, action='indicator_update', entity_type='indicator', entity_id=sample['indicator'].id))
    db.commit()
    if kind:
        remove_link(db, sample['activity'], kind)
    response = strategy_client.get('/activity-mapping?period_id=1')
    assert response.status_code == 200
    assert ('Hazır' in response.text) == (kind is None)
    context = response.context
    assert context['unresolved_count'] == int(kind is not None)
    assert context['mapping_counts'] == {
        'subprogram': int(kind == 'subprogram'), 'card': int(kind == 'card'),
        'catalogue': int(kind == 'catalogue'), 'total': int(kind is not None),
    }
    records = strategy_client.get('/api/operations/status?period_id=1').json()['records']
    assert records['unresolved_activities'] == int(kind is not None)
    assert records['mapping_gaps'] == context['mapping_counts']
    progress = strategy_client.get('/api/progress?period_id=1').json()['rows'][0]
    assert progress['unresolved_activities'] == int(kind is not None)
    assert progress['mapping_gaps'] == context['mapping_counts']
    assert progress['state'] == ('needs_attention' if kind else 'ready')
    assert (progress['progress_percent'] == 100) == (kind is None)
    assert strategy_client.get('/dashboard?period_id=1').context['unresolved_count'] == int(kind is not None)


def test_counters_count_each_gap_and_distinct_activities_in_selected_period(strategy_client, db, sample):
    activity = sample['activity']
    remove_link(db, activity, 'card')
    remove_link(db, activity, 'catalogue')
    db.add(Activity(period_id=1, department_id=activity.department_id, name='Üç eksik'))
    other = ReportingPeriod(year=2030, status='draft')
    db.add(other)
    db.flush()
    db.add(Activity(period_id=other.id, department_id=activity.department_id, name='Başka dönem'))
    db.commit()
    context = strategy_client.get('/activity-mapping?period_id=1').context
    assert context['mapping_counts'] == {'subprogram': 1, 'card': 2, 'catalogue': 2, 'total': 2}
    assert len(context['groups'][0]['activities']) == 2


def test_export_states_and_csv_import_compatibility(strategy_client, db, sample):
    from app.main import MAPPING_CSV_HEADERS
    remove_link(db, sample['activity'], 'subprogram')
    response = strategy_client.get('/api/activity-mappings/export.csv?period_id=1')
    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[0][-3:] == ['Alt program durumu', 'Kart durumu', 'Resmî katalog durumu']
    assert rows[1][-3:] == ['Eksik', 'Tamam', 'Tamam']
    rows[1][6] = f"{sample['subprogram'].program.name} / {sample['subprogram'].name}"
    for legacy in (False, True):
        output = io.StringIO()
        csv.writer(output).writerows([r[:len(MAPPING_CSV_HEADERS)] if legacy else r for r in rows])
        data = output.getvalue().encode('utf-8-sig')
        preview = strategy_client.post('/api/activity-mappings/import-preview?period_id=1', files={'file': ('queue.csv', data, 'text/csv')})
        assert preview.status_code == 200
        assert preview.json()['ok'], preview.text
    # Subprogram mapping must not make a cardless activity disappear.
    remove_link(db, sample['activity'], 'card')
    result = strategy_client.post('/api/activity-mappings/import-apply?period_id=1', files={'file': ('queue.csv', data, 'text/csv')})
    assert result.status_code == 200, result.text
    assert result.json()['remaining'] == 1
    assert result.json()['mapping_gaps']['card'] == 1
    assert 'Hazır' not in strategy_client.get('/activity-mapping?period_id=1').text
    rows = list(csv.DictReader(io.StringIO(strategy_client.get('/api/activity-mappings/export.csv?period_id=1').content.decode('utf-8-sig'))))
    assert len(rows) == 1
    assert rows[0]['Kart durumu'] == 'Eksik'
    assert rows[0]['Alt program durumu'] == 'Tamam'


@pytest.mark.parametrize('kind', ['card', 'catalogue', None])
def test_bulk_remaining_uses_all_three_links(strategy_client, db, sample, kind):
    if kind:
        remove_link(db, sample['activity'], kind)
    remove_link(db, sample['activity'], 'subprogram')
    result = strategy_client.post('/api/activity-mappings/bulk?period_id=1', json={
        'assignments': [{'activity_id': sample['activity'].id, 'subprogram_id': sample['subprogram'].id}],
    })
    assert result.status_code == 200, result.text
    assert result.json()['updated'] == 1
    assert result.json()['remaining'] == int(kind is not None)
    assert result.json()['mapping_gaps']['total'] == int(kind is not None)


def test_bulk_subprogram_change_leaves_cleared_card_visible(strategy_client, db, sample):
    from app.models import Indicator, SubProgram
    previous = sample['subprogram']
    other = SubProgram(period_id=1, program_id=previous.program_id, name='Diğer alt program')
    db.add(other)
    db.flush()
    db.add(Indicator(period_id=1, department_id=sample['department'].id, subprogram_id=other.id,
                     name='Diğer gösterge', unit='Adet'))
    db.commit()
    response = strategy_client.post('/api/activity-mappings/bulk?period_id=1', json={
        'assignments': [{'activity_id': sample['activity'].id, 'subprogram_id': other.id}],
    })
    assert response.status_code == 200, response.text
    assert response.json()['remaining'] == 1
    assert response.json()['mapping_gaps'] == {'subprogram': 0, 'card': 1, 'catalogue': 0, 'total': 1}
    db.refresh(sample['activity'])
    assert sample['activity'].card_id is None
    assert 'Hazır' not in strategy_client.get('/activity-mapping?period_id=1').text
