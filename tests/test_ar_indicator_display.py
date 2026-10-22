"""CIV-077: scoped read-only indicator display on synthetic PostgreSQL data."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import func, select

from app import activity_contract_service as service
from app.db import Base
from app.main import app, require_user
from app.models import (Department, Indicator, IndicatorValue, Publication,
                        ActivityReportApproval, ReportCandidate, ReportCandidateState)
from tests.test_activity_contract import publish, new_report, actual_payload
from tests.test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def counts(db):
    return {table.name: db.scalar(select(func.count()).select_from(table))
            for table in Base.metadata.sorted_tables}


def open_page(browser, client, width):
    context = browser.new_context(viewport={'width': width, 'height': 900 if width == 390 else 768})

    def serve(route):
        response = client.request(route.request.method, route.request.url,
                                  follow_redirects=False)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)

    context.route('http://testserver/**', serve)
    return context, context.new_page()


def screenshot(page, name, width):
    if os.getenv('CIVENSA_UI_SCREENSHOTS'):
        directory = Path(os.environ['CIVENSA_UI_SCREENSHOTS'])
        directory.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(directory / f'{name}-{width}.png'), full_page=True)


@pytest.mark.parametrize('width', [1366, 390])
def test_latest_actual_and_newest_first_history(browser, client, db, sample, width):
    empty = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
                      subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
                      name='Henüz gerçekleşmesi olmayan gösterge', unit='Adet')
    db.add(empty); db.flush()
    db.add(IndicatorValue(indicator_id=empty.id, year=2027, value_kind='target', value='1'))
    db.commit()
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    for revision, value, state in [(0, '0', 'verified'), (1, '12500.23', 'needs_review')]:
        response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(
            expected_revision=revision, value=value, state=state,
            explanation=f'Gerçekleşme açıklaması {revision + 1}',
            evidence=[{'title': f'Dayanak {revision + 1}', 'locator': 'Sayfa 7', 'source_revision': '2027-v2'}]))
        assert response.status_code == 200, response.text
    before = counts(db)
    context, page = open_page(browser, client, width)
    try:
        page.goto(f'http://testserver/activity-reports/revisions/{report["revision_id"]}')
        card = page.locator(f'#indicator-{slot}')
        card.scroll_into_view_if_needed()
        # Align to the card top without opening history or any other control.
        card.evaluate('(el) => el.scrollIntoView({block: "start"})')
        latest = card.locator('[data-latest-actual]')
        for text in ['12.500,23', 'İncelenmeli', 'Gerçekleşme açıklaması 2', 'Dayanak 2', 'Sayfa 7', '2027-v2']:
            expect(latest.get_by_text(text, exact=False)).to_be_visible()
        box = latest.bounding_box()
        assert box['y'] >= 0 and box['y'] + box['height'] <= page.viewport_size['height']
        assert card.locator('details').get_attribute('open') is None
        screenshot(page, 'latest-actual', width)
        card.get_by_text('Gerçekleşme geçmişi', exact=False).click()
        history = card.locator('details article')
        assert history.locator('h3').all_text_contents() == ['Gerçekleşme revizyon 2', 'Gerçekleşme revizyon 1']
        expect(history.nth(1)).to_contain_text('0')
        expect(history.nth(1)).to_contain_text('Doğrulanmış')
        empty_card = page.locator(f'#indicator-{report["indicators"][1]["report_indicator_id"]}')
        expect(empty_card.locator('[data-latest-actual]')).to_have_text('Son gerçekleşmeKayıt yok')
        assert '0' not in empty_card.locator('[data-latest-actual]').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert counts(db) == before
    finally:
        context.close()


def synthetic_publication(db, sample):
    # Freeze synthetic two-department definitions directly: financial PP gates are
    # outside this display test, while hashes and explicit bindings stay real.
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    payload, definitions = service.freeze_program_payload(db, sample['period'].id, sample['strategy'])
    snapshot = service.canonical(payload)
    version = (db.scalar(select(func.max(Publication.version))) or 0) + 1
    publication = Publication(period_id=sample['period'].id, version=version,
                              snapshot_json=snapshot, sha256=service.digest(snapshot),
                              created_by=sample['strategy'].id)
    db.add(publication); db.flush()
    service.attach_publication_definitions(db, publication, definitions, sample['strategy'])
    db.commit()
    return publication


@pytest.mark.parametrize('width', [1366, 390])
def test_newer_comparison_is_explicit_read_only_and_scoped(browser, client, db, sample, width):
    other = Department(organization_id=sample['department'].organization_id, name='Diğer Müdürlüğü')
    db.add(other); db.flush()
    hidden = Indicator(period_id=sample['period'].id, department_id=other.id,
                       subprogram_id=sample['subprogram'].id, name='Gizli gösterge', unit='Adet')
    db.add(hidden); db.flush()
    db.add(IndicatorValue(indicator_id=hidden.id, year=2027, value_kind='target', value='1'))
    db.commit()
    first = synthetic_publication(db, sample)
    report = new_report(client, first, sample)
    url = f'/activity-reports/revisions/{report["revision_id"]}'
    assert '?compare=newer' not in client.get(url).text
    assert 'data-newer-comparison' not in client.get(url + '?compare=newer').text
    sample['indicator'].name = 'Güncellenmiş hizmet sayısı'
    db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == sample['indicator'].id)).value = '12500.23'
    hidden.name = 'Gizli yeni tanım'; db.commit()
    second = synthetic_publication(db, sample)
    before = counts(db)
    assert 'data-newer-comparison' not in client.get(url).text
    context, page = open_page(browser, client, width)
    try:
        page.goto('http://testserver' + url)
        page.get_by_role('link', name='Yeni program v2 ile hedef ve tanım farklarını gör').click()
        comparison = page.locator('[data-newer-comparison]')
        expect(comparison).to_contain_text('Baz program v1 → Yeni program v2')
        for text in ['Hizmet sayısı', 'Güncellenmiş hizmet sayısı', '12.500,23', 'Salt okunur']:
            expect(comparison).to_contain_text(text)
        assert comparison.locator('form, input, button, select, textarea').count() == 0
        screenshot(page, 'newer-comparison', width)
        app.dependency_overrides[require_user] = lambda: sample['user']
        page.goto('http://testserver' + url + '?compare=newer')
        assert 'Gizli' not in page.locator('main').inner_text()
        expect(page.locator('[data-newer-comparison]')).to_contain_text('Güncellenmiş hizmet sayısı')
        assert page.locator('[id^="indicator-"]').count() == 1
        assert counts(db) == before
        unchanged = client.get('/api' + url).json()
        assert unchanged['publication_id'] == first.id
        assert unchanged['indicators'][0]['definition']['name'] == 'Hizmet sayısı'
    finally:
        context.close()
    # Moving the base still requires the existing explicit revision action.
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    newer = new_report(client, second, sample, report_id=report['report_id'], expected_revision=1)
    assert newer['publication_id'] == second.id
    assert client.post(f'/api/activity-reports/indicators/{report["indicators"][0]["report_indicator_id"]}/actuals',
                       json=actual_payload()).status_code == 409
    assert '?compare=newer' not in client.get(f'/activity-reports/revisions/{newer["revision_id"]}').text


@pytest.mark.parametrize('width', [1366, 390])
def test_revision_status_badges(browser, client, db, sample, width):
    first = publish(client, db, sample)
    report = new_report(client, first, sample)
    url = f'/activity-reports/revisions/{report["revision_id"]}'
    def badges(page, revision_id):
        return page.locator('li').filter(has=page.locator(f'a[href="/activity-reports/revisions/{revision_id}"]')).locator('.badge').all_text_contents()
    context, page = open_page(browser, client, width)
    try:
        page.goto('http://testserver/activity-reports')
        assert badges(page, report['revision_id']) == ['Güncel', 'Taslak']
        app.dependency_overrides[require_user] = lambda: sample['user']
        assert client.post(f'/api/activity-reports/indicators/{report["indicators"][0]["report_indicator_id"]}/actuals', json=actual_payload()).status_code == 200
        app.dependency_overrides[require_user] = lambda: sample['strategy']
        assert client.post('/api' + url + '/approve').status_code == 200
        page.reload()
        assert badges(page, report['revision_id']) == ['Güncel', 'Onaylı']
        new = new_report(client, first, sample, report_id=report['report_id'], expected_revision=1,
                         revision_reason='Kaynak düzeltmesi')
        page.reload()
        assert badges(page, report['revision_id']) == ['Geçmiş revizyon', 'Onaylı']
        assert badges(page, new['revision_id']) == ['Güncel', 'Taslak']
        # Synthetic persisted returned-after-approval state; no workflow code is mocked.
        db.add(ActivityReportApproval(report_revision_id=new['revision_id'], created_by=sample['strategy'].id))
        candidate = ReportCandidate(organization_id=sample['department'].organization_id,
            period_id=sample['period'].id, resource_scope='activity_report', report_key=str(report['report_id']),
            sequence=1, activity_revision_id=new['revision_id'], payload_json='{}', payload_sha256='0'*64,
            manifest_json='{}', sha256='0'*64, created_by=sample['strategy'].id)
        db.add(candidate); db.flush()
        db.add(ReportCandidateState(candidate_id=candidate.id, state='returned_to_strategy')); db.commit()
        before = counts(db)
        page.reload()
        assert badges(page, new['revision_id']) == ['Güncel', 'Nihai onay sonrası iade edildi']
        screenshot(page, 'status-badges', width)
        assert counts(db) == before
    finally:
        context.close()


@pytest.mark.parametrize('state,value,label', [('missing', None, 'Kayıt yok'), ('verified', '0', '0')])
def test_latest_missing_and_zero_are_distinct(browser, client, db, sample, state, value, label):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals',
                       json=actual_payload(value=value, state=state)).status_code == 200
    context, page = open_page(browser, client, 390)
    try:
        page.goto(f'http://testserver/activity-reports/revisions/{report["revision_id"]}')
        latest = page.locator('[data-latest-actual]')
        expect(latest.locator('strong')).to_have_text(label)
        expect(latest).to_contain_text('Eksik' if state == 'missing' else 'Doğrulanmış')
        assert latest.locator('details').count() == 0
    finally:
        context.close()
