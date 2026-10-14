"""CIV-012: role boundaries on real, disposable PostgreSQL; no auth overrides."""
import base64
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app import main
from app.db_privileges import assert_runtime_restricted, audit_engine
from app.models import AuditLog, ImportBatch, Indicator, LoginAttempt, Publication, Submission, SubmissionEvent
from app.security import hash_password
from tests.conftest import sample as sample_fixture
from tests.test_word_import import word_document

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.postgres
ROLE_SQL = (ROOT / 'ops/db_roles.sql').read_text()


def apply_roles(engine):
    with engine.connect() as connection:
        connection.execution_options(no_parameters=True).exec_driver_sql(ROLE_SQL)


@pytest.fixture
def roles_db(request):
    url = os.getenv('CIVENSA_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('Disposable PostgreSQL test database not configured')
    # A separate database avoids public-schema/global-default changes in the
    # suite's other scenarios. The configured test administrator needs CREATEDB/CREATEROLE.
    admin = create_engine(url, isolation_level='AUTOCOMMIT', hide_parameters=True)
    name = 'civ012_' + uuid4().hex
    database = None
    engines = []
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE {name}')
    try:
        target = make_url(url).set(database=name)
        database = create_engine(target, isolation_level='AUTOCOMMIT', hide_parameters=True)
        apply_roles(database)
        apply_roles(database)
        credential = secrets.token_urlsafe(32)
        # Ephemeral credentials only, sent directly to the disposable server.
        with database.connect() as connection:
            cursor = connection.connection.driver_connection.cursor()
            for role in ('civensa_owner', 'civensa_app'):
                cursor.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role), sql.Literal(credential)))
            cursor.close()
        owner_url = target.set(username='civensa_owner', password=credential)
        app_url = target.set(username='civensa_app', password=credential)
        owner = create_engine(owner_url, hide_parameters=True)
        runtime = create_engine(app_url, hide_parameters=True)
        engines.extend((owner, runtime))
        result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', getattr(request, 'param', 'head')],
                                cwd=ROOT, env={**os.environ,
                                    'DATABASE_URL': app_url.render_as_string(hide_password=False),
                                    'MIGRATION_DATABASE_URL': owner_url.render_as_string(hide_password=False)},
                                capture_output=True, text=True)
        assert result.returncode == 0, 'Owner CLI migration failed (connection details suppressed)'
        yield SimpleNamespace(admin=database, owner=owner, runtime=runtime,
                              owner_url=owner_url, app_url=app_url)
    finally:
        for engine in engines:
            engine.dispose()
        if database is not None:
            database.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE {name} WITH (FORCE)')
        admin.dispose()


def configure_runtime(monkeypatch, db):
    monkeypatch.setenv('DATABASE_URL', db.app_url.render_as_string(hide_password=False))
    monkeypatch.setenv('MIGRATION_DATABASE_URL', db.owner_url.render_as_string(hide_password=False))
    monkeypatch.setenv('CIVENSA_ENV', 'production')
    monkeypatch.setenv('SESSION_SECRET', secrets.token_urlsafe(40))
    monkeypatch.setenv('COOKIE_SECURE', '1')
    monkeypatch.setattr(main, 'engine', db.runtime)
    factory = sessionmaker(bind=db.runtime, expire_on_commit=False)
    monkeypatch.setattr(main, 'SessionLocal', factory)
    # get_db is the real application generator and resolves its module's factory.
    monkeypatch.setattr('app.db.SessionLocal', factory)
    assert not main.app.dependency_overrides


def denied(engine, statement, state='42501'):
    with pytest.raises(DBAPIError) as error:
        with engine.begin() as connection:
            connection.exec_driver_sql(statement)
    assert error.value.orig.sqlstate == state
    return str(error.value.orig)


