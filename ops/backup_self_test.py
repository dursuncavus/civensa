"""PR-safe round trip using generated keys and synthetic disposable PostgreSQL only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

import psycopg

from ops.backup_crypto import ciphertext_pair, encrypt_backup
from ops import preprint_rehearsal, release_rehearsal
from ops.release_rehearsal import assert_local_database, database_state, run_private
from scripts.first_load_dryrun import local_test_url
from scripts.rehearse_clear_preprint_2027 import empty_database, pg_environment


def pg_tool(arguments, url, root):
    env = pg_environment(url)
    command = ["docker", "run", "--rm", "--log-driver=none", "--network", "host",
               "--user", f"{os.getuid()}:{os.getgid()}",
               "--volume", f"{root}:{root}"]
    for name in ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGUSER", "PGPASSWORD", "PGCONNECT_TIMEOUT"):
        command += ["--env", name]
    run_private([*command, "postgres:18", *arguments, "--dbname", url.database],
                "Sentetik PostgreSQL işlemi başarısız.", env=env)


def self_test():
    # Reuse the existing local-only parser and disposable DB guard; no production URL.
    url = local_test_url()
    assert_local_database(url.set(drivername="postgresql").render_as_string(hide_password=False))
    with TemporaryDirectory(prefix="civ092-self-test-") as directory:
        root = Path(directory)
        key = root / "identity.txt"
        run_private(["age-keygen", "--output", str(key)], "Geçici test anahtarı üretilemedi.")
        recipient = subprocess.check_output(["age-keygen", "-y", str(key)], stderr=subprocess.DEVNULL).decode().strip()
        with empty_database(url) as source:
            plain_url = source.url.set(drivername="postgresql").render_as_string(hide_password=False)
            with psycopg.connect(plain_url) as connection:
                connection.execute("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)")
                connection.execute("INSERT INTO alembic_version VALUES ('civ092_synthetic')")
                connection.execute("CREATE TABLE synthetic (id integer PRIMARY KEY, label text)")
                connection.execute("INSERT INTO synthetic VALUES (1, 'sentetik'), (2, NULL)")
            dump = root / "synthetic.dump"
            pg_tool(["pg_dump", "--format=custom", "--no-owner", "--no-privileges", "--file", str(dump)],
                    source.url, root)
            expected = database_state(plain_url)
            manifest = dict(expected, utc_timestamp=datetime.now(timezone.utc).isoformat(),
                            file_name=dump.name, file_size_bytes=dump.stat().st_size,
                            sha256=hashlib.sha256(dump.read_bytes()).hexdigest())
            dump.with_suffix(".manifest.json").write_text(json.dumps(manifest))
            # No repository secret: this throwaway key exists only for this job.
            with patch.dict(os.environ, BACKUP_AGE_RECIPIENT=recipient,
                            BACKUP_AGE_IDENTITY="", BACKUP_AGE_IDENTITY_FILE=str(key)):
                encrypted = root / "artifact"
                encrypt_backup(dump, encrypted)
                assert len(ciphertext_pair(encrypted)) == 2
                with patch.object(release_rehearsal, "BACKUP_DIR", encrypted):
                    saved, decrypted = release_rehearsal.verify_dump()
                assert "BACKUP_AGE_IDENTITY_FILE" not in os.environ

            # Exercise preprint's download/decrypt boundary without a GitHub call
            # or an existing artifact: the mocked download copies this fixture only.
            def synthetic_download(*args):
                for source_file in encrypted.glob("*.age"):
                    shutil.copyfile(source_file, root / "preprint" / source_file.name)

            responses = [dict(default_branch="feature/authorization-workflow-phase5"),
                         dict(name="Daily verified database backup",
                              head_branch="feature/authorization-workflow-phase5", event="schedule",
                              status="completed", conclusion="success", created_at=manifest["utc_timestamp"]),
                         dict(artifacts=[dict(id=1, name="civensa-db-backup-synthetic", expired=False)])]
            with patch.dict(os.environ, BACKUP_AGE_IDENTITY="", BACKUP_AGE_IDENTITY_FILE=str(key),
                            GITHUB_REPOSITORY="synthetic/fixture"), \
                    patch.object(preprint_rehearsal, "BACKUP_DIR", root / "preprint"), \
                    patch.object(preprint_rehearsal, "github_json", side_effect=responses), \
                    patch.object(preprint_rehearsal, "run_private", side_effect=synthetic_download):
                preprint_dump, metadata = preprint_rehearsal.download_verified_run(1)
                assert preprint_dump.read_bytes() == dump.read_bytes()
                assert metadata == dict(backup_run_id=1, artifact_id=1)
                assert "BACKUP_AGE_IDENTITY_FILE" not in os.environ
            saved = json.loads(decrypted.with_suffix(".manifest.json").read_text())
            assert saved == manifest
            assert saved["sha256"] == hashlib.sha256(decrypted.read_bytes()).hexdigest()
            with empty_database(url) as target:
                pg_tool(["pg_restore", "--exit-on-error", "--single-transaction", "--no-owner", "--no-privileges",
                         str(decrypted)], target.url, root)
                target_url = target.url.set(drivername="postgresql").render_as_string(hide_password=False)
                assert database_state(target_url) == expected
                with psycopg.connect(target_url) as connection:
                    assert connection.execute("SELECT * FROM synthetic ORDER BY id").fetchall() == [(1, "sentetik"), (2, None)]
    print("Şifreli sentetik yedek çözüldü; PostgreSQL geri yükleme, SHA256 ve sayım kontrolleri geçti.")


if __name__ == "__main__":
    self_test()
