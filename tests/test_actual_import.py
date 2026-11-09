"""CIV-192: only synthetic workbooks and disposable PostgreSQL."""
import io
import json
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from fastapi import HTTPException
from openpyxl import Workbook
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette.datastructures import FormData
from app import actual_import_service as imp, activity_contract_service as contract, structure_service
from app.models import (ActualRevision, ActualImport, AuditLog, Indicator, IndicatorValue,
    IndicatorDefinitionRevision, Department, DepartmentScope, Submission, Publication,
    ReportCandidate, StructureChangeCancellation)
from app.main import app, require_user
from tests.test_activity_contract import new_report, actual_payload

pytestmark = pytest.mark.postgres

# Same 24-column layout as the task; values are entirely invented.
HEADERS = ['Ana Hizmet Alanı', 'Alan kodu', 'Stratejik Hedef', 'SH kodu', 'Sorumlu Müdürlük',
    'PG kodu', 'Gösterge Adı', 'Hesaplama Yöntemi', 'Birim', 'Hedef etkisi', '2025 Hedef',
    '2025 Gerçekleşen', '2026 Hedef', '2026 Q1', '2026 Q2', '2026 Q3', '2026 Q4',
    'Q4 Gerçekleşen Toplamı', '2026 YILI TOPLAMI', 'Değerlendirme 1', 'Değerlendirme 2',
    'Değerlendirme 3', 'Değerlendirme 4', 'Açıklama']


@pytest.fixture
def db(postgres_templates):
    # Use real migrated search_path so workflow ownership guards inspect exactly
    # the same schema as the application's SQL, including candidate/release tables.
    with postgres_templates.clone('head') as engine:
        with Session(engine, expire_on_commit=False) as session:
            yield session


def workbook(rows, headers=None, reverse=False):
    book = Workbook(); sheet = book.active; sheet.title = 'veriler'
    sheet.append(list(reversed(headers or HEADERS)) if reverse else (headers or HEADERS))
    for row in rows:
        values = ['', '', '', 'SH1', row.get('department', 'Test Müdürlüğü'), 'PG1', row['name'],
            row.get('method', 'TOPLA'), row.get('unit', 'Adet'), '', '', '', '',
            *row.get('q', [1, 2, 3, 4]), '', row.get('annual'), '', '', '', '', row.get('explanation', 'Sentetik açıklama')]
        sheet.append(list(reversed(values)) if reverse else values)
    book.create_sheet('ANALİZ').append(['Bu sayfa yok sayılır', 999])
    data = io.BytesIO(); book.save(data); return data.getvalue()


@pytest.fixture
def scenario(client, db, sample):
    sample['period'].year = 2026
    db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == sample['indicator'].id)).year = 2026
    names = [('Tamamlanan eğitim sayısı', 'Adet'), ('Memnuniyet oranı', '%'),
             ('Belirsiz oran', 'Puan'), ('Eksik hizmet sayısı', 'Adet'), ('Kanıtsız sayı', 'Adet')]
    for name, unit in names:
        row = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
            subprogram_id=sample['subprogram'].id, card_id=sample['card'].id, name=name, unit=unit)
        db.add(row); db.flush()
        db.add(IndicatorValue(indicator_id=row.id, year=2026, value_kind='target', value=50))
    db.commit()
    from app.program_service import book_snapshot
    raw = contract.canonical(book_snapshot(db, sample['period'].id))
    pub = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw,
        sha256=contract.digest(raw), created_by=sample['strategy'].id)
    db.add(pub); db.flush()
    for indicator in db.scalars(select(Indicator)):
        contract.bind_legacy_indicator(db, sample['strategy'], pub.id, indicator.id, None, 'Sentetik test yayını')
    db.commit()
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    report = new_report(client, pub, sample)
    for indicator in report['indicators']:
        if indicator['definition']['name'] != 'Kanıtsız sayı':
            contract.save_actual(db, sample['strategy'], indicator['report_indicator_id'], **actual_payload(value='7'))
    db.commit()
    return report


