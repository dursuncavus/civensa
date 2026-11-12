"""CIV-219 acceptance with real scope, submission snapshots and exports."""
import json
import os
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image
from fastapi import HTTPException
from sqlalchemy import select, text
from app import ar_unit_tables_service as tables, activity_sections_service as sections
from app import ar_unit_workflow_service as workflow, activity_contract_service as contracts
from app.models import Publication, ARUnitTable
from test_activity_sections import section_client, login
from ar_unit_workflow_helpers import ready_unit, reviewer

pytestmark = pytest.mark.postgres


@pytest.fixture
def table_report(section_client, db, sample):
    client, docs, other, _ = section_client
    doc = docs[f'birim:{sample["department"].id}']
    sample['period'].year = 2026
    year = sample['period'].year
    # Real published department rows, linked to the frozen responsibility catalogue.
    payload = {'schema_version': '5.0', 'period': year, 'departments': [
        {'department_id': doc.department_id, 'department': 'Sentetik Park Müdürlüğü', 'activities': [
            {'id': 51, 'code': 'F.01', 'name': 'Park bakım ve onarım', 'program': 'Çevre',
             'subprogram': 'Yeşil alan', 'subprogram_id': 9, 'official_ids': [71]},
            {'id': 52, 'code': 'F.02', 'name': 'Yeni park yapımı', 'program': 'Çevre',
             'subprogram': 'Yeşil alan', 'subprogram_id': 9, 'official_ids': [71]}]},
        {'department_id': other.id, 'department': 'Sentetik Diğer Müdürlük', 'activities': [{'id': 99, 'name': 'Diğer birimin gizli faaliyeti'}]}],
        'catalogue': [{'id': 71, 'code': 'F', 'name': 'Park', 'departments': [doc.department_id],
                       'program_code': '01', 'program_name': 'Çevre', 'subprogram_code': '01.01',
                       'subprogram_name': 'Yeşil alan'}]}
    raw = contracts.canonical(payload)
    db.add(Publication(period_id=doc.period_id, version=1, snapshot_json=raw,
        sha256=contracts.digest(raw), created_by=sample['strategy'].id))
    db.commit()
    return client, doc, docs, other


def post(client, token, doc, kind, rows, **changes):
    data = dict(expected_revision=doc.revision, rows=rows)
    data.update(changes)
    return client.post(f'/api/activity-sections/reports/{doc.id}/unit-tables/{kind}', json=data,
                       headers={'X-CSRF-Token': token})


def staff(mismatch=False):
    return [dict(key=key, status='Genel İdare Hizmetleri', positions='12', actual='10',
                 women='4', men='7' if mismatch and i == 0 else '6') for i, key in enumerate(tables.STAFF)]


def outputs(db, doc):
    return [dict(key=a['key'], outputs='12 parkta 1.250 m2 alan yenilendi.', inside='1.234.567,89', outside='0')
            for a in tables.book(db, doc)['activities']]


def save_all(db, sample, doc):
    actor = sample['user']
    tables.save(db, actor, doc.id, '1', doc.revision, [dict(name='Sentetik Hizmet Binası',
        address='Örnek Mahallesi No: 10', purpose='Vatandaş hizmetleri', area='1.250,50', ownership='Belediye mülkü')])
    tables.save(db, actor, doc.id, '2', doc.revision, staff())
    tables.save(db, actor, doc.id, '7', doc.revision, outputs(db, doc))
    programme = tables.book(db, doc)['programmes'][0]['key']
    tables.save(db, actor, doc.id, '8', doc.revision, [dict(name='Sentetik Engelsiz Park Projesi',
        programme=programme, start='2026-01-01', end='2026-12-31', physical='75', spending='250.000,50', state='Devam ediyor')], False)
    image = BytesIO(); Image.new('RGB', (360, 220), '#3f7c71').save(image, format='PNG')
    tables.upload(db, actor, doc.id, tables.book(db, doc)['activities'][0]['key'], doc.revision,
                  'Sentetik park bakım çalışması', image.getvalue(), 'park.png')
    db.commit()


