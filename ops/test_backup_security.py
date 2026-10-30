"""Exercise the actual upload boundary with real age and job-generated test keys."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from ops.backup_crypto import BackupCryptoError, ciphertext_pair, decrypt_backup, encrypt_backup


ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


class BackupSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="civ092-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        key = self.root / "key.txt"
        subprocess.run(["age-keygen", "-o", str(key)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        recipient = subprocess.check_output(["age-keygen", "-y", str(key)], stderr=subprocess.DEVNULL).decode().strip()
        self.env = dict(os.environ, BACKUP_AGE_RECIPIENT=recipient,
                        BACKUP_AGE_IDENTITY="", BACKUP_AGE_IDENTITY_FILE=str(key), PYTHONPATH=str(ROOT))
        self.dump = self.root / "backup" / "synthetic.dump"
        self.dump.parent.mkdir(mode=0o700)
        self.dump.write_bytes(b"PGDMP\x00synthetic-private-test-data")
        self.manifest = self.dump.with_suffix(".manifest.json")
        self.manifest.write_text(json.dumps({"public_table_row_counts": {"synthetic": 2}}))

    def test_actual_workflow_uploads_only_ciphertext(self):
        steps = workflow("db-backup.yml")["jobs"]["backup"]["steps"]
        encrypt = next(s for s in steps if s.get("name") == "Encrypt verified dump and private manifest")
        upload = next(s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@"))
        subprocess.run(["bash", "-euo", "pipefail", "-c", encrypt["run"]],
                       cwd=self.root, env=self.env, check=True, capture_output=True)
        uploaded = sorted(self.root.glob(upload["with"]["path"]))
        self.assertEqual(len(uploaded), 2)
        self.assertEqual(set(uploaded), set(ciphertext_pair(self.root / "backup-encrypted")))
        for path in uploaded:
            data = path.read_bytes()
            self.assertTrue(path.name.endswith(".age"))
            self.assertTrue(data.startswith(b"age-encryption.org/v1\n"))
            self.assertFalse(data.startswith(b"PGDMP"))
            self.assertNotIn(b"synthetic-private-test-data", data)
            self.assertNotIn(b"public_table_row_counts", data)
        self.assertEqual(upload["with"]["retention-days"], "30")
        self.assertNotIn("if", upload)  # Upload must never run after failed encryption.

    def test_workflow_fails_closed_before_dump_without_or_with_invalid_recipient(self):
        steps = workflow("db-backup.yml")["jobs"]["backup"]["steps"]
        guard_index = next(i for i, s in enumerate(steps) if "Require backup secret" in s.get("name", ""))
        dump_index = next(i for i, s in enumerate(steps) if s.get("id") == "backup")
        self.assertLess(guard_index, dump_index)
        for recipient in ("", " ", "invalid-recipient"):
            result = subprocess.run(["bash", "-euo", "pipefail", "-c", steps[guard_index]["run"]],
                                    cwd=self.root, env=dict(self.env, BACKUP_AGE_RECIPIENT=recipient,
                                                           NEON_BACKUP_DATABASE_URL="unused"), capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.root / "backup-encrypted").exists())

    def test_synthetic_round_trip_with_secret_style_identity(self):
        with patch.dict(os.environ, self.env):
            encrypt_backup(self.dump, self.root / "encrypted")
        # Exercise the workflow's secret-based identity without ever printing it.
        with patch.dict(os.environ, dict(self.env, BACKUP_AGE_IDENTITY=Path(self.env["BACKUP_AGE_IDENTITY_FILE"]).read_text())):
            restored = decrypt_backup(self.root / "encrypted", self.root / "decrypted")
        self.assertEqual(restored.read_bytes(), self.dump.read_bytes())
        self.assertEqual(restored.with_suffix(".manifest.json").read_bytes(), self.manifest.read_bytes())
        self.assertEqual(restored.stat().st_mode & 0o777, 0o600)

    def test_reject_plaintext_extra_file_and_renamed_dump(self):
        with patch.dict(os.environ, self.env):
            encrypt_backup(self.dump, self.root / "encrypted")
        stray = self.root / "encrypted" / "leaked.dump"
        stray.write_bytes(b"PGDMP")
        with self.assertRaises(BackupCryptoError):
            ciphertext_pair(stray.parent)
        stray.unlink()
        (stray.parent / (self.dump.name + ".age")).write_bytes(b"PGDMP-renamed")
        with self.assertRaises(BackupCryptoError):
            ciphertext_pair(stray.parent)

    def test_wrong_key_and_corruption_leave_no_plaintext_or_diagnostics(self):
        with patch.dict(os.environ, self.env):
            encrypt_backup(self.dump, self.root / "encrypted")
        other = self.root / "wrong-key.txt"
        subprocess.run(["age-keygen", "-o", str(other)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with patch.dict(os.environ, dict(self.env, BACKUP_AGE_IDENTITY_FILE=str(other))):
            with self.assertRaises(BackupCryptoError):
                decrypt_backup(self.root / "encrypted", self.root / "bad-key")
        self.assertFalse((self.root / "bad-key").exists())
        encrypted_dump = self.root / "encrypted" / (self.dump.name + ".age")
        encrypted_dump.write_bytes(encrypted_dump.read_bytes()[:-8])
        with patch.dict(os.environ, self.env):
            with self.assertRaises(BackupCryptoError):
                decrypt_backup(self.root / "encrypted", self.root / "corrupt")
        self.assertFalse((self.root / "corrupt").exists())

    def test_no_secrets_or_private_backup_download_in_pr_jobs(self):
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            doc = workflow(path.name)
            events = doc.get("on", {})
            if not any(name in events for name in ("pull_request", "pull_request_target")):
                continue
            for name, job in doc["jobs"].items():
                if job.get("if") == "github.event_name == 'workflow_dispatch'":
                    continue
                serialized = json.dumps({"workflow_env": doc.get("env", {}), "job": job})
                self.assertNotIn("secrets.", serialized, f"{path.name}:{name}")
                self.assertNotIn("ops.preprint_rehearsal", serialized)
                self.assertNotIn("ops.release_rehearsal", serialized)
                self.assertNotIn("gh run download", serialized)

    def test_full_history_is_manual_and_report_is_redacted(self):
        job = workflow("security.yml")["jobs"]["full-history"]
        self.assertEqual(job["if"], "github.event_name == 'workflow_dispatch'")
        self.assertEqual(job["steps"][0]["with"]["fetch-depth"], "0")
        scan = next(s["run"] for s in job["steps"] if s.get("name") == "Scan full history with redacted findings")
        self.assertIn('--log-opts="--all --full-history"', scan)
        self.assertIn("--redact=100", scan)
        uploads = [s for s in job["steps"] if s.get("uses", "").startswith("actions/upload-artifact@")]
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0]["with"]["path"], "${{ runner.temp }}/gitleaks-full-history-redacted.json")


    def test_secret_jobs_run_in_production_environment(self):
        # D-247: live-database and private-key secrets live only in the
        # "production" environment, limited to the phase5 branch.
        for name, job in (("db-backup.yml", "backup"),
                          ("preprint-backup-rehearsal.yml", "rehearsal"),
                          ("release-rehearsal.yml", "rehearsal")):
            self.assertEqual(workflow(name)["jobs"][job].get("environment"), "production", name)


if __name__ == "__main__":
    unittest.main()
