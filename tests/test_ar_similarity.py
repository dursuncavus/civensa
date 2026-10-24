"""CIV-088: approved-only, non-blocking narrative advice and export isolation."""
import copy
import json
from datetime import datetime, UTC
from unittest.mock import patch

import pytest
from lxml import html
from sqlalchemy import select, update

from app import activity_sections_service as sections, ar_similarity as similarity
from app.models import (ARDocument, ARDocumentFreeze, ARUnitWorkflowEvent, ReportingPeriod,
                        DepartmentScope, Organization)
from test_activity_sections import section_client, login, save, ready_and_freeze
from test_ar_release_chain import reopen, freeze, downloads
from ar_unit_workflow_helpers import ready_unit, approve_unit

pytestmark = pytest.mark.postgres

# Distinct words without digits (which intentionally normalize to the same token).
WORDS = ['kelime' + chr(97 + i // 26) + chr(97 + i % 26) for i in range(40)]
TEXT = ' '.join(WORDS)


def narrative(text=TEXT, code='I.A', **kwargs):
    return {'code': code, 'content_kind': 'narrative',
            'blocks': [{'type': 'paragraph', 'text': text}], **kwargs}


def baseline(section=None, **kwargs):
    return {'year': 2026, 'message': '', 'sections': {'I.A': section or narrative()},
            'source_url': '/approved.json', 'source_label': 'Sürüm 2', **kwargs}


def prior_document(db, sample, doc, year=2026, organization_id=None):
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
    if not period:
        period = ReportingPeriod(year=year, status='active')
        db.add(period); db.flush()
    prior = db.scalar(select(ARDocument).where(ARDocument.period_id == period.id,
        ARDocument.organization_id == (organization_id or doc.organization_id), ARDocument.scope == doc.scope))
    if not prior:
        prior = ARDocument(organization_id=organization_id or doc.organization_id, period_id=period.id,
            department_id=doc.department_id, scope=doc.scope, definition_version=doc.definition_version,
            revision=0, created_by=sample['strategy'].id)
        db.add(prior); db.flush()
    return prior


def store_baseline(db, sample, doc, text=TEXT, version=1, kind=None, tampered=False, payload=None, **kwargs):
    prior = prior_document(db, sample, doc, **kwargs)
    if payload is None:
        payload = sections.report_data(db, sample['strategy'], doc.id)
        payload.update(id=prior.id, period_id=prior.period_id,
                       year=db.get(ReportingPeriod, prior.period_id).year, revision=version)
        for s in payload['sections']:
            if s['code'] in {'I.A', 'I.B'}:
                s['blocks'] = [{'type': 'paragraph', 'text': text}]
    raw = sections.numeric_canonical(payload)
    sha = '0' * 64 if tampered else sections.digest(raw)
    kind = kind or ('approval' if doc.department_id else 'freeze')
    if kind == 'freeze':
        record = ARDocumentFreeze(document_id=prior.id, version=version, payload_json=raw,
                                  sha256=sha, created_by=sample['strategy'].id)
    else:
        record = ARUnitWorkflowEvent(document_id=prior.id, revision=version,
            action='approve' if kind == 'approval' else 'submit', from_status='submitted' if kind == 'approval' else 'draft',
            to_status='approved' if kind == 'approval' else 'submitted', actor_id=sample['strategy'].id,
            actor_name='Strateji', created_at=datetime.now(UTC), payload_json=raw, sha256=sha)
    db.add(record); db.commit()
    return record


def own_report(docs, sample):
    return docs[f"birim:{sample['department'].id}"]


def test_above_threshold_year_percent_and_exact_threshold():
    result = similarity.compare_section(narrative(' '.join(WORDS[:35] + ['yeni'] * 5)), baseline())
    assert result['percent'] == 88
    assert result['message'] == ('Bu bölüm 2026 yılı onaylı raporundaki aynı bölümle %88 benzer. '
                                 'Metni bu yılın gelişmelerine göre güncelleyin.')
    assert result['source_url'] == '/approved.json'
    exact = similarity.compare_section(narrative(' '.join(WORDS[:34] + ['yeni'] * 6)), baseline())
    assert exact['percent'] == 85 and exact['message'] == ''
    # Rounding to 85 must not suppress a ratio that is strictly greater than 85.
    almost = ' '.join(WORDS + ['farklı'] * 14)
    assert similarity.compare_section(narrative(almost), baseline())['message']


def test_turkish_case_punctuation_numbers_lists_and_tables():
    before = narrative(TEXT + ' İSTANBUL IĞDIR İŞÇİ 12.500,23 2026')
    after = narrative(TEXT + ' istanbul ığdır işçi 99,5 2027')
    assert similarity.compare_section(after, baseline(before))['percent'] == 100
    assert similarity.normalized_words([{'type': 'paragraph', 'text': 'İ I,  İŞÇİ!\n\tIĞDIR…'},
        {'type': 'bullets', 'items': ['Bir; iki.', '3.000,25 adet']},
        {'type': 'table', 'rows': [['Hariç metin', '9876']]}]) == [
            'i', 'ı', 'işçi', 'ığdır', 'bir', 'iki', '#', 'adet']
    list_only = {'code': 'I.A', 'blocks': [{'type': 'bullets', 'items': WORDS}]}
    assert similarity.compare_section(list_only, baseline())['percent'] == 100


@pytest.mark.parametrize('section', [narrative(' '.join(WORDS[:29])), narrative('', code='I.A'),
    narrative(code=sections.CORE), narrative(code='EKLER'), narrative(content_kind='assurance'),
    {'code': 'I.A', 'blocks': [{'type': 'table', 'rows': [[TEXT]]}]}])
def test_short_or_excluded_has_no_warning_or_percentage(section):
    assert similarity.compare_section(section, baseline()) is None


def test_thirty_words_compared_and_below_threshold_has_no_warning():
    at_limit = similarity.compare_section(narrative(' '.join(WORDS[:30])), baseline())
    assert at_limit['percent'] == 86 and at_limit['message']
    below = similarity.compare_section(narrative(' '.join(['yeni'] * 40)), baseline())
    assert below['percent'] == 0 and below['message'] == ''


@pytest.mark.parametrize('unit', [False, True])
def test_editor_overview_and_pinned_download_once_per_report(section_client, db, sample, unit):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample) if unit else docs['idare']
    record = store_baseline(db, sample, doc, version=2)
    # A newer draft/submission must never replace the approved source.
    if unit:
        store_baseline(db, sample, doc, text='Taslak', version=3, kind='submit')
    token = login(client, 'strategy@example.invalid')
    for code in ('I.A', 'I.B'):
        assert save(client, token, doc, code=code, blocks=narrative()['blocks']).status_code == 200
    with patch.object(similarity, 'load_baseline', wraps=similarity.load_baseline) as load:
        editor = client.get(f'/activity-sections/reports/{doc.id}?code=I.A')
        assert editor.status_code == 200
        assert load.call_count == 1
    warning = html.fromstring(editor.text).xpath('//*[@data-ar-similarity]')
    assert len(warning) == 1 and '2026 yılı' in warning[0].text_content() and '%100 benzer' in warning[0].text_content()
    link = warning[0].xpath('.//a')[0]
    assert ('Revizyon 2' if unit else 'Sürüm 2') in link.text_content()
    download = client.get(link.get('href'))
    assert download.status_code == 200 and download.content == record.payload_json.encode()
    assert download.headers['cache-control'] == 'private, no-store'
    with patch.object(similarity, 'load_baseline', wraps=similarity.load_baseline) as load:
        overview = client.get(f"/activity-sections?period_id={sample['period'].id}")
        assert overview.status_code == 200 and load.call_count == 1
    assert len(html.fromstring(overview.text).xpath('//*[@data-ar-similarity]')) == 2
    # Adding a newer baseline does not change the already rendered source URL.
    store_baseline(db, sample, doc, text='Değişti', version=4)
    assert client.get(link.get('href')).content == download.content
    assert sections.digest(record.payload_json) == record.sha256


def test_latest_approval_or_freeze_and_scope_isolation(section_client, db, sample):
    _, docs, _, _ = section_client
    for doc in (docs['idare'], own_report(docs, sample)):
        store_baseline(db, sample, doc, text='Eski', version=1)
        latest = store_baseline(db, sample, doc, version=2)
        if doc.department_id:
            # A legacy unit freeze must not take precedence over unit approvals.
            store_baseline(db, sample, doc, text='Eski birim dondurması', version=5, kind='freeze')
        result = similarity.load_baseline(db, doc, 2026)
        assert similarity.compare_section(narrative(), result)['percent'] == 100
        expected_source = f'/approvals/{latest.id}.json' if doc.department_id else 'version=2'
        assert expected_source in result['source_url']


def test_missing_baseline_same_code_year_organization_and_no_drafts(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample)
    store_baseline(db, sample, doc, year=2025)
    store_baseline(db, sample, doc, year=2026, kind='submit')
    other_org = Organization(name='Başka belediye'); db.add(other_org); db.flush()
    store_baseline(db, sample, doc, organization_id=other_org.id)
    token = login(client, 'strategy@example.invalid')
    assert save(client, token, doc, blocks=narrative()['blocks']).status_code == 200
    missing = 'Karşılaştırma yapılamadı: 2026 yılı için onaylı rapor bulunamadı.'
    for path in (f'/activity-sections/reports/{doc.id}', f"/activity-sections?period_id={sample['period'].id}"):
        response = client.get(path)
        assert response.status_code == 200 and missing in response.text
        assert '%100' not in response.text
    missing_section = baseline(sections={'I.B': narrative(code='I.B')})
    assert similarity.compare_section(narrative(), missing_section) == {'percent': None, 'message': missing}


@pytest.mark.parametrize('unit', [False, True])
@pytest.mark.parametrize('invalid', ['sha', 'json'])
def test_tampered_baseline_is_nonblocking_turkish_error(section_client, db, sample, unit, invalid):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample) if unit else docs['idare']
    store_baseline(db, sample, doc, tampered=invalid == 'sha', payload={} if invalid == 'json' else None)
    token = login(client, 'strategy@example.invalid')
    assert save(client, token, doc, blocks=narrative()['blocks']).status_code == 200
    for path in (f'/activity-sections/reports/{doc.id}', f"/activity-sections?period_id={sample['period'].id}&section=I.A"):
        response = client.get(path)
        assert response.status_code == 200
        assert '2026 yılı onaylı rapor kopyası doğrulanamadı' in response.text
        assert '%100' not in response.text
        assert not html.fromstring(response.text).xpath('//*[@data-ar-similarity]//a')
    if invalid == 'sha':
        # The unfiltered overview also visits the damaged historical report itself.
        overview = client.get('/activity-sections?section=I.A')
        assert overview.status_code == 200
        assert '2026 yılı onaylı rapor kopyası doğrulanamadı' in overview.text
        assert not html.fromstring(overview.text).xpath('//*[@data-ar-similarity]//a')


