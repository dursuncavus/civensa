"""CIV-197: audited settings, frozen directions and presentation comparisons."""
from copy import deepcopy
from decimal import Decimal
import json
import os
from pathlib import Path

import pytest
from sqlalchemy import select

from app import activity_contract_service as contract, activity_sections_service as sections
from app.main import app, require_user
from app.models import (AuditLog, DepartmentScope, IndicatorDirection, IndicatorDefinitionRevision,
    ReportingPeriod)
from app.sunum import render_deck
from app.sunum.meclis import scorecard
from app.sunum.recipes import activity_report, indicator_comparison
from app.sunum.recipes_idare import idare_activity_report
from test_activity_contract import publish, new_report, actual_payload
from test_activity_sections import section_client, login, ready_and_freeze


def indicator(actual, target=10, **extra):
    return dict(name='Sentetik yanıt süresi', unit='Gün', actual=actual, actual_state='verified',
        targets=[dict(value=target, state='verified')], **extra)


@pytest.mark.parametrize('actual,target,direction,met,ratio', [
    (5, 10, 'lower', True, 200), (20, 10, 'lower', False, 50),
    (10, 10, 'lower', True, 100), (0, 10, 'lower', True, None),
    (0, 0, 'lower', True, None), (5, 0, 'lower', False, 0),
    (20, 10, 'higher', True, 200), (5, 10, 'higher', False, 50),
    (0, 10, 'higher', False, 0), (0, 0, 'higher', True, None),
    (None, 10, 'lower', None, None), (5, None, 'lower', None, None),
])
def test_direction_rules(actual, target, direction, met, ratio):
    assert indicator_comparison(Decimal(actual) if actual is not None else None,
        Decimal(target) if target is not None else None, direction) == (met, ratio)


def slide(slides, title):
    return next(s for s in slides if s.get('title') == title)


@pytest.mark.parametrize('actual,met,ratio', [(5, 1, '200'), (20, 0, '50'), (0, 1, '—')])
def test_all_three_presentations_use_frozen_direction(actual, met, ratio):
    item = indicator(actual, direction='lower')
    unit = dict(department_id=1, department='Sentetik Müdürlük', core=dict(indicators=[item]))
    payload = dict(year=2027, department='Sentetik Müdürlük', core=unit['core'], unit_indicator_sources=[unit])
    before = deepcopy(payload)
    scores = scorecard([unit])
    assert scores[0]['met'] == met
    if not met:
        assert scores[0]['missed'][0]['ratio'] == '%50,0'
        assert '(düşük daha iyi)' in scores[0]['missed'][0]['name']
    rows = slide(activity_report(payload), 'Gösterge gerçekleşmeleri')['rows']
    assert rows[0][3] == ratio
    assert '(düşük daha iyi)' in rows[0][0]
    slides = idare_activity_report(payload)
    summary = slide(slides, 'Müdürlüklere göre gösterge özeti')['rows'][0]
    assert summary[3] == (ratio + ',0' if ratio != '—' else ratio)
    assert 'düşük daha iyi' in summary[0]
    assert 'düşük değer daha iyi göstergelerde gerçekleşen ≤ hedef' in slide(
        slides, 'Müdürlükler hedeflerine ne kadar yaklaştı?')['note']
    assert payload == before


def test_legacy_facts_default_to_higher_and_average_omits_undefined_ratios():
    items = [indicator(20), indicator(20, direction='lower'), indicator(0, direction='lower')]
    unit = dict(department='Sentetik Müdürlük', core=dict(indicators=items))
    assert (scorecard([unit])[0]['met'], scorecard([unit])[0]['measured']) == (2, 3)
    # The zero actual is met but has no finite ratio; average only the other two.
    summary = slide(idare_activity_report(dict(year=2027, unit_indicator_sources=[unit])),
        'Müdürlüklere göre gösterge özeti')['rows'][0]
    assert summary[3] == '125,0'
    old = dict(year=2027, department='Sentetik', core=dict(indicators=[indicator(5)]))
    explicit = deepcopy(old)
    explicit['core']['indicators'][0]['direction'] = 'higher'
    assert activity_report(old) == activity_report(explicit)


