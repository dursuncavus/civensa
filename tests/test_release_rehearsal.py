from datetime import datetime, timedelta, timezone

import pytest

from ops.release_rehearsal import (
    BACKUP_REQUIRED, RehearsalFailure, assert_local_database,
    require_fresh_backup, row_losses,
)

NOW = datetime(2026, 10, 19, tzinfo=timezone.utc)


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
