"""CIV-090: draft actuals and the unit's current-revision deviation gate."""
import json
from decimal import Decimal
from html.parser import HTMLParser

import pytest
from sqlalchemy import func, select

from app import activity_contract_service as contracts, activity_sections_service as sections
from app.models import (ActualRevision, ARUnitWorkflowEvent, Indicator, IndicatorValue,
                        Publication)
from ar_unit_workflow_helpers import ready_unit
from test_activity_sections import section_client, login

pytestmark = pytest.mark.postgres


@pytest.fixture
def deviation_report(section_client, db, sample):
    client, docs, other, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]

    def create(**revision_options):
        # Synthetic publication bypasses unrelated PP financial gates, while
        # definition hashes, publication bindings and actual saves stay real.
        payload, definitions = contracts.freeze_program_payload(db, doc.period_id, sample['strategy'])
        snapshot = contracts.canonical(payload)
        version = (db.scalar(select(func.max(Publication.version))) or 0) + 1
        publication = Publication(period_id=doc.period_id, version=version, snapshot_json=snapshot,
            sha256=contracts.digest(snapshot), created_by=sample['strategy'].id)
        db.add(publication); db.flush()
        contracts.attach_publication_definitions(db, publication, definitions, sample['strategy'])
        revision = contracts.create_report_revision(db, sample['strategy'], publication.id, doc.organization_id, **revision_options)
        db.commit()
        report = contracts.report_data(db, sample['strategy'], revision.id)
        token = login(client, sample['user'].email)
        return client, doc, report, token

    return create, other


def save_actual(client, token, slot, **changes):
    data = {'expected_revision': 0, 'value': '12501.98', 'state': 'verified',
            'evidence': [{'title': 'Birim kaydı', 'locator': 'Sayfa 1', 'source_revision': '2027-v1'}],
            'explanation': '', 'deviation': {}}
    data.update(changes)
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=data,
                           headers={'X-CSRF-Token': token})
    assert response.status_code == 200, response.text
    return response.json()


def submit(client, token, doc, html=False):
    url = f'/activity-sections/reports/{doc.id}/workflow/submit'
    if html:
        return client.post(url, data={'csrf_token': token, 'expected_revision': doc.revision})
    return client.post('/api' + url, json={'expected_revision': doc.revision},
                       headers={'X-CSRF-Token': token})


def test_missing_explanation_blocks_submit_then_latest_explanation_allows_it(deviation_report, db, sample, monkeypatch):
    create, _ = deviation_report
    client, doc, report, token = create()
    slot = report['indicators'][0]['report_indicator_id']
    saved = save_actual(client, token, slot)
    assert Decimal(saved['deviation']['delta']) == Decimal('12500.23')
    ready_unit(db, doc, sample['user'])
    revision = doc.revision
    builds = []
    original = sections.report_data

    def counted(*args, **kwargs):
        builds.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(sections, 'report_data', counted)
    response = submit(client, token, doc)
    assert len(builds) == 1
    message = ('Birim faaliyet raporu gönderilemedi. Şu göstergelerde hedef farkı açıklaması eksik: '
               'Hizmet sayısı.')
    assert response.status_code == 409, response.text
    assert response.json()['message'] == message
    assert doc.revision == revision
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0
    save_actual(client, token, slot, expected_revision=1, explanation='Kaynakla doğrulanan hizmet artışı.')
    response = submit(client, token, doc)
    assert response.status_code == 200, response.text
    assert len(builds) == 2
    event = db.scalar(select(ARUnitWorkflowEvent))
    pinned = json.loads(event.payload_json)['core']['indicators'][0]
    assert pinned['explanation'] == 'Kaynakla doğrulanan hizmet artışı.'
    assert pinned['deviation'].get('corrective_action', '') == ''


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.textareas = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.links.append(attrs.get('href'))
        if tag == 'textarea':
            self.textareas[attrs['name']] = attrs


