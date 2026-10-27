"""Real stuck threads must neither hide timeout failures nor prevent exit."""
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest


@pytest.mark.parametrize('stage,limit,message', [
    ('before', 35, 'barrier timed out after 30s'),
    ('after', 65, 'worker 1 did not finish within 60s'),
])
def test_race_helper_bounds_stuck_workers_and_process_exit(stage, limit, message):
    script = textwrap.dedent('''
        from threading import Event
        import pytest
        from tests.race_helpers import run_race

        stage = STAGE
        def healthy(barrier):
            barrier.wait()
            return 'ok'

        def stuck(barrier):
            if stage == 'after':
                barrier.wait()
            Event().wait()  # Intentionally never released, even on failure.

        with pytest.raises(pytest.fail.Exception) as failure:
            run_race('synthetic_stuck_race', [healthy, stuck])
        message = str(failure.value)
        assert 'synthetic_stuck_race' in message, message
        assert EXPECTED in message, message
        if stage == 'before':
            assert '1' in message, message
        # Also exercise successful ordered results and worker error propagation.
        assert run_race('success', [healthy, healthy]) == ['ok', 'ok']
        def error(barrier):
            barrier.wait()
            raise ValueError('worker failure')
        with pytest.raises(ValueError, match='worker failure'):
            run_race('error', [healthy, error])
    ''').replace('STAGE', repr(stage)).replace('EXPECTED', repr(message))
    started = time.monotonic()
    result = subprocess.run([sys.executable, '-c', script],
                            cwd=Path(__file__).resolve().parents[1],
                            capture_output=True, text=True, timeout=limit)
    assert result.returncode == 0, result.stdout + result.stderr
    assert time.monotonic() - started < limit
