from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from ops import preprint_rehearsal
from scripts import first_load_live as live


REFUSAL = (
    'Kaynak yalnız varsayılan daldaki (schedule veya elle başlatılan) yeşil '
    'Daily verified database backup çalışması olabilir.'
)


@pytest.fixture
def backup_lookup(tmp_path, monkeypatch):
    branch = 'feature/authorization-workflow-phase5'
    run = {
        'id': 155,
        'name': 'Daily verified database backup',
        'head_branch': branch,
        'event': 'schedule',
        'status': 'completed',
        'conclusion': 'success',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    artifact = {'id': 1, 'name': 'civensa-db-backup-test', 'expired': False}
    lookup = Mock(side_effect=[{'default_branch': branch}, run, {'artifacts': [artifact]}])
    monkeypatch.setenv('GITHUB_REPOSITORY', 'example/civensa')
    monkeypatch.setattr(preprint_rehearsal, 'github_json', lookup)
    monkeypatch.setattr(preprint_rehearsal, 'run_private', Mock())
    monkeypatch.setattr(preprint_rehearsal, 'decrypt_backup', lambda *_: tmp_path / 'backup.dump')
    monkeypatch.setattr(preprint_rehearsal, 'BACKUP_DIR', tmp_path / 'backup')
    return branch, run, lookup


@pytest.mark.parametrize('event', ['schedule', 'workflow_dispatch'])
def test_download_verified_run_accepts_default_branch_schedule_or_dispatch(backup_lookup, event):
    branch, run, lookup = backup_lookup
    run['event'] = event

    dump, metadata = preprint_rehearsal.download_verified_run(155)

    assert dump.name == 'backup.dump'
    assert metadata == {'backup_run_id': 155, 'artifact_id': 1}
    assert lookup.call_args_list[0].args == ('repos/example/civensa',)
    assert lookup.call_args_list[1].args == ('repos/example/civensa/actions/runs/155',)


@pytest.mark.parametrize('changes', [
    {'head_branch': 'main'},
    {'head_branch': 'task/other'},
    {'event': 'pull_request'},
    {'event': 'push'},
])
def test_download_verified_run_rejects_other_branch_or_event(backup_lookup, changes):
    _, run, lookup = backup_lookup
    run.update(changes)

    with pytest.raises(live.Refusal) as exc:
        preprint_rehearsal.download_verified_run(155)

    assert str(exc.value) == REFUSAL
    assert lookup.call_count == 2
    preprint_rehearsal.run_private.assert_not_called()


@pytest.mark.parametrize('metadata', [
    {},
    None,
    [],
    {'default_branch': None},
    {'default_branch': ''},
    {'default_branch': '  '},
    {'default_branch': 155},
])
def test_download_verified_run_requires_well_formed_default_branch(backup_lookup, metadata):
    _, _, lookup = backup_lookup
    lookup.side_effect = [metadata]

    with pytest.raises(live.Refusal) as exc:
        preprint_rehearsal.download_verified_run(155)

    assert str(exc.value) == REFUSAL
    lookup.assert_called_once_with('repos/example/civensa')
    preprint_rehearsal.run_private.assert_not_called()


def test_download_verified_run_fails_closed_when_default_branch_lookup_fails(backup_lookup):
    _, _, lookup = backup_lookup
    lookup.side_effect = RuntimeError('private lookup failure')

    with pytest.raises(live.Refusal) as exc:
        preprint_rehearsal.download_verified_run(155)

    assert str(exc.value) == REFUSAL
    lookup.assert_called_once_with('repos/example/civensa')
    preprint_rehearsal.run_private.assert_not_called()
