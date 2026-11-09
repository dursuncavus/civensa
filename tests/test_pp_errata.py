"""CIV-190: real 2026 book rows, FR projection and immutable PP provenance."""
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
import json
import os

from docx import Document
from pypdf import PdfReader
import pytest
from sqlalchemy import select

from app.data import pp_errata
from app.models import Department, ImportBatch, ARDocumentFreeze
from app.program_service import book_snapshot, approved_book_provenance, publication_checks
from app.import_service import _serialize_department_state
from app.activity_contract_service import digest
from app.serialization import json_dumps
from app import activity_sections_service as sections
from app.book_export import blocks, export_book
from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
from app.ar_pdf_export import build_activity_report_pdf
from test_approved_book_publication import approved_books, walk, period, publish
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def figure(payload, name, table='economic', year=2026):
    return next(row for row in payload['planned_figures']
                if name in row['department'] and row['table'] == table and row['year'] == year)


def stored_states(db, pid):
    return {did: json_dumps(_serialize_department_state(db, did, pid), sort_keys=True)
            for did in db.scalars(select(Department.id))}


def test_real_loaded_totals_and_provenance_unchanged(walk):
    db, _, _, _, _, _ = walk
    pid = period(db).id
    before = stored_states(db, pid)
    batch_hashes = list(db.execute(select(ImportBatch.id, ImportBatch.applied_hash).order_by(ImportBatch.id)))
    provenance = approved_book_provenance(db, pid)
    checks = publication_checks(db, pid)
    printed = book_snapshot(db, pid)
    printed_text = json_dumps(printed, sort_keys=True)
    fr = pp_errata.apply_pp_errata(printed)
    assert figure(fr, 'Bilgi İşlem')['amount'] == Decimal('176086246')
    assert figure(fr, 'Bilgi İşlem')['stored_amount'] == Decimal('176085750')
    assert figure(fr, 'Bilgi İşlem', 'cost')['amount'] == Decimal('176086246')
    # K2/K3 printed erroneous totals are absent from loaded cost rows. No entry.
    for name, expected in [('Çevre Koruma', '10841775'), ('İmar', '27702989')]:
        assert figure(fr, name, 'cost')['amount'] == Decimal(expected)
        assert not figure(fr, name, 'cost')['errata']
    assert figure(fr, 'Ruhsat')['amount'] == Decimal('11623833')
    assert not figure(fr, 'Ruhsat')['errata']
    for name in ('Zabıta', 'Veteriner'):
        row = figure(fr, name)
        assert row['amount'] is None and not row['errata']
        assert row['sources'] == {'inside': None, 'outside': None}
    assert figure(fr, 'Fen İşleri', year=2027)['stored_amount'] == Decimal('1290738800')
    assert figure(fr, 'Fen İşleri', year=2027)['amount'] == Decimal('1290738000')
    assert figure(fr, 'Fen İşleri', year=2028)['amount'] == Decimal('1677960440')
    assert not figure(fr, 'Fen İşleri', year=2028)['errata']
    assert fr['departments'] == printed['departments']  # No invented line split.
    assert json_dumps(printed, sort_keys=True) == printed_text
    db.flush()
    assert stored_states(db, pid) == before
    assert list(db.execute(select(ImportBatch.id, ImportBatch.applied_hash).order_by(ImportBatch.id))) == batch_hashes
    assert approved_book_provenance(db, pid) == provenance
    assert provenance['book_sha256'] == '1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6'
    assert publication_checks(db, pid) == checks  # PP publication gates stay printed.
    assert blocks(book_snapshot(db, pid)) == blocks(printed)


def test_absent_entries_mismatch_blank_and_other_year_change_nothing(walk, monkeypatch):
    db, *_ = walk
    printed = book_snapshot(db, period(db).id)
    entries = pp_errata.errata_entries(2026)
    assert {e['item_id'] for e in entries} == {'K1', 'K6'}
    monkeypatch.setattr(pp_errata, 'errata_entries', lambda year: [])
    plain = pp_errata.apply_pp_errata(printed)
    assert figure(plain, 'Bilgi İşlem')['amount'] == Decimal('176085750')
    assert all(not row['errata'] for row in plain['planned_figures'])
    monkeypatch.undo()
    for value in (None, '1.00'):
        changed = deepcopy(printed)
        dep = next(d for d in changed['departments'] if 'Bilgi İşlem' in d['department'])
        row = next(r for r in dep['economics'] if r['year'] == 2026)
        row['amount'] = value
        result = figure(pp_errata.apply_pp_errata(changed), 'Bilgi İşlem')
        assert not result['errata'] and 'BELİRSİZ' in result['errata_warning']
        if value is None:assert result['amount'] is None
    incomplete = deepcopy(printed)
    dep = next(d for d in incomplete['departments'] if 'Bilgi İşlem' in d['department'])
    dep['activities'][0]['costs'] = [r for r in dep['activities'][0]['costs']
                                    if not (r['year'] == 2026 and r['funding_type'] == 'total')]
    assert figure(pp_errata.apply_pp_errata(incomplete), 'Bilgi İşlem', 'cost')['amount'] is None
    other = pp_errata.apply_pp_errata(book_snapshot(db, period(db, 2027).id))
    assert all(not row['errata'] for row in other['planned_figures'])
    changed = deepcopy(printed)
    dep = next(d for d in changed['departments'] if 'Fen İşleri' in d['department'])
    for row in dep['economics']:row['source_context_json'] = '{}'
    result = figure(pp_errata.apply_pp_errata(changed), 'Fen İşleri', year=2027)
    assert result['amount'] == Decimal('1290738800') and 'BELİRSİZ' in result['errata_warning']


