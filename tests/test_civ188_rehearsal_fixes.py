"""CIV-188: finance warnings, deviation gate, and saved summary parity."""
import pytest
from sqlalchemy import select

from app.models import ARSectionContent
from app import activity_sections_service as sections
from ar_unit_workflow_helpers import ready_unit, approve_sources
from test_activity_sections import section_client, login
from test_ar_deviation_gate import deviation_report, save_actual, submit
from test_unsaved_drafts_ui import editor, saved
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def open_finance(db, doc, status='empty', reason=''):
    for definition in sections.definitions(db, doc):
        if sections.owner(definition, doc) == 'finance':
            content = db.scalar(select(ARSectionContent).where(
                ARSectionContent.document_id == doc.id,
                ARSectionContent.definition_id == definition.id))
            content.status, content.reason = status, reason
    db.commit()


@pytest.mark.parametrize('status', ['empty', 'draft'])
def test_open_finance_warns_but_deviation_still_blocks(deviation_report, db, sample, status):
    create, _ = deviation_report
    client, doc, report, token = create()
    slot = report['indicators'][0]['report_indicator_id']
    save_actual(client, token, slot)
    ready_unit(db, doc, sample['user'])
    open_finance(db, doc, status)
    response = submit(client, token, doc)
    assert response.status_code == 409
    assert 'hedef farkı açıklaması eksik: Hizmet sayısı' in response.json()['message']
    report_page = client.get(f'/activity-sections/reports/{doc.id}?code=III.A.1')
    assert 'Uyarılar (gönderimi engellemez)' in report_page.text
    payload = sections.report_data(db, sample['user'], doc.id)
    finance = [s for s in payload['sections'] if s['owner'] == 'finance']
    assert finance and all(not s['missing'] and s['warnings'] for s in finance)
    save_actual(client, token, slot, expected_revision=1, explanation='SENTETİK: hizmet artışı doğrulandı.')
    response = submit(client, token, doc)
    assert response.status_code == 200, response.text


def test_finance_not_applicable_still_requires_reason():
    from app.ar_unit_workflow_service import completeness
    payload = {'department_id': 1, 'sections': [{'owner': 'finance',
        'title': 'Malî Bilgiler', 'status': 'not_applicable', 'reason': ' ', 'missing': []}]}
    assert completeness(payload) == ['Malî Bilgiler']
    payload['sections'][0]['reason'] = 'SENTETİK: mali olay yok.'
    assert completeness(payload) == []
    payload['sections'][0]['missing'] = ['Kaynak eksik']
    assert completeness(payload) == ['Malî Bilgiler']


def test_idare_finance_status_still_blocks_freeze(section_client, db, sample):
    client, docs, _, _ = section_client
    idare = docs['idare']
    approve_sources(db, idare)
    open_finance(db, idare)
    token = login(client, sample['strategy'].email)
    response = client.post(f'/api/activity-sections/reports/{idare.id}/freeze',
        json={'expected_revision': idare.revision}, headers={'X-CSRF-Token': token})
    assert response.status_code == 409
    assert response.json()['errors'][0]['field'] == 'sections'
    assert 'Malî Bilgiler' in response.json()['detail']


@pytest.mark.parametrize('editor', ['ar'], indirect=True)
def test_ajax_summary_matches_reload_for_each_state(editor):
    from playwright.sync_api import expect
    page = editor.page
    record = editor.records[0]
    summary = page.locator('.indicator-report-summary')
    expect(summary).to_contain_text('2 Kayıt yok')
    for state, label in [('missing', 'Eksik'), ('needs_review', 'İncelenmeli'), ('verified', 'Doğrulanmış')]:
        record.locator(editor.field).fill('12,5' if state != 'missing' else '')
        record.locator('[name=state]').select_option(state)
        editor.save(record)
        saved(record)
        expect(summary).to_contain_text('1 ' + label)
        expect(summary).to_contain_text('1 Kayıt yok')
        if state == 'verified':
            expect(summary).to_contain_text('1 açıklama bekliyor')
        counts = summary.inner_text()
        page.reload()
        expect(summary).to_have_text(counts)
    record.locator(editor.explanation).fill('SENTETİK: hizmet artışı doğrulandı.')
    editor.save(record)
    saved(record)
    expect(summary).not_to_contain_text('açıklama bekliyor')
    counts = summary.inner_text()
    page.reload()
    expect(summary).to_have_text(counts)


@pytest.mark.parametrize('kind', ['unverified', 'absent', 'zero'])
def test_target_guidance_preserves_raw_text_and_zero(deviation_report, db, sample, kind):
    from app.models import IndicatorValue
    target = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == sample['indicator'].id))
    if kind == 'absent':
        db.delete(target)
    elif kind == 'unverified':
        target.state = 'needs_review'
        target.value = None
        target.raw_text = '<script>Her yıl & artış</script>'
    else:
        target.value = 0
    db.commit()
    create, _ = deviation_report
    client, _, report, token = create()
    url = f"/activity-reports/revisions/{report['revision_id']}"
    for has_actual in (False, True):
        if has_actual:
            slot = report['indicators'][0]['report_indicator_id']
            save_actual(client, token, slot)
        page = client.get(url)
        if kind == 'zero':
            assert 'Hedef: 0' in page.text
            assert 'data-unverified-target' not in page.text
        else:
            assert 'data-unverified-target' in page.text
            assert 'Fark hesaplanmaz; Strateji' in page.text
            if kind == 'unverified':
                assert 'Basılı hedef metni: &lt;script&gt;Her yıl &amp; artış&lt;/script&gt;' in page.text
                assert '<script>Her yıl' not in page.text
            else:
                assert 'Hedef kaydı yok.' in page.text
