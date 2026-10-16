# Runtime and migration database roles (CIV-012)

This implements the code/test part of [issue #4](https://github.com/dursuncavus/civensa/issues/4)
and audit gap PP-19. It does **not** establish production readiness or close the
issue. No live database was inspected or changed. A separately authorized rollout
must verify actual provider permissions, ownership, backups and connection settings.

## Privilege contract

The SQL targets a **dedicated Civensa database, application schema `public`**, on
PostgreSQL 16+. Do not apply its broad PUBLIC revokes to a shared application schema.

| Role | Schema | Tables | Sequences | Functions | Role administration |
| --- | --- | --- | --- | --- | --- |
| `civensa_owner` | Owns `public`; USAGE/CREATE/ALTER | Owns migration-created objects; DDL and DML | Owns migration-created sequences | Owns migration-created functions | NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS |
| `civensa_app` | USAGE only; no CREATE/ownership | SELECT, INSERT, UPDATE, DELETE; no TRUNCATE, REFERENCES, TRIGGER or ownership | USAGE, SELECT; no UPDATE/setval or ownership | EXECUTE on application SECURITY INVOKER functions | Same negative attributes; NOINHERIT; no memberships, including `civensa_owner` |

Owner privileges can bypass immutability: the owner connection is exclusively for
migrations/administration. Application triggers still reject changes to immutable
records even though the runtime has table-level UPDATE/DELETE grants. Mutable
tables need those grants for entry, workflow, import and login-throttle cleanup.
The migration metadata table `alembic_version` is SELECT-only for runtime; both
the role SQL and split-role Alembic completion revoke its write grants so requests
cannot alter which migrations the owner will run next.
Function EXECUTE is needed by invoker trigger helpers and trigger WHEN expressions;
no SECURITY DEFINER functions exist in the current migration chain. Future ones
require review and will be rejected by the startup guard if runtime can call them.
PostgreSQL built-in functions retain their standard grants (including advisory
locks used by login throttling). Runtime receives database CONNECT only; CREATE
and TEMPORARY are revoked from runtime and PUBLIC. Only the migration owner is
granted TEMPORARY, preventing runtime DDL even in temporary schemas.

`ops/db_roles.sql` creates missing roles without passwords, normalizes role
attributes, removes runtime memberships, makes `civensa_owner` the schema owner,
and resets existing grants and owner default privileges. Global default revokes
are intentional: schema-local defaults cannot subtract global grants. Objects
created later by `civensa_owner` receive the same runtime grants, including sequences
created by SERIAL. Migrations must connect **as** `civensa_owner`; merely being a
member does not make another creator's default privileges apply. Existing table,
sequence and routine ownership must be transferred explicitly. The script refuses
to proceed if `civensa_app` still owns objects; it never silently reassigns them.
It does not manage passwords, provider roles, database ownership, extensions or
privileges in other schemas. The audit and startup guard expose remaining risks.

## Connection selection and startup

- `DATABASE_URL` exclusively supplies request sessions and runtime inspection.
- Nonempty `MIGRATION_DATABASE_URL` supplies both startup Alembic and `alembic`
  CLI, including stamp, online migration and offline SQL generation. Both URLs
  accept `postgres://`, `postgresql://`, and `postgresql+psycopg://` with the installed
  psycopg driver. Percent-encoded credentials survive Alembic interpolation.
- If the migration URL is absent/empty, the existing DATABASE_URL/Alembic-config
  fallback and pilot startup behaviour remain in place. No new migration is added.
- If it is present, startup checks the runtime connection **before** migration or
  serving traffic. It fails with a Turkish log/error naming both variable names
  and the audit command if runtime is unsafe or the check cannot complete. URLs,
  passwords and raw connection exceptions are not logged by the guard.

The guard reads PostgreSQL catalogs in a read-only transaction. It rejects unsafe
role attributes, owner-role membership, database ownership/CREATE/TEMPORARY, persistent
schema ownership/CREATE, relation/routine/type ownership, table TRUNCATE/TRIGGER
(and MAINTAIN on PostgreSQL 17+), callable SECURITY DEFINER routines, predefined
server-file/program roles, and SET/ALTER SYSTEM on `session_replication_role`. It follows
indirect memberships and checks session identity too, so NOINHERIT or an initial
SET ROLE cannot hide an administrator connection. Membership checking deliberately
fails conservatively even for edges with SET/INHERIT disabled. It checks all
non-system schemas; resolve any unrelated privileged membership rather than
weakening the guard. It performs no CREATE/DROP probes.

The guard is a startup configuration check, not a continuous monitor or a proof
against future administrator changes. The two URLs must identify the same database
and application schema, with compatible search paths. Migration credentials remain
available to the startup process under this design; a future dedicated migration
job can remove them from the serving process. This task does not add such a job.

## Read-only audit

Have the secret manager inject the connection URL into an environment variable;
never paste credentials into command arguments, source control or PR output.

```sh
python tools/db_privilege_audit.py --url-env DATABASE_URL > runtime-privileges.json
python tools/db_privilege_audit.py --url-env MIGRATION_DATABASE_URL > owner-privileges.json
```

The default variable is `DATABASE_URL`. There is deliberately no URL command-line
argument. The JSON contains session/current identity, PostgreSQL version, role
attributes and transitive membership edges (including SET/INHERIT/admin options),
schema/table/sequence owners, effective grants (including PUBLIC/inherited grants),
function ownership/EXECUTE, default ACLs, and all application triggers, including
immutable trigger definitions and enablement (`O` = normally enabled, `D` = disabled).
No table data, connection URLs or passwords are read into the report. The audit
never writes; it uses a REPEATABLE READ, READ ONLY transaction and SELECT catalog
queries. Connection errors are suppressed to avoid leaking URL components.

Exit 0 means the audit completed, **not** that the role is safe. Review
`unsafe_runtime_privileges` (must be empty for runtime), owner/grant expectations,
all expected immutable triggers and their enabled states. The owner's report
should have unsafe-runtime findings because it is intentionally privileged. Save
both reports as restricted operational evidence; they contain object/role names.

## Disposable verification

Set `CIVENSA_TEST_POSTGRES_URL` to a disposable PostgreSQL 16+ test administrator
with CREATEDB/CREATEROLE (the CI service user is a disposable superuser). Never set
it to a pilot/production connection. The new tests create and destroy uniquely
named databases and provision passwords only for their disposable test roles.
Do not run parallel test processes against the same cluster: role names are shared.

```sh
python -m pytest -q --require-postgres tests/test_db_roles.py
python -m pytest -q --require-postgres
python tools/build_bundle.py
```

Normal PR CI runs the full suite on PostgreSQL 16 and 18. Tests apply the SQL twice,
migrate as the owner through CLI and startup, verify ownership/default grants,
read the audit, and exercise authenticated HTTP with the restricted role. They
prove populated immutable-record UPDATE/DELETE failures, and deny TRUNCATE,
disable/drop trigger and ALTER OWNER on every immutable-trigger table, plus schema
CREATE/ownership, SET ROLE and replication-setting bypasses. Login lock writes,
expiry cleanup and success resets, directorate entry, submit, return, correction,
approval, publication and synthetic Word preview/apply run with real login/CSRF.
No Word import implementation changes are required.

## Neon / Render rollout checklist — separate authorization required

Every Neon-specific step below is **to verify during rollout**. These are proposed
operator actions, not claims about tested Neon capabilities or current production.

1. **To verify during rollout — Neon:** identify the exact project/branch/database,
   server version, administrator account, endpoint type and current runtime role.
   Run the read-only audit with the current connection. Review all owners, inherited
   provider roles, PUBLIC grants, default ACLs and trigger state. Confirm that
   `public` contains only Civensa objects; inventory extensions separately.
2. **To verify during rollout — Neon:** create and verify a recoverable backup and
   rehearse this checklist on an isolated restored branch. Confirm a maintenance
   window, who can administer roles/ownership, and that the administrator can run
   the required REVOKE, ALTER ROLE, ALTER SCHEMA and ALTER DEFAULT PRIVILEGES.
   Provider restrictions must be resolved explicitly; do not assume superuser access.
3. **To verify during rollout — Neon:** create `civensa_owner` and `civensa_app` if
   absent (the creation blocks in `ops/db_roles.sql` are idempotent). Where neither
   new role owns existing objects, the full script can bootstrap roles/grants;
   otherwise create the missing roles first and transfer runtime-owned objects
   before running the full script. Do not grant application membership in the owner.
4. **To verify during rollout — Neon:** set separate generated passwords via the
   approved secret-management channel (for example interactive `psql` `\password`
   if supported). Do not put password SQL in files or shell history. Confirm LOGIN
   and direct connections for each role and the required TLS/endpoint settings.
5. **To verify during rollout — Neon:** while application writes are paused, transfer
   **reviewed application objects** to `civensa_owner`: tables/partitions, their
   sequences, views if present and all application function signatures. Review a
   generated ownership script before execution, for example:

   ```sql
   SELECT format('ALTER TABLE %I.%I OWNER TO civensa_owner;', n.nspname, c.relname)
   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') ORDER BY c.relname;
   SELECT format('ALTER SEQUENCE %I.%I OWNER TO civensa_owner;', n.nspname, c.relname)
   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public' AND c.relkind = 'S' ORDER BY c.relname;
   SELECT format('ALTER FUNCTION %I.%I(%s) OWNER TO civensa_owner;',
                 n.nspname, p.proname, pg_get_function_identity_arguments(p.oid))
   FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.prokind = 'f' ORDER BY p.proname;
   ```

   **To verify during rollout — Neon:** distinguish application and extension objects
   in the generated list; transfer tables before their owned sequences. Include
   `alembic_version`, indexes/constraints associated with tables and every trigger
   function in the inventory. Do not blindly use REASSIGN OWNED on a provider/admin
   role: it can affect non-application/shared objects. Ensure `civensa_app` owns
   neither the database nor any schema; database ownership stays with a reviewed
   administrator. Record inverse ownership statements for rollback.
6. **To verify during rollout — Neon:** apply `ops/db_roles.sql` transactionally with
   error-stop enabled (`psql -X --set ON_ERROR_STOP=1 --file ops/db_roles.sql`, using
   secret-managed connection configuration). Rerun the audits. Verify no provider
   memberships or alternate schema/default/parameter grants restore runtime DDL.
   Test repeat application and owner-created future object grants on the rehearsal
   branch. Resolve any permission errors before changing service configuration.
7. **To verify during rollout — Neon connection URLs on Render:** set `DATABASE_URL`
   to the `civensa_app` connection and `MIGRATION_DATABASE_URL` to `civensa_owner`,
   for the same database/schema. Confirm provider endpoint/pooling compatibility
   for migration/session behaviour; do not assume pooled and direct URLs are
   interchangeable. Set secrets in Render's approved interface. A separately
   authorized restart/deploy applies them; this code-only task performs neither.
8. **To verify during rollout — Neon:** verify successful owner migration, runtime
   guard, one Alembic head and audit evidence from the actual runtime identity.
   Confirm trigger enablement and ownership, then smoke-test login, directorate
   entry, review/publication and synthetic import using approved operational data.
   Resume traffic only after the operator accepts results. Record evidence in #4;
   PP-19 remains a deployment gate until this verification is complete.
9. **To verify during rollout — Neon rollback:** pause writes and preserve failure
   logs/audits without secrets. Restore the previous Render variables from the
   secret manager; unset the migration override only as part of the approved
   rollback. If the old connection needs ownership again, execute the reviewed
   inverse ownership/grant script and verify its access before restarting the
   previous application version. Keeping split roles is preferable if rolling back
   only application code. No schema downgrade is required by CIV-012. Restoring the
   old owner/runtime combination reopens PP-19; record that explicitly. Do not
   drop roles, delete data or restore a backup over new writes as a shortcut.
