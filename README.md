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
```

`sitecustomize.py` maps provider URLs `postgres://` and `postgresql://` to the
installed psycopg 3 driver. Launch with `PYTHONPATH` set to the checkout directory
(the container sets `/app`). Explicit `postgresql+psycopg://` URLs also work.

The deterministic source bundle is generated on demand for release packaging
only. Dockerfile and Render deployments use the source directly. Task PRs must
not add `bundle.part*`, `bundle-manifest.json`, or generated bundle output.

Build and verify a release bundle in the ignored default directory `dist/bundle/`:

```
python tools/build_bundle.py
python check_bundle.py
```

Pass a directory to build or check elsewhere (the builder rejects the checkout root):

```
python tools/build_bundle.py /tmp/civensa-release-bundle
python check_bundle.py /tmp/civensa-release-bundle
python qa_bundle_check.py /tmp/civensa-release-bundle
```

Both check entry points default to `dist/bundle/` and verify checksums, the file
list, exact source equality, and Python syntax. Bundle and integration-runtime
tests build their own temporary bundles; no committed bundle is needed.

Historical release notes are retained. Old manual pilot scripts are archived in
`tools/legacy-qa`; they are not current release gates. The obsolete partial
`deploy/app` copy is available in staging history only; use the complete current
application and migration chain.

Failed login attempts are always limited per normalized e-mail. Per-IP locking
is disabled by default because the current Render/Uvicorn setup exposes the
shared proxy address as `request.client.host`. `CIVENSA_LOGIN_IP_LIMIT=0` keeps
the IP lock disabled while failed attempts still store a hashed IP key. Set the
variable to a positive integer only when `request.client.host` reliably contains
distinct client addresses. The application does not parse `X-Forwarded-For`.

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
