"""CIV-152: byte-frozen form contracts, synthetic evidence and real POST flows."""
from hashlib import sha256
import os
from pathlib import Path
from urllib.parse import urlsplit

from lxml.html import fromstring
from playwright.sync_api import expect
import pytest
from sqlalchemy import select
from starlette.requests import Request

from app.main import templates
from test_activity_sections import section_client, login
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path(__file__).parent / 'fixtures/bindings_financial_import_start'
HASHES = {
    'activity_contract_bindings.html': '18633454497540c0647c19cfd3538e158835d41992eb6a4d8de03b07172b97bf',
    'activity_financial_import.html': '598e7936f9835b308182196435fdd06dab66346e1b4bf9016a406c9bfd461bb9',
}


def scene(name, state='ready', long=False):
    request = Request({'type': 'http', 'scheme': 'http', 'server': ('testserver', 80),
        'path': '/activity-reports/publications/41/bindings' if name == 'bindings' else
            '/activity-sections/reports/51/financial/imports/61',
        'headers': [], 'session': {'csrf_token': 'synthetic-csrf'}})
    data = dict(request=request, user=dict(role='strategy', full_name='Örnek Kullanıcı', department_id=1))
    if name == 'bindings':
        data.update(year=2027, publication=dict(id=41, version=2),
            rows=[dict(id=i+1, name=label + (' UzunGöstergeAdı' * 20 if long else ''),
                department='Sentetik Park ve Bahçeler Müdürlüğü', unit='Adet',
                code=code, organization_id=org, bound=bound)
                for i, (label, code, org, bound) in enumerate([
                    ('Bakımı tamamlanan park sayısı', 'G-01', 1, True),
                    ('Yenilenen yeşil alan sayısı', '', 1, False),
                    ('İkinci kurumun hizmet sayısı', 'G-03', 2, False)])],
            identities=[dict(indicator_id=key, organization_id=org, label=label) for key, org, label in [
                ('identity-1', 1, 'Park bakımı · Adet · 2027 · Tanım sürümü 1'),
                ('identity-2', 2, 'Diğer kurum · Adet · 2027 · Tanım sürümü 2'),
                ('identity-3', 1, 'Yeşil alan · Adet · 2026 · Tanım sürümü 3')]])
        if state == 'empty':
            data['rows'] = []
        elif state == 'evidence':
            data['rows'] = data['rows'][:2]
    else:
        numeric = ['initial','added','deducted','entered_final','actual','cancelled','carried','estimate','refunds']
        columns = [(key, key) for key in numeric] + [('explanation', 'Açıklama')]
        differences = [dict(action=action, label=label,
            before=None if action == 'added' else {**dict.fromkeys(numeric, 12500.23), 'explanation':'Önceki <metin> & kayıt'},
            after=None if action == 'removed' else {**dict.fromkeys(numeric, 0), 'explanation':'Yeni açıklama'})
            for action, label in [('added','03 · Teşebbüs ve mülkiyet gelirleri'),
                                  ('removed','05 · Diğer gelirler'), ('changed','01 · Vergi gelirleri')]]
        if state in {'evidence', 'errors'}:
            columns = [('actual','Tahsilat'), ('explanation','Açıklama')]
        data.update(report=dict(id=51, year=2027, department='Sentetik Belediyesi', revision=7, frozen=state == 'frozen'),
            preview=dict(id=61, rows=[{}, {}, {}],
                errors=[dict(message='Satır 4 · Ekonomik kod bilinmiyor. Dosyadaki kodu düzeltip yeniden yükleyin.'),
                        dict(message='Satır 5 · Tahsilat sayısal olmalıdır. Tutarı düzeltip yeniden yükleyin.')]
                        if state == 'errors' else [],
                differences=[] if state == 'empty' else differences), columns=columns, stale=state == 'stale')
    return data


def render(name, data, before=False):
    filename = 'activity_contract_bindings.html' if name == 'bindings' else 'activity_financial_import.html'
    raw = (FROZEN / filename).read_bytes()
    assert sha256(raw).hexdigest() == HASHES[filename]
    template = templates.env.from_string(raw.decode()) if before else templates.env.get_template(filename)
    return template.render(data)


def normalized(el):
    return ' '.join(el.text_content().split())


def contract(html):
    main = fromstring(html).get_element_by_id('main')
    controls, hooks, labels = [], [], []
    for el in main.iter():
        if not isinstance(el.tag, str):
            continue
        attrs = tuple(sorted((k,v) for k,v in el.attrib.items() if k not in {'class','style'}))
        form = next(el.iterancestors('form'), None)
        parent = (form.get('method'), form.get('action')) if form is not None else None
        if el.tag in {'form','input','select','textarea','option','button'}:
            value = el.text_content() if el.tag == 'textarea' else normalized(el) if el.tag in {'option','button'} else ''
            controls.append((el.tag, attrs, value, parent))
        hook = tuple(sorted((k,v) for k,v in el.attrib.items() if k in {'id','role'} or k.startswith(('data-','aria-'))))
        if hook:
            hooks.append((el.tag,hook))
        if el.tag == 'label':
            labels.append((el.text or '').strip())
    # The existing back link moves above the intro; its contract is unchanged.
    links = sorted((a.get('href'), normalized(a)) for a in main.xpath('.//a'))
    cells = [normalized(c) for c in main.xpath('.//th|.//td')]
    return controls, hooks, labels, links, cells


