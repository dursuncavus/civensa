"""CIV-151: frozen publication/import contracts and synthetic browser evidence."""
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace as Record
from urllib.parse import urlsplit

from lxml.html import fromstring
from playwright.sync_api import expect
import pytest
from starlette.datastructures import FormData

from app.pp_display import status_label
from test_activity_mapping_gaps import strategy_client
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/report_builder_start'
HASHES = {
    'report_builder.html': 'd279dcd9d9e14de002851c908fbf37bfcb815912f7f9ec667f5a3d6a680ed23e',
    'pp_section_import.html': 'edc10068c2b4fa03126f971f4704483e82559bcc3de03d000e2672c68d7c30f4',
}


@pytest.fixture
def scenes(strategy_client, sample):
    response = strategy_client.get(f"/report-builder?period_id={sample['period'].id}")
    assert response.status_code == 200
    data = dict(response.context)
    departments = [Record(id=601+i, name=name) for i, name in enumerate([
        'Sentetik Park ve Bahçeler Müdürlüğü', 'Sentetik Fen İşleri Müdürlüğü',
        'Sentetik Kültür Müdürlüğü', 'Sentetik Sosyal Hizmetler Müdürlüğü'])]
    sections = [Record(id=701+i, position=i+1, title=title, kind=kind,
                       content_json=json.dumps(content, ensure_ascii=False))
        for i, (title, kind, content) in enumerate([
            ('Sentetik sunuş', 'text', {'text': 'Birinci satır\nİkinci satır & <içerik>', 'placement': 'before'}),
            ('Sentetik kurum tablosu', 'table', {'rows': [['Birim', 'Tutar'], ['Park', '12.500,23']], 'placement': 'after'}),
            ('Sentetik kurum görseli', 'image', {'caption': 'Görsel açıklaması', 'data': '', 'placement': 'before'})])]
    catalogue = [Record(id=801, program_code='1', program_name='Çevre hizmetleri',
        subprogram_code='1.1', subprogram_name='Yeşil alan', code='1.1.1', name='Sentetik park bakımı')]
    data.update(departments=departments, department_names={d.id: d.name for d in departments},
        scopes={d.id: Record(status=status, position=i+1, display_name=d.name, reason=reason)
            for i, (d, status, reason) in enumerate(zip(departments,
                ['required', 'zero', 'excluded'], ['', 'Sıfır bütçe gerekçesi', 'Kapsam gerekçesi']))},
        sections=sections, catalogue=catalogue, responsibilities={801: [601, 603]},
        source_periods=[Record(id=901, year=2026)],
        section_copy_result=Record(copied=2, kept=1, conflicts=[Record(
            message='Sentetik başlık çakışması; hedef içerik korundu.', target_ids=[701, 702])]),
        publications=[Record(id=1002, version=2, created_at=datetime(2026, 10, 29, 10), creator=sample['strategy']),
                      Record(id=1001, version=1, created_at=datetime(2026, 10, 28, 9), creator=None)],
        superseded_by={1001: 2}, stale_departments=[departments[0].name],
        publication_reopens={1002: [], 1001: [Record(department_name=departments[1].name,
            event=Record(actor=sample['strategy'], created_at=datetime(2026, 10, 28, 12),
                         note='Sentetik kaynak tutarı düzeltmesi.'))]},
        reconciliation=[Record(level='department', label='Sentetik birim', path='Program / Alt program / Birim',
            year=2027, value_kind='budget', amount=None, source_amount=12500, difference=None,
            complete=False, status='Yayın engeli', errors=['Sentetik maliyet eksik; kartı düzeltin.'],
            warnings=['Kaynak kontrolü gerekli.'])])
    return response.template.environment, data


