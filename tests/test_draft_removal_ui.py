"""Real browser confirmation/cancellation and refusal against actual PP routes."""
import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import AuditLog
from test_draft_removal import fresh, actor
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('role', ['department', 'strategy'])
@pytest.mark.parametrize('kind,path', [('indicator', '/department/1'), ('indicator', '/program/1'), ('card', '/program/1')])
def test_inline_confirm_before_removal(browser, client, db, sample, fresh, kind, path, role):
    actor(sample, role)
    obj = fresh[kind]; obj_id = obj.id; model = type(obj)
    with browser.new_context() as context:
        writes, dialogs = [], []

        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={key: request.headers[key] for key in ['content-type', 'accept', 'x-csrf-token'] if key in request.headers},
                follow_redirects=False)
            if request.url.endswith('/remove'):
                writes.append((request.url, response.status_code))
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        page.goto(f'http://testserver{path}?period_id=1')
        if path.startswith('/department') and role == 'department':
            # The inline warning covers discarding unsaved edits too; removal
            # must not invoke the browser's native beforeunload confirmation.
            page.locator(f'.record[data-id="{obj_id}"] [data-field="name"]').fill('Kaydedilmemiş ad')
        panel = page.locator(f'[data-removal="{kind}-{obj_id}"]')
        if kind == 'card':
            panel.locator('..').locator(':scope > summary').click()
        confirm = panel.get_by_role('button', name='Kaldırmayı Onayla', exact=True)
        expect(confirm).not_to_be_visible()
        panel.locator('summary').click()
        expect(confirm).to_be_visible()
        expect(panel).to_contain_text(obj.name if kind == 'indicator' else obj.source_title)
        assert writes == [] and db.get(model, obj_id)
        panel.get_by_role('button', name='Vazgeç', exact=True).click()
        expect(confirm).not_to_be_visible()
        assert writes == []
        panel.locator('summary').click()
        with page.expect_navigation():
            confirm.click()
        expect(page).to_have_url(f'http://testserver{path}?period_id=1')
        assert len(writes) == 1 and writes[0][1] == 200
        assert not dialogs
        db.expire_all()
        assert db.get(model, obj_id) is None
        assert db.scalar(select(AuditLog.id).where(AuditLog.action == f'{kind}_remove', AuditLog.entity_id == obj_id))


def test_inline_refusal_keeps_record(browser, client, db, sample):
    with browser.new_context() as context:
        def serve(route):
            request = route.request
            result = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={key: request.headers[key] for key in ['content-type', 'accept'] if key in request.headers},
                follow_redirects=False)
            route.fulfill(status=result.status_code, headers=dict(result.headers), body=result.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto('http://testserver/program/1?period_id=1')
        panel = page.locator(f'[data-removal="card-{sample["card"].id}"]')
        panel.locator('..').locator(':scope > summary').click()
        panel.locator('summary').click()
        panel.get_by_role('button', name='Kaldırmayı Onayla').click()
        expect(panel.get_by_role('alert')).to_contain_text('1 gösterge ve 1 faaliyet var')
        expect(panel.get_by_role('button', name='Kaldırmayı Onayla')).to_be_enabled()
        assert db.get(type(sample['card']), sample['card'].id)
        assert not db.scalar(select(AuditLog.id).where(AuditLog.action == 'card_remove'))
