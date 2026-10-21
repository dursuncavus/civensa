"""Append-only indicator attachments and frozen manifests; no filesystem store."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, func, inspect
from .models import (ActivityEvidenceFile, ActivityEvidenceFreeze, ActualRevision,
                     ReportIndicator, PublicationIndicatorBinding, AuditLog)
from . import activity_contract_service as contract
from .file_security import validate_office_zip

# Same binary storage, limit and PDF/XLSX contract as financial statements.
from .activity_financial_service import MAX_FILE, validate_xlsx


def fail(message, field='source_file', status=422):
    raise HTTPException(status, {'message': message, 'field': field})


def validate_file(data, filename):
    suffix = Path(filename).suffix.lower()
    if not data or len(data) > MAX_FILE:
        fail('Kanıt dosyası boş veya 10 MB sınırını aşıyor. En fazla 10 MB PDF veya XLSX yükleyin.')
    if suffix == '.xlsx':
        try:
            validate_office_zip(data, suffix)
            validate_xlsx(data).close()
        except HTTPException as error:
            fail(f'Kanıt dosyası okunamadı: {error.detail} Geçerli PDF veya XLSX yükleyin.')
    elif suffix != '.pdf' or not data.startswith(b'%PDF-'):
        fail('Kanıt dosyasının biçimi geçersiz. PDF veya XLSX yükleyin.')
    return Path(filename).name[:200]


def ensure_upload_writable(db, report, revision, department_id):
    from .models import ARDocument, ARDocumentFreeze
    schema = db.connection().get_execution_options().get('schema_translate_map', {}).get(None)
    inspector = inspect(db.connection())
    sealed = inspector.has_table('activity_evidence_freezes', schema=schema) and db.scalar(
        select(ActivityEvidenceFreeze.id).where(ActivityEvidenceFreeze.report_revision_id == revision.id))
    if inspector.has_table('ar_documents', schema=schema):
        # Match the frozen core revision explicitly: a later correction revision
        # must not inherit a freeze of an older indicator snapshot.
        documents = db.scalars(select(ARDocument).where(ARDocument.organization_id == report.organization_id,
            ARDocument.period_id == report.period_id,
            (ARDocument.department_id == department_id) | ARDocument.department_id.is_(None))
            .order_by(ARDocument.id).with_for_update()).all()
        for document in documents:
            frozen = db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id == document.id))
            if frozen and json.loads(frozen.payload_json).get('core', {}).get('revision_id') == revision.id:
                sealed = True
    if sealed:
        fail('Bu gösterge revizyonu dondurulmuş rapor içeriğinde yer alıyor. Yeni kanıt dosyası için Strateji ile düzeltme revizyonu oluşturun.', status=409)


def prepare(db, item, previous, evidence, uploads):
    """Resolve identities from the previous realisation, never trust client hashes."""
    old = {s['source_id']: s for s in json.loads(previous.evidence_json) if s.get('source_id')} if previous else {}
    result, pending, seen = [], [], set()
    for index, source in enumerate(evidence):
        source = dict(source)
        identity = source.get('source_id')
        if identity:
            if not isinstance(identity, str) or identity not in old or identity in seen:
                fail('Kanıt kaynağının kimliği geçersiz veya yinelenmiş. Güncel gerçekleşmeyi açıp kaynakları yeniden kontrol edin.', 'source_title')
            seen.add(identity)
            source['files'] = old[identity].get('files', [])
        elif source.get('files'):
            fail('Kanıt dosyası başka bir kaynaktan taşınamaz. Bu kaynak satırına dosyayı yükleyin.', 'source_file')
        else:
            source.pop('source_id', None)
            source.pop('files', None)
        if index in uploads:
            data, filename = uploads[index]
            try:
                filename = validate_file(data, filename)
            except HTTPException as error:
                error.detail['source_index'] = index
                raise
            identity = identity or str(uuid4())
            source['source_id'] = identity
            source['files'] = list(source.get('files', []))
            version = (db.scalar(select(func.max(ActivityEvidenceFile.version)).where(
                ActivityEvidenceFile.report_indicator_id == item.id, ActivityEvidenceFile.source_id == identity)) or 0) + 1
            pending.append((source, data, filename, version))
        result.append(source)
    if set(uploads) - set(range(len(result))):
        fail('Dosyanın kaynak satırı bulunamadı. Kaynağı tamamlayıp yeniden yükleyin.')
    return result, pending


def persist(db, user, actual, evidence, pending):
    rows = []
    for source, data, filename, version in pending:
        row = ActivityEvidenceFile(actual_revision=actual, report_indicator_id=actual.report_indicator_id,
            source_id=source['source_id'], version=version, filename=filename, file_data=data,
            sha256=hashlib.sha256(data).hexdigest(), created_by=user.id)
        db.add(row)
        source['files'].append({'version': version, 'filename': filename, 'sha256': row.sha256,
            'download_url': f'/api/activity-reports/indicators/{actual.report_indicator_id}/evidence/{row.source_id}/{version}'})
        rows.append(row)
    actual.evidence_json = contract.canonical(evidence)
    db.flush()
    for row in rows:
        db.add(AuditLog(user_id=user.id, action='activity_evidence_upload', entity_type='activity_evidence_file',
            entity_id=row.id, details=contract.canonical({'actual_revision_id': actual.id, 'source_id': row.source_id,
                'version': row.version, 'sha256': row.sha256})))


def download(db, user, indicator_id, source_id, version):
    row = db.scalar(select(ActivityEvidenceFile).where(ActivityEvidenceFile.report_indicator_id == indicator_id,
        ActivityEvidenceFile.source_id == source_id, ActivityEvidenceFile.version == version))
    if not row:
        raise HTTPException(404, 'Kanıt dosyası bulunamadı. Gerçekleşme geçmişinden dosya sürümünü seçin.')
    item = db.get(ReportIndicator, row.report_indicator_id)
    binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
    contract.authorize(user, binding.department_id)
    contract.report_revision(db, user, item.report_revision_id)
    if hashlib.sha256(row.file_data).hexdigest() != row.sha256:
        raise HTTPException(409, 'Kanıt dosyasının doğrulama kodu uyuşmuyor. Sistem sorumlusuyla iletişime geçin.')
    db.add(AuditLog(user_id=user.id, action='activity_evidence_download', entity_type='activity_evidence_file',
                    entity_id=row.id, details=contract.canonical({'sha256': row.sha256, 'version': row.version})))
    return row


def verify_sources(db, item, sources):
    """A frozen package may carry files from its original indicator slot."""
    message = 'Kanıt eki listesi dosya kaydıyla uyuşmuyor. Kaynak gerçekleşmedeki ekleri kontrol edip paketi yeniden hazırlayın.'
    for source in sources:
        files = source.get('files', [])
        if not isinstance(files, list):
            fail(message, status=409)
        for meta in files:
            if (not isinstance(meta, dict) or type(meta.get('version')) is not int
                    or not isinstance(source.get('source_id'), str)):
                fail(message, status=409)
            row = db.scalar(select(ActivityEvidenceFile).join(ReportIndicator,
                ActivityEvidenceFile.report_indicator_id == ReportIndicator.id).where(
                    ReportIndicator.publication_binding_id == item.publication_binding_id,
                    ActivityEvidenceFile.source_id == source.get('source_id'),
                    ActivityEvidenceFile.version == meta.get('version')))
            if not row or meta != {'version': row.version, 'filename': row.filename, 'sha256': row.sha256,
                'download_url': f'/api/activity-reports/indicators/{row.report_indicator_id}/evidence/{row.source_id}/{row.version}'}:
                fail(message, status=409)


def freeze(db, revision_id):
    if not inspect(db.connection()).has_table('activity_evidence_freezes', schema=db.connection().get_execution_options().get('schema_translate_map', {}).get(None)):
        return  # Historical migration checkpoints have no attachment contract.
    existing = db.scalar(select(ActivityEvidenceFreeze).where(ActivityEvidenceFreeze.report_revision_id == revision_id))
    if existing:
        return existing
    manifest = []
    for item in db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision_id).order_by(ReportIndicator.id)):
        actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision.desc()))
        sources = json.loads(actual.evidence_json) if actual else []
        verify_sources(db, item, sources)
        manifest.append({'report_indicator_id': item.id, 'actual_revision_id': actual.id if actual else None,
                         'sources': sources})
    raw = contract.canonical(manifest)
    row = ActivityEvidenceFreeze(report_revision_id=revision_id, manifest_json=raw, sha256=contract.digest(raw))
    db.add(row); db.flush()
    return row