def test_fixed_activities_own_book_and_turkish_amounts(table_report, db, sample):
    client, doc, _, _ = table_report
    token = login(client, sample['user'].email)
    source = tables.book(db, doc)
    assert [a['activity'] for a in source['activities']] == ['F.01 Park bakım ve onarım', 'F.02 Yeni park yapımı']
    rows = outputs(db, doc)
    assert post(client, token, doc, '7', rows).status_code == 200
    data = sections.report_data(db, sample['user'], doc.id)['unit_tables']
    assert data['tables']['7']['rows'][0]['total'] == Decimal('1234567.89')
    for bad in [rows[:1], rows + [rows[0]], [dict(rows[0], key='99'), rows[1]],
                [dict(rows[0], activity='Yeniden adlandırıldı'), rows[1]]]:
        assert post(client, token, doc, '7', bad).status_code == 422
    assert post(client, token, doc, '7', [dict(rows[0], inside='-1'), rows[1]]).status_code == 422
    assert post(client, token, doc, '7', [dict(rows[0], inside='1,234.56'), rows[1]]).status_code == 422


def test_staff_warning_draft_and_linked_submit_blocker(table_report, db, sample):
    client, doc, _, _ = table_report
    token = login(client, sample['user'].email)
    ready_unit(db, doc, sample['user'])
    assert post(client, token, doc, '2', staff(True)).status_code == 200
    response = client.get(f'/activity-sections/reports/{doc.id}/unit-tables')
    assert response.status_code == 200
    assert 'Kadın + Erkek = Fiili Çalışan' in response.text
    response = client.post(f'/api/activity-sections/reports/{doc.id}/workflow/submit',
        json={'expected_revision': doc.revision}, headers={'X-CSRF-Token': token})
    assert response.status_code == 409
    problems = response.json()['blockers']
    assert len(problems) == 1 and problems[0]['link'].endswith('#table-2-row-0-actual')
    assert post(client, token, doc, '2', staff()).status_code == 200
    assert client.post(f'/api/activity-sections/reports/{doc.id}/workflow/submit',
        json={'expected_revision': doc.revision}, headers={'X-CSRF-Token': token}).status_code == 200


def test_not_applied_reason_and_projects_choice(table_report, db, sample):
    client, doc, _, _ = table_report
    token = login(client, sample['user'].email)
    rows = [dict(key=a['key'], not_applied=True) for a in tables.book(db, doc)['activities']]
    assert post(client, token, doc, '7', rows).status_code == 200
    payload = sections.report_data(db, sample['user'], doc.id)
    assert any('Uygulanmadı için gerekçe' in b['message'] for b in tables.blockers(payload))
    assert post(client, token, doc, '8', [], no_projects=False).status_code == 422
    assert post(client, token, doc, '8', [], no_projects=True).status_code == 200
    programme = tables.book(db, doc)['programmes'][0]['key']
    row = dict(name='Proje', programme=programme, start='2026-01-01', end='2026-12-31',
               physical='100', spending='0', state='Tamamlandı')
    assert post(client, token, doc, '8', [row], no_projects=True).status_code == 422
    for bad in [dict(row, physical='100,01'), dict(row, spending='-1'), dict(row, programme='other'),
                dict(row, start='2027-01-01'), dict(row, state='Bilinmiyor')]:
        assert post(client, token, doc, '8', [bad], no_projects=False).status_code == 422
    assert post(client, token, doc, '8', [row], no_projects=False).status_code == 200


@pytest.mark.parametrize('target,actual,expected', [
    ('1000','1099',False), ('1000','1100',True), ('1000','900',True), ('1000','901',False),
    ('0','0',False), ('0','0.000001',True), ('0','-1',True), ('-100','-90',True),
])
def test_deviation_boundary(target, actual, expected):
    delta = Decimal(actual) - Decimal(target)
    assert contracts.needs_deviation_explanation('verified', delta, '', actual) is expected
    assert not contracts.needs_deviation_explanation('verified', delta, 'Gerekçe', actual)
    assert not contracts.needs_deviation_explanation('missing', delta, '', actual)


