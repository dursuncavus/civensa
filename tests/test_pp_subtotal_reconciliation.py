"""CIV-069: current PP totals, source reconciliation and the frozen book."""
import io
import json
from decimal import Decimal

import pytest
from docx import Document
from pypdf import PdfReader
from sqlalchemy import select, func

from app.models import (Activity, ActivityCatalogueLink, ActivityCostValue, Program,
                        Publication, ReportCard, ReportingPeriod, SubProgram)
from app.program_service import book_snapshot, publication_checks
from app.book_export import export_book
from tests.test_publication_gates import prepare

pytestmark = pytest.mark.postgres


def reconciliation(db, sample):
    return book_snapshot(db, sample['period'].id)['cost_reconciliation']


def current_rows(db, sample):
    return [r for r in reconciliation(db, sample) if r['year'] == 2027 and r['level'] != 'department_total']


def source(db, sample, amount='133.50'):
    value = db.scalar(select(ActivityCostValue).where(
        ActivityCostValue.activity_id == sample['activity'].id,
        ActivityCostValue.year == 2027, ActivityCostValue.funding_type == 'total'))
    value.source_amount = Decimal(amount)
    db.commit()
    return value


def add_activity(db, sample, amount='0.10'):
    a = Activity(period_id=1, department_id=1, subprogram_id=sample['subprogram'].id,
                 card_id=sample['card'].id, name='İkinci faaliyet', explanation='Güncel kayıt')
    db.add(a); db.flush()
    db.add(ActivityCatalogueLink(activity_id=a.id, official_activity_id=sample['official'].id))
    for y, k in [(2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')]:
        for fund, value in [('inside', amount), ('outside', '0'), ('total', amount)]:
            db.add(ActivityCostValue(activity_id=a.id, year=y, value_kind=k,
                                     funding_type=fund, amount=Decimal(value)))
    db.commit()
    return a


def test_subtotals_sum_current_records_at_every_level(db, sample):
    add_activity(db, sample)
    rows = current_rows(db, sample)
    assert [r['level'] for r in rows] == ['program', 'subprogram', 'department']
    assert all(Decimal(r['amount']) == Decimal('133.60') for r in rows)
    assert all(r['complete'] for r in rows)
    assert all(r['source_amount'] is None and 'kaynak toplamı yok' in r['warnings'][0] for r in rows)
    # The next snapshot reflects edits, rather than a saved/cached subtotal.
    value = db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == 2,
                     ActivityCostValue.year == 2027, ActivityCostValue.funding_type == 'total'))
    value.amount = Decimal('0.20')
    db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == 2,
        ActivityCostValue.year == 2027, ActivityCostValue.funding_type == 'inside')).amount = Decimal('0.20')
    db.commit()
    assert all(Decimal(r['amount']) == Decimal('133.70') for r in current_rows(db, sample))


@pytest.mark.parametrize('missing', ['subprogram', 'card', 'catalogue', 'unattributed'])
def test_missing_link_never_shows_partial_programme_total(db, sample, missing):
    a = add_activity(db, sample)
    if missing in {'subprogram', 'unattributed'}: a.subprogram_id = None
    if missing in {'card', 'unattributed'}: a.card_id = None
    if missing in {'catalogue', 'unattributed'}:
        db.delete(db.scalar(select(ActivityCatalogueLink).where(ActivityCatalogueLink.activity_id == a.id)))
    db.commit()
    rows = current_rows(db, sample)
    assert rows and all(not r['complete'] and r['amount'] is None for r in rows)
    assert any('İkinci faaliyet' in error and 'tamamlayın' in error for r in rows for error in r['errors'])
    checks = publication_checks(db, 1)
    assert any(c['id'].startswith('subtotal:') and c['errors'] for c in checks)


def test_source_mismatch_blocks_and_matching_source_publishes(client, db, sample):
    prepare(db, sample)
    source(db, sample, '130')
    response = client.post('/report-builder/publish', data={'period_id': 1}, headers={'accept': 'application/json'}, follow_redirects=False)
    assert response.status_code == 422
    body = response.json()
    assert body['errors'][0]['field'] == 'publish'
    for text in ['Test Programı', '2027', '133,50', '130,00', '3,50', 'fark', 'karşılaştırın']:
        assert text in body['detail']
    assert db.scalar(select(func.count()).select_from(Publication)) == 0
    source(db, sample)
    assert all(Decimal(r['difference']) == 0 for r in current_rows(db, sample))
    response = client.post('/report-builder/publish', data={'period_id': 1}, follow_redirects=False)
    assert response.status_code == 303, response.text
    frozen = json.loads(db.scalar(select(Publication)).snapshot_json)['cost_reconciliation']
    assert frozen == reconciliation(db, sample)