@pytest.mark.postgres
def test_setting_is_strategy_only_validated_append_only_and_audited(client, db, sample):
    sample['indicator'].name = 'Sentetik yanıt süresi'
    sample['indicator'].unit = 'Gün'
    pub = publish(client, db, sample)
    url = f'/activity-reports/publications/{pub.id}/directions'
    page_url = f'/activity-reports/publications/{pub.id}/bindings'
    data = dict(snapshot_indicator_id=sample['indicator'].id, direction='lower', reason='Sentetik süre hedefi')
    identity = sample['indicator'].persistent_indicator_id
    definitions_before = [(r.id, r.definition_json, r.sha256) for r in db.scalars(select(IndicatorDefinitionRevision))]
    assert contract.indicator_direction(db, identity, pub.period_id) == 'higher'  # Gün is not a detection rule.
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert client.post(url, data=data).status_code == 403
    assert client.get(page_url).status_code == 403
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    for invalid in [dict(data, reason='  '), dict(data, direction='sideways'), dict(data, snapshot_indicator_id=999999)]:
        assert client.post(url, data=invalid).status_code == 422
    assert not db.scalars(select(IndicatorDirection)).all()
    assert client.post(url, data=data, follow_redirects=False).status_code == 303
    assert contract.indicator_direction(db, identity, pub.period_id) == 'lower'
    page = client.get(page_url)
    assert 'value="lower" selected' in page.text
    assert 'Yön değişikliği gerekçesi' in page.text
    assert client.post(url, data=dict(data, direction='higher', reason='Sentetik düzeltme'), follow_redirects=False).status_code == 303
    rows = db.scalars(select(IndicatorDirection).order_by(IndicatorDirection.id)).all()
    assert [(r.indicator_id, r.direction, r.reason, r.created_by) for r in rows] == [
        (identity, 'lower', data['reason'], sample['strategy'].id),
        (identity, 'higher', 'Sentetik düzeltme', sample['strategy'].id)]
    assert contract.indicator_direction(db, identity, pub.period_id) == 'higher'
    next_period = ReportingPeriod(year=2028, status='active')
    db.add(next_period); db.flush()
    assert contract.indicator_direction(db, identity, next_period.id) == 'higher'
    logs = db.scalars(select(AuditLog).where(AuditLog.action == 'indicator_direction_set').order_by(AuditLog.id)).all()
    assert [json.loads(log.details)['reason'] for log in logs] == [data['reason'], 'Sentetik düzeltme']
    assert [log.entity_id for log in logs] == [r.id for r in rows]
    assert definitions_before == [(r.id, r.definition_json, r.sha256) for r in db.scalars(select(IndicatorDefinitionRevision))]
    rows[0].reason = 'Geçmişi değiştir'
    with pytest.raises(ValueError, match='Geçmiş sürüm değiştirilemez'):
        db.flush()
    db.rollback()


@pytest.mark.postgres
def test_real_fr_approval_keeps_direction_after_later_change(section_client, db, sample):
    client, docs, _, _ = section_client
    token = login(client, sample['strategy'].email)
    client.headers['X-CSRF-Token'] = token
    for dep in section_client[2:]:
        scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == sample['period'].id,
            DepartmentScope.department_id == dep.id))
        scope.status = 'excluded'
        scope.reason = 'Bu sentetik PP örneğinin dışında'
    pub = publish(client, db, sample)
    report = new_report(client, pub, sample)
    slot = report['indicators'][0]['report_indicator_id']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).status_code == 200
    url = f'/activity-reports/publications/{pub.id}/directions'
    data = dict(snapshot_indicator_id=sample['indicator'].id, direction='lower', reason='Sentetik süre kuralı')
    assert client.post(url, data=data).status_code == 303
    doc = docs[f"birim:{sample['department'].id}"]
    app.dependency_overrides.pop(require_user, None)
    ready_and_freeze(client, token, doc)
    frozen = sections.report_data(db, sample['strategy'], doc.id)
    assert frozen['core']['indicators'][0]['direction'] == 'lower'
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    assert client.post(url, data=dict(data, direction='higher', reason='Sonraki değerlendirme')).status_code == 303
    assert sections.core_summary(db, doc)['indicators'][0]['direction'] == 'higher'
    assert sections.report_data(db, sample['strategy'], doc.id)['core'] == frozen['core']
    actual = contract.report_data(db, sample['strategy'], report['revision_id'])['indicators'][0]['actuals'][0]
    assert actual['deviation']['delta'] == '1.000001'
    assert actual['deviation']['achievement_percent'] is None


