import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def test_bundle_matches_reviewable_source(tmp_path):
    bundle_dir = tmp_path / "bundle"
    subprocess.run([sys.executable, str(ROOT / "tools/build_bundle.py"), str(bundle_dir)],
                   cwd=tmp_path, check=True, timeout=180)
    data = json.loads((bundle_dir / "bundle-manifest.json").read_text())
    raw = base64.b64decode("".join((bundle_dir / part).read_text() for part in data["parts"]),
                          validate=True)
    assert hashlib.sha256(raw).hexdigest() == data["sha256"]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(data["files"])
        for name, digest in data["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
            assert archive.read(name) == (ROOT / name).read_bytes()

    # Both entry points verify the external bundle against the checkout, including syntax.
    for checker in ["check_bundle.py", "qa_bundle_check.py"]:
        result = subprocess.run([sys.executable, str(ROOT / checker), str(bundle_dir)],
                                cwd=tmp_path, text=True, capture_output=True, check=True, timeout=180)
        assert "BUNDLE_INTEGRITY_OK" in result.stdout

    # Output location and a repeated build must not alter any artifact bytes.
    second_dir = tmp_path / "second-bundle"
    subprocess.run([sys.executable, str(ROOT / "tools/build_bundle.py"), str(second_dir)],
                   cwd=tmp_path, check=True, timeout=180)
    for name in [*data["parts"], "bundle-manifest.json"]:
        assert (bundle_dir / name).read_bytes() == (second_dir / name).read_bytes()


def test_bundle_builder_rejects_repository_root(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "tools/build_bundle.py"), str(ROOT)],
                            cwd=tmp_path, text=True, capture_output=True, timeout=180)
    assert result.returncode != 0
    assert "Bundle output must be outside the repository root" in result.stderr
