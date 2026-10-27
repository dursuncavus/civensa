"""Exercise timeout reports through the same worker/controller path as CI."""

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_signal_timeout_preserves_worker_and_emits_stack_annotation(tmp_path):
    (tmp_path / "pytest.ini").write_text((ROOT / "pytest.ini").read_text())
    (tmp_path / "test_timeout_proof.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "import time\n"
        "import pytest\n"
        "@pytest.fixture\n"
        "def cleanup():\n"
        "    yield\n"
        "    Path('cleanup.pid').write_text(str(os.getpid()))\n"
        "def hanging_operation():\n"
        "    time.sleep(30)\n"
        "@pytest.mark.timeout(1)\n"
        "def test_hang(cleanup, pytestconfig):\n"
        "    assert pytestconfig.getini('timeout') == '300'\n"
        "    assert pytestconfig.getini('timeout_method') == 'signal'\n"
        "    hanging_operation()\n"
        "def test_after_timeout():\n"
        "    assert Path('cleanup.pid').read_text() == str(os.getpid())\n"
        "    Path('surviving.pid').write_text(str(os.getpid()))\n",
        encoding="utf-8",
    )
    report = tmp_path / "failures.json"
    env = dict(os.environ, PYTHONPATH=str(ROOT),
               PYTEST_PLUGINS="ops.ci.pytest_annotations",
               CIVENSA_PYTEST_FAILURES=str(report))
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-n", "1", "--dist", "loadfile",
         "--max-worker-restart=0"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=45,
    )
    output = run.stdout + run.stderr
    assert run.returncode == 1, output
    assert "1 failed, 1 passed" in output, output
    assert (tmp_path / "surviving.pid").exists(), output
    rows = json.loads(report.read_text())
    assert len(rows) == 1, rows
    assert rows[0]["nodeid"] == "test_timeout_proof.py::test_hang"
    assert rows[0]["file"] == "test_timeout_proof.py"
    assert rows[0]["line"] == 11
    emitted = subprocess.run(
        [sys.executable, str(ROOT / "ops/ci/pytest_annotations.py"), str(report)],
        capture_output=True, text=True, check=True, timeout=10,
    )
    assert len(emitted.stdout.splitlines()) == 1
    assert "title=test_timeout_proof.py%3A%3Atest_hang" in emitted.stdout
    assert "Timeout (>1.0s)" in emitted.stdout
    assert "hanging_operation" in emitted.stdout
    assert "test_timeout_proof.py:10" in emitted.stdout
