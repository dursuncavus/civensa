"""Validate the split deployment bundle before release."""
import base64
import io
import pathlib
import zipfile

PARTS = [
    "bundle.part01", "bundle.part02", "bundle.part03a", "bundle.part03b",
    "bundle.part03c", "bundle.part03d", "bundle.part04", "bundle.part05",
]
root = pathlib.Path(__file__).resolve().parent
encoded = "".join((root / name).read_text() for name in PARTS)
archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded)))
bad_controls = []
python_files = 0
for name in archive.namelist():
    if not name.endswith(".py"):
        continue
    source = archive.read(name).decode("utf-8")
    python_files += 1
    controls = [(index, ord(char)) for index, char in enumerate(source)
                if ord(char) < 32 and char not in "\n\r\t"]
    if controls:
        bad_controls.append((name, controls[:5]))
main = archive.read("app/main.py").decode("utf-8")
assert not bad_controls, bad_controls
assert "APP_VERSION" in main
assert "app/templates/department.html" in archive.namelist()
assert "app/static/app.js" in archive.namelist()
print("BUNDLE_INTEGRITY_OK", len(archive.namelist()), "files", python_files, "python_utf8_clean")
