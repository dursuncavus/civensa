"""Turkish PP errors and request-local, server-rendered form recovery."""
from functools import wraps
from html import escape
from html.parser import HTMLParser
from http import HTTPStatus

from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from markupsafe import Markup
from starlette.exceptions import HTTPException as StarletteHTTPException

LABELS = {
    'period_id': 'Raporlama dönemi', 'department_id': 'Müdürlük', 'id': 'Kayıt',
    'subprogram_id': 'Alt program', 'card_id': 'Performans kartı', 'record_id': 'Atanacak kayıt',
    'kind': 'Kayıt türü', 'position': 'Sıra', 'name': 'Gösterge adı', 'unit': 'Ölçü birimi',
    'title': 'Bölüm başlığı', 'content': 'Bölüm içeriği', 'placement': 'Bölüm konumu',
    'image': 'Bölüm görseli', 'amount': 'Tutar', 'value': 'Gösterge değeri',
    'value_kind': 'Değer türü', 'program_group': 'Program grubu', 'funding_type': 'Bütçe kaynağı',
    'publish': 'Nihai yayın', 'status': 'Müdürlük kapsamı', 'reason': 'Gerekçe',
    'department_ids': 'Sorumlu müdürlükler', 'official_ids': 'Resmî faaliyet bağlantısı',
    'request': 'Performans programı isteği', 'format': 'Dosya biçimi',
}
DEFAULTS = {
    401: 'Oturum doğrulanamadı. Yeniden giriş yapın.',
    403: 'Bu kayıt için işlem yetkiniz yok. Kaydın müdürlüğünü ve yetkili hesabınızı kontrol edin.',
    404: 'İstenen kayıt veya sayfa bulunamadı. Dönem ve kayıt bağlantısını kontrol edin.',
    405: 'Bu sayfada istenen işlem kullanılamıyor. Ekranı yeniden açıp ilgili işlem düğmesini kullanın.',
    422: 'Alan bilgisi geçersiz. İşaretli alanı düzeltip yeniden kaydedin.',
}


def pp_error(status, message=None, field='request'):
    """One status/detail/field contract, also usable by domain services."""
    message = message or DEFAULTS.get(status, 'Kayıt işlenemedi. Sayfayı yenileyip tekrar deneyin.')
    exc = HTTPException(status, message)
    exc.pp_errors = [{'field': field, 'message': message}]
    return exc


def payload(exc):
    if hasattr(exc, 'pp_errors'):
        return {'detail': exc.detail, 'errors': exc.pp_errors}
    detail = exc.detail
    if not detail or detail in [s.phrase for s in HTTPStatus] or detail == 'Not authenticated':
        detail = DEFAULTS.get(exc.status_code, DEFAULTS[422])
    if isinstance(detail, list):
        detail = ' '.join(str(item) for item in detail)
    message = str(detail)
    # Preserve existing Turkish explanations; add the missing recovery step.
    actions = ('edin', 'girin', 'seçin', 'açın', 'başvurun', 'yazın', 'kaydedin',
               'deneyin', 'isteyin', 'kaldırın', 'düzeltin', 'tamamlayın', 'karşılaştırın')
    if exc.status_code in DEFAULTS and not any(action in message.lower() for action in actions):
        message += ' İlgili alanı veya kaydı kontrol edip yeniden deneyin.'
    return {'detail': message, 'errors': [{'field': 'request', 'message': message}]}


def is_pp_path(path):
    return any(path == p or path.startswith(p + '/') for p in (
        '/program', '/report-builder', '/publications', '/department', '/review',
        '/structure', '/activity-mapping', '/dashboard', '/export/department',
        '/period', '/periods', '/api/indicators', '/api/activities',
        '/api/departments', '/api/submissions', '/api/activity-mappings', '/api/periods',
        '/api/import-batches', '/api/template-snapshots',
    )) or path.startswith('/publications/')


def wants_json(request):
    return request.url.path.startswith('/api/') or 'application/json' in request.headers.get('accept', '')


