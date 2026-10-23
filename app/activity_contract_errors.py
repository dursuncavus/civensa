"""Legacy AR adapter for shared Turkish validation and form recovery."""
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.datastructures import FormData

from .activity_sections_routes import TurkishValidationRoute
from .pp_errors import payload

LABELS = {
    'publication_id': 'Baz program yayını', 'organization_id': 'Kurum',
    'report_id': 'Faaliyet raporu', 'revision_id': 'Rapor revizyonu',
    'expected_revision': 'Beklenen kayıt sürümü', 'revision_reason': 'Revizyon gerekçesi',
    'report_indicator_id': 'Rapor göstergesi', 'value': 'Gerçekleşme değeri',
    'state': 'Veri durumu', 'evidence': 'Kanıt kaynakları', 'explanation': 'Açıklama',
    'deviation': 'Sapma bilgisi', 'corrective_action': 'Düzeltici işlem',
    'snapshot_indicator_id': 'Yayındaki gösterge', 'indicator_id': 'Kalıcı gösterge kimliği',
    'period_indicator_id': 'Dönem göstergesi', 'reason': 'Eşleme gerekçesi',
    'source_index': 'Kaynak satırı', 'source_id': 'Kaynak kimliği',
    'source_title': 'Kaynak adı', 'source_locator': 'Kaynak konumu',
    'source_revision': 'Kaynak sürümü', 'title': 'Kaynak adı', 'locator': 'Kaynak konumu',
    'file': 'Kanıt dosyası', 'source_file': 'Kanıt dosyası', 'version': 'Dosya sürümü',
    'evidence_rows': 'Kaynak satırları',
}


def error_detail(error):
    detail = error.detail
    message = detail.get('message', '') if isinstance(detail, dict) else detail
    message = payload(HTTPException(error.status_code, message))['detail']
    field = detail.get('field') if isinstance(detail, dict) else None
    label = LABELS.get(field, 'Faaliyet raporu')
    if not str(message).casefold().startswith(label.casefold()):
        message = f'{label}: {message}'
    return {**detail, 'message': message} if isinstance(detail, dict) else message


def render_error(request, user, error, back, attempted=None):
    from .main import templates
    detail = error_detail(error)
    # Files and CSRF tokens must never be replayed as text or stale hidden values.
    data = attempted if attempted is not None else getattr(request, '_form', None)
    items = [(key, value) for key, value in (data.multi_items() if data else [])
             if isinstance(value, str) and key != 'csrf_token']
    return templates.TemplateResponse(request, 'activity_contract_error.html', {
        'user': user, 'message': detail.get('message') if isinstance(detail, dict) else detail,
        'blockers': detail.get('blockers', []) if isinstance(detail, dict) else [],
        'back': back, 'attempted_items': items, 'field_labels': LABELS,
    }, status_code=error.status_code)


class LegacyTurkishValidationRoute(TurkishValidationRoute):
    """Extend the sections validator with legacy labels and HTML recovery.

    Use the raw APIRoute handler so validation locations are still available;
    the sections handler translates them immediately using section-only labels.
    """
    def get_route_handler(self):
        original = APIRoute.get_route_handler(self)

        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError as validation:
                fields = []
                for issue in validation.errors():
                    parts = [f'{part + 1}. satır' if isinstance(part, int) else LABELS.get(part, 'İstek alanı')
                             for part in issue.get('loc', ()) if part not in {'body', 'query', 'path'}]
                    fields.append('İstek içeriği' if issue['type'] == 'json_invalid' else (' / '.join(parts) or 'İstek içeriği'))
                message = ('Faaliyet raporu isteği işlenemedi. ' + ', '.join(dict.fromkeys(fields)) +
                           ': Alan biçimi geçersiz. Kayıt ve sürüm için tam sayı, gerçekleşme için ondalık metin kullanın; '
                           'işaretli alanları düzeltip yeniden gönderin.')
                error = HTTPException(422, message)
            except HTTPException as caught:
                error = caught
            if error.status_code < 400:
                raise error
            detail = error_detail(error)
            if (request.url.path.startswith('/api/') or 'application/json' in request.headers.get('accept', '')
                    or (request.method != 'POST' and 'text/html' not in request.headers.get('accept', ''))):
                return JSONResponse({'detail': detail, 'message': detail.get('message') if isinstance(detail, dict) else detail},
                                    status_code=error.status_code, headers=error.headers)
            # Validation can fail before the endpoint reads the form.
            attempted = await request.form() if request.method == 'POST' else FormData()
            return render_error(request, getattr(request.state, 'contract_user', None), error,
                                '/activity-reports', attempted)
        return handler
