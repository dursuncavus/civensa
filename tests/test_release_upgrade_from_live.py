"""CIV-156: rehearse the populated live schema on disposable local PostgreSQL."""
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from psycopg import sql
import pytest
from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from ops.release_rehearsal import row_losses

ROOT = Path(__file__).resolve().parents[1]
LIVE_REVISION = 'c048a1b2c3d4'
NEW_TABLES = {
    'activity_evidence_files', 'activity_evidence_freezes', 'release_confirmations',
    'ar_unit_workflow_events', 'ic_monitoring_periods', 'ic_monitoring_batches',
    'ic_monitoring_period_events', 'ic_monitoring_events', 'ic_monitoring_notes',
    'ic_monitoring_targets', 'ic_monitoring_entries', 'ar_section_table_keys',
    'ar_section_row_keys', 'ar_statement_figure_keys',
}
pytestmark = pytest.mark.postgres


class HealthReadinessMismatch(AssertionError):
    """Only the confirmed health contract defect may be an expected failure."""


@pytest.fixture
def live_database(monkeypatch, isolated_application_startup):
    configured = os.getenv('CIVENSA_TEST_POSTGRES_URL')
    if not configured:
        pytest.skip('Disposable PostgreSQL test database not configured')
    target = make_url(configured)
    # Validate before connecting; libpq query options could override the host.
    assert (target.get_backend_name() == 'postgresql'
            and target.host in {'localhost', '127.0.0.1', '::1'}
            and not target.query), 'CIV-156 requires disposable local PostgreSQL without URL overrides'
    admin = create_engine(target, isolation_level='AUTOCOMMIT', hide_parameters=True)
    name = 'civ156_' + uuid4().hex
    engine = None
    created = False
    try:
        with admin.connect() as connection:
            assert int(connection.exec_driver_sql('SHOW server_version_num').scalar_one()) >= 160000
            connection.exec_driver_sql(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(
                sql.Identifier(name)).as_string())
            created = True
        target = target.set(database=name)
        engine = create_engine(target, hide_parameters=True)
        monkeypatch.setenv('DATABASE_URL', target.render_as_string(hide_password=False))
        monkeypatch.delenv('MIGRATION_DATABASE_URL', raising=False)
        monkeypatch.setenv('DEMO_SEED', '0')
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin.connect() as connection:
                connection.exec_driver_sql(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(
                    sql.Identifier(name)).as_string())
        admin.dispose()


def upgrade(revision):
    result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', revision],
        cwd=ROOT, env=dict(os.environ), capture_output=True, text=True, timeout=180)
    # Child diagnostics may contain a connection URL. Never replay them.
    assert result.returncode == 0, f'Alembic upgrade {revision} failed (details suppressed)'