def test_role_sql_defaults_idempotence_and_read_only_audit(roles_db):
    db = roles_db
    snapshot = audit_engine(db.runtime)
    assert snapshot['read_only'] == 'on'
    assert snapshot['role'] == snapshot['session_role'] == 'civensa_app'
    assert snapshot['unsafe_runtime_privileges'] == []
    assert snapshot['memberships'] == []
    assert snapshot['database']['connect'] is True
    assert snapshot['database']['create'] is snapshot['database']['temporary'] is False
    assert {r['owner'] for r in snapshot['relations']} == {'civensa_owner'}
    assert snapshot['schemas'] == [dict(name='public', owner='civensa_owner', usage=True, create=False)]
    assert all(not snapshot['roles'][0][flag] for flag in ('superuser', 'createdb', 'createrole', 'replication', 'bypassrls', 'inherit'))
    for relation in snapshot['relations']:
        expected = {'SELECT', 'INSERT', 'UPDATE', 'DELETE'}
        if relation['kind'] == 'S':
            expected = {'USAGE', 'SELECT'}
        elif relation['name'] == 'alembic_version':
            expected = {'SELECT'}
        assert set(relation['grants']) == expected
    denied(db.runtime, "UPDATE alembic_version SET version_num = '290ef7e62102'")
    denied(db.runtime, 'DELETE FROM alembic_version')
    apply_roles(db.admin)
    apply_roles(db.admin)
    assert audit_engine(db.runtime) == snapshot
    # Reapplying also repairs privilege drift on existing roles and objects.
    with db.admin.connect() as connection:
        connection.exec_driver_sql('GRANT civensa_owner TO civensa_app WITH INHERIT FALSE')
        connection.exec_driver_sql('ALTER ROLE civensa_app CREATEDB CREATEROLE REPLICATION BYPASSRLS')
        connection.exec_driver_sql('GRANT CREATE ON SCHEMA public TO PUBLIC')
        connection.exec_driver_sql('GRANT TRUNCATE ON publications TO PUBLIC')
        connection.exec_driver_sql('GRANT UPDATE ON ALL SEQUENCES IN SCHEMA public TO civensa_app')
        connection.exec_driver_sql('GRANT SET ON PARAMETER session_replication_role TO civensa_app')
    assert audit_engine(db.runtime)['unsafe_runtime_privileges']
    apply_roles(db.admin)
    assert audit_engine(db.runtime) == snapshot
    # Future objects created by the migration role receive the same privileges.
    with db.owner.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE public.future_probe (id serial PRIMARY KEY, value text)')
        connection.exec_driver_sql("CREATE FUNCTION public.future_value() RETURNS integer LANGUAGE sql AS 'SELECT 12'")
    with db.runtime.begin() as connection:
        assert connection.exec_driver_sql("INSERT INTO future_probe(value) VALUES ('ok') RETURNING id").scalar() == 1
        connection.exec_driver_sql("UPDATE future_probe SET value = 'changed'")
        assert connection.exec_driver_sql('SELECT future_value()').scalar() == 12
        connection.exec_driver_sql('DELETE FROM future_probe')
    denied(db.runtime, 'TRUNCATE future_probe')
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(db.runtime, 'before_cursor_execute', record)
    try:
        audit_engine(db.runtime)
    finally:
        event.remove(db.runtime, 'before_cursor_execute', record)
    assert all(s.lstrip().split()[0] in {'SELECT', 'WITH', 'SET'} for s in statements)
    assert statements[0] == 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'
    result = subprocess.run([sys.executable, 'tools/db_privilege_audit.py', '--url-env', 'AUDIT_TEST_URL'],
                            cwd=ROOT, env={**os.environ, 'AUDIT_TEST_URL': db.app_url.render_as_string(hide_password=False)},
                            capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report['role'] == 'civensa_app' and report['unsafe_runtime_privileges'] == []
    assert db.app_url.password not in result.stdout + result.stderr
    assert not result.stderr
    # Optional local evidence path, never required by CI.
    evidence = os.getenv('CIVENSA_TEST_PRIVILEGE_EVIDENCE')
    if evidence:
        Path(evidence).write_text(result.stdout)


@pytest.mark.parametrize('roles_db', ['f2b7c4d91e08'], indirect=True)
def test_production_lifespan_migrates_as_owner_and_requests_use_app(roles_db, monkeypatch):
    db = roles_db
    assert not inspect(db.runtime).has_table('login_attempts')
    configure_runtime(monkeypatch, db)
    with TestClient(main.app):
        assert inspect(db.runtime).has_table('login_attempts')
        with db.runtime.connect() as connection:
            assert connection.exec_driver_sql('SELECT version_num FROM alembic_version').scalar() == main.migration_head()
    assert {r['owner'] for r in audit_engine(db.runtime)['relations']} == {'civensa_owner'}


@pytest.mark.parametrize('misconfiguration', [
    'owner', 'superuser', 'schema_create', 'public_create', 'database_create', 'temporary',
    'truncate', 'table_owner', 'membership', 'indirect_membership', 'security_definer', 'replication_setting',
    'schema_owner', 'type_owner', 'server_files',
])
def test_startup_guard_fails_before_migration(roles_db, monkeypatch, caplog, misconfiguration):
    db = roles_db
    configure_runtime(monkeypatch, db)
    statements = {
        'schema_create': 'GRANT CREATE ON SCHEMA public TO civensa_app',
        'public_create': 'GRANT CREATE ON SCHEMA public TO PUBLIC',
        'database_create': f'GRANT CREATE ON DATABASE {db.app_url.database} TO civensa_app',
        'temporary': f'GRANT TEMPORARY ON DATABASE {db.app_url.database} TO civensa_app',
        'truncate': 'GRANT TRUNCATE ON publications TO civensa_app',
        'table_owner': 'ALTER TABLE login_attempts OWNER TO civensa_app',
        'membership': 'GRANT civensa_owner TO civensa_app WITH INHERIT FALSE',
        'indirect_membership': 'GRANT civensa_owner TO civ012_bridge; GRANT civ012_bridge TO civensa_app WITH INHERIT FALSE',
        'security_definer': "CREATE FUNCTION public.unsafe_probe() RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
        'replication_setting': 'GRANT SET ON PARAMETER session_replication_role TO civensa_app',
        'schema_owner': 'CREATE SCHEMA pgx AUTHORIZATION civensa_app',
        'type_owner': "CREATE TYPE public.guard_probe AS ENUM ('a'); ALTER TYPE public.guard_probe OWNER TO civensa_app",
        'server_files': 'GRANT pg_write_server_files TO civensa_app',
    }
    try:
        with db.admin.connect() as connection:
            if misconfiguration == 'indirect_membership':
                connection.exec_driver_sql('CREATE ROLE civ012_bridge')
            if misconfiguration in statements:
                connection.exec_driver_sql(statements[misconfiguration])
        if misconfiguration in {'owner', 'superuser'}:
            monkeypatch.setattr(main, 'engine', db.owner if misconfiguration == 'owner' else db.admin)
        migrations = []
        monkeypatch.setattr(main.alembic_command, 'upgrade', lambda *args: migrations.append(args))
        with pytest.raises(RuntimeError, match='MIGRATION_DATABASE_URL.*DATABASE_URL'):
            with TestClient(main.app):
                pass
        assert not migrations
        assert 'DATABASE_URL' in caplog.text
        assert db.app_url.password not in caplog.text
    finally:
        with db.admin.connect() as connection:
            connection.exec_driver_sql('REVOKE civensa_owner FROM civensa_app')
            connection.exec_driver_sql('REVOKE pg_write_server_files FROM civensa_app')
            connection.exec_driver_sql('REVOKE SET ON PARAMETER session_replication_role FROM civensa_app')
            if misconfiguration == 'indirect_membership':
                connection.exec_driver_sql('DROP ROLE civ012_bridge')


def test_restricted_http_flows_and_immutable_history(roles_db, monkeypatch):
    db = roles_db
    configure_runtime(monkeypatch, db)
    credential = secrets.token_urlsafe(24)
    with Session(db.runtime, expire_on_commit=False) as session:
        sample = sample_fixture.__wrapped__(session)
        for key in ('user', 'strategy'):
            sample[key].password_hash = hash_password(credential)
        session.add(LoginAttempt(email_key='expired', ip_key='expired', failed_at=datetime.now(UTC) - timedelta(days=2)))
        session.commit()
        did, pid, iid = sample['department'].id, sample['period'].id, sample['indicator'].id
    seen_roles = set()
    def verify_role(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('SET TRANSACTION'):
            return  # Isolation level must be set before the first SELECT.
        cursor.execute('SELECT current_user, session_user')
        seen_roles.add(cursor.fetchone())
    event.listen(db.runtime, 'before_cursor_execute', verify_role)
    try:
        with TestClient(main.app, follow_redirects=False) as directorate, TestClient(main.app, follow_redirects=False) as strategy:
            def login(client, email):
                assert client.post('/login', data={'email': email, 'password': credential}).status_code == 303
                # Read the token issued by the real signed session (no forged session).
                token = json.loads(base64.b64decode(client.cookies['session'].split('.')[0]))['csrf_token']
                client.headers['X-CSRF-Token'] = token
            for _ in range(5):
                response = directorate.post('/login', data={'email': sample['user'].email, 'password': 'wrong'})
                assert response.status_code == 400
            assert main.login_throttling.LOCK_MESSAGE in response.text
            assert directorate.post('/login', data={'email': sample['user'].email, 'password': credential}).status_code == 400
            with Session(db.runtime) as session:
                assert session.scalar(select(LoginAttempt).where(LoginAttempt.email_key == 'expired')) is None
                assert session.scalar(select(AuditLog).where(AuditLog.action == 'login_throttle_lock')) is not None
                # Advance persisted failures past their window; next real login cleans them.
                session.execute(text("UPDATE login_attempts SET failed_at = now() - interval '2 days', email_locked_until = now() - interval '1 day'"))
                session.commit()
            assert directorate.post('/login', data={'email': sample['user'].email, 'password': 'wrong'}).status_code == 400
            login(directorate, sample['user'].email)
            login(strategy, sample['strategy'].email)
            with Session(db.runtime) as session:
                assert session.scalars(select(LoginAttempt.email_cleared)).all() == [True]
            assert directorate.get(f'/department/{did}').status_code == 200
            assert directorate.post(f'/api/indicators/{iid}/save', json={'value_2027_target': '2,5'}).status_code == 200
            assert directorate.post(f'/api/departments/{did}/submit').json() == {'ok': True, 'revision': 1}
            with Session(db.runtime) as session:
                sub_id = session.scalar(select(Submission.id))
            decision = f'/api/submissions/{sub_id}/decision'
            assert strategy.post(decision, json={'decision': 'return', 'note': 'Hedefi düzeltin.'}).status_code == 200
            assert directorate.post(f'/api/indicators/{iid}/save', json={'value_2027_target': '3,5'}).status_code == 200
            assert directorate.post(f'/api/departments/{did}/submit').json() == {'ok': True, 'revision': 2}
            assert strategy.post(decision, json={'decision': 'approve'}).json() == {'ok': True, 'status': 'approved'}
            assert strategy.post('/report-builder/section', data={'period_id': pid, 'title': 'Genel Bilgiler', 'kind': 'text', 'content': 'Onaylı içerik'}).status_code == 303
            response = strategy.post('/report-builder/publish', data={'period_id': pid})
            assert response.status_code == 303, response.text
            with Session(db.runtime) as session:
                publication = session.scalar(select(Publication))
                frozen = publication.snapshot_json.encode()
                publication_id = publication.id
                assert [e.event_type for e in session.scalars(select(SubmissionEvent).order_by(SubmissionEvent.id))] == ['submitted', 'return', 'submitted', 'approve']
            assert strategy.get(f'/publications/{publication_id}.json').content == frozen
            assert hashlib.sha256(frozen).hexdigest() == publication.sha256
            # A different synthetic directorate is imported after publication.
            response = strategy.post(f'/api/periods/{pid}/data-import-preview', files={'file': ('synthetic.docx', word_document(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
            assert response.status_code == 200, response.text
            preview = response.json()
            assert preview['can_apply'] is True
            response = strategy.post(f"/api/import-batches/{preview['batch_id']}/apply")
            assert response.status_code == 200, response.text
            assert response.json()['indicators'] == 1
            with Session(db.runtime) as session:
                assert session.get(ImportBatch, preview['batch_id']).status == 'applied'
                assert session.scalar(select(Indicator).where(Indicator.name == 'Park sayısı')) is not None
    finally:
        event.remove(db.runtime, 'before_cursor_execute', verify_role)
    assert seen_roles == {('civensa_app', 'civensa_app')}
    # Real populated immutable rows, not zero-row UPDATE/DELETE false positives.
    for table, key in [('publications', 'id'), ('indicator_identities', 'indicator_id'),
                       ('indicator_definition_revisions', 'id'), ('publication_indicator_bindings', 'id')]:
        with db.runtime.connect() as connection:
            assert connection.exec_driver_sql(f'SELECT count(*) FROM {table}').scalar() > 0
        assert 'değiştirilemez' in denied(db.runtime, f'UPDATE {table} SET {key} = {key}', 'P0001')
        assert 'değiştirilemez' in denied(db.runtime, f'DELETE FROM {table}', 'P0001')
    # Every immutable trigger in the migrated schema is protected from owner DDL.
    triggers = [t for t in audit_engine(db.runtime)['triggers'] if t['name'].startswith('immutable_')]
    assert len(triggers) >= 20
    for trigger in triggers:
        table, name = trigger['table'], trigger['name']
        denied(db.runtime, f'TRUNCATE {table} CASCADE')
        denied(db.runtime, f'ALTER TABLE {table} DISABLE TRIGGER {name}')
        denied(db.runtime, f'DROP TRIGGER {name} ON {table}')
        denied(db.runtime, f'ALTER TABLE {table} OWNER TO civensa_app')
    denied(db.runtime, 'CREATE TABLE public.forbidden (id integer)')
    denied(db.runtime, 'CREATE TEMP TABLE forbidden (id integer)')
    denied(db.runtime, 'ALTER SCHEMA public OWNER TO civensa_app')
    denied(db.runtime, 'SET ROLE civensa_owner')
    denied(db.runtime, "SET session_replication_role = 'replica'")
    with db.runtime.connect() as connection:
        assert connection.exec_driver_sql('SELECT snapshot_json FROM publications').scalar().encode() == frozen


def test_unset_migration_url_preserves_owner_pilot_startup(roles_db, monkeypatch):
    db = roles_db
    configure_runtime(monkeypatch, db)
    monkeypatch.delenv('MIGRATION_DATABASE_URL')
    monkeypatch.setenv('DATABASE_URL', db.owner_url.render_as_string(hide_password=False))
    monkeypatch.setattr(main, 'engine', db.owner)
    with TestClient(main.app):
        assert inspect(db.owner).has_table('users')


def test_guard_unavailable_database_fails_closed_without_connection_details(monkeypatch, caplog):
    def unavailable(*args):
        raise RuntimeError('sensitive connection details')
    monkeypatch.setattr('app.db_privileges.audit_engine', unavailable)
    with pytest.raises(RuntimeError, match='Yetki denetimi tamamlanamadı') as error:
        assert_runtime_restricted(None)
    assert 'sensitive connection details' not in str(error.value) + caplog.text
    assert 'DATABASE_URL' in caplog.text


def test_audit_failure_does_not_print_supplied_url():
    result = subprocess.run([sys.executable, 'tools/db_privilege_audit.py', '--url-env', 'AUDIT_TEST_URL'],
                            cwd=ROOT, env={**os.environ, 'AUDIT_TEST_URL': 'invalid-sensitive-value'},
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert 'invalid-sensitive-value' not in result.stdout + result.stderr
    assert 'Connection details suppressed' in result.stderr