def test_absent_source_is_warning_and_does_not_block(client, db, sample):
    prepare(db, sample)
    assert all(r['source_amount'] is None and r['warnings'] and not r['errors'] for r in current_rows(db, sample))
    assert client.post('/report-builder/publish', data={'period_id': 1}, follow_redirects=False).status_code == 303


def test_book_exports_subtotals_in_programme_subprogramme_department_order(db, sample):
    payload = book_snapshot(db, 1)
    word, _ = export_book(payload, 'docx')
    pdf, _ = export_book(payload, 'pdf')
    document = Document(io.BytesIO(word))
    text = '\n'.join(c.text for t in document.tables for row in t.rows for c in row.cells)
    pdftext = '\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    for output in [text, pdftext]:
        positions = [output.index(label) for label in [
            'Program ara toplamı: Test Programı', 'Alt program ara toplamı: Test Alt Programı',
            'Müdürlük ara toplamı: Test Müdürlüğü']]
        assert positions == sorted(positions)
        assert '133,50' in output and 'kaynak toplamı yok' in output


def test_reconciliation_screen_shows_turkish_problem_location_and_action(client, db, sample):
    prepare(db, sample); source(db, sample, '130')
    response = client.get('/report-builder?period_id=1')
    assert response.status_code == 200
    for text in ['Maliyet Ara Toplamları ve Kaynak Mutabakatı', 'Test Programı',
                 'Yayın engeli', '133,50', '130,00', '3,50', 'karşılaştırın']:
        assert text in response.text


@pytest.mark.parametrize('fund', ['inside', 'outside', 'total'])
def test_missing_amount_marks_each_parent_incomplete(db, sample, fund):
    value = db.scalar(select(ActivityCostValue).where(ActivityCostValue.year == 2027,
                                                    ActivityCostValue.funding_type == fund))
    value.amount = None; db.commit()
    assert all(r['amount'] is None and not r['complete'] and r['errors'] for r in current_rows(db, sample))


def test_partial_source_never_becomes_a_partial_parent_source(db, sample):
    source(db, sample, '130')
    add_activity(db, sample)
    assert all(r['source_amount'] is None and r['warnings'] and r['errors'] for r in current_rows(db, sample))


def test_opposite_source_mismatches_cannot_cancel(db, sample):
    source(db, sample, '133.40')
    a = add_activity(db, sample, '0.10')
    value = db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == a.id,
        ActivityCostValue.year == 2027, ActivityCostValue.funding_type == 'total'))
    value.source_amount = Decimal('0.20'); db.commit()
    assert all(Decimal(r['difference']) == 0 and r['errors'] for r in current_rows(db, sample))


def test_explicit_source_decision_and_reallocation_remain_traceable(db, sample):
    value = source(db, sample, '130')
    from app.program_service import save_activity_costs
    save_activity_costs(db, sample['activity'], 2027,
        {'cost_2027_budget_inside': '123,45', 'cost_2027_budget_outside': '10,05',
         'cost_2027_budget_use_computed': True, 'cost_2027_budget_reason': 'Kaynak hatası belgede doğrulandı.'},
         actor=sample['user'])
    db.commit()
    assert all(not r['errors'] and r['warnings'] and r['difference'] == '3.50' for r in current_rows(db, sample))
    # A separate approved reallocation adjustment also keeps the original source.
    value.source_resolution_json = '{"budget_reallocation_delta":"3.50"}'; db.commit()
    assert all(not r['errors'] and Decimal(r['source_amount']) == Decimal('130.00') for r in current_rows(db, sample))


def test_multiple_programmes_subprogrammes_and_departments_are_not_double_counted(db, sample):
    from app.models import Department, DepartmentScope
    p2 = Program(period_id=1, name='Başka Program'); db.add(p2); db.flush()
    sp2 = SubProgram(period_id=1, program_id=p2.id, name='Başka Alt Program'); db.add(sp2); db.flush()
    d2 = Department(organization_id=sample['department'].organization_id, name='İkinci Müdürlük')
    db.add(d2); db.flush(); db.add(DepartmentScope(period_id=1, department_id=d2.id, status='required'))
    card2 = ReportCard(period_id=1, department_id=d2.id, subprogram_id=sample['subprogram'].id)
    db.add(card2); db.flush()
    a2 = add_activity(db, sample, '0.10')
    a2.department_id = d2.id; a2.card_id = card2.id
    a3 = add_activity(db, sample, '0.20')
    card3 = ReportCard(period_id=1, department_id=1, subprogram_id=sp2.id); db.add(card3); db.flush()
    a3.subprogram_id = sp2.id; a3.card_id = card3.id; db.commit()
    rows = current_rows(db, sample)
    assert [Decimal(r['amount']) for r in rows if r['level'] == 'program'] == [Decimal('.20'), Decimal('133.60')]
    assert [Decimal(r['amount']) for r in rows if r['level'] == 'subprogram'] == [Decimal('.20'), Decimal('133.60')]
    assert sorted(Decimal(r['amount']) for r in rows if r['level'] == 'department') == [Decimal('.10'), Decimal('.20'), Decimal('133.50')]
    department_total = next(r for r in reconciliation(db, sample)
        if r['level'] == 'department_total' and r['department_id'] == 1 and r['year'] == 2027)
    assert Decimal(department_total['amount']) == Decimal('133.70')
    # An activity in a different period does not enter any current-period subtotal.
    p = ReportingPeriod(year=2030); db.add(p); db.flush()
    db.add(Activity(period_id=p.id, department_id=1, name='Diğer dönemin faaliyeti')); db.commit()
    assert current_rows(db, sample) == rows