def test_unit_only_own_percentage_strategy_every_unit_and_download_acl(section_client, db, sample):
    client, docs, other, _ = section_client
    own = own_report(docs, sample)
    another = docs[f'birim:{other.id}']
    token = login(client, 'strategy@example.invalid')
    sources = {}
    for doc in (own, another, docs['idare']):
        sources[doc.id] = store_baseline(db, sample, doc)
        assert save(client, token, doc, blocks=narrative()['blocks']).status_code == 200
    overview = client.get(f"/activity-sections?period_id={sample['period'].id}&section=I.A")
    assert len(html.fromstring(overview.text).xpath('//*[@data-ar-similarity]')) == 3
    login(client, 'test@example.invalid')
    overview = client.get(f"/activity-sections?period_id={sample['period'].id}&section=I.A")
    rows = html.fromstring(overview.text).xpath('//*[@data-ar-similarity]')
    assert len(rows) == 1 and f'/reports/{sources[own.id].document_id}/' in rows[0].xpath('.//a/@href')[0]
    assert not html.fromstring(client.get(f"/activity-sections/reports/{docs['idare'].id}").text).xpath('//*[@data-ar-similarity]')
    assert client.get(f'/activity-sections/reports/{another.id}').status_code == 403
    forbidden = sources[another.id]
    assert client.get(f'/activity-sections/reports/{forbidden.document_id}/approvals/{forbidden.id}.json').status_code == 403
    own_source = sources[own.id]
    assert client.get(f'/activity-sections/reports/{own_source.document_id}/approvals/{forbidden.id}.json').status_code == 404
    assert client.get(f'/activity-sections/reports/{own_source.document_id}/approvals/{own_source.id}.json').status_code == 200


