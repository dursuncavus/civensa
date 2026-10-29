"""CIV-153: frozen money-form contract, real split flows and synthetic evidence."""
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
import re
from types import SimpleNamespace as Record

from lxml.html import fromstring
from playwright.sync_api import expect
import pytest
from starlette.datastructures import FormData

from test_activity_mapping_gaps import strategy_client
from test_programme_split import split_rows, payload
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/economic_split_start/economic_split.html'
FROZEN_SHA = 'b8c0f2a0e5f13550ddf29ba6dea22d4dc3dea15ea96c3297b9b016b69f3fa5d4'


def normalized(text):
    return ' '.join(text.split())


@pytest.fixture
def scenes(strategy_client, sample):
    response = strategy_client.get(f"/program/{sample['department'].id}/economic-split?period_id={sample['period'].id}")
    assert response.status_code == 200
    data = dict(response.context)
    cards = [Record(source_title=f'Sentetik kart {i+1}', source_page=page,
        subprogram=Record(name='Sentetik alt program', program=Record(name=name)))
        for i, (page, name) in enumerate([('41, 42', 'Sentetik Hizmet Programı'),
                                        ('43', 'Yönetim ve Destek Programı'),
                                        (None, 'Sentetik Kültür Programı')])]
    cells = [Record(id=601+i, year=2027+i, value_kind='budget' if i == 0 else 'estimate',
        category='personnel', funding_type='inside', amount=amount,
        raw_text=raw, source_table_number=7 if i != 2 else None, issue=issue)
        for i, (amount, raw, issue) in enumerate([
            (Decimal('12500000.23'), '12.500.000,23', 'Sentetik kaynak uyarısı; tutarı kaynak tabloyla doğrulayın.'),
            (Decimal('0.00'), '0,00', ''),
            (None, '', 'Sentetik kaynak tutarı belirsiz; program sayfasından doğrulayın.')])]
    data.update(department=Record(id=sample['department'].id, name='Sentetik Park ve Bahçeler Müdürlüğü'),
                cards=cards, cells=cells, pages={601: '41, 42', 602: '43'},
                fingerprint=lambda cell: f'synthetic-fingerprint-{cell.id}',
                data={}, saved=0, error=None, blocked=False)
    return response.template.environment, data


def scene_data(base, state):
    data = dict(base)
    if state == 'empty':
        data.update(cells=[], cards=[])
    elif state == 'saved':
        data.update(saved=3, cells=[])
    elif state == 'blocked':
        data['blocked'] = True
    elif state == 'server-error':
        data.update(error='Sentetik dağılım kaydedilemedi. Payları düzeltip yeniden kaydedin.',
            data=FormData([('share_601_service', '12.000.000,00'),
                ('share_601_management', '100,23'), ('share_601_outside_program', ''),
                ('share_602_service', ''), ('zero_group_602', 'outside_program'),
                ('fingerprint_601', 'posted-stale-fingerprint'),
                ('reason', 'Gönderilen gerekçe <kaynak> & kontrol\nİkinci satır')]))
    return data


def render(env, data, before=False):
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == FROZEN_SHA
    template = env.from_string(source.decode()) if before else env.get_template('economic_split.html')
    return template.render(data)


def contract(html):
    """Every non-presentation attribute, control value and relevant DOM binding.

    app.js finds the form, error panel and submit button by ID/type and each
    share/output through its own TR. Compare these ancestors as well as attrs.
    Added presentation wrappers/classes and the page-local stylesheet are excluded.
    """
    main = fromstring(html).get_element_by_id('main')
    result = []
    for el in main.iter():
        if not isinstance(el.tag, str) or el.tag == 'link':
            continue
        attrs = tuple(sorted((k, v) for k, v in el.attrib.items() if k not in {'class', 'style'}))
        if not attrs and el.tag not in {'fieldset', 'details', 'textarea', 'output', 'option'}:
            continue
        ancestors = tuple((p.tag, p.get('id'), p.get('data-split-cell'))
            for p in el.iterancestors() if p.tag in {'form', 'fieldset', 'tr', 'details'})
        value = el.text_content() if el.tag == 'textarea' else (
            normalized(el.text_content()) if el.tag in {'option', 'button', 'a', 'output'} else '')
        result.append((el.tag, attrs, value, ancestors))
    return result


