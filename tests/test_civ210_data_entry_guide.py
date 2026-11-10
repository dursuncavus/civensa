"""CIV-210: Veri Girişi at a glance (badges, summary, grouped submit errors, staff note)."""
import pytest
from playwright.sync_api import expect

from app.main import indicator_issues
from app.models import IndicatorValue
from test_department_design import configure
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def open_page(browser, client, width=1440):
    context = browser.new_context(viewport={'width': width, 'height': 900})
    def serve(route):
        req = route.request
        response = client.request(req.method, req.url, content=req.post_data_buffer,
            headers={'content-type': req.headers.get('content-type', '')}, follow_redirects=False)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://testserver/department/1?period_id=1')
    return context, page, errors


def test_unreadable_source_value_says_what_to_type(db, sample):
    ind = sample['indicator']
    db.add(IndicatorValue(indicator_id=ind.id, year=2025, value_kind='planned', value=None, raw_text='%40', state='needs_review'))
    db.commit(); db.refresh(ind)
    issue = next(i for i in indicator_issues(ind, 2026) if i.startswith('2025 Planlanan'))
    assert 'doğrulanmalı' in issue and '“%40”' in issue and 'sayıyı girin' in issue


@pytest.mark.parametrize('width', [1440, 390])
def test_badges_summary_and_jump(browser, client, db, sample, width):
    configure(db, sample, 'draft-issues', 'staff')
    context, page, errors = open_page(browser, client, width)
    with context:
        badge = page.locator('article.record.has-issue .record-head .badge').first
        expect(badge).to_have_text('1 düzeltme')
        summary = page.locator('.entry-summary')
        expect(summary).to_contain_text('göstergeden 1 tanesinde düzeltme gerekli')
        page.locator('.entry-summary-jump').click()
        expect(page.locator('article.record.has-issue .issue-jump').first).to_be_focused()
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert errors == []


def test_staff_without_permission_sees_who_submits(browser, client, db, sample):
    configure(db, sample, 'draft-clean', 'staff')
    sample['user'].can_submit = False
    db.commit()
    context, page, errors = open_page(browser, client)
    with context:
        expect(page.locator('#submitDepartment')).to_be_hidden()
        expect(page.locator('.submit-bar')).to_contain_text('Paketi Müdürünüz gönderir')
        expect(page.locator('.record-head .badge').first).to_have_text('Sorun yok')
        assert errors == []


@pytest.mark.parametrize('actor', ['staff', 'director'])
def test_permitted_users_keep_the_submit_button(browser, client, db, sample, actor):
    configure(db, sample, 'draft-clean', actor)
    context, page, errors = open_page(browser, client)
    with context:
        expect(page.locator('#submitDepartment')).to_be_visible()
        assert page.locator('meta[name="pp-can-submit"]').count() == 0
        assert errors == []


def test_submit_errors_are_grouped_with_a_way_there(browser, client, db, sample):
    configure(db, sample, 'draft-issues', 'director')
    context, page, errors = open_page(browser, client)
    with context:
        page.locator('#submitDepartment').click()
        box = page.locator('.submit-errors')
        expect(box).to_be_visible()
        expect(box).to_contain_text('Paket gönderilemedi')
        groups = box.locator('details.submit-error-group')
        assert groups.count() >= 1
        names = groups.locator('summary').all_inner_texts()
        assert any(name.startswith('Performans göstergeleri') for name in names)
        # The list sits under the submit bar, not squeezed beside its button.
        assert page.evaluate('''() => { const bar = document.querySelector('.submit-bar'), box = document.querySelector('.submit-errors');
            const a = bar.getBoundingClientRect(), b = box.getBoundingClientRect();
            return bar.nextElementSibling === box && b.top >= a.bottom - 1 && b.width >= a.width - 2; }''')
        group = groups.filter(has_text='Performans göstergeleri')
        group.evaluate('el => { el.open = true; }')
        group.locator('button', has_text='İlk göstergeye git').click()
        expect(page.locator('article.record.has-issue .issue-jump').first).to_be_focused()
        assert errors == []


def test_review_queue_puts_waiting_packages_first(browser, client, db, sample):
    from sqlalchemy import select
    from app.models import Department, Submission
    first = db.scalar(select(Submission))
    other = Department(name='Sentetik İkinci Müdürlüğü', organization_id=db.get(Department, first.department_id).organization_id)
    db.add(other); db.flush()
    db.add(Submission(period_id=sample['period'].id, department_id=other.id, status='submitted', revision=1))
    db.commit()
    assert first.status == 'draft'
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    def serve(route):
        response = client.get(route.request.url)
        headers = dict(response.headers); headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)
    with context:
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/review?period_id={sample["period"].id}')
        expect(page.locator('.review-summary')).to_contain_text('İncelemenizi bekleyen 1 paket var')
        expect(page.locator('.review-summary')).to_contain_text('1 müdürlük henüz gönderilmedi')
        rows = page.locator('.review-panel tbody > tr')
        expect(rows.first.locator('.status')).to_have_class('status submitted')
        expect(rows.nth(1)).to_contain_text('Henüz gönderilmedi')
        assert 'Eski kayıt' not in rows.nth(1).inner_text()
        assert errors == []


def test_card_assignment_goes_to_program_page_catalogue_to_strategy(browser, client, db, sample):
    configure(db, sample, 'draft-clean', 'director')
    context, page, errors = open_page(browser, client)
    with context:
        name = page.locator('#indicators article.record h3').first.inner_text()
        page.evaluate('''name => globalThis.civSubmitErrors(document.querySelector('#submitDepartment'),
            [name + ': kart bağlantısı eksik.', 'Sentetik faaliyet: sorumlu harcama birimleri kataloğu bağlantısı eksik.'])''', name)
        groups = page.locator('.submit-errors details.submit-error-group')
        program = groups.filter(has_text='Performans kartları ve ekonomik tablolar')
        expect(program).to_contain_text('kart bağlantısı eksik')
        expect(program.locator('a.button')).to_have_attribute('href', '/program/1?period_id=1')
        expect(groups.filter(has_text='katalog bağlantıları')).to_contain_text('kataloğu bağlantısı eksik')
        assert groups.filter(has_text='Performans göstergeleri').count() == 0
        assert errors == []
