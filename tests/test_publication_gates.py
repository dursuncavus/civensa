import pytest
from sqlalchemy import select, func
from app.models import (Submission, ReportSection, DepartmentScope, DepartmentCostValue,
                        EconomicValue, ActivityCostValue, ActivityCatalogueLink, Publication, AuditLog)
from app.main import app, require_user


def prepare(db, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    db.scalar(select(Submission)).status = 'approved'
    db.add(ReportSection(period_id=1, title='Genel Bilgiler', kind='text', content_json='{"text":"Onaylı içerik"}'))
    db.commit()


@pytest.mark.parametrize('problem,expected', [
    ('scope', 'kapsam'), ('approval', 'onay eksik'), ('section', 'genel bilgi'),
    ('finance', 'finansman bilgisi eksik'), ('source', 'personel ve SGK gideri eksik'),
    ('economic_zero', 'ekonomik gider hücresi eksik'), ('mismatch', 'uyuşmuyor'),
    ('catalogue_link', 'kataloğu bağlantısı eksik'), ('excluded_with_data', 'kapsam dışı müdürlükte veri var'),
])
def test_invalid_package_cannot_publish(client, db, sample, problem, expected):
    prepare(db, sample)
    if problem == 'scope': db.delete(db.scalar(select(DepartmentScope)))
    elif problem == 'approval': db.scalar(select(Submission)).status = 'submitted'
    elif problem == 'section': db.delete(db.scalar(select(ReportSection)))
    elif problem == 'finance': db.delete(db.scalar(select(ActivityCostValue).where(ActivityCostValue.year == 2028, ActivityCostValue.funding_type == 'outside')))
    elif problem == 'source': db.scalar(select(DepartmentCostValue)).state = 'needs_review'
    elif problem == 'economic_zero': db.delete(db.scalar(select(EconomicValue).where(EconomicValue.year == 2027, EconomicValue.category == 'lending', EconomicValue.funding_type == 'outside')))
    elif problem == 'mismatch': db.scalar(select(EconomicValue).where(EconomicValue.year == 2027, EconomicValue.category == 'goods_services', EconomicValue.funding_type == 'inside')).amount += 1
    elif problem == 'catalogue_link': db.delete(db.scalar(select(ActivityCatalogueLink)))
    else:
        scope = db.scalar(select(DepartmentScope)); scope.status = 'excluded'; scope.reason = 'Test gerekçesi'
    db.commit()
    response = client.post('/report-builder/publish', data={'period_id': 1}, follow_redirects=False)
    assert response.status_code == 409
    assert any(expected in message for message in response.json()['detail'])
    assert db.scalar(select(func.count()).select_from(Publication)) == 0
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'publication_freeze')) == 0


def test_failed_republication_preserves_frozen_version(client, db, sample):
    prepare(db, sample)
    assert client.post('/report-builder/publish', data={'period_id': 1}, follow_redirects=False).status_code == 303
    publication = db.scalar(select(Publication))
    before = (publication.version, publication.snapshot_json, publication.sha256)
    db.scalar(select(DepartmentCostValue)).state = 'needs_review'; db.commit()
    assert client.post('/report-builder/publish', data={'period_id': 1}, follow_redirects=False).status_code == 409
    db.expire_all()
    assert (publication.version, publication.snapshot_json, publication.sha256) == before
    assert db.scalar(select(func.count()).select_from(Publication)) == 1
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == 'publication_freeze')) == 1
