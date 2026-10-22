import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from app.models import ReportingPeriod
from ops.db_storage_report import collect_report, main, read_only_connection


@pytest.mark.postgres
def test_postgres_report_totals_top_five_and_no_content(db):
    engine = db.get_bind()
    schema = engine.get_execution_options()['schema_translate_map'][None]
    relation = f'"{schema}".storage_probe'
    # Include empty and null values; ties must have deterministic ID ordering.
    db.execute(text(f'CREATE TABLE {relation} (id integer PRIMARY KEY, file_data bytea, filename text)'))
    sizes = [0, 2, 8, 8, 32, 64, 128]
    for identifier, size in enumerate(sizes, 1):
        db.execute(text(f'INSERT INTO {relation} VALUES (:id, :data, :filename)'),
                   {'id': identifier, 'data': b'x' * size, 'filename': 'PRIVATE-PERSON.pdf'})
    db.execute(text(f'INSERT INTO {relation} VALUES (8, NULL, :filename)'), {'filename': 'PRIVATE-PERSON.pdf'})
    db.add(ReportingPeriod(id=1, year=2027, status='active'))
    db.flush()
    content = json.dumps({'data': 'c2VjcmV0', 'caption': 'Özel içerik'}, ensure_ascii=False)
    db.execute(text(f'''INSERT INTO "{schema}".report_sections
                       (id, period_id, position, title, kind, content_json)
                       VALUES (1, 1, 1, 'PRIVATE-TITLE', 'image', :content)'''), {'content': content})
    db.commit()
    statements = []

    def record(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, 'before_cursor_execute', record)
    try:
        with read_only_connection(engine) as connection:
            report = collect_report(connection, schema)
            assert connection.scalar(text('SHOW transaction_read_only')) == 'on'
            assert report['database_bytes'] == connection.scalar(text('SELECT pg_database_size(current_database())'))
            table = next(t for t in report['tables'] if t['name'] == 'storage_probe')
            assert table['total_bytes'] == connection.scalar(
                text('SELECT pg_total_relation_size(to_regclass(:relation))'), {'relation': relation})
        assert statements[0] == 'SET TRANSACTION READ ONLY'
    finally:
        event.remove(engine, 'before_cursor_execute', record)
    binary = next(c for c in report['columns'] if c['table'] == 'storage_probe')
    assert (binary['row_count'], binary['value_count'], binary['total_bytes'], binary['max_bytes']) == (8, 7, sum(sizes), 128)
    assert binary['largest_rows'] == [
        {'id': 7, 'bytes': 128}, {'id': 6, 'bytes': 64}, {'id': 5, 'bytes': 32},
        {'id': 3, 'bytes': 8}, {'id': 4, 'bytes': 8},
    ]
    image = next(c for c in report['columns'] if c['table'] == 'report_sections')
    assert image['row_count'] == 1
    assert image['total_bytes'] == image['max_bytes'] == len(content.encode('utf-8'))
    evidence = next(c for c in report['columns'] if c['table'] == 'activity_evidence_files')
    assert (evidence['row_count'], evidence['total_bytes'], evidence['max_bytes'], evidence['largest_rows']) == (0, 0, 0, [])
    assert report['missing_base64_columns'] == []

    # Exercise the standalone script with an explicit disposable database URL.
    env = {**os.environ, 'DATABASE_URL': engine.url.render_as_string(hide_password=False)}
    result = subprocess.run([sys.executable, 'ops/db_storage_report.py', '--schema', schema],
                            cwd=Path(__file__).resolve().parents[1], env=env,
                            capture_output=True, text=True, check=True)
    emitted = json.loads(result.stdout)
    assert emitted['columns'] == report['columns']
    for private in ('PRIVATE-PERSON', 'PRIVATE-TITLE', 'c2VjcmV0', 'Özel içerik'):
        assert private not in result.stdout + result.stderr


@pytest.mark.postgres
def test_read_only_transaction_actually_rejects_writes(db):
    engine = db.get_bind()
    schema = engine.get_execution_options()['schema_translate_map'][None]
    relation = f'"{schema}".write_probe'
    db.execute(text(f'CREATE TABLE {relation} (id integer)'))
    db.commit()
    with pytest.raises(DBAPIError) as caught:
        with read_only_connection(engine) as connection:
            connection.execute(text(f'INSERT INTO {relation} VALUES (1)'))
    assert caught.value.orig.sqlstate == '25006'
    assert db.scalar(text(f'SELECT count(*) FROM {relation}')) == 0


def test_sqlite_refused_without_connecting(monkeypatch, capsys):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    assert main([]) == 1
    assert 'PostgreSQL only' in capsys.readouterr().err


@pytest.mark.parametrize('url', [None, 'invalid secret password',
                                    'postgresql+missing://PRIVATE:SECRET@localhost/private'])
def test_report_errors_never_disclose_connection_details(monkeypatch, capsys, url):
    if url is None:
        monkeypatch.delenv('DATABASE_URL', raising=False)
    else:
        monkeypatch.setenv('DATABASE_URL', url)
    assert main([]) == 1
    output = capsys.readouterr()
    assert output.err and not output.out
    for private in ('PRIVATE', 'SECRET', 'password'):
        assert private not in output.err
