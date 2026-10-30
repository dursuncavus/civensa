from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest

from ops import release_rehearsal

from ops.release_rehearsal import (
    BACKUP_REQUIRED, RehearsalFailure, assert_local_database, github_json,
    require_fresh_backup, row_losses,
)

NOW = datetime(2026, 10, 19, tzinfo=timezone.utc)


@pytest.fixture
def backup_lookup(tmp_path, monkeypatch):
    branch = 'feature/authorization-workflow-phase5'
    run = {'id': 155, 'name': 'Daily verified database backup',
           'head_branch': branch, 'event': 'schedule',
           'created_at': datetime.now(timezone.utc).isoformat()}
    artifact = {'name': 'civensa-db-backup-test', 'expired': False}
    responses = [{'default_branch': branch}, {'workflow_runs': [run]},
                 {'artifacts': [artifact]}]
    lookup = Mock(side_effect=responses)
    download = Mock()
    target = tmp_path / 'backup'
    monkeypatch.setenv('GITHUB_REPOSITORY', 'example/civensa')
    monkeypatch.setattr(release_rehearsal, 'github_json', lookup)
    monkeypatch.setattr(release_rehearsal, 'run_private', download)
    monkeypatch.setattr(release_rehearsal, 'BACKUP_DIR', target)
    return responses, lookup, download, target