def seed_live(engine):
    """Core inserts reflected from c048, without current ORM models or defaults."""
    from app.security import hash_password

    metadata = MetaData(schema='public')
    metadata.reflect(engine)
    password = secrets.token_urlsafe(24)
    now = datetime(2026, 10, 1, 12)
    with engine.begin() as connection:
        def insert(table_name, **values):
            return connection.execute(metadata.tables['public.' + table_name].insert().values(
                **values)).inserted_primary_key[0]

        organization = insert('organizations', name='Sentetik Yükseltme Belediyesi')
        departments = [insert('departments', organization_id=organization,
            name=f'Sentetik Yeni Birim {index}', is_active=True) for index in range(1, 5)]
        strategy = insert('users', email='upgrade-strategy@example.invalid',
            full_name='Sentetik Strateji', role='strategy', department_id=None,
            password_hash=hash_password(password), is_active=True, position='staff',
            can_submit=False, must_change_password=False)
        for index, department in enumerate(departments, 1):
            insert('users', email=f'upgrade-department-{index}@example.invalid',
                full_name=f'Sentetik Birim Kullanıcısı {index}', role='department',
                department_id=department, password_hash=hash_password(secrets.token_urlsafe(24)),
                is_active=True, position='staff', can_submit=True, must_change_password=False)

        periods = []
        for year, status in [(2026, 'closed'), (2027, 'active')]:
            period = insert('reporting_periods', year=year, status=status, template_status='ready')
            periods.append(period)
            program = insert('programs', period_id=period, name=f'Sentetik Program {year}')
            subprogram = insert('subprograms', period_id=period, program_id=program,
                name=f'Sentetik Alt Program {year}', rationale='Sentetik gerekçe', goal='Sentetik hedef')
            for index, department in enumerate(departments):
                insert('department_scopes', period_id=period, department_id=department,
                    display_name=f'Sentetik {"Eski" if year == 2026 else "Yeni"} Birim {index + 1}',
                    status='required', reason='Sentetik dönem adı', position=index,
                    budget_code=None if index == 0 else f'{index:02}',
                    active_from=date(year, 1, 1), active_to=None if year == 2027 else date(year, 12, 31))
                card = insert('report_cards', period_id=period, department_id=department,
                    subprogram_id=subprogram, position=index, source_title=f'{year}/{index + 1}',
                    administration='Sentetik İdare', responsible='Sentetik Birim', rationale='Gerekçe',
                    goal='Hedef', explanation='Sentetik açıklama', calculation_method='Sayım',
                    data_source='Sentetik kayıt', footnote='', source_page='1',
                    service_area='Sentetik alan', strategic_link='Sentetik bağlantı')
                indicator = insert('indicators', period_id=period, department_id=department,
                    subprogram_id=subprogram, card_id=card, name='Sentetik gösterge', unit='Adet',
                    explanation='', calculation_method='Sayım', data_source='Sentetik kayıt',
                    status='active', code=f'G{index + 1}', position=index)
                activity = insert('activities', period_id=period, department_id=department,
                    subprogram_id=subprogram, card_id=card, name='Sentetik faaliyet',
                    explanation='Sentetik faaliyet açıklaması', code=f'F{index + 1}',
                    position=index, contract_bound=False)
                for offset, amount, raw in [(0, None, ''), (1, Decimal('0'), '0'),
                                            (2, Decimal('9876543210.23'), '9.876.543.210,23')]:
                    state = 'missing' if amount is None else 'verified'
                    insert('indicator_values', indicator_id=indicator, year=year + offset,
                        value_kind='target', value=None if amount is None else
                            Decimal('0') if offset == 1 else Decimal('1.234567'),
                        raw_text='' if amount is None else '0' if offset == 1 else '1,234567', state=state)
                    insert('activity_cost_values', activity_id=activity, year=year + offset,
                        value_kind='budget' if offset == 0 else 'forecast', funding_type='inside',
                        amount=amount, raw_text=raw, state=state, source_amount=amount, source_raw_text=raw)
                    insert('economic_values', period_id=period, department_id=department,
                        year=year + offset, value_kind='budget' if offset == 0 else 'forecast',
                        category='goods_services', program_group='service', funding_type='inside',
                        amount=amount, raw_text=raw, state=state, issue='',
                        source_card_id=card if offset == 2 else None, source_table_number=0 if offset == 1 else None)
                    insert('department_cost_values', period_id=period, department_id=department,
                        year=year + offset, value_kind='budget' if offset == 0 else 'forecast',
                        category='personnel_sgk', amount=amount, raw_text=raw, state=state)
                submission_status = ('draft', 'submitted', 'approved', 'returned')[index]
                insert('submissions', period_id=period, department_id=department,
                    status=submission_status, revision=index,
                    return_note='Sentetik iade gerekçesi' if submission_status == 'returned' else '',
                    submitted_at=None if submission_status == 'draft' else now,
                    reviewed_at=now if submission_status in {'approved', 'returned'} else None)

        closed, active = periods
        insert('audit_log', user_id=strategy, action='synthetic_upgrade_seed', entity_type='department',
            entity_id=departments[0], details='Yalnız sentetik yükseltme verisi', created_at=now)
        package = insert('directorate_packages', organization_id=organization,
            department_id=departments[0], resource_scope='performance_program', period_id=active,
            report_revision_id=None, source_key=f'period:{active}', state='draft', version=1, current_revision=1)
        package_json = json.dumps({'synthetic': True, 'amount': None, 'zero': '0.00'})
        insert('package_revisions', package_id=package, revision=1, previous_revision_id=None,
            content_json=package_json, sha256=hashlib.sha256(package_json.encode()).hexdigest(),
            created_by=strategy, reason='Sentetik ilk sürüm')
        publication_json = json.dumps({'period': 2026, 'departments': [], 'sections': [],
            'synthetic_values': [None, '0.00', '9876543210.23']})
        insert('publications', period_id=closed, version=1, snapshot_json=publication_json,
            sha256=hashlib.sha256(publication_json.encode()).hexdigest(), template_version='5.0',
            created_by=strategy, created_at=now)

        batch = insert('ic_imports', source_filename='synthetic.xlsx', source_sha256='a' * 64,
            source_json='{"synthetic":true}', created_by=strategy)
        plan = insert('ic_plans', title='Sentetik Uyum Planı', start_year=2027, end_year=2029,
            version_label='v1', approval_date=None, status='draft', source_filename='synthetic.xlsx',
            source_sha256='a' * 64, import_id=batch, supersedes_id=None, created_by=strategy)
        condition = insert('ic_conditions', plan_id=plan, standard_code='KOS1', standard_title='Sentetik standart',
            condition_code='KOS1.1', condition_code_raw='KOS 1.1', text='Sentetik şart',
            current_state_text='Sentetik durum', sort_order=0)
        action = insert('ic_actions', plan_id=plan, condition_id=condition, action_code='KOS1.1.1',
            action_code_raw='KOS.1.1.1', text='Sentetik eylem', output_text='Sentetik çıktı',
            start_raw='2027', due_raw='Sürekli', due_date=None, is_continuous=True, note='', sort_order=0)
        insert('ic_action_parties', action_id=action, role='responsible', department_id=departments[0],
            body_name=None, all_departments=False, raw_name='Sentetik Birim 1', sort_order=0)
        insert('ic_unit_aliases', raw_name='Sentetik Eski Birim 1', department_id=departments[0],
            body_name=None, created_by=strategy)
        # Commit audit comes last: c048 then freezes inserts into this plan.
        insert('ic_import_audits', import_id=batch, plan_id=plan, actor_id=strategy,
            source_sha256='a' * 64, result='commit', report_json='{"synthetic":true}')

        # Populate the c048 content that c086 will backfill with stable keys.
        document = insert('ar_documents', organization_id=organization, period_id=closed,
            department_id=None, scope='idare', definition_version=1, revision=1, created_by=strategy)
        definitions = connection.execute(text("SELECT id FROM ar_section_definitions "
            "WHERE version=1 AND applies_to IN ('idare','both') ORDER BY id")).scalars().all()
        assert definitions
        for position, definition in enumerate(definitions):
            insert('ar_section_contents', document_id=document, definition_id=definition,
                blocks_json=json.dumps([{'type': 'table', 'rows': [['Sentetik'], ['0']]}])
                    if position == 0 else '[]',
                status='draft', reason='', copied_from_id=None, copied_needs_review=False,
                edited_by=strategy, edited_at=now)
        for position, value in enumerate([None, 0, 12500]):
            insert('ar_resource_rows', document_id=document, table_kind='buildings', position=position,
                name=f'Sentetik Kaynak {position}', category='', address='', purpose='', ownership='mülk',
                count=value, area=None if value is None else Decimal(value))
        insert('ar_financial_entries', document_id=document, kind='explanations', position=0,
            payload_json='{"amount":null,"zero":0}')
        insert('ar_financial_statements', document_id=document, name='Sentetik mali tablo',
            period='2026', statement_date='2026-12-31', explanation='Sentetik açıklama',
            figures_json='[{"label":"Sentetik","amount":null},{"label":"Sıfır","amount":0}]',
            filename='', sha256='', file_data=None)
    return departments[0], password


