import pytest
from sqlalchemy import select
from app.models import ActivityCostValue, DepartmentCostValue, EconomicValue, Submission
from app.main import department_progress_overview


def row(db, sample):
    return department_progress_overview(db, sample['period'])['rows'][0]


@pytest.mark.parametrize('problem', ['missing_finance', 'missing_economic_zero', 'unverified_personnel', 'mismatch', 'missing_card'])
def test_invalid_package_never_ready(client, db, sample, problem):
    assert client.post(f'/api/indicators/{sample["indicator"].id}/save', json={}).status_code == 200
    assert row(db, sample)['state'] == 'ready'
    if problem == 'missing_finance': db.delete(db.scalar(select(ActivityCostValue).where(ActivityCostValue.year == 2028, ActivityCostValue.funding_type == 'outside')))
    elif problem == 'missing_economic_zero': db.delete(db.scalar(select(EconomicValue).where(EconomicValue.year == 2027, EconomicValue.category == 'lending', EconomicValue.funding_type == 'outside')))
    elif problem == 'unverified_personnel': db.scalar(select(DepartmentCostValue)).state = 'needs_review'
    elif problem == 'mismatch': db.scalar(select(EconomicValue).where(EconomicValue.category == 'goods_services', EconomicValue.funding_type == 'inside')).amount += 1
    else: sample['activity'].card_id = None
    db.commit(); db.expire_all()
    result = row(db, sample)
    assert result['state'] == 'needs_attention'
    assert result['progress_percent'] < 100
    assert result['warning_count'] > 0
    assert client.post('/api/departments/1/submit').status_code == 422


def test_corrected_finance_restores_ready(client, db, sample):
    client.post('/api/indicators/1/save', json={})
    cost = db.scalar(select(DepartmentCostValue)); cost.state = 'needs_review'; db.commit()
    assert row(db, sample)['state'] == 'needs_attention'
    cost.state = 'verified'; db.commit()
    assert row(db, sample)['state'] == 'ready'
    assert row(db, sample)['progress_percent'] == 100


@pytest.mark.parametrize('status', ['submitted', 'approved', 'returned'])
def test_workflow_progress_status_preserved(client, db, sample, status):
    client.post('/api/indicators/1/save', json={})
    db.scalar(select(Submission)).status = status
    db.scalar(select(DepartmentCostValue)).state = 'needs_review'; db.commit()
    result = row(db, sample)
    assert result['state'] == status
    assert result['progress_percent'] == 100 if status != 'returned' else result['progress_percent'] < 100