@pytest.mark.parametrize('name,state', [('bindings','ready'), ('bindings','empty')] +
    [('financial',s) for s in ['ready','errors','stale','frozen','empty']])
def test_frozen_contract(name, state):
    data = scene(name,state)
    before, after = (render(name,data,old) for old in (True,False))
    assert contract(after) == contract(before)
    old, new = (fromstring(h).get_element_by_id('main') for h in (before,after))
    if name == 'bindings':
        selects = new.xpath('.//select')
        if selects:
            assert [o.get('value') for o in selects[0]] == ['', 'identity-1', 'identity-3']
            assert [o.get('value') for o in selects[1]] == ['', 'identity-2']
        # Only the two approved badge labels are added. Back-link order may move.
        for el in new.xpath('.//span[contains(concat(" ",@class," ")," status ")]'):
            el.getparent().remove(el)
        for main in (old,new):
            for el in main.xpath('.//a[@href="/activity-reports"]'):
                el.getparent().remove(el)
        # Separators between elements are insignificant; visible characters remain.
        assert ''.join(old.text_content().split()) == ''.join(new.text_content().split())
    else:
        assert [normalized(el) for el in old.xpath('.//h1|.//h2|.//p[not(a)]|.//th|.//td|.//button|.//a')] == [normalized(el) for el in new.xpath('.//h1|.//h2|.//p[not(a)]|.//th|.//td|.//button|.//a')]
        if state == 'ready':
            cells = contract(after)[-1]
            assert '12.500,23' in cells and '0' in cells and '—' in cells
        assert bool(new.xpath('.//form')) == (state in {'ready','empty'})


def serve_assets(route):
    path = urlsplit(route.request.url).path
    if path.startswith('/static/'):
        file = ROOT / 'app' / path.lstrip('/')
        route.fulfill(path=str(file))
    else:
        route.fulfill(status=200, content_type='application/json', body='{}')


def assert_design(page, selector):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    root = page.locator(selector)
    assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
    for item in root.locator('.binding-row,.info-panel,.error-panel,.warning-panel,p').all():
        assert item.bounding_box()['width'] <= 704.5
    for form in root.locator('.form-grid').all():
        assert len(form.evaluate('el => getComputedStyle(el).gridTemplateColumns').split()) == 1
    if root.locator('.table-wrap').count():
        assert root.locator('.table-wrap').evaluate('el => el.scrollWidth >= el.clientWidth')
        for cell in root.locator('td.numeric').all():
            assert cell.evaluate("el => getComputedStyle(el).textAlign === 'right' && getComputedStyle(el).fontVariantNumeric.includes('tabular-nums')")
    script = TEXT_PAIRS.replace('.section-index-page',selector)
    pairs = set(map(tuple,page.evaluate(script)))
    for control in root.locator('a,button,select,textarea').all():
        control.hover()
        pairs.update(map(tuple,page.evaluate(script)))
        control.focus()
        assert control.evaluate("el => getComputedStyle(el).outlineStyle === 'solid'")
        pairs.update(map(tuple,page.evaluate(script)))
    assert all(contrast(pair) >= 4.5 for pair in pairs), [(pair,contrast(pair)) for pair in pairs if contrast(pair)<4.5]


@pytest.mark.parametrize('width',[1440,390])
@pytest.mark.parametrize('before',[True,False],ids=['before','after'])
@pytest.mark.parametrize('name,state',[('bindings','evidence'),('financial','errors'),('financial','evidence')])
def test_browser_evidence(browser,width,before,name,state,tmp_path):
    data = scene(name,state)
    html = render(name,data,before)
    with browser.new_context(viewport={'width':width,'height':1000},locale='tr-TR') as context:
        path = data['request'].url.path
        def serve(route):
            if urlsplit(route.request.url).path == path:
                route.fulfill(content_type='text/html; charset=utf-8',body=html)
            else:
                serve_assets(route)
        context.route('http://testserver/**',serve)
        page=context.new_page()
        page.goto('http://testserver'+path)
        page.evaluate('document.fonts.ready')
        if not before:
            assert_design(page,'.indicator-bindings-page' if name == 'bindings' else '.financial-import-page')
        folder=Path(os.getenv('CIVENSA_CIV152_SCREENSHOTS',str(tmp_path)))
        folder.mkdir(parents=True,exist_ok=True)
        page.mouse.move(0,0)
        page.locator('h1').click()
        page.screenshot(path=str(folder/f'{name}-{state}-{width}-{"before" if before else "after"}.png'),full_page=True)


