# Render production deployment

## Türkçe özet

- 17 Ekim 2026 geçişinde doğrulanan üretim servisi `civensa-pilot`; kaynak dalı `main`, kök dizini depo köküdür.
- Render, ücretsiz native Python 3 servisi olarak kaynak koddan kurulur; eski bundle komutları asla geri getirilmemelidir.
- Başlatma komutundaki `PYTHONPATH=.` zorunludur; komut değişince **Clear build cache & deploy** kullanılmalıdır.
- Üretimde güçlü `SESSION_SECRET`, güvenli çerezler ve doğrudan (havuzsuz) Neon bağlantısı gerekir; demo verisi kapalıdır.
- Yayın PR’ında release rehearsal yeşil olmalıdır; başarısız kontrol varken `main` dalına yayın yapılmaz.
- Yayından önce üretimden süresiz bir Neon yedek dalı oluşturun; gizli istemle alınan bağlantının sunucu adını doğrulayıp migrasyonu çalıştırın.
- Yayından sonra başlangıç logunu, giriş sayfasını ve satır sayılarını kontrol edin; bağlantı bilgilerini hiçbir yerde paylaşmayın.
- Geri dönüşte önceki Render dalına geçiş ile yedek daldan veritabanı geri yüklemesi birlikte yapılmalıdır; eski kod yeni şemayla çalışamaz.

## Verified service configuration

These operational facts were verified by the lead during the **17 October 2026**
production switch. They describe the production configuration at that switch;
repository inspection alone cannot verify live Render or Neon settings.

| Render setting | Configuration |
| --- | --- |
| Service | `civensa-pilot` |
| Type | Web service |
| Runtime | Native Python 3 |
| Instance | Free |
| Deploy branch | `main` |
| Root Directory | Empty (repository root) |

Build Command:

```sh
pip install -r requirements.txt
```

Start Command:

```sh
PYTHONPATH=. python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`PYTHONPATH=.` is required so the repository's [sitecustomize.py](../../sitecustomize.py)
loads at Python startup and maps `postgres://` and `postgresql://` provider URLs
to the installed psycopg 3 driver. The inline assignment overrides any Render
`PYTHONPATH` environment variable for this command. Keep Root Directory empty so
`.` resolves to the repository root.

The old bundle-based commands (`cat bundle.part* …` and
`cd runtime && uvicorn …`) have been obsolete since **CIV-013** and must never be
restored. Render deploys source directly. After changing the build or start
command, use **Clear build cache & deploy**.

## Required environment variables

Only variable names and non-secret configuration are documented here. Enter
secrets directly in Render's environment settings through the approved channel.

| Variable | Requirement |
| --- | --- |
| `CIVENSA_ENV` | `production` |
| `SESSION_SECRET` | At least 32 random characters; never use a development secret |
| `COOKIE_SECURE` | `1` |
| `DEMO_SEED` | `0` |
| `DATABASE_URL` | Neon production database, direct **non-pooled** connection; never record its value here |
| `PYTHON_VERSION` | Set explicitly to the approved Python version; the Dockerfile and README use Python 3.12 |

In production, [app/config.py](../../app/config.py) refuses startup with an empty,
known development, or shorter-than-32-character `SESSION_SECRET`, or with
`COOKIE_SECURE` off. [app/main.py](../../app/main.py)'s lifespan runs the equivalent
of `alembic upgrade head` itself before serving traffic. A deployment can therefore
change the database schema even if no manual migration was run.

## Release procedure

These are operator instructions; documenting them does not execute a deployment
or a production database command.

1. **Release rehearsal must be green on the release PR** (`phase5` → `main`).
   The `Release migration rehearsal` check restores the newest successful
   `Daily verified database backup` artifact from `main` (maximum age 48 hours)
   into disposable PostgreSQL 18 inside GitHub Actions. It verifies checksum,
   size, counts and Alembic versions, upgrades twice, and starts the production
   lifespan with demo seeding disabled before checking `/login`. The summary
   contains PASS/FAIL and public table counts before → after, including new
   tables; raw database/app output and row contents are suppressed. No artifacts
   are uploaded and downloaded files are deleted even on failure. Production
   data stays inside Actions; no production connection or secret is used.
   Pre-existing tables must not lose rows; intentional deletions require a
   reason in `ops/release_rehearsal.py`'s allowlist and the release PR.
   If the backup is missing/stale, the owner runs **Actions → Daily verified
   database backup → Run workflow** on `main`, waits for green, then uses
   **Re-run failed jobs** on the release check. For a manual rehearsal use
   **Actions → Release migration rehearsal → Run workflow**, selecting the
   release-candidate branch. Manual dispatch becomes available in the Actions
   UI once this workflow is on `main`; until then the release PR event runs it.
   Require this check through branch protection on `main`; the workflow alone
   does not configure branch protection. Use trusted same-repository release
   PRs only; fork PRs cannot access production backup artifacts.