def test_below_threshold_overview_percentage_is_not_a_warning(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample)
    store_baseline(db, sample, doc)
    token = login(client, 'strategy@example.invalid')
    assert save(client, token, doc, blocks=narrative(' '.join(WORDS[:34] + ['yeni'] * 6))['blocks']).status_code == 200
    editor = client.get(f'/activity-sections/reports/{doc.id}').text
    assert not html.fromstring(editor).xpath('//*[@data-ar-similarity]')
    overview = client.get(f"/activity-sections?period_id={sample['period'].id}&section=I.A").text
    assert 'Önceki yıl benzerliği: %85' in overview
    assert not html.fromstring(overview).xpath('//*[@data-ar-similarity]')


@pytest.mark.parametrize('tampered', [False, True])
def test_warning_never_blocks_save_submit_approve_or_changes_frozen_exports(section_client, db, sample, tampered):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample)
    ready_unit(db, doc, sample['user'])
    store_baseline(db, sample, doc, tampered=tampered)
    token = login(client, 'test@example.invalid')
    assert save(client, token, doc, status='ready', blocks=narrative()['blocks']).status_code == 200
    report = sections.report_data(db, sample['user'], doc.id)
    untouched = copy.deepcopy(report)
    assert similarity.for_report(db, sample['user'], report)['I.A']['percent'] == (None if tampered else 100)
    assert report == untouched
    message = 'kopyası doğrulanamadı' if tampered else '%100 benzer'
    assert message in client.get(f'/activity-sections/reports/{doc.id}').text
    approval = approve_unit(db, doc, sample['user'])
    frozen_before = (approval.payload_json, approval.sha256)
    assert 'similarity' not in approval.payload_json and 'benzer' not in approval.payload_json
    login(client, 'strategy@example.invalid')
    def exports():
        result = []
        for suffix in ('typeset.json', 'export.docx', 'export.pdf', 'export.json'):
            response = client.get(f'/activity-sections/reports/{doc.id}/{suffix}')
            assert response.status_code == 200, response.text[:500]
            result.append(response.content)
        return result
    before = exports()
    assert b'ar-typeset/1' in before[0] and b'similarity' not in before[0]
    assert message in client.get(f'/activity-sections/reports/{doc.id}').text
    assert message in client.get(f"/activity-sections?period_id={sample['period'].id}").text
    # Change the advice by damaging only the previous year's source.
    prior = prior_document(db, sample, doc)
    db.execute(update(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == prior.id).values(sha256='0' * 64))
    db.commit()
    assert 'kopyası doğrulanamadı' in client.get(f'/activity-sections/reports/{doc.id}').text
    with patch.object(similarity, 'for_report', side_effect=AssertionError('Exports must not calculate advice')):
        assert exports() == before
    assert (approval.payload_json, approval.sha256) == frozen_before


