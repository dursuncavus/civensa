# Civensa

Belediyeler için performans programı ve faaliyet raporu sistemi.

## Local development and validation

Use Python 3.12, install `requirements-dev.txt`, and supply environment variables
before starting `python -m uvicorn app.main:app`. See `.env.example`; it is an
example, not an automatically loaded configuration. Demo seeding is disabled by
default. Startup applies committed Alembic migrations; back up any existing data
before an upgrade. The container includes the migration chain and uses the same
startup path as the source. Its environment must supply database/session settings.

For validation use a **fresh disposable** PostgreSQL database:

```
CIVENSA_TEST_POSTGRES_URL=postgresql+psycopg://USER@localhost/TEST_DB python -m pytest -q --require-postgres
python -m compileall -q app migrations tools
node --check app/static/app.js
python check_bundle.py
```

`sitecustomize.py` maps provider URLs `postgres://` and `postgresql://` to the
installed psycopg 3 driver. Launch with `PYTHONPATH` set to the checkout directory
(the container sets `/app`). Explicit `postgresql+psycopg://` URLs also work.
`tools/build_bundle.py` rebuilds the deterministic source bundle; both bundle
check entry points verify hashes and exact source equality.

Historical release notes are retained. Old manual pilot scripts are archived in
`tools/legacy-qa`; they are not current release gates. The obsolete partial
`deploy/app` copy is available in staging history only; use the complete current
application and migration chain.

## Integration and deployment status

See `docs/integration-staging-performance-bridge.md` for the deliberate history
bridge and reconciliation decisions. Deployment is not authorized by this PR.
[Issue #4](https://github.com/dursuncavus/civensa/issues/4) (database roles) and
[issue #5](https://github.com/dursuncavus/civensa/issues/5) (sidebar overlap) must be
resolved before deployment. The repeat migration-test collision remains tracked
separately in `docs/issues/postgres-migration-test-repeat.md`.

After the integration PR is approved and merged with a **merge commit**, future
work must branch from updated GitHub `main`. Do not squash or rebase this bridge:
its two parents are necessary to preserve both existing histories.
