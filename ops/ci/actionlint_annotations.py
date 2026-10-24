"""Convert actionlint JSON diagnostics to escaped, non-blocking annotations."""

import json
import subprocess
import sys

from pytest_annotations import escape


def main():
    result = subprocess.run(
        [sys.argv[1], "-no-color", "-format", "{{json .}}"],
        text=True, capture_output=True, check=False,
    )
    # Failures other than lint diagnostics must still be visible as warnings.
    try:
        findings = json.loads(result.stdout or "[]")
    except ValueError:
        findings = []
        print("::warning title=actionlint::Could not parse actionlint diagnostics.")
    for finding in (findings or [])[:50]:
        print(
            f"::warning file={escape(finding['filepath'], property=True)},"
            f"line={finding['line']},col={finding['column']},title=actionlint::"
            f"{escape(finding['message'])}"
        )
    if result.stderr:
        print(f"::warning title=actionlint::{escape(result.stderr[:8000])}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
