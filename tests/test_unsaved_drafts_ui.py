"""Per-record saves against real handlers, auth/CSRF and disposable PostgreSQL.

Like test_sidebar_ui, route Chromium requests through TestClient so the browser
uses the application's templates/assets without contacting a deployed service.
"""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import Indicator, IndicatorValue, ActualRevision
from test_sidebar_ui import browser
from test_activity_contract import publish, new_report

pytestmark = pytest.mark.postgres


@pytest.fixture(params=['pp', 'ar'])
def editor(request, browser, client, db, sample):
    from app.main import app, require_user
    from app.security import hash_password

    second = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
        subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
        name='İkinci hizmet sayısı', unit='Adet')
    db.add(second); db.flush()
    db.add(IndicatorValue(indicator_id=second.id, year=2027, value_kind='target', value='0'))
    db.commit()
    module = request.param
    if module == 'ar':
        report = new_report(client, publish(client, db, sample), sample)
        slots = [row['report_indicator_id'] for row in report['indicators']]
        url = f"/activity-reports/revisions/{report['revision_id']}"
        selectors = [f'#indicator-{slot}' for slot in slots]
        field, explanation = '[name="value"]', '[name="explanation"]'
    else:
        slots = [sample['indicator'].id, second.id]
        url = f"/department/{sample['department'].id}"
        selectors = [f'.record[data-id="{slot}"]' for slot in slots]
        field, explanation = '[data-field="value_2027_target"]', '[data-field="explanation"]'

    # Setup helpers above use Strategy; all browser writes below use real login.
    app.dependency_overrides.pop(require_user, None)
    sample['user'].password_hash = hash_password('draft-browser-test-only')
    db.commit()
    assert client.post('/login', data={'email': sample['user'].email,
        'password': 'draft-browser-test-only'}, follow_redirects=False).status_code == 303
    pending = {}
    requests = []
    with browser.new_context(viewport={'width': 1200, 'height': 1000}) as context:
        def fulfill(route, response):
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        def serve(route):
            req = route.request
            response = client.request(req.method, req.url, content=req.post_data_buffer,
                headers={'content-type': req.headers.get('content-type', ''),
                         'X-CSRF-Token': req.headers.get('x-csrf-token', '')},
                # Playwright routes only the first request of a redirected fetch.
                # Follow it in TestClient to serve the real final HTML locally.
                follow_redirects=req.resource_type in {'fetch', 'xhr'})
            requests.append((req.method, req.url, response.status_code))
            if req.method == 'POST' and pending.pop('hold', False):
                pending['route'], pending['response'] = route, response
            else:
                fulfill(route, response)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver' + url)
        records = [page.locator(selector) for selector in selectors]
        for record in records:
            expect(record.locator(field)).to_be_visible()
        if module == 'ar':
            for record in records:
                record.locator('[name="source_title"]').fill('Sentetik kayıt defteri')
                record.locator('[name="source_locator"]').fill('Sayfa 3')
                record.locator('[name="source_revision"]').fill('2027 kayıt 4')
        def save(record):
            record.locator('.save-indicator' if module == 'pp' else 'form button').click()
        def screenshot(name):
            output = os.getenv('CIVENSA_UI_SCREENSHOTS')
            if output:
                folder = Path(output); folder.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(folder / f'{module}-{name}.png'), full_page=name != 'confirmation')
        yield SimpleNamespace(page=page, records=records, field=field, explanation=explanation,
            save=save, screenshot=screenshot, module=module, pending=pending, requests=requests,
            release=lambda: fulfill(pending.pop('route'), pending.pop('response')), slots=slots)
        assert not errors, errors


def draft(record):
    expect(record.locator('.draft-status')).to_have_text('Kaydedilmedi')


def saved(record):
    expect(record.locator('.draft-status')).to_have_text('Kaydedildi')


def test_sibling_save_preserves_draft_and_both_persist_after_reload(editor, db):
    a, b = editor.records
    a.locator(editor.field).fill('99,99')
    a.locator(editor.explanation).fill('A kaydedilmemiş açıklama')
    b.locator(editor.field).fill('0')
    b.locator(editor.explanation).fill('B kayıtlı açıklama')
    draft(a); draft(b)
    editor.save(b); saved(b)
    expect(a.locator(editor.field)).to_have_value('99,99')
    expect(a.locator(editor.explanation)).to_have_value('A kaydedilmemiş açıklama')
    draft(a)
    editor.screenshot('unsaved-marker')
    editor.save(a); saved(a); saved(b)
    # A second save must use the refreshed actual expected_revision (CAS).
    b.locator(editor.explanation).fill('B ikinci kayıtlı açıklama')
    editor.save(b); saved(b)
    dialogs = []
    editor.page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
    editor.page.reload()
    expect(a.locator(editor.field)).to_have_value('99,99')
    expect(b.locator(editor.field)).to_have_value('0')
    expect(b.locator(editor.explanation)).to_have_value('B ikinci kayıtlı açıklama')
    editor.page.get_by_role('link', name='Modüller', exact=True).click()
    expect(editor.page).to_have_url('http://testserver/modules')
    assert not dialogs
    db.expire_all()
    if editor.module == 'pp':
        rows = db.scalars(select(IndicatorValue).where(IndicatorValue.year == 2027,
            IndicatorValue.value_kind == 'target').order_by(IndicatorValue.indicator_id)).all()
        assert [str(row.value) for row in rows] == ['99.990000', '0.000000']
    else:
        rows = db.scalars(select(ActualRevision).order_by(ActualRevision.id)).all()
        assert len(rows) == 3 and rows[-1].revision == 2


