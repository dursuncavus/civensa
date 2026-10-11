"""S4 on SQLite: reference history is immutable, references are refused and XOR holds; no trigger is lost."""
import os
import sqlite3
import subprocess
import sys
import pytest
from tests.test_authorization_foundation import ROOT


@pytest.fixture
def migrated(tmp_path):
    path = tmp_path / 's4.db'
    run = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT,
                         env={**os.environ, 'DATABASE_URL': f'sqlite:///{path}'}, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    db = sqlite3.connect(path);yield db;db.close()


ROW = {'organization_id': 1, 'activity_report_id': 1, 'reporting_period_id': 1, 'successor_report_revision_id': 1,
       'successor_report_indicator_id': 2, 'predecessor_release_id': 1, 'predecessor_candidate_id': 1,
       'predecessor_report_indicator_id': 1, 'source_release_id': 1, 'source_report_indicator_id': 1, 'source_actual_revision_id': 1,
       'persistent_indicator_id': 'x', 'definition_revision_id': 1, 'content_sha256': 'a' * 64, 'provenance_json': '{}',
       'reference_sha256': 'b' * 64, 'created_by': 1}


def insert_reference(db):
    db.execute(f"INSERT INTO activity_realization_references ({','.join(ROW)}) VALUES ({','.join('?' * len(ROW))})", list(ROW.values()))


def test_sqlite_refuses_references_and_keeps_existing_triggers(migrated):
    with pytest.raises(sqlite3.IntegrityError, match='Activity references require PostgreSQL'):insert_reference(migrated)
    triggers = {name for (name,) in migrated.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    assert {'immutable_activity_realization_references_update', 'immutable_activity_realization_references_delete',
            'activity_reference_guard', 'activity_reference_actual_xor', 'candidate_actual_seal', 'candidate_indicator_seal',
            'immutable_package_decisions_update', 'immutable_package_decisions_delete', 'package_decision_binding',
            'activity_successor_guard'} <= triggers


def test_sqlite_history_immutable_and_xor(migrated):
    db = migrated;db.execute('PRAGMA foreign_keys=OFF')
    # Only to reach the other triggers: drop the refusal inside this throwaway database.
    db.execute('DROP TRIGGER activity_reference_guard');insert_reference(db)
    for statement in ('UPDATE activity_realization_references SET content_sha256=content_sha256', 'DELETE FROM activity_realization_references'):
        with pytest.raises(sqlite3.IntegrityError, match='Immutable activity reference history'):db.execute(statement)
    with pytest.raises(sqlite3.IntegrityError, match='Report indicator is realized by a reference'):
        db.execute("INSERT INTO actual_revisions (report_indicator_id,revision,raw_text,state,evidence_json,explanation,deviation_json,created_by) "
                   "VALUES (2,1,'','missing','[]','','{}',1)")
