"""Check current bundle hashes, source equality and Python syntax without importing it."""
from pathlib import Path
import base64
import hashlib
import io
import json
import zipfile


def check_bundle(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    manifest = json.loads((root / "bundle-manifest.json").read_text())
    raw = base64.b64decode("".join((root / part).read_text() for part in manifest["parts"]), validate=True)
    assert hashlib.sha256(raw).hexdigest() == manifest["sha256"], "Bundle checksum mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None, "Corrupt ZIP entry"
        assert set(archive.namelist()) == set(manifest["files"]), "Bundle file list mismatch"
        for name, digest in manifest["files"].items():
            content = archive.read(name)
            assert hashlib.sha256(content).hexdigest() == digest, name
            assert content == (root / name).read_bytes(), f"Stale bundled source: {name}"
            if name.endswith(".py"):
                source = content.decode("utf-8")
                assert all(ord(char) >= 32 or char in "\n\r\t" for char in source), name
                compile(source, name, "exec")
    print("BUNDLE_INTEGRITY_OK", len(manifest["files"]), "files", manifest["sha256"])


if __name__ == "__main__":
    check_bundle()
