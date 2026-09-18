"""Validate the split deployment bundle before release."""
import base64, io, pathlib, zipfile
PARTS=["bundle.part01","bundle.part02","bundle.part03a","bundle.part03b","bundle.part03c","bundle.part03d","bundle.part04","bundle.part05"]
root=pathlib.Path(__file__).resolve().parent
archive=zipfile.ZipFile(io.BytesIO(base64.b64decode("".join((root/n).read_text() for n in PARTS))))
for name in archive.namelist():
    if name.endswith(".py"): compile(archive.read(name).decode("utf-8"),name,"exec")
main=archive.read("app/main.py").decode()
template=archive.read("app/templates/activity_mapping.html").decode()
javascript=archive.read("app/static/app.js").decode()
assert 'APP_VERSION = "2.2.2"' in main
assert "selected' if suggestion" not in template
assert "choose-suggestion" in template and "selectStrongSuggestions" in template
assert "window.confirm(assignments.length" in javascript
print("BUNDLE_INTEGRITY_OK",len(archive.namelist()))