def test_scope_review_return_approval_and_exports(table_report, db, sample, tmp_path):
    client, doc, docs, other = table_report
    save_all(db, sample, doc)
    token = login(client, 'park@example.invalid')
    for path in [f'/activity-sections/reports/{doc.id}/unit-tables',
                 f'/api/activity-sections/reports/{doc.id}',
                 f'/activity-sections/reports/{doc.id}/unit-tables/photos/1']:
        assert client.get(path).status_code == 403
    assert post(client, token, doc, '1', []).status_code == 403
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, '1', []).status_code == 403
    page = client.get(f'/activity-sections/reports/{doc.id}/unit-tables')
    assert page.status_code == 200 and 'Salt okunur' in page.text
    assert 'data-unit-table=' not in page.text
    # Pin this book to the indicator source created by the existing ready fixture.
    ready_unit(db, doc, sample['user'])
    workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision)
    approver = reviewer(db, doc)
    workflow.transition(db, approver, doc.id, 'return', doc.revision, 'Personel sayısını kontrol edin.')
    db.commit()
    tables.save(db, sample['user'], doc.id, '2', doc.revision, staff())
    workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision)
    approval = workflow.transition(db, approver, doc.id, 'approve', doc.revision)
    db.commit()
    before = approval.payload_json
    with pytest.raises(HTTPException) as error:
        tables.save(db, sample['user'], doc.id, '1', doc.revision, [])
    assert error.value.status_code == 409
    snapshot = sections.report_data(db, sample['strategy'], doc.id)
    assert snapshot['unit_tables']['tables']['1']['totals']['area']['value'] == Decimal('1250.50')
    assert snapshot['unit_tables']['photos'][0]['label'] == 'Fotoğraf 1'
    from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
    from app.ar_pdf_export import build_activity_report_pdf
    assert 'image_base64' not in approval.payload_json
    export_payload = tables.with_export_photos(db, snapshot)
    assert 'image_base64' not in snapshot['unit_tables']['photos'][0]
    word = build_activity_report_docx(export_payload, TEMPLATE_PATH)
    with ZipFile(BytesIO(word)) as archive:
        xml = archive.read('word/document.xml').decode()
        for label in ['Tablo 1', 'Tablo 2', 'Tablo 7', 'Tablo 8', 'TOPLAM', 'Fotoğraf 1', '1.250,5', '2.469.135,78']:
            assert label in xml
        assert any(p.startswith('word/media/') for p in archive.namelist())
    from pypdf import PdfReader
    pdf = build_activity_report_pdf(export_payload)
    pdftext = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
    for label in ['Tablo 1', 'Tablo 2', 'Tablo 7', 'Tablo 8', 'Fotoğraf 1']:
        assert label in pdftext
    assert client.get(f'/activity-sections/reports/{doc.id}/export.docx').content == word
    assert client.get(f'/activity-sections/reports/{doc.id}/export.pdf').content == pdf
    assert approval.payload_json == before
    consolidated = sections.report_data(db, sample['strategy'], docs['idare'].id)['unit_tables']
    assert consolidated['units'][0]['tables'] == snapshot['unit_tables']['tables']
    # The legacy idare API is readable by staff; new cross-unit tables must not
    # escape through that existing route, including its immutable release path.
    central_page = client.get(f'/activity-sections/reports/{docs["idare"].id}/unit-tables')
    assert central_page.status_code == 200 and 'id="table-1"' in central_page.text
    assert 'Sentetik Engelsiz Park Projesi' in central_page.text and 'data-unit-table=' not in central_page.text
    idare_payload = sections.report_data(db, sample['strategy'], docs['idare'].id)
    from app.models import ARDocumentFreeze
    raw = sections.numeric_canonical(idare_payload)
    login(client, 'park@example.invalid')
    assert 'unit_tables' not in client.get(f'/api/activity-sections/reports/{docs["idare"].id}').json()
    assert client.get(f'/activity-sections/reports/{docs["idare"].id}/unit-tables').status_code == 403
    db.add(ARDocumentFreeze(document_id=docs['idare'].id, payload_json=raw,
        sha256=contracts.digest(raw), created_by=sample['strategy'].id)); db.commit()
    assert 'unit_tables' not in client.get(f'/api/activity-sections/reports/{docs["idare"].id}').json()