def builder_data(data, state):
    data = dict(data)
    if state == 'empty':
        data.update(departments=[], scopes={}, sections=[], catalogue=[], responsibilities={},
                    source_periods=[], section_copy_result=None, publications=[], superseded_by={},
                    publication_reopens={}, stale_departments=[], reconciliation=[])
    elif state.startswith('failed-'):
        action = state.removeprefix('failed-')
        attempts = {
            'scope': [('department_id', '601'), ('position', 'yanlış'), ('display_name', 'Gönderilen <ad>'),
                      ('status', 'zero'), ('reason', '')],
            'section': [('id', '701'), ('position', '9'), ('title', 'Gönderilen <başlık>'),
                        ('placement', 'after'), ('kind', 'table'), ('content', 'Başlık\tTutar\nPark\t12.500,23')],
            'catalogue': [('id', '801'), ('program_code', '9'), ('program_name', 'Gönderilen program'),
                          ('subprogram_code', '9.1'), ('subprogram_name', 'Gönderilen alt program'),
                          ('code', '9.1.1'), ('name', 'Gönderilen faaliyet'),
                          ('department_ids', '602'), ('department_ids', '604')],
            'copy-sections': [('base_period_id', '901')],
            'publish': [],
            'fallback': [('id', '9999'), ('title', 'Listede bulunmayan bölüm'), ('content', 'Satır 1\nSatır 2')],
        }
        fields = attempts[action] + [('period_id', str(data['period'].id))]
        path = '/report-builder/' + ('section' if action == 'fallback' else action)
        field = {'scope': 'reason', 'section': 'content', 'catalogue': 'name',
                 'copy-sections': 'base_period_id', 'publish': 'publish', 'fallback': 'content'}[action]
        data['request'].state.pp_attempt = (path, FormData(fields), {
            'detail': 'Sentetik kayıt kaydedilemedi. İşaretli alanı düzeltip yeniden kaydedin.',
            'errors': [{'field': field, 'message': 'Sentetik alanı kontrol edin.'}]})
    return data


def import_data(data, state):
    items = [Record(title=f'Sentetik {action} {kind}', kind=kind, action=action,
                    content=Record(text='Birinci satır\n  Girintili ikinci satır & <metin>',
                        rows=[['Sentetik sütun '+str(i) for i in range(8)], ['12.500,23']*8]),
                    target_ids=[] if action == 'create' else [701, 702])
             for action in ('create', 'keep', 'conflict') for kind in ('text', 'table')]
    items.append(Record(title='Sentetik görsel', kind='image', action='create', content=Record(), target_ids=[]))
    return dict(data, batch=Record(id=1101, filename='sentetik-genel-bolumler.docx',
                                   status='applied' if state in {'revert', 'locked'} else 'preview'),
        preview=Record(general_sections=[] if state == 'empty' else items,
            warnings=['Sentetik kaynak uyarısı; dosyayı kontrol edin.'],
            general_section_warnings=['Sentetik bölüm uyarısı; hedef bölümü inceleyin.'],
            can_apply=state == 'apply', can_revert=state == 'revert',
            revert_reason='Bölüm düzenlendi; otomatik geri alma engellendi.'))


def render(env, name, data, before=False):
    data['request'].state.pp_attempt_rendered = False
    source = (FROZEN / name).read_bytes()
    assert sha256(source).hexdigest() == HASHES[name]
    template = env.from_string(source.decode()) if before else env.get_template(name)
    return template.render(data)


