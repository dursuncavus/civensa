"""Collect xdist controller reports, then emit bounded GitHub error annotations.

Load with PYTEST_PLUGINS=ops.ci.pytest_annotations. Run this file after pytest
to publish the JSON report without parsing terminal output or adding dependencies.
"""

import argparse
import json
import os
from pathlib import Path
import sys


MAX_ANNOTATIONS = 50
MESSAGE_LINES = 10


def escape(value, *, property=False):
    value = str(value).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if property:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def annotation(record):
    return (
        f"::error file={escape(record['file'], property=True)},"
        f"line={int(record['line'])},"
        f"title={escape(record['nodeid'], property=True)}::"
        f"{escape(record['nodeid'] + chr(10) + record['message'])}"
    )


def emit(records, stream, batch=None):
    # Keep the summary inside GitHub's 50-annotation budget too.
    total = len(records)
    limit = MAX_ANNOTATIONS if total <= MAX_ANNOTATIONS else MAX_ANNOTATIONS - 1
    commands = []
    if total > MAX_ANNOTATIONS:
        commands.append(
            f"::error title=Pytest failure summary::{total} failing tests in this shard; "
            f"showing {limit}, omitted {total - limit}."
        )
    commands.extend(annotation(record) for record in records[:limit])
    # The runner records only 10 errors per step. Separate workflow steps publish
    # each batch; one step printing 50 commands would silently lose annotations.
    if batch is not None:
        commands = commands[batch * 10:(batch + 1) * 10]
    for command in commands:
        print(command, file=stream)


class FailureReports:
    def __init__(self, path):
        self.path = Path(path)
        self.failures = {}

    def pytest_runtest_logreport(self, report):
        if not report.failed:
            return
        nodeid = report.nodeid
        location = report.location
        crash = getattr(report.longrepr, "reprcrash", None)
        message = getattr(crash, "message", None) or report.longreprtext
        excerpt = "\n".join(str(message).splitlines()[:MESSAGE_LINES])[:8000]
        if "Timeout (>" in str(message) and "from pytest-timeout" in str(message):
            # The signal method produces a normal failed TestReport. Preserve
            # its interrupted call stack too; reprcrash alone only says timeout.
            excerpt = (str(message) + "\n" + report.longreprtext)[:8000]
        detail = f"{report.when}: {excerpt}"
        if nodeid in self.failures:
            # A failing call and teardown belong to the same failing test.
            self.failures[nodeid]["message"] += "\n" + detail
        else:
            self.failures[nodeid] = {
                "nodeid": nodeid,
                "file": location[0],
                "line": max(1, location[1] + 1),  # pytest uses zero-based lines
                "message": detail,
            }

    def pytest_sessionfinish(self, session, exitstatus):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(sorted(self.failures.values(), key=lambda row: row["nodeid"])),
            encoding="utf-8",
        )
        temporary.replace(self.path)


def pytest_configure(config):
    path = os.environ.get("CIVENSA_PYTEST_FAILURES")
    # Workers serialize TestReports to the controller, which sees both call and
    # fixture failures exactly once. Workers must not race to write this file.
    if path and not hasattr(config, "workerinput"):
        config.pluginmanager.register(FailureReports(path), "civensa-failure-reports")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--batch", type=int, choices=range(5))
    args = parser.parse_args()
    path = args.report
    if not path.exists():
        if args.batch in (None, 0):
            print("::warning title=Pytest annotations::No test report; pytest may not have started or completed.")
        return
    emit(json.loads(path.read_text(encoding="utf-8")), sys.stdout, batch=args.batch)


if __name__ == "__main__":
    main()