@pytest.mark.parametrize('tampered', [False, True])
def test_idare_warning_never_blocks_freeze_or_changes_release_bytes(section_client, db, sample, tampered):
    client, docs, _, _ = section_client
    doc = docs['idare']
    store_baseline(db, sample, doc, tampered=tampered)
    token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc)
    assert reopen(client, token, doc).status_code == 200
    assert save(client, token, doc, status='ready', blocks=narrative()['blocks']).status_code == 200
    message = 'kopyası doğrulanamadı' if tampered else '%100 benzer'
    assert message in client.get(f'/activity-sections/reports/{doc.id}').text
    assert freeze(client, token, doc).status_code == 200
    record = sections.latest_release(db, doc)
    original = record.payload_json, record.sha256
    assert 'similarity' not in record.payload_json and 'benzer' not in record.payload_json
    typeset_url = f'/activity-sections/reports/{doc.id}/typeset.json?version={record.version}'
    typeset = client.get(typeset_url)
    assert typeset.status_code == 200
    before = downloads(client, doc, record.version)
    assert message in client.get(f'/activity-sections/reports/{doc.id}').text
    assert message in client.get(f"/activity-sections?period_id={sample['period'].id}").text
    with patch.object(similarity, 'for_report', side_effect=AssertionError('Exports must not calculate advice')):
        assert downloads(client, doc, record.version) == before
        assert client.get(typeset_url).content == typeset.content
    assert (record.payload_json, record.sha256) == original


