"""CIV-183: pinned council facts, popup navigation, print pages and rounding."""
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
import logging
import os
from pathlib import Path

from lxml import html
import pytest
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader

from app.sunum import render_deck
from app.sunum.engine import prepare_slides
from app.sunum.meclis import budget_distribution, scorecard
from app.sunum.recipes_idare import idare_activity_report
from test_sunum_idare import idare_fixture, by_title
from test_activity_sections import section_client
from test_sunum_browser import browser_options, deck_url

pytestmark = pytest.mark.postgres


def indicator(actual=100, target=100, **extra):
    return dict(name='Gösterge', actual=actual, actual_state='verified',
        targets=[dict(value=target, state='verified')], **extra)


def test_unmeasurable_targets_and_actuals_zero_and_exact_status_boundaries():
    base = indicator()
    excluded = [dict(base, actual=None), dict(base, actual=''), dict(base, actual='NaN'),
        dict(base, actual_state='needs_review'), dict(base, targets=[]),
        dict(base, targets=[dict(value=100, state='needs_review')]),
        dict(base, targets=base['targets']*2), dict(base, targets=[dict(value=None, state='verified')])]
    rows = scorecard([dict(department_id=i, department=f'Müdürlük {i}',
        core=dict(indicators=[indicator()]*met + [indicator(50)]*(10-met) + excluded))
        for i, met in enumerate([9, 7, 6])])
    assert [(r['measured'], r['met'], r['rate'], r['status']) for r in rows] == [
        (10, 9, 90, 'Hedefte'), (10, 7, 70, 'Yakın'), (10, 6, 60, 'Geride')]
    assert [r['expandable'] for r in rows] == [False, True, True]
    assert rows[1]['missed'][0]['reason'] == '—'
    zero, blank = scorecard([dict(core=dict(indicators=[indicator(actual=0, target=0)])),
        dict(core=dict(indicators=excluded))])
    assert (zero['measured'], zero['met'], zero['status']) == (1, 1, 'Hedefte')
    assert (blank['rate'], blank['status'], blank['percentage'], blank['missed']) == (None, '', '—', [])
    explanation = scorecard([dict(core=dict(indicators=[indicator(20, explanation='Gecikme',
        deviation=dict(corrective_action='Yeni takvim', delta='-80', achievement_percent=None))]))])[0]
    assert explanation['missed'][0]['reason'] == 'Gecikme\nYeni takvim'
    many = scorecard([dict(core=dict(indicators=[base]*1000))])[0]
    assert many['measured_display'] == many['met_display'] == '1.000'


@pytest.mark.parametrize('idare_fixture', [dict(council=True)], indirect=True)
def test_approved_fixture_scorecard_distribution_and_group_order(idare_fixture):
    payload = idare_fixture['enriched']
    before = deepcopy(payload)
    slides = prepare_slides(idare_activity_report(payload))
    score = by_title(slides, 'Amaçlarımıza ne kadar yaklaştık?')
    assert [(r['met'], r['measured'], r['rate'], r['status']) for r in score['rows']] == [
        (10, 10, 100, 'Hedefte'), (8, 10, 80, 'Yakın'), (6, 10, 60, 'Geride')]
    assert [r['count'] for r in score['summary']] == [1, 1, 1]
    assert score['rows'][2]['missed'][0]['reason'] == '—'
    budget = by_title(slides, 'Her 100 TL nereye harcandı?')
    assert [b['share'] for b in budget['boxes']] == [34, 27, 22, 6, 6, 5]
    assert budget['boxes'][-1]['name'] == 'Diğer (faiz, sermaye transferi)'
    assert [row['name'] for row in budget['top']] == ['Mal ve hizmet alımına',
        'Yatırımlara (sermaye giderleri)', 'Personel giderlerine']
    assert sum(Decimal(str(b['share'])) for b in budget['boxes']) == Decimal('100.0')
    titles = [s.get('title') for s in slides]
    assert titles.index('Bütçe bir bakışta') + 1 == titles.index(budget['title'])
    assert titles.index(score['title']) + 1 == titles.index('Müdürlüklere göre gösterge özeti')
    assert score['section'] == 't3' and budget['section'] == 't2'
    assert payload == before


