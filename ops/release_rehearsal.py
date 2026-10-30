"""Rehearse only inside Actions; never emit child output or exception details."""
import hashlib
import html
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlsplit

from ops.backup_crypto import decrypt_backup

BACKUP_REQUIRED = "Önce Actions → Daily verified database backup → Run workflow çalıştırın, yeşil bittikten sonra bu kontrolü yeniden çalıştırın."
# table: one-line reason for an intentional deletion (also explain it in the PR).
ROW_LOSS_ALLOWLIST: dict[str, str] = {}
BACKUP_DIR = Path("rehearsal-backup")


class RehearsalFailure(Exception):
    pass


def require_fresh_backup(timestamp, now=None):
    try:
        created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age = (now or datetime.now(timezone.utc)) - created
        if not timedelta(0) <= age <= timedelta(hours=48):
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise RehearsalFailure(BACKUP_REQUIRED) from None


def assert_local_database(url):
    try:
        parsed = urlsplit(url)
        # Reject libpq query overrides (host, hostaddr, service, etc.), multi-host
        # URLs and sockets; the same URL goes to psycopg, Docker and Alembic.
        if (parsed.scheme not in {"postgresql", "postgresql+psycopg"} or parsed.hostname not in {"localhost", "127.0.0.1"}
                or parsed.query or parsed.fragment or not parsed.path.strip("/")
                or parsed.port != 5432):
            raise ValueError
    except (TypeError, ValueError):
        raise RehearsalFailure("Disposable database URL must target localhost or 127.0.0.1 on port 5432 without query overrides.") from None


def row_losses(before, after, allowlist=None):
    allowed = ROW_LOSS_ALLOWLIST if allowlist is None else allowlist
    return sorted(table for table, count in before.items()
                  if (table not in after or after[table] < count)
                  and not allowed.get(table, "").strip())


def run_private(command, message, **kwargs):
    # Never replay stdout/stderr, including SQL parameters, COPY failures, or
    # tracebacks. Child output goes directly to /dev/null, not an Actions log.
    result = subprocess.run(command, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, **kwargs)
    if result.returncode:
        raise RehearsalFailure(message)


def github_json(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True)
    if result.returncode:
        raise RehearsalFailure("Backup lookup failed; check Actions read permission.")
    return json.loads(result.stdout)


def download_backup():
    repo = os.environ["GITHUB_REPOSITORY"]
    try:
        metadata = github_json(f"repos/{repo}")
    except (ValueError, TypeError):
        raise RehearsalFailure(BACKUP_REQUIRED) from None
    default_branch = metadata.get("default_branch") if isinstance(metadata, dict) else None
    if not isinstance(default_branch, str) or not default_branch.strip():
        raise RehearsalFailure(BACKUP_REQUIRED)
    branch = quote(default_branch, safe="")
    runs = github_json(f"repos/{repo}/actions/workflows/db-backup.yml/runs?branch={branch}&status=success&per_page=1")["workflow_runs"]
    if not runs:
        raise RehearsalFailure(BACKUP_REQUIRED)
    run = runs[0]
    require_fresh_backup(run["created_at"])
    if (run["name"] != "Daily verified database backup" or run["head_branch"] != default_branch
            or run.get("event") not in {"schedule", "workflow_dispatch"}):
        raise RehearsalFailure(BACKUP_REQUIRED)
    artifacts = github_json(f"repos/{repo}/actions/runs/{run['id']}/artifacts")["artifacts"]
    artifacts = [a for a in artifacts if not a["expired"] and a["name"].startswith("civensa-db-backup-")]
    if len(artifacts) != 1:
        raise RehearsalFailure(BACKUP_REQUIRED)
    BACKUP_DIR.mkdir(mode=0o700)
    run_private(["gh", "run", "download", str(run["id"]), "--repo", repo,
                 "--name", artifacts[0]["name"], "--dir", str(BACKUP_DIR)],
                "Verified backup download failed.")


def verify_dump():
    dump = decrypt_backup(BACKUP_DIR, BACKUP_DIR / "decrypted")
    os.environ.pop("BACKUP_AGE_IDENTITY", None)
    os.environ.pop("BACKUP_AGE_IDENTITY_FILE", None)
    saved = json.loads(dump.with_suffix(".manifest.json").read_text())
    require_fresh_backup(saved.get("utc_timestamp"))
    with dump.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if (saved["file_name"] != dump.name or saved["file_size_bytes"] != dump.stat().st_size
            or saved["sha256"] != digest):
        raise RehearsalFailure("Backup checksum or size verification failed.")
    return saved, dump


