"""CIV-169: real approved books, disposable migrated PostgreSQL, real HTTP/CSRF.

The publication fixture models the owner's approved PP. It deliberately does not
claim that the incomplete first-load data passes the final-publication gates.
"""
from copy import deepcopy
from datetime import date
from io import BytesIO
import json
import os
from pathlib import Path
import re

from docx import Document
from docx.oxml.ns import qn
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from pypdf import PdfReader
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models import (ARDocument, Department, DepartmentScope, OfficialActivity,
    Publication, ReportingPeriod, User)
from app import activity_contract_service as contract, activity_sections_service as sections
from app.security import hash_password
from scripts import first_load_live as live
from scripts.first_load_dryrun import disposable_database, inspect_import, local_test_url
from test_sidebar_ui import browser
from test_internal_control import workbook, action_row
from test_internal_control_questionnaire import question_file
from test_assurance_helpers import variables

pytestmark = pytest.mark.postgres
PASSWORD = 'Civ169-local-test-only!'
TECHNICAL = re.compile(r'name:[0-9a-f]+')


def clean(text):
    assert not TECHNICAL.search(text)
    assert 'None' not in text
    assert '()' not in text


def extracted(response, format):
    assert response.status_code == 200, response.text[:500] if response.status_code != 200 else ''
    if format == 'docx':
        doc = Document(BytesIO(response.content))
        return '\n'.join(node.text or '' for node in doc.element.iter(qn('w:t')))
    if format == 'xlsx':
        book = load_workbook(BytesIO(response.content))
        return '\n'.join(str(v) for s in book for row in s.values for v in row if v is not None)
    if format == 'pdf':
        return '\n'.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
    return response.text


@pytest.fixture(scope='module')
def loaded_books():
    parsed = live.verify_book(live.book_config(2026)[0], year=2026)
    with disposable_database(local_test_url()) as engine, Session(engine, expire_on_commit=False) as db:
        inspection = inspect_import(db, deepcopy(parsed), live.book_config(2026)[0].name, year=2026)
        assert not inspection['apply_error'] and inspection['protected_2027_before'] == inspection['protected_2027_after']
        assert inspection['applied']['indicators'] == 226
        assert len(inspection['catalogue']['unlinked']) == 174
        strategy = db.scalar(select(User).where(User.role == 'strategy'))
        strategy.department_id = db.scalar(select(Department.id).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
        strategy.position = 'director'
        strategy.password_hash = hash_password(PASSWORD)
        renamed = db.scalar(select(Department).where(Department.name == 'Plan Proje Müdürlüğü'))
        user = User(email='civ169@example.invalid', full_name='2026 birim kullanıcısı', role='department',
                    department_id=renamed.id, position='director', can_submit=True, password_hash=hash_password(PASSWORD))
        db.add(user)
        db.commit()
        for period in db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year)):
            # Owner-approved publication precondition, using production freezing.
            payload, definitions = contract.freeze_program_payload(db, period.id, strategy)
            raw = contract.canonical(payload)
            pub = Publication(period_id=period.id, version=1, snapshot_json=raw,
                              sha256=contract.digest(raw), created_by=strategy.id)
            db.add(pub); db.flush()
            contract.attach_publication_definitions(db, pub, definitions, strategy)
            contract.create_report_revision(db, strategy, pub.id, renamed.organization_id)
            sections.create_year(db, strategy, renamed.organization_id, period.id)
        from app import internal_control_service as ic, internal_control_monitoring_service as m
        batch, report = ic.create_import(db, strategy, workbook([
            action_row(**{'7': renamed.name, '8': 'Tüm Müdürlükler', '10':'2026', '11':'Sürekli'})
        ], metadata=['2026–2027 deneme planı', 2026, 2027, 'v1', '03.11.2026']), 'civ169.xlsx')
        assert report['can_commit'], report['issues']
        plan = ic.commit_import(db, strategy, batch.id)
        ic.activate_plan(db, strategy, plan.id)
        from app import internal_control_questionnaire_service as q
        questions = q.save_list(db, strategy, '2026 dönem değerlendirmesi', question_file())
        renamed_ids = list(db.scalars(select(DepartmentScope.department_id).where(
            DepartmentScope.period_id == selected(db).id, DepartmentScope.display_name != '')))
        for year in (2027, 2026):
            period = m.open_period(db, strategy, plan.id, year, 1, date(2028, 1, 20))
            q.attach(db, strategy, period.id, questions.id, renamed_ids, 0)
            if year == 2027:
                m.close_period(db, strategy, period.id, 1, '2026 provası için karşılaştırma dönemi kapatıldı.')
        db.commit()
        yield engine, parsed


