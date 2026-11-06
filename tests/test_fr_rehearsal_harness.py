"""Keep rehearsal writes opt-in and browser logins isolated by account."""
import secrets

import httpx
import pytest

from app.security import hash_password
from scripts.guide_screenshots import local_http

pytestmark = pytest.mark.postgres


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