def install(app, templates):
    templates.env.filters['pp_form'] = retain_form

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        if not is_pp_path(request.url.path) or exc.status_code < 400:
            return await http_exception_handler(request, exc)
        body = payload(exc)
        if wants_json(request) or 'text/html' not in request.headers.get('accept', ''):
            return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)
        return templates.TemplateResponse(request, 'pp_error.html', body,
            status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        if not is_pp_path(request.url.path):
            return await request_validation_exception_handler(request, exc)
        errors = []
        for issue in exc.errors():
            field = str(issue.get('loc', ('request',))[-1])
            message = f'{LABELS.get(field, "Kayıt alanı")} geçersiz. Alan biçimini ve seçilen kaydı kontrol edip yeniden deneyin.'
            errors.append({'field': field, 'message': message})
        body = {'detail': ' '.join(e['message'] for e in errors), 'errors': errors}
        if wants_json(request):
            return JSONResponse(body, status_code=422)
        return templates.TemplateResponse(request, 'pp_error.html', body, status_code=422)


def recover_form(screen):
    """Catch form validation only; permission/workflow/period conflicts retain their status."""
    def decorate(endpoint):
        @wraps(endpoint)
        async def wrapped(*args, **kwargs):
            request, db = kwargs['request'], kwargs['db']
            data = await request.form()
            try:
                return await endpoint(*args, **kwargs)
            except HTTPException as exc:
                if exc.status_code != 422:
                    raise
                db.rollback()
                body = payload(exc)
                if wants_json(request):
                    return JSONResponse(body, status_code=422)
                request.state.pp_attempt = (request.url.path, data, body)
                response = screen(request, db, kwargs['user'], kwargs.get('department_id'), data)
                response.status_code = 422
                return response
        return wrapped
    return decorate


class Controls(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.action = None
        self.hidden = {}
        self.feed(str(html))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.action = attrs.get('action')
        if tag == 'input' and attrs.get('type') == 'hidden':
            self.hidden[attrs.get('name')] = attrs.get('value', '')


def retain_form(html, request):
    """Jinja filter: bind attempted controls only in the submitted form.

    Hidden record keys distinguish repeated forms. CSRF always comes from the
    current session. Values are escaped as text, never interpreted as markup.
    File controls cannot be populated by browsers; their message asks to reselect.
    """
    attempt = getattr(request.state, 'pp_attempt', None)
    if not attempt:
        return html
    path, data, body = attempt
    controls = Controls(html)
    if controls.action != path:
        return html
    for key in ('id', 'kind', 'record_id', 'activity_id', 'department_id'):
        if key in controls.hidden and controls.hidden[key] != str(data.get(key, '')):
            return html
    if 'id' in data and 'id' not in controls.hidden:
        return html
    parser = RetainedControls(data, body)
    parser.feed(str(html))
    return Markup(''.join(parser.output))


class RetainedControls(HTMLParser):
    def __init__(self, data, body):
        super().__init__(convert_charrefs=False)
        self.data, self.body = data, body
        self.output = []
        self.textarea = None
        self.select = None
        self.options = set()
        self.messages = {e['field']: e['message'] for e in body['errors']}

    def emit(self, tag, attrs, closed=False):
        attributes = ''.join(' ' + k + ('="' + escape(str(v), quote=True) + '"' if v is not None else '') for k, v in attrs.items())
        self.output.append('<' + tag + attributes + (' />' if closed else '>'))

    def field_error(self, name):
        if name in self.messages:
            self.output.append('<span class="field-error" role="alert" id="pp-error-' + escape(name, quote=True) + '">' + escape(self.messages[name]) + '</span>')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get('name')
        if name in self.messages:
            attrs.update({'aria-invalid': 'true', 'aria-describedby': 'pp-error-' + name})
        if tag == 'form':
            self.emit(tag, attrs)
            self.output.append('<div class="return-note" role="alert">' + escape(self.body['detail']) + '</div>')
            return
        if tag == 'input' and name != 'csrf_token' and name in self.data:
            kind = attrs.get('type', 'text')
            if kind in {'checkbox', 'radio'}:
                attrs.pop('checked', None)
                if attrs.get('value', 'on') in self.data.getlist(name):
                    attrs['checked'] = None
            elif kind != 'file':
                attrs['value'] = self.data[name]
                # Invalid numeric spellings must remain visible in browsers too.
                if kind == 'number':
                    attrs['type'] = 'text'
                    attrs['inputmode'] = 'numeric'
        if tag == 'textarea':
            self.textarea = name if name in self.data else None
        if tag == 'select':
            self.select = name
            self.options = set()
        if tag == 'option' and self.select:
            attrs.pop('selected', None)
            value = attrs.get('value', '')
            self.options.add(value)
            if value in self.data.getlist(self.select):
                attrs['selected'] = None
        self.emit(tag, attrs)
        if tag == 'input':
            self.field_error(name)
            if attrs.get('type') == 'file' and getattr(self.data.get(name), 'filename', ''):
                self.output.append('<span class="field-error">Görsel dosyasını yeniden seçip kaydedin.</span>')
        if tag == 'textarea' and self.textarea:
            # HTML strips one initial textarea newline; supply it explicitly.
            self.output.append('\n' + escape(str(self.data[self.textarea])))

    def handle_endtag(self, tag):
        name = self.textarea if tag == 'textarea' else self.select if tag == 'select' else None
        if tag == 'select' and self.select:
            for value in self.data.getlist(self.select):
                if value not in self.options:
                    self.emit('option', {'value': value, 'selected': None})
                    self.output.append(escape(str(value)) + '</option>')
            self.select = None
        if tag == 'textarea':
            self.textarea = None
        self.output.append('</' + tag + '>')
        self.field_error(name)

    def handle_data(self, data):
        if not self.textarea:
            self.output.append(data)

    def handle_entityref(self, name):
        if not self.textarea:
            self.output.append('&' + name + ';')

    def handle_charref(self, name):
        if not self.textarea:
            self.output.append('&#' + name + ';')
