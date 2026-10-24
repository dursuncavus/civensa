"""AR unit review and immutable approved versions, independent of PP storage."""
import json
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy import func, select

from . import activity_sections_service as sections
from .activity_contract_service import digest
from .models import (ARContentEvent, ARDocument, ARUnitWorkflowEvent, Department, DepartmentScope, User,
                     ActivityReport, ActivityReportRevision, ActualRevision, ReportIndicator, PublicationIndicatorBinding)
from .pp_errors import pp_error
from .released_permissions import require_strategy_director, SOD_ERROR
from .structure_service import period_name
from .time_display import turkey_time

STATUSES = {'draft': 'Taslak', 'submitted': 'Gönderildi', 'returned': 'İade edildi', 'approved': 'Onaylandı'}


def latest(db, doc, action=None):
    query = select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == doc.id)
    if action:
        query = query.where(ARUnitWorkflowEvent.action == action)
    return db.scalar(query.order_by(ARUnitWorkflowEvent.id.desc()).limit(1))


def state(db, doc):
    current = latest(db, doc) if doc.department_id else None
    return current.to_status if current else 'draft'


def verified_payload(record):
    if not record.payload_json or digest(record.payload_json) != record.sha256:
        raise pp_error(409, 'Birim raporunun sabit kopyası doğrulanamadı. Strateji ile rapor sürümünü kontrol edin.', 'document_id')
    return json.loads(record.payload_json, parse_float=Decimal)


def view(db, doc):
    current = latest(db, doc)
    status = current.to_status if current else 'draft'
    events = db.scalars(select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == doc.id)
                        .order_by(ARUnitWorkflowEvent.id)).all()
    return {'status': status, 'label': STATUSES[status], 'reason': current.reason if current else '',
            'events': [{'id': e.id, 'action': e.action, 'from_status': e.from_status, 'to_status': e.to_status,
                        'label': STATUSES[e.to_status], 'reason': e.reason, 'actor_id': e.actor_id,
                        'actor_name': e.actor_name, 'created_at': turkey_time(e.created_at),
                        'revision': e.revision, 'sha256': e.sha256} for e in events]}


def approved_sources(db, doc):
    """Current reporting scope, including departments whose document is absent."""
    deps = db.scalars(select(Department).join(DepartmentScope, DepartmentScope.department_id == Department.id)
        .where(Department.organization_id == doc.organization_id, DepartmentScope.period_id == doc.period_id,
               DepartmentScope.status != 'excluded').order_by(Department.id)).all()
    sources, missing = [], []
    for dep in deps:
        unit = db.scalar(select(ARDocument).where(ARDocument.organization_id == doc.organization_id,
            ARDocument.period_id == doc.period_id, ARDocument.department_id == dep.id))
        approval = latest(db, unit, 'approve') if unit else None
        name = period_name(db, doc.period_id, dep)
        if not approval:
            missing.append({'department_id': dep.id, 'department': name})
        else:
            sources.append((approval, verified_payload(approval)))
    return sources, missing


def completeness(payload):
    # Includes the read-only indicator section and the locked assurance slots.
    return [s['title'] for s in payload['sections'] if s['status'] not in {'ready', 'not_applicable'}
            or s['missing'] or (s['status'] == 'not_applicable' and not s['reason'].strip())]


def independent(db, user, doc, cursor):
    edits = db.scalars(select(ARContentEvent).where(ARContentEvent.document_id == doc.id,
        ARContentEvent.actor_id == user.id, ARContentEvent.id > cursor)).all()
    for edit in edits:
        if edit.action not in {'create', 'freeze'} or (
                edit.action == 'create' and (json.loads(edit.after_json).get('copied_from_id') or
                                          json.loads(edit.after_json).get('copied_from_approval_id'))):
            raise pp_error(403, SOD_ERROR.format(record='Birim faaliyet raporu'), 'actor_id')


def source_editors(db, doc):
    """Include the editors of read-only sources actually reviewed at submission."""
    reset = db.scalar(select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == doc.id,
        ARUnitWorkflowEvent.action.in_(['return', 'reopen'])).order_by(ARUnitWorkflowEvent.id.desc()).limit(1))
    actuals = select(ActualRevision.created_by).join(ReportIndicator,
        ReportIndicator.id == ActualRevision.report_indicator_id).join(PublicationIndicatorBinding,
        PublicationIndicatorBinding.id == ReportIndicator.publication_binding_id).join(ActivityReportRevision,
        ActivityReportRevision.id == ReportIndicator.report_revision_id).join(ActivityReport,
        ActivityReport.id == ActivityReportRevision.report_id).where(
        ActivityReport.organization_id == doc.organization_id, ActivityReport.period_id == doc.period_id,
        ActivityReportRevision.revision == ActivityReport.current_revision,
        PublicationIndicatorBinding.department_id == doc.department_id)
    finance = select(ARContentEvent).join(ARDocument, ARDocument.id == ARContentEvent.document_id).where(
        ARDocument.organization_id == doc.organization_id, ARDocument.period_id == doc.period_id,
        ARDocument.department_id.is_(None), ARContentEvent.section_code == 'III.A.1',
        ARContentEvent.action.in_(['financial_save', 'financial_import']))
    if reset:
        cutoff = reset.created_at
        if cutoff.tzinfo is None: cutoff = cutoff.replace(tzinfo=UTC)
        actuals = actuals.where(ActualRevision.created_at >= cutoff.astimezone(UTC).replace(tzinfo=None))
        finance = finance.where(ARContentEvent.created_at >= cutoff)
    editors = set(db.scalars(actuals))
    for edit in db.scalars(finance):
        for raw in (edit.before_json, edit.after_json):
            data = json.loads(raw)
            if isinstance(data, dict) and 'lower_rate' in data:
                editors.add(edit.actor_id)
            rows = data.get('rows', []) if isinstance(data, dict) else data if isinstance(data, list) else []
            if any(row.get('department_id') == doc.department_id for row in rows):
                editors.add(edit.actor_id)
    return sorted(editors)


