-- CIV-012. PostgreSQL 16+; run as a role administrator in the dedicated Civensa DB.
-- No passwords here. Review docs/operations/db-roles.md before an existing DB rollout.
-- Existing application objects must already belong to civensa_owner (see checklist).
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'civensa_owner') THEN
        CREATE ROLE civensa_owner LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'civensa_app') THEN
        CREATE ROLE civensa_app LOGIN;
    END IF;
END $$;
ALTER ROLE civensa_owner NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE civensa_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;
-- Remove every membership, including NOINHERIT/SET ROLE paths to an owner/admin.
DO $$
DECLARE membership record;
BEGIN
    FOR membership IN
        SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.roleid
        WHERE m.member = 'civensa_app'::regrole
    LOOP
        EXECUTE format('REVOKE %I FROM civensa_app', membership.rolname);
    END LOOP;
    IF EXISTS (SELECT FROM pg_database WHERE datdba = 'civensa_app'::regrole)
       OR EXISTS (SELECT FROM pg_namespace WHERE nspowner = 'civensa_app'::regrole)
       OR EXISTS (SELECT FROM pg_class WHERE relowner = 'civensa_app'::regrole)
       OR EXISTS (SELECT FROM pg_proc WHERE proowner = 'civensa_app'::regrole) THEN
        RAISE EXCEPTION 'civensa_app still owns objects; transfer ownership before applying db_roles.sql';
    END IF;
    EXECUTE format('REVOKE CREATE, TEMPORARY ON DATABASE %I FROM PUBLIC, civensa_app', current_database());
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO civensa_owner, civensa_app', current_database());
    EXECUTE format('GRANT TEMPORARY ON DATABASE %I TO civensa_owner', current_database());
END $$;
ALTER SCHEMA public OWNER TO civensa_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC, civensa_app;
GRANT USAGE ON SCHEMA public TO civensa_app;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC, civensa_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO civensa_app;
DO $$
BEGIN
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        REVOKE INSERT, UPDATE, DELETE ON public.alembic_version FROM civensa_app;
    END IF;
END $$;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC, civensa_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO civensa_app;
-- These are SECURITY INVOKER functions used by application triggers and helpers.
-- Future SECURITY DEFINER routines require separate review; the startup guard rejects them.
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC, civensa_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO civensa_app;
REVOKE SET, ALTER SYSTEM ON PARAMETER session_replication_role FROM civensa_app;

-- Global revokes matter: schema-local REVOKE cannot cancel a global default grant.
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner REVOKE ALL ON TABLES FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner REVOKE ALL ON SEQUENCES FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM PUBLIC, civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO civensa_app;
ALTER DEFAULT PRIVILEGES FOR ROLE civensa_owner IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO civensa_app;
COMMIT;