def test_form_save_is_a_draft_with_turkish_warning_and_optional_corrective_action(deviation_report, db):
    create, _ = deviation_report
    client, _, report, token = create()
    slot = report['indicators'][0]['report_indicator_id']
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data={
        'csrf_token': token, 'expected_revision': 0, 'value': '12.501,98', 'state': 'verified',
        'source_title': 'Birim kaydı', 'source_locator': 'Sayfa 1', 'source_revision': '2027-v1',
        'explanation': '   ', 'corrective_action': ''})
    assert response.status_code == 303, response.text
    page = client.get(response.headers['location'])
    assert page.status_code == 200
    assert 'Hedef ile gerçekleşme arasında 12.500,23 fark var. Birim raporunu göndermeden önce açıklama girin.' in page.text
    assert 'Gönderim için zorunlu (fark varsa)' in page.text
    assert 'Kaydet taslak olarak saklar; eksik alanlar birim raporu gönderilirken kontrol edilir.' in page.text
    fields = Elements(page.text).textareas
    assert 'required' not in fields['explanation']  # Draft saves remain possible.
    assert 'required' not in fields['corrective_action']
    actual = db.scalar(select(ActualRevision))
    assert actual.explanation.strip() == '' and actual.revision == 1
    save_actual(client, token, slot, expected_revision=1, explanation='Artışın kaynağı açıklandı.')
    assert 'data-deviation-warning' not in client.get(response.headers['location']).text


@pytest.mark.parametrize('second_name', ['Hizmet sayısı', '<script>Diğer & gösterge</script>'])
def test_submit_lists_all_missing_indicators_with_distinct_safe_anchor_links(
        deviation_report, db, sample, second_name):
    create, _ = deviation_report
    second = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
                       subprogram_id=sample['subprogram'].id, name=second_name, unit='Adet')
    db.add(second); db.flush()
    db.add(IndicatorValue(indicator_id=second.id, year=2027, value_kind='target', value='1.75'))
    db.commit()
    client, doc, report, token = create()
    for row in report['indicators']:
        save_actual(client, token, row['report_indicator_id'], explanation=' \t\n ')
    ready_unit(db, doc, sample['user'])
    api = submit(client, token, doc)
    message = ('Birim faaliyet raporu gönderilemedi. Şu göstergelerde hedef farkı açıklaması eksik: '
               f'Hizmet sayısı; {second_name}.')
    assert api.status_code == 409 and api.json()['message'] == message
    assert api.json()['detail'] == message
    page = submit(client, token, doc, html=True)
    assert page.status_code == 409
    links = Elements(page.text).links
    for row in report['indicators']:
        anchor = f'/activity-reports/revisions/{report["revision_id"]}#indicator-{row["report_indicator_id"]}'
        assert anchor in links
        target = client.get(anchor.split('#')[0])
        assert f'id="indicator-{row["report_indicator_id"]}"' in target.text
    assert '<script>Diğer' not in page.text
    if '<script>' in second_name:
        assert '&lt;script&gt;Diğer &amp; gösterge&lt;/script&gt;' in page.text
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0


@pytest.mark.parametrize('target_kind,state,value,allowed', [
    ('verified', 'verified', '1.75', True),
    ('absent', 'verified', '8', True),
    ('needs_review', 'verified', '8', True),
    ('verified', 'needs_review', '8', False),
    ('verified', 'missing', None, False),
])
def test_zero_unknown_targets_and_unverified_actuals_do_not_trigger_deviation_gate(
        deviation_report, db, sample, target_kind, state, value, allowed):
    create, _ = deviation_report
    target = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == sample['indicator'].id))
    if target_kind == 'absent':
        db.delete(target)
    elif target_kind == 'needs_review':
        target.state = 'needs_review'
    db.commit()
    client, doc, report, token = create()
    slot = report['indicators'][0]['report_indicator_id']
    save_actual(client, token, slot, value='1.75', explanation='Önceki doğrulanmış kayıt.')
    ready_unit(db, doc, sample['user'])
    actual = save_actual(client, token, slot, expected_revision=1, state=state, value=value)
    if target_kind == 'verified' and state == 'verified':
        assert Decimal(actual['deviation']['delta']) == 0
    else:
        assert actual['deviation']['delta'] is None
    assert 'data-deviation-warning' not in client.get(f'/activity-reports/revisions/{report["revision_id"]}').text
    response = submit(client, token, doc)
    if allowed:
        assert response.status_code == 200, response.text
    else:
        # Existing completeness checks still own missing/needs_review states.
        assert response.status_code == 409
        assert response.json()['errors'][0]['field'] == 'sections'
        assert 'hedef farkı açıklaması eksik' not in response.text


