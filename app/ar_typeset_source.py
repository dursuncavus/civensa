"""Capture identities alongside NEW report snapshots; never repair old snapshots."""
import json
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy import select

from . import activity_sections_service as sections
from .ar_typeset_keys import section_keys
from .models import (ARContentEvent, ARDocument, ARSectionContent, ARResourceRow, ARFinancialEntry,
    ActivityReport, ActivityReportRevision, ReportIndicator, PublicationIndicatorBinding,
    IndicatorDefinitionRevision, ActualRevision, Publication, ARStatementFigureKey)

SOURCE_VERSION = 'ar-source/1'
LEGACY_MESSAGE = 'Bu sürüm dizgi veri sözleşmesinden önce dondurulmuş. Strateji Geliştirme Müdürü raporu gerekçeyle açıp yeni sürüm yayınlamalıdır.'


def compatible(payload):
    if not isinstance(payload, dict):
        return False
    source = payload.get('_typeset', {})
    return isinstance(source, dict) and source.get('schema_version') == SOURCE_VERSION and source.get('complete') is True


def require_keys(payload):
    if not compatible(payload):
        sections.fail(LEGACY_MESSAGE, 409)


def enrich(db, doc, payload):
    """Called only while reading a mutable draft / capturing a new submission.

    Positions bind already-persisted keys to the snapshot's presentation order;
    they never generate an identity. Approved unit keys come only from snapshots.
    """
    source = {'schema_version': SOURCE_VERSION, 'complete': True,
              'sections': {}, 'resources': {}, 'entries': {}, 'figures': {}, 'indicators': [], 'activities': []}
    stamps = []
    # All report-owned edits append an event. Related central finance edits and
    # indicator revisions also advance this deterministic draft source timestamp.
    ids = [doc.id]
    if doc.department_id:
        central = db.scalar(select(ARDocument.id).where(ARDocument.organization_id == doc.organization_id,
                            ARDocument.period_id == doc.period_id, ARDocument.department_id.is_(None)))
        if central:
            ids.append(central)
    for stamp in db.scalars(select(ARContentEvent.created_at).where(ARContentEvent.document_id.in_(ids))):
        stamps.append(stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp)
    contents = list(db.scalars(select(ARSectionContent).where(ARSectionContent.document_id == doc.id)))
    by_definition = {c.definition_id: c for c in contents}
    for definition in sections.definitions(db, doc):
        content = by_definition[definition.id]
        keys = section_keys(db, content)
        blocks = json.loads(content.blocks_json)
        expected = [(i, len(b['rows'])) for i, b in enumerate(blocks) if b['type'] == 'table']
        if [(t['position'], len(t['rows'])) for t in keys] != expected:
            source['complete'] = False
        source['sections'][definition.code] = keys
    from .activity_financial_service import ENTRY_FIELDS
    for kind in ENTRY_FIELDS:
        source['entries'][kind] = [{'document_id': doc.id, 'stable_key': r.stable_key} for r in db.scalars(
            select(ARFinancialEntry).where(ARFinancialEntry.document_id == doc.id,
                ARFinancialEntry.kind == kind).order_by(ARFinancialEntry.position, ARFinancialEntry.id))]
    for statement in payload.get('financial',{}).get('statements',[]):
        source['figures'][str(statement['id'])]=list(db.scalars(select(ARStatementFigureKey.stable_key).where(ARStatementFigureKey.statement_id==statement['id']).order_by(ARStatementFigureKey.position,ARStatementFigureKey.id)))
    if doc.department_id:
        for kind in sections.TABLES:
            source['resources'][kind] = [{'document_id': doc.id, 'stable_key': r.stable_key} for r in db.scalars(
                select(ARResourceRow).where(ARResourceRow.document_id == doc.id, ARResourceRow.table_kind == kind)
                .order_by(ARResourceRow.position, ARResourceRow.id))]
        revision_id = payload['core'].get('revision_id')
        revision = db.get(ActivityReportRevision, revision_id) if revision_id else None
        if revision:
            query = select(ReportIndicator).join(PublicationIndicatorBinding,
                PublicationIndicatorBinding.id == ReportIndicator.publication_binding_id).where(
                ReportIndicator.report_revision_id == revision.id, PublicationIndicatorBinding.department_id == doc.department_id)
            for item in db.scalars(query.order_by(ReportIndicator.id)):
                binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
                definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
                source['indicators'].append({'indicator_id': definition.indicator_id,
                    'department_id': doc.department_id, 'document_id': doc.id})
                actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id)
                    .order_by(ActualRevision.revision.desc()).limit(1))
                if actual:
                    stamps.append(actual.created_at.replace(tzinfo=UTC) if actual.created_at.tzinfo is None else actual.created_at)
            publication = db.get(Publication, revision.publication_id)
            if sections.digest(publication.snapshot_json) != publication.sha256:
                sections.fail('Faaliyetlerin bağlı PP kopyası doğrulanamadı. Strateji ile PP yayınını kontrol edin.', 409)
            snapshot = json.loads(publication.snapshot_json, parse_float=Decimal)
            for department in snapshot.get('departments', []):
                if department['department_id'] == doc.department_id:
                    source['activities'].extend({'document_id': doc.id, 'department_id': doc.department_id,
                        'publication_id': publication.id, 'data': activity} for activity in department.get('activities', []))
    else:
        from .ar_unit_workflow_service import approved_sources
        approved, _ = approved_sources(db, doc)
        for kind in sections.TABLES:
            source['resources'][kind] = []
        for kind in ('aid', 'audit'):
            source['entries'][kind + '_directorates'] = []
        for approval, unit in approved:
            if not compatible(unit):
                source['complete'] = False
                continue
            captured = unit['_typeset']
            for kind in sections.TABLES:
                source['resources'][kind].extend(captured['resources'][kind])
            for kind in ('aid', 'audit'):
                source['entries'][kind + '_directorates'].extend(captured['entries'][kind])
            source['indicators'].extend(captured['indicators'])
            source['activities'].extend(captured['activities'])
            stamps.append(approval.created_at.replace(tzinfo=UTC) if approval.created_at.tzinfo is None else approval.created_at)
    source['generated_at'] = max(stamps).isoformat() if stamps else datetime(1970, 1, 1, tzinfo=UTC).isoformat()
    payload['_typeset'] = source
    return payload