def contract(html):
    """All control attributes/values, form and details binding, hooks and links.

    sections.js uses IDs, data-batch-id/data-period-id and the DETAILS tag. It has
    no class selectors. Presentation class/style changes are intentionally outside
    this contract; every original class is checked separately below.
    """
    main = fromstring(html).get_element_by_id('main')
    controls, hooks, disclosures, labels = [], [], [], []
    for el in main.iter():
        if not isinstance(el.tag, str):
            continue
        attrs = tuple(sorted((k, v) for k, v in el.attrib.items() if k not in {'class', 'style'}))
        details = next((p for p in el.iterancestors('details')), None)
        form = next((p for p in el.iterancestors('form')), None)
        binding = (form.get('method'), form.get('action')) if form is not None else None
        disclosure = (details.get('id'), ' '.join(details.find('summary').itertext()).strip()) if details is not None else None
        # Summary punctuation is the only approved per-record text change.
        if disclosure:
            disclosure = (disclosure[0], re.sub(r'\s+', ' ', disclosure[1]).replace(' · ', ' '))
        if el.tag in {'form', 'input', 'textarea', 'select', 'option', 'button', 'a'}:
            value = el.text_content() if el.tag == 'textarea' else ' '.join(el.text_content().split()) if el.tag in {'option','button','a'} else ''
            controls.append((el.tag, attrs, value, binding, disclosure))
        attributes = tuple(sorted((k, v) for k, v in el.attrib.items()
            if k in {'id', 'role'} or k.startswith(('data-', 'aria-'))))
        if attributes:
            hooks.append((el.tag, attributes))
        if el.tag == 'details':
            disclosures.append((el.get('id'), 'open' in el.attrib))
        if el.tag == 'label':
            # Values belong to controls above; a label's own text stays identical.
            labels.append(' '.join((el.text or '').split()))
    return controls, hooks, disclosures, labels


def assert_original_classes(before, after):
    """Retain existing control/record/table classes, including danger on revert."""
    old, new = (fromstring(h).get_element_by_id('main') for h in (before, after))
    for selector in ('.//details', './/form', './/a', './/button', './/article', './/p[contains(concat(" ",normalize-space(@class)," ")," bad ")]'):
        left, right = old.xpath(selector), new.xpath(selector)
        assert len(left) == len(right)
        for a, b in zip(left, right):
            assert set(a.get('class', '').split()) <= set(b.get('class', '').split())


def words(html):
    main = fromstring(html).get_element_by_id('main')
    return ' '.join(' '.join(main.xpath('.//text()[not(ancestor::script or ancestor::style)]')).split())


def assert_visible_text(before, after, data, builder):
    """Only the explicitly listed title and punctuation changes are allowed."""
    expected = words(before)
    if builder:
        for dept in data['departments']:
            scope = data['scopes'].get(dept.id)
            status = status_label(scope.status) if scope else 'Belirtilmedi'
            name = data['department_names'][dept.id]
            expected = expected.replace(f'{name} · {status}', f'{name} {status}')
        for index, publication in enumerate(data['publications']):
            number = publication.version
            if index == 0:
                expected = expected.replace(f'Sürüm {number} · Güncel sürüm', f'Sürüm {number} Güncel sürüm')
            else:
                successor = data['superseded_by'][publication.id]
                expected = expected.replace(f'Sürüm {number} · Önceki sürüm — Sürüm {successor}',
                                            f'Sürüm {number} Önceki sürüm · Sürüm {successor}')
        actual = words(after)
        # This existing region label becomes a visible heading exactly once.
        assert actual.count('Yayın sürümleri') == expected.count('Yayın sürümleri') + 1
        actual = actual.replace('Yayın sürümleri ', '', 1) if 'Yayın sürümleri ' in actual else actual.removesuffix(' Yayın sürümleri')
    else:
        for item in data['preview'].general_sections:
            label = {'create': 'Eklenecek', 'keep': 'Mevcut bölüm korunacak',
                     'conflict': 'Çakışma — hedef bölüm korunacak'}[item.action]
            expected = expected.replace(f'{item.title} · {label}', f'{item.title} {label}')
        actual = words(after)
    assert actual == expected


@pytest.mark.parametrize('state', ['populated', 'empty', 'failed-scope', 'failed-section',
    'failed-catalogue', 'failed-copy-sections', 'failed-publish', 'failed-fallback'])
def test_builder_frozen_contract(scenes, state):
    env, base = scenes
    data = builder_data(base, state)
    before, after = (render(env, 'report_builder.html', data, old) for old in (True, False))
    assert contract(after) == contract(before)
    assert_original_classes(before, after)
    assert_visible_text(before, after, data, True)
    if state.startswith('failed-'):
        main = fromstring(after).get_element_by_id('main')
        assert all('open' in d.attrib for d in main.xpath('.//details[@class="record"]') if not d.xpath('.//select[@name="base_period_id"]'))
        assert main.xpath('.//*[@role="alert"]')
        if state == 'failed-catalogue':
            assert main.xpath('.//form[@action="/report-builder/catalogue"]//option[@selected]/@value') == ['602', '604']
        if state == 'failed-section':
            assert main.xpath('.//details[@id="section-701"]//textarea/text()') == ['\nBaşlık\tTutar\nPark\t12.500,23']