@pytest.fixture
def walk(loaded_books):
    # Production handlers may commit; keep every scenario independent anyway.
    engine, _ = loaded_books
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as db:
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app, follow_redirects=False)
            strategy = db.scalar(select(User).where(User.role == 'strategy'))
            user = db.scalar(select(User).where(User.email == 'civ169@example.invalid'))
            def login(actor):
                client.cookies.clear()
                response = client.post('/login', data={'email': actor.email, 'password': PASSWORD})
                assert response.status_code == 303, response.text
                page = client.get('/modules')
                return re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
            token = login(strategy)
            try:
                yield db, client, strategy, user, login, token
            finally:
                client.close()
                app.dependency_overrides.clear()
        transaction.rollback()


def selected(db, year=2026):
    return db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))


def revision(db, year=2026):
    from app.models import ActivityReport, ActivityReportRevision
    return db.scalar(select(ActivityReportRevision).join(ActivityReport).join(ReportingPeriod)
                     .where(ReportingPeriod.year == year))


def ready_2026_narrative(db, doc, user):
    """Required supporting content; actuals remain those saved by the HTTP test."""
    from app.models import ARSectionContent
    from app import assurance_service
    for definition in sections.definitions(db, doc):
        if definition.code in {sections.CORE, 'EKLER'}:
            continue
        content = db.scalar(select(ARSectionContent).where(ARSectionContent.document_id == doc.id,
            ARSectionContent.definition_id == definition.id))
        content.blocks_json = '[{"type":"paragraph","text":"2026 yıllık değerlendirme"}]'
        content.status = 'not_applicable' if definition.code.startswith('III.A') else 'ready'
        content.reason = 'Bu testte malî veri bulunmuyor.' if content.status == 'not_applicable' else ''
        content.edited_by = user.id
    db.flush()
    assurance_service.save(db, user, doc.id, 'EK-2', {'expected_revision':doc.revision, 'variables':variables(year=2026)})
    db.commit()


@pytest.mark.parametrize('year', [2026, 2027])
def test_period_screens_and_names(walk, year):
    db, client, strategy, user, login, token = walk
    period = selected(db, year)
    paths = ['/modules', '/dashboard', '/activity-report?year=' + str(year), '/review',
        '/report-builder', '/report-builder/manifest', '/report-builder/manifest.json', '/activity-mapping',
        '/source-comparison', '/activity-reports', f'/activity-reports/revisions/{revision(db, year).id}',
        '/activity-sections', '/structure', '/users', '/budget-reallocations', '/budget-reallocations/new']
    for path in paths:
        response = client.get(path + ('&' if '?' in path else '?') + f'period_id={period.id}')
        assert response.status_code == 200, (path, response.status_code, response.text[:300])
        clean(response.text)
    renamed = db.scalars(select(DepartmentScope).where(DepartmentScope.period_id == selected(db).id,
                                                     DepartmentScope.display_name != '')).all()
    assert len(renamed) == 4
    for scope in renamed:
        department = db.get(Department, scope.department_id)
        expected = scope.display_name if year == 2026 else department.name
        for path in [f'/program/{department.id}', f'/department/{department.id}',
                     f'/program/{department.id}/economic-split']:
            response = client.get(path + ('&' if '?' in path else '?') + f'period_id={period.id}')
            assert response.status_code == 200, path
            clean(response.text)
            assert expected in response.text, path
        for path in ['/dashboard','/review','/report-builder','/activity-report?year=' + str(year)]:
            assert expected in client.get(path + ('&' if '?' in path else '?') + f'period_id={period.id}').text, (path, expected)
    login(user)
    for path in ['/dashboard', f'/department/{user.department_id}', f'/program/{user.department_id}',
                 f'/activity-reports/revisions/{revision(db, year).id}', '/activity-sections', '/submit-authorizations']:
        response = client.get(path + ('&' if '?' in path else '?') + f'period_id={period.id}')
        assert response.status_code == 200, (path, response.text[:200])
        clean(response.text)
    page = client.get(f'/submit-authorizations?period_id={period.id}')
    expected = 'Harita ve Planlama Müdürlüğü' if year == 2026 else 'Plan Proje Müdürlüğü'
    assert expected in page.text


