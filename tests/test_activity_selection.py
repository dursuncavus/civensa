import pytest
from sqlalchemy import select, func
from app.models import Activity, ReportingPeriod, Program, SubProgram


@pytest.mark.parametrize('raw', ['yanlış', [], {}, True, 1.5, '1.5', -1, 0, None, '', 10**100])
@pytest.mark.parametrize('operation', ['create', 'update'])
def test_invalid_subprogram_rejected_without_mutation(client, db, sample, raw, operation):
    activity = sample['activity']
    before = (activity.name, activity.explanation, activity.subprogram_id, activity.card_id)
    count = db.scalar(select(func.count()).select_from(Activity))
    payload = {'period_id': sample['period'].id, 'name': 'Değişmemeli', 'explanation': 'Değişmemeli', 'subprogram_id': raw}
    response = (client.post('/api/activities', json=payload) if operation == 'create'
                else client.put(f'/api/activities/{activity.id}', json=payload))
    assert response.status_code == 422
    assert isinstance(response.json()['detail'], str)
    db.expire_all()
    assert (activity.name, activity.explanation, activity.subprogram_id, activity.card_id) == before
    assert db.scalar(select(func.count()).select_from(Activity)) == count


@pytest.mark.parametrize('operation', ['create', 'update'])
@pytest.mark.parametrize('raw_kind', ['integer', 'string', 'missing', 'other_period'])
def test_subprogram_scope_and_valid_selection(client, db, sample, operation, raw_kind):
    sid = sample['subprogram'].id
    if raw_kind == 'string': sid = str(sid)
    if raw_kind == 'missing': sid = 9999
    if raw_kind == 'other_period':
        period = ReportingPeriod(year=2030, status='draft'); db.add(period); db.flush()
        program = Program(period_id=period.id, name='Başka'); db.add(program); db.flush()
        subprogram = SubProgram(period_id=period.id, program_id=program.id, name='Başka')
        db.add(subprogram); db.commit(); sid = subprogram.id
    payload = {'period_id': sample['period'].id, 'name': 'Geçerli faaliyet', 'subprogram_id': sid}
    response = (client.post('/api/activities', json=payload) if operation == 'create'
                else client.put(f'/api/activities/{sample["activity"].id}', json=payload))
    assert response.status_code == (200 if raw_kind in {'integer', 'string'} else 422)
