"""Global native-form feedback classification, including errors and fetches."""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.testclient import TestClient
import pytest
from starlette.middleware.sessions import SessionMiddleware

from app.main import SavedNoticeMiddleware

NOTICE = '<div id="saved-notice" role="status" hidden>Kaydedildi.</div>'


@pytest.fixture
def notices():
    app = FastAPI()
    app.add_middleware(SavedNoticeMiddleware)
    app.add_middleware(SessionMiddleware, secret_key='synthetic-civ201-test-only')

    @app.post('/save')
    async def save():
        return RedirectResponse('/next?tab=budget', 303)

    @app.post('/invalid')
    async def invalid():
        return HTMLResponse(NOTICE, status_code=422)

    @app.post('/api/save')
    async def api():
        return RedirectResponse('/next?tab=budget', 303)

    @app.get('/next')
    async def next_page(request: Request):
        return HTMLResponse(NOTICE, status_code=int(request.headers.get('x-test-status', '200')))

    with TestClient(app) as client:
        yield client


def visible(response):
    return ' hidden>' not in response.text


def test_success_is_server_rendered_once(notices):
    assert notices.post('/save', data={'value': '0'}, follow_redirects=False).status_code == 303
    result = notices.get('/next?tab=budget')
    assert visible(result)
    assert 'role="status"' in result.text and 'Kaydedildi.' in result.text
    assert len(result.content) == int(result.headers['content-length'])
    assert not visible(notices.get('/next?tab=budget'))


@pytest.mark.parametrize('status', [400, 401, 403, 404, 422, 500])
def test_redirect_destination_error_never_claims_success(notices, status):
    notices.post('/save', data={'value': '0'}, follow_redirects=False)
    result = notices.get('/next?tab=budget', headers={'x-test-status': str(status)})
    assert result.status_code == status and not visible(result)
    assert not visible(notices.get('/next?tab=budget'))


@pytest.mark.parametrize('headers,payload', [
    ({'Sec-Fetch-Mode': 'cors'}, {'data': {'value': '0'}}),
    ({'Accept': 'application/json'}, {'data': {'value': '0'}}),
    ({'X-Requested-With': 'XMLHttpRequest'}, {'data': {'value': '0'}}),
    ({}, {'json': {'value': 0}}),
])
def test_fetch_and_json_do_not_set_notice(notices, headers, payload):
    notices.post('/save', headers=headers, follow_redirects=False, **payload)
    assert not visible(notices.get('/next?tab=budget'))


def test_api_post_and_failed_form_do_not_set_notice(notices):
    notices.post('/api/save', data={'value': '0'}, follow_redirects=False)
    assert not visible(notices.get('/next?tab=budget'))
    assert not visible(notices.post('/invalid', data={'value': 'invalid'}))
    assert not visible(notices.get('/next?tab=budget'))


def test_notice_is_bound_to_redirect_destination(notices):
    notices.post('/save', data={'value': '0'}, follow_redirects=False)
    assert not visible(notices.get('/next?tab=other'))
    assert not visible(notices.get('/next?tab=budget'))
