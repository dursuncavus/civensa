"""AR-10: fail-closed legal text, owned variables and immutable freeze metadata."""
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import select
from . import activity_sections_service as sections
from .assurance_models import AssuranceStatement
from .models import Department, DepartmentScope, ReportingPeriod
from .structure_service import period_name
from .activity_contract_service import canonical

ASSET_PATH = Path(__file__).parent / 'legal' / 'assurance_statements_2025.json'
FILE_SHA256 = '116c9b8c4b3aca362bdd13b4b81cf6155f4903c5d7d592a0a0edc3afc0692c50'
VERSION_ID = 'KIKY-RG-2025-03-05-32832'
INTEGRITY_ERROR = ('Güvence beyanlarının kilitli metni doğrulanamadı: '
    'app/legal/assurance_statements_2025.json. Dondurma ve yayımlama durduruldu. '
    'Sistem sorumlusundan doğrulanmış dosyayı geri yükleyip uygulamayı yeniden başlatmasını isteyin.')
LOCK_ERROR = ('Güvence beyanının metni, başlığı, dipnotları ve imza alanı değiştirilemez. '
    'EKLER beyan formunda yalnızca yer, tarih, görev dönemleri ve gerekçeli çekinceleri düzenleyin.')
_startup_error = ''


def asset():
    try:
        raw = ASSET_PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest() != FILE_SHA256:
            return None
        return json.loads(raw)
    except (OSError, ValueError):
        return None


def check_startup():
    global _startup_error
    _startup_error = '' if asset() else INTEGRITY_ERROR
    return _startup_error


def integrity_error():
    return _startup_error or ('' if asset() else INTEGRITY_ERROR)


def require_integrity():
    if integrity_error():
        sections.fail(INTEGRITY_ERROR, 409)


def codes(doc):
    return ('EK-2',) if doc.department_id else ('EK-1', 'EK-3')


def can_edit(db, user, doc, code):
    if not user.is_active or code not in codes(doc):
        return False
    if code == 'EK-1':
        return user.role == 'strategy'
    if code == 'EK-2':
        return user.role == 'department' and user.department_id == doc.department_id
    return (user.role == 'department' and sections.finance(db, user)
            and sections.document(db, user, doc.id).organization_id == doc.organization_id)


def empty_variables():
    return {'place': '', 'date': '', 'signatories': [], 'reservations': []}


def text(value, label, limit=300):
    if not isinstance(value, str) or len(value) > limit:
        sections.fail(f'{label}: Alan biçimi veya uzunluğu geçersiz. En fazla {limit} karakterlik metin girin.')
    return value.strip()


