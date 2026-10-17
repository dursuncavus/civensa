"""Confirmed F1/F6/F2 regressions and Turkish presentation-only formatting."""
import json
from pathlib import Path
from decimal import Decimal
import pytest
from sqlalchemy import select, func
from app.models import (Publication, IndicatorIdentity, IndicatorDefinitionRevision,
    PublicationIndicatorBinding, ActivityReportRevision, ActualRevision, AuditLog, IndicatorValue)
from app import activity_contract_service as service
from app.numbers import format_number
from test_activity_contract import publish, new_report, actual_payload


def load_v1(db, sample):
    frozen = json.loads((Path(__file__).parent / 'fixtures/activity_contract_v1_checkpoint.json').read_text())
    assert frozen['source_commit'] == '8c39c268bea7ce0ff85277acec3047a34363f6c3'
    db.add(IndicatorIdentity(indicator_id=frozen['indicator_id'], organization_id=sample['department'].organization_id));db.flush()
    sample['indicator'].persistent_indicator_id = frozen['indicator_id']
    definition = IndicatorDefinitionRevision(id=1, indicator_id=frozen['indicator_id'], revision=1,
        period_id=sample['period'].id, definition_json=frozen['definition_json'], sha256=frozen['definition_sha256'], created_by=sample['strategy'].id)
    db.add(definition); db.flush()
    pub = Publication(period_id=sample['period'].id, version=1, snapshot_json=frozen['publication_snapshot_json'],
        sha256=frozen['publication_sha256'], created_by=sample['strategy'].id)
    db.add(pub); db.flush()
    binding = PublicationIndicatorBinding(publication_id=pub.id, snapshot_indicator_id=sample['indicator'].id,
        definition_revision_id=definition.id, department_id=sample['department'].id, created_by=sample['strategy'].id, reason='Checkpoint v1 relationship')
    db.add(binding); db.commit()
    return pub, definition, binding, frozen


def test_card_method_and_source_are_frozen_and_diffed(client, db, sample):
    first = publish(client, db, sample); report = new_report(client, first, sample)
    definition = report['indicators'][0]['definition']
    assert definition['calculation_method'] == sample['card'].calculation_method
    assert definition['data_source'] == sample['card'].data_source
    assert definition['definition_contract_version'] == report['contract_version'] == '3.0'
    original = (first.snapshot_json, first.sha256)
    sample['card'].calculation_method = 'Yeni kart yöntemi'
    sample['card'].data_source = 'Yeni kart kaynağı';db.commit()
    second = publish(client, db, sample)
    revised = new_report(client, second, sample, report_id=report['report_id'], expected_revision=1)
    change = revised['differences'][0]
    assert change['before']['calculation_method'] == 'Kaynak yöntemi'
    assert change['after']['calculation_method'] == 'Yeni kart yöntemi'
    assert change['before']['data_source'] == 'Kaynak kayıt'
    assert change['after']['data_source'] == 'Yeni kart kaynağı'
    assert revised['indicators'][0]['definition_revision_id'] != report['indicators'][0]['definition_revision_id']
    page = client.get(f"/activity-reports/revisions/{revised['revision_id']}")
    assert all(text in page.text for text in ('Hesaplama yöntemi', 'Kaynak yöntemi', 'Yeni kart yöntemi', 'Kaynak kayıt', 'Yeni kart kaynağı'))
    db.expire_all(); assert (first.snapshot_json, first.sha256) == original
    old = client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()
    assert old['indicators'][0]['definition']['data_source'] == 'Kaynak kayıt'


def test_indicator_override_wins_over_card_inheritance(client, db, sample):
    sample['indicator'].calculation_method = 'Gösterge yöntemi'
    sample['indicator'].data_source = 'Gösterge kaynağı';db.commit()
    report = new_report(client, publish(client, db, sample), sample)
    definition = report['indicators'][0]['definition']
    assert definition['calculation_method'] == 'Gösterge yöntemi'
    assert definition['data_source'] == 'Gösterge kaynağı'


