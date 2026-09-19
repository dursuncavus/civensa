"""Validate the split deployment bundle before release."""
import base64,io,pathlib,zipfile
parts=["bundle.part01","bundle.part02","bundle.part03a","bundle.part03b","bundle.part03c","bundle.part03d","bundle.part04","bundle.part05"]
root=pathlib.Path(__file__).resolve().parent
z=zipfile.ZipFile(io.BytesIO(base64.b64decode("".join((root/p).read_text() for p in parts))))
for n in z.namelist():
    if n.endswith(".py"):compile(z.read(n).decode(),n,"exec")
m=z.read("app/main.py").decode();t=z.read("app/templates/activity_mapping.html").decode()
assert 'APP_VERSION = "2.2.3"' in m
assert '"mapping_suggestions": mapping_suggestions' in m
assert "strong_suggestion_count" in t
print("BUNDLE_INTEGRITY_OK",len(z.namelist()))