def exact_fields(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        sections.fail(LOCK_ERROR)


def day(raw, label):
    try:
        if not isinstance(raw, str) or len(raw) != 10:
            raise ValueError
        parsed = date.fromisoformat(raw)
        if parsed.isoformat() != raw:
            raise ValueError
        return parsed
    except (TypeError, ValueError):
        sections.fail(f'{label}: Tarih okunamadı. Yıl-ay-gün biçiminde geçerli bir tarih girin.')


def validate_variables(raw, year, code):
    exact_fields(raw, ('place', 'date', 'signatories', 'reservations'))
    result = {'place': text(raw['place'], 'Yer'), 'date': text(raw['date'], 'Tarih', 10)}
    if result['date'] and day(result['date'], 'Beyan tarihi').year < year:
        sections.fail('Beyan tarihi rapor yılından önce olamaz. Rapor yılı veya sonraki bir tarihi seçin.')
    periods = raw['signatories']
    if not isinstance(periods, list) or len(periods) > 100:
        sections.fail('İmzalayan görev dönemleri geçersiz. En fazla 100 görev dönemi girin.')
    normalized = []
    people = {}
    for item in periods:
        exact_fields(item, ('person_ref', 'name', 'title', 'start_date', 'end_date'))
        item = {key: text(value, 'İmzalayan / görev dönemi') for key, value in item.items()}
        if not all(item.values()):
            sections.fail('İmzalayan kaydı eksik. Kişi kodu, Ad-Soyad, Ünvan ve görev başlangıç/bitiş tarihlerini doldurun.')
        start, end = day(item['start_date'], 'Görev başlangıcı'), day(item['end_date'], 'Görev bitişi')
        if start > end or start.year != year or end.year != year:
            sections.fail(f'Görev dönemi geçersiz. Başlangıç ve bitişi {year} yılı içinde, tarih sırasıyla girin.')
        identity = item['person_ref'].casefold()
        if identity in people and people[identity] != item['name']:
            sections.fail('Aynı kişi kodunda farklı Ad-Soyad var. Kişi kodunu ve adı kontrol edin.')
        people[identity] = item['name']
        normalized.append(item)
    normalized.sort(key=lambda item: item['start_date'])
    if any(a['end_date'] >= b['start_date'] for a, b in zip(normalized, normalized[1:])):
        sections.fail('İmzalayan görev dönemleri çakışıyor. Her gün için tek görevli olacak şekilde dönemleri düzeltin.')
    result['signatories'] = normalized
    reservations = raw['reservations']
    if not isinstance(reservations, list) or len(reservations) > 100:
        sections.fail('Çekince listesi geçersiz. En fazla 100 gerekçeli madde girin.')
    if code == 'EK-3' and reservations:
        sections.fail('EK-3 beyanında çekince alanı bulunmaz. Çekinceleri bu beyandan kaldırın.')
    result['reservations'] = []
    for item in reservations:
        exact_fields(item, ('text', 'justification'))
        cleaned = {key: text(value, 'Çekince / gerekçe', 10000) for key, value in item.items()}
        if not all(cleaned.values()):
            sections.fail('Çekince veya gerekçesi boş. Her çekinceyi somut olarak yazın ve gerekçesini doldurun.')
        result['reservations'].append(cleaned)
    return result


def predecessor(variables, code):
    return code != 'EK-3' and len({p['person_ref'].casefold() for p in variables['signatories']}) > 1


def missing_fields(variables, year, active_to=None, department_name=''):
    missing = []
    if not variables['place']: missing.append('Yer alanını doldurun.')
    if not variables['date']: missing.append('Beyan tarihini doldurun.')
    periods = variables['signatories']
    required_end = active_to or date(year, 12, 31)
    next_day = date(year, 1, 1)
    for person in periods:
        start, end = day(person['start_date'], 'Görev başlangıcı'), day(person['end_date'], 'Görev bitişi')
        if start > next_day:
            break
        next_day = max(next_day, end + timedelta(days=1))
        if next_day > required_end:
            break  # No signatory coverage is required after the closure day.
    if next_day <= required_end:
        if active_to:
            missing.append(f'{department_name}: Müdürlük {active_to.strftime("%d.%m.%Y")} tarihinde kapandı/birleşti. '
                f'EK-2 Harcama yetkilisi görev dönemleri {year} yılı başından kapanış tarihine kadar kesintisiz olmalıdır. '
                f'EKLER → EK-2 beyan formunda 01.01.{year}–{active_to.strftime("%d.%m.%Y")} arasındaki eksik '
                'görev dönemlerinin Ad-Soyad, Ünvan, başlangıç ve bitiş tarihlerini tamamlayın.')
        elif not periods:
            missing.append('İmzalayanın Ad-Soyad, Ünvan ve rapor yılındaki görev dönemlerini girin.')
        else:
            missing.append('İmzalayan görev dönemleri rapor yılının tamamını kapsamıyor. Eksik dönemleri tamamlayın.')
    return missing


def record_data(record):
    return {'code': record.code, 'version_id': record.version_id, 'file_sha256': record.file_sha256,
            'variables': json.loads(record.variables_json)}


def slot(db, doc, row, frozen=False):
    """Single EKLER hook for live completeness and the frozen variable snapshot."""
    error = integrity_error()
    year = db.get(ReportingPeriod, doc.period_id).year
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == doc.period_id,
        DepartmentScope.department_id == doc.department_id)) if doc.department_id else None
    active_to = scope.active_to if scope and scope.active_to and scope.active_to.year == year else None
    department_name = period_name(db, doc.period_id, db.get(Department, doc.department_id)) if active_to else ''
    if frozen:
        placed = {item['code']: item for item in row.get('assurances', [])}
    else:
        placed = {r.code: record_data(r) for r in db.scalars(
            select(AssuranceStatement).where(AssuranceStatement.document_id == doc.id))}
    items, missing = [], []
    for code in codes(doc):
        item = placed.get(code)
        problems = []
        if item is None:
            item = {'code': code, 'version_id': None, 'file_sha256': None, 'variables': empty_variables()}
            problems.append('Beyan henüz yerleştirilmedi. Yetkili birim beyan alanlarını kaydetmelidir.')
        elif item['version_id'] != VERSION_ID or item['file_sha256'] != FILE_SHA256:
            problems.append('Beyanın sürüm veya dosya doğrulama kodu uyuşmuyor. Sistem sorumlusuyla iletişime geçin.')
        problems.extend(missing_fields(item['variables'], year, active_to=active_to if code == 'EK-2' else None,
                                       department_name=department_name))
        # Snapshot the resolved legal text together with the entered variables.
        # Existing freezes retain any view already stored; never replace it with live text.
        item = dict(item)
        if 'rendered' not in item:
            item['rendered'] = view(item)
        items.append(item)
        missing.extend(f'{code}: {problem}' for problem in problems)
    if error: missing.insert(0, error)
    row.update(assurances=items, missing=missing, blocks=[], reason='', copied_needs_review=False,
               status=('empty' if not placed else 'draft') if missing else 'ready')
    return row