def test_exact_v1_checkpoint_survives_current_contract_and_keeps_all_history(client, db, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    pub, definition, binding, frozen = load_v1(db, sample)
    before = (pub.snapshot_json, pub.sha256, definition.definition_json, definition.sha256,
              binding.publication_id, binding.snapshot_indicator_id, binding.definition_revision_id, binding.reason)
    report = new_report(client, pub, sample)
    assert report['contract_version'] == '1.0'
    assert report['indicators'][0]['definition']['calculation_method'] == ''
    assert report['indicators'][0]['definition']['data_source'] == ''
    sample['card'].calculation_method = 'Yeni canlı kart'
    sample['card'].data_source = 'Yeni canlı kaynak';db.commit()
    new_pub = publish(client, db, sample)
    checked, payload = service.checked_publication(db, pub.id)
    assert service.publication_bindings(db, checked, payload, sample['department'].organization_id)
    revised = new_report(client, new_pub, sample, report_id=report['report_id'], expected_revision=1)
    assert revised['contract_version'] == '3.0'
    assert revised['differences'][0]['before']['calculation_method'] == ''
    assert revised['differences'][0]['after']['calculation_method'] == 'Yeni canlı kart'
    assert client.get(f"/activity-reports/revisions/{report['revision_id']}").status_code == 200
    assert client.get(f'/publications/{pub.id}.json').text == frozen['publication_snapshot_json']
    db.expire_all()
    assert (pub.snapshot_json, pub.sha256, definition.definition_json, definition.sha256,
            binding.publication_id, binding.snapshot_indicator_id, binding.definition_revision_id, binding.reason) == before


def approved_report(client, db, sample):
    pub = publish(client, db, sample);report = new_report(client, pub, sample)
    from tests.test_activity_contract import report_editor
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: report_editor(sample)
    slot = report['indicators'][0]['report_indicator_id']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).status_code == 200
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    assert client.post(f"/api/activity-reports/revisions/{report['revision_id']}/approve").status_code == 200
    return pub, report


@pytest.mark.parametrize('new_publication', [False, True])
@pytest.mark.parametrize('reason', [None, '', ' \t\n '])
def test_approved_correction_requires_reason_on_same_or_new_base(client, db, sample, new_publication, reason):
    pub, report = approved_report(client, db, sample)
    if new_publication:
        sample['card'].data_source = 'Yeni kaynak'; db.commit();pub = publish(client, db, sample)
    data = {'publication_id': pub.id, 'organization_id': report['organization_id'],
            'report_id': report['report_id'], 'expected_revision': 1}
    if reason is not None:
        data['revision_reason'] = reason
    response = client.post('/api/activity-reports/revisions', json=data)
    assert response.status_code == 422 and 'düzeltme gerekçesi' in response.json()['detail']
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == 1
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'activity_report_revision')) == 1
    assert client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()['approved']


@pytest.mark.parametrize('new_publication', [False, True])
def test_correction_reason_api_history_audit_and_immutability(client, db, sample, new_publication):
    pub, original = approved_report(client, db, sample)
    old = client.get(f"/api/activity-reports/revisions/{original['revision_id']}").json()
    if new_publication:
        sample['card'].calculation_method = 'Yeni yöntem';db.commit();pub = publish(client, db, sample)
    reason = '  Kaynak belgesine göre düzeltme <b>gerekçesi</b>  '
    corrected = new_report(client, pub, sample, report_id=original['report_id'], expected_revision=1, revision_reason=reason)
    assert corrected['revision_reason'] == reason.strip()
    audit = db.scalar(select(AuditLog).where(AuditLog.entity_id == corrected['revision_id'], AuditLog.action == 'activity_report_revision'))
    assert json.loads(audit.details)['revision_reason'] == reason.strip()
    assert json.loads(audit.details)['previous_revision_id'] == original['revision_id']
    for url in (f"/activity-reports/revisions/{corrected['revision_id']}", '/activity-reports'):
        page = client.get(url)
        assert page.status_code == 200 and 'Kaynak belgesine göre düzeltme &lt;b&gt;gerekçesi&lt;/b&gt;' in page.text
    after = client.get(f"/api/activity-reports/revisions/{original['revision_id']}").json()
    assert after['indicators'] == old['indicators'] and after['approved'] and after['revision_reason'] == ''
    revision = db.get(ActivityReportRevision, corrected['revision_id']);revision.revision_reason = 'Üzerine yaz'
    with pytest.raises(ValueError, match='değiştirilemez'): db.commit()
    db.rollback();assert revision.revision_reason == reason.strip()