def test_browser_tables_and_capture(table_report, db, sample, tmp_path):
    from playwright.sync_api import sync_playwright, expect
    client, doc, _, _ = table_report
    save_all(db, sample, doc)
    token = login(client, sample['user'].email)
    folder = Path(os.getenv('CIV219_CAPTURE', str(tmp_path))); folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.getenv('CIVENSA_CHROMIUM_PATH', '/usr/bin/chromium'))
        context = browser.new_context(locale='tr-TR')
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(f'http://testserver/activity-sections/reports/{doc.id}/unit-tables')
            assert page.locator('h2').filter(has_text='Tablo 7').count() == 1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            for kind in ('1', '2', '7', '8'):
                panel = page.locator(f'#table-{kind}')
                if width == 390:
                    assert panel.locator('.unit-scroll').evaluate('(el) => el.scrollWidth <= el.clientWidth')
                # Keep the whole panel inside the viewport for Chromium's
                # element capture (fixed off-screen skip links stay off-screen).
                height = int(panel.bounding_box()['height']) + 100
                page.set_viewport_size({'width': width, 'height': max(1000, height)})
                page.evaluate('document.activeElement.blur()')
                panel.screenshot(path=str(folder / f'tablo-{kind}-{width}.png'))
            page.set_viewport_size({'width': width, 'height': 1000})
            page.locator('#photos').screenshot(path=str(folder / f'photos-{width}.png'))
            # Client totals and draft mismatch warning use Turkish numbers.
            page.locator('[name=women_0]').fill('5')
            expect(page.locator('[data-staff-warning]')).to_contain_text('personel sayılarını düzeltin')
            expect(page.locator('[data-unit-table="2"] [data-column-total="women"]')).to_have_text('17')
            page.locator('[name=women_0]').fill('4')
            page.locator('[name=inside_0]').fill('999.999.999.999.999,99')
            page.locator('[name=outside_0]').fill('0,01')
            expect(page.locator('[data-total]').first).to_have_text('1.000.000.000.000.000,00')
        # Exercise the real submit form, grouped errors and its linked field.
        ready_unit(db, doc, sample['user'])
        tables.save(db, sample['user'], doc.id, '2', doc.revision, staff(True)); db.commit()
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(f'http://testserver/activity-sections/reports/{doc.id}/unit-tables')
            page.get_by_role('button', name='Strateji’ye gönder').click()
            expect(page.get_by_role('heading', name='Tablo 2 — ' + tables.TABLES['2'][2], exact=True)).to_be_visible()
            page.screenshot(path=str(folder / f'submit-errors-{width}.png'), full_page=True)
            page.get_by_role('link', name='Tablo 2 · 1. satır').click()
            expect(page.locator('#table-2-row-0-actual')).to_be_in_viewport()
        tables.save(db, sample['user'], doc.id, '2', doc.revision, staff()); db.commit()
        workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision); db.commit()
        approver = reviewer(db, doc); db.commit()
        login(client, approver.email)
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(f'http://testserver/activity-sections/reports/{doc.id}/unit-tables')
            expect(page.get_by_text('Salt okunur ·', exact=False)).to_be_visible()
            assert page.locator('[data-unit-table]').count() == 0
            page.screenshot(path=str(folder / f'strategy-review-{width}.png'), full_page=True)
        workflow.transition(db, approver, doc.id, 'approve', doc.revision); db.commit()
        snapshot = sections.report_data(db, sample['strategy'], doc.id)
        from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
        from app.ar_pdf_export import build_activity_report_pdf
        export_payload = tables.with_export_photos(db, snapshot)
        (folder / 'export-synthetic.docx').write_bytes(build_activity_report_docx(export_payload, TEMPLATE_PATH))
        (folder / 'export-synthetic.pdf').write_bytes(build_activity_report_pdf(export_payload))
        assert not errors
        context.close(); browser.close()


from test_ar_deviation_gate import deviation_report, save_actual, submit


@pytest.mark.parametrize('target,actual,status', [('1.75', '1.92325', 200), ('1.75','1.925',409),
                                                ('0','0',200), ('0','0.000001',409)])
def test_deviation_submit_uses_ten_percent_gate(deviation_report, db, sample, target, actual, status):
    from app.models import IndicatorValue
    row = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == sample['indicator'].id))
    row.value = Decimal(target); db.commit()
    create, _ = deviation_report
    client, doc, report, token = create()
    saved = save_actual(client, token, report['indicators'][0]['report_indicator_id'], value=actual)
    ready_unit(db, doc, sample['user'])
    response = submit(client, token, doc)
    assert response.status_code == status, response.text
    if target != '0':
        assert Decimal(str(saved['deviation_percent'])) == (Decimal('9.9') if status == 200 else Decimal('10'))


