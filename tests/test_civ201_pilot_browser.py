"""CIV-201: full synthetic seed, native dialogs, real form redirects and CSP.

Page reads use TestClient with a disposable PostgreSQL clone. Chromium loads
real templates/assets; native submits use a real loopback Uvicorn server.
"""
import json
import os
from pathlib import Path
import re
import socket
import threading
import time

from fastapi.testclient import TestClient
from playwright.sync_api import expect
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import ARDocument, Publication, User
from app.security import hash_password
from scripts.profile_strateji_steps import seed
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
PAGES = [
    ('source-comparison', '/source-comparison?period_id=1', 33),
    ('operations', '/operations?period_id=1', 34),
    ('indicator-report', '/activity-reports/revisions/1', 33),
    ('financial-overview', '/activity-sections/reports/1?code=III.A', 34),
    ('financial-budget', '/activity-sections/reports/1?code=III.A.1', 34),
]


def token(client):
    return re.search(r'name="csrf_token" value="([^"]+)"', client.get('/modules').text).group(1)


@pytest.fixture(scope='module')
def full_seed(postgres_templates):
    with postgres_templates.clone() as translated:
        schema = translated.get_execution_options()['schema_translate_map'][None]
        engine = create_engine(translated.url.update_query_dict({'options': '-csearch_path=' + schema}))
        result = seed(engine, tiny=False)
        assert result['counts'] == dict(cards=105, indicators=226, activities=182, economic_values=1270)
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
            connection.execute(text('INSERT INTO alembic_version VALUES (:head)'), {'head': main.migration_head()})
        with Session(engine, expire_on_commit=False) as db:
            # Creating a report revision requires a Strategy staff member.
            db.add(User(email='editor@example.invalid', full_name='SENTETİK Editör', role='strategy',
                        department_id=1, password_hash=hash_password('Civ201-local-test-only!')))
            db.commit()
        try:
            yield engine
        finally:
            engine.dispose()


@pytest.fixture
def pilot_client(full_seed, monkeypatch):
    monkeypatch.setattr(main, 'engine', full_seed)
    with Session(full_seed, expire_on_commit=False) as db:
        def database():
            yield db
        main.app.dependency_overrides[get_db] = database
        client = TestClient(main.app, follow_redirects=False)
        try:
            login = client.post('/login', data={'email': 'strategy@example.invalid', 'password': 'Civ196-local-test-only!'})
            assert login.status_code == 303
            csrf = token(client)
            if not db.scalar(select(Publication)):
                data = dict(period_id=1, organization_id=1, csrf_token=csrf,
                            approval_reference='SENTETİK CIV-201; gerçek meclis kararı değildir.')
                assert client.post('/report-builder/publish-approved-book', data=data).status_code == 303
                assert client.post('/activity-sections/years', data=data).status_code == 303
                assert client.post('/login', data={'email': 'editor@example.invalid', 'password': 'Civ201-local-test-only!'}).status_code == 303
                assert client.post('/activity-reports/revisions', data={'publication_id': 1, 'organization_id': 1, 'csrf_token': token(client)}).status_code == 303
                assert client.post('/login', data={'email': 'strategy@example.invalid', 'password': 'Civ196-local-test-only!'}).status_code == 303
                token(client)
            yield client, db
        finally:
            client.close()
            main.app.dependency_overrides.clear()


def bridge(context, client, writes):
    documents = {}
    def serve(route):
        request = route.request
        response = client.request(request.method, request.url, content=request.post_data_buffer,
            headers={key: value for key, value in request.headers.items()
                     if key in {'content-type', 'accept', 'sec-fetch-mode', 'x-requested-with', 'x-csrf-token'}},
            follow_redirects=False)
        if hasattr(response, 'context'):
            documents[request.url] = response
        if request.method == 'POST':
            writes.append((request.url, response.status_code))
        headers = dict(response.headers)
        headers.pop('set-cookie', None)  # TestClient owns the signed server session.
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)
    return documents


