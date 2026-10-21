"""Migrated PostgreSQL guards and the actual candidate/approval/publication path."""
import json
import os
import subprocess
import sys
import pytest
from fastapi import HTTPException
from sqlalchemy import select, text, func
from sqlalchemy.exc import DBAPIError
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.models import (Publication, ReportIndicator, ActivityEvidenceFile, ActivityEvidenceFreeze,
                        ReportCandidateState, ActualRevision)
from app import activity_contract_service as contract, activity_evidence_service as evidence
from app import report_workflow_service as workflow, package_service as packages, authorization_service as auth
from tests.test_authorization_foundation import foundation_db, people, established, ROOT
from tests.test_package_workflow import act, submit

pytestmark = pytest.mark.postgres
PDF = b'%PDF-1.7\nworkflow evidence\n%%EOF'


def create_actual(db, x):
    payload, definitions = contract.freeze_program_payload(db, x['period'].id, x['strategy'])
    raw = contract.canonical(payload)
    pub = Publication(period_id=x['period'].id, version=1, snapshot_json=raw, sha256=contract.digest(raw), created_by=x['strategy'].id)
    db.add(pub); db.flush(); contract.attach_publication_definitions(db, pub, definitions, x['strategy']); db.commit()
    revision = contract.create_report_revision(db, x['strategy'], pub.id, x['department'].organization_id); db.commit()
    slot = db.scalar(select(ReportIndicator)).id
    actual = contract.save_actual(db, x['user'], slot, 0, '1.75', 'verified',
        [{'title': 'Defter', 'locator': 's1', 'source_revision': 'r1'}], 'Hedef gerçekleşti', {},
        uploads={0: (PDF, 'kaynak.pdf')})
    db.commit()
    return revision, slot, actual


def test_candidate_release_manifest_and_all_ownership_guards(foundation_db, people):
    db, x = foundation_db, people
    established(db, x)
    revision, slot, actual = create_actual(db, x)
    sources = json.loads(actual.evidence_json)
    pkg = packages.create_package(db, x['user'], x['department'].organization_id, x['department'].id, 'activity_report', revision.id)
    db.commit(); submit(db, x, pkg); act(db, x, pkg, 'director_approve'); act(db, x, pkg, 'strategy_approve', 'strategy')
    auth.assign_final_authority(db, x['strategy'], pkg.organization_id, x['director'].id, 'Nihai yetki yazısı'); db.commit()
    candidate = workflow.assemble_candidate(db, x['strategy'], pkg.organization_id, 'activity_report', revision.id, [pkg.id]); db.commit()
    assert workflow.ACTIVITY_REFERENCE_SUCCESSORS is False
    assert json.loads(candidate.payload_json)['entries'][0]['evidence'] == sources
    for stage in ('candidate', 'approved', 'published'):
        if stage == 'approved':
            state = db.get(ReportCandidateState, candidate.id)
            workflow.request_final_review(db, x['strategy'], pkg.organization_id, candidate.id, state.version, candidate.sha256); db.commit()
            workflow.final_decision(db, x['director'], pkg.organization_id, candidate.id, 'final_approve', state.version, candidate.sha256); db.commit()
            frozen = db.scalar(select(ActivityEvidenceFreeze).where(ActivityEvidenceFreeze.report_revision_id == candidate.activity_revision_id))
            assert json.loads(frozen.manifest_json)[0]['sources'] == sources
        if stage == 'published':
            state = db.get(ReportCandidateState, candidate.id)
            workflow.publish(db, x['strategy'], pkg.organization_id, candidate.id, state.version, candidate.sha256); db.commit()
        with pytest.raises(HTTPException) as caught:
            contract.save_actual(db, x['user'], slot, 1, '1.75', 'verified', sources, '', {}, uploads={0: (PDF, 'new.pdf')})
        assert caught.value.status_code == 409 and 'aday/yayın iş akışı' in str(caught.value.detail)
        db.rollback()
        assert evidence.download(db, x['user'], slot, sources[0]['source_id'], 1).file_data == PDF
        db.commit()
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 1
    snapshot = contract.report_data(db, x['strategy'], candidate.activity_revision_id)
    assert snapshot['evidence_manifest'][0]['sources'] == sources


def test_migrated_sql_immutable_files_hashes_manifest_and_safe_downgrade(foundation_db, people):
    db, x = foundation_db, people
    revision, slot, actual = create_actual(db, x)
    evidence.freeze(db, revision.id); db.commit()
    for statement in ("UPDATE activity_evidence_files SET file_data=decode('00','hex')", "UPDATE activity_evidence_files SET sha256='changed'",
        'DELETE FROM activity_evidence_files', "UPDATE activity_evidence_freezes SET manifest_json='[]'", 'DELETE FROM activity_evidence_freezes'):
        with pytest.raises(DBAPIError, match='değiştirilemez'):
            with db.begin_nested(): db.execute(text(statement))
    result = subprocess.run([sys.executable, '-m', 'alembic', 'downgrade', 'c048a1b2c3d4'], cwd=ROOT,
        env={**os.environ, 'DATABASE_URL': db.get_bind().url.render_as_string(hide_password=False)}, capture_output=True, text=True)
    assert result.returncode != 0 and 'Veriyi koruyan' in result.stderr
    db.rollback()
    assert db.scalar(select(ActivityEvidenceFile)).file_data == PDF
    assert len(ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini'))).get_heads()) == 1


def test_empty_migration_roundtrip_and_repeat_upgrade(foundation_db):
    db = foundation_db
    env = {**os.environ, 'DATABASE_URL': db.get_bind().url.render_as_string(hide_password=False)}
    for command, revision in [('downgrade', 'c048a1b2c3d4'), ('upgrade', 'head'), ('upgrade', 'head')]:
        result = subprocess.run([sys.executable, '-m', 'alembic', command, revision], cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
