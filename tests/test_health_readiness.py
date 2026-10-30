"""Public readiness uses the current schema without exposing connection details."""
import secrets
import socket

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL

from app import main


@pytest.fixture
def health_engine(postgres_templates, monkeypatch):
    with postgres_templates.clone('head') as engine:
        with engine.connect() as connection:
            assert int(connection.exec_driver_sql('SHOW server_version_num').scalar_one()) >= 160000
        monkeypatch.setattr(main, 'engine', engine)
        yield engine


def read_health():
    # Do not enter the lifespan: it would upgrade a deliberately behind schema.
    client = TestClient(main.app)
    try:
        return client.get('/health')
    finally:
        client.close()


def assert_private(response, engine, *sensitive):
    body = response.text
    for value in (engine.url.host, engine.url.username, engine.url.password, *sensitive):
        if value:
            assert value not in body
    assert '://' not in body
    assert set(response.json()) == {
        'status', 'app', 'version', 'environment', 'database', 'ready', 'migration',
    }


@pytest.mark.postgres
@pytest.mark.parametrize('environment', ['qa', 'production'])
def test_migrated_database_is_ready_on_one_connection(health_engine, monkeypatch, environment):
    monkeypatch.setenv('CIVENSA_ENV', environment)
    queries, checkouts = [], []

    def record(connection, cursor, statement, parameters, context, executemany):
        queries.append((connection, statement))

    def checkout(connection, record, proxy):
        checkouts.append(connection)

    event.listen(health_engine, 'before_cursor_execute', record)
    event.listen(health_engine, 'checkout', checkout)
    try:
        response = read_health()
    finally:
        event.remove(health_engine, 'before_cursor_execute', record)
        event.remove(health_engine, 'checkout', checkout)
    assert response.status_code == 200
    payload = response.json()
    assert payload['ready'] is True
    assert payload['status'] == 'ok'
    assert payload['app'] == 'civensa'
    assert payload['version'] == main.APP_VERSION
    assert payload['environment'] == environment
    assert set(payload['database']) == {'backend', 'status', 'latency_ms'}
    assert payload['database']['backend'] == 'postgresql'
    assert payload['database']['status'] == 'ok'
    assert payload['database']['latency_ms'] >= 0
    assert payload['migration'] == {'current': main.migration_head(), 'head': main.migration_head()}
    assert len(checkouts) == 1
    assert len(queries) == 2
    assert queries[0][0] is queries[1][0]
    assert queries[0][1] == 'SELECT 1'
    assert queries[1][1].upper().startswith('SELECT ')
    assert 'alembic_version' in queries[1][1]
    assert_private(response, health_engine)


@pytest.mark.postgres
def test_database_one_revision_behind_is_unready(health_engine):
    scripts = ScriptDirectory.from_config(Config(str(main.BASE_DIR.parent / 'alembic.ini')))
    previous = scripts.get_revision(main.migration_head()).down_revision
    assert isinstance(previous, str)
    with health_engine.begin() as connection:
        connection.exec_driver_sql('UPDATE alembic_version SET version_num = %s', (previous,))
    response = read_health()
    assert response.status_code == 503
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] == 'degraded'
    assert payload['database']['status'] == 'ok'
    assert payload['migration'] == {'current': previous, 'head': main.migration_head()}
    with health_engine.connect() as connection:
        assert connection.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one() == previous
    assert_private(response, health_engine)


@pytest.mark.postgres
@pytest.mark.parametrize('change', [
    'DROP TABLE alembic_version',
    'ALTER TABLE alembic_version RENAME COLUMN version_num TO unreadable_revision',
    'DELETE FROM alembic_version',
])
def test_missing_unreadable_or_empty_revision_is_unready(health_engine, change):
    with health_engine.begin() as connection:
        connection.exec_driver_sql(change)
    response = read_health()
    assert response.status_code == 503
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] == 'degraded'
    assert payload['database']['status'] == 'ok'
    assert payload['migration'] == {'current': None, 'head': main.migration_head()}
    assert_private(response, health_engine, 'unreadable_revision', 'UndefinedTable', 'UndefinedColumn')


def test_unreachable_database_is_unready_without_connection_details(monkeypatch):
    # Reserve a local port without listening; no remote endpoint can be contacted.
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))
        url = URL.create('postgresql+psycopg', username='probe_' + secrets.token_hex(8),
                         password=secrets.token_hex(24), host='127.0.0.1',
                         port=reserved.getsockname()[1], database='disposable_probe')
        engine = create_engine(url, connect_args={'connect_timeout': 1}, hide_parameters=True)
        monkeypatch.setattr(main, 'engine', engine)
        try:
            response = read_health()
            assert response.status_code == 503
            payload = response.json()
            assert payload['ready'] is False
            assert payload['status'] == 'degraded'
            assert payload['database']['backend'] == 'postgresql'
            assert payload['database']['status'] == 'error'
            assert payload['migration'] == {'current': None, 'head': main.migration_head()}
            assert_private(response, engine, 'disposable_probe', 'OperationalError', 'Connection refused')
        finally:
            engine.dispose()