@pytest.mark.parametrize('idare_fixture', [dict(blank_economic=True), dict(missing_budget=True)], indirect=True)
def test_incomplete_economic_actual_omits_distribution_and_logs(idare_fixture, caplog):
    with caplog.at_level(logging.INFO):
        response = idare_fixture['client'].get(f"/activity-sections/reports/{idare_fixture['idare'].id}/sunum.html")
    assert response.status_code == 200
    assert 'Her 100 TL nereye harcandı?' not in html.fromstring(response.content).xpath('//h2/text()')
    assert 'Bu raporda ekonomik sınıflandırmaya göre eksiksiz harcama dağılımı bilgisi yok' in caplog.text


def test_distribution_rounding_total_validation_and_subcodes():
    payload = dict(financial=dict(tables=dict(expenditure=dict(rows=[
        dict(economic_code=code, actual=1) for code in ['01', '03.01', '06']],
        totals=dict(actual=dict(value=3, missing=0))))))
    result = budget_distribution(payload)
    assert [box['display'] for box in result['boxes']] == ['33,4', '33,3', '33,3']
    assert sum(Decimal(str(box['share'])) for box in result['boxes']) == 100
    assert [row['display'] for row in result['top']] == ['33,4', '33,3', '33,3']
    for bad in [None, '', -1, 'NaN']:
        copy = deepcopy(payload)
        copy['financial']['tables']['expenditure']['rows'][0]['actual'] = bad
        assert budget_distribution(copy) is None
    payload['financial']['tables']['expenditure']['totals']['actual']['value'] = 4
    assert budget_distribution(payload) is None


def test_scorecard_six_row_pagination_unique_popup_ids_and_table_markers():
    sources = [dict(department_id=i, core=dict(indicators=[indicator(50)])) for i in range(13)]
    prepared = prepare_slides(idare_activity_report(dict(year=2027, unit_indicator_sources=sources)))
    cards = [s for s in prepared if s['type'] == 'scorecard']
    assert [len(s['rows']) for s in cards] == [6, 6, 1]
    assert [s['continuation'] for s in cards] == ['Tablo 1/3', 'Tablo 2/3', 'Tablo 3/3']
    ids = [row['popup_id'] for s in cards for row in s['rows']]
    assert len(ids) == len(set(ids))
    for count in [1, 10, 11]:
        content = render_deck([dict(type='table', title='Test', source='Test', headers=['Ad'],
            rows=[['Veri']]*count)], title='Test', code='TASLAK')
        assert b'Tablo 1/1' not in content
        if count > 10:
            assert b'Tablo 1/2' in content and b'Tablo 2/2' in content


