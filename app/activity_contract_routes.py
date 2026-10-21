"""JSON contract and server-rendered workflow share the same guarded services."""
import json
from typing import Any
from fastapi import Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field, StrictInt, StrictStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from .db import get_db
from .models import (ActivityReport, ActivityReportRevision, Publication, ReportingPeriod,
                     Department, Organization, AuditLog, IndicatorIdentity, PublicationIndicatorBinding)
from . import activity_contract_service as service
from .numbers import parse_number


class NewRevision(BaseModel):
    publication_id: StrictInt
    organization_id: StrictInt
    report_id: StrictInt | None = None
    expected_revision: StrictInt = Field(default=0, ge=0)
    revision_reason: StrictStr = Field(default='', max_length=10000)


class NewActual(BaseModel):
    expected_revision: StrictInt = Field(ge=0)
    value: StrictStr | None = None
    state: StrictStr = 'verified'
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    explanation: StrictStr = ''
    deviation: dict[str, Any] = Field(default_factory=dict)


class LegacyBinding(BaseModel):
    snapshot_indicator_id: StrictInt
    indicator_id: StrictStr | None = None
    reason: StrictStr


class PeriodIdentity(BaseModel):
    indicator_id: StrictStr
    reason: StrictStr


def register(app):
    from .main import require_user, templates

    def transact(db, user, action, entity, operation, audit_details='Yayın sürümüne bağlı veri sözleşmesi'):
        try:
            result = operation()
            entity_id = getattr(result, 'id', 0)
            if isinstance(result, ActivityReportRevision):
                audit_details = service.canonical({'revision_reason': result.revision_reason,
                    'previous_revision_id': result.previous_revision_id, 'publication_id': result.publication_id})
            db.add(AuditLog(user_id=user.id, action=action, entity_type=entity, entity_id=entity_id,
                            details=audit_details))
            db.commit()
            return result
        except HTTPException:
            db.rollback(); raise
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Kayıt başka bir işlemle çakıştı. Son sürümü açıp tekrar kontrol edin.') from None
        except OperationalError as error:
            db.rollback()
            if getattr(error.orig, 'sqlstate', None) in {'40001', '40P01'} or 'database is locked' in str(error.orig).lower():
                raise HTTPException(409, 'Eşzamanlı işlem çakışması oluştu. Son sürümü açıp tekrar kontrol edin.') from None
            raise HTTPException(503, 'Veritabanına şu anda erişilemiyor. Kaydı tekrar denemeden önce bağlantıyı kontrol edin.') from None

    @app.post('/api/activity-reports/revisions')
    def create_revision(data: NewRevision, db: Session = Depends(get_db), user=Depends(require_user)):
        result = transact(db, user, 'activity_report_revision', 'activity_report_revision',
            lambda: service.create_report_revision(db, user, **data.model_dump()))
        return {'revision_id': result.id, 'report_id': result.report_id, 'revision': result.revision}

    @app.get('/api/activity-reports/revisions/{revision_id}')
    def get_revision(revision_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
        return service.report_data(db, user, revision_id)

    @app.post('/api/activity-reports/indicators/{report_indicator_id}/actuals')
    def actual(report_indicator_id: int, data: NewActual, db: Session = Depends(get_db), user=Depends(require_user)):
        result = transact(db, user, 'actual_revision_create', 'actual_revision',
            lambda: service.save_actual(db, user, report_indicator_id, **data.model_dump()))
        return service.actual_data(result)

    @app.post('/api/activity-reports/revisions/{revision_id}/approve')
    def approve(revision_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
        result = transact(db, user, 'activity_report_approve', 'activity_report_approval',
            lambda: service.approve_report(db, user, revision_id))
        return {'approved': True, 'approval_id': result.id}

    @app.post('/api/publications/{publication_id}/indicator-bindings')
    def legacy_binding(publication_id: int, data: LegacyBinding, db: Session = Depends(get_db), user=Depends(require_user)):
        result = transact(db, user, 'publication_indicator_bind', 'publication_indicator_binding',
            lambda: service.bind_legacy_indicator(db, user, publication_id, data.snapshot_indicator_id,
                                                  data.indicator_id, data.reason))
        return {'binding_id': result.id}

    @app.post('/api/indicators/{period_indicator_id}/identity')
    def period_identity(period_indicator_id: int, data: PeriodIdentity, db: Session = Depends(get_db), user=Depends(require_user)):
        def operation():
            service.link_period_identity(db, user, period_indicator_id, data.indicator_id, data.reason)
            from .models import Indicator
            return db.get(Indicator, period_indicator_id)
        transact(db, user, 'period_indicator_identity', 'indicator', operation, audit_details=data.reason)
        return {'indicator_id': data.indicator_id}

    def ui_error(request, user, error, back):
        return templates.TemplateResponse(request, 'activity_contract_error.html',
            {'user': user, 'message': error.detail.get('message') if isinstance(error.detail, dict) else error.detail, 'blockers': error.detail.get('blockers', []) if isinstance(error.detail, dict) else [], 'back': back}, status_code=error.status_code)

    def integer(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise HTTPException(422, 'Seçilen kayıt veya revizyon numarası geçersiz.') from None

    @app.get('/activity-reports')
    def index(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        service.authorize(user)
        reports = db.scalars(select(ActivityReport).order_by(ActivityReport.id)).all()
        if user.role == 'department':
            org = db.get(Department, user.department_id).organization_id
            reports = [r for r in reports if r.organization_id == org]
        revisions = []
        for report in reports:
            for rev in db.scalars(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id).order_by(ActivityReportRevision.revision.desc())):
                pub = db.get(Publication, rev.publication_id)
                revisions.append({'id': rev.id, 'year': db.get(ReportingPeriod, report.period_id).year,
                    'revision': rev.revision, 'publication_version': pub.version,
                    'revision_reason': rev.revision_reason,
                    'organization': db.get(Organization, report.organization_id).name})
        publications = []
        if user.role == 'strategy':
            for pub in db.scalars(select(Publication).order_by(Publication.period_id, Publication.version.desc())):
                publications.append({'id': pub.id, 'year': db.get(ReportingPeriod, pub.period_id).year,
                    'version': pub.version, 'created_at': pub.created_at,
                    'valid': service.digest(pub.snapshot_json) == pub.sha256})
        return templates.TemplateResponse(request, 'activity_contract_index.html', {'user': user,
            'revisions': revisions, 'publications': publications,
            'organizations': db.scalars(select(Organization).order_by(Organization.name)).all() if user.role == 'strategy' else []})

    @app.post('/activity-reports/revisions')
    async def create_form(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await request.form()
        try:
            result = transact(db, user, 'activity_report_revision', 'activity_report_revision',
                lambda: service.create_report_revision(db, user, integer(data.get('publication_id')),
                    integer(data.get('organization_id')), integer(data['report_id']) if data.get('report_id') else None,
                    integer(data.get('expected_revision', 0)), data.get('revision_reason', '')))
            return RedirectResponse(f'/activity-reports/revisions/{result.id}', 303)
        except HTTPException as error:
            return ui_error(request, user, error, '/activity-reports')

    @app.get('/activity-reports/revisions/{revision_id}')
    def detail(revision_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        try:
            report = service.report_data(db, user, revision_id)
            pubs = db.scalars(select(Publication).where(Publication.period_id == db.get(ActivityReport, report['report_id']).period_id).order_by(Publication.version.desc())).all() if user.role == 'strategy' else []
            return templates.TemplateResponse(request, 'activity_contract_detail.html',
                {'user': user, 'report': report, 'publications': pubs})
        except HTTPException as error:
            return ui_error(request, user, error, '/activity-reports')

    @app.post('/api/activity-reports/indicators/{report_indicator_id}/evidence-files')
    async def upload_evidence(report_indicator_id: int, expected_revision: int = Form(...),
            source_index: int = Form(...), file: UploadFile = File(...),
            db: Session = Depends(get_db), user=Depends(require_user)):
        from .models import ActualRevision, ReportIndicator
        from .activity_evidence_service import MAX_FILE
        data = await file.read(MAX_FILE + 1)
        item = db.get(ReportIndicator, report_indicator_id)
        if not item:
            raise HTTPException(404, 'Rapor göstergesi bulunamadı. Güncel raporu açın.')
        binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
        service.authorize(user, binding.department_id)
        latest = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision.desc()))
        if not latest:
            raise HTTPException(422, 'Dosya için gerçekleşme kaydı bulunamadı. Önce kaynak satırını kaydedin.')
        result = transact(db, user, 'actual_revision_create', 'actual_revision', lambda: service.save_actual(db, user,
            report_indicator_id, expected_revision, str(latest.value) if latest.value is not None else None,
            latest.state, json.loads(latest.evidence_json), latest.explanation, json.loads(latest.deviation_json),
            uploads={source_index: (data, file.filename or '')}))
        return service.actual_data(result)

    @app.get('/api/activity-reports/indicators/{report_indicator_id}/evidence/{source_id}/{version}')
    def download_evidence(report_indicator_id: int, source_id: str, version: int,
            db: Session = Depends(get_db), user=Depends(require_user)):
        from . import activity_evidence_service as attachments
        row = transact(db, user, 'activity_evidence_access', 'activity_evidence_file',
            lambda: attachments.download(db, user, report_indicator_id, source_id, version))
        suffix = '.pdf' if row.filename.lower().endswith('.pdf') else '.xlsx'
        return Response(row.file_data,
            media_type='application/pdf' if suffix == '.pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="kanit-v{row.version}{suffix}"',
                     'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'private, no-store', 'X-Evidence-SHA256': row.sha256})

    @app.post('/activity-reports/indicators/{report_indicator_id}/actuals')
    async def actual_form(report_indicator_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        from .models import ActualRevision, ReportIndicator
        from .activity_evidence_service import MAX_FILE
        data = await request.form(max_files=30)
        back, item, evidence = '/activity-reports', None, []
        # Repeated fields preserve row order, including blank/invalid rows.
        titles, locators, revisions, identities = (data.getlist(k) for k in
            ('source_title', 'source_locator', 'source_revision', 'source_id'))
        for index in range(max(len(titles), len(locators), len(revisions), len(identities))):
            source = {k: values[index] if index < len(values) else '' for k, values in
                (('title', titles), ('locator', locators), ('source_revision', revisions))}
            if index < len(identities) and identities[index]:
                source['source_id'] = identities[index]
            evidence.append(source)
        uploads = {}
        try:
            for index, file in enumerate(data.getlist('source_file')):
                if hasattr(file, 'read') and file.filename:
                    uploads[index] = (await file.read(MAX_FILE + 1), file.filename)
            item = db.get(ReportIndicator, report_indicator_id)
            if not item:
                raise HTTPException(404, 'Rapor göstergesi bulunamadı. Güncel raporu açın.')
            back = f'/activity-reports/revisions/{item.report_revision_id}'
            binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
            service.authorize(user, binding.department_id)
            latest = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision.desc()))
            if latest and len(json.loads(latest.evidence_json)) > 1 and data.get('evidence_rows') != '1':
                raise HTTPException(422, 'Bu kayıtta birden fazla kanıt var. Güncel formu açıp tüm kaynak satırlarını kontrol edin.')
            try:
                parsed = parse_number(data.get('value', ''))
            except ValueError:
                raise HTTPException(422, {'message': 'Gerçekleşme alanındaki sayı okunamadı. Sayısal bir değer girin; örneğin 12.500,23. Ondalık için virgül kullanın.', 'field': 'value'}) from None
            # A sole untouched empty row represents no evidence, not a partial source.
            if len(evidence) == 1 and not uploads and not any(evidence[0].values()):
                evidence = []
            transact(db, user, 'actual_revision_create', 'actual_revision', lambda: service.save_actual(db, user,
                report_indicator_id, integer(data.get('expected_revision')), str(parsed) if parsed is not None else None,
                data.get('state', 'verified'), evidence, data.get('explanation', ''),
                {**(json.loads(latest.deviation_json) if latest else {}), 'corrective_action': data.get('corrective_action', '')}, uploads=uploads))
            return RedirectResponse(back, 303)
        except HTTPException as error:
            if item and error.status_code in {422, 409, 413}:
                report = service.report_data(db, user, item.report_revision_id)
                indicator = next(row for row in report['indicators'] if row['report_indicator_id'] == item.id)
                # Restore server-owned attachment lists; retain every attempted text value.
                previous_sources = {s.get('source_id'): s for r in report['indicators'] if r['report_indicator_id'] == item.id
                    for actual in r['actuals'] for s in actual['evidence'] if s.get('source_id')}
                for index, source in enumerate(evidence):
                    source['files'] = previous_sources.get(source.get('source_id'), {}).get('files', [])
                    if index in uploads:
                        source['attempted_filename'] = uploads[index][1]
                pubs = db.scalars(select(Publication).where(Publication.period_id == db.get(ActivityReport, report['report_id']).period_id).order_by(Publication.version.desc())).all() if user.role == 'strategy' else []
                detail = error.detail if isinstance(error.detail, dict) else {'message': error.detail}
                message = detail['message']
                field = detail.get('field', 'source_title' if any(k in str(message).lower() for k in ('kaynak', 'kanıt')) else 'state')
                return templates.TemplateResponse(request, 'activity_contract_detail.html',
                    {'user': user, 'report': report, 'publications': pubs,
                     'attempted_slot': report_indicator_id, 'attempted': dict(data), 'attempted_sources': evidence,
                     'form_error': f"{indicator['definition']['name']} — {message}", 'error_field': field, 'error_source_index': detail.get('source_index')}, status_code=error.status_code)
            return ui_error(request, user, error, back)

    @app.post('/activity-reports/revisions/{revision_id}/approve')
    def approve_form(revision_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        back = f'/activity-reports/revisions/{revision_id}'
        try:
            transact(db, user, 'activity_report_approve', 'activity_report_approval',
                     lambda: service.approve_report(db, user, revision_id))
            return RedirectResponse(back, 303)
        except HTTPException as error:
            return ui_error(request, user, error, back)

    @app.get('/activity-reports/publications/{publication_id}/bindings')
    def bindings_form(publication_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        service.strategy(user)
        pub, payload = service.checked_publication(db, publication_id)
        bound = set(db.scalars(select(PublicationIndicatorBinding.snapshot_indicator_id).where(PublicationIndicatorBinding.publication_id == pub.id)))
        rows = list(service.snapshot_rows(payload).values())
        for row in rows:
            row['bound'] = row['id'] in bound
            row['organization_id'] = db.get(Department, row['department_id']).organization_id
        from .models import IndicatorDefinitionRevision
        identities = []
        for identity in db.scalars(select(IndicatorIdentity).order_by(IndicatorIdentity.indicator_id)):
            definition = db.scalar(select(IndicatorDefinitionRevision).where(IndicatorDefinitionRevision.indicator_id == identity.indicator_id).order_by(IndicatorDefinitionRevision.revision.desc()))
            if definition:
                metadata = json.loads(definition.definition_json)
                identities.append({'indicator_id': identity.indicator_id, 'organization_id': identity.organization_id,
                    'label': f"{metadata['name']} · {metadata['unit']} · {metadata['year']} · Tanım sürümü {definition.revision}"})
        return templates.TemplateResponse(request, 'activity_contract_bindings.html', {'user': user,
            'publication': pub, 'year': payload['period'], 'rows': rows,
            'identities': identities})

    @app.post('/activity-reports/publications/{publication_id}/bindings')
    async def bind_form(publication_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await request.form()
        back = f'/activity-reports/publications/{publication_id}/bindings'
        try:
            transact(db, user, 'publication_indicator_bind', 'publication_indicator_binding',
                lambda: service.bind_legacy_indicator(db, user, publication_id, integer(data.get('snapshot_indicator_id')),
                    data.get('indicator_id') or None, data.get('reason', '')))
            return RedirectResponse(back, 303)
        except HTTPException as error:
            return ui_error(request, user, error, back)
