"""CIV-185: approved numbers, editorial isolation, authorization and playback."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import logging
import os
from pathlib import Path
import re

from lxml import html
import pytest
from sqlalchemy import func, select

from app import activity_sections_service as reports, sunum_highlights as highlights
from app.sunum import activity_report, render_deck
from app.sunum.engine import prepare_slides
from app.sunum.facts import facts
from app.sunum.models import SunumHighlight, SunumPhoto
from app.sunum.recipes_idare import idare_activity_report
from test_activity_sections import section_client, login, PASSWORD
from app.security import hash_password
from test_sunum_idare import idare_fixture, by_title, freeze_fixture
from test_sunum_photos import image_bytes, upload
from test_sunum_browser import browser_options, deck_url

pytestmark = pytest.mark.postgres


def create(f, key='org:staff_total', **fields):
    return f['client'].post(f"/activity-sections/reports/{f['idare'].id}/highlights",
        headers={'X-CSRF-Token': f['token']}, data=dict(kind='spot', fact_key=key,
        sentence='Hizmetlerimizi kentimizin her mahallesine ulaştırdık.', selected='on') | fields)


def edit(f, row, action, **data):
    return f['client'].post(f"/activity-sections/reports/{f['idare'].id}/highlights/{row.id}/{action}",
        headers={'X-CSRF-Token': f['token']}, data=data)


def test_catalogue_matches_existing_kpis_and_unit_charts(idare_fixture):
    payload = idare_fixture['enriched']
    original = deepcopy(payload)
    catalogue = facts(payload, payload['unit_indicator_sources'])
    indexed = {f['key']: f for f in catalogue}
    slides = prepare_slides(idare_activity_report(payload))
    assert indexed['org:staff_total']['value'] == by_title(slides, 'Kurumumuzun ekibi')['figures'][0]['value'] == 38
    for key, figure in zip(('final', 'actual', 'rate'), by_title(slides, 'Bütçe bir bakışta')['figures']):
        assert indexed['org:budget_' + key]['value'] == figure['value']
        assert indexed['org:budget_' + key]['display'] == figure['display']
    for suffix, title in [('staff', 'Müdürlüklere göre personel'), ('spending', 'Müdürlüklere göre harcama')]:
        chart = by_title(slides, title)
        for unit in payload['unit_manifest']:
            i = chart['categories'].index(unit['department'])
            assert indexed[f"unit:{unit['department_id']}:{suffix}"]['value'] == Decimal(str(chart['series'][0]['values'][i]))
    assert len([f for f in catalogue if f['key'].startswith('ind:')]) == 4
    assert all(isinstance(f['value'], Decimal) for f in catalogue)
    assert payload == original


def test_absent_incomplete_ambiguous_and_unverified_facts(idare_fixture):
    payload = deepcopy(idare_fixture['enriched'])
    unit = payload['unit_indicator_sources'][0]
    unit['core']['indicators'].append(deepcopy(unit['core']['indicators'][0]))
    unit['core']['indicators'][1]['actual_state'] = 'unverified'
    payload['resources']['employment']['rows'][0]['count'] = None
    payload['financial']['tables']['expenditure']['rows'][0]['actual'] = None
    catalogue = {f['key']: f for f in facts(payload, payload['unit_indicator_sources'])}
    assert 'org:staff_total' not in catalogue
    assert not any(k.startswith('org:budget_') or k.endswith(':spending') for k in catalogue)
    assert f"unit:{unit['department_id']}:staff" not in catalogue
    assert not any(k.startswith(f"ind:{unit['department_id']}:") for k in catalogue)
    # Genuine zero is offered and retains the exact name-based identity.
    other = payload['unit_indicator_sources'][1]
    name = other['core']['indicators'][0]['name']
    key = f"ind:{other['department_id']}:{sha256(name.encode()).hexdigest()[:16]}:actual"
    assert catalogue[key]['value'] == 0


def test_million_money_scale_matches_kpi(idare_fixture):
    payload = deepcopy(idare_fixture['enriched'])
    for row in payload['financial']['tables']['expenditure']['rows']:
        row['final'] = Decimal(row['final']) * 1000
        row['actual'] = Decimal(row['actual']) * 1000
    indexed = {f['key']: f for f in facts(payload, payload['unit_indicator_sources'])}
    assert indexed['org:budget_final']['value'] == 6
    assert indexed['org:budget_final']['display'] == '6,00'
    assert indexed['org:budget_actual']['unit'] == 'milyon TL'
    assert indexed['org:budget_final']['value'] == by_title(idare_activity_report(payload), 'Bütçe bir bakışta')['figures'][0]['value']


@pytest.mark.parametrize('field,value', [('sentence','Kentte 12 park açıldı.'),('label','12 park'),('sentence','Kentte ٢ park açıldı.'),('label','m²')])
def test_digits_rejected_without_storage(idare_fixture, db, field, value):
    data = dict(kind='spot', fact_key='org:staff_total', sentence='Ekibimiz güçlendi.', label='kişi')
    data[field] = value
    f = idare_fixture
    response = f['client'].post(f"/activity-sections/reports/{f['idare'].id}/highlights", headers={'X-CSRF-Token':f['token']}, data=data)
    assert response.status_code == 422
    assert highlights.DIGIT_ERROR in response.text
    assert db.scalar(select(func.count()).select_from(SunumHighlight)) == 0


def test_limits_edit_order_confirmation_and_photo_scope(idare_fixture, db, sample):
    f = idare_fixture
    for _ in range(5):
        assert create(f).status_code == 303
    assert create(f).status_code == 422
    assert 'en fazla 5 spot' in create(f).text
    rows = list(db.scalars(select(SunumHighlight).order_by(SunumHighlight.id)))
    assert edit(f, rows[-1], 'order', value='up').status_code == 303
    db.expire_all()
    assert rows[-1].sort_order < rows[-2].sort_order
    assert edit(f, rows[0], 'delete').status_code == 422
    assert edit(f, rows[0], 'edit', kind='spot', fact_key='org:budget_actual', sentence='Kaynaklarımızı hizmete dönüştürdük.', selected='on', context='100. Yıl Mahallesi').status_code == 303
    db.expire_all()
    assert rows[0].context == '100. Yıl Mahallesi'
    assert edit(f, rows[0], 'delete', value='yes').status_code == 303
    assert create(f).status_code == 303
    dep = f['units'][0].department_id
    assert create(f, f'unit:{dep}:staff', kind='feature', department_id=str(dep)).status_code == 303
    response = create(f, f'unit:{dep}:spending', kind='feature', department_id=str(dep))
    assert response.status_code == 422 and 'yalnız bir' in response.text
    photo_fixture = f['client'], f['docs'], f['token']
    assert upload(photo_fixture, sample).status_code == 303
    photo = db.scalar(select(SunumPhoto))
    other = f['units'][1].department_id
    response = create(f, f'unit:{other}:staff', kind='feature', department_id=str(other), photo_id=str(photo.id))
    assert response.status_code == 422 and 'aynı müdürlük ve yıldan tek fotoğraf' in response.text
    assert db.scalar(select(func.count()).select_from(SunumHighlight).where(SunumHighlight.kind=='feature')) == 1


@pytest.mark.parametrize('role', ['department','finance','viewer'])
def test_all_new_routes_refuse_non_strategy(idare_fixture, db, sample, role):
    from app.models import User
    f = idare_fixture
    user = db.scalar(select(User).where(User.role==role))
    if user is None:
        user = User(email=f'{role}@invalid', full_name=role, role=role, password_hash=hash_password(PASSWORD))
        db.add(user); db.commit()
    token = login(f['client'], user.email)
    url = f"/activity-sections/reports/{f['idare'].id}/highlights"
    assert f['client'].get(url).status_code == 403
    for suffix in ['', '/1/edit', '/1/order', '/1/delete', '/1/unknown']:
        assert f['client'].post(url+suffix, headers={'X-CSRF-Token': token}, data={'kind':'spot'}).status_code == 403


@pytest.fixture
def highlight_deck(idare_fixture, db, sample):
    f = idare_fixture
    photo_fixture = f['client'], f['docs'], f['token']
    for i, key in enumerate(['org:staff_total', 'org:budget_rate']):
        assert create(f, key, context='Kurumumuzun yıl boyunca yürüttüğü hizmetler').status_code == 303
    for i, unit in enumerate(f['units']):
        photo_id = ''
        if i != 1:
            assert upload(photo_fixture, sample, image_bytes(i), department_id=str(unit.department_id)).status_code == 303
            photo_id = str(db.scalar(select(SunumPhoto.id).order_by(SunumPhoto.id.desc()).limit(1)))
        assert create(f, f'unit:{unit.department_id}:staff', kind='feature', department_id=str(unit.department_id), photo_id=photo_id, context='100. Yıl Mahallesi').status_code == 303
    return f


def test_render_resolves_payload_numbers_order_and_report_isolation(highlight_deck, db, sample):
    f = highlight_deck
    freeze_fixture(db, f, sample['strategy'])
    base = f"/activity-sections/reports/{f['idare'].id}"
    original = f['client'].get(base+'/export.json?version=1').content
    own = f['units'][0]
    birim = f['client'].get(f'/activity-sections/reports/{own.id}/sunum').content
    response = f['client'].get(base+'/sunum?version=1')
    assert response.status_code == 200
    document = html.fromstring(response.content)
    spots = document.xpath('//section[@data-type="spot"]')
    assert [s.xpath('.//*[@data-count]/@data-count')[0] for s in spots] == ['38','76.67']
    cards = document.xpath('//section[@data-type="feature"]//article')
    assert len(cards) == 3 and len(cards[1].xpath('.//img')) == 0
    assert [s.xpath('.//*[@class="v"]/text()')[0] for s in cards] == ['22','10','6']
    types = document.xpath('//section/@data-type')
    assert types[:4] == ['cover','map','separator','spot']
    assert not re.search(rb'(?:src|href)=["\']https?://',response.content)
    assert 'Müdürlük bölümleri' in response.text
    assert f['client'].get(base+'/export.json?version=1').content == original
    assert f['client'].get(f'/activity-sections/reports/{own.id}/sunum').content == birim
    code = sha256(original).hexdigest()[:8].upper()
    assert code[:4]+'-'+code[4:] in response.text
    # Same editorial selection, different approved payload: never retain a number.
    payload = deepcopy(f['enriched'])
    items = highlights.deck_items(db, f['idare'])
    indicator = next(fact for fact in facts(payload,payload['unit_indicator_sources']) if fact['key'].startswith('ind:'))
    items[0].update(fact_key=indicator['key'], department_id=indicator['department_id'])
    before = idare_activity_report(payload, highlights=items)
    assert len([s for s in before if s['type']=='spot']) == 2
    payload['unit_indicator_sources'][0]['core']['indicators'] = []
    after = idare_activity_report(payload, highlights=items)
    assert len([s for s in after if s['type']=='spot']) == 1


def test_missing_fact_logs_and_keeps_other_slides(idare_fixture, caplog):
    p = idare_fixture['enriched']
    rows = [dict(id=1, kind='spot', fact_key='ind:1:removed:actual', department_id=1,
        sort_order=0, sentence='Hizmet tamamlandı.', label='', context='')]
    with caplog.at_level(logging.INFO):
        assert idare_activity_report(p, highlights=rows) == idare_activity_report(p)
    assert 'rakamı raporda artık yok; slayt/kart atlandı' in caplog.text


def test_browser_counts_cards_pdf_and_responsive_page(highlight_deck, db, sample, tmp_path):
    from playwright.sync_api import sync_playwright
    f = highlight_deck
    base = f"/activity-sections/reports/{f['idare'].id}"
    freeze_fixture(db, f, sample['strategy'])
    content = f['client'].get(base+'/sunum').content
    path = tmp_path/'highlights.html'; path.write_bytes(content)
    screenshots = os.getenv('CIVENSA_SUNUM_SCREENSHOTS')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**browser_options())
        page = browser.new_page(viewport={'width':1920,'height':1080}, offline=True)
        page.goto(deck_url(page,path)); page.wait_for_function('() => window.sunumRendered === true')
        indexes = page.evaluate("[...document.querySelectorAll('.slides>section')].flatMap((s,i)=>s.dataset.type==='spot'?[i]:[])")
        page.evaluate('(i)=>deck.slide(i)',indexes[0])
        page.wait_for_timeout(180)
        counter = page.locator('section.present [data-count]')
        intermediate = counter.inner_text()
        assert intermediate != '38'
        page.wait_for_timeout(1000)
        assert counter.inner_text() == '38'
        assert page.evaluate('deck.getIndices().h') == indexes[0]
        if screenshots:
            Path(screenshots).mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(Path(screenshots)/'civ185-spot-green.png'))
        page.evaluate('(i)=>deck.slide(i)',indexes[1]);page.wait_for_timeout(1200)
        if screenshots: page.screenshot(path=str(Path(screenshots)/'civ185-spot-dark.png'))
        feature_index = page.evaluate("[...document.querySelectorAll('.slides>section')].findIndex(s=>s.dataset.type==='feature')")
        page.evaluate('(i)=>deck.slide(i)',feature_index)
        page.wait_for_timeout(90)
        opacity = page.locator('section.present .card').evaluate_all('(els)=>els.map(e=>Number(getComputedStyle(e).opacity))')
        assert opacity[0] > opacity[2]
        page.wait_for_timeout(1100)
        assert page.locator('section.present .card').evaluate_all('(els)=>els.every(e=>getComputedStyle(e).opacity==="1")')
        assert page.evaluate('deck.getIndices().h') == feature_index
        if screenshots: page.screenshot(path=str(Path(screenshots)/'civ185-feature-cards.png'))
        page = browser.new_page(viewport={'width':1920,'height':1080}, offline=True)
        page.goto(deck_url(page,path)+'#pdf');page.wait_for_function('() => window.sunumRendered === true')
        assert page.locator('[data-type="spot"] [data-count]').all_inner_texts() == ['38','76,67']
        assert page.locator('[data-type="spot"] [data-count]').evaluate_all('(els)=>els.every(e=>!e.getAnimations().length)')
        if screenshots: page.locator('[data-type="spot"]').first.screenshot(path=str(Path(screenshots)/'civ185-spot-pdf.png'))
        page = browser.new_page(viewport={'width':1920,'height':1080}, offline=True)
        page.emulate_media(reduced_motion='reduce');page.goto(deck_url(page,path));page.wait_for_function('() => window.sunumRendered === true')
        page.evaluate('(i)=>deck.slide(i)',indexes[0]);page.wait_for_timeout(50)
        assert page.locator('section.present [data-count]').inner_text() == '38'
        # Serve real authenticated page/static/image bytes via TestClient.
        page = browser.new_page(viewport={'width':1920,'height':1080})
        def serve(route):
            response = f['client'].get(route.request.url.replace('http://testserver',''))
            route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)
        page.route('http://testserver/**',serve)
        page.goto('http://testserver'+base+'/highlights');page.wait_for_load_state('networkidle')
        assert page.get_by_role('heading', name='Meclis sunumu öne çıkanlar').count() == 1
        if screenshots: page.screenshot(path=str(Path(screenshots)/'civ185-highlights-desktop.png'))
        page.set_viewport_size({'width':390,'height':1080});page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if screenshots: page.screenshot(path=str(Path(screenshots)/'civ185-highlights-mobile.png'),full_page=True)
        browser.close()


def test_later_approved_release_removes_selected_indicator(idare_fixture, db, sample, caplog):
    from app import ar_unit_workflow_service as workflow
    from app.models import ActivityReport, ActivityReportRevision, ActualRevision, ReportIndicator, User
    from ar_unit_workflow_helpers import ready_unit, approve_unit
    f = idare_fixture
    indicator = next(fact for fact in facts(f['enriched'], f['enriched']['unit_indicator_sources']) if fact['key'].startswith('ind:'))
    dep = indicator['department_id']
    assert create(f, indicator['key']).status_code == 303
    assert create(f, indicator['key'],kind='feature',department_id=str(dep)).status_code == 303
    other=f['units'][1].department_id
    assert create(f, f'unit:{other}:staff',kind='feature',department_id=str(other)).status_code == 303
    freeze_fixture(db, f, sample['strategy'])
    base = f"/activity-sections/reports/{f['idare'].id}"
    old_export = f['client'].get(base+'/export.json?version=1').content
    old_deck = f['client'].get(base+'/sunum?version=1').content
    assert b'data-type="spot"' in old_deck
    unit = f['units'][0]
    actor = db.scalar(select(User).where(User.role=='department',User.department_id==dep))
    workflow.transition(db,sample['strategy'],unit.id,'reopen',unit.revision,'Yeni gösterge kapsamı')
    # A new synthetic contract revision omits one binding; historical rows and
    # the first approved payload remain immutable. Real submit/approve pins v2.
    report = db.scalar(select(ActivityReport).where(ActivityReport.organization_id==unit.organization_id,ActivityReport.period_id==unit.period_id))
    previous = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id==report.id, ActivityReportRevision.revision==report.current_revision))
    items = list(db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id==previous.id).order_by(ReportIndicator.id)))
    revision = ActivityReportRevision(report_id=report.id,revision=2,publication_id=previous.publication_id,
        publication_sha256=previous.publication_sha256,previous_revision_id=previous.id,created_by=actor.id)
    db.add(revision);db.flush()
    for item in items[1:]:
        replacement = ReportIndicator(report_revision_id=revision.id,publication_binding_id=item.publication_binding_id)
        db.add(replacement);db.flush()
        actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id==item.id).order_by(ActualRevision.revision.desc()).limit(1))
        db.add(ActualRevision(report_indicator_id=replacement.id,revision=1,value=actual.value,state=actual.state,
            evidence_json=actual.evidence_json,explanation=actual.explanation,deviation_json=actual.deviation_json,created_by=actor.id))
    report.current_revision=2
    db.flush();ready_unit(db,unit,actor);approve_unit(db,unit,actor)
    later = reports.report_data(db,sample['strategy'],f['idare'].id,use_freeze=False)
    from app.models import ARDocumentFreeze
    serialized = reports.numeric_canonical(later)
    db.add(ARDocumentFreeze(document_id=f['idare'].id,version=2,payload_json=serialized,
        sha256=sha256(serialized.encode()).hexdigest(),created_by=sample['strategy'].id))
    db.commit()
    with caplog.at_level(logging.INFO):
        response = f['client'].get(base+'/sunum?version=2')
    assert response.status_code==200
    assert b'data-type="spot"' not in response.content
    assert len(html.fromstring(response.content).xpath('//section[@data-type="feature"]//article')) == 1
    assert 'rakamı raporda artık yok; slayt/kart atlandı' in caplog.text
    assert f['client'].get(base+'/export.json?version=1').content == old_export
    assert f['client'].get(base+'/sunum?version=1').content == old_deck
    page = f['client'].get(base+'/highlights')
    assert highlights.MISSING in page.text


def test_five_spots_twelve_cards_sixteen_photos_under_eight_mb(highlight_deck, db, sample):
    f=highlight_deck
    items=highlights.deck_items(db,f['idare'])
    spots=[dict(items[0],id=i,sort_order=i) for i in range(5)]
    payload=deepcopy(f['enriched'])
    cards=[]
    from app import sunum_photos_service as photos_service
    import base64
    photos=[]
    for i in range(16):
        processed=photos_service.process_image(image_bytes(80+i))
        uri='data:image/webp;base64,'+base64.b64encode(processed['webp_data']).decode('ascii')
        photos.append(dict(type='photo',image=uri,title='Tamamlanan çalışma',meta='Mahalle',source='Fotoğraf: müdürlük'))
    for i in range(12):
        dep=200+i
        name=f'Müdürlük {i}'
        payload['unit_manifest'].append(dict(department_id=dep,department=name))
        payload['resources']['employment']['rows'].append(dict(department_id=dep,department=name,count=i))
        cards.append(dict(items[2],id=10+i,sort_order=10+i,department_id=dep,department=name,
            fact_key=f'unit:{dep}:staff',image=photos[i]['image']))
    slides=idare_activity_report(payload,highlights=spots+cards,photos=photos)
    assert sum(s['type']=='spot' for s in slides)==5
    assert sum(s['type']=='feature' for s in slides)==4
    data=render_deck(slides,title='Boyut testi',code='ABCD-1234',max_bytes=8_000_000)
    assert len(data)<8_000_000
    if os.getenv('CIVENSA_SUNUM_SCREENSHOTS'):
        Path(os.environ['CIVENSA_SUNUM_SCREENSHOTS'],'size-stress.txt').write_text(f'{len(data)} bytes: 5 spots, 12 cards, 16 photos\n')


def test_concurrent_fifth_spot_is_serialized(idare_fixture, db, sample):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from sqlalchemy.orm import Session
    from app.models import User
    f=idare_fixture
    for _ in range(4):
        assert create(f).status_code==303
    barrier=Barrier(2)
    catalogue=facts(f['enriched'],f['enriched']['unit_indicator_sources'])
    actor_id=sample['strategy'].id
    document_id=f['idare'].id
    def attempt():
        with Session(db.get_bind()) as session:
            user=session.get(User,actor_id)
            barrier.wait(timeout=10)
            try:
                doc=highlights.scope(session,user,document_id,lock=True)
                highlights.save(session,doc,user,dict(kind='spot',fact_key='org:staff_total',sentence='Ekibimiz güçlendi.',selected='on'),catalogue)
                session.commit()
                return 303
            except HTTPException as error:
                session.rollback()
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:attempt(),range(2)))
    assert sorted(results)==[303,422]
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(SunumHighlight).where(SunumHighlight.selected))==5
