"""CIV-203: dashboard/users lead with a numbered to-do list instead of counters.

The strategy dashboard orders "open personal accounts" before "select activity
sub-programs", hides zero-count items, and shows one line when nothing remains.
/users shows the three bulk-account steps in order and the same empty line.
"""
import re

import pytest

from app.main import app, require_user
from app.models import Department
from app.security import hash_password
from test_activity_sections import login, PASSWORD

pytestmark = pytest.mark.postgres


@pytest.fixture
def strategy_client(client, db, sample):
    client.follow_redirects = False
    app.dependency_overrides.pop(require_user)
    sample['strategy'].password_hash = hash_password(PASSWORD)
    db.commit()
    login(client, sample['strategy'].email)
    return client


def render_dashboard(response, missing_accounts, unresolved_count):
    summary = dict(response.context['progress_summary'])
    summary['missing_accounts'] = missing_accounts
    return response.template.render({
        **response.context,
        'progress_summary': summary,
        'unresolved_count': unresolved_count,
    })


def todo_items(html):
    match = re.search(r'<ol class="dashboard-todo-list">(.*?)</ol>', html, flags=re.S)
    return re.findall(r'<li>(.*?)</li>', match.group(1), flags=re.S) if match else []


def test_dashboard_todo_orders_accounts_before_mapping(strategy_client, sample):
    response = strategy_client.get(f'/dashboard?period_id={sample["period"].id}')
    html = render_dashboard(response, missing_accounts=3, unresolved_count=7)
    items = todo_items(html)
    assert len(items) == 2
    assert '3 müdürlüğe kişisel hesap aç' in items[0]
    assert '/users' in items[0]
    assert '7 faaliyetin alt programını seç' in items[1]
    assert '/activity-mapping' in items[1]


def test_dashboard_todo_hides_zero_count_items(strategy_client, sample):
    response = strategy_client.get(f'/dashboard?period_id={sample["period"].id}')
    # Only the mapping step remains once every account exists.
    html = render_dashboard(response, missing_accounts=0, unresolved_count=5)
    items = todo_items(html)
    assert len(items) == 1
    assert 'faaliyetin alt programını seç' in items[0]
    assert 'müdürlüğe kişisel hesap aç' not in html
    # Only the account step remains once mapping is complete.
    html = render_dashboard(response, missing_accounts=4, unresolved_count=0)
    items = todo_items(html)
    assert len(items) == 1
    assert 'müdürlüğe kişisel hesap aç' in items[0]
    assert 'faaliyetin alt programını seç' not in html


def test_dashboard_todo_all_zero_shows_nothing_left(strategy_client, sample):
    response = strategy_client.get(f'/dashboard?period_id={sample["period"].id}')
    html = render_dashboard(response, missing_accounts=0, unresolved_count=0)
    assert 'Yapılacak iş kalmadı.' in html
    assert '<ol class="dashboard-todo-list">' not in html


def users_todo_items(html):
    match = re.search(r'<section class="users-todo"[^>]*>(.*?)</section>', html, flags=re.S)
    return re.findall(r'<li>(.*?)</li>', match.group(1), flags=re.S) if match else []


def test_users_todo_names_each_missing_department_with_an_open_button(strategy_client, db, sample):
    db.add(Department(organization_id=sample['department'].organization_id, name='Yeni Sentetik Müdürlük'))
    db.commit()
    response = strategy_client.get('/users')
    assert response.status_code == 200
    assert '1 müdürlüğün kişisel hesabı yok.' in response.text
    items = users_todo_items(response.text)
    assert len(items) == 1
    assert 'Yeni Sentetik Müdürlük' in items[0]
    assert 'create-department-user' in items[0] and 'Hesap aç' in items[0]
    # The bulk CSV steps are no longer dressed up as separate to-do items.
    assert 'parola dosyasını teslim et' not in response.text


def test_users_todo_folds_a_long_missing_list(strategy_client, db, sample):
    for n in range(7):
        db.add(Department(organization_id=sample['department'].organization_id, name=f'Sentetik Eksik {n}'))
    db.commit()
    html = strategy_client.get('/users').text
    assert '<details class="users-todo-fold"><summary>7 müdürlüğü göster</summary>' in html
    assert len(users_todo_items(html)) == 7


def test_users_todo_empty_when_no_missing_departments(strategy_client):
    response = strategy_client.get('/users')
    assert response.status_code == 200
    assert 'Yapılacak iş kalmadı.' in response.text
    assert 'users-todo-missing' not in response.text