@pytest.mark.parametrize('state', ['apply', 'revert', 'locked', 'empty'])
def test_import_frozen_contract(scenes, state):
    env, base = scenes
    data = import_data(base, state)
    before, after = (render(env, 'pp_section_import.html', data, old) for old in (True, False))
    assert contract(after) == contract(before)
    assert_original_classes(before, after)
    assert_visible_text(before, after, data, False)
    old, new = (fromstring(h) for h in (before, after))
    assert old.xpath('.//p[@style="white-space:pre-wrap"]/text()') == new.xpath('.//p[@class="section-text"]/text()')
    assert [e.text_content() for e in old.xpath('.//td')] == [e.text_content() for e in new.xpath('.//td')]


def test_page_local_tokens_and_styles(strategy_client):
    css = Path('app/static/design/report-builder.css').read_text()
    tokens = Path('app/static/design/tokens.css').read_text()
    assert set(re.findall(r'var\((--[\w-]+)\)', css)) <= set(re.findall(r'(--[\w-]+):', tokens))
    assert not re.search(r'#[\da-fA-F]{3,8}\b|rgba?\(|hsla?\(|--[\w-]+\s*:', css)
    assert 'uppercase' not in css
    for value in re.findall(r'(?:font-size|padding|gap|border-radius)\s*:\s*([^;}]+)', css):
        assert 'var(--' in value or value.strip() == '0'
    assert 'report-builder.css' not in strategy_client.get('/dashboard?period_id=1').text
    assert 'report-builder.css' not in strategy_client.get('/report-builder/manifest?period_id=1').text


def capture(page, scene, before, width):
    folder = os.getenv('CIVENSA_CIV151_SCREENSHOTS')
    if folder and scene in {'populated', 'failed-section', 'apply'}:
        target = Path(folder) / f"{'before' if before else 'after'}-{'040' if scene == 'apply' else '039'}-{scene}-{width}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        page.mouse.move(0, 0)
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
        page.screenshot(path=str(target), full_page=True)
        assert target.stat().st_size <= 1_500_000


