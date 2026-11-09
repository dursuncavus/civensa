"""Keep rehearsal writes opt-in and browser logins isolated by account."""
import secrets

import httpx
import pytest

from app.security import hash_password
from scripts.fr_rehearsal import Rehearsal
from scripts.guide_screenshots import GuideError, local_http

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('result', ['OK', 'SLOW'])
def test_only_idare_scope_limit_is_expected_blocker(tmp_path, result):
    rehearsal = Rehearsal('', {}, tmp_path)
    rehearsal.steps = [
        {'step': 'Faaliyet gerçekleşmesi girişi ara', 'result': result}
        for _ in range(3)
    ] + [{'step': 'İdare raporunu onayla ve dondur denemesi', 'result': 'BLOCKER'}]
    rehearsal.check_blockers()


@pytest.mark.parametrize('blockers', [
    [],
    ['Faaliyet gerçekleşmesi girişi ara'],
    ['İdare raporunu onayla ve dondur denemesi', 'Faaliyet gerçekleşmesi girişi ara'],
    ['İdare raporunu onayla ve dondur denemesi', 'Birim raporunu gönder'],
    ['İdare raporunu onayla ve dondur denemesi'] * 2,
])
def test_missing_scope_limit_or_additional_blockers_fail(tmp_path, blockers):
    rehearsal = Rehearsal('', {}, tmp_path)
    rehearsal.steps = [{'step': step, 'result': 'BLOCKER'} for step in blockers]
    with pytest.raises(GuideError, match='İdare kapsam sınırı'):
        rehearsal.check_blockers()


@pytest.mark.parametrize('rehearsal', [False, True])
def test_loopback_write_boundary_and_session_isolation(db, sample, rehearsal):
    password = secrets.token_urlsafe(32)
    for actor in (sample['user'], sample['strategy']):
        actor.password_hash = hash_password(password)
    db.commit()
    data = {'accounts': {'strategy': sample['strategy'].email,
                         'department': sample['user'].email},
            'password': password, 'rehearsal': rehearsal, '_server_errors': []}
    with local_http(db.get_bind(), data) as base, httpx.Client(trust_env=False, headers={'Accept':'text/html'}) as browser:
        def get(account):
            return browser.get(base + '/modules', headers={'X-Guide-Account': account})
        response = get('strategy')
        assert response.status_code == (303 if rehearsal else 200)
        response = browser.post(base + '/login', headers={'X-Guide-Account': 'strategy'},
                                data={'email': sample['strategy'].email, 'password': password})
        assert response.status_code == (303 if rehearsal else 405)
        assert get('strategy').status_code == 200
        assert get('anonymous').status_code == 303
        # UI rehearsal must not borrow a different account's just-opened session.
        assert get('department').status_code == (303 if rehearsal else 200)
        assert get('unknown').status_code == 403
        assert not data['_server_errors']