def test_another_units_missing_explanation_does_not_block_this_unit(deviation_report, db, sample):
    create, other = deviation_report
    hidden = Indicator(period_id=sample['period'].id, department_id=other.id,
                       subprogram_id=sample['subprogram'].id, name='Diğer birimin göstergesi', unit='Adet')
    db.add(hidden); db.flush()
    db.add(IndicatorValue(indicator_id=hidden.id, year=2027, value_kind='target', value='1.75'))
    db.commit()
    client, doc, report, token = create()
    for row in report['indicators']:
        is_own = row['definition']['department_id'] == doc.department_id
        actor = sample['user'] if is_own else sample['strategy']
        contracts.save_actual(db, actor, row['report_indicator_id'], 0, '5', 'verified',
            [{'title': 'Kaynak', 'locator': 'Sayfa 1', 'source_revision': '1'}],
            'Birim açıklaması' if is_own else '', {})
    db.commit()
    ready_unit(db, doc, sample['user'])
    response = submit(client, token, doc)
    assert response.status_code == 200, response.text
    pinned = json.loads(db.scalar(select(ARUnitWorkflowEvent)).payload_json)['core']['indicators']
    assert len(pinned) == 1 and pinned[0]['name'] == 'Hizmet sayısı'


@pytest.mark.parametrize('current_missing', [False, True])
def test_only_current_report_revision_is_checked(deviation_report, db, sample, current_missing):
    create, _ = deviation_report
    client, doc, old, token = create()
    save_actual(client, token, old['indicators'][0]['report_indicator_id'],
                explanation='Eski açıklama' if current_missing else '')
    ready_unit(db, doc, sample['user'])
    client, doc, current, token = create(report_id=old['report_id'], expected_revision=1)
    slot = current['indicators'][0]['report_indicator_id']
    save_actual(client, token, slot, explanation='' if current_missing else 'Güncel açıklama')
    response = submit(client, token, doc)
    assert response.status_code == (409 if current_missing else 200), response.text


@pytest.mark.parametrize('state,delta,explanation,expected', [
    ('verified', '1', '', True), ('verified', '-1', ' \n\t ', True),
    ('verified', Decimal('1.000001'), '', True), ('verified', '0.000000', '', False),
    ('verified', None, '', False), ('verified', '1', ' Gerekçe ', False),
    ('needs_review', '1', '', False), ('missing', '1', '', False),
])
def test_shared_rule(state, delta, explanation, expected):
    assert contracts.needs_deviation_explanation(state, delta, explanation) is expected


def test_approval_still_uses_the_existing_deviation_message(client, db, sample):
    from app.main import app, require_user
    from test_activity_contract import publish, new_report, actual_payload
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    app.dependency_overrides[require_user] = lambda: sample['user']
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals',
                           json=actual_payload(explanation=' \t ', deviation={}))
    assert response.status_code == 200
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    response = client.post(f'/api/activity-reports/revisions/{report["revision_id"]}/approve')
    assert response.status_code == 409
    assert response.json()['detail']['blockers'] == [{
        'indicator': 'Hizmet sayısı', 'report_indicator_id': slot,
        'message': 'Hedef ile gerçekleşme farkı için açıklama girin.'}]


def test_captured_identity_without_anchor_still_blocks_submit(deviation_report, db, sample, monkeypatch):
    create, _ = deviation_report
    client, doc, report, token = create()
    save_actual(client, token, report['indicators'][0]['report_indicator_id'])
    ready_unit(db, doc, sample['user'])
    original = sections.report_data

    def stale_capture(*args, **kwargs):
        payload = original(*args, **kwargs)
        # Simulate an identity captured before its binding moved out of scope.
        payload['_typeset']['indicators'][0]['indicator_id'] = 'stale-captured-identity'
        return payload

    monkeypatch.setattr(sections, 'report_data', stale_capture)
    revision = doc.revision
    for html in (False, True):
        response = submit(client, token, doc, html=html)
        assert response.status_code == 409, response.text
        message = ('Birim faaliyet raporu gönderilemedi. Şu göstergelerde hedef farkı açıklaması eksik: '
                   'Hizmet sayısı.')
        if html:
            assert message in response.text
            assert not any('#indicator-' in (link or '') for link in Elements(response.text).links)
        else:
            assert response.json()['message'] == message
            blocker = response.json()['blockers'][0]
            assert blocker['report_indicator_id'] is None
            assert blocker['link'] == f"/activity-reports/revisions/{report['revision_id']}"
    assert doc.revision == revision
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0
