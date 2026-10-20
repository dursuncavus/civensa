"""CIV-059: local PostgreSQL deletion, history guards and atomic audits."""
import hashlib
import json
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from app.main import app, require_user
from app.models import (AuditLog, Department, DepartmentScope, DirectoratePackage,
    EconomicValue, Indicator, IndicatorDefinitionRevision, IndicatorIdentity, IndicatorValue,
    PackageDecision, PackageRevision, Publication, ReportCard, ReportingPeriod,
    Submission, SubmissionEvent, WorkflowEvent)
from app.program_service import record
from test_pp_required_period import snapshot

pytestmark = pytest.mark.postgres


@pytest.fixture
def fresh(db, sample):
    card = ReportCard(period_id=sample['period'].id, department_id=sample['department'].id,
        subprogram_id=sample['subprogram'].id, source_title='Yanlış kart', goal='Taslak hedef')
    indicator = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
        subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
        name='Yanlış gösterge', unit='Adet', explanation='Taslak açıklama')
    db.add_all([card, indicator]); db.commit()
    return {'card': card, 'indicator': indicator}


def url(kind, obj, department_id=1):
    return f'/program/{department_id}/{"cards" if kind == "card" else "indicator"}/{obj.id}/remove'


def actor(sample, role):
    app.dependency_overrides[require_user] = lambda: sample['strategy' if role == 'strategy' else 'user']


def refuse(client, db, kind, obj, status=409, period_id=1, department_id=1):
    before = snapshot(db)
    response = client.post(url(kind, obj, department_id), data={'period_id': period_id}, follow_redirects=False)
    assert response.status_code == status, response.text
    db.expire_all()
    assert snapshot(db) == before
    return response.json()['detail']


@pytest.mark.parametrize('role', ['department', 'strategy'])
@pytest.mark.parametrize('state', ['draft', 'returned'])
@pytest.mark.parametrize('kind', ['card', 'indicator'])
def test_remove_fresh_record_with_complete_audit(client, db, sample, fresh, kind, state, role):
    actor(sample, role)
    db.scalar(select(Submission)).status = state
    db.commit()
    obj = fresh[kind]; model = type(obj); record_id = obj.id
    previous = record(obj)
    if kind == 'indicator':
        previous['values'] = []
    before_count = len(db.scalars(select(AuditLog)).all())
    response = client.post(url(kind, obj), data={'period_id': 1, 'return_to': 'department'},
        headers={'Accept': 'application/json'})
    assert response.status_code == 200, response.text
    assert response.json()['redirect_url'] == '/department/1?period_id=1'
    db.expire_all()
    assert db.get(model, record_id) is None
    audits = db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert len(audits) == before_count + 1
    audit = audits[-1]
    assert audit.action == f'{kind}_remove'
    assert audit.entity_id == record_id
    assert audit.user_id == sample['strategy' if role == 'strategy' else 'user'].id
    assert json.loads(audit.details) == {'period_id': 1, 'department_id': 1, 'previous': previous}
    assert db.get(ReportCard, sample['card'].id)
    assert db.get(Indicator, sample['indicator'].id)


@pytest.mark.parametrize('role', ['department', 'strategy'])
@pytest.mark.parametrize('state', ['submitted', 'approved', 'closed'])
@pytest.mark.parametrize('kind', ['card', 'indicator'])
def test_refuse_locked_package_or_period(client, db, sample, fresh, kind, state, role):
    actor(sample, role)
    if state == 'closed':
        sample['period'].status = 'closed'
    else:
        db.scalar(select(Submission)).status = state
    db.commit()
    refuse(client, db, kind, fresh[kind])
    for path in ['/program/1?period_id=1', '/department/1?period_id=1']:
        assert 'data-draft-removal' not in client.get(path).text


@pytest.mark.parametrize('state', ['director_review', 'strategy_review', 'strategy_approved'])
@pytest.mark.parametrize('kind', ['card', 'indicator'])
def test_refuse_new_workflow_package_in_review(client, db, sample, fresh, state, kind):
    db.add(DirectoratePackage(organization_id=sample['department'].organization_id, department_id=1,
        period_id=1, resource_scope='performance_program', source_key='pp:1', state=state))
    db.commit()
    assert 'taslak veya iade' in refuse(client, db, kind, fresh[kind])


@pytest.mark.parametrize('kind', ['card', 'indicator'])
@pytest.mark.parametrize('case', ['other_path', 'other_record', 'excluded', 'wrong_period', 'missing_period'])
def test_department_and_period_boundaries(client, db, sample, fresh, kind, case):
    obj = fresh[kind]
    other = Department(organization_id=sample['department'].organization_id, name='Başka Müdürlük')
    period = ReportingPeriod(year=2028, status='draft')
    db.add_all([other, period]); db.flush()
    db.add(DepartmentScope(period_id=period.id, department_id=1, status='required'))
    if case == 'other_record':
        obj.department_id = other.id
    if case == 'excluded':
        db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == 1)).status = 'excluded'
    db.commit()
    if case == 'missing_period':
        before = snapshot(db)
        assert client.post(url(kind, obj), follow_redirects=False).status_code == 422
        assert snapshot(db) == before
    else:
        refuse(client, db, kind, obj, status=409 if case == 'wrong_period' else 403,
            period_id=period.id if case == 'wrong_period' else 1,
            department_id=other.id if case == 'other_path' else 1)