@pytest.mark.parametrize('unit', [False, True])
def test_copy_review_flag_independent_of_similarity(section_client, db, sample, unit):
    client, docs, _, _ = section_client
    doc = own_report(docs, sample) if unit else docs['idare']
    source = store_baseline(db, sample, doc)
    # create_year's actual previous-year copy behavior is exercised on a fresh scope/year.
    target = ReportingPeriod(year=2028, status='active'); db.add(target); db.flush()
    if unit:
        db.add(DepartmentScope(period_id=target.id, department_id=doc.department_id, status='required'))
    # Store the same source in 2027, which is the copy baseline for 2028.
    payload = json.loads(source.payload_json)
    payload.update(id=doc.id, year=2027, period_id=doc.period_id)
    raw = sections.numeric_canonical(payload)
    if unit:
        record = ARUnitWorkflowEvent(document_id=doc.id, revision=1, action='approve', from_status='submitted',
            to_status='approved', actor_id=sample['strategy'].id, actor_name='Strateji', created_at=datetime.now(UTC),
            payload_json=raw, sha256=sections.digest(raw))
    else:
        record = ARDocumentFreeze(document_id=doc.id, version=1, payload_json=raw,
            sha256=sections.digest(raw), created_by=sample['strategy'].id)
    db.add(record); db.commit()
    created = sections.create_year(db, sample['strategy'], doc.organization_id, target.id, copy_previous=True)
    copied = next(d for d in created if d.scope == doc.scope)
    db.commit()
    _, content = sections.section_pair(db, copied, 'I.A')
    assert content.copied_needs_review
    assert (content.copied_from_approval_id if unit else content.copied_from_id) == record.id
    token = login(client, 'strategy@example.invalid')
    html_before = client.get(f'/activity-sections/reports/{copied.id}').text
    assert 'Geçen yıldan kopyalandı — gözden geçirin' in html_before and '%100 benzer' in html_before
    overview = client.get(f'/activity-sections?period_id={target.id}&section=I.A').text
    assert 'Geçen yıldan kopyalandı — gözden geçirin' in overview and '%100 benzer' in overview
    assert save(client, token, copied, status='ready', blocks=narrative()['blocks']).status_code == 200
    db.refresh(content)
    assert not content.copied_needs_review
    html_after = client.get(f'/activity-sections/reports/{copied.id}').text
    assert 'Geçen yıldan kopyalandı — gözden geçirin' not in html_after and '%100 benzer' in html_after