def test_turkish_navigation_confirmation_and_native_reload_guard(editor):
    a, _ = editor.records
    a.locator(editor.field).fill('22,5'); draft(a)
    editor.page.get_by_role('link', name='Modüller', exact=True).click()
    dialog = editor.page.get_by_role('dialog')
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text('Kaydedilmemiş değişiklikler var')
    editor.screenshot('confirmation')
    dialog.get_by_role('button', name='Sayfada kal', exact=True).click()
    expect(a.locator(editor.field)).to_have_value('22,5'); draft(a)
    dialogs = []
    editor.page.on('dialog', lambda native: (dialogs.append(native.type), native.dismiss()))
    with editor.page.expect_event('dialog') as reload_warning:
        editor.page.evaluate('location.reload()')
    assert reload_warning.value.type == 'beforeunload'
    assert dialogs == ['beforeunload']
    expect(a.locator(editor.field)).to_have_value('22,5'); draft(a)
    editor.page.get_by_role('link', name='Modüller', exact=True).click()
    dialog.get_by_role('button', name='Kaydetmeden ayrıl', exact=True).click()
    expect(editor.page).to_have_url('http://testserver/modules')
    assert dialogs == ['beforeunload']  # No second prompt after explicit consent.


@pytest.mark.parametrize('invalid', ['number', 'metadata'])
def test_validation_error_keeps_both_attempts_and_recovery(editor, invalid):
    a, b = editor.records
    a.locator(editor.field).fill('11,25')
    a.locator(editor.explanation).fill('A taslağı')
    b.locator(editor.field).fill('abc' if invalid == 'number' else '12,5')
    metadata = '[data-field="unit"]' if editor.module == 'pp' else '[name="source_title"]'
    if invalid == 'metadata':
        b.locator(metadata).fill('')
    b.locator(editor.explanation).fill('B hatalı denemesi')
    editor.save(b)
    expect(b.locator('.draft-error')).to_be_visible()
    expected_error = ('sayı' if editor.module == 'ar' else 'Sayı') if invalid == 'number' else ('Eksik kaynak kaydı' if editor.module == 'ar' else 'birimini')
    expect(b.locator('.draft-error')).to_contain_text(expected_error)
    expect(a.locator(editor.field)).to_have_value('11,25')
    expect(b.locator(editor.field)).to_have_value('abc' if invalid == 'number' else '12,5')
    if invalid == 'metadata':
        expect(b.locator(metadata)).to_have_value('')
    expect(a.locator(editor.explanation)).to_have_value('A taslağı')
    expect(b.locator(editor.explanation)).to_have_value('B hatalı denemesi')
    draft(a); draft(b)
    if editor.module == 'ar':
        invalid_input = b.locator(editor.field if invalid == 'number' else metadata)
        expect(invalid_input).to_have_attribute('aria-invalid', 'true')
        expect(invalid_input).to_have_attribute('aria-describedby', b.locator('.draft-error').get_attribute('id'))
    assert any(status == 422 for _, _, status in editor.requests)
    b.locator(editor.field).fill('12,5')
    if invalid == 'metadata':
        b.locator(metadata).fill('Adet' if editor.module == 'pp' else 'Sentetik kayıt defteri')
    editor.save(b); saved(b); draft(a)
    expect(b.locator('.draft-error')).to_have_count(0)


def test_edits_during_pending_save_remain_unsaved(editor):
    a, b = editor.records
    a.locator(editor.field).fill('3,5')
    b.locator(editor.field).fill('4,5')
    editor.pending['hold'] = True
    editor.save(b)
    expect(b.locator('button').last).to_be_disabled()
    b.locator(editor.field).fill('5,5')
    b.locator(editor.explanation).fill('İstek sürerken yeni taslak')
    editor.release()
    draft(a); draft(b)
    expect(b.locator(editor.field)).to_have_value('5,5')
    expect(b.locator(editor.explanation)).to_have_value('İstek sürerken yeni taslak')
    editor.save(b); saved(b); draft(a)


def test_logout_confirmation_cancels_before_session_is_closed(editor):
    a, _ = editor.records
    a.locator(editor.field).fill('7,5')
    editor.page.get_by_role('button', name='Çıkış', exact=True).click()
    dialog = editor.page.get_by_role('dialog')
    expect(dialog).to_be_visible()
    dialog.get_by_role('button', name='Sayfada kal', exact=True).click()
    expect(a.locator(editor.field)).to_have_value('7,5'); draft(a)
    assert not any(url.endswith('/logout') for _, url, _ in editor.requests)