@pytest.mark.parametrize('state', ['mismatch', 'missing_link'])
def test_turkish_reconciliation_in_chromium(client, db, sample, tmp_path, state):
    import os
    from pathlib import Path
    from playwright.sync_api import sync_playwright, expect
    prepare(db, sample)
    source(db, sample, '130')
    if state == 'missing_link':
        sample['activity'].subprogram_id = None; db.commit()
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        with pw.chromium.launch(**options) as browser, browser.new_page(viewport={'width': 1600, 'height': 1100}) as page:
            def serve(route):
                from urllib.parse import urlsplit
                url = urlsplit(route.request.url)
                response = client.get(url.path + ('?' + url.query if url.query else ''))
                route.fulfill(status=response.status_code, body=response.content,
                    headers={'content-type': response.headers.get('content-type', 'text/plain')})
            page.route('http://civensa.test/**', serve)
            page.goto('http://civensa.test/report-builder?period_id=1')
            view = page.locator('#pp-reconciliation')
            expect(view).to_be_visible()
            assert view.get_by_text('Yayın engeli', exact=True).count() == (12 if state == 'missing_link' else 4)
            if state == 'missing_link':
                assert view.get_by_text('Eksik ara toplam', exact=True).count() == 12
                view.locator('details').first.evaluate('el => el.open = true')
                assert 'bağlantıları tamamlayın' in view.inner_text()
            else:
                assert view.get_by_text('133,50', exact=True).count() == 12
                assert view.get_by_text('130,00', exact=True).count() == 4
                assert view.get_by_text('3,50', exact=True).count() == 4
                view.locator('details').first.evaluate('el => el.open = true')
                assert 'kaynakla karşılaştırın' in view.inner_text().lower()
            view.locator('details').first.evaluate('el => el.open = false')
            output = Path(os.getenv('CIVENSA_RECONCILIATION_SCREENSHOT_DIR', str(tmp_path)))
            output.mkdir(parents=True, exist_ok=True)
            view.screenshot(path=str(output / f'reconciliation-{state}.png'))
            page.set_viewport_size({'width': 390, 'height': 844})
            expect(view.get_by_role('heading')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')


def test_release_checklist_receives_the_same_subtotal_errors_and_warnings(db, sample):
    from app.release_service import release_checklist
    source(db, sample, '130')
    checklist = release_checklist(db, sample['period'], {}, 'test-version', {}, {})
    automatic = [c for c in checklist['automatic'] if c['id'].startswith('publication:subtotal:')]
    assert any(c['status'] == 'Engelli' and '3,50' in str(c['evidence']['errors']) for c in automatic)
    assert any('kaynak toplamı yok' in str(c['evidence']['warnings']) for c in automatic)
    assert [c['evidence']['observed'] for c in automatic] == reconciliation(db, sample)


def test_explicit_zero_and_absent_department_records_stay_distinct(db, sample):
    from app.models import Department, DepartmentScope
    for status in ['zero', 'required']:
        d = Department(organization_id=sample['department'].organization_id, name=f'Boş Müdürlük {status}')
        db.add(d); db.flush()
        db.add(DepartmentScope(period_id=1, department_id=d.id, status=status, reason='Açık kapsam kararı'))
    db.commit()
    rows = reconciliation(db, sample)
    zero = next(r for r in rows if r['label'].endswith('Boş Müdürlük zero'))
    missing = next(r for r in rows if r['label'].endswith('Boş Müdürlük required'))
    assert Decimal(zero['amount']) == 0 and zero['complete'] and not zero['errors']
    assert zero['source_amount'] is None and zero['warnings']
    assert missing['amount'] is None and not missing['complete'] and missing['errors']


def test_matching_zero_source_is_a_real_total(db, sample):
    source(db, sample, '0')
    for value in db.scalars(select(ActivityCostValue).where(ActivityCostValue.year == 2027)):
        value.amount = Decimal('0')
    db.commit()
    assert all(Decimal(r['amount']) == Decimal(r['source_amount']) == Decimal(r['difference']) == 0
               and r['status'] == 'Mutabık' for r in current_rows(db, sample))
