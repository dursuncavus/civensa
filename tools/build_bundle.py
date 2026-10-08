"""Rebuild the existing eight-part deployment artifact from reviewable source."""
from pathlib import Path
import base64,io,zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PARTS=['bundle.part01','bundle.part02','bundle.part03a','bundle.part03b','bundle.part03c','bundle.part03d','bundle.part04','bundle.part05']
files=[]
for folder in ['app','migrations']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
files.extend(ROOT/name for name in ['requirements.txt','alembic.ini','RELEASE_V5.md','sitecustomize.py'])
stream=io.BytesIO()
with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for path in sorted(files):
        entry=zipfile.ZipInfo(path.relative_to(ROOT).as_posix(),date_time=(2026,10,2,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o644<<16
        archive.writestr(entry,path.read_bytes())
raw=stream.getvalue();encoded=base64.b64encode(raw).decode();size=(len(encoded)+7)//8
for i,name in enumerate(PARTS):(ROOT/name).write_text(encoded[i*size:(i+1)*size])
manifest={'version':'5.0.0','sha256':hashlib.sha256(raw).hexdigest(),'parts':PARTS,'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
(ROOT/'bundle-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'bytes':len(raw),'files':len(files),'sha256':manifest['sha256']}))
