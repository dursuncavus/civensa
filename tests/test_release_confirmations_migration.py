"""Prove append-only evidence at the database boundary on both supported engines."""
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models import AuditLog, ReleaseConfirmation
from app.release_service import append_confirmation
from tests.conftest import sample as sample_fixture

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.postgres


@pytest.fixture(params=['sqlite', 'postgresql'])
def migrated(request, tmp_path):
    admin = None
    if request.param == 'sqlite':
        url = f'sqlite:///{tmp_path / "release.db"}'
    else:
        admin = create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'], isolation_level='AUTOCOMMIT')
        name = 'civ067_' + uuid4().hex
        with admin.connect() as conn: conn.exec_driver_sql(f'CREATE DATABASE {name}')
        url = make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).set(database=name).render_as_string(hide_password=False)
    env = {**os.environ, 'DATABASE_URL': url}
    env.pop('MIGRATION_DATABASE_URL', None)
    def migrate(*args):
        return subprocess.run([sys.executable, '-m', 'alembic', *args], cwd=ROOT,
            env=env, capture_output=True, text=True)
    engine = create_engine(url)
    try:
        assert migrate('upgrade', 'c063a1b2c3d4').returncode == 0
        # Upgrade over populated current-head data, rather than empty create_all.
        with Session(engine, expire_on_commit=False) as db:
            sample = sample_fixture.__wrapped__(db)
            actor_id, period_id = sample['strategy'].id, sample['period'].id
        assert migrate('upgrade', 'head').returncode == 0
        yield engine, migrate, actor_id, period_id
    finally:
        engine.dispose()
        if admin is not None:
            with admin.connect() as conn: conn.exec_driver_sql(f'DROP DATABASE {name} WITH (FORCE)')
            admin.dispose()


def test_confirmation_is_audited_and_db_rejects_mutation_and_lossy_downgrade(migrated):
    from app.models import ReportingPeriod, User
    engine, migrate, actor_id, period_id = migrated
    with Session(engine, expire_on_commit=False) as db:
        event = append_confirmation(db, db.get(User, actor_id), db.get(ReportingPeriod, period_id),
            dict(item_id='PP-19', decision='confirmed', reason='Yetkili teyidi',
                 evidence='Rol denetim tutanağı', context_sha256='a' * 64), 'a' * 64)
        audit = db.scalar(select(AuditLog).where(AuditLog.action == 'release_manual_confirmation'))
        assert audit.entity_id == event['id'] and 'Rol denetim tutanağı' in audit.details
        row = db.get(ReleaseConfirmation, event['id'])
        row.reason = 'Değişiklik'
        with pytest.raises(ValueError, match='Geçmiş sürüm değiştirilemez'): db.commit()
        db.rollback()
        db.delete(db.get(ReleaseConfirmation, event['id']))
        with pytest.raises(ValueError, match='Geçmiş sürüm değiştirilemez'): db.commit()
        db.rollback()
    statements = ["UPDATE release_confirmations SET reason='değişiklik'", 'DELETE FROM release_confirmations']
    if engine.dialect.name == 'postgresql': statements.append('TRUNCATE release_confirmations CASCADE')
    for statement in statements:
        with pytest.raises(DBAPIError):
            with engine.begin() as conn: conn.execute(text(statement))
    assert migrate('downgrade', 'c063a1b2c3d4').returncode != 0
    with engine.connect() as conn:
        assert conn.execute(text('SELECT reason FROM release_confirmations')).scalar() == 'Yetkili teyidi'
        assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'c067a1b2c3d4'
