"""D-396: loader failure reasons carry schema names and code location, never row values."""
from types import SimpleNamespace

from scripts import first_load_live as live


class FakeDBError(Exception):
    pass


def raise_here(exc):
    raise exc


def test_failure_detail_keeps_schema_names_and_drops_message_text():
    orig = SimpleNamespace(sqlstate='23505', diag=SimpleNamespace(
        table_name='official_activities', constraint_name='uq_official_activity_key',
        column_name=None))
    exc = FakeDBError('duplicate key value (name)=(Gizli Değer 123) postgresql://user:secret@host/db')
    exc.orig = orig
    try:
        raise_here(exc)
    except FakeDBError as caught:
        detail = live.failure_detail(caught)
    assert detail.startswith('FakeDBError, SQLSTATE 23505, tablo official_activities, kısıt uq_official_activity_key')
    assert 'konum tests/test_first_load_failure_detail.py:' in detail
    assert 'Gizli' not in detail and 'secret' not in detail and 'postgresql' not in detail


def test_failure_detail_rejects_non_identifier_diag_values():
    orig = SimpleNamespace(pgcode='bad code!', diag=SimpleNamespace(
        table_name='x; DROP', constraint_name='Has Space', column_name='name'))
    exc = KeyError('payload-value')
    exc.orig = orig
    detail = live.failure_detail(exc)
    assert detail == 'KeyError, sütun name'
