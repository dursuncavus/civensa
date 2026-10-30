"""Keep operational-script regressions on their explicitly supported release schema."""
from contextlib import contextmanager
from unittest.mock import patch
from sqlalchemy import MetaData, inspect
from app.db import Base
from alembic import command
from alembic.config import Config
from scripts import first_load_live as live
from scripts.first_load_dryrun import disposable_database, environment


@contextmanager
def disposable_release50_database(url):
    # The generic scratch helper follows Alembic head. These operational tools
    # deliberately refuse anything except live.HEAD; a new application migration
    # must not silently widen their production schema contract.
    with disposable_database(url) as engine:
        rendered = engine.url.render_as_string(hide_password=False)
        with environment(DATABASE_URL=rendered, MIGRATION_DATABASE_URL=rendered):
            command.downgrade(Config(str(live.ROOT / 'alembic.ini')), live.HEAD)
        # The clear script enumerates the model metadata for locks/FK guards.
        # Present the exact historical table set without adding new application
        # tables to a database that deliberately remains at the old checkpoint.
        names = set(inspect(engine).get_table_names())
        checkpoint = MetaData()
        # Reflect columns and references too: copying today's models can retain
        # a new FK to a table deliberately absent at this historical checkpoint.
        checkpoint.reflect(bind=engine, only=sorted(names & set(Base.metadata.tables)))
        with patch.object(Base, 'metadata', checkpoint):
            yield engine
