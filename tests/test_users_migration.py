"""CIV-044 upgrade from actual populated #41 schemas; lossless re-upgrade."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend', ['postgres', 'sqlite'])
def test_populated_personal_password_upgrade_and_lossless_downgrade(tmp_path, backend):
    scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    assert scripts.get_heads() == ['c044a1b2c3d4']
    assert scripts.get_revision('c044a1b2c3d4').down_revision == 'c031b1a2c3d4'
    admin = None
    if backend == 'postgres':
        admin = create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
        schema = 'civ044_migration_' + uuid4().hex
        with admin.begin() as conn: conn.execute(CreateSchema(schema))
        url = make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict(
            {'options': '-csearch_path=' + schema}).render_as_string(hide_password=False)
    else:
        url = f'sqlite:///{tmp_path / "passwords.db"}'
    engine = create_engine(url)
    def migrate(direction, revision):
        result = subprocess.run([sys.executable, '-m', 'alembic', direction, revision], cwd=ROOT,
                                env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    try:
        migrate('upgrade', 'c031b1a2c3d4')
        assert 'must_change_password' not in {c['name'] for c in inspect(engine).get_columns('users')}
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash) VALUES (1,'existing@example.invalid','Eski Kullanıcı','strategy','preserved-hash')"))
        migrate('upgrade', 'head')
        with engine.begin() as conn:
            saved = conn.execute(text('SELECT id,email,password_hash,must_change_password FROM users')).one()
            assert saved[:3] == (1, 'existing@example.invalid', 'preserved-hash') and not saved[3]
            conn.execute(text('UPDATE users SET must_change_password=true WHERE id=1'))
        migrate('downgrade', 'c031b1a2c3d4')
        migrate('upgrade', 'head')
        with engine.connect() as conn:
            assert conn.execute(text('SELECT COUNT(*) FROM users')).scalar() == 1
            assert conn.execute(text('SELECT must_change_password FROM users WHERE id=1')).scalar()
            assert conn.execute(text('SELECT password_hash FROM users WHERE id=1')).scalar() == 'preserved-hash'
        assert 'uq_active_department_director' in {i['name'] for i in inspect(engine).get_indexes('users')}
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as conn: conn.execute(DropSchema(schema, cascade=True))
            admin.dispose()
