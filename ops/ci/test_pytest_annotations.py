"""Dependency-free unit tests; optional real pytest/xdist integration proof."""

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from actionlint_annotations import main as lint_main
from pytest_annotations import FailureReports, annotation, emit, escape, pytest_configure


ROOT = Path(__file__).resolve().parents[2]


def report(nodeid="tests/test_example.py::test_case[param]", when="call", failed=True):
    return SimpleNamespace(
        nodeid=nodeid, when=when, failed=failed,
        location=("tests/test_example.py", 6, "test_case[param]"),
        longrepr=SimpleNamespace(reprcrash=SimpleNamespace(
            message="AssertionError: expected 1, got 2\n" + "\n".join(map(str, range(20)))
        )),
        longreprtext="Full traceback",
    )


class AnnotationTests(unittest.TestCase):
    def test_location_nodeid_message_and_unique_test(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shard.json"
            plugin = FailureReports(path)
            plugin.pytest_runtest_logreport(report(failed=False))
            self.assertFalse(plugin.failures)
            plugin.pytest_runtest_logreport(report())
            plugin.pytest_runtest_logreport(report(when="teardown"))
            plugin.pytest_sessionfinish(None, 1)
            rows = json.loads(path.read_text())
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["line"], 7)
            output = annotation(rows[0])
            self.assertIn("file=tests/test_example.py,line=7", output)
            self.assertIn("test_case[param]", output)
            self.assertIn("call: AssertionError: expected 1, got 2", output)
            self.assertIn("teardown:", output)
            self.assertNotIn("%0A9%0A", output)

    def test_string_longrepr_fallback(self):
        plugin = FailureReports("unused")
        failure = report(when="setup")
        failure.longrepr = "worker failure"
        plugin.pytest_runtest_logreport(failure)
        self.assertEqual(next(iter(plugin.failures.values()))["message"], "setup: Full traceback")

    def test_workflow_command_injection_is_escaped(self):
        self.assertEqual(escape("100%\r\n::error::bad"), "100%25%0D%0A::error::bad")
        row = {"nodeid": "a,b:\n::error::injected", "file": "a,b:\r\n.py",
               "line": 1, "message": "bad\n::error::injected"}
        result = annotation(row)
        self.assertEqual(len(result.splitlines()), 1)
        self.assertIn("file=a%2Cb%3A%0D%0A.py", result)
        self.assertIn("title=a%2Cb%3A%0A", result)

    def test_cap_includes_summary_and_exact_total(self):
        row = {"nodeid": "test", "file": "test.py", "line": 1, "message": "failure"}
        for total, expected, summary in [(0, 0, False), (50, 50, False), (63, 50, True)]:
            with self.subTest(total=total):
                output = io.StringIO()
                emit([row] * total, output)
                lines = output.getvalue().splitlines()
                self.assertEqual(len(lines), expected)
                self.assertEqual("summary" in output.getvalue(), summary)
                if summary:
                    self.assertIn("63 failing tests", lines[0])
                    self.assertIn("omitted 14", lines[0])

    def test_batches_preserve_every_annotation_with_ten_per_step(self):
        records = [{"nodeid": f"test_{i}", "file": "test.py", "line": i + 1,
                    "message": "failure"} for i in range(63)]
        full = io.StringIO()
        emit(records, full)
        batches = []
        for batch in range(5):
            output = io.StringIO()
            emit(records, output, batch=batch)
            lines = output.getvalue().splitlines()
            self.assertEqual(len(lines), 10)
            batches.extend(lines)
        self.assertEqual(batches, full.getvalue().splitlines())
        self.assertIn("63 failing tests", batches[0])

    def test_workers_do_not_register_writer(self):
        manager = SimpleNamespace(register=lambda *args: self.fail("Worker registered a writer"))
        worker = SimpleNamespace(workerinput={}, pluginmanager=manager)
        with patch.dict(os.environ, {"CIVENSA_PYTEST_FAILURES": "unused"}):
            pytest_configure(worker)

    def test_actionlint_diagnostics_become_escaped_warnings(self):
        result = SimpleNamespace(returncode=1, stderr="", stdout=json.dumps([{
            "filepath": ".github/workflows/a,b.yml", "line": 12, "column": 4,
            "message": "unknown context\n::error::injected",
        }]))
        output = io.StringIO()
        with patch("actionlint_annotations.subprocess.run", return_value=result), \
             patch.object(sys, "argv", ["helper", "actionlint"]), redirect_stdout(output):
            self.assertEqual(lint_main(), 1)
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertIn("::warning file=.github/workflows/a%2Cb.yml,line=12,col=4", output.getvalue())
        self.assertIn("unknown context%0A::error::injected", output.getvalue())

    def test_actionlint_execution_failure_still_warns(self):
        result = SimpleNamespace(returncode=2, stderr="tool failure\n", stdout="invalid JSON")
        output = io.StringIO()
        with patch("actionlint_annotations.subprocess.run", return_value=result), \
             patch.object(sys, "argv", ["helper", "actionlint"]), redirect_stdout(output):
            self.assertEqual(lint_main(), 2)
        self.assertIn("Could not parse actionlint diagnostics", output.getvalue())
        self.assertIn("tool failure%0A", output.getvalue())

    @unittest.skipUnless(importlib.util.find_spec("xdist"), "optional local pytest-xdist proof")
    def test_real_xdist_reports_from_multiple_workers_and_shards(self):
        # Isolated from application fixtures/DBs. Exercise real serialized
        # TestReports, parametrized IDs, assertion failures and fixture errors.
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "test_proof.py").write_text(
                "import pytest\n"
                "@pytest.mark.parametrize('i', range(8))\n"
                "def test_assertion(i):\n"
                "    assert i == -1, 'CIV-089 assertion proof'\n"
                "@pytest.fixture\n"
                "def broken():\n"
                "    raise RuntimeError('CIV-089 setup proof')\n"
                "def test_setup(broken): pass\n"
                "def test_pass(): pass\n",
                encoding="utf-8",
            )
            (directory / "test_other_worker.py").write_text(
                "def test_other_worker():\n"
                "    raise ValueError('CIV-089 second worker proof')\n",
                encoding="utf-8",
            )
            for shard in (0, 1):
                path = directory / f"shard-{shard}.json"
                env = dict(os.environ, PYTHONPATH=str(ROOT),
                           PYTEST_PLUGINS="ops.ci.pytest_annotations",
                           CIVENSA_PYTEST_FAILURES=str(path))
                run = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "-n", "4", "--dist", "loadfile"],
                    cwd=directory, env=env, capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
                rows = json.loads(path.read_text())
                self.assertEqual(len(rows), 10)
                self.assertTrue(any("[7]" in row["nodeid"] for row in rows))
                self.assertTrue(any("setup: RuntimeError: CIV-089 setup proof" in row["message"] for row in rows))
                self.assertTrue(any("CIV-089 assertion proof" in row["message"] for row in rows))
                self.assertEqual({row["file"] for row in rows}, {"test_proof.py", "test_other_worker.py"})
                self.assertEqual({row["line"] for row in rows}, {1, 2, 8})
                emitted = subprocess.run(
                    [sys.executable, str(ROOT / "ops/ci/pytest_annotations.py"), str(path)],
                    capture_output=True, text=True, check=True,
                )
                self.assertEqual(len(emitted.stdout.splitlines()), 10)


if __name__ == "__main__":
    unittest.main()