def preview(db, sample, scenario, rows, **kwargs):
    record = imp.preview_import(db, sample['strategy'], scenario['revision_id'], workbook(rows, **kwargs))
    db.commit()
    return record, json.loads(record.preview_json)


def confirmed(p, selection=None):
    result = {}
    for row in p['rows']:
        if row['options'] and row['status'] not in {'Hata', 'Eksik', 'Eşleşmedi'}:
            o = row['options'][0]
            result[str(row['line'])] = {'indicator_id': o['id'], 'scale': selection or o['scale'], 'confirmed': True}
    return result


def apply(db, sample, record, p, choices=None):
    result = imp.apply_import(db, sample['strategy'], record.id, p['expected_revision'],
        confirmed(p) if choices is None else choices)
    db.commit(); return result


def test_matching_annual_rules_and_no_preview_writes(client, db, sample, scenario):
    count = db.scalar(select(func.count()).select_from(ActualRevision))
    record, p = preview(db, sample, scenario, [
        {'name': 'PG 4.2: HİZMET SAYISI', 'q': [1, 2, 3, 4]},
        {'name': 'Tamamlanan eğitimlerin sayısı', 'method': 'kÜMÜLATİF', 'q': [1, 2, 3, 12]},
        {'name': 'Zzzzz bambaşka kayıt'},
        {'name': 'Hizmet sayısı', 'annual': 20},
        {'name': 'Eksik hizmet sayısı', 'q': [1, 2, 3, None]},
        {'name': 'Kanıtsız sayı', 'annual': 13},
    ], reverse=True)
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == count
    assert [r['status'] for r in p['rows']] == ['Eşleşti', 'Onay gerekiyor', 'Eşleşmedi', 'Hata', 'Eksik', 'Eşleşti']
    assert p['rows'][0]['raw_value'] == '10'
    assert p['rows'][1]['raw_value'] == '12'
    assert len(p['rows'][1]['options']) <= 3
    definitions = list(db.execute(select(IndicatorDefinitionRevision.id, IndicatorDefinitionRevision.definition_json)))
    targets = list(db.execute(select(IndicatorValue.id, IndicatorValue.value)))
    names = list(db.execute(select(Indicator.id, Indicator.name, Indicator.unit)))
    pub = db.get(Publication, scenario['publication_id']); original = pub.snapshot_json
    evidence = db.scalar(select(ActualRevision).order_by(ActualRevision.id)).evidence_json
    result = apply(db, sample, record, p)
    assert result['counts'] == {'Yazıldı': 2, 'Eşleşmedi': 1, 'Hata': 2, 'Eksik': 1}
    assert 'kaynak bulunmuyor' in result['rows'][5]['message']
    assert list(db.execute(select(IndicatorDefinitionRevision.id, IndicatorDefinitionRevision.definition_json))) == definitions
    assert list(db.execute(select(IndicatorValue.id, IndicatorValue.value))) == targets
    assert list(db.execute(select(Indicator.id, Indicator.name, Indicator.unit))) == names
    assert pub.snapshot_json == original
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).evidence_json == evidence
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == count + 2
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'actual_import_apply'))
    assert json.loads(audit.details)['sha256'] == record.source_sha256
    assert len(json.loads(audit.details)['row_ids_written']) == 2
    assert apply(db, sample, record, p) == result
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'actual_import_apply')) == 1
    again, p2 = preview(db, sample, scenario, [{'name': 'Hizmet sayısı', 'q': [1, 2, 3, 4]}])
    assert p2['rows'][0]['status'] == 'Değişmedi'
    assert apply(db, sample, again, p2)['counts'] == {'Değişmedi': 1}