@pytest.mark.parametrize('branch', ['feature/authorization-workflow-phase5', 'main', 'release/a&b#c'])
@pytest.mark.parametrize('event', ['schedule', 'workflow_dispatch'])
def test_download_backup_from_repository_default_branch(backup_lookup, branch, event):
    responses, lookup, download, target = backup_lookup
    responses[0]['default_branch'] = branch
    responses[1]['workflow_runs'][0].update(head_branch=branch, event=event)
    release_rehearsal.download_backup()
    assert lookup.call_args_list[0].args == ('repos/example/civensa',)
    query = urlsplit(lookup.call_args_list[1].args[0])
    assert query.path == 'repos/example/civensa/actions/workflows/db-backup.yml/runs'
    assert parse_qs(query.query) == {'branch': [branch], 'status': ['success'], 'per_page': ['1']}
    assert lookup.call_args_list[2].args == ('repos/example/civensa/actions/runs/155/artifacts',)
    download.assert_called_once_with(
        ['gh', 'run', 'download', '155', '--repo', 'example/civensa',
         '--name', 'civensa-db-backup-test', '--dir', str(target)],
        'Verified backup download failed.')
    assert target.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize('changes', [
    {'head_branch': 'main'}, {'head_branch': 'task/civ-155'},
    {'event': 'pull_request'}, {'event': 'push'}, {'event': None},
    {'name': 'Other workflow'},
    {'created_at': (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()},
])
def test_download_backup_rejects_untrusted_or_stale_run(backup_lookup, changes):
    responses, lookup, download, target = backup_lookup
    responses[1]['workflow_runs'][0].update(changes)
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    assert lookup.call_count == 2
    download.assert_not_called()
    assert not target.exists()


@pytest.mark.parametrize('metadata', [{}, {'default_branch': None}, {'default_branch': ''},
                                      {'default_branch': '  '}, {'default_branch': 155}, None])
def test_download_backup_requires_default_branch(backup_lookup, metadata):
    responses, lookup, download, target = backup_lookup
    responses[0] = metadata
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    lookup.assert_called_once_with('repos/example/civensa')
    download.assert_not_called()
    assert not target.exists()


def test_download_backup_default_branch_lookup_failure(backup_lookup, monkeypatch, capfd):
    _, _, download, target = backup_lookup
    # Exercise the real helper, but never invoke gh or disclose its output.
    monkeypatch.setattr(release_rehearsal, 'github_json', github_json)
    child = Mock(return_value=Mock(returncode=1, stdout=b'private', stderr=b'private'))
    monkeypatch.setattr(release_rehearsal.subprocess, 'run', child)
    with pytest.raises(RehearsalFailure, match='Backup lookup failed; check Actions read permission.'):
        release_rehearsal.download_backup()
    child.assert_called_once_with(['gh', 'api', 'repos/example/civensa'], capture_output=True)
    download.assert_not_called()
    assert not target.exists()
    assert capfd.readouterr() == ('', '')


def test_download_backup_malformed_default_branch_response(backup_lookup, monkeypatch):
    _, _, download, target = backup_lookup
    monkeypatch.setattr(release_rehearsal, 'github_json', github_json)
    child = Mock(return_value=Mock(returncode=0, stdout=b'not json', stderr=b''))
    monkeypatch.setattr(release_rehearsal.subprocess, 'run', child)
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    child.assert_called_once_with(['gh', 'api', 'repos/example/civensa'], capture_output=True)
    download.assert_not_called()
    assert not target.exists()


def test_download_backup_requires_successful_run(backup_lookup):
    responses, _, download, target = backup_lookup
    responses[1]['workflow_runs'] = []
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    download.assert_not_called()
    assert not target.exists()


def test_download_backup_never_falls_back_to_older_run(backup_lookup):
    responses, _, download, target = backup_lookup
    newest = responses[1]['workflow_runs'][0]
    responses[1]['workflow_runs'] = [dict(newest, event='pull_request'), newest]
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    download.assert_not_called()
    assert not target.exists()


@pytest.mark.parametrize('artifacts', [[],
    [{'name': 'civensa-db-backup-test', 'expired': True}],
    [{'name': 'other', 'expired': False}],
    [{'name': 'civensa-db-backup-one', 'expired': False},
     {'name': 'civensa-db-backup-two', 'expired': False}],
])
def test_download_backup_still_requires_one_valid_artifact(backup_lookup, artifacts):
    responses, _, download, target = backup_lookup
    responses[2]['artifacts'] = artifacts
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        release_rehearsal.download_backup()
    download.assert_not_called()
    assert not target.exists()


@pytest.mark.parametrize('timestamp', [None, '', 'invalid', '2026-10-19',
    (NOW - timedelta(hours=48, seconds=1)).isoformat(),
    (NOW + timedelta(seconds=1)).isoformat()])
def test_missing_or_stale_backup(timestamp):
    with pytest.raises(RehearsalFailure, match=BACKUP_REQUIRED):
        require_fresh_backup(timestamp, NOW)


@pytest.mark.parametrize('hours', [0, 24, 48])
def test_fresh_backup(hours):
    require_fresh_backup((NOW - timedelta(hours=hours)).isoformat(), NOW)


def test_row_loss_including_dropped_table():
    assert row_losses({'kept': 3, 'lost': 2, 'dropped': 0},
                      {'kept': 4, 'lost': 1, 'new': 8}, {}) == ['dropped', 'lost']


def test_row_loss_allowlist_requires_reason():
    before, after = {'archive': 2}, {'archive': 0}
    assert row_losses(before, after, {'archive': 'Intentional retention cleanup.'}) == []
    assert row_losses(before, after, {'archive': ' '}) == ['archive']
    assert row_losses(before, after) == ['archive']


@pytest.mark.parametrize('url', [
    'postgresql://user:password@production.example:5432/db',
    'postgresql://localhost.evil:5432/db', 'postgresql:///db',
    'sqlite:///local.db', 'postgresql://127.0.0.1:5433/db',
    'postgresql://localhost:5432/db?host=production.example',
    'postgresql://localhost:5432/db?hostaddr=192.0.2.1',
    'postgresql://localhost:5432/db?service=production',
    'postgresql://localhost:5432/db#fragment',
    'postgresql://localhost:bad/db',
])
def test_refuse_nonlocal_or_overridden_url(url):
    with pytest.raises(RehearsalFailure):
        assert_local_database(url)


@pytest.mark.parametrize('host', ['localhost', '127.0.0.1'])
@pytest.mark.parametrize('scheme', ['postgresql', 'postgresql+psycopg'])
def test_accept_only_local_service(host, scheme):
    assert_local_database(f'{scheme}://user:password@{host}:5432/rehearsal')


def test_child_failure_never_replays_output(capfd):
    import sys
    from ops.release_rehearsal import run_private

    with pytest.raises(RehearsalFailure, match='Safe failure'):
        run_private([sys.executable, '-c',
                     "import sys; print('private-row'); print('private-error', file=sys.stderr); sys.exit(1)"],
                    'Safe failure')
    captured = capfd.readouterr()
    assert captured.out == captured.err == ''


def test_summary_only_counts_and_escaped_names(tmp_path, monkeypatch):
    from ops.release_rehearsal import summary

    target = tmp_path / 'summary.md'
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(target))
    summary('FAIL', {'old|<table>': 5}, {'old|<table>': 4, 'new': 0})
    text = target.read_text()
    assert '| old&#124;&lt;table&gt; | 5 | 4 |' in text
    assert '| new | new | 0 |' in text
    assert 'FAIL' in text