@pytest.mark.parametrize('width',[1440,390])
@pytest.mark.parametrize('name,state',[('bindings','ready'),('financial','stale'),('financial','frozen'),('financial','empty')])
def test_browser_edge_states(browser,width,name,state):
    data=scene(name,state,long=True)
    with browser.new_context(viewport={'width':width,'height':1000}) as context:
        context.route('http://testserver/**',lambda route: route.fulfill(content_type='text/html; charset=utf-8',
            body=render(name,data)) if urlsplit(route.request.url).path == data['request'].url.path else serve_assets(route))
        page=context.new_page();page.goto(str(data['request'].url))
        assert_design(page,'.indicator-bindings-page' if name == 'bindings' else '.financial-import-page')


def route_client(context,client):
    writes=[]
    def serve(route):
        req=route.request
        response=client.request(req.method,req.url,content=req.post_data_buffer,
            headers={'content-type':req.headers.get('content-type','')},follow_redirects=False)
        if req.method == 'POST':
            writes.append((urlsplit(req.url).path,response.status_code,response.headers.get('location')))
        if response.status_code == 303:
            # Playwright routes only the first URL in an HTTP redirect chain.
            # Resolve the relative hop in TestClient, keeping testserver local.
            assert response.headers['location'].startswith('/')
            response=client.get(response.headers['location'],follow_redirects=True)
        headers=dict(response.headers);headers.pop('set-cookie',None)
        route.fulfill(status=response.status_code,headers=headers,body=response.content)
    context.route('http://testserver/**',serve)
    return writes


@pytest.mark.postgres
@pytest.mark.parametrize('width',[1440,390])
def test_binding_save_real_browser(browser,section_client,db,sample,width):
    client,_,_,_=section_client
    login(client,'strategy@example.invalid')
    from app.models import Publication,PublicationIndicatorBinding
    from app.program_service import book_snapshot
    from app.serialization import json_dumps
    raw=json_dumps(book_snapshot(db,sample['period'].id))
    pub=Publication(period_id=sample['period'].id,version=1,snapshot_json=raw,
        sha256=sha256(raw.encode()).hexdigest(),created_by=sample['strategy'].id)
    db.add(pub);db.commit()
    with browser.new_context(viewport={'width':width,'height':1000}) as context:
        writes=route_client(context,client)
        page=context.new_page();page.goto(f'http://testserver/activity-reports/publications/{pub.id}/bindings')
        root=page.locator('.indicator-bindings-page')
        root.get_by_label('Eşleme gerekçesi').fill('Aynı kavramı temsil eden bağımsız tarihsel kayıt.')
        root.get_by_role('button',name='Açık kimlik ilişkisini kaydet').click()
        expect(root.get_by_text('Sabitlendi',exact=True)).to_be_visible()
        assert root.locator('form').count()==0
        binding=db.scalar(select(PublicationIndicatorBinding).where(PublicationIndicatorBinding.publication_id==pub.id))
        assert writes==[(f'/activity-reports/publications/{pub.id}/bindings',303,f'/activity-reports/publications/{pub.id}/bindings')]
        assert binding.reason=='Aynı kavramı temsil eden bağımsız tarihsel kayıt.'
        assert pub.snapshot_json==raw


@pytest.mark.postgres
@pytest.mark.parametrize('width',[1440,390])
def test_financial_apply_real_browser(browser,section_client,sample,width):
    from test_activity_financial import preview,post,financial
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    first=preview(client,token,doc,'revenue',[dict(economic_code='01',estimate=12500.23,actual=10000,refunds=0)]).json()
    assert post(client,token,doc,f'/imports/{first["id"]}/apply').status_code==200
    pending=preview(client,token,doc,'revenue',[dict(economic_code='01',estimate=12500.23,actual=11000,refunds=0)]).json()
    with browser.new_context(viewport={'width':width,'height':1000}) as context:
        writes=route_client(context,client)
        page=context.new_page();page.goto(f'http://testserver/activity-sections/reports/{doc.id}/financial/imports/{pending["id"]}')
        expect(page.locator('.ar-table')).to_contain_text('10.000')
        expect(page.locator('.ar-table')).to_contain_text('11.000')
        page.get_by_role('button',name='Farkları onayla ve içe aktarmayı uygula').click()
        expect(page.get_by_role('heading',name='Bütçe Uygulama Sonuçları',exact=True)).to_be_visible()
        assert writes==[(f'/activity-sections/reports/{doc.id}/financial/imports/{pending["id"]}/apply',303,f'/activity-sections/reports/{doc.id}?code=III.A.1')]
        assert financial(client,doc)['tables']['revenue']['rows'][0]['actual']==11000