def view(item):
    """Always resolve body/labels/notes from the verified asset, including frozen views."""
    legal = asset()
    if integrity_error() or legal is None:
        return {'error': INTEGRITY_ERROR, 'code': item['code']}
    if item['version_id'] not in {None, VERSION_ID} or item['file_sha256'] not in {None, FILE_SHA256}:
        return {'error': 'Beyan sürümü doğrulanamadı. Sistem sorumlusuyla iletişime geçin.', 'code': item['code']}
    statement = next(s for s in legal['statements'] if s['code'] == item['code'])
    variables = item['variables']
    paragraphs = list(statement['paragraphs'])
    inserted = predecessor(variables, item['code'])
    if inserted:
        anchor = statement['footnote_anchor_paragraph']
        # Preserve the entire official sentence and exact mandated noun phrase.
        paragraphs[anchor] = (paragraphs[anchor][:-1] + ' ve ' + statement['predecessor_phrase']
                              + ' ile desteklenmektedir.')
    signer = variables['signatories'][-1] if variables['signatories'] else {}
    return {**statement, 'paragraphs': paragraphs, 'variables': variables,
            'name': signer.get('name', ''), 'title_value': signer.get('title', ''),
            'signature': '', 'predecessor_inserted': inserted, 'error': '',
            'date_display': date.fromisoformat(variables['date']).strftime('%d.%m.%Y') if variables['date'] else ''}


def save(db, user, document_id, code, payload):
    doc = sections.document(db, user, document_id)
    if code not in codes(doc):
        sections.fail('Beyan bu rapor türüne ait değil. Birim için EK-2, idare için EK-1 veya EK-3 seçin.', 422)
    if not can_edit(db, user, doc, code):
        sections.fail('Bu beyanı düzenleme yetkiniz yok. EK-2 için ilgili müdürlük, EK-1 için Strateji, EK-3 için Mali Hizmetler hesabını kullanın.', 403)
    exact_fields(payload, ('expected_revision', 'variables'))
    revision = payload['expected_revision']
    if type(revision) is not int or revision < 0:
        sections.fail('Rapor sürümü geçersiz. Sayfayı yenileyip değişiklikleri yeniden kaydedin.')
    sections.writable(db, user, doc, revision)
    require_integrity()
    variables = validate_variables(payload['variables'], db.get(ReportingPeriod, doc.period_id).year, code)
    record = db.scalar(select(AssuranceStatement).where(
        AssuranceStatement.document_id == doc.id, AssuranceStatement.code == code))
    before = record_data(record) if record else None
    if record is None:
        record = AssuranceStatement(document_id=doc.id, code=code)
        db.add(record)
    record.version_id = VERSION_ID
    record.file_sha256 = FILE_SHA256
    record.variables_json = canonical(variables)
    after = record_data(record)
    sections.event(db, user, doc, 'EKLER', 'assurance_save', before, after)
    old_variables = before['variables'] if before else empty_variables()
    for field, action in (('signatories', 'assurance_signatories'), ('reservations', 'assurance_reservations')):
        if old_variables[field] != variables[field]:
            sections.event(db, user, doc, 'EKLER', action,
                           {'code': code, field: old_variables[field]}, {'code': code, field: variables[field]})
    if predecessor(old_variables, code) != predecessor(variables, code):
        sections.event(db, user, doc, 'EKLER', 'assurance_predecessor',
                       {'code': code, 'inserted': predecessor(old_variables, code)},
                       {'code': code, 'inserted': predecessor(variables, code),
                        'sentence': view(after)['paragraphs'][3]})
    doc.revision += 1
    db.flush()
    return doc