def row_counts(engine):
    with engine.connect() as connection:
        tables = inspect(connection).get_table_names(schema='public')
        return {table: connection.exec_driver_sql(sql.SQL('SELECT count(*) FROM public.{}').format(
            sql.Identifier(table)).as_string()).scalar_one() for table in tables}


def checksums(engine, metadata):
    """Hash every original column, including explicit NULL flags, keyed by PK."""
    result = {}
    with engine.connect() as connection:
        for table in metadata.sorted_tables:
            if table.name == 'alembic_version':
                continue
            assert table.primary_key.columns, f'{table.name} needs a stable row identity'
            result[table.name] = {}
            for row in connection.execute(select(table)).mappings():
                key = tuple(row[column.name] for column in table.primary_key.columns)
                payload = [(column.name, row[column.name] is None, row[column.name]) for column in table.columns]
                encoded = json.dumps(payload, ensure_ascii=False, default=str, separators=(',', ':')).encode()
                result[table.name][key] = hashlib.sha256(encoded).hexdigest()
    return result


def assert_preserved(engine, before_counts, before_values, metadata):
    assert row_losses(before_counts, row_counts(engine), allowlist={}) == []
    after_values = checksums(engine, metadata)
    for table, rows in before_values.items():
        for key, digest in rows.items():
            assert after_values[table].get(key) == digest, f'{table} row {key} changed or disappeared'


