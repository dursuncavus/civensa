"""CIV-182 council recipe, real approved PostgreSQL sources and offline output."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
import logging
import os
from pathlib import Path
import re
from uuid import uuid4

from lxml import html
import pytest
from pypdf import PdfReader
from sqlalchemy import select

from app import activity_sections_service as service, ar_unit_workflow_service as workflow
from app.activity_contract_service import canonical, digest
from app.models import (ActivityReport, ActivityReportRevision, ActualRevision, ARDocumentFreeze, Department, DepartmentScope,
    IndicatorDefinitionRevision, IndicatorIdentity, Publication, PublicationIndicatorBinding, ReportIndicator, User)
from app.sunum import activity_report, render_deck
from app.sunum.engine import prepare_slides
from app.sunum.recipes_idare import idare_activity_report
from ar_unit_workflow_helpers import ready_unit, approve_unit
from test_activity_sections import section_client, login, resource, save
from test_sunum_browser import browser_options, deck_url

pytestmark = pytest.mark.postgres


def seed_indicators(db, doc, actor, values):
    report = db.scalar(select(ActivityReport).where(ActivityReport.organization_id == doc.organization_id,
        ActivityReport.period_id == doc.period_id))
    if report is None:
        publication = Publication(period_id=doc.period_id, version=1, snapshot_json='{}', sha256=digest('{}'), created_by=actor.id)
        db.add(publication)
        db.flush()
        report = ActivityReport(organization_id=doc.organization_id, period_id=doc.period_id, current_revision=1)
        db.add(report)
        db.flush()
        revision = ActivityReportRevision(report_id=report.id, revision=1, publication_id=publication.id,
            publication_sha256=publication.sha256, created_by=actor.id)
        db.add(revision)
        db.flush()
    else:
        revision = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id,
            ActivityReportRevision.revision == report.current_revision))
    for index, (target, actual) in enumerate(values):
        identity = IndicatorIdentity(indicator_id=str(uuid4()), organization_id=doc.organization_id)
        db.add(identity)
        db.flush()
        definition_json = canonical(dict(name=f'{doc.department_id} birim göstergesi {index}', unit='Adet',
            targets=[dict(value=str(target), state='verified')], data_source='Test kaydı'))
        definition = IndicatorDefinitionRevision(indicator_id=identity.indicator_id, revision=1,
            period_id=doc.period_id, definition_json=definition_json, sha256=digest(definition_json), created_by=actor.id)
        db.add(definition)
        db.flush()
        binding = PublicationIndicatorBinding(publication_id=revision.publication_id,
            snapshot_indicator_id=20000+doc.id*10+index, definition_revision_id=definition.id,
            department_id=doc.department_id, created_by=actor.id, reason='CIV-182 test kaynağı')
        db.add(binding)
        db.flush()
        item = ReportIndicator(report_revision_id=revision.id, publication_binding_id=binding.id)
        db.add(item)
        db.flush()
        db.add(ActualRevision(report_indicator_id=item.id, revision=1, value=actual, state='verified',
            evidence_json='[{"title":"Kaynak","locator":"Sayfa 1","source_revision":"1"}]',
            explanation='Test gözlemi', deviation_json='{}', created_by=actor.id))
    db.flush()


@pytest.fixture
def idare_fixture(section_client, db, sample, request):
    client, docs, other, finance = section_client
    options = getattr(request, 'param', {})
    idare = docs['idare']
    units = [docs[f'birim:{dep.id}'] for dep in (sample['department'], other, finance)]
    token = login(client, sample['strategy'].email)
    budget_rows = [dict(department_id=doc.department_id, economic_code='03', initial=str(initial),
        added='0', deducted='0', actual=str(actual), cancelled='0', carried='0')
        for doc, initial, actual in zip(units, [1000, 2000, 3000], [700, 1500, 2400])]
    if options.get('missing_budget'):
        budget_rows.pop()
    response = client.post(f'/api/activity-sections/reports/{idare.id}/financial/budget/expenditure',
        headers={'X-CSRF-Token': token}, json={'expected_revision': idare.revision, 'rows': budget_rows})
    assert response.status_code == 200, response.text
    for doc, counts, observations in zip(units, [(18, 4), (8, 2), (5, 1)],
            [[(100, 75), (20, 10)], [(40, 0), (20, 30)], [(10, None)]]):
        actor = db.scalar(select(User).where(User.department_id == doc.department_id, User.role == 'department'))
        seed_indicators(db, doc, actor, observations)
        ready_unit(db, doc, actor)
        if options.get('blank_staff') and doc == units[-1]:
            counts = (None, None)
        assert resource(client, token, doc, 'employment', [dict(category='memur', count=counts[0]),
            dict(category='işçi — kadrolu', count=counts[1])]).status_code == 200
        assert save(client, token, doc, 'I.C.4', status='ready').status_code == 200
        approve_unit(db, doc, actor)
    assert save(client, token, idare, 'I.B', blocks=[dict(type='bullets', items=[
        'Belediye hizmetlerini planlamak', 'Kurumsal kaynakları verimli kullanmak'])]).status_code == 200
    assert save(client, token, idare, 'II.B', blocks=[dict(type='paragraph',
        text='Erişilebilir ve sürdürülebilir belediye hizmetleri sunmak.')]).status_code == 200
    payload = service.report_data(db, sample['strategy'], idare.id)
    sources = [dict(department_id=p['department_id'], department=p['department'], core=p['core'])
        for _, p in workflow.approved_sources(db, idare)[0]]
    return dict(client=client, docs=docs, idare=idare, units=units, payload=payload,
        enriched=dict(payload, unit_indicator_sources=sources), token=token)


def by_title(slides, title):
    return next(s for s in slides if s.get('title') == title)


def test_real_staff_budget_and_verified_indicator_aggregates(idare_fixture):
    fixture = idare_fixture
    original = deepcopy(fixture['enriched'])
    slides = prepare_slides(idare_activity_report(fixture['enriched']))
    assert fixture['enriched'] == original
    assert len(fixture['payload']['unit_manifest']) == 3
    assert slides[0]['subtitle'] == 'Meclis sunumu'
    assert slides[0]['department'] == fixture['payload']['organization']
    staff = by_title(slides, 'Müdürlüklere göre personel')
    assert staff['categories'] == [u['department'] for u in fixture['payload']['unit_manifest']]
    assert staff['series'][0]['values'] == [22, 10, 6]
    assert by_title(slides, 'Kurumumuzun ekibi')['figures'][0]['value'] == 38
    budget = by_title(slides, 'Bütçe bir bakışta')['figures']
    assert [f['value'] for f in budget] == [6000, 4600, Decimal('76.67')]
    assert by_title(slides, 'Müdürlüklere göre harcama')['series'][0]['values'] == [2400, 1500, 700]
    summary = by_title(slides, 'Müdürlüklere göre gösterge özeti')
    assert [row[1:] for row in summary['rows']] == [['2', '2', '62,5'], ['2', '2', '75'], ['1', '—', '—']]


@pytest.mark.parametrize('idare_fixture', [dict(blank_staff=True)], indirect=True)
def test_blank_staff_is_not_partial_or_zero(idare_fixture):
    slides = prepare_slides(idare_activity_report(idare_fixture['enriched']))
    assert not any(s.get('title') == 'Kurumumuzun ekibi' for s in slides)
    chart = by_title(slides, 'Müdürlüklere göre personel')
    assert chart['series'][0]['values'] == [22, 10, None]
    assert chart['series'][0]['display'] == ['22', '10', '—']


@pytest.mark.parametrize('idare_fixture', [dict(missing_budget=True)], indirect=True)
def test_missing_unit_budget_skips_comparison_and_total_with_log(idare_fixture, caplog):
    with caplog.at_level(logging.INFO):
        response = idare_fixture['client'].get(f"/activity-sections/reports/{idare_fixture['idare'].id}/sunum.html")
    assert response.status_code == 200
    document = html.fromstring(response.content)
    headings = document.xpath('//h2/text()')
    assert 'Müdürlüklere göre harcama' not in headings
    assert 'Bütçe bir bakışta' not in headings
    assert 'Bu raporda müdürlüklere göre eksiksiz harcama bilgisi yok' in caplog.text


def test_route_selects_idare_and_birim_deck_bytes_are_unchanged(idare_fixture, db, sample):
    fixture = idare_fixture
    client = fixture['client']
    for doc in [fixture['idare'], *fixture['units']]:
        payload = service.report_data(db, sample['strategy'], doc.id)
        recipe = idare_activity_report(fixture['enriched']) if doc.department_id is None else activity_report(payload)
        # Unit approvals use the canonical export payload including workflow.
        canonical_json = client.get(f'/activity-sections/reports/{doc.id}/export.json').content
        short = sha256(canonical_json).hexdigest()[:8].upper()
        code = short[:4]+'-'+short[4:] if payload['frozen'] else 'TASLAK'
        expected = render_deck(recipe, title=f"{payload['department']} · {payload['year']} Faaliyet Raporu sunumu", code=code)
        for suffix in ('sunum', 'sunum.html'):
            response = client.get(f'/activity-sections/reports/{doc.id}/{suffix}')
            assert response.status_code == 200
            assert response.content == expected
        if doc.department_id is None:
            assert b'Meclis sunumu' in expected
        else:
            assert b'Ba\xc5\x9fkanl\xc4\xb1k sunumu' in expected
    for email in (sample['user'].email, 'park@example.invalid', 'finance@example.invalid'):
        login(client, email)
        for suffix in ('sunum', 'sunum.html'):
            response = client.get(f"/activity-sections/reports/{fixture['idare'].id}/{suffix}")
            assert response.status_code == 403


def test_missing_units_and_legacy_unattributed_indicators_are_not_invented(idare_fixture, caplog):
    payload = deepcopy(idare_fixture['payload'])
    payload['missing_units'] = [dict(department_id=100, department='Henüz onaylanmayan müdürlük')]
    with caplog.at_level(logging.INFO):
        slides = idare_activity_report(payload)
    assert not any(s.get('title') == 'Müdürlüklere göre gösterge özeti' for s in slides)
    assert 'Bu raporda müdürlüklere göre doğrulanmış gösterge bilgisi yok' in caplog.text
    assert by_title(slides, 'Henüz onaylanmamış birimler')['bullets'] == ['Henüz onaylanmayan müdürlük']
    assert not any(s.get('title') == 'Kurumumuzun ekibi' for s in slides)


def freeze_fixture(db, fixture, actor, payload=None):
    serialized = service.numeric_canonical(payload if payload is not None else fixture['payload'])
    release = ARDocumentFreeze(document_id=fixture['idare'].id, payload_json=serialized,
        sha256=digest(serialized), created_by=actor.id)
    db.add(release)
    db.commit()
    return release


def test_frozen_summary_keeps_exact_approval_after_unit_is_reapproved(idare_fixture, db, sample):
    fixture = idare_fixture
    release = freeze_fixture(db, fixture, sample['strategy'])
    url = f"/activity-sections/reports/{fixture['idare'].id}/sunum.html?version=1"
    before = fixture['client'].get(url)
    assert before.status_code == 200
    unit = fixture['units'][0]
    workflow.transition(db, sample['strategy'], unit.id, 'reopen', unit.revision, 'Yeni gözlem')
    item = db.scalar(select(ReportIndicator).join(PublicationIndicatorBinding,
        PublicationIndicatorBinding.id == ReportIndicator.publication_binding_id)
        .where(PublicationIndicatorBinding.department_id == unit.department_id).order_by(ReportIndicator.id))
    actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id))
    db.add(ActualRevision(report_indicator_id=item.id, revision=2, supersedes_id=actual.id, value=100,
        state='verified', evidence_json=actual.evidence_json, explanation='Yeni onaylı gözlem',
        deviation_json='{}', created_by=sample['user'].id))
    db.flush()
    ready_unit(db, unit, sample['user'])
    approve_unit(db, unit, sample['user'])
    new_approval = workflow.latest(db, unit, 'approve')
    assert new_approval.id != fixture['payload']['unit_manifest'][0]['approval_id']
    assert service.core_summary(db, unit)['indicators'][0]['actual'] == 100
    after = fixture['client'].get(url)
    assert after.status_code == 200
    assert after.content == before.content
    short = sha256(release.payload_json.encode()).hexdigest()[:8].upper()
    assert f'Doğrulama kodu <b>{short[:4]}-{short[4:]}</b>' in after.text


@pytest.mark.parametrize('mismatch', ['approval_id', 'sha256', 'department_id'])
def test_frozen_manifest_must_match_verified_unit_source(idare_fixture, db, sample, mismatch):
    payload = deepcopy(idare_fixture['payload'])
    payload['unit_manifest'][0][mismatch] = '0'*64 if mismatch == 'sha256' else 999999
    freeze_fixture(db, idare_fixture, sample['strategy'], payload)
    response = idare_fixture['client'].get(f"/activity-sections/reports/{idare_fixture['idare'].id}/sunum.html")
    assert response.status_code == 409
    assert 'Strateji ile rapor sürümünü kontrol edin' in response.json()['detail']


def test_summary_verified_only_paging_and_blank_values(idare_fixture):
    payload = deepcopy(idare_fixture['enriched'])
    base = dict(name='Gösterge', targets=[dict(value=100, state='verified')], actual=50, actual_state='verified')
    candidates = [base, dict(base, actual=0), dict(base, actual=None), dict(base, actual_state='needs_review'),
        dict(base, targets=[dict(value=200, state='needs_review')]), dict(base, targets=[dict(value=0, state='verified')]),
        dict(base, targets=[dict(value=100, state='verified')]*2), dict(base, actual='NaN')]
    payload['unit_indicator_sources'] = [dict(department=f'Müdürlük {i}', core=dict(indicators=candidates)) for i in range(23)]
    payload['unit_indicator_sources'][-1]['core'] = dict(indicators=[dict(base, actual=None)])
    tables = [s for s in prepare_slides(idare_activity_report(payload)) if s['type'] == 'table']
    assert [s['continuation'] for s in tables] == ['Tablo 1/3', 'Tablo 2/3', 'Tablo 3/3']
    assert [len(s['rows']) for s in tables] == [10, 10, 3]
    assert tables[0]['rows'][0][1:] == ['8', '5', '25']
    assert tables[-1]['rows'][-1][1:] == ['1', '—', '—']


def test_missing_department_budget_provenance_logs_and_empty_data_skips_slides(idare_fixture, caplog):
    payload = deepcopy(idare_fixture['enriched'])
    for row in payload['financial']['tables']['expenditure']['rows']:
        row.pop('department_id')
    with caplog.at_level(logging.INFO):
        slides = idare_activity_report(payload)
    assert not any(s.get('title') == 'Müdürlüklere göre harcama' for s in slides)
    assert 'Bu raporda müdürlüklere göre eksiksiz harcama bilgisi yok' in caplog.text
    assert by_title(slides, 'Bütçe bir bakışta')['figures'][0]['value'] == 6000
    with caplog.at_level(logging.INFO):
        empty = idare_activity_report(dict(year=2027, organization='Test Belediyesi'))
    assert [s['type'] for s in empty] == ['cover', 'closing']
    assert 'Bu raporda müdürlüklere göre personel bilgisi yok' in caplog.text


def test_download_offline_browser_and_screenshots(idare_fixture, tmp_path):
    from playwright.sync_api import sync_playwright, expect
    fixture = idare_fixture
    response = fixture['client'].get(f"/activity-sections/reports/{fixture['idare'].id}/sunum.html")
    assert response.status_code == 200
    assert len(response.content) <= 3_000_000
    document = html.fromstring(response.content)
    # Vendor license comments and SVG namespace strings are not network loads.
    assert not document.xpath('//*[@src and not(starts-with(@src,"data:"))]')
    assert not document.xpath('//*[@href and not(starts-with(@href,"#"))]')
    assert not re.search(rb'(?:src|href)=["\']https?://', response.content)
    path = tmp_path / 'idare-sunum.html'
    path.write_bytes(response.content)
    folder = Path(os.environ.get('CIVENSA_IDARE_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'single-file-size.txt').write_text(f'{len(response.content)} bytes\n')
    (folder / 'slides.json').write_text(json.dumps([dict(type=s['type'], title=s.get('title', s.get('department')))
        for s in prepare_slides(idare_activity_report(fixture['enriched']))], ensure_ascii=False, indent=2))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**browser_options())
        page = browser.new_page(viewport=dict(width=1920, height=1080), offline=True)
        errors, network = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: network.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        url = deck_url(page, path)
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        expect(page.locator('section.present .lead')).to_have_text('Meclis sunumu')
        page.screenshot(path=str(folder / 'cover.png'))
        for title, filename in [('Müdürlüklere göre personel', 'staff-per-mudurluk.png'),
                ('Müdürlüklere göre gösterge özeti', 'indicator-summary.png')]:
            page.evaluate('title => { const s = [...document.querySelectorAll("section")].find(s => s.querySelector("h2")?.textContent === title); deck.slide(deck.getIndices(s).h,0,-1); }', title)
            page.wait_for_timeout(1600)
            if filename.startswith('staff'):
                chart = page.locator('section.present [data-chart]')
                expect(chart.locator('svg')).to_be_visible()
                option = chart.evaluate('(el)=>echarts.getInstanceByDom(el).getOption()')
                assert option['series'][0]['data'] == [22, 10, 6]
            else:
                expect(page.locator('section.present tbody tr')).to_have_count(3)
                assert '62,5' in page.locator('section.present').inner_text()
            page.screenshot(path=str(folder / filename))
        assert errors == []
        assert network == ([url] if url.startswith('http:') else [])
        page.goto(url + '#pdf')
        page.wait_for_function('() => window.sunumRendered === true')
        assert page.locator('html.pdf').count() == 1
        assert page.locator('[data-chart] svg').count() == 2
        pdf = PdfReader(BytesIO(page.pdf(prefer_css_page_size=True, print_background=True)))
        assert len(pdf.pages) == 13
        assert '62,5' in pdf.pages[11].extract_text()
        assert errors == []
        browser.close()