@pytest.mark.parametrize('children', ['indicators_activities', 'economic', 'economic_context', 'economic_both'])
def test_card_lists_child_counts(client, db, sample, fresh, children):
    card = sample['card']
    if children == 'indicators_activities':
        message = refuse(client, db, 'card', card)
        assert '2 gösterge ve 1 faaliyet var' in message
    else:
        card = fresh['card']
        value = db.scalar(select(EconomicValue))
        if children != 'economic_context':
            value.source_card_id = card.id
        if children != 'economic':
            value.source_context_json = json.dumps({'card_ids': [card.id, sample['card'].id]})
        db.commit()
        assert '1 ekonomik değer var' in refuse(client, db, 'card', card)


@pytest.mark.parametrize('state,raw,value', [('verified', '0', 0), ('needs_review', '—', None),
                                          ('verified', '', 1)])
def test_source_and_verified_values_are_preserved(client, db, fresh, state, raw, value):
    indicator = fresh['indicator']
    db.add(IndicatorValue(indicator_id=indicator.id, year=2027, value_kind='target',
        state=state, raw_text=raw, value=value))
    db.commit()
    message = refuse(client, db, 'indicator', indicator)
    assert indicator.name in message and '1 kaynak veya doğrulanmış değer' in message


@pytest.mark.parametrize('shared', [False, True])
def test_persistent_identity_never_deleted(client, db, sample, fresh, shared):
    indicator = fresh['indicator']
    identity_id = str(uuid4())
    db.add(IndicatorIdentity(indicator_id=identity_id, organization_id=sample['department'].organization_id))
    db.flush(); indicator.persistent_indicator_id = identity_id
    if shared:
        period = ReportingPeriod(year=2028, status='draft'); db.add(period); db.flush()
        db.add(Indicator(period_id=period.id, department_id=1, subprogram_id=sample['subprogram'].id,
            name='Sonraki dönem', unit='Adet', persistent_indicator_id=identity_id))
    db.commit()
    if shared:
        assert 'başka dönemde' in refuse(client, db, 'indicator', indicator)
    else:
        response = client.post(url('indicator', indicator), data={'period_id': 1}, follow_redirects=False)
        assert response.status_code == 303, response.text
        db.expire_all()
        assert db.get(Indicator, indicator.id) is None
    assert db.get(IndicatorIdentity, identity_id)


@pytest.mark.parametrize('history', ['publication', 'approval', 'definition', 'package_approval'])
def test_returned_record_keeps_frozen_history(client, db, sample, fresh, history):
    indicator = fresh['indicator']
    db.scalar(select(Submission)).status = 'returned'
    content = json.dumps({'indicators': [record(indicator)]})
    if history == 'publication':
        db.add(Publication(period_id=1, version=1, created_by=sample['strategy'].id,
            snapshot_json=json.dumps({'departments': [json.loads(content)]}),
            sha256=hashlib.sha256(content.encode()).hexdigest()))
    elif history == 'approval':
        db.add(SubmissionEvent(submission_id=db.scalar(select(Submission.id)), department_id=1, period_id=1,
            actor_user_id=sample['strategy'].id, event_type='approve', snapshot_json=content))
    elif history == 'definition':
        identity_id = str(uuid4())
        db.add(IndicatorIdentity(indicator_id=identity_id, organization_id=sample['department'].organization_id))
        db.flush(); indicator.persistent_indicator_id = identity_id
        db.add(IndicatorDefinitionRevision(indicator_id=identity_id, revision=1, period_id=1,
            definition_json=content, sha256=hashlib.sha256(content.encode()).hexdigest(), created_by=sample['strategy'].id))
    else:
        package = DirectoratePackage(organization_id=sample['department'].organization_id, department_id=1,
            period_id=1, resource_scope='performance_program', source_key='pp:1', state='returned')
        db.add(package); db.flush()
        revision = PackageRevision(package_id=package.id, revision=1, content_json=content,
            sha256=hashlib.sha256(content.encode()).hexdigest(), created_by=sample['user'].id)
        workflow_event = WorkflowEvent(actor_user_id=sample['strategy'].id, actor_snapshot_json='{}',
            organization_id=sample['department'].organization_id, department_id=1,
            event_type='strategy_approve', resource_type='directorate_package', resource_id=str(package.id),
            context_json='{}', reason='Test onayı', source='manual', correlation_id=str(uuid4()))
        db.add_all([revision, workflow_event]); db.flush()
        db.add(PackageDecision(package_revision_id=revision.id, snapshot_sha256=revision.sha256,
            action='strategy_approve', from_state='strategy_review', to_state='strategy_approved',
            workflow_event_id=workflow_event.id))
    db.commit()
    message = refuse(client, db, 'indicator', indicator)
    assert indicator.name in message
    assert ('donmuş' if history == 'definition' else 'geçmişte') in message


def test_unrelated_publication_does_not_block_new_draft(client, db, sample, fresh):
    content = json.dumps({'departments': [{'indicators': [record(sample['indicator'])]}]})
    db.add(Publication(period_id=1, version=1, created_by=sample['strategy'].id,
        snapshot_json=content, sha256=hashlib.sha256(content.encode()).hexdigest()))
    db.commit()
    assert client.post(url('indicator', fresh['indicator']), data={'period_id': 1}, follow_redirects=False).status_code == 303


@pytest.mark.parametrize('kind', ['card', 'indicator'])
def test_audit_failure_rolls_back_removal(client, db, fresh, kind):
    def fail_audit(mapper, connection, target):
        raise IntegrityError('disposable test audit failure', {}, Exception('test'))
    event.listen(AuditLog, 'before_insert', fail_audit)
    try:
        refuse(client, db, kind, fresh[kind])
    finally:
        event.remove(AuditLog, 'before_insert', fail_audit)
