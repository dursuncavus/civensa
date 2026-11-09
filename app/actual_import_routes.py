"""Strateji-only annual actual workbook UI on the existing report screen."""
import json
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from .db import get_db
from . import actual_import_service as service
from .activity_contract_errors import render_error


def register(app):
    from .main import require_user, templates

    @app.post('/activity-reports/imports/preview')
    async def preview(request: Request, db=Depends(get_db), user=Depends(require_user)):
        try:
            service.contract.strategy(user)
            form = await request.form()
            try:
                revision_id = int(form.get('revision_id', ''))
            except (TypeError, ValueError):
                service.fail('Rapor revizyonu seçilmedi. 2026 raporunu seçip yeniden yükleyin.')
            file = form.get('file')
            if not hasattr(file, 'read'):
                service.fail('Excel dosyası seçilmedi. XLSX dosyasını seçip yeniden yükleyin.')
            record = service.preview_import(db, user, revision_id, await file.read(service.MAX_FILE + 1))
            db.commit()
            return RedirectResponse(f'/activity-reports/imports/{record.id}', 303)
        except HTTPException as error:
            db.rollback()
            return render_error(request, user, error, '/activity-reports')

    @app.get('/activity-reports/imports/{import_id}')
    def detail(import_id: int, request: Request, db=Depends(get_db), user=Depends(require_user)):
        try:
            record, preview = service.import_preview(db, user, import_id)
            return templates.TemplateResponse(request, 'actual_import.html', {'user': user, 'record': record,
                'preview': preview, 'result': json.loads(record.result_json) if record.result_json else None})
        except HTTPException as error:
            return render_error(request, user, error, '/activity-reports')

    @app.post('/activity-reports/imports/{import_id}/apply')
    async def apply(import_id: int, request: Request, db=Depends(get_db), user=Depends(require_user)):
        try:
            service.contract.strategy(user)
            form = await request.form()
            _, preview = service.import_preview(db, user, import_id)
            choices = {}
            for row in preview['rows']:
                line = row['line']
                selected = form.get(f'choice_{line}', '')
                if selected:
                    try:
                        indicator_id, scale = selected.split(':')
                        choices[str(line)] = {'indicator_id': int(indicator_id), 'scale': scale, 'confirmed': True}
                    except (ValueError, TypeError):
                        service.fail(f'{line}. satır seçimi okunamadı. Önizlemeden yeniden seçin.')
            try:
                expected = int(form.get('expected_revision', ''))
            except (TypeError, ValueError):
                service.fail('Rapor sürümü okunamadı. Dosyayı yeniden önizleyin.')
            service.apply_import(db, user, import_id, expected, choices)
            db.commit()
            return RedirectResponse(f'/activity-reports/imports/{import_id}', 303)
        except (IntegrityError, OperationalError):
            db.rollback()
            return render_error(request, user, HTTPException(409,
                'İçe aktarma başka bir işlemle çakıştı. Son gerçekleşmeleri kontrol edip yeniden önizleyin.'), '/activity-reports')
        except HTTPException as error:
            db.rollback()
            return render_error(request, user, error, '/activity-reports')