def assert_design(page, width, builder):
    selector = '.report-builder-page' if builder else '.section-import-page'
    root = page.locator(selector)
    assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
    assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
    assert root.locator('.button.primary').count() == 1
    for row in root.locator('summary,.publication-row h3,p,.report-fields').all():
        if row.is_visible():
            assert row.bounding_box()['width'] <= 704
    for form in root.locator('.report-fields').all():
        if not form.is_visible():
            continue
        columns = form.evaluate('el => getComputedStyle(el).gridTemplateColumns').split()
        assert len(columns) == (2 if width >= 1024 and form.get_attribute('action') != '/report-builder/publish' else 1)
        for label in form.locator('label:has(textarea),label:has(select[multiple])').all():
            assert abs(label.bounding_box()['width'] - form.bounding_box()['width']) <= 1
    pairs = set(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', selector))))
    for control in root.locator('summary,.button,a').all():
        if control.is_visible() and control.is_enabled():
            control.hover()
            control.focus()
            assert control.evaluate("el => getComputedStyle(el).outlineStyle === 'solid'")
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', selector))))
    assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('before', [True, False], ids=['before', 'after'])
@pytest.mark.parametrize('scene', ['populated', 'failed-section', 'apply', 'revert', 'empty-import'])
def test_browser_flows_layout_and_evidence(browser, scenes, strategy_client, width, before, scene):
    env, base = scenes
    builder = scene in {'populated', 'failed-section'}
    data = builder_data(base, scene) if builder else import_data(base, 'empty' if scene == 'empty-import' else scene)
    html = render(env, 'report_builder.html' if builder else 'pp_section_import.html', data, before)
    path = '/report-builder' if builder else '/report-builder/import/1101'
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR') as context:
        context.set_default_timeout(5000)
        pending, writes, errors = [], [], []

        def serve(route):
            request = route.request
            current = urlsplit(request.url).path
            if request.method == 'POST' and current.startswith('/api/import-batches/'):
                writes.append(request)
                pending.append(route)
            elif current == path:
                route.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)
            else:
                response = strategy_client.get(request.url, follow_redirects=False)
                headers = dict(response.headers)
                headers.pop('set-cookie', None)
                route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f"http://testserver{path}?period_id={data['period'].id}" + ('#section-701' if builder else ''))
        page.evaluate('document.fonts.ready')
        if builder:
            expect(page.locator('#section-701')).to_have_attribute('open', '')
        else:
            for summary in page.locator('details > summary').all():
                summary.click()
        capture(page, scene, before, width)
        if not before:
            if scene == 'empty-import':
                assert page.locator('.button.primary').count() == 0
                assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            else:
                assert_design(page, width, builder)
        if builder:
            page.evaluate("location.hash='new-section'")
            expect(page.locator('#new-section')).to_have_attribute('open', '')
            page.evaluate("location.hash='section-702'")
            expect(page.locator('#section-702')).to_have_attribute('open', '')
            if scene == 'failed-section':
                expect(page.locator('#section-701 input[name=title]')).to_have_value('Gönderilen <başlık>')
                expect(page.locator('#section-701 textarea')).to_have_value('Başlık\tTutar\nPark\t12.500,23')
                expect(page.locator('#section-701 textarea')).to_have_attribute('aria-invalid', 'true')
            expect(page.locator('[data-publication-version="2"] .publication-links a' if not before else '[data-publication-version="2"] a')).to_have_count(3)
        elif scene != 'empty-import':
            action = 'apply' if scene == 'apply' else 'revert'
            button = page.locator('#applySections' if scene == 'apply' else '#revertSections')
            button.click()
            expect(button).to_be_disabled()
            assert len(pending) == 1
            assert urlsplit(writes[0].url).path == '/api/import-batches/1101/' + action
            assert urlsplit(writes[0].url).query == ''
            pending.pop().fulfill(status=422, json={'detail': 'Sentetik içe aktarma uygulanamadı; hedef bölümü kontrol edin.'})
            expect(button).to_be_enabled()
            expect(page.locator('#toast')).to_contain_text('Sentetik içe aktarma uygulanamadı')
            button.click()
            expect(button).to_be_disabled()
            pending.pop().fulfill(status=200, json={'ok': True})
            expect(page).to_have_url(f"http://testserver/report-builder/manifest?period_id={data['period'].id}")
        else:
            expect(page.get_by_text('Kaynakta tanınan genel bölüm bulunamadı.', exact=False)).to_be_visible()
        assert not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('before', [True, False], ids=['before', 'after'])