@pytest.mark.parametrize('year', [2026, 2027])
def test_catalogue_edit_keeps_technical_key(walk, year):
    db, client, strategy, user, login, token = walk
    period = selected(db, year)
    item = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == period.id))
    old_code = item.code
    page = client.get('/report-builder', params={'period_id':period.id})
    if year == 2026:
        assert old_code not in page.text
    else:
        assert old_code in page.text
    from app.models import ActivityResponsibility
    ids = list(db.scalars(select(ActivityResponsibility.department_id).where(ActivityResponsibility.official_activity_id == item.id)))
    data = {f:getattr(item, f) for f in ('program_code','program_name','subprogram_code','subprogram_name','code','name')}
    data.update(id=item.id, period_id=period.id, csrf_token=token, department_ids=[str(i) for i in ids], name=item.name + ' düzenlendi')
    if year == 2026:
        for field in ('code','program_code','subprogram_code'):
            data.pop(field)
    response = client.post('/report-builder/catalogue', data=data)
    assert response.status_code == 303, response.text[:500]
    db.refresh(item)
    assert item.code == old_code
    assert item.name.endswith(' düzenlendi')
    if year == 2026:
        data.update(code='9999', program_code='9999', subprogram_code='9999')
        assert client.post('/report-builder/catalogue', data=data).status_code == 303
        db.refresh(item)
        assert item.code == old_code and item.program_code == item.subprogram_code == ''
        data['name'] = ''
        response = client.post('/report-builder/catalogue', data=data)
        assert response.status_code == 422
        clean(response.text)
        response = client.get('/audit')
        assert response.status_code == 200
        clean(response.text)


@pytest.mark.parametrize('year', [2026, 2027])
def test_pp_and_activity_report_exports(walk, year):
    db, client, strategy, user, login, token = walk
    period = selected(db, year)
    pub = db.scalar(select(Publication).where(Publication.period_id == period.id))
    frozen = pub.snapshot_json, pub.sha256
    # Full PP PDF has a separately recorded, bounded rehearsal (see walk report).
    # Its 2,869-row reconciliation table must not stall the ordinary CI suite.
    paths = [(f'/report-builder/preview.docx?period_id={period.id}', 'docx')]
    paths += [(f'/publications/{pub.id}.{f}', f) for f in ('docx','json')]
    names = db.scalars(select(DepartmentScope).where(DepartmentScope.period_id == selected(db).id,
                                                   DepartmentScope.display_name != '')).all()
    docs = db.scalars(select(ARDocument).where(ARDocument.period_id == period.id,
        (ARDocument.department_id.is_(None)) | ARDocument.department_id.in_([s.department_id for s in names]))).all()
    for doc in docs:
        page = client.get(f'/activity-sections/reports/{doc.id}')
        assert page.status_code == 200
        clean(page.text)
        paths += [(f'/activity-sections/reports/{doc.id}/export.{f}', f) for f in ('docx','pdf','json')]
    for path, format in paths:
        text = extracted(client.get(path), format)
        clean(text)
        if path.startswith(('/publications/', '/report-builder/')):
            for scope in names:
                expected = scope.display_name if year == 2026 else db.get(Department, scope.department_id).name
                assert expected in text, (path, expected)
        for doc in docs:
            if doc.department_id and path.startswith(f'/activity-sections/reports/{doc.id}/export.'):
                scope = next(s for s in names if s.department_id == doc.department_id)
                expected = scope.display_name if year == 2026 else db.get(Department, scope.department_id).name
                assert expected in text, (path, expected)
    db.refresh(pub)
    assert (pub.snapshot_json, pub.sha256) == frozen
    if year == 2027:
        assert client.get(f'/publications/{pub.id}.json').text == frozen[0]


def test_book_order_and_absent_economic_amounts(walk, loaded_books):
    from app.book_export import blocks
    db, client, strategy, user, login, token = walk
    _, source = loaded_books
    payload = json.loads(db.scalar(select(Publication).where(Publication.period_id == selected(db).id)).snapshot_json)
    content = blocks(payload)
    tables = [rows for kind, rows in content if kind == 'table']
    # Compare the printed book order to the export, including repeated names.
    source_departments = {source['book_department_names'].get(d['name'],d['name']):d
                          for d in source['departments']}
    expected = [[i['name'] for i in block['indicators']]
        for department in payload['departments'] if department['department'] in source_departments
        for block in source_departments[department['department']]['blocks']]
    actual = [[row[0] for row in table[1:]] for table in tables
        if table[0][0] == 'Kod / Performans Göstergesi']
    assert actual == expected
    expected_activities = [[a['name'] for a in source_departments[d['department']]['activities']]
        for d in payload['departments'] if d['department'] in source_departments]
    actual_activities = [[row[0].split('\n')[0].strip() for row in table[1:-3:3]] for table in tables
        if table[0][0] == 'Faaliyet / Finansman']
    # The 2027-only directorate has no 2026 costs and contributes an empty table.
    assert [rows for rows in actual_activities if rows] == [rows for rows in expected_activities if rows]
    totals = next(table for table in tables if table[0] == ['Müdürlük', '2026', '2027', '2028'])
    indexed = {row[0]:row for row in totals[1:]}
    missing = 0
    for department in payload['departments']:
        if (department.get('scope') or {}).get('status') == 'excluded':
            continue
        for index, year in enumerate((2026, 2027, 2028), 1):
            values = [v for v in department['economics'] if v['year'] == year
                      and v['value_kind'] == ('budget' if year == 2026 else 'forecast')]
            if any(v['amount'] is None for v in values):
                assert indexed[department['department']][index] == '—'
                missing += 1
    assert missing


