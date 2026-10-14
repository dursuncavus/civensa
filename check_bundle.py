"""Check current bundle hashes, source equality and Python syntax without importing it."""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json
import zipfile


ROOT = Path(__file__).resolve().parent
DEFAULT_BUNDLE_DIR = ROOT / "dist" / "bundle"


def check_bundle(bundle_dir=DEFAULT_BUNDLE_DIR):
    bundle_dir = Path(bundle_dir)
    manifest = json.loads((bundle_dir / "bundle-manifest.json").read_text(encoding="utf-8"))
    encoded = "".join((bundle_dir / part).read_text(encoding="utf-8") for part in manifest["parts"])
    raw = base64.b64decode(encoded, validate=True)
    assert hashlib.sha256(raw).hexdigest() == manifest["sha256"], "Bundle checksum mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None, "Corrupt ZIP entry"
        assert set(archive.namelist()) == set(manifest["files"]), "Bundle file list mismatch"
        for name, digest in manifest["files"].items():
            content = archive.read(name)
            assert hashlib.sha256(content).hexdigest() == digest, name
            assert content == (ROOT / name).read_bytes(), f"Stale bundled source: {name}"
            if name.endswith(".py"):
                source = content.decode("utf-8")
                assert all(ord(char) >= 32 or char in "\n\r\t" for char in source), name
                compile(source, name, "exec")
    print("BUNDLE_INTEGRITY_OK", len(manifest["files"]), "files", manifest["sha256"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", nargs="?", type=Path, default=DEFAULT_BUNDLE_DIR,
                        help="Bundle directory (default: dist/bundle/ in the checkout).")
    check_bundle(parser.parse_args().bundle_dir)


if __name__ == "__main__":
    main()