def test_native_forms_save_and_publish_gate_in_real_handlers(browser, strategy_client, db, sample, width, before):
    """Submit all five native forms through unchanged handlers and disposable DB."""
    from sqlalchemy import select
    from app.models import DepartmentScope, OfficialActivity, ReportingPeriod, ReportSection

    source = ReportingPeriod(year=2026, status='draft')
    db.add(source)
    db.flush()
    db.add(ReportSection(period_id=source.id, position=1, title='Sentetik kaynak bölüm',
                         kind='text', content_json='{"text":"Sentetik kaynak içeriği"}'))
    db.commit()
    period_id, department_id = sample['period'].id, sample['department'].id
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR') as context:
        context.set_default_timeout(5000)
        writes, errors = [], []

        def serve(route):
            request = route.request
            response = strategy_client.request(request.method, request.url,
                content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=False)
            if request.method == 'POST':
                writes.append((urlsplit(request.url).path, response.status_code))
            if response.status_code == 303:
                # Playwright routes only the first URL of an HTTP redirect.
                # Resolve this local TestClient hop here; never send the fake
                # testserver hostname to the environment's outbound proxy.
                assert response.headers['location'] == f'/report-builder?period_id={period_id}'
                response = strategy_client.get(response.headers['location'])
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            body = response.content
            if before and getattr(response, 'template', None) and response.template.name == 'report_builder.html':
                body = render(response.template.environment, 'report_builder.html', dict(response.context), True).encode()
                headers.pop('content-length', None)
            route.fulfill(status=response.status_code, headers=headers, body=body)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/report-builder?period_id={period_id}')
        scope = page.locator('form[action="/report-builder/scope"]').first
        scope.locator('xpath=ancestor::details/summary').click()
        scope.locator('[name=position]').fill('7')
        scope.locator('[name=display_name]').fill('Sentetik dönem adı')
        with page.expect_navigation():
            scope.get_by_role('button', name='Kapsamı Kaydet', exact=True).click()
        db.expire_all()
        saved_scope = db.scalar(select(DepartmentScope).where(DepartmentScope.department_id == department_id,
                                                             DepartmentScope.period_id == period_id))
        assert (saved_scope.position, saved_scope.display_name, saved_scope.status) == (7, 'Sentetik dönem adı', 'required')
        page.evaluate("location.hash='new-section'")
        section = page.locator('#new-section form')
        section.locator('[name=title]').fill('Sentetik tarayıcı bölümü')
        section.locator('[name=placement]').select_option('after')
        section.locator('[name=content]').fill('Birinci satır\nİkinci satır & <içerik>')
        with page.expect_navigation():
            section.get_by_role('button', name='Bölümü Kaydet', exact=True).click()
        db.expire_all()
        saved = db.scalar(select(ReportSection).where(ReportSection.title == 'Sentetik tarayıcı bölümü'))
        assert saved.period_id == period_id
        assert json.loads(saved.content_json) == {'text': 'Birinci satır\r\nİkinci satır & <içerik>', 'placement': 'after'}
        copy = page.locator('form[action="/report-builder/copy-sections"]')
        copy.locator('xpath=ancestor::details/summary').click()
        copy.locator('[name=base_period_id]').select_option(str(source.id))
        with page.expect_navigation():
            copy.get_by_role('button', name='Genel Bölümleri Kopyala', exact=True).click()
        expect(page.locator('[role=status]')).to_contain_text('1 bölüm kopyalandı')
        db.expire_all()
        assert db.scalar(select(ReportSection.id).where(ReportSection.title == 'Sentetik kaynak bölüm',
                                                        ReportSection.period_id == period_id))
        catalogue = page.locator('form[action="/report-builder/catalogue"]').last
        catalogue.locator('xpath=ancestor::details/summary').click()
        values = {'program_code': '9', 'program_name': 'Sentetik program', 'subprogram_code': '9.1',
                  'subprogram_name': 'Sentetik alt program', 'code': '9.1.1', 'name': 'Sentetik katalog faaliyeti'}
        for name, value in values.items():
            catalogue.locator(f'[name={name}]').fill(value)
        catalogue.locator('[name=department_ids]').select_option(str(department_id))
        with page.expect_navigation():
            catalogue.get_by_role('button', name='Kataloğu Kaydet', exact=True).click()
        db.expire_all()
        saved_item = db.scalar(select(OfficialActivity).where(OfficialActivity.name == values['name']))
        assert saved_item.period_id == period_id
        assert all(getattr(saved_item, name) == value for name, value in values.items())
        with page.expect_navigation():
            page.get_by_role('button', name='Kontrol Et ve Nihai Sürümü Oluştur', exact=True).click()
        expect(page.locator('form[action="/report-builder/publish"] [role=alert]')).to_be_visible()
        assert writes == [('/report-builder/scope', 303), ('/report-builder/section', 303),
                          ('/report-builder/copy-sections', 200), ('/report-builder/catalogue', 303),
                          ('/report-builder/publish', 422)]
        assert not errors
