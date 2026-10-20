"""A missing write context must never select either of the available years."""
import pytest
from sqlalchemy import select

from app.db import Base
from app.main import app, require_user
from test_pp_period_context import two_periods

pytestmark = pytest.mark.postgres
MISSING = 'Raporlama dönemi belirtilmedi. Sayfayı yenileyip seçtiğiniz yıl üzerinden tekrar deneyin.'

# Valid owners/records ensure these requests reach the period gate. In particular,
# updates and deletes would mutate existing records if active-period fallback ran.
WRITES = [
    ('post', '/api/indicators/1/save', 'department', {'name': 'Kaydedilmemeli'}),
    ('post', '/api/activities', 'department', {'name': 'Kaydedilmemeli', 'subprogram_id': 1}),
    ('put', '/api/activities/1', 'department', {'name': 'Kaydedilmemeli'}),
    ('delete', '/api/activities/1', 'department', None),
    ('post', '/api/activities/1/contract-bound', 'department', {'contract_bound': True}),
    ('post', '/api/departments/1/personnel-costs', 'department', {'cost_2027_budget': '999'}),
    ('post', '/api/departments/1/submit', 'department', {}),
    ('post', '/api/submissions/1/decision', 'strategy', {'decision': 'return', 'note': 'Kontrol edin.'}),
    *[('post', '/program/1/' + path, 'strategy' if path == 'economic-split' else 'department', {})
      for path in ['cards', 'assign', 'indicator', 'finance/1', 'economic', 'economic-grid',
                   'catalogue-link', 'verify-value/1', 'verify-money/activity/1',
                   'verify-money/personnel/1', 'verify-money/economic/1', 'economic-split']],
    *[('post', '/report-builder/' + path, 'strategy', {})
      for path in ['scope', 'section', 'catalogue', 'publish']],
    *[('post', '/api/activity-mappings/' + path, 'strategy', {'assignments': [{'activity_id': 1, 'subprogram_id': 1}]})
      for path in ['bulk', 'batches/0123456789abcdef/revert', 'import-preview', 'import-apply']],
    *[('post', '/structure/' + path, 'strategy', {})
      for path in ['departments', 'departments/1/rename', 'departments/1/active',
                   'programs', 'programs/1', 'subprograms', 'subprograms/1',
                   'scopes', 'subprograms/1/responsibilities', 'changes', 'changes/1/cancel']],
]


def snapshot(db):
    # Includes every row count, audit record, value and workflow/structure event.
    return {table.name: sorted((tuple(row) for row in db.execute(select(table))), key=repr)
            for table in Base.metadata.sorted_tables}


@pytest.mark.parametrize('method,path,role,payload', WRITES,
                         ids=[method.upper() + ' ' + path for method, path, _, _ in WRITES])
def test_missing_write_period_is_refused_without_any_change(client, db, sample, two_periods,
                                                           method, path, role, payload, monkeypatch):
    app.dependency_overrides[require_user] = lambda: sample['strategy' if role == 'strategy' else 'user']
    before = snapshot(db)
    from app import main
    def no_active_fallback(*args):
        pytest.fail('A PP write must not consult the active period.')
    monkeypatch.setattr(main, 'active_period', no_active_fallback)
    options = {'follow_redirects': False}
    if path.endswith(('import-preview', 'import-apply')):
        options['files'] = {'file': ('mapping.csv', b'Faaliyet ID\n1\n', 'text/csv')}
    elif path.startswith(('/program/', '/report-builder/', '/structure/')):
        options['data'] = payload
    elif payload is not None:
        options['json'] = payload
    response = getattr(client, method)(path, **options)
    assert response.status_code == 422, response.text
    assert response.json()['detail'] == MISSING
    db.expire_all()
    assert snapshot(db) == before


@pytest.mark.parametrize('source', ['query', 'form', 'json'])
def test_delete_uses_explicit_period_from_each_supported_source(client, db, sample, two_periods, source):
    from app.models import Activity
    period, other = two_periods
    activity_id = sample['activity'].id
    options = {'params': {'period_id': period.id}} if source == 'query' else {
        'data' if source == 'form' else 'json': {'period_id': period.id}}
    response = client.request('DELETE', f'/api/activities/{activity_id}', **options)
    assert response.status_code == 200, response.text
    assert response.json()['period_id'] == period.id
    db.expire_all()
    assert db.get(Activity, activity_id) is None
    assert not db.scalar(select(Activity.id).where(Activity.period_id == other.id))