def transition(db, user, document_id, action, expected_revision, reason=''):
    user = db.get(User, user.id, populate_existing=True)
    doc = sections.document(db, user, document_id)
    if not doc.department_id:
        raise pp_error(422, 'Bu işlem yalnız birim raporu içindir. Birim faaliyet raporunu seçin.', 'document_id')
    if action == 'submit':
        if user.department_id != doc.department_id or (user.position != 'director' and not user.can_submit):
            raise pp_error(403, 'Birim faaliyet raporu gönderilemedi. Kendi müdürlüğünüzün Müdür hesabını veya gönderim yetkili Personel hesabını kullanın; yetki için Strateji birimine başvurun.', 'actor_id')
    else:
        require_strategy_director(user)
    sections.lock_documents(db, doc)
    if sections.frozen(db, doc):
        raise pp_error(409, 'Önceden dondurulmuş faaliyet raporu değiştirilemez. Strateji ile yeni rapor dönemi için iletişime geçin.', 'document_id')
    if doc.revision != expected_revision:
        raise pp_error(409, 'Birim faaliyet raporunun sürümü değişti. Sayfayı yenileyip son sürümde yeniden deneyin.', 'expected_revision')
    current = latest(db, doc)
    status = current.to_status if current else 'draft'
    allowed = {'submit': {'draft', 'returned'}, 'return': {'submitted'}, 'approve': {'submitted'}, 'reopen': {'approved'}}
    if action not in allowed or status not in allowed[action]:
        raise pp_error(409, f'Birim faaliyet raporu için bu geçiş kullanılamıyor. Güncel durum: {STATUSES[status]}. Sayfayı yenileyip uygun işlemi seçin.', 'status')
    reason = reason.strip()
    if action in {'return', 'reopen'} and not reason:
        raise pp_error(422, 'Birim faaliyet raporu iade edilmedi veya yeniden açılmadı. Gerekçe alanını doldurup yeniden deneyin.', 'reason')
    if len(reason) > 10000:
        raise pp_error(422, 'Birim faaliyet raporu gerekçesi çok uzun. En fazla 10.000 karakter yazın.', 'reason')
    cursor = current.content_event_cursor if current else 0
    payload_json = sha256 = None
    if action == 'submit':
        # Actual edits/rebases lock this row too. Keep the pinned CORE values and
        # their editor provenance consistent while capturing the unit version.
        db.scalar(select(ActivityReport).where(ActivityReport.organization_id == doc.organization_id,
            ActivityReport.period_id == doc.period_id).with_for_update().execution_options(populate_existing=True))
        payload = sections.report_data(db, user, doc.id, use_freeze=False, include_typeset=True)
        from .ar_typeset_source import require_keys
        require_keys(payload)
        missing = completeness(payload)
        if missing:
            raise pp_error(409, 'Birim faaliyet raporu gönderilemedi. Şu bölümleri tamamlayın: ' + '; '.join(missing), 'sections')
        payload.pop('workflow', None)
        payload['source_editor_ids'] = source_editors(db, doc)
        payload_json = sections.numeric_canonical(payload)
        sha256 = digest(payload_json)
    elif action == 'approve':
        independent(db, user, doc, cursor)
        reviewed = verified_payload(current)
        from .ar_typeset_source import compatible
        if not compatible(reviewed):
            raise pp_error(409, 'Gönderilmiş birim kopyasında dizgi anahtarları yok. Raporu gerekçeyle iade edip yeni anahtarlarla yeniden gönderilmesini sağlayın.', 'document_id')
        if user.id in reviewed['source_editor_ids']:
            raise pp_error(403, SOD_ERROR.format(record='Birim faaliyet raporu'), 'actor_id')
        payload_json, sha256 = current.payload_json, current.sha256
    else:
        cursor = db.scalar(select(func.max(ARContentEvent.id)).where(ARContentEvent.document_id == doc.id)) or 0
    doc.revision += 1
    record = ARUnitWorkflowEvent(document_id=doc.id, revision=doc.revision, action=action,
        from_status=status, to_status={'submit': 'submitted', 'return': 'returned', 'approve': 'approved', 'reopen': 'draft'}[action],
        reason=reason, actor_id=user.id, actor_name=user.full_name, created_at=datetime.now(UTC),
        content_event_cursor=cursor, payload_json=payload_json, sha256=sha256)
    db.add(record)
    db.flush()
    return record
