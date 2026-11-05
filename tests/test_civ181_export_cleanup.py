"""CIV-181: export presentation stays separate from stored audit/report data."""
import ast
import csv
import io
from pathlib import Path
from urllib.parse import quote

import pytest
from sqlalchemy import select

from app.audit_display import action_label
from app.main import app, require_user
from app.models import AuditLog, DepartmentScope, Submission


pytestmark = pytest.mark.postgres


@pytest.fixture
def strategy_client(client, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    return client


@pytest.mark.parametrize(('details', 'expected'), [
    ('code=name:0123456789abcdef; açıklama=Korundu',
     'code=Kod belirtilmedi; açıklama=Korundu'),
    ('password=name:0123456789abcdef', '[hassas ayrıntı gizlendi]'),
])
def test_audit_csv_cleans_display_without_changing_stored_details(
        strategy_client, db, sample, details, expected):
    row = AuditLog(user_id=sample['strategy'].id, action='catalogue_create',
                   entity_type='official_activity', details=details)
    db.add(row)
    db.commit()

    response = strategy_client.get('/api/audit/export.csv?action=catalogue_create')

    assert response.status_code == 200
    records = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert len(records) == 1
    assert records[0]['Değişiklik'] == expected
    assert 'name:' not in response.text
    db.refresh(row)
    assert row.details == details


@pytest.mark.parametrize('display_name', ['Dönemin Özel Müdürlüğü', ''])
def test_department_word_filename_uses_period_name(
        strategy_client, db, sample, monkeypatch, display_name):
    from app import program_service

    period, department = sample['period'], sample['department']
    scope = db.scalar(select(DepartmentScope).where(
        DepartmentScope.period_id == period.id,
        DepartmentScope.department_id == department.id))
    scope.display_name = display_name
    submission = db.scalar(select(Submission).where(
        Submission.period_id == period.id,
        Submission.department_id == department.id))
    submission.status = 'approved'
    db.commit()
    # Synthetic fixture data need not satisfy unrelated PP readiness checks.
    monkeypatch.setattr(program_service, 'validate_department', lambda *args: ([], []))

    response = strategy_client.get(
        f'/export/department/{department.id}.docx?period_id={period.id}')

    assert response.status_code == 200
    expected = quote(
        f'{period.year}-{display_name or department.name}-performans-raporu.docx')
    assert response.headers['content-disposition'] == f"attachment; filename*=UTF-8''{expected}"
    assert response.content.startswith(b'PK')


def test_approved_book_action_label_is_declared_in_shared_literal():
    app_dir = Path(__file__).parents[1] / 'app'
    tree = ast.parse((app_dir / 'audit_display.py').read_text())
    labels = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'ACTION_LABELS'
                          for target in node.targets))
    expected = 'Onaylı kitaptan yayın oluşturuldu'
    assert ast.literal_eval(labels)['publication_approved_book'] == expected
    assert action_label('publication_approved_book') == expected
    routes = ast.parse((app_dir / 'program_routes.py').read_text())
    assert not any(isinstance(node, ast.Name) and node.id == 'ACTION_LABELS'
                   for node in ast.walk(routes))
