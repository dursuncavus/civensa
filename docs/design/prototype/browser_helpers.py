"""Yalnız statik prototip için loopback sunucusu ve Chromium ayarları.

CIV-093 guide_screenshots.py: 1440×900, DPR 1, tr-TR, Europe/Istanbul,
light, reduced_motion, font bekleme ve optimize PNG kuralları korunur.
Uygulamayı veya veritabanını başlatmaz; guide modülünün app bağımlılıklarını almaz.
"""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
from threading import Thread

ROOT = Path(__file__).resolve().parent
PAGES = ["components.html", "screens/034-modules.html", "screens/024-department.html",
         "screens/012-section-editor.html"]
MAX_PNG_BYTES = 1_500_000


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def static_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def launch(pw):
    executable = os.getenv("CIVENSA_CHROMIUM_PATH") or shutil.which("chromium")
    return pw.chromium.launch(**({"executable_path": executable} if executable else {}))


def context(browser, width):
    return browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=1,
                               color_scheme="light", locale="tr-TR", timezone_id="Europe/Istanbul",
                               reduced_motion="reduce", service_workers="block")
