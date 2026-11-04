"""CIV-176: metadata pages must not transfer publication snapshots."""
from contextlib import contextmanager

from lxml.html import fromstring
import pytest
from sqlalchemy import create_engine, event, text

from app import activity_contract_service as service, main
from app.models import AuditLog, Publication
from tests.test_activity_contract import new_report

pytestmark = pytest.mark.postgres


@contextmanager
def publication_statements(db):
    """Capture result columns too: a database hash may reference the Text column."""
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if cursor.description and 'publications' in statement.lower():
            statements.append((statement, parameters, [column[0] for column in cursor.description]))

    event.listen(db.bind, 'after_cursor_execute', capture)
    try:
        yield statements
    finally:
        event.remove(db.bind, 'after_cursor_execute', capture)


def assert_metadata_only(statements):
    assert statements, 'The request must actually query publication metadata.'
    assert all(not selects_snapshot(columns) for _, _, columns in statements), statements


def selects_snapshot(columns):
    return any(column == 'snapshot_json' or column.endswith('_snapshot_json') for column in columns)


@pytest.fixture
def publications(client, db, sample):
    payload, definitions = service.freeze_program_payload(db, sample['period'].id, sample['strategy'])
    # Over 8 MB of UTF-8, including Turkish, combining characters and emoji.
    payload['metadata_load_probe'] = 'İıŞşĞğÜüÖöÇç e\u0301 🏛\n' * 300_000
    raw = service.canonical(payload)
    assert len(raw.encode('utf-8')) > 8_000_000
    first = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw,
                        sha256=service.digest(raw), created_by=sample['strategy'].id)
    db.add(first)
    db.flush()
    service.attach_publication_definitions(db, first, definitions, sample['strategy'])
    db.commit()
    report = new_report(client, first, sample)
    # Insert a separately tampered publication; immutable stored history is never edited.
    second = Publication(period_id=first.period_id, version=2, snapshot_json=raw + ' ',
                         sha256=first.sha256, created_by=first.created_by)
    db.add(second)
    db.flush()
    for entity_type, publication in [('publication', first), ('publications', second)]:
        db.add(AuditLog(action='publication_freeze', entity_type=entity_type,
                        entity_id=publication.id, user_id=sample['strategy'].id, details=''))
    db.commit()
    result = dict(first_id=first.id, second_id=second.id, report=report,
                  expected_valid={first.id: service.digest(raw) == first.sha256,
                                  second.id: service.digest(raw + ' ') == second.sha256})
    main.app.dependency_overrides[main.require_user] = lambda: sample['strategy']
    # A warm identity map can conceal a missing defer or a template lazy load.
    db.expunge_all()
    return result


@pytest.mark.parametrize('role', ['strategy', 'department'])
def test_index_returns_only_metadata_and_preserves_utf8_integrity(client, db, sample, publications, role):
    main.app.dependency_overrides[main.require_user] = lambda: sample['strategy' if role == 'strategy' else 'user']
    with publication_statements(db) as statements:
        response = client.get('/activity-reports')
    assert response.status_code == 200, response.text
    assert 'Program v1' in response.text
    assert_metadata_only(statements)
    if role == 'strategy':
        actual = {pub['id']: pub['valid'] for pub in response.context['publications']}
        assert actual == publications['expected_valid'] == {
            publications['first_id']: True, publications['second_id']: False}
        options = fromstring(response.text).xpath('//select[@name="publication_id"]/option[@value]')
        disabled = {int(option.get('value')): option.get('disabled') is not None
                    for option in options if option.get('value')}
        assert disabled == {key: not value for key, value in actual.items()}
        integrity_queries = [statement for statement, _, _ in statements if 'sha256(' in statement]
        assert len(integrity_queries) == 1
        assert 'convert_to(' in integrity_queries[0]


@pytest.mark.parametrize('error_form', [False, True])
def test_detail_dropdown_does_not_load_snapshot_or_trigger_template_lazy_load(
        client, db, publications, error_form):
    report = publications['report']
    with publication_statements(db) as statements:
        if error_form:
            response = client.post(
                f"/activity-reports/indicators/{report['indicators'][0]['report_indicator_id']}/actuals",
                data={'expected_revision': '0', 'value': 'okunamayan sayı', 'state': 'verified'})
        else:
            response = client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert response.status_code == (422 if error_form else 200), response.text
    assert 'Program v2' in response.text
    # report_data legitimately reads and verifies the base snapshot once. The
    # dropdown and template must never fetch either snapshot again, even on error.
    content = [(statement, parameters) for statement, parameters, columns in statements
               if selects_snapshot(columns)]
    assert len(content) == 1, statements
    statement, parameters = content[0]
    assert 'publications.id = ' in statement
    assert list(parameters.values()) == [publications['first_id']]
    metadata = [entry for entry in statements if not selects_snapshot(entry[2])]
    assert_metadata_only(metadata)


def test_audit_both_publication_entity_names_use_metadata(client, db, publications):
    with publication_statements(db) as statements:
        response = client.get('/audit')
    assert response.status_code == 200, response.text
    assert '1. sürüm' in response.text and '2. sürüm' in response.text
    assert_metadata_only(statements)
    assert len(statements) == 1, 'Publication audit lookups must remain batched.'


@pytest.fixture
def runtime_probe(db, monkeypatch):
    # Readiness uses a separate connection for technical checks. Point it only
    # at this test's disposable clone and schema, including a local head marker.
    schema = db.bind.get_execution_options()['schema_translate_map'][None]
    db.execute(text(f'CREATE TABLE "{schema}".alembic_version (version_num VARCHAR(64))'))
    db.execute(text(f'INSERT INTO "{schema}".alembic_version VALUES (:head)'),
               {'head': main.migration_head()})
    db.commit()
    engine = create_engine(db.bind.url, connect_args={'options': f'-csearch_path={schema}'})
    monkeypatch.setattr(main, 'engine', engine)
    try:
        yield
    finally:
        engine.dispose()


@pytest.mark.parametrize('path', ['/operations', '/api/release/readiness'])
def test_release_context_pages_load_only_publication_metadata(
        client, db, publications, runtime_probe, path):
    with publication_statements(db) as statements:
        response = client.get(path)
    assert response.status_code == 200, response.text
    assert_metadata_only(statements)


def test_builder_history_still_defers_snapshots(client, db, sample, publications):
    with publication_statements(db) as statements:
        response = client.get(f"/report-builder?period_id={sample['period'].id}")
    assert response.status_code == 200, response.text
    assert 'data-publication-version="2"' in response.text
    assert_metadata_only(statements)
