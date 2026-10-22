"""Disposable AR review fixtures, with real pinned indicator and actual rows."""
from uuid import uuid4
from sqlalchemy import select
from app import activity_sections_service as sections, ar_unit_workflow_service as workflow
from app.activity_contract_service import canonical, digest
from app.models import (ActivityReport, ActivityReportRevision, Publication, PublicationIndicatorBinding,
    IndicatorIdentity, IndicatorDefinitionRevision, ReportIndicator, ActualRevision, ARDocument,
    ARSectionContent, User, Department)


def ensure_core_ready(db, doc, actor):
    if sections.core_summary(db, doc)['status'] == 'ready':
        return
    report = db.scalar(select(ActivityReport).where(ActivityReport.organization_id == doc.organization_id,
        ActivityReport.period_id == doc.period_id))
    if not report:
        pub = Publication(period_id=doc.period_id, version=1, snapshot_json='{}', sha256=digest('{}'), created_by=actor.id)
        db.add(pub); db.flush()
        report = ActivityReport(organization_id=doc.organization_id, period_id=doc.period_id, current_revision=1)
        db.add(report); db.flush()
        revision = ActivityReportRevision(report_id=report.id, revision=1, publication_id=pub.id,
            publication_sha256=pub.sha256, created_by=actor.id)
        db.add(revision); db.flush()
    else:
        revision = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id,
            ActivityReportRevision.revision == report.current_revision))
    items = db.scalars(select(ReportIndicator).join(PublicationIndicatorBinding,
        PublicationIndicatorBinding.id == ReportIndicator.publication_binding_id).where(
        ReportIndicator.report_revision_id == revision.id, PublicationIndicatorBinding.department_id == doc.department_id)).all()
    if not items:
        identity = IndicatorIdentity(indicator_id=str(uuid4()), organization_id=doc.organization_id)
        db.add(identity); db.flush()
        text = canonical({'name': 'Doğrulanmış birim göstergesi', 'unit': 'Adet', 'targets': [], 'data_source': 'Birim kaydı'})
        definition = IndicatorDefinitionRevision(indicator_id=identity.indicator_id, revision=1, period_id=doc.period_id,
            definition_json=text, sha256=digest(text), created_by=actor.id)
        db.add(definition); db.flush()
        binding = PublicationIndicatorBinding(publication_id=revision.publication_id, snapshot_indicator_id=10000+doc.id,
            definition_revision_id=definition.id, department_id=doc.department_id, created_by=actor.id, reason='Test kapsamı')
        db.add(binding); db.flush()
        item = ReportIndicator(report_revision_id=revision.id, publication_binding_id=binding.id)
        db.add(item); db.flush()
        items = [item]
    for item in items:
        actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id)
            .order_by(ActualRevision.revision.desc()).limit(1))
        if not actual or actual.state != 'verified':
            db.add(ActualRevision(report_indicator_id=item.id, revision=actual.revision+1 if actual else 1,
                supersedes_id=actual.id if actual else None, value=0, state='verified',
                evidence_json='[{"title":"Kaynak","locator":"Sayfa 1","source_revision":"1"}]',
                explanation='Doğrulanmış test verisi', deviation_json='{}', created_by=actor.id))
    db.flush()


def reviewer(db, doc):
    user = db.scalar(select(User).where(User.email == 'ar-reviewer@example.invalid'))
    if not user:
        from app.security import hash_password
        from test_activity_sections import PASSWORD
        dep = Department(organization_id=doc.organization_id, name='Bağımsız Strateji Birimi')
        db.add(dep); db.flush()
        user = User(email='ar-reviewer@example.invalid', full_name='Bağımsız Strateji Müdürü', role='strategy',
            department_id=dep.id, position='director', password_hash=hash_password(PASSWORD))
        db.add(user); db.flush()
    return user


def ready_unit(db, doc, editor):
    """Ready content fixture; production validation and transitions remain active."""
    from app import assurance_service
    from test_assurance_helpers import variables
    for definition in sections.definitions(db, doc):
        if definition.code in {sections.CORE, 'EKLER'}:
            continue
        content = db.scalar(select(ARSectionContent).where(ARSectionContent.document_id == doc.id,
            ARSectionContent.definition_id == definition.id))
        content.blocks_json = '[{"type":"paragraph","text":"Yıllık değerlendirme"}]'
        content.status = 'not_applicable' if definition.code.startswith('III.A') else 'ready'
        content.reason = 'Bu örnekte malî veri bulunmuyor.' if content.status == 'not_applicable' else ''
        content.edited_by = editor.id
    db.flush()
    assurance_service.save(db, editor, doc.id, 'EK-2', {'expected_revision':doc.revision, 'variables':variables()})
    ensure_core_ready(db, doc, editor)
    db.commit()


def approve_unit(db, doc, editor):
    editor.can_submit = True
    workflow.transition(db, editor, doc.id, 'submit', doc.revision)
    approval = workflow.transition(db, reviewer(db, doc), doc.id, 'approve', doc.revision)
    db.commit()
    return approval


def approve_sources(db, idare):
    from app.models import DepartmentScope
    for doc in db.scalars(select(ARDocument).join(DepartmentScope,
        (DepartmentScope.department_id == ARDocument.department_id) & (DepartmentScope.period_id == ARDocument.period_id))
        .where(ARDocument.organization_id == idare.organization_id, ARDocument.period_id == idare.period_id,
               ARDocument.department_id.is_not(None), DepartmentScope.status != 'excluded')):
        if workflow.latest(db, doc, 'approve'):
            continue
        editor = db.scalar(select(User).where(User.department_id == doc.department_id, User.role == 'department'))
        ready_unit(db, doc, editor)
        approve_unit(db, doc, editor)