def assert_head(engine, head):
    with engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM public.alembic_version')).scalars().all() == [head]


@pytest.mark.xfail(strict=True, raises=HealthReadinessMismatch,
    reason='CIV-156: /health returns status=ok without readiness or Alembic head revision')
def test_populated_live_schema_upgrades_twice_and_serves_app(live_database, monkeypatch):
    engine = live_database
    assert row_counts(engine) == {}
    upgrade(LIVE_REVISION)
    assert_head(engine, LIVE_REVISION)
    department, password = seed_live(engine)
    before_counts = row_counts(engine)
    assert NEW_TABLES.isdisjoint(before_counts)
    metadata = MetaData(schema='public')
    metadata.reflect(engine)
    before_values = checksums(engine, metadata)
    scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    assert len(scripts.get_heads()) == 1
    head = scripts.get_current_head()
    assert head != LIVE_REVISION

    upgrade('head')
    assert_head(engine, head)
    assert_preserved(engine, before_counts, before_values, metadata)
    after_first = row_counts(engine)
    assert NEW_TABLES <= after_first.keys()
    assert after_first['ar_section_table_keys'] == 1
    assert after_first['ar_section_row_keys'] == 2
    assert after_first['ar_statement_figure_keys'] == 2
    head_metadata = MetaData(schema='public')
    head_metadata.reflect(engine)
    first_values = checksums(engine, head_metadata)
    upgrade('head')
    assert_head(engine, head)
    assert row_counts(engine) == after_first
    assert checksums(engine, head_metadata) == first_values
    assert_preserved(engine, before_counts, before_values, metadata)

    from app import main
    monkeypatch.setenv('CIVENSA_ENV', 'production')
    monkeypatch.setenv('SESSION_SECRET', secrets.token_urlsafe(48))
    monkeypatch.setenv('COOKIE_SECURE', '1')
    monkeypatch.setattr(main, 'engine', engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(main, 'SessionLocal', factory)
    monkeypatch.setattr('app.db.SessionLocal', factory)
    assert not main.app.dependency_overrides
    with TestClient(main.app, base_url='https://testserver') as client:
        # Entering the lifespan runs production's real Alembic upgrade again.
        assert_head(engine, head)
        assert row_counts(engine) == after_first
        assert checksums(engine, head_metadata) == first_values
        assert_preserved(engine, before_counts, before_values, metadata)
        health = client.get('/health')
        assert health.status_code == 200
        assert health.json()['database']['backend'] == 'postgresql'
        assert health.json()['database']['status'] == 'ok'
        assert client.get('/login').status_code == 200
        login = client.post('/login', data={'email': 'upgrade-strategy@example.invalid',
            'password': password}, follow_redirects=False)
        assert login.status_code == 303
        for path in ['/dashboard', f'/program/{department}', '/report-builder', '/activity-sections']:
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 200, f'{path} returned {response.status_code}'
        # Login adds audit/throttle rows; all pre-existing rows must still match.
        assert_head(engine, head)
        assert_preserved(engine, before_counts, before_values, metadata)
        # /health currently tests SELECT 1 only. Keep the requested readiness
        # contract visible without hiding migration, value, login or page failures.
        if health.json().get('status') != 'ready' or health.json().get('migration') != head:
            raise HealthReadinessMismatch('/health must report ready and the current Alembic head')