def database_state(url):
    # Same public-table and version checks as db-backup.yml; no row values read.
    import psycopg
    from psycopg import sql

    with psycopg.connect(url, connect_timeout=30) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        tables = connection.execute("""
            SELECT c.relname FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'f')
            ORDER BY c.relname
        """).fetchall()
        counts = {}
        for (table,) in tables:
            query = sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("public"), sql.Identifier(table))
            counts[table] = connection.execute(query).fetchone()[0]
        versions = [row[0] for row in connection.execute(
            "SELECT version_num FROM public.alembic_version ORDER BY version_num")]
    return {"public_table_row_counts": counts, "alembic_version": {"version_num": versions}}


def smoke():
    assert_local_database(os.environ["DATABASE_URL"])
    if "MIGRATION_DATABASE_URL" in os.environ:
        raise RehearsalFailure("Migration override must be unset.")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app, base_url="https://localhost") as client:
        if client.get("/login").status_code != 200:
            raise RehearsalFailure("Application login smoke check failed.")


def summary(status, before, after):
    lines = [f"## Release migration rehearsal: {status}", "",
             "| Public table | Before | After |", "| --- | ---: | ---: |"]
    for table in sorted(before.keys() | after.keys()):
        # Escape Markdown/HTML and workflow-command characters in identifiers.
        name = html.escape(table).replace("|", "&#124;").replace("\n", "&#10;").replace("\r", "&#13;").replace("`", "&#96;")
        lines.append(f"| {name} | {before.get(table, 'new')} | {after.get(table, 'unavailable')} |")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
        output.write("\n".join(lines) + "\n")


def rehearse():
    before, after = {}, {}
    status = "FAIL"
    try:
        if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
            raise RehearsalFailure("Özel yedek yalnız elle başlatılan provada kullanılabilir.")
        url = os.environ["DATABASE_URL"]
        assert_local_database(url)
        # sitecustomize normalizes DATABASE_URL at Python startup. libpq tools
        # need the plain scheme; the checked host and all other fields stay fixed.
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
        if "MIGRATION_DATABASE_URL" in os.environ:
            raise RehearsalFailure("Migration override must be unset.")
        download_backup()
        saved, dump = verify_dump()
        # Candidate code gets no Actions token. The session secret exists only
        # for this process and its children, never a workflow output or artifact.
        os.environ.pop("GH_TOKEN", None)
        os.environ.pop("GITHUB_TOKEN", None)
        os.environ.update(SESSION_SECRET=secrets.token_urlsafe(48), COOKIE_SECURE="1",
                          DEMO_SEED="0", CIVENSA_ENV="production")
        env = dict(os.environ, PGDATABASE=url)
        run_private(["docker", "run", "--rm", "--network", "host", "--volume",
                     f"{BACKUP_DIR.resolve()}:/backup:ro", "--env", "PGDATABASE", "postgres:18",
                     "sh", "-c", 'exec "$@" --dbname="$PGDATABASE"', "pg-client",
                     "pg_restore", "--exit-on-error", "--single-transaction", "--no-owner",
                     "--no-privileges", f"/backup/decrypted/{dump.name}"], "Disposable restore failed.", env=env)
        restored = database_state(url)
        before = restored["public_table_row_counts"]
        if any(restored[key] != saved[key] for key in restored):
            raise RehearsalFailure("Restored counts or Alembic versions differ from manifest.")
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        if not head:
            raise RehearsalFailure("Exactly one migration head is required.")
        previous = None
        for _ in range(2):
            run_private([sys.executable, "-m", "alembic", "upgrade", "head"], "Alembic upgrade failed; details suppressed.")
            current = database_state(url)
            after = current["public_table_row_counts"]
            if current["alembic_version"]["version_num"] != [head]:
                raise RehearsalFailure("Migrated Alembic version does not match script head.")
            if previous is not None and current != previous:
                raise RehearsalFailure("Second upgrade changed counts or Alembic version.")
            previous = current
        run_private([sys.executable, "-m", "ops.release_rehearsal", "smoke"], "Application lifespan or login smoke check failed; details suppressed.")
        after = database_state(url)["public_table_row_counts"]
        if row_losses(before, after):
            raise RehearsalFailure("Pre-existing public tables lost rows; see count summary.")
        status = "PASS"
    finally:
        summary(status, before, after)


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["smoke"]:
            smoke()
        else:
            rehearse()
    except RehearsalFailure as exc:
        print(f"::error::{exc}")
        sys.exit(1)
    except Exception:
        print("::error::Release rehearsal failed; diagnostic details suppressed.")
        sys.exit(1)