@pytest.mark.parametrize('state', ['populated', 'server-error', 'blocked', 'empty', 'saved'])
def test_frozen_contract(scenes, state):
    env, base = scenes
    data = scene_data(base, state)
    before, after = (render(env, data, old) for old in (True, False))
    assert contract(after) == contract(before)
    old, new = (fromstring(h).get_element_by_id('main') for h in (before, after))
    assert normalized(' '.join(old.xpath('.//text()'))) == normalized(' '.join(new.xpath('.//text()')))
    for tag in ('p', 'a', 'details', 'div[@id="economicSplitErrors"]', 'button'):
        left, right = old.xpath('.//'+tag), new.xpath('.//'+tag)
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert set(a.get('class', '').split()) <= set(b.get('class', '').split())
    assert old.xpath('.//strong/text()') == new.xpath('.//strong/text()')
    if state in {'populated', 'blocked'}:
        assert new.xpath('.//input[@data-split-share]/@value') == [''] * 9
        assert new.xpath('.//tr[@data-split-cell]/@data-source-amount') == ['12500000.23', '0.00', '']
    if state == 'server-error':
        assert new.xpath('.//option[@selected]/@value') == ['outside_program']


def test_page_local_token_styles(strategy_client):
    css = Path('app/static/design/economic-split.css').read_text()
    tokens = Path('app/static/design/tokens.css').read_text()
    assert set(re.findall(r'var\((--[\w-]+)\)', css)) <= set(re.findall(r'(--[\w-]+):', tokens))
    assert not re.search(r'#[\da-fA-F]{3,8}\b|rgba?\(|hsla?\(|--[\w-]+\s*:', css)
    assert 'uppercase' not in css
    assert '/static/design/economic-split.css' not in strategy_client.get('/program/1?period_id=1').text