def test_correction_reason_html_flow_and_initial_creation(client, db, sample):
    pub, original = approved_report(client, db, sample)
    page = client.get(f"/activity-reports/revisions/{original['revision_id']}")
    assert 'name="revision_reason" maxlength="10000" required' in page.text
    data = {'publication_id': pub.id, 'organization_id': original['organization_id'],
            'report_id': original['report_id'], 'expected_revision': 1}
    for reason in ('', '   '):
        response = client.post('/activity-reports/revisions', data={**data, 'revision_reason': reason})
        assert response.status_code == 422 and 'düzeltme gerekçesi' in response.text
    response = client.post('/activity-reports/revisions', data={**data, 'revision_reason': 'HTML kaynak düzeltmesi'}, follow_redirects=False)
    assert response.status_code == 303
    assert 'HTML kaynak düzeltmesi' in client.get(response.headers['location']).text
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == 2
    assert client.get(f"/api/activity-reports/revisions/{original['revision_id']}").json()['approved']


def test_initial_creation_has_no_reason_requirement(client, db, sample):
    pub = publish(client, db, sample)
    response = client.post('/activity-reports/revisions', data={'publication_id': pub.id,
        'organization_id': sample['department'].organization_id}, follow_redirects=False)
    assert response.status_code == 303
    assert db.scalar(select(ActivityReportRevision)).revision_reason == ''


@pytest.mark.parametrize('number,expected', [
    ('12500','12.500'), ('12500.23','12.500,23'), ('1.75','1,75'), ('0','0'),
    ('-1.75','-1,75'), ('-12500','-12.500'), ('12345678901234567890.123456','12.345.678.901.234.567.890,123456'),
])
def test_turkish_decimal_display(number, expected):
    value = Decimal(number)
    assert format_number(value) == expected
    assert format_number(number) == expected
    assert value == Decimal(number)


@pytest.mark.parametrize('target,actual,shown_target,shown_actual,shown_delta', [
    ('12500','12500.23','12.500','12.500,23','0,23'),
    ('1.75','0','1,75','0','-1,75'),
    ('0','-12500.23','0','-12.500,23','-12.500,23'),
    # SQLite Numeric is not an exact 26-digit store; exercise production PostgreSQL.
    pytest.param('12345678901234567890','12345678901234567890.123456','12.345.678.901.234.567.890',
                 '12.345.678.901.234.567.890,123456','0,123456', marks=pytest.mark.postgres),
])
def test_contract_screen_formats_target_actual_deviation_and_preserves_numbers(client, db, sample, target, actual, shown_target, shown_actual, shown_delta):
    target_row = db.scalar(select(IndicatorValue));target_row.value = Decimal(target);db.commit()
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    result = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(value=actual))
    assert result.status_code == 200
    page = client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert f'Hedef: {shown_target}' in page.text
    assert f'<p>{shown_actual} ·' in page.text
    assert f'Sayısal fark: {shown_delta}' in page.text
    assert f'name="value" value="{shown_actual}"' in page.text
    assert Decimal(result.json()['value']) == Decimal(actual)
    assert db.scalar(select(ActualRevision)).value == Decimal(actual)
    assert target_row.value == Decimal(target)


def test_target_difference_view_uses_turkish_formatting(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    db.scalar(select(IndicatorValue)).value = Decimal('12500.23');db.commit()
    revised = new_report(client, publish(client, db, sample), sample, report_id=report['report_id'], expected_revision=1)
    page = client.get(f"/activity-reports/revisions/{revised['revision_id']}")
    assert '<td>1,75</td>' in page.text and '<td>12.500,23</td>' in page.text
    assert "'value': '12500.23'" not in page.text
