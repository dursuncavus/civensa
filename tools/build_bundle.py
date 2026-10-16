"""Build the deterministic eight-part source bundle for release packaging."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "dist" / "bundle"
PARTS = [
    "bundle.part01", "bundle.part02", "bundle.part03a", "bundle.part03b",
    "bundle.part03c", "bundle.part03d", "bundle.part04", "bundle.part05",
]


def build_bundle(output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = Path(output_dir).resolve()
    if output_dir == ROOT:
        raise ValueError("Bundle output must be outside the repository root; use dist/bundle/.")

    files = []
    for folder in ["app", "migrations"]:
        files.extend(
            path for path in (ROOT / folder).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    files.extend(ROOT / name for name in [
        "requirements.txt", "alembic.ini", "RELEASE_V5.md", "sitecustomize.py",
    ])
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            entry = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 10, 2, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, path.read_bytes())
    raw = stream.getvalue()
    encoded = base64.b64encode(raw).decode()
    size = (len(encoded) + 7) // 8
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(PARTS):
        (output_dir / name).write_text(encoded[i * size:(i + 1) * size], encoding="utf-8")
    manifest = {
        "version": "5.0.0",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "parts": PARTS,
        "files": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(files)
        },
    }
    (output_dir / "bundle-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({"bytes": len(raw), "files": len(files), "sha256": manifest["sha256"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", nargs="?", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Bundle output directory (default: dist/bundle/ in the checkout).")
    args = parser.parse_args()
    if args.output_dir.resolve() == ROOT:
        parser.error("Bundle output must be outside the repository root; use dist/bundle/.")
    build_bundle(args.output_dir)


if __name__ == "__main__":
    main()
