from pathlib import Path
import base64,hashlib,io,json,zipfile

def test_bundle_matches_reviewable_source():
    root=Path(__file__).resolve().parents[1];manifest=root/'bundle-manifest.json'
    if not manifest.exists():return  # Source-only local checkout before packaging.
    data=json.loads(manifest.read_text());raw=base64.b64decode(''.join((root/p).read_text() for p in data['parts']))
    assert hashlib.sha256(raw).hexdigest()==data['sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert set(archive.namelist())==set(data['files'])
        for name,digest in data['files'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest
            assert archive.read(name)==(root/name).read_bytes()
