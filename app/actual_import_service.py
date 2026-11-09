"""CIV-192 staged, explicitly confirmed annual indicator actual imports."""
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from difflib import SequenceMatcher
from itertools import islice
from zipfile import ZipFile, BadZipFile
from xml.etree.ElementTree import ParseError
from lxml.etree import XMLSyntaxError
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from fastapi import HTTPException
from sqlalchemy import select
from . import activity_contract_service as contract, structure_service
from .config import attachment_max_bytes
from .models import ActualImport, ActualRevision, AuditLog

MAX_FILE = attachment_max_bytes()
TTL = timedelta(hours=24)
PREVIEW_VERSION = 3
HEADERS = {
    'department': ('Sorumlu Müdürlük', 'Müdürlük'),
    'name': ('Gösterge Adı', 'Performans Göstergesi', 'Performans Gösterge Adı', 'PERFORMANS \nGÖSTERLERİ'),
    'method': ('Hesaplama Yöntemi',),
    'unit': ('Birim', 'Birimi', 'Ölçü Birimi', 'GÖST.\nBİRİMİ'),
    'q4_total': ('2026 YILI 4. ÇEYREK GERÇEKLEŞEN TOPLAMI', 'Q4 Gerçekleşen Toplamı'),
    'strategy_ratio': ('2026 YILI TOPLAMI',),
    **{f'q{i}': (f'2026 Q{i}', f'2026 {i}. Çeyrek', f'2026 {i}. Çeyrek Gerçekleşen',
                   f'2026 {i}. Çeyrek Gerçekleşme', f'2026 Yılı {i}. Çeyrek',
                   f'{i}. Çeyrek', f'{i}. Çeyrek Gerçekleşen') for i in range(1, 5)},
    'explanation': ('Açıklama',),
}


def fail(message, code=422):
    raise HTTPException(code, message)


def normalized(value):
    text = unicodedata.normalize('NFKC', str(value or '')).translate(str.maketrans({'İ':'i', 'I':'ı'})).casefold()
    text = text.replace('ı', 'i')
    return ' '.join(re.sub(r'[_\W]+', ' ', text, flags=re.UNICODE).split())


def indicator_name(value):
    text = str(value or '').strip()
    text = re.sub(r'^\s*(?:(?:S\.?\s*H|P\.?\s*G)\s*[.:_\-]?\s*\d+'
                  r'(?:\s*[.\-/]\s*\d+)*\s*[:.,;/\-–—)]*\s*)+', '', text, flags=re.I)
    return normalized(text)


def numeric(value):
    # Text (including "%" and uncached formulas), booleans and blanks are not numbers.
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    result = Decimal(str(value))
    return result if result.is_finite() else None


def workbook_rows(data, data_only):
    book = load_workbook(io.BytesIO(data), read_only=True, data_only=data_only, keep_links=False)
    try:
        if 'veriler' not in book.sheetnames:
            fail('Excel içinde veriler sayfası yok. Ana çalışma kitabının veriler sayfasını koruyup yeniden yükleyin.')
        sheet = book['veriler']
        if (sheet.max_row or 0) > 5001 or (sheet.max_column or 0) > 100:
            fail('veriler sayfası çok büyük. En fazla 5.000 satır ve 100 sütunla yeniden yükleyin.')
        rows = list(islice(sheet.iter_rows(values_only=data_only), 5002))
        if len(rows) > 5001 or any(len(r) > 100 for r in rows):
            fail('veriler sayfası çok büyük. En fazla 5.000 satır ve 100 sütunla yeniden yükleyin.')
        return rows
    finally:
        book.close()


def header_matches(key, value, labels):
    if normalized(value) in {normalized(label) for label in labels}:
        return True
    if re.fullmatch(r'q[1-4]', key):
        # Only a bare year/quarter heading may lose its month annotation. The
        # Q4 total and performance-evaluation headings must remain distinct.
        bare = normalized(re.sub(r'\([^)]*\)', '', str(value or '')))
        return bare in {f'2026 yili {key[1]} çeyrek', f'2026 {key[1]} çeyrek'}
    return False


