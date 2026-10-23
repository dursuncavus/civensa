"""The typeset download reads immutable release bytes without resolving live facts."""
import json
from decimal import Decimal

from . import activity_sections_service as sections
from .ar_typeset_contract import export_bytes
from .models import ARUnitWorkflowEvent


def download(db, user, doc, version=None, approval_id=None):
    if version is not None and approval_id is not None:
        sections.fail('Tek bir rapor sürümü seçin. Yayın sürümü ile birim onayını birlikte kullanmayın.')
    release = sections.latest_release(db, doc, version) if version is not None else sections.frozen(db, doc)
    if version is not None and release is None:
        sections.fail('Faaliyet raporu sürümü bulunamadı. Sürüm geçmişinden mevcut bir sürüm seçin.', 404)
    approval = None
    if approval_id is not None:
        approval = db.get(ARUnitWorkflowEvent, approval_id)
        if not approval or approval.document_id != doc.id or approval.action != 'approve':
            sections.fail('Birim raporu onayı bulunamadı. Kendi raporunuzun sürüm geçmişini kullanın.', 404)
        release = None
    elif release is None and doc.department_id:
        from .ar_unit_workflow_service import latest
        current = latest(db, doc)
        if current and current.to_status == 'approved':
            approval = current
    if release or approval:
        record = release or approval
        if sections.digest(record.payload_json) != record.sha256:
            sections.fail('Dondurulmuş raporun doğrulama kodu uyuşmuyor. Sistem sorumlusuyla iletişime geçin.', 409)
        try:
            payload = json.loads(record.payload_json, parse_float=Decimal)
        except (ValueError, TypeError):
            sections.fail('Dondurulmuş raporun JSON kopyası okunamadı. Sistem sorumlusuyla iletişime geçin.', 409)
        metadata = {'release_version': release.version if release else approval.revision, 'source_sha256': record.sha256}
    else:
        payload = sections.report_data(db, user, doc.id, include_typeset=True)
        metadata = {'release_version': 'draft'}
    try:
        return export_bytes(payload, **metadata)
    except (KeyError, ValueError, TypeError, IndexError):
        sections.fail('Dizgi verisinin anahtarları veya sayıları doğrulanamadı. Strateji ile rapor kaynağını kontrol edip yeni sürüm yayınlayın.', 409)
