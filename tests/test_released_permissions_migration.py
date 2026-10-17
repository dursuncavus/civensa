"""35-user pilot upgrade, database uniqueness, and non-destructive rollback."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend', ['sqlite', 'postgres'])
def test_civ025_pilot_upgrade_downgrade_reupgrade(tmp_path, backend):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    assert scripts.get_heads() == ['c025a1b2c3d4']
    assert scripts.get_revision('c025a1b2c3d4').down_revision == 'b8d011e6f420'
    admin = None
    if backend == 'postgres':
        admin = create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
        schema = 'civ025_migration_' + uuid4().hex
        with admin.begin() as conn:
            conn.execute(CreateSchema(schema))
        url = make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict(
            {'options': '-csearch_path='+schema}).render_as_string(hide_password=False)
    else:
        url = f'sqlite:///{tmp_path / "pilot.db"}'
    engine = create_engine(url)
    def migrate(command, revision):
        result = subprocess.run([sys.executable, '-m', 'alembic', command, revision], cwd=ROOT,
                                env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    try:
        migrate('upgrade', 'b8d011e6f420')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations (id,name) VALUES (1,'Test Belediyesi')"))
            conn.execute(text("INSERT INTO reporting_periods (id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO departments (id,organization_id,name) VALUES (1,1,'Test Müdürlüğü')"))
            for i in range(1, 36):
                conn.execute(text('INSERT INTO users (id,email,full_name,role,password_hash,department_id,is_active) '
                                  'VALUES (:id,:email,:name,:role,:hash,:did,:active)'),
                             {'id': i, 'email': f'user{i}@example.invalid', 'name': f'Kullanıcı {i}',
                              'role': 'strategy' if i == 35 else 'department', 'hash': 'preserve-hash',
                              'did': None if i == 35 else 1, 'active': i != 34})
        migrate('upgrade', 'head')
        with engine.begin() as conn:
            users = conn.execute(text('SELECT * FROM users ORDER BY id')).mappings().all()
            assert len(users) == 35 and all(u['position'] == 'staff' for u in users)
            assert all(u['can_submit'] for u in users[:34]) and not users[34]['can_submit']
            assert users[34]['department_id'] and all(u['password_hash'] == 'preserve-hash' for u in users)
            assert not users[33]['is_active']
            assert conn.execute(text("SELECT status FROM department_scopes WHERE department_id = :did"), {'did': users[34]['department_id']}).scalar() == 'excluded'
            assert conn.execute(text("SELECT COUNT(*) FROM audit_log WHERE action = 'user_position_change'")).scalar() == 35
            assert conn.execute(text("SELECT COUNT(*) FROM audit_log WHERE action = 'user_can_submit_change'")).scalar() == 35
            conn.execute(text("UPDATE users SET position = 'director' WHERE id = 1"))
            conn.execute(text('UPDATE users SET can_submit = false WHERE id = 2'))
            conn.execute(text("INSERT INTO users (id,email,full_name,role,password_hash,department_id,is_active) "
                              "VALUES (36,'new@example.invalid','Yeni','department','unused',1,true)"))
            assert not conn.execute(text('SELECT can_submit FROM users WHERE id = 36')).scalar()
        with pytest.raises(IntegrityError), engine.begin() as conn:
            conn.execute(text("UPDATE users SET position = 'director' WHERE id = 2"))
        migrate('downgrade', 'b8d011e6f420')
        with engine.connect() as conn:
            assert conn.execute(text('SELECT COUNT(*) FROM users')).scalar() == 36
            assert conn.execute(text('SELECT position FROM users WHERE id = 1')).scalar() == 'director'
            assert not conn.execute(text('SELECT can_submit FROM users WHERE id = 2')).scalar()
        migrate('upgrade', 'head')
        with engine.connect() as conn:
            assert conn.execute(text('SELECT COUNT(*) FROM users')).scalar() == 36
            assert conn.execute(text('SELECT position FROM users WHERE id = 1')).scalar() == 'director'
            assert not conn.execute(text('SELECT can_submit FROM users WHERE id = 2')).scalar()
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as conn:
                conn.execute(DropSchema(schema, cascade=True))
            admin.dispose()