def read_rows(data):
    if len(data) > MAX_FILE:
        fail(f'Excel dosyası çok büyük. En fazla {MAX_FILE // (1024*1024)} MB XLSX yükleyin.')
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 50*1024*1024:
                fail('Excel açılmış boyutu çok büyük. Daha küçük bir XLSX dosyası yükleyin.')
        rows = workbook_rows(data, True)
        formula_rows = workbook_rows(data, False)
    except (BadZipFile, ValueError, KeyError, TypeError, OSError, ParseError, XMLSyntaxError, InvalidFileException):
        fail('Excel dosyası okunamadı. Geçerli XLSX dosyasını seçip yeniden yükleyin.')
    headers = rows[0] if rows else []
    columns = {}
    for key, labels in HEADERS.items():
        matches = [i for i, h in enumerate(headers) if header_matches(key, h, labels)]
        if not matches and key in {'explanation', 'strategy_ratio'}:
            continue
        if len(matches) != 1:
            fail(f'veriler sayfasında {labels[0]} başlığı eksik veya yinelenmiş. Başlığı düzeltip yeniden yükleyin.')
        columns[key] = matches[0]
    result = []
    for line, (row, cells) in enumerate(zip(rows[1:], formula_rows[1:], strict=True), 2):
        if not any(v is not None for v in row) and not any(c.data_type == 'f' for c in cells):
            continue
        values = {k: row[i] if i < len(row) else None for k, i in columns.items()}
        values['formulas'] = {key: {'formula': cells[i].value,
            'cached_numeric': numeric(values[key]) is not None}
            for key, i in columns.items() if i < len(cells) and cells[i].data_type == 'f'}
        result.append((line, values))
    return result


def method_value(row):
    quarters = [numeric(row[f'q{i}']) for i in range(1, 5)]
    method = normalized(row['method'])
    if method == 'topla' and all(v is not None for v in quarters):
        return sum(quarters, Decimal(0)), 'TOPLA: Q1 + Q2 + Q3 + Q4'
    if 'kumulatif' in method.replace('ü', 'u'):
        return quarters[3], 'KÜMÜLATİF: Q4'
    return None, 'Yıllık değer hesaplanamadı; yöntemi ve dört çeyreği kontrol edin.'


def annual_readings(row):
    # "2026 YILI TOPLAMI" is an achievement ratio, including cached zeros.
    # It is context only and must never become an actual or a fallback value.
    total = numeric(row.get('q4_total'))
    calculated, rule = method_value(row)
    readings = []
    if total is not None:
        readings.append({'key':'q4_total', 'value':total, 'rule':'2026 YILI 4. ÇEYREK GERÇEKLEŞEN TOPLAMI'})
    if calculated is not None and (total is None or calculated != total):
        readings.append({'key':'method', 'value':calculated, 'rule':rule})
    return readings


def annual_value(row):
    readings = annual_readings(row)
    return (readings[0]['value'], readings[0]['rule']) if readings else (None, method_value(row)[1])


def candidate_context(indicator, book_row):
    """Use pinned book text, never mutable PP rows, to distinguish candidates."""
    definition = indicator['definition']
    card = book_row.get('_report_card') or {}
    parts = [indicator['department'], f"Kart: {card.get('source_title') or definition.get('card_id') or 'belirtilmemiş'}"]
    for key, label in (('program', 'Program'), ('subprogram', 'Alt program')):
        if book_row.get(key):
            parts.append(f'{label}: {book_row[key]}')
    if card.get('goal'):
        goal = str(card['goal'])
        parts.append(f"Kart hedefi: {goal[:120]}{'…' if len(goal) > 120 else ''}")
    if definition.get('code'):
        parts.append(f"Gösterge kodu: {definition['code']}")
    parts.append(f"Kitap kaydı #{indicator['snapshot_indicator_id']}")
    return ' · '.join(parts)


def option(indicator, reading, workbook_unit, book_row):
    raw = reading['value']
    definition = indicator['definition']
    previous = indicator['actuals'][-1] if indicator['actuals'] else None
    scale = 'raw'
    if raw is not None and raw <= 1 and 'oran' in normalized(workbook_unit):
        unit = normalized(definition['unit'])
        targets = [numeric(Decimal(str(t['value']))) for t in definition['targets']
                   if t.get('state') == 'verified' and t.get('value') is not None]
        if '%' in definition['unit'] or 'yüzde' in unit or ('oran' in unit and any(t is not None and t > 1 for t in targets)):
            scale = 'percent'
        else:
            scale = 'choose'
    value = raw * 100 if raw is not None and scale == 'percent' else raw
    return {'id': indicator['report_indicator_id'], 'name': definition['name'], 'department': indicator['department'],
        'context': candidate_context(indicator, book_row),
        'reading': reading['key'], 'rule': reading['rule'], 'scale': scale, 'value': value, 'raw_value': raw,
        'percent_value': raw * 100 if raw is not None else None,
        'current': previous['value'] if previous else None,
        'expected_revision': previous['revision'] if previous else 0}


