"""Run operational-script regressions on their explicitly pinned migration schema."""
from contextlib import contextmanager
from alembic import command
from alembic.config import Config
from scripts import first_load_live as live
from scripts.first_load_dryrun import disposable_database, environment


@contextmanager
def disposable_first_load_database(url):
    # The repository-head equality test forces review when a migration is added.
    # Keep the target at the operator pin even during that future review.
    with disposable_database(url) as engine:
        rendered = engine.url.render_as_string(hide_password=False)
        with environment(DATABASE_URL=rendered, MIGRATION_DATABASE_URL=rendered):
            command.downgrade(Config(str(live.ROOT / 'alembic.ini')), live.HEAD)
        yield engine


# Compatibility for the existing cleanup regression module.
disposable_release50_database = disposable_first_load_database