def test_scale_requires_confirmation_and_shows_both_readings(client, db, sample, scenario):
    record, p = preview(db, sample, scenario, [{'name': 'Memnuniyet oranı', 'unit': 'Oran (%)', 'annual': 1},
        {'name': 'Belirsiz oran', 'unit': 'Oran', 'annual': .25}])
    assert [r['status'] for r in p['rows']] == ['Onay gerekiyor', 'Onay gerekiyor']
    assert p['rows'][0]['options'][0]['percent_value'] == '100'
    assert p['rows'][1]['options'][0]['scale'] == 'choose'
    response = client.get(f'/activity-reports/imports/{record.id}')
    assert response.status_code == 200, response.text
    assert '×100 (oran kesirden yüzdeye)' in response.text
    assert '0,25' in response.text and '25' in response.text
    count = db.scalar(select(func.count()).select_from(ActualRevision))
    assert apply(db, sample, record, p, {})['counts'] == {'Aktarılmadı': 2}
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == count
    record, p = preview(db, sample, scenario, [{'name': 'Memnuniyet oranı', 'unit': 'Oran', 'annual': 1}])
    bad = confirmed(p, 'raw')
    with pytest.raises(HTTPException, match='ölçeği'):
        imp.apply_import(db, sample['strategy'], record.id, p['expected_revision'], bad)
    db.rollback()
    assert apply(db, sample, record, p)['counts'] == {'Yazıldı': 1}
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == 100


def test_structure_rename_and_merge(client, db, sample, scenario):
    dep = sample['department']
    renamed = structure_service.save_change(db, sample['strategy'], FormData({
        'organization_id': str(dep.organization_id), 'period_id': str(sample['period'].id),
        'change_type': 'RENAMED', 'effective_date': '2026-02-01', 'council_decision_date': '2026-01-01',
        'council_decision_no': 'SENTETIK-1', 'from_department_ids': str(dep.id), 'new_name': 'Yeni Test Müdürlüğü'}))
    old = Department(organization_id=dep.organization_id, name='Birleşen Test Müdürlüğü'); db.add(old); db.flush()
    structure_service.save_change(db, sample['strategy'], FormData({
        'organization_id': str(dep.organization_id), 'period_id': str(sample['period'].id),
        'change_type': 'MERGED', 'effective_date': '2026-03-01', 'council_decision_date': '2026-01-01',
        'council_decision_no': 'SENTETIK-2', 'from_department_ids': str(old.id), 'to_department_ids': str(dep.id)}))
    db.commit()
    _, p = preview(db, sample, scenario, [{'name': 'Hizmet sayısı', 'department': 'Yeni Test Müdürlüğü'},
        {'name': 'Tamamlanan eğitim sayısı', 'department': old.name}])
    assert [r['status'] for r in p['rows']] == ['Eşleşti', 'Eşleşti']
    assert p['rows'][0]['options'][0]['department'] == 'Test Müdürlüğü'
    assert renamed.id


def test_missing_text_zero_annual_precedence_and_cumulative_variants(client, db, sample, scenario):
    for source, expected, rule in [
        ({'annual': 0, 'method': 'TOPLA', 'q': [1,2,3,None]}, Decimal(0), '2026 YILI TOPLAMI'),
        ({'annual': '%', 'method': 'T.KÜMÜLATİF', 'q': [1,2,3,9]}, Decimal(9), 'KÜMÜLATİF: Q4'),
        ({'method': 'TOPLA', 'q': [1,2,'%',4]}, None, None),
        ({'method': 'kÜMÜLATİF', 'q': [1,2,3,None]}, None, None),
    ]:
        parsed = imp.read_rows(workbook([{'name':'Hizmet sayısı', **source}]))[0][1]
        value, chosen = imp.annual_value(parsed)
        assert value == expected
        if rule: assert chosen == rule
    record, p = preview(db, sample, scenario, [{'name': 'Eksik hizmet sayısı', 'q': [1,2,3,None]}])
    before = db.scalar(select(func.count()).select_from(ActualRevision))
    assert apply(db, sample, record, p)['counts'] == {'Eksik': 1}
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == before