def summary(rows):
    return dict(Counter(row['status'] for row in rows))


def preview_import(db, user, revision_id, data):
    contract.strategy(user)
    report = contract.report_data(db, user, revision_id)
    if report['year'] != 2026:
        fail('Excel aktarımı yalnız 2026 yılı içindir. 2026 Faaliyet Raporu revizyonunu seçin.')
    rows = []
    claimed = set()
    department_map = structure_service.import_department_map(db, report['organization_id'], 2026, normalized)
    _, publication = contract.checked_publication(db, report['publication_id'])
    book_rows = contract.snapshot_rows(publication)
    for line, source in read_rows(data):
        readings = annual_readings(source)
        conflict = len(readings) > 1
        raw, rule = annual_value(source)
        deps = department_map.get(normalized(source['department']), set())
        pool = [i for i in report['indicators'] if i['definition']['department_id'] in deps]
        name = indicator_name(source['name'])
        exact = [i for i in pool if name and indicator_name(i['definition']['name']) == name]
        candidates = exact or sorted([i for i in pool if name and SequenceMatcher(None, name,
            indicator_name(i['definition']['name'])).ratio() >= .6], key=lambda i: (-SequenceMatcher(None, name,
                indicator_name(i['definition']['name'])).ratio(), i['report_indicator_id']))[:3]
        available = readings or [{'key':'missing', 'value':None, 'rule':rule}]
        options = [option(i, reading, source['unit'], book_rows[i['snapshot_indicator_id']])
                   for i in candidates[:3] for reading in available]
        match = len(exact) == 1
        status = 'Eşleşti' if match else 'Onay gerekiyor' if options else 'Eşleşmedi'
        message = ''
        if match:
            selected = options[0]
            if selected['id'] in claimed:
                status = 'Hata'; message = 'Bu gösterge ikinci kez isteniyor. Yinelenen satırı düzeltip yeniden yükleyin.'
            else:
                claimed.add(selected['id'])
                if conflict or selected['scale'] != 'raw':
                    status = 'Onay gerekiyor'
                elif raw is not None and selected['current'] is not None and raw == Decimal(selected['current']):
                    status = 'Değişmedi'
        if raw is None and status != 'Hata':
            status = 'Eksik'; message = 'Sayısal yıllık değer yok. Eksik çeyrekleri veya yıllık toplamı tamamlayın; boş sıfır değildir.'
            if any(k != 'strategy_ratio' and not f['cached_numeric'] for k, f in source['formulas'].items()):
                message += " Formülün sayısal önbelleği yok. Excel'de hesaplatıp kaydederek yeniden yükleyin."
        elif conflict and status != 'Hata':
            message = 'Q4 toplamı ile hesaplama yöntemi farklı. Aktarılacak yıllık değeri seçerek onaylayın.'
        ratio = source.get('strategy_ratio')
        rows.append({'line': line, 'source': {k: str(v) if v is not None else '' for k, v in source.items() if k != 'formulas'},
            'strategy_ratio': ratio if ratio is None or numeric(ratio) is not None else str(ratio),
            'formulas': source['formulas'], 'readings': readings, 'conflict': conflict,
            'quarters': [source[f'q{i}'] if source[f'q{i}'] is None or numeric(source[f'q{i}']) is not None
                         else str(source[f'q{i}']) for i in range(1, 5)], 'rule': rule, 'raw_value': raw,
            'options': options, 'exact': match, 'status': status, 'message': message})
    preview = {'schema_version':PREVIEW_VERSION, 'revision_id': revision_id,
        'expected_revision': report['revision'], 'rows': rows, 'counts': summary(rows)}
    record = ActualImport(report_revision_id=revision_id, actor_id=user.id,
        source_sha256=hashlib.sha256(data).hexdigest(), preview_json=contract.canonical(preview))
    db.add(record); db.flush()
    return record


def import_preview(db, user, import_id, lock=False):
    contract.strategy(user)
    query = select(ActualImport).where(ActualImport.id == import_id).execution_options(populate_existing=True)
    if lock:
        query = query.with_for_update()
    record = db.scalar(query)
    if not record:
        fail('İçe aktarma önizlemesi bulunamadı. Dosyayı yeniden yükleyin.', 404)
    if not record.result_json and datetime.now(UTC).replace(tzinfo=None) > record.created_at + TTL:
        fail('İçe aktarma önizlemesinin 24 saatlik süresi doldu. Dosyayı yeniden yükleyin.', 410)
    preview = json.loads(record.preview_json)
    if not record.result_json and preview.get('schema_version') != PREVIEW_VERSION:
        fail('Yıllık değer kuralları güncellendi. Eski önizleme uygulanamaz; Excel dosyasını yeniden yükleyin.', 409)
    return record, preview