@pytest.mark.parametrize('idare_fixture', [dict(council=True)], indirect=True)
def test_popup_browser_keyboard_pdf_pages_and_screenshots(idare_fixture, tmp_path):
    response = idare_fixture['client'].get(f"/activity-sections/reports/{idare_fixture['idare'].id}/sunum.html")
    assert response.status_code == 200
    assert len(response.content) <= 3_000_000
    path = tmp_path / 'meclis.html'
    path.write_bytes(response.content)
    folder = Path(os.environ.get('CIVENSA_MECLIS_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'single-file-size.txt').write_text(f'{len(response.content)} bytes\n')
    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_options())
        page = browser.new_page(viewport=dict(width=1920, height=1080), offline=True)
        errors, network = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: network.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        url = deck_url(page, path)
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        page.evaluate("deck.slide(deck.getIndices(document.querySelector('[data-type=scorecard]')).h)")
        page.wait_for_timeout(1500)
        index = page.evaluate('deck.getIndices().h')
        page.screenshot(path=str(folder / 'karne.png'))
        trigger = page.locator('section.present [data-detail]').first
        trigger.click()
        expect(page.locator('.pop.open')).to_be_visible()
        page.keyboard.press('ArrowRight')
        assert page.evaluate('deck.getIndices().h') == index
        assert page.evaluate('deck.getConfig().keyboard') is False
        page.wait_for_timeout(400)
        page.screenshot(path=str(folder / 'karne-acilim.png'))
        page.keyboard.press('Escape')
        expect(page.locator('.pop.open')).to_have_count(0)
        assert page.evaluate('deck.getIndices().h') == index
        assert page.evaluate('deck.getConfig().keyboard') is True
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(600)
        assert page.evaluate('deck.getIndices().h') == index + 1
        page.evaluate('i=>deck.slide(i)', index)
        page.wait_for_timeout(600)
        trigger.press('Enter')
        page.locator('.pop.open .x').click()
        expect(page.locator('.pop.open')).to_have_count(0)
        trigger.click()
        page.evaluate('i=>deck.slide(i+1)', index)
        expect(page.locator('.pop.open')).to_have_count(0)
        assert page.evaluate('deck.getConfig().keyboard') is True
        page.evaluate("deck.slide(deck.getIndices(document.querySelector('[data-type=budget]')).h)")
        page.wait_for_timeout(1600)
        expect(page.locator('section.present .tm svg')).to_be_visible()
        option = page.locator('section.present .tm').evaluate('el=>echarts.getInstanceByDom(el).getOption()')
        assert option['series'][0]['type'] == 'treemap'
        assert len(option['series'][0]['data']) == 6
        page.screenshot(path=str(folder / 'butce-dagilimi.png'))
        assert network == ([url] if url.startswith('http:') else [])
        page.goto(url + '#pdf')
        page.wait_for_function('() => window.sunumRendered === true')
        assert page.locator('section.pdf-detail').count() == 2
        assert page.locator('.pdf-detail .x, .pdf-detail .hint').count() == 0
        assert page.evaluate('''() => [...document.querySelectorAll('section[data-type=scorecard]')].every(s=>{
            let next=s.closest('.pdf-page').nextElementSibling?.querySelector('section');
            for(let i=0;i<s.querySelectorAll('[data-detail]').length;i++){
                if(next?.dataset.parent!==s.id) return false;
                next=next.closest('.pdf-page').nextElementSibling?.querySelector('section');
            } return true;
        })''')
        pdf_bytes = page.pdf(prefer_css_page_size=True, print_background=True)
        pdf = PdfReader(BytesIO(pdf_bytes))
        texts = [page.extract_text() for page in pdf.pages]
        # Chromium positions the Latin-ext glyph runs separately in the PDF.
        card_index = next(i for i, text in enumerate(texts) if
            'Amaçlarımızanekadaryaklaştık?' in ''.join(text.split()))
        assert 'hedefi tutmayan 2 gösterge' in texts[card_index+1]
        assert 'hedefi tutmayan 4 gösterge' in texts[card_index+2]
        assert 'Müdürlüklere göre gösterge özeti' in texts[card_index+3]
        assert len(pdf.pages) == page.locator('.slides section').count()
        page.add_style_tag(content='.pdf-help{display:none!important}')
        page.locator('section.pdf-detail').first.locator('..').screenshot(path=str(folder / 'pdf-acilim.png'))
        assert errors == []
        browser.close()


def test_long_popup_scrolls_and_pdf_continuations_stay_with_their_card(tmp_path):
    sources = [dict(department_id=i, department=f'Müdürlük {i}',
        core=dict(indicators=[indicator(50, explanation='Uzun sapma açıklaması. '*12)]*12)) for i in range(7)]
    slides = idare_activity_report(dict(year=2027, unit_indicator_sources=sources))
    path = tmp_path / 'long-popup.html'
    path.write_bytes(render_deck(slides, title='Test', code='TASLAK'))
    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_options())
        page = browser.new_page(viewport=dict(width=1920, height=1080), offline=True)
        url = deck_url(page, path)
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        page.evaluate("deck.slide(deck.getIndices(document.querySelector('[data-type=scorecard]')).h)")
        page.locator('section.present [data-detail]').first.click()
        assert page.locator('.pop.open .popbody').evaluate('el=>el.scrollHeight>el.clientHeight')
        page.keyboard.press('End')
        page.keyboard.press('Escape')
        page.goto(url + '#pdf')
        page.wait_for_function('() => window.sunumRendered === true')
        sequence = page.locator('.slides section').evaluate_all('els=>els.map(el=>[el.dataset.type,el.id,el.dataset.parent])')
        cards = [i for i, s in enumerate(sequence) if s[0] == 'scorecard']
        assert len(cards) == 2
        assert [s[2] for s in sequence[cards[0]+1:cards[1]]] == [sequence[cards[0]][1]]*6
        assert sequence[cards[1]+1][2] == sequence[cards[1]][1]
        assert page.locator('section.pdf-detail').count() == 7
        assert page.locator('.pdf-detail .popbody').first.evaluate('el=>el.scrollHeight<=el.clientHeight+1')
        pdf = PdfReader(BytesIO(page.pdf(prefer_css_page_size=True, print_background=True)))
        assert len(pdf.pages) == len(sequence)
        assert pdf.pages[cards[0]+1].extract_text().count('Gösterge') == 12
        browser.close()