@pytest.mark.parametrize('name,url,count', PAGES, ids=[page[0] for page in PAGES])
def test_full_seed_cards_dialogs_search_and_height(browser, pilot_client, name, url, count):
    client, _ = pilot_client
    with browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1) as context:
        documents = bridge(context, client, [])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        response = page.goto('http://testserver' + url, timeout=180000)
        assert response.status == 200
        page.evaluate('document.fonts.ready')
        server = documents['http://testserver' + url]
        if name == 'source-comparison':
            assert page.locator('[data-subtotal-level]').count() == len(server.context['reconciliation'])
            assert page.locator('.source-comparison-table tr[data-status]').count() == len(server.context['comparison']['rows'])
        elif name == 'operations':
            release = server.context['readiness']['release']
            assert page.locator('[data-check-id]').count() == len(release['automatic']) + len(release['manual'])
        elif name == 'indicator-report':
            assert page.locator('[data-actual-form]').count() == len(server.context['report']['indicators'])
        cards = page.locator('[data-directorate-card]')
        expect(cards).to_have_count(count)
        assert page.evaluate('document.documentElement.scrollHeight') < 7200
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('script:not([src]):not([type="application/json"])').count() == 0
        assert page.locator('*').evaluate_all("els => els.every(el => [...el.attributes].every(a => !/^on/i.test(a.name)))")
        assert "script-src 'self'" in response.headers['content-security-policy']
        # Representative dialogs across the grid use showModal, trap focus and
        # restore the trigger. Every card has its own matching unique dialog ID.
        targets = cards.locator('[data-open-dialog]').evaluate_all('els => els.map(el => el.dataset.openDialog)')
        assert len(set(targets)) == count
        assert all(page.locator('[id="' + target + '"]').count() == 1 for target in targets)
        for index in (0, count // 2, count - 1):
            trigger = cards.nth(index).get_by_role('button', name='Ayrıntıyı aç')
            target = trigger.get_attribute('data-open-dialog')
            trigger.click()
            dialog = page.locator('[id="' + target + '"]')
            expect(dialog).to_be_visible()
            assert dialog.evaluate("el => el.matches(':modal')")
            dialog.get_by_role('button', name='Kapat', exact=True).click()
            expect(dialog).not_to_be_visible()
            expect(trigger).to_be_focused()
        search = page.locator('[data-directorate-search]')
        search.fill('STRATEJİ')  # Turkish dotted-I matching.
        expect(cards.filter(visible=True)).to_have_count(1)
        search.fill('bu müdürlük yok')
        expect(cards.filter(visible=True)).to_have_count(0)
        search.fill('')
        expect(cards.filter(visible=True)).to_have_count(count)
        if name.startswith('financial'):
            figures = server.context['financial']['pp_planned_figures']
            years_by_name = {}
            for figure in figures:
                years_by_name.setdefault(figure['department'], set()).add(figure['year'])
            assert page.locator('[data-planned-year]').count() == sum(len(years) == 1 for years in years_by_name.values())
            for card in cards.all():
                target = card.locator('[data-open-dialog]').get_attribute('data-open-dialog')
                years = years_by_name.get(card.get_attribute('data-directorate-card'), set())
                dialog = page.locator('[id="' + target + '"]')
                assert dialog.locator('th').filter(has_text=re.compile('^Yıl$')).count() == (len(years) > 1)
            page.get_by_role('button', name='İdare bütçesi, malî tablolar ve ortak kontrolleri aç').click()
            expect(page.locator('#financial-central')).to_be_visible()
            assert page.locator('#financial-central form[method="post"]').count() > 0
            page.locator('#financial-central').get_by_role('button', name='Kapat', exact=True).click()
            # A validation response reopens its dialog with the attempted value
            # and the error inside the modal, where it remains accessible.
            page.get_by_role('button', name='İdare bütçesi, malî tablolar ve ortak kontrolleri aç').click()
            policy = page.locator('#financial-central form[action$="/financial/policy"]')
            policy.locator('[name="lower_rate"]').fill('geçersiz')
            with page.expect_navigation():
                policy.get_by_role('button').click()
            expect(page.locator('#financial-central')).to_be_visible()
            expect(page.locator('#financial-central [role="alert"]')).to_be_visible()
            expect(page.locator('#financial-central [name="lower_rate"]')).to_have_value('geçersiz')
            expect(page.locator('#saved-notice')).to_be_hidden()
            page.locator('#financial-central').get_by_role('button', name='Kapat', exact=True).click()
        # Numeric output is readable in both comparison and financial tables.
        numeric = page.locator('.pilot-numeric, .amount, .directorate-dialog .indicator-target')
        assert numeric.count()
        assert numeric.evaluate_all("els => els.every(el => getComputedStyle(el).textAlign === 'right' && getComputedStyle(el).fontVariantNumeric.includes('tabular-nums'))")
        assert not errors, errors
        folder = os.getenv('CIVENSA_CIV201_SCREENSHOTS')
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            page.evaluate('scrollTo(0,0)')
            page.screenshot(path=str(Path(folder) / f'{name}-after.png'))


@pytest.fixture
def native_server(pilot_client):
    """Real loopback HTTP for native browser POST -> 303 -> GET behavior."""
    import uvicorn
    client, db = pilot_client
    previous = main.app.dependency_overrides[get_db]
    def database():
        with Session(db.bind, expire_on_commit=False) as session:
            yield session
    main.app.dependency_overrides[get_db] = database
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    origin = 'http://127.0.0.1:' + str(sock.getsockname()[1])
    server = uvicorn.Server(uvicorn.Config(main.app, lifespan='off', log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.01)
        assert server.started
        yield origin, [dict(name=cookie.name, value=cookie.value, url=origin) for cookie in client.cookies.jar]
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()
        main.app.dependency_overrides[get_db] = previous
        assert not thread.is_alive()


@pytest.mark.parametrize('path', ['/structure?period_id=1', '/operations?period_id=1'])
def test_real_browser_submit_saved_notice_scroll_and_error(browser, native_server, path):
    origin, cookies = native_server
    writes = []
    with browser.new_context(viewport={'width': 1440, 'height': 900}) as context:
        context.add_cookies(cookies)
        page = context.new_page()
        page.on('response', lambda response: writes.append((response.url, response.status)) if response.request.method == 'POST' else None)
        page.goto(origin + path, timeout=180000)
        expect(page.locator('#saved-notice')).to_be_hidden()
        if path.startswith('/structure'):
            form = page.locator('form[action$="/rename"]').nth(10)
            # Re-save the existing synthetic name; no fixture content is replaced.
        else:
            form = page.locator('.pp-release-form')
            form.locator('[name="decision"]').select_option('revoked')
            form.locator('[name="reason"]').fill('SENTETİK CIV-201 tarayıcı geri çekme denemesi.')
            form.locator('[name="evidence"]').fill('SENTETİK kayıt; gerçek kişi onayı değildir.')
        button = form.locator('button[type="submit"], button:not([type])').last
        button.scroll_into_view_if_needed()
        before = page.evaluate('scrollY')
        assert before > 200
        with page.expect_navigation():
            button.click()
        expect(page.locator('#saved-notice')).to_be_visible()
        expect(page.locator('#saved-notice')).to_have_text('Kaydedildi.')
        assert abs(page.evaluate('scrollY') - before) <= 60
        assert writes[-1][1] == 303
        # The notice is consumed once, rather than reappearing on refresh.
        page.reload()
        expect(page.locator('#saved-notice')).to_be_hidden()
        if path.startswith('/operations'):
            # An actual application validation error must not claim success.
            form = page.locator('.pp-release-form')
            form.locator('[name="reason"]').fill('SENTETİK geçersiz madde.')
            form.locator('[name="evidence"]').fill('SENTETİK test kanıtı.')
            form.locator('[name="item_id"]').evaluate("el => el.options[0].value = 'invalid-civ201'")
            with page.expect_navigation():
                form.locator('button').click()
            assert writes[-1][1] == 422
            expect(page.locator('#saved-notice')).to_be_hidden()


def test_compact_financial_keeps_department_checks_without_planned_figures(pilot_client, monkeypatch):
    """Years without PP planned figures still show every directorate's checks."""
    from app import activity_financial_service as service
    original = service.pp_references
    monkeypatch.setattr(service, 'pp_references',
        lambda *a, **k: (lambda r: (r[0], r[1], []) if k.get('include_plan') else r)(original(*a, **k)))
    client, _ = pilot_client
    response = client.get('/activity-sections/reports/1?code=III.A.1')
    assert response.status_code == 200
    financial = response.context['financial']
    assert 'pp_planned_figures' not in financial
    names = response.context['financial_department_names'].values()
    department_missing = [m for m in financial['missing']['III.A.1'] if any(m.startswith(n + ':') for n in names)]
    assert department_missing  # The seed has directorate-specific budget gaps.
    html = response.text
    assert 'id="financial-directorates"' in html and 'Müdürlük kontrolleri' in html
    for message in department_missing:
        assert str(markupsafe_escape(message)) in html, message


def markupsafe_escape(value):
    from markupsafe import escape
    return escape(value)


def test_indicator_fragment_opens_its_directorate_dialog(browser, pilot_client):
    """Correction links (#indicator-N) reach records that sit in closed dialogs."""
    client, _ = pilot_client
    url = '/activity-reports/revisions/1'
    with browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1) as context:
        documents = bridge(context, client, [])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver' + url, timeout=180000)
        rows = documents['http://testserver' + url].context['report']['indicators']
        first, last = rows[0]['report_indicator_id'], rows[-1]['report_indicator_id']
        page.goto(f'http://testserver{url}#indicator-{last}', timeout=180000)
        target = page.locator(f'[id="indicator-{last}"]')
        expect(target).to_be_visible()
        dialog = target.locator('xpath=ancestor::dialog')
        assert dialog.evaluate("el => el.matches(':modal')")
        dialog.get_by_role('button', name='Kapat', exact=True).click()
        expect(target).not_to_be_visible()
        page.evaluate(f"location.hash = 'indicator-{first}'")  # Same-page fragment change.
        expect(page.locator(f'[id="indicator-{first}"]')).to_be_visible()
        assert not errors, errors


def test_saved_form_inside_dialog_returns_to_its_scroll_position(browser, native_server):
    """A save far down a long dialog reopens that dialog where the form was."""
    origin, cookies = native_server
    with browser.new_context(viewport={'width': 1440, 'height': 900}) as context:
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(origin + '/activity-sections/reports/1?code=III.A.1', timeout=180000)
        page.get_by_role('button', name='İdare bütçesi, malî tablolar ve ortak kontrolleri aç').click()
        dialog = page.locator('#financial-central')
        form = dialog.locator('form[action$="/financial/policy"]')
        # Re-save the thresholds as they are; no fixture content changes.
        form.get_by_role('button').scroll_into_view_if_needed()
        before = dialog.evaluate('el => el.scrollTop')
        assert before > 300
        with page.expect_navigation():
            form.get_by_role('button').click()
        expect(dialog).to_be_visible()
        expect(page.locator('#saved-notice')).to_be_visible()
        for _ in range(40):  # The restore runs on the next animation frame.
            if abs(dialog.evaluate('el => el.scrollTop') - before) <= 60:
                break
            page.wait_for_timeout(50)
        assert abs(dialog.evaluate('el => el.scrollTop') - before) <= 60


def test_closing_a_dialog_keeps_the_unsaved_change_guard(browser, pilot_client):
    """'Kapat' only closes the dialog; it neither asks to leave nor disarms the guard."""
    client, _ = pilot_client
    url = '/activity-reports/revisions/1'
    with browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1) as context:
        bridge(context, client, [])
        page = context.new_page()
        page.goto('http://testserver' + url, timeout=180000)
        trigger = page.locator('[data-directorate-card]').first.get_by_role('button', name='Ayrıntıyı aç')
        dialog = page.locator('[id="' + trigger.get_attribute('data-open-dialog') + '"]')
        trigger.click()
        field = dialog.locator('[data-actual-form] textarea, [data-actual-form] input[type="text"], [data-actual-form] input:not([type])').first
        field.fill('SENTETİK kaydedilmemiş değişiklik')
        confirm = page.locator('dialog.draft-confirm')
        dialog.get_by_role('button', name='Kapat', exact=True).click()
        expect(dialog).not_to_be_visible()
        expect(confirm).not_to_be_visible()
        # The guard is still armed: leaving through a link asks first.
        page.locator('a[href="/modules"], nav a[href^="/"]').first.click()
        expect(confirm).to_be_visible()