def apply_import(db, user, import_id, expected_revision, choices):
    record, preview = import_preview(db, user, import_id, lock=True)
    if record.result_json:
        return json.loads(record.result_json)
    report, revision, _, _ = contract.report_revision(db, user, record.report_revision_id)
    if expected_revision != preview['expected_revision'] or revision.revision != report.current_revision:
        fail('Rapor revizyonu değişti. Güncel raporu seçip dosyayı yeniden önizleyin.', 409)
    if not isinstance(choices, dict) or set(choices) - {str(r['line']) for r in preview['rows']}:
        fail('Satır seçimleri geçersiz. Önizlemeyi açıp her satırı yeniden seçin.')
    results = []
    claimed = set()
    # Validate all selections before the first actual write.
    selections = {}
    for row in preview['rows']:
        choice = choices.get(str(row['line']))
        if not choice:
            continue
        if not isinstance(choice, dict) or choice.get('confirmed') is not True:
            fail(f"{row['line']}. satır onaylanmadı. Seçimi ve yıllık değeri açıkça onaylayın.")
        selected = next((o for o in row['options'] if o['id'] == choice.get('indicator_id')
            and o['reading'] == choice.get('reading')), None)
        if not selected or row['status'] in {'Hata', 'Eksik', 'Eşleşmedi'}:
            fail(f"{row['line']}. satır seçimi geçersiz. Eşleşen, sayısal değeri olan satırı seçin.")
        scale = choice.get('scale')
        if scale not in ({'raw', 'percent'} if selected['scale'] == 'choose' else {selected['scale']}):
            fail(f"{row['line']}. satır ölçeği onaylanmadı. Önizlemedeki sayı yorumunu seçin.")
        selections[row['line']] = (selected, scale)
    for row in preview['rows']:
        item = {'line': row['line'], 'status': row['status'], 'message': row['message']}
        if row['line'] not in selections:
            if row['status'] not in {'Hata', 'Eksik', 'Eşleşmedi', 'Değişmedi'}:
                item.update(status='Aktarılmadı', message='Strateji bu satırı onaylamadı.')
            results.append(item); continue
        selected, scale = selections[row['line']]
        if selected['id'] in claimed:
            item.update(status='Hata', message='Aynı gösterge ikinci kez seçildi. Her gösterge için tek satır seçip yeniden önizleyin.')
            results.append(item); continue
        claimed.add(selected['id'])
        value = Decimal(str(selected['percent_value'] if scale == 'percent' else selected['raw_value']))
        try:
            with db.begin_nested():
                # Serialize against screen edits/rebases before testing idempotence.
                contract.lock_report(db, report)
                previous = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == selected['id'])
                    .order_by(ActualRevision.revision.desc()))
                if previous and previous.value == value:
                    item.update(status='Değişmedi', message='Mevcut değer aynı; yeni revizyon yazılmadı.')
                else:
                    explanation = row['source'].get('explanation', '')
                    if not explanation.strip():
                        explanation = previous.explanation if previous else ''
                    actual = contract.save_actual(db, user, selected['id'], selected['expected_revision'],
                        format(value, 'f'), 'verified', json.loads(previous.evidence_json) if previous else [],
                        explanation, json.loads(previous.deviation_json) if previous else {})
                    db.flush()
                    item.update(status='Yazıldı', message='Yeni gerçekleşme revizyonu kaydedildi.',
                        report_indicator_id=selected['id'], actual_revision_id=actual.id,
                        annual_reading=selected['reading'], annual_rule=selected['rule'], scale=scale, value=format(value, 'f'))
        except HTTPException as error:
            # lock_report uses a SQL CAS followed by refresh, without marking
            # the ORM row dirty. Savepoint rollback does not restore that cached
            # lock_version; reload before the next row can try its own lock.
            db.expire(report)
            detail = error.detail.get('message', str(error.detail)) if isinstance(error.detail, dict) else str(error.detail)
            item.update(status='Hata', message=detail)
        results.append(item)
    result = {'rows': results, 'counts': summary(results), 'sha256': record.source_sha256}
    record.result_json = contract.canonical(result)
    db.add(AuditLog(user_id=user.id, action='actual_import_apply', entity_type='actual_import', entity_id=record.id,
        details=contract.canonical({**result, 'row_ids_written': [r['actual_revision_id'] for r in results if r['status'] == 'Yazıldı']})))
    db.flush()
    return result
