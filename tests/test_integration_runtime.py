"""Provider-URL compatibility must work in both source and packaged runtimes."""
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_url_uses_installed_driver_in_source_and_bundle(tmp_path, scheme):
    manifest = json.loads((ROOT / "bundle-manifest.json").read_text())
    raw = base64.b64decode("".join((ROOT / part).read_text() for part in manifest["parts"]))
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        archive.extractall(tmp_path)
    for runtime in (ROOT, tmp_path):
        env = {**os.environ, "PYTHONPATH": str(runtime),
               "DATABASE_URL": f"{scheme}://example:example@127.0.0.1:1/disposable",
               "MIGRATION_DATABASE_URL": f"{scheme}://owner:example@127.0.0.1:1/disposable"}
        # Create the engine without connecting; importing psycopg2 would fail here.
        result = subprocess.run(
            [sys.executable, "-c", "from app.db import engine; import os; "
             "assert engine.dialect.driver == 'psycopg'; "
             "assert os.environ['DATABASE_URL'].startswith('postgresql+psycopg://'); "
             "assert os.environ['MIGRATION_DATABASE_URL'].startswith('postgresql+psycopg://'); "
             "assert engine.url.username == 'example'"],
            cwd=runtime, env=env, text=True, capture_output=True,
        )
        assert result.returncode == 0, result.stderr