def assert_visuals(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    root = page.locator('.economic-split-page')
    assert root.evaluate("el => [...el.querySelectorAll('*')].every(e => getComputedStyle(e).textTransform !== 'uppercase')")
    pairs = page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.economic-split-page'))
    assert pairs and min(map(contrast, pairs)) >= 4.5
    assert root.locator('.split-info').evaluate('el => el.getBoundingClientRect().width <= 704')
    assert root.locator('.split-reason').evaluate('el => el.getBoundingClientRect().width <= 704')
    field = root.locator('[data-split-share]').first
    assert field.evaluate("el => getComputedStyle(el).textAlign") == 'right'
    assert field.evaluate("el => getComputedStyle(el).fontVariantNumeric") == 'tabular-nums'
    # The longest required money display fits without clipping inside the input.
    assert field.evaluate("""el => {
      const style = getComputedStyle(el), canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d'); ctx.font = style.font;
      return ctx.measureText('12.500.000,00').width <= el.clientWidth -
        parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    }""")
    for selector in ('.button', '.button.primary', 'summary', '[data-split-share]', 'select', 'textarea'):
        control = root.locator(selector).first
        control.hover()
        assert min(map(contrast, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.economic-split-page')))) >= 4.5
        if control.is_enabled():
            control.focus()
            assert control.evaluate("el => getComputedStyle(el).outlineStyle") != 'none'
            assert min(map(contrast, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.economic-split-page')))) >= 4.5
    # The scroll container has room for the input focus outline on both edges.
    if field.is_enabled():
        field.focus()
        assert field.evaluate("""el => {
          const box = el.getBoundingClientRect(), wrap = el.closest('.table-wrap').getBoundingClientRect();
          return box.left - 4 >= wrap.left && box.right + 4 <= wrap.right;
        }""")


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('state', ['populated', 'server-error', 'blocked'])
@pytest.mark.parametrize('before', [True, False], ids=['before', 'after'])
def test_browser_synthetic_evidence(scenes, strategy_client, browser, width, state, before):
    env, base = scenes
    data = scene_data(base, state)
    html = render(env, data, before)
    errors = []
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            if route.request.resource_type == 'document':
                route.fulfill(status=422 if state == 'server-error' else 200, content_type='text/html', body=html)
            else:
                response = strategy_client.get(route.request.url)
                route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/program/1/economic-split?period_id=1')
        expect(page.locator('.record')).to_have_attribute('open', '')
        if state == 'populated':
            field = page.locator('[name=share_601_service]')
            field.fill('12.000.000,00')
            expect(page.locator('[data-split-cell="601"] output')).to_have_text('500.000,23')
            page.locator('[name=zero_group_602]').select_option('service')
        elif state == 'server-error':
            expect(page.locator('#economicSplitErrors')).to_be_visible()
            expect(page.locator('[name=share_601_service]')).to_have_value('12.000.000,00')
            expect(page.locator('[name=zero_group_602]')).to_have_value('outside_program')
            expect(page.locator('[name=reason]')).to_have_value(data['data']['reason'])
        else:
            expect(page.locator('fieldset')).to_have_attribute('disabled', '')
            expect(page.locator('[data-split-share]').first).to_be_disabled()
            expect(page.locator('button[type=submit]')).to_be_disabled()
            if not before:
                assert page.locator('button[type=submit]').evaluate("""el => {
                  const select = document.querySelector('select');
                  return getComputedStyle(el).backgroundColor === getComputedStyle(select).backgroundColor &&
                    getComputedStyle(el).color === getComputedStyle(select).color;
                }""")
        if not before:
            assert_visuals(page)
        # Capture after the interaction checks, at the top with table scroll reset.
        page.evaluate("document.querySelectorAll('.table-wrap').forEach(el => el.scrollLeft=0); window.scrollTo(0,0); document.activeElement.blur()")
        directory = os.getenv('CIVENSA_CIV153_EVIDENCE_DIR')
        if directory:
            output = Path(directory) / f'{"before" if before else "after"}-{state}-{width}.png'
            output.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output), full_page=True)
            assert output.stat().st_size <= 1_500_000
            if state == 'populated':
                page.evaluate("document.querySelector('[data-split-remaining]').closest('.table-wrap').scrollLeft=10000")
                money_output = output.with_name(output.stem.replace('populated', 'populated-money') + '.png')
                page.screenshot(path=str(money_output), full_page=True)
                assert money_output.stat().st_size <= 1_500_000
        assert not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('before', [True, False], ids=['before', 'after'])
def test_real_browser_split_flow(strategy_client, db, sample, split_rows, browser, width, before):
    """Existing atomic split, HTML error re-render and JSON submit at both sizes."""
    department_id, period_id = sample['department'].id, sample['period'].id
    path = f'/program/{department_id}/economic-split?period_id={period_id}'
    posted = payload(split_rows)
    posted['zero_group_'+str(next(r.id for r in split_rows if r.amount == 0))] = 'outside_program'
    posted['reason'] = ''
    failed = strategy_client.post(path, data=posted, follow_redirects=False)
    assert failed.status_code == 422
    errors, writes = [], []
    first = True
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            nonlocal first
            req = route.request
            if req.resource_type == 'document' and first:
                response = failed
                first = False
            else:
                response = strategy_client.request(req.method, req.url, content=req.post_data_buffer,
                    headers={'content-type': req.headers.get('content-type', ''),
                             'Accept': req.headers.get('accept', '')},
                    follow_redirects=req.resource_type in {'fetch', 'xhr'})
            if req.method == 'POST':
                writes.append(response.status_code)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            body = response.content
            if before and getattr(response, 'template', None) and response.template.name == 'economic_split.html':
                body = render(response.template.environment, dict(response.context), True).encode()
                headers.pop('content-length', None)
            route.fulfill(status=response.status_code, headers=headers, body=body)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver'+path)
        expect(page.locator('#economicSplitErrors')).to_be_visible()
        for key, value in posted.items():
            if key.startswith('share_'):
                expect(page.locator(f'[name="{key}"]')).to_have_value(value)
            elif key.startswith('zero_group_'):
                field = page.locator(f'[name="{key}"]')
                if field.count():
                    expect(field).to_have_value(value)
        expect(page.locator('[name=reason]')).to_have_value('')
        page.locator('[name=reason]').fill('Sentetik tarayıcı dağılım gerekçesi')
        row = next(r for r in split_rows if r.amount > 0)
        field = page.locator(f'[name=share_{row.id}_service]')
        original = field.input_value()
        field.fill('0')
        expect(page.locator(f'[data-split-cell="{row.id}"] output')).not_to_have_text('0,00')
        page.locator('button[type=submit]').click()
        expect(page.locator('#economicSplitErrors')).to_contain_text('Payları düzeltin.')
        expect(page.locator('#economicSplitErrors')).to_be_focused()
        expect(field).to_have_value('0')
        field.fill(original)
        expect(page.locator('[data-split-remaining]').filter(has_text='0,00')).to_have_count(len(split_rows))
        page.locator('button[type=submit]').click()
        expect(page.locator('p[role=status]')).to_contain_text('denetim kaydıyla birlikte kaydedildi')
        expect(page).to_have_url(re.compile(r'economic-split\?period_id=\d+&saved='))
        assert writes == [422, 200]
        assert not errors
        if not before:
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            pairs = page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.economic-split-page'))
            assert pairs and min(map(contrast, pairs)) >= 4.5