def test_first_load_publication_gate_stays_closed(walk):
    db, client, strategy, user, login, token = walk
    response = client.post('/report-builder/publish', data={'csrf_token':token, 'period_id':selected(db).id})
    assert response.status_code == 422
    assert 'kataloğu bağlantısı eksik' in response.text
    clean(response.text)


def test_actual_entry_submit_and_strategy_review(walk):
    db, client, strategy, user, login, token = walk
    from app.models import ReportIndicator, PublicationIndicatorBinding, ActualRevision
    rev = revision(db)
    indicators = db.scalars(select(ReportIndicator).join(PublicationIndicatorBinding).where(
        ReportIndicator.report_revision_id == rev.id, PublicationIndicatorBinding.department_id == user.department_id)
        .order_by(ReportIndicator.id)).all()
    assert indicators
    token = login(user)
    for item in indicators:
        response = client.post(f'/activity-reports/indicators/{item.id}/actuals', data={
            'csrf_token':token, 'expected_revision':0, 'value':'12,5', 'state':'verified', 'evidence_rows':'1',
            'source_title':'2026 birim kayıtları', 'source_locator':'Sayfa 1', 'source_revision':'2026',
            'explanation':'2026 gerçekleşmesi kaynak kayıtlarından doğrulandı.', 'deviation_reason':'Faaliyetler tamamlandı.'})
        assert response.status_code == 303, response.text[:1000]
        actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id))
        assert actual.value == 12.5
    doc = db.scalar(select(ARDocument).where(ARDocument.period_id == selected(db).id,
                                           ARDocument.department_id == user.department_id))
    ready_2026_narrative(db, doc, user)
    response = client.post(f'/activity-sections/reports/{doc.id}/workflow/submit',
                           data={'csrf_token':token, 'expected_revision':doc.revision})
    assert response.status_code == 303, response.text[:1000]
    token = login(strategy)
    page = client.get(f'/activity-sections/reports/{doc.id}')
    assert page.status_code == 200
    clean(page.text)
    response = client.post(f'/activity-sections/reports/{doc.id}/workflow/approve',
                           data={'csrf_token':token, 'expected_revision':doc.revision})
    assert response.status_code == 303, response.text[:1000]
    text = extracted(client.get(f'/activity-sections/reports/{doc.id}/export.docx'), 'docx')
    clean(text)
    assert 'Harita ve Planlama Müdürlüğü' in text and '12,5' in text