@pytest.mark.postgres
def test_synthetic_setting_and_scorecard_screenshots(client, db, sample, tmp_path):
    from playwright.sync_api import sync_playwright
    from test_sunum_browser import browser_options
    sample['indicator'].name = 'Sentetik yanıt süresi'
    sample['indicator'].unit = 'Gün'
    pub = publish(client, db, sample)
    data = dict(snapshot_indicator_id=sample['indicator'].id, direction='lower', reason='Sentetik süre hedefi')
    assert client.post(f'/activity-reports/publications/{pub.id}/directions', data=data, follow_redirects=False).status_code == 303
    page_url = f'/activity-reports/publications/{pub.id}/bindings'
    deck = render_deck(idare_activity_report(dict(year=2027, unit_indicator_sources=[dict(
        department_id=1, department='Sentetik Müdürlük', core=dict(indicators=[indicator(20, direction='lower')]))])),
        title='Sentetik CIV-197', code='TASLAK')
    folder = Path(os.environ.get('CIVENSA_CIV197_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_options())
        page = browser.new_page(viewport=dict(width=1440, height=1100))
        def route(request):
            path = request.request.url.replace('http://testserver', '')
            response = client.get(path)
            request.fulfill(status=response.status_code, headers={'content-type': response.headers.get('content-type', 'text/html')}, body=response.content)
        page.route('http://testserver/**', route)
        page.goto('http://testserver' + page_url)
        page.locator('select[name=direction]').select_option('lower')
        page.locator('textarea[name=reason]').fill('Sentetik süre hedefi')
        page.locator('.indicator-bindings-page').screenshot(path=str(folder / 'direction-setting.png'))
        page.route('http://testserver/civ197-deck', lambda r: r.fulfill(content_type='text/html', body=deck))
        page.goto('http://testserver/civ197-deck')
        page.wait_for_function('() => window.sunumRendered === true')
        page.evaluate("deck.slide(deck.getIndices(document.querySelector('[data-type=scorecard]')).h)")
        page.locator('section.present [data-detail]').first.click()
        assert page.get_by_text('Sentetik yanıt süresi (düşük daha iyi)', exact=True).is_visible()
        page.screenshot(path=str(folder / 'lower-scorecard.png'), full_page=True, animations='disabled')
        browser.close()


@pytest.mark.postgres
def test_civ199_direction_save_returns_to_row_and_says_saved(client, db, sample):
    """CIV-199 (8): a successful save must be visible; the page must not silently jump to the top."""
    from playwright.sync_api import sync_playwright, expect
    from test_sunum_browser import browser_options
    sample['indicator'].name = 'Sentetik İşlem yanıt süresi'
    sample['indicator'].unit = 'Gün'
    pub = publish(client, db, sample)
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    sid = sample['indicator'].id
    page_url = f'/activity-reports/publications/{pub.id}/bindings'
    response = client.post(f'/activity-reports/publications/{pub.id}/directions', follow_redirects=False,
        data=dict(snapshot_indicator_id=sid, direction='lower', reason='Sentetik süre hedefi'))
    assert response.status_code == 303
    assert response.headers['location'] == f'{page_url}?saved=direction&row={sid}#gosterge-{sid}'
    html = client.get(response.headers['location'].split('#')[0]).text
    assert 'Kaydedildi: yön «Düşük değer daha iyi».' in html
    assert f'id="gosterge-{sid}"' in html and 'id="bindingSearch"' in html
    # Without the marker (or with a forged one) nothing claims a save.
    assert 'Kaydedildi:' not in client.get(page_url).text
    assert 'Kaydedildi:' not in client.get(f'{page_url}?saved=other&row={sid}').text
    assert 'Kaydedildi:' not in client.get(f'{page_url}?saved=direction&row=x').text
    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_options())
        context = browser.new_context(viewport=dict(width=1440, height=500))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def route(request):
            path = request.request.url.replace('http://testserver', '')
            if request.request.method == 'POST':
                result = client.post(path, content=request.request.post_data_buffer, follow_redirects=False,
                    headers={'content-type': request.request.headers['content-type']})
                if result.status_code == 303:
                    # Chromium does not send the follow-up GET of a fulfilled 303 back through the route
                    # (it fails with ERR_NAME_NOT_RESOLVED for testserver); hand the browser a plain
                    # navigation to the same Location, hash included, so the anchor behaviour is tested.
                    target = 'http://testserver' + result.headers['location']
                    request.fulfill(status=200, content_type='text/html',
                        body=f'<meta http-equiv="refresh" content="0;url={target}">')
                    return
                request.fulfill(status=result.status_code, headers=dict(result.headers), body=result.content)
                return
            result = client.get(path)
            request.fulfill(status=result.status_code, headers={'content-type': result.headers.get('content-type', 'text/html')}, body=result.content)
        context.route('http://testserver/**', route)
        page.goto('http://testserver' + page_url)
        page.locator('#bindingSearch').fill('yanıt süresi')
        expect(page.locator('#bindingSearchCount')).to_have_text('1 gösterge bulundu.')
        # Turkish casing: dotted capital İ must match dotted i (stored text keeps its casing).
        page.locator('#bindingSearch').fill('işlem YANIT SÜRESİ')
        expect(page.locator('#bindingSearchCount')).to_have_text('1 gösterge bulundu.')
        page.locator('#bindingSearch').fill('bulunmayan gösterge')
        expect(page.locator('#bindingSearchCount')).to_have_text('0 gösterge bulundu.')
        page.locator('#bindingSearch').fill('')
        row = page.locator(f'#gosterge-{sid}')
        save = row.get_by_role('button', name='Gösterge yönünü kaydet')
        # CIV-199 (14): inactive until the direction changes and a reason is written.
        expect(save).to_be_disabled()
        row.locator('textarea[name=reason]').fill('Sentetik düzeltme')
        expect(save).to_be_disabled()
        row.locator('select[name=direction]').select_option('higher')
        expect(save).to_be_enabled()
        row.locator('select[name=direction]').select_option('lower')
        expect(save).to_be_disabled()
        row.locator('select[name=direction]').select_option('higher')
        expect(save).to_be_enabled()
        # Wait for the POST -> 303 -> GET round trip itself; CI runners were slower than the 5 s default.
        with page.expect_navigation(url=f'**{page_url}?saved=direction&row={sid}*', timeout=20000):
            save.click()
        assert not errors, errors
        saved = page.locator(f'#gosterge-{sid} .binding-saved')
        expect(saved).to_have_text('Kaydedildi: yön «Yüksek değer daha iyi».')
        expect(saved).to_be_in_viewport()
        if os.getenv('CIVENSA_CIV199_ARTIFACTS'):
            page.screenshot(path=str(Path(os.environ['CIVENSA_CIV199_ARTIFACTS']) / 'gosterge-yonu-kaydedildi.png'))
        browser.close()
    app.dependency_overrides.pop(require_user, None)


def test_civ199_many_directorates_become_cards_with_dialogs(client, db, sample):
    """CIV-199 (11): more than three directorates -> card grid; indicators open in an in-page <dialog>."""
    from copy import deepcopy
    pub = publish(client, db, sample)
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    response = client.get(f'/activity-reports/publications/{pub.id}/bindings')
    rows = response.context['rows']
    assert 'binding-grid' not in response.text and '<dialog' not in response.text
    many = []
    for n in range(4):
        for row in rows:
            copy = deepcopy(row)
            copy['department'] = f'Sentetik Müdürlük {n}'
            many.append(copy)
    html = response.template.render({**response.context, 'rows': many})
    assert 'reports-panel binding-grid' in html
    assert html.count('<article class="binding-card" data-binding-card>') == 4
    assert html.count('<dialog class="binding-dialog"') == 4
    assert html.count('data-open-dialog="binding-dialog-') == 4
    assert '<details class="binding-dept"' not in html
