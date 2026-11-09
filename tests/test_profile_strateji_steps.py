"""CIV-196 — `scripts/profile_strateji_steps.py` duman testi (küçük veri, çıkış 0)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_profile_strateji_steps_runs_on_tiny_db(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "profile_strateji_steps.py"),
         "--tiny", "--runs", "1"],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stderr
    # Dört adımın dördü de ölçüldü ve özet basıldı.
    for marker in ("step1", "step2", "step3", "step4", "SQL sayısı"):
        assert marker in result.stdout, marker
