"""CIV-221: read-only pilot inventory of accounts and directorate data; local PG only."""
from datetime import date, datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models as m
from scripts import pilot_inventory as inventory
from scripts.first_load_dryrun import local_test_url
from tests.first_load_checkpoint import disposable_first_load_database


def snapshot(engine):
    from app.db import Base
    with engine.connect() as connection:
        return {t.name: connection.scalar(select(func.count()).select_from(t))
                for t in Base.metadata.sorted_tables
                if connection.dialect.has_table(connection, t.name)}


def test_inventory_lists_accounts_references_and_directorate_rows_without_writing():
    with disposable_first_load_database(local_test_url()) as engine:
        with Session(engine) as db:
            org = m.Organization(name='CIV-221 disposable')
            db.add(org)
            db.flush()
            fen, afet = (m.Department(organization_id=org.id, name=n) for n in ('Fen İşleri', 'Afet'))
            db.add_all([fen, afet])
            db.flush()
            strategy = m.User(email='strateji@example.invalid', full_name='Strateji Kişi', role='strategy',
                              password_hash='x')
            used = m.User(email='fen.mudur@civensa.local', full_name='Fen Test', role='department',
                          department_id=fen.id, position='director', password_hash='x')
            unused = m.User(email='afet@civensa.local', full_name='Afet Test', role='department',
                            department_id=afet.id, password_hash='x', is_active=False)
            db.add_all([strategy, used, unused])
            db.flush()
            period = m.ReportingPeriod(year=2026, status='draft', template_status='verified')
            db.add(period)
            db.flush()
            program = m.Program(period_id=period.id, name='P')
            db.add(program)
            db.flush()
            sub = m.SubProgram(period_id=period.id, program_id=program.id, name='S')
            db.add(sub)
            db.flush()
            db.add(m.Indicator(period_id=period.id, subprogram_id=sub.id, department_id=fen.id,
                               code='G1', name='Gösterge', unit='Adet'))
            db.add(m.AuditLog(user_id=used.id, action='login', entity_type='user', entity_id=used.id,
                              created_at=datetime(2026, 11, 10, 9, 30)))
            change = m.StructureChange(change_type='RENAMED', effective_date=date(2026, 1, 1),
                                       council_decision_no='1', council_decision_date=date(2026, 1, 1),
                                       snapshot_json='{}', created_by=strategy.id)
            db.add(change)
            db.flush()
            db.add_all([m.StructureChangeLink(change_id=change.id, from_department_id=afet.id, to_department_id=fen.id),
                        m.StructureChangeLink(change_id=change.id, from_department_id=fen.id, to_department_id=afet.id)])
            db.commit()
            ids = dict(strategy=strategy.id, used=used.id, unused=unused.id, fen=fen.id, afet=afet.id)

        before = snapshot(engine)
        result = inventory.execute(engine)
        assert snapshot(engine) == before

        users = {u['id']: u for u in result['users']}
        assert users[ids['used']]['last_login'] == datetime(2026, 11, 10, 9, 30)
        assert users[ids['used']]['references'] == {'audit_log.user_id': 1}
        assert users[ids['unused']]['reference_total'] == 0
        assert users[ids['unused']]['active'] is False
        assert users[ids['strategy']]['last_login'] is None
        assert result['data'][ids['fen']]['indicators'] == (1, 1)
        # Two directorate FKs on one table are reported per column, never overwritten.
        assert result['data'][ids['fen']]['structure_change_links.from_department_id'] == (1, 0)
        assert result['data'][ids['fen']]['structure_change_links.to_department_id'] == (1, 0)
        assert 'indicators' not in result['data'][ids['afet']]

        report = inventory.format_report(result)
        assert 'fen.mudur@civensa.local' in report and 'Fen İşleri: 3 / 1' in report
        assert report.endswith('Hedefe 0 satır yazıldı (salt okunur).')


def test_inventory_refuses_wrong_schema():
    with disposable_first_load_database(local_test_url()) as engine:
        with engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num = 'c197a1b2c3d4'"))
        try:
            inventory.execute(engine)
        except inventory.live.Refusal as exc:
            assert 'c219b1c2d3e4' in str(exc)
        else:
            raise AssertionError('wrong schema must refuse')