def test_refusal_stale_and_duplicate_selected_claim(client, db, sample, scenario):
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı'}, {'name':'Hizmet sayıları'}])
    result = apply(db, sample, record, p)
    assert result['counts'] == {'Yazıldı': 1, 'Hata': 1}
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'annual': 42}])
    slot = p['rows'][0]['options'][0]['id']
    contract.save_actual(db, sample['strategy'], slot, **actual_payload(expected_revision=2, value='31'))
    db.commit()
    result = apply(db, sample, record, p)
    assert result['counts'] == {'Hata': 1}
    assert 'başka bir kullanıcı' in result['rows'][0]['message']
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'annual': 44}])
    # A real approved revision triggers save_actual's workflow refusal.
    from app.models import ActivityReportApproval
    db.add(ActivityReportApproval(report_revision_id=scenario['revision_id'], created_by=sample['strategy'].id)); db.commit()
    result = apply(db, sample, record, p)
    assert result['counts'] == {'Hata': 1}
    assert 'Onaylı rapor' in result['rows'][0]['message']


def test_headers_expiry_and_non_strategy_403(client, db, sample, scenario):
    with pytest.raises(HTTPException, match='Gösterge Adı'):
        imp.preview_import(db, sample['strategy'], scenario['revision_id'], workbook([], headers=[h for h in HEADERS if h != 'Gösterge Adı']))
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı'}])
    record.created_at = datetime.now() - timedelta(hours=25); db.commit()
    assert client.get(f'/activity-reports/imports/{record.id}').status_code == 410
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert client.get(f'/activity-reports/imports/{record.id}').status_code == 403
    assert client.post('/activity-reports/imports/preview', files={'file':('synthetic.xlsx', workbook([]))},
        data={'revision_id': scenario['revision_id']}).status_code == 403
    assert client.post(f'/activity-reports/imports/{record.id}/apply', data={'expected_revision':1}).status_code == 403
    assert "Excel'den içe aktar" not in client.get('/activity-reports').text


def test_close_match_is_not_written_without_selection(client, db, sample, scenario):
    record, p = preview(db, sample, scenario, [{'name':'Tamamlanan eğitimlerin sayısı'}])
    assert p['rows'][0]['status'] == 'Onay gerekiyor'
    count = db.scalar(select(func.count()).select_from(ActualRevision))
    assert apply(db, sample, record, p, {})['counts'] == {'Aktarılmadı': 1}
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == count


def test_same_pg_code_cannot_cross_directorates(client, db, sample, scenario):
    # Every fixture row has PG1; neither an unknown directorate nor a PG code is a key.
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'department':'Bilinmeyen Müdürlük'}])
    assert p['rows'][0]['status'] == 'Eşleşmedi'
    assert apply(db, sample, record, p)['counts'] == {'Eşleşmedi': 1}


@pytest.mark.parametrize('prefix', ['SH.1.2 / PG.1.3: ', 'P.G.2.1 — '])
def test_punctuated_leading_codes_still_match_by_name(client, db, sample, scenario, prefix):
    _, p = preview(db, sample, scenario, [{'name': prefix + 'HİZMET SAYISI'}])
    assert p['rows'][0]['status'] == 'Eşleşti'
    assert p['rows'][0]['options'][0]['name'] == 'Hizmet sayısı'


