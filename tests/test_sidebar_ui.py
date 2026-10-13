"""Real browser layout/interaction checks against the app's local TestClient.

Request routing keeps the existing disposable DB fixture and actual auth/CSRF
handlers, templates and assets, without starting a network server or live DB.
"""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, expect

VIEWPORTS = [(1012, 1103), (1366, 768), (1280, 600), (800, 900), (800, 320)]


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as playwright:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = playwright.chromium.launch(**options)
        yield browser
        browser.close()


@pytest.mark.parametrize('role', ['strategy', 'department'])
@pytest.mark.parametrize('viewport', VIEWPORTS, ids=lambda size: f'{size[0]}x{size[1]}')
def test_sidebar_controls_separate_and_clickable(browser, db, sample, role, viewport):
    from app.main import app
    from app.db import get_db
    from app.security import hash_password

    user = sample['strategy' if role == 'strategy' else 'user']
    user.password_hash = hash_password('sidebar-test-only')
    db.commit()

    def database():
        yield db

    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client, browser.new_context(
            viewport={'width': viewport[0], 'height': viewport[1]}
        ) as context:
            assert client.post('/login', data={
                'email': user.email, 'password': 'sidebar-test-only'
            }, follow_redirects=False).status_code == 303

            logout_redirects = []

            def serve(route):
                request = route.request
                response = client.request(
                    request.method, request.url,
                    content=request.post_data_buffer,
                    headers={'content-type': request.headers.get('content-type', '')},
                    follow_redirects=False,
                )
                # TestClient maintains the signed session cookie across requests.
                headers = dict(response.headers)
                headers.pop('set-cookie', None)
                if request.url.endswith('/logout'):
                    # The real handler has already cleared TestClient's signed
                    # session. Finish this synthetic browser navigation without
                    # following a DNS request to the fake testserver hostname.
                    logout_redirects.append((response.status_code, headers.pop('location', None)))
                    route.fulfill(status=200, headers=headers, body=b'logged out')
                    return
                route.fulfill(status=response.status_code, headers=headers, body=response.content)

            context.route('http://testserver/**', serve)
            page = context.new_page()
            page.goto('http://testserver/modules')
            password = page.get_by_role('button', name='Parolamı Değiştir', exact=True)
            logout = page.get_by_role('button', name='Çıkış', exact=True)
            password.scroll_into_view_if_needed()
            logout.scroll_into_view_if_needed()
            first, second = password.bounding_box(), logout.bounding_box()
            assert first and second
            assert first['y'] + first['height'] <= second['y']
            for control in (password, logout):
                expect(control).to_be_in_viewport()
                assert control.evaluate('(el) => getComputedStyle(el).fontSize') != '0px'
                assert control.evaluate('(el) => el.scrollWidth <= el.clientWidth')
                control.click(trial=True)

            screenshots = os.getenv('CIVENSA_UI_SCREENSHOTS')
            if screenshots and viewport in [(1012, 1103), (1280, 600)]:
                folder = Path(screenshots)
                folder.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(folder / f'{role}-{viewport[0]}x{viewport[1]}.png'))

            password.click()
            expect(page.locator('#passwordModal')).to_be_visible()
            expect(page.locator('#currentPassword')).to_be_focused()
            assert client.get('/modules').status_code == 200
            page.get_by_role('button', name='Vazgeç', exact=True).click()
            expect(page.locator('#passwordModal')).to_be_hidden()
            logout.click()
            assert page.url == 'http://testserver/logout'
            assert logout_redirects == [(303, '/login')]
            assert client.get('/modules').status_code == 401
    finally:
        app.dependency_overrides.clear()
