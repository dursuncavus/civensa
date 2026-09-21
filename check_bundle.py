import base64,io,pathlib,zipfile
parts=["bundle.part01","bundle.part02","bundle.part03a","bundle.part03b","bundle.part03c","bundle.part03d","bundle.part04","bundle.part05"];r=pathlib.Path(__file__).resolve().parent
z=zipfile.ZipFile(io.BytesIO(base64.b64decode("".join((r/p).read_text() for p in parts))))
for n in z.namelist():
 if n.endswith(".py"):compile(z.read(n).decode(),n,"exec")
m=z.read("app/main.py").decode()
assert 'APP_VERSION = "2.8.0"' in m and "/api/audit/export.csv" in m and "alembic_command.upgrade" in m and "alembic_command.stamp" in m and "user_bulk_create_revert" in m and "is_active" in z.read("app/models.py").decode()
assert "migrations/versions/8c4f72a10b31_add_user_active.py" in z.namelist()
print("BUNDLE_INTEGRITY_OK",len(z.namelist()))