def test_browser_upload_confirm_apply(client, db, sample, scenario, tmp_path):
    import os
    from pathlib import Path
    from playwright.sync_api import sync_playwright, expect
    from scripts.guide_screenshots import local_http
    from app.db import get_db
    original_db = app.dependency_overrides[get_db]
    data = {'rehearsal': True, 'accounts': {'strategy': 'synthetic@example.invalid'}, '_server_errors': []}
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    rows = [{'name':'Hizmet sayısı'}, {'name':'Memnuniyet oranı', 'unit':'Oran (%)', 'annual':.8},
        {'name':'Tamamlanan eğitimlerin sayısı', 'method':'T.KÜMÜLATİF', 'q':[1,2,3,12]},
        {'name':'Eksik hizmet sayısı', 'q':[1,2,3,None]}, {'name':'Kanıtsız sayı', 'annual':13}]
    try:
        with local_http(db.get_bind(), data) as base, sync_playwright() as pw:
            options = {'headless':True}
            if os.getenv('CIVENSA_CHROMIUM_PATH'):
                options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
            browser = pw.chromium.launch(**options)
            page = browser.new_page(viewport={'width':1920, 'height':1080}, extra_http_headers={'X-Guide-Account':'strategy'})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base + '/activity-reports')
            page.select_option('select[name=revision_id]', str(scenario['revision_id']))
            page.set_input_files('input[name=file]', {'name':'synthetic.xlsx', 'mimeType':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer':workbook(rows)})
            page.get_by_role('button', name='Excel önizlemesini aç').click()
            expect(page.get_by_role('heading', name='Excel önizlemesi')).to_be_visible()
            assert page.locator('select[name=choice_3]').input_value() == ''
            output = Path(os.environ['CIV192_SCREENSHOTS']) if os.getenv('CIV192_SCREENSHOTS') else tmp_path
            output.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output/'preview.png'), full_page=True)
            for line in (2,3,4,6):
                select = page.locator(f'select[name=choice_{line}]')
                choice = select.locator('option').nth(1).get_attribute('value')
                select.select_option(choice)
            page.get_by_role('button', name='Onaylanan satırları uygula').click()
            expect(page.get_by_role('heading', name='İçe aktarma sonucu')).to_be_visible()
            assert 'Yazıldı: 3' in page.locator('main').inner_text()
            assert 'kaynak bulunmuyor' in page.locator('main').inner_text()
            page.screenshot(path=str(output/'result.png'), full_page=True)
            assert not errors and not data['_server_errors']
            browser.close()
    finally:
        app.dependency_overrides[get_db] = original_db


def test_cancelled_structure_alias_is_not_used(client, db, sample, scenario):
    dep = sample['department']
    change = structure_service.save_change(db, sample['strategy'], FormData({
        'organization_id': str(dep.organization_id), 'period_id': str(sample['period'].id),
        'change_type': 'RENAMED', 'effective_date': '2026-02-01', 'council_decision_date': '2026-01-01',
        'council_decision_no': 'SENTETIK-3', 'from_department_ids': str(dep.id), 'new_name': 'İptal Edilen Ad'}))
    db.flush()
    structure_service.cancel_change(db, sample['strategy'], change.id, 'Sentetik iptal')
    db.commit()
    _, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'department':'İptal Edilen Ad'}])
    assert p['rows'][0]['status'] == 'Eşleşmedi'


@pytest.mark.parametrize('scale,expected', [('raw', Decimal('.25')), ('percent', Decimal('25'))])
def test_ambiguous_scale_uses_only_selected_reading(client, db, sample, scenario, scale, expected):
    record, p = preview(db, sample, scenario, [{'name':'Belirsiz oran', 'unit':'Oran', 'annual':.25}])
    assert p['rows'][0]['options'][0]['scale'] == 'choose'
    assert apply(db, sample, record, p, confirmed(p, scale))['counts'] == {'Yazıldı':1}
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == expected


def test_uncached_formula_is_not_evaluated(client, db, sample, scenario):
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'annual':'=SUM(N2:Q2)', 'q':[1,2,3,None]}])
    assert p['rows'][0]['status'] == 'Eksik'
    assert apply(db, sample, record, p)['counts'] == {'Eksik':1}


def test_candidate_owned_report_stays_closed(client, db, sample, scenario):
    from app.report_workflow_service import hash_content
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'annual':43}])
    candidate = ReportCandidate(organization_id=sample['department'].organization_id,
        period_id=sample['period'].id, resource_scope='activity_report', report_key=str(scenario['report_id']),
        sequence=1, activity_revision_id=scenario['revision_id'], payload_json='{}', payload_sha256=contract.digest('{}'),
        manifest_json='{}', sha256=hash_content('{}', '{}'), created_by=sample['strategy'].id)
    # Ownership must already prevent writes inside the candidate's transaction;
    # the minimal candidate is rolled back before deferred completeness checks.
    db.add(candidate); db.flush()
    before = db.scalar(select(func.count()).select_from(ActualRevision))
    result = imp.apply_import(db, sample['strategy'], record.id, p['expected_revision'], confirmed(p))
    assert result['counts'] == {'Hata':1}
    assert 'nihai rapor adayına bağlı' in result['rows'][0]['message']
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == before
    db.rollback()