def create_fr(walk):
    db, client, strategy, _, _, token = walk
    p = period(db)
    assert publish(client, token, p.id).status_code == 303
    org = db.scalar(select(Department.organization_id).limit(1))
    docs = sections.create_year(db, strategy, org, p.id)
    db.flush()
    return docs


def test_fr_unit_idare_export_and_retained_snapshot(walk):
    db, client, strategy, _, _, _ = walk
    docs = create_fr(walk)
    for doc in [d for d in docs if d.department_id is None or
                'Bilgi İşlem' in db.get(Department, d.department_id).name]:
        data = sections.report_data(db, strategy, doc.id)
        planned = data['financial']['pp_planned_figures']
        row = next(r for r in planned if 'Bilgi İşlem' in r['department'] and r['year'] == 2026 and r['table'] == 'economic')
        assert row['amount'] == Decimal('176086246') and row['errata'][0]['item_id'] == 'K1'
        if doc.department_id:assert {r['department_id'] for r in planned} == {doc.department_id}
        page = client.get(f'/activity-sections/reports/{doc.id}?code=III.A.1')
        assert page.status_code == 200
        assert 'Düzeltildi (K1, s.243)' in page.text and '176.086.246' in page.text
        assert 'Basılı: 176.085.750' in page.text
        # Keep the export regression focused on the financial section.
        data['sections'] = [s for s in data['sections'] if s['code'] == 'III.A.1']
        word = build_activity_report_docx(data, TEMPLATE_PATH)
        text = '\n'.join(c.text for t in Document(BytesIO(word)).tables for r in t.rows for c in r.cells)
        assert '176.086.246,00' in text and 'Düzeltildi (K1, s.243)' in text
        pdf = build_activity_report_pdf(data)
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
        assert '176.086.246,00' in text and 'Düzeltildi (K1, s.243)' in text
    # A retained FR is immutable: its approved facts/bytes are never re-projected.
    idare = next(d for d in docs if d.department_id is None)
    data = sections.report_data(db, strategy, idare.id)
    raw = sections.numeric_canonical(data)
    retained = ARDocumentFreeze(document_id=idare.id, payload_json=raw, sha256=digest(raw), created_by=strategy.id)
    db.add(retained);db.flush()
    assert sections.report_data(db, strategy, idare.id)['financial']['pp_planned_figures'] == json.loads(raw, parse_float=Decimal)['financial']['pp_planned_figures']
    assert retained.payload_json == raw and digest(raw) == retained.sha256


def test_pp_exports_keep_printed_lines(walk):
    db, *_ = walk
    payload = book_snapshot(db, period(db).id)
    payload['departments'] = [d for d in payload['departments'] if 'Bilgi İşlem' in d['department']]
    payload.update(economics=[], program_costs=[], cost_reconciliation=[], sections=[], catalogue=[])
    before = deepcopy(payload)
    pp_errata.apply_pp_errata(payload)
    assert payload == before
    for fmt in ('docx', 'pdf'):
        output, _ = export_book(payload, fmt)
        if fmt == 'docx':
            doc = Document(BytesIO(output))
            text = '\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
        else:text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(output)).pages)
        # The 2026 economic printed goods/services line is unchanged.
        dep = payload['departments'][0]
        printed = next(r['raw_text'] for r in dep['economics'] if r['year'] == 2026 and r['category'] == 'goods_services' and r['funding_type'] == 'inside')
        assert printed in text
        assert 'Düzeltildi' not in text


def test_strategy_readonly_list_and_fr_marker_in_browser(walk, browser):
    db, client, strategy, _, _, _ = walk
    docs = create_fr(walk)
    doc = next(d for d in docs if d.department_id and 'Bilgi İşlem' in db.get(Department, d.department_id).name)
    with browser.new_context(viewport={'width':1440, 'height':1000}) as context:
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=False)
            headers = dict(response.headers);headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(f'http://testserver/report-builder?period_id={period(db).id}')
        block = page.get_by_role('region', name='Basılı kitap düzeltmeleri (2026)')
        assert block.count() == 1
        assert '176.085.750,00' in block.inner_text() and '176.086.246,00' in block.inner_text()
        assert '1.290.738.000,00' in block.inner_text()
        assert 'Dr. Ali KAYA' in block.inner_text()
        assert block.locator('input,button,form,select,textarea').count() == 0
        if os.getenv('CIV190_SCREENSHOTS'):
            block.screenshot(path='docs/reports/civ-190/strateji.png')
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}?code=III.A.1')
        marker = page.get_by_text('Düzeltildi (K1, s.243)', exact=True)
        assert marker.count() == 1 and '176.085.750' in marker.get_attribute('title')
        if os.getenv('CIV190_SCREENSHOTS'):
            page.get_by_role('region', name='PP planlanan tutarlar').screenshot(path='docs/reports/civ-190/fr-marker.png')
