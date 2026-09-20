import base64,io,pathlib,zipfile
parts=["bundle.part01","bundle.part02","bundle.part03a","bundle.part03b","bundle.part03c","bundle.part03d","bundle.part04","bundle.part05"];r=pathlib.Path(__file__).resolve().parent
z=zipfile.ZipFile(io.BytesIO(base64.b64decode("".join((r/p).read_text() for p in parts))))
for n in z.namelist():
    if n.endswith(".py"):compile(z.read(n).decode(),n,"exec")
m=z.read("app/main.py").decode();u=z.read("app/templates/users.html").decode()
assert 'APP_VERSION = "2.3.2"' in m and "missing-departments.csv" in m and "Eksik hesap listesini indir" in u
print("BUNDLE_INTEGRITY_OK",len(z.namelist()))
