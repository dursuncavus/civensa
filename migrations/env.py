from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db import Base, normalize_database_url
from app import models  # noqa: F401 - import models so metadata is populated

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Optional owner connection for migrations; requests remain on DATABASE_URL.
database_url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", normalize_database_url(database_url).replace("%", "%%"))

target_metadata = Base.metadata


def restrict_migration_metadata() -> None:
    # Default table grants also apply when Alembic first creates its version
    # table. Requests only need to read it for readiness, never change history.
    if os.getenv("MIGRATION_DATABASE_URL") and context.get_context().dialect.name == "postgresql":
        context.execute("""DO $$ BEGIN
            IF to_regclass('alembic_version') IS NOT NULL
               AND EXISTS (SELECT FROM pg_roles WHERE rolname = 'civensa_app') THEN
                REVOKE INSERT, UPDATE, DELETE ON alembic_version FROM civensa_app;
            END IF;
        END $$""")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
        restrict_migration_metadata()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
            restrict_migration_metadata()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