@pytest.mark.parametrize('year', [2026, 2027])
def test_internal_control_period_names_and_exports(walk, year):
    db, client, strategy, user, login, token = walk
    from app.internal_control_monitoring_models import ICMonitoringPeriod, ICMonitoringBatch
    period = db.scalar(select(ICMonitoringPeriod).where(ICMonitoringPeriod.year == year))
    expected = 'Harita ve Planlama Müdürlüğü' if year == 2026 else 'Plan Proje Müdürlüğü'
    page = client.get('/internal-control/monitoring', params={'period_id':period.id})
    assert page.status_code == 200
    clean(page.text)
    assert expected in page.text
    names = db.scalars(select(DepartmentScope).where(DepartmentScope.period_id == selected(db).id,
                                                   DepartmentScope.display_name != '')).all()
    for scope in names:
        label = scope.display_name if year == 2026 else db.get(Department, scope.department_id).name
        assert label in page.text
    page = client.get(f'/internal-control/plans/{period.plan_id}?year={year}')
    assert page.status_code == 200
    clean(page.text)
    assert expected in page.text
    from app import internal_control_questionnaire_service as q
    for invalid in ('geçersiz', '2025'):
        response = client.get(f'/internal-control/plans/{period.plan_id}?year={invalid}')
        assert response.status_code == 422 and 'Plan yılı geçersiz' in response.text
    question = next(b for b in q.batches(db, period.id) if b.department_id == user.department_id)
    page = client.get(f'/internal-control/questionnaires/batches/{question.id}')
    assert page.status_code == 200
    clean(page.text)
    assert expected in page.text
    text = extracted(client.get(f'/internal-control/monitoring/periods/{period.id}/questionnaire.xlsx?draft=true'), 'xlsx')
    clean(text)
    for scope in names:
        label = scope.display_name if year == 2026 else db.get(Department, scope.department_id).name
        assert label in text
    for report in ('report', 'official-report'):
        for format in ('docx','xlsx'):
            text = extracted(client.get(f'/internal-control/monitoring/periods/{period.id}/{report}.{format}?draft=true'), format)
            clean(text)
            assert expected in text
    text = extracted(client.get(f'/internal-control/monitoring/plans/{period.plan_id}/annual.xlsx?year={year}'), 'xlsx')
    clean(text)
    assert str(year) in text
    page = client.get(f'/internal-control/monitoring/periods/{period.id}/narrative')
    assert page.status_code == 200
    clean(page.text)
    login(user)
    page = client.get('/internal-control/our-actions', params={'period_id':period.id})
    assert page.status_code == 200
    clean(page.text)
    batch = db.scalar(select(ICMonitoringBatch).where(ICMonitoringBatch.period_id == period.id))
    page = client.get(f'/internal-control/monitoring/batches/{batch.id}')
    assert page.status_code == 200
    clean(page.text)
    assert expected in page.text


@pytest.mark.parametrize('width', [390, 1280])
def test_changed_screen_evidence(walk, browser, width):
    db, client, strategy, user, login, token = walk
    period = selected(db)
    from app.internal_control_monitoring_models import ICMonitoringPeriod
    from app import internal_control_questionnaire_service as q
    ic_period = db.scalar(select(ICMonitoringPeriod).where(ICMonitoringPeriod.year == 2026))
    question = next(b for b in q.batches(db, ic_period.id) if b.department_id == user.department_id)
    from app.models import ActivityResponsibility
    item = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == period.id))
    owners = list(db.scalars(select(ActivityResponsibility.department_id).where(ActivityResponsibility.official_activity_id == item.id)))
    response = client.post('/report-builder/catalogue', data={
        'id':item.id, 'period_id':period.id, 'csrf_token':token,
        'name':item.name + ' ekran provası', 'program_name':item.program_name, 'subprogram_name':item.subprogram_name,
        'department_ids':[str(did) for did in owners]})
    assert response.status_code == 303
    paths = [('catalogue', f'/report-builder?period_id={period.id}', '#catalogue'),
        ('program', f'/program/{user.department_id}?period_id={period.id}', '#rp-catalogue'),
        ('economic-split', f'/program/{user.department_id}/economic-split?period_id={period.id}', None),
        ('users', f'/users?period_id={period.id}', '.users-page'),
        ('audit', f'/audit?period_id={period.id}&action=catalogue_create', None),
        ('ic-plan', f'/internal-control/plans/{ic_period.plan_id}?year=2026', '.internal-control-page'),
        ('ic-questionnaire-overview', f'/internal-control/monitoring?period_id={ic_period.id}', '#soru-formu'),
        ('ic-questionnaire-detail', f'/internal-control/questionnaires/batches/{question.id}', '.questionnaire-form')]
    folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
    with browser.new_context(viewport={'width':width,'height':900}) as context:
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')})
            headers = dict(response.headers)
            headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        for label, path, anchor in paths:
            page.goto('http://testserver' + path)
            if anchor:
                section = page.locator(anchor)
                if label == 'catalogue':
                    section.locator('..').locator('details').first.evaluate('(e) => e.open = true')
                if label == 'users':
                    page.locator('.users-page details').first.evaluate('(e) => e.open = true')
                    section = page.locator('.missing-departments')
                section.evaluate('(e) => e.scrollIntoView({block:"start"})')
            if label == 'audit':
                page.locator('.audit-details details').first.evaluate('(e) => e.open = true')
                page.locator('.audit-details').first.evaluate('(e) => e.scrollIntoView({block:"start",inline:"end"})')
            clean(page.locator('body').inner_text())
            if folder:
                target = Path(folder); target.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target / f'{label}-{width}.png'))
        login(user)
        page.goto(f'http://testserver/submit-authorizations?period_id={period.id}')
        clean(page.locator('body').inner_text())
        if folder:
            page.screenshot(path=str(Path(folder) / f'submit-authorizations-{width}.png'))
