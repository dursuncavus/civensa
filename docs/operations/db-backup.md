# Daily verified pilot database backup

`Daily verified database backup` runs from `main` daily at **00:30 UTC
(03:30 Istanbul)** and can be started through **Actions → Daily verified database
backup → Run workflow**. GitHub may delay scheduled runs. The owner must first
set repository Actions secret `NEON_BACKUP_DATABASE_URL` to the direct/non-pooled
Neon `postgresql://` URL with `sslmode=require`; never paste it into an issue,
PR, or log. No live database writes are performed.

PostgreSQL 18 tools create a custom-format dump without owners or privileges.
One read-only snapshot supplies both the dump and manifest: UTC timestamp, size,
SHA-256, tool version, Alembic `version_num` values (an array supporting multiple
heads), and exact `count(*)` values for every public table. A disposable
PostgreSQL 18 service restores it and checks all those counts and versions.
Only a successful verification uploads the dump and manifest together as
`civensa-db-backup-YYYYMMDD-HHMMZ`, retained for **90 days**.

## Download and restore locally

Open a successful workflow run in the repository's **Actions** tab and download
its artifact under **Artifacts**. Alternatively, use
`gh run download RUN_ID --repo dursuncavus/civensa --name civensa-db-backup-YYYYMMDD-HHMMZ`.
Extract the ZIP; the `.dump` and `.manifest.json` files belong together.
Before restoring, compare the dump's `sha256sum` and byte size with the manifest.
Backups contain pilot data: restrict access and store downloaded copies securely.

Use PostgreSQL 18 tools and a **new, empty local database**, never the live URL:

```sh
createdb -h localhost -U postgres civensa_restore
pg_restore -h localhost -U postgres -d civensa_restore \
  --exit-on-error --single-transaction --no-owner --no-privileges \
  civensa-neon-YYYYMMDD-HHMMZ.dump
psql -h localhost -U postgres -d civensa_restore \
  -c 'SELECT version_num FROM public.alembic_version ORDER BY version_num;'
```

Recompute `SELECT count(*) FROM public."table_name";` for every manifest table
and compare with `public_table_row_counts`. Password prompts or a local
`.pgpass` file avoid putting credentials in commands. Required extensions must
also exist locally; unavailable extensions fail the restore rather than produce
an unverified backup.

## Operations

After owner merge and secret setup, manually run on `main` and confirm a green
run with both artifact files. Check GitHub Actions failure notifications are
enabled and investigate failed or missing daily runs; this is a daily recovery
point, not continuous recovery. Empty secrets, TLS/connection failures,
insufficient read privileges, restore errors, or count/version mismatches fail
the job visibly. Raw connection errors are suppressed to keep secrets out of logs.

Assumptions: the secret reads all tables and Alembic metadata; PostgreSQL remains
version 18 or older; any Neon extensions needed by the dump are available in the
official `postgres:18` image. No concurrent schema migrations should run during
the backup. If the server is upgraded, upgrade both client and restore image.
Repository/organization Actions settings must permit 90-day artifact retention
and sufficient artifact storage. Expired artifacts are removed by GitHub; a
longer archive requires a separate owner-managed copy. Neon's history remains
independent of this logical backup.
