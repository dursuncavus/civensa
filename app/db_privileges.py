"""Read-only PostgreSQL privilege evidence shared by startup and the operator audit."""
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

# Follow all memberships conservatively, even edges with INHERIT/SET disabled.
ROLES = """
WITH RECURSIVE reachable(oid) AS (
    SELECT oid FROM pg_catalog.pg_roles WHERE rolname IN (current_user, session_user)
    UNION
    SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN reachable r ON m.member = r.oid
)
SELECT r.oid, r.rolname AS name, r.rolsuper AS superuser, r.rolcreatedb AS createdb,
       r.rolcreaterole AS createrole, r.rolreplication AS replication,
       r.rolbypassrls AS bypassrls, r.rolinherit AS inherit, r.rolcanlogin AS login
FROM pg_catalog.pg_roles r JOIN reachable x ON x.oid = r.oid ORDER BY r.rolname
"""
USER_SCHEMA = "n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'"


def privilege_snapshot(connection):
    """SELECT catalog data only. Caller must start a READ ONLY transaction."""
    def rows(sql, **params):
        return [dict(row) for row in connection.execute(text(sql), params).mappings()]

    # MAINTAIN was introduced in PostgreSQL 17; PG16 rejects that privilege name.
    maintain = ",'MAINTAIN'" if connection.dialect.server_version_info >= (17,) else ""
    dangerous_table_grants = 'TRUNCATE,TRIGGER' + (',MAINTAIN' if maintain else '')
    identity = rows("SELECT current_user AS role, session_user AS session_role, "
                    "current_setting('server_version') AS server_version, "
                    "current_setting('transaction_read_only') AS read_only")[0]
    roles = rows(ROLES)
    database = rows("""
        SELECT pg_catalog.pg_get_userbyid(d.datdba) AS owner,
               pg_catalog.has_database_privilege(d.oid, 'CONNECT') AS connect,
               pg_catalog.has_database_privilege(d.oid, 'CREATE') AS create,
               pg_catalog.has_database_privilege(d.oid, 'TEMPORARY') AS temporary
        FROM pg_catalog.pg_database d WHERE d.datname = current_database()
    """)[0]
    members = rows("""
        SELECT parent.rolname AS role, child.rolname AS member, m.admin_option,
               m.inherit_option, m.set_option
        FROM pg_catalog.pg_auth_members m
        JOIN pg_catalog.pg_roles parent ON parent.oid = m.roleid
        JOIN pg_catalog.pg_roles child ON child.oid = m.member
        WHERE m.member = ANY(:oids) ORDER BY child.rolname, parent.rolname
    """, oids=[r['oid'] for r in roles])
    schemas = rows(f"""
        SELECT n.nspname AS name, pg_catalog.pg_get_userbyid(n.nspowner) AS owner,
               pg_catalog.has_schema_privilege(n.oid, 'USAGE') AS usage,
               pg_catalog.has_schema_privilege(n.oid, 'CREATE') AS create
        FROM pg_catalog.pg_namespace n WHERE {USER_SCHEMA} ORDER BY n.nspname
    """)
    relations = rows(f"""
        SELECT n.nspname AS schema, c.relname AS name, c.relkind AS kind,
               pg_catalog.pg_get_userbyid(c.relowner) AS owner,
               ARRAY(SELECT p FROM unnest(CASE WHEN c.relkind = 'S'
                     THEN ARRAY['USAGE','SELECT','UPDATE']
                     ELSE ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'{maintain}] END) p
                     WHERE CASE WHEN c.relkind = 'S'
                       THEN pg_catalog.has_sequence_privilege(c.oid, p)
                       ELSE pg_catalog.has_table_privilege(c.oid, p) END) AS grants
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE {USER_SCHEMA} AND c.relkind IN ('r','p','v','m','f','S')
        ORDER BY n.nspname, c.relname
    """)
    routines = rows(f"""
        SELECT n.nspname AS schema, p.proname AS name,
               pg_catalog.pg_get_function_identity_arguments(p.oid) AS arguments,
               pg_catalog.pg_get_userbyid(p.proowner) AS owner, p.prosecdef AS security_definer,
               pg_catalog.has_function_privilege(p.oid, 'EXECUTE') AS execute
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE {USER_SCHEMA} ORDER BY n.nspname, p.proname, arguments
    """)
    triggers = rows(f"""
        SELECT n.nspname AS schema, c.relname AS table, t.tgname AS name,
               t.tgenabled AS enabled, pg_catalog.pg_get_triggerdef(t.oid) AS definition
        FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE {USER_SCHEMA} AND NOT t.tgisinternal ORDER BY n.nspname, c.relname, t.tgname
    """)
    defaults = rows("""
        SELECT pg_catalog.pg_get_userbyid(d.defaclrole) AS owner,
               COALESCE(n.nspname, '*') AS schema, d.defaclobjtype AS kind,
               d.defaclacl::text AS acl
        FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
        ORDER BY owner, schema, kind
    """)
    # Check each reachable role as well as current effective privileges: NOINHERIT
    # does not prevent SET ROLE. This never executes a DDL probe.
    risks = []
    for role in roles:
        name = role['name']
        if name in {'civensa_owner', 'pg_execute_server_program', 'pg_write_server_files',
                    'pg_read_server_files'} or any(role[k] for k in ('superuser','createdb','createrole','replication','bypassrls')):
            risks.append(f"privileged role: {name}")
        for risk in rows(f"""
            SELECT 'database ownership/CREATE/TEMPORARY' AS reason FROM pg_catalog.pg_database d
              WHERE d.datname = current_database() AND
              (d.datdba = :oid OR pg_catalog.has_database_privilege(:oid, d.oid, 'CREATE,TEMPORARY'))
            UNION ALL
            SELECT 'schema ownership/CREATE: ' || n.nspname FROM pg_catalog.pg_namespace n
              WHERE {USER_SCHEMA} AND (n.nspowner = :oid OR pg_catalog.has_schema_privilege(:oid, n.oid, 'CREATE'))
            UNION ALL
            SELECT 'relation ownership: ' || n.nspname || '.' || c.relname
              FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
              WHERE {USER_SCHEMA} AND c.relowner = :oid
            UNION ALL
            SELECT 'dangerous table grants: ' || n.nspname || '.' || c.relname
              FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
              WHERE {USER_SCHEMA} AND c.relkind IN ('r','p','f')
              AND pg_catalog.has_table_privilege(:oid, c.oid, :dangerous_table_grants)
            UNION ALL
            SELECT 'type ownership: ' || n.nspname || '.' || t.typname
              FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
              WHERE {USER_SCHEMA} AND t.typowner = :oid AND t.typrelid = 0
            UNION ALL
            SELECT 'routine ownership/SECURITY DEFINER: ' || n.nspname || '.' || p.proname
              FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
              WHERE {USER_SCHEMA} AND (p.proowner = :oid OR
              (p.prosecdef AND pg_catalog.has_function_privilege(:oid, p.oid, 'EXECUTE')))
            UNION ALL
            SELECT 'SET/ALTER SYSTEM session_replication_role' WHERE
              pg_catalog.has_parameter_privilege(:oid, 'session_replication_role', 'SET,ALTER SYSTEM')
        """, oid=role['oid'], dangerous_table_grants=dangerous_table_grants):
            risks.append(f"{name}: {risk['reason']}")
    for role in roles:
        role.pop('oid')
    return dict(**identity, database=database, roles=roles, memberships=members, schemas=schemas,
                relations=relations, routines=routines, triggers=triggers,
                default_privileges=defaults, unsafe_runtime_privileges=sorted(set(risks)))


def audit_engine(engine):
    if engine.dialect.name != 'postgresql':
        raise ValueError('PostgreSQL 16+ is required for the database privilege audit')
    with engine.connect() as connection:
        with connection.begin():
            connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            if connection.dialect.server_version_info < (16,):
                raise ValueError('PostgreSQL 16+ is required for the database privilege audit')
            return privilege_snapshot(connection)


def assert_runtime_restricted(engine):
    message = ('MIGRATION_DATABASE_URL ayarlı ancak DATABASE_URL rolü güvenli değil. '
               'Çalışma rolünün sahiplik, DDL ve yönetim yetkilerini kaldırın; '
               'tools/db_privilege_audit.py ile doğrulayın.')
    try:
        snapshot = audit_engine(engine)
    except Exception:
        logger.error('%s Yetki denetimi tamamlanamadı.', message)
        raise RuntimeError(message + ' Yetki denetimi tamamlanamadı.') from None
    if snapshot['unsafe_runtime_privileges']:
        logger.error('%s Bulgular: %s', message, '; '.join(snapshot['unsafe_runtime_privileges']))
        raise RuntimeError(message)