2. Record the previous Render branch and deployed revision. Create a Neon backup
   branch **from production before any migration**, remove its expiration, and
   record its identity and recovery point. Record baseline row counts for the
   tables that will be checked after release.
3. On a trusted machine, use a checkout of the intended release revision at the
   repository root, with its dependencies installed. Read the production direct
   connection into `DATABASE_URL` through a hidden prompt. For **zsh**:

   ```zsh
   read -s "DATABASE_URL?Production direct DATABASE_URL: "
   export DATABASE_URL
   ```

   Ensure `MIGRATION_DATABASE_URL` is unset in this shell: the repository's
   `migrations/env.py` gives it precedence over `DATABASE_URL`. See
   [database role operations](db-roles.md) for the separate split-role procedure.
   Inspect only the host name without displaying the connection string:

   ```sh
   python -c 'import os; from urllib.parse import urlsplit; print(urlsplit(os.environ["DATABASE_URL"]).hostname)'
   ```

   Compare the host name with the intended production endpoint in Neon and
   confirm it is direct/non-pooled. **Stop if it differs.** Only after verifying
   the endpoint and backup, run:

   ```sh
   alembic upgrade head
   ```

   Stop on migration failure. When finished, remove the secret from the shell:

   ```sh
   unset DATABASE_URL
   ```

4. Switch Render's deploy branch to the approved release branch (`main` for the
   verified production configuration) and deploy. If either command changed,
   use **Clear build cache & deploy**.
5. Check Render logs for **Application startup complete** and investigate any
   startup or migration errors before accepting the release.
6. Open `/login` on the production service and check that the login page loads.
   Compare post-release row counts with the recorded baseline, accounting only
   for expected migration changes and legitimate writes. If using Neon SQL
   Editor for read-only counts, follow the warning below.

## Secret handling and Neon SQL Editor

Never paste connection strings into chat, tickets, or screenshots. Do not place
them in shell command literals, repository files, PRs, or logs. If a connection
string is exposed, reset the Neon role password and update Render's
`DATABASE_URL` with the replacement through the approved secret channel.

**Neon SQL Editor opens with sample code that creates a table. Always start a
new empty query before running anything on production.** Review the target
branch/database and the entire query before executing it; never run the sample
code against production.

## Rollback

Set Render's branch back to the recorded previous branch **only together with
restoring the database from the pre-release Neon backup branch**. Old code cannot
run on a newer schema; changing only the Render branch is not a rollback.
Coordinate the database restore and application deployment while writes are
paused. A restore returns data to the backup recovery point, so preserve and
account for subsequent writes before proceeding. Repeat the startup-log, login,
and row-count checks after restoration.

## Repository command cross-check

- [Dockerfile](../../Dockerfile) installs the same `requirements.txt` (with the
  additional `--no-cache-dir` option) and launches `python -m uvicorn app.main:app`
  on `0.0.0.0`. Docker uses port `8000` and `PYTHONPATH=/app`; native Render uses
  `$PORT` and `PYTHONPATH=.` because the runtime paths differ.
- [README.md](../../README.md) documents Python 3.12, the same Uvicorn module,
  repository-root `PYTHONPATH`, direct source deployment, and startup migrations.
  Its integration/deployment-status section retains historical pre-switch gates;
  the configuration above records the lead-verified production switch.
- [app/config.py](../../app/config.py) supplies the production secret and cookie
  checks; [app/main.py](../../app/main.py) supplies the lifespan migration and
  `/login` route. [migrations/env.py](../../migrations/env.py) and
  [alembic.ini](../../alembic.ini) support the repository-root Alembic command.