def test_photo_limits_scope_real_format_and_revision(table_report, db, sample):
    client, doc, _, _ = table_report
    token = login(client, sample['user'].email)
    source = tables.book(db, doc)['activities'][0]['key']
    url = f'/activity-sections/reports/{doc.id}/unit-tables/photos/upload'
    image = BytesIO(); Image.new('RGB', (40,40), '#123456').save(image, format='JPEG')
    raw = image.getvalue()
    for key, caption, data, name in [(source, '', raw, 'x.jpg'), ('foreign', 'Açıklama', raw, 'x.jpg'),
                                    (source, 'Açıklama', b'not an image', 'x.png'),
                                    (source, 'Açıklama', raw, 'x.svg'),
                                    (source, 'Açıklama', b'x'*(tables.MAX_FILE+1), 'x.png')]:
        result = client.post(url, data=dict(csrf_token=token, expected_revision=doc.revision,
            activity_key=key, caption=caption), files={'file': (name, data)})
        assert result.status_code == 422, result.text
    revision = doc.revision
    assert client.post(url, data=dict(csrf_token=token, expected_revision=revision,
        activity_key=source, caption='Sentetik JPG'), files={'file': ('x.jpg', raw)}).status_code == 303
    assert client.post(url, data=dict(csrf_token=token, expected_revision=revision,
        activity_key=source, caption='Eski sürüm'), files={'file': ('x.jpg', raw)}).status_code == 409
    assert client.get(f'/activity-sections/reports/{doc.id}/unit-tables/photos/99999').status_code == 404


def test_changed_book_keeps_old_data_and_requires_explicit_review(table_report, db, sample):
    _, doc, _, _ = table_report
    save_all(db, sample, doc)
    before = tables.stored(db, doc, '7').payload_json
    original = db.scalar(select(Publication).where(Publication.period_id == doc.period_id))
    updated = json.loads(original.snapshot_json)
    updated['departments'][0]['activities'] = []
    raw = contracts.canonical(updated)
    db.add(Publication(period_id=doc.period_id, version=2, snapshot_json=raw,
        sha256=contracts.digest(raw), created_by=sample['strategy'].id)); db.commit()
    payload = sections.report_data(db, sample['user'], doc.id)
    assert payload['unit_tables']['tables']['7']['rows'] == []
    assert payload['unit_tables']['tables']['7']['book_changed']
    assert any('Bağlı kitap değişti' in b['message'] for b in tables.blockers(payload))
    assert tables.stored(db, doc, '7').payload_json == before
    tables.save(db, sample['user'], doc.id, '7', doc.revision, [])
    tables.save(db, sample['user'], doc.id, '8', doc.revision, [], True)
    payload = sections.report_data(db, sample['user'], doc.id)
    assert not tables.blockers(payload)


def test_invalid_form_count_is_bounded_and_attempted_values_survive(table_report, sample):
    client, doc, _, _ = table_report
    token = login(client, sample['user'].email)
    response = client.post(f'/activity-sections/reports/{doc.id}/unit-tables/1', data={
        'csrf_token': token, 'expected_revision': doc.revision, 'row_count': '999999999',
        'include_0': 'on', 'name_0': 'Korunan <örnek> adı'})
    assert response.status_code == 422
    assert 'Korunan &lt;örnek&gt; adı' in response.text
    assert 'name_2000' not in response.text
    response = client.post(f'/activity-sections/reports/{doc.id}/unit-tables/1', data={
        'csrf_token': token, 'expected_revision': doc.revision, 'row_count': '1',
        'include_0': 'on', 'name_0': 'Korunan bina', 'area_0': 'geçersiz'})
    assert response.status_code == 422 and 'value="geçersiz"' in response.text
    assert 'value="Korunan bina"' in response.text


def test_photos_follow_book_order_and_tall_images_fit_word(table_report, db, sample):
    _, doc, _, _ = table_report
    source = tables.book(db, doc)['activities']
    image = BytesIO(); Image.new('RGB', (10, 1600), '#21514a').save(image, format='PNG')
    for index, caption in [(1, 'İkinci faaliyet'), (0, 'Birinci faaliyet')]:
        tables.upload(db, sample['user'], doc.id, source[index]['key'], doc.revision,
                      caption, image.getvalue(), 'sentetik.png')
    payload = sections.report_data(db, sample['user'], doc.id)
    assert [(p['label'], p['caption']) for p in payload['unit_tables']['photos']] == [
        ('Fotoğraf 1', 'Birinci faaliyet'), ('Fotoğraf 2', 'İkinci faaliyet')]
    from app.ar_export import build_activity_report_docx, TEMPLATE_PATH, BODY
    from docx import Document
    document = Document(BytesIO(build_activity_report_docx(tables.with_export_photos(db, payload), TEMPLATE_PATH)))
    assert all(shape.width <= 3810000 and shape.height <= 5080000 for shape in document.inline_shapes)
    pictures = [p for p in document.paragraphs if p._p.xpath('.//w:drawing')]
    assert len(pictures) == 2 and all(p.style.name == BODY for p in pictures)
