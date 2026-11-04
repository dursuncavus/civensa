"""D-397: a CLI process must hash and discover the same table set as the web app."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROBE = '''
from app.db import Base
import app.first_load_service as service
before = 'ic_narrative_events' in Base.metadata.tables
service.load_all_models()
print(before, 'ic_narrative_events' in Base.metadata.tables, len(Base.metadata.tables))
'''


def run_probe():
    env = dict(os.environ, DATABASE_URL='sqlite://')
    env.pop('MIGRATION_DATABASE_URL', None)
    out = subprocess.run([sys.executable, '-c', PROBE], cwd=ROOT, env=env,
                         capture_output=True, text=True, check=True).stdout.split()
    return out[0] == 'True', out[1] == 'True', int(out[2])


def test_load_all_models_registers_lazily_imported_tables_in_a_fresh_process():
    _, after, count = run_probe()
    assert after
    from app.db import Base
    from app.first_load_service import load_all_models
    load_all_models()
    # A fresh CLI process sees exactly the table set of the fully imported app.
    assert count == len(Base.metadata.tables)
