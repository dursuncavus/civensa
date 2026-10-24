"""Worker-local, pristine database templates for disposable PostgreSQL tests.

Each test gets a physical clone, so commits, independent connections, triggers
and migration round trips keep their real behavior without sharing test state.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema

from app.db import Base


class PostgresTemplates:
    def __init__(self, url):
        self.url = make_url(url)
        if self.url.get_backend_name() != 'postgresql':
            raise ValueError('CIVENSA_TEST_POSTGRES_URL must use PostgreSQL')
        self.admin = create_engine(self.url, isolation_level='AUTOCOMMIT', hide_parameters=True)
        self.templates = {}
        self.databases = set()

    def create(self, template=None):
        name = 'civensa_test_' + uuid4().hex
        statement = sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name))
        if template:
            statement += sql.SQL(' TEMPLATE {}').format(sql.Identifier(template))
        with self.admin.connect() as connection:
            connection.exec_driver_sql(statement.as_string())
        self.databases.add(name)
        return name

    def drop(self, name):
        with self.admin.connect() as connection:
            connection.exec_driver_sql(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(
                sql.Identifier(name)).as_string())
        self.databases.remove(name)

    def template(self, revision):
        # None means create_all, preserving the ORM fixture's existing behavior.
        if revision not in self.templates:
            name = self.create()
            schema = 'civensa_test_' + uuid4().hex
            url = self.url.set(database=name)
            engine = create_engine(url, hide_parameters=True)
            try:
                with engine.begin() as connection:
                    connection.execute(CreateSchema(schema))
                if revision is None:
                    Base.metadata.create_all(engine.execution_options(schema_translate_map={None: schema}))
                else:
                    scoped = url.update_query_dict({'options': '-csearch_path=' + schema})
                    result = subprocess.run(
                        [sys.executable, '-m', 'alembic', 'upgrade', revision],
                        cwd=Path(__file__).resolve().parents[1],
                        env={**os.environ, 'DATABASE_URL': scoped.render_as_string(hide_password=False)},
                        capture_output=True, text=True)
                    assert result.returncode == 0, result.stderr
            finally:
                engine.dispose()
            self.templates[revision] = name, schema
        return self.templates[revision]

    @contextmanager
    def clone(self, revision=None):
        template, schema = self.template(revision)
        name = self.create(template)
        url = self.url.set(database=name)
        if revision is not None:
            url = url.update_query_dict({'options': '-csearch_path=' + schema})
        engine = create_engine(url, hide_parameters=True)
        if revision is None:
            engine = engine.execution_options(schema_translate_map={None: schema})
        try:
            yield engine
        finally:
            engine.dispose()
            self.drop(name)

    def close(self):
        try:
            for name in list(self.databases):
                self.drop(name)
        finally:
            self.admin.dispose()
