"""Guide tables: scoped drafts, book identities, computed totals and submit gates."""
import base64
from copy import deepcopy
import hashlib
import json
import warnings
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import defer

from . import activity_sections_service as sections
from .activity_evidence_service import MAX_FILE
from .models import (ARDocument, ARUnitTable, ARUnitPhoto, ARUnitPhotoRemoval, ActivityReport, ActivityReportRevision,
                     Publication, User)
from .numbers import parse_number, format_number
from .listing_memo import memo, KEY

STAFF = ['Memur', 'Sözleşmeli Personel (657/4-B)', 'Kadrolu İşçi', 'Şirket Personeli (696 KHK)']
PROJECT_STATES = ['Devam ediyor', 'Tamamlandı', 'Başlamadı', 'İptal']
TABLES = {
    '1': ('I.C.1', 'Fiziksel Yapı', 'Müdürlük Hizmet Binaları ve Tesisleri', [
        ('name', 'Bina / Tesis Adı'), ('address', 'Bulunduğu Mahalle / Adres'),
        ('purpose', 'Kullanım Amacı'), ('area', 'Alan (m2)'), ('ownership', 'Mülkiyet Durumu')]),
    '2': ('I.C.2', 'Yönetim Yapısı', 'Müdürlük İnsan Kaynakları Dağılımı (31.12.2026 itibarıyla)', [
        ('status', 'Hizmet Sınıfı / Statüsü'), ('positions', 'Kadro Sayısı'),
        ('actual', 'Fiili Çalışan'), ('women', 'Kadın'), ('men', 'Erkek')]),
    '7': ('III.B.2', 'Faaliyet ve Proje Bilgileri', 'Faaliyet ve Alt Faaliyet Bazında Çıktı ve Maliyet Gerçekleşme Tablosu', [
        ('activity', 'Faaliyet / Alt Faaliyet Kodu ve Adı'), ('outputs', 'Yürütülen İşler ve Somut Çıktılar'),
        ('inside', '2026 Bütçe İçi Harcama (TL)'), ('outside', 'Bütçe Dışı Kaynak (TL)'),
        ('total', 'Toplam Maliyet (TL)')]),
    '8': ('III.B.2', 'Faaliyet ve Proje Bilgileri', '2026 Yılı Proje İzleme ve Gerçekleşme Tablosu', [
        ('name', 'Proje Adı'), ('programme', 'İlişkili Program / Alt Program'),
        ('start', 'Başlama'), ('end', 'Bitiş'), ('physical', 'Fiziki (%)'),
        ('spending', 'Harcama (TL)'), ('state', 'Durumu')]),
}
NUMBERS = {'area', 'positions', 'actual', 'women', 'men', 'inside', 'outside', 'physical', 'spending', 'total'}
COUNTS = {'positions', 'actual', 'women', 'men'}
MONEY = {'inside', 'outside', 'spending', 'total'}
ORPHAN_PHOTO_WARNING = 'Bu fotoğrafın faaliyeti güncel kitapta yok; kaldırın veya yeniden yükleyin.'


def pinned_snapshot(db, publication):
    """Digest-checked book snapshot, parsed once per process (CIV-220/CIV-223).

    Publications are immutable (sha256-pinned); listing pages build report data
    for every directorate, so the parsed book is shared and must not be mutated.
    """
    # CIV-223: reused across requests too (process cache); read-only for callers.
    from .pinned_book_cache import get_or_build
    return get_or_build(db, 'ar_unit_book', publication,
                        lambda raw: json.loads(raw, parse_float=Decimal))


def book_publication(db, doc):
    report = db.scalar(select(ActivityReport).where(ActivityReport.organization_id == doc.organization_id,
                                                    ActivityReport.period_id == doc.period_id))
    revision = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id,
        ActivityReportRevision.revision == report.current_revision)) if report else None
    # Listing pages call this per directorate: never fetch the multi-MB snapshot
    # column again once the session has parsed it (pinned_snapshot).
    lean = select(Publication).options(defer(Publication.snapshot_json))
    return db.scalar(lean.where(Publication.id == revision.publication_id)) if revision else db.scalar(
        lean.where(Publication.period_id == doc.period_id).order_by(Publication.version.desc()))


def book(db, doc):
    """Same pinned book and department activities used by ar_typeset_source."""
    publication = memo(db, ('unit_book_publication', doc.organization_id, doc.period_id),
                       lambda: book_publication(db, doc))
    if not publication:
        return {'publication_id': None, 'activities': [], 'programmes': []}
    snapshot = pinned_snapshot(db, publication)
    if snapshot is None:
        sections.fail('Tablo 7 için bağlı kitap doğrulanamadı. Strateji ile kitap sürümünü kontrol edin.', 409)
    # PP errata affects financial totals only; catalogue/activity labels stay pinned.
    department = next((d for d in snapshot.get('departments', []) if d['department_id'] == doc.department_id), {})
    officials = {a['id']: a for a in snapshot.get('catalogue', [])}
    activities, programmes = [], {}
    # Programme choices use only this directorate's frozen responsibilities
    # and its own programme/subprogramme rows, including rows without activities.
    for official in officials.values():
        if doc.department_id in official.get('departments', []):
            key = f"catalogue:{official.get('program_code', '')}:{official.get('subprogram_code', '')}:{official['program_name']}:{official['subprogram_name']}"
            programmes[key] = f"{official.get('program_code', '')} {official['program_name']} / {official.get('subprogram_code', '')} {official['subprogram_name']}".strip()
    for row in [*department.get('activities', []), *department.get('cards', []), *department.get('indicators', [])]:
        if row.get('program') and row.get('subprogram'):
            key = f"subprogram:{row.get('subprogram_id')}:{row['program']}:{row['subprogram']}"
            programmes[key] = f"{row['program']} / {row['subprogram']}"
    for activity in department.get('activities', []):
        activities.append({'key': f"{publication.id}:{activity['id']}",
                           'activity': ' '.join(filter(None, [activity.get('code'), activity['name']]))})
    return {'publication_id': publication.id, 'activities': activities,
            'programmes': [{'key': key, 'label': label} for key, label in programmes.items()]}


def stored(db, doc, kind):
    if KEY in db.info:
        # CIV-224: one query for all of a document's tables during a listing.
        return memo(db, ('unit_tables', doc.id), lambda: {t.kind: t for t in db.scalars(
            select(ARUnitTable).where(ARUnitTable.document_id == doc.id))}).get(kind)
    return db.scalar(select(ARUnitTable).where(ARUnitTable.document_id == doc.id, ARUnitTable.kind == kind))


def writable(db, user, document_id, revision, kind):
    if kind not in TABLES:
        sections.fail('Birim raporu tablosu bulunamadı. Tablo 1, 2, 7 veya 8 seçin.', 404)
    doc = sections.document(db, user, document_id)
    user = db.get(User, user.id, populate_existing=True)
    if not doc.department_id or user.role != 'department' or user.department_id != doc.department_id:
        sections.fail('Bu tabloyu düzenleyemezsiniz. Kendi müdürlüğünüzün hesabını kullanın; Strateji tabloları salt okunur inceler.', 403)
    definition, _ = sections.section_pair(db, doc, TABLES[kind][0])
    sections.writable(db, user, doc, revision, definition)
    return doc


def number(value, key, location):
    if isinstance(value, bool):
        sections.fail(f'{location}: Sayı biçimi geçersiz. Türkçe biçimde sayı girin.')
    try:
        result = parse_number(value, money=key in MONEY or key == 'area')
    except ValueError:
        sections.fail(f'{location}: Sayı okunamadı. Negatif olmayan Türkçe biçimde sayı girin (örnek: 1.234.567,89).')
    if result is not None and (result < 0 or result >= Decimal('1e18') or
            (key in COUNTS and result != result.to_integral()) or (key == 'physical' and result > 100)):
        sections.fail(f'{location}: Değer aralık dışında. Kişi sayıları için tam sayı, Fiziki (%) için 0–100, tutarlar için negatif olmayan sayı girin.')
    return result


def normalize(kind, rows, source):
    if not isinstance(rows, list) or len(rows) > 2000 or any(not isinstance(r, dict) for r in rows):
        sections.fail(f'Tablo {kind}: Satırlar okunamadı. En fazla 2.000 satır girin.')
    fields = [key for key, _ in TABLES[kind][3] if key not in {'activity', 'total'}]
    if kind == '2':
        if [r.get('key') for r in rows] != STAFF:
            sections.fail('Tablo 2: Sabit personel türleri değiştirilemez. Dört personel satırını kullanın.')
    if kind == '7':
        keys = [r.get('key') for r in rows]
        expected = [a['key'] for a in source['activities']]
        if any(not isinstance(key, str) for key in keys) or len(keys) != len(set(keys)) or set(keys) != set(expected):
            sections.fail('Tablo 7: Faaliyetler bağlı kitaptaki müdürlük kapsamıyla eşleşmiyor. Sayfayı yenileyin; faaliyet eklemeyin veya adını değiştirmeyin.')
        rows = sorted(rows, key=lambda r: expected.index(r['key']))
    result = []
    for index, row in enumerate(rows):
        allowed = set(fields) | ({'key'} if kind == '2' else {'key', 'not_applied', 'reason'} if kind == '7' else set())
        if set(row) - allowed:
            sections.fail(f'Tablo {kind}, {index+1}. satır: Hesaplanan veya sabit alan değiştirilemez. Yalnız giriş alanlarını doldurun.')
        item = {}
        for key in fields:
            label = dict(TABLES[kind][3])[key]
            location = f'Tablo {kind}, {index+1}. satır, {label}'
            value = row.get(key)
            if key in NUMBERS:
                item[key] = number(value, key, location)
            else:
                if value is not None and not isinstance(value, str):
                    sections.fail(f'{location}: Metin girin.')
                value = (value or '').strip()
                if len(value) > 10000:
                    sections.fail(f'{location}: En fazla 10.000 karakter girin.')
                item[key] = value
        if kind == '2':
            item['key'] = row['key']
        if kind == '7':
            if not isinstance(row.get('not_applied', False), bool):
                sections.fail('Tablo 7: Uygulanmadı seçimini kontrol edin.')
            item.update(key=row['key'], not_applied=row.get('not_applied', False))
            reason = row.get('reason', '')
            if not isinstance(reason, str) or len(reason) > 10000:
                sections.fail('Tablo 7: Uygulanmadı gerekçesini en fazla 10.000 karakterle yazın.')
            item['reason'] = reason.strip()
            if item['not_applied'] and (item['outputs'] or item['inside'] is not None or item['outside'] is not None):
                sections.fail(f'Tablo 7, {index+1}. satır: Uygulanmadı seçildi. Çıktı ve tutarları kaldırın; gerekçe girin.')
        if kind == '8':
            if item['programme'] and item['programme'] not in {p['key'] for p in source['programmes']}:
                sections.fail(f'Tablo 8, {index+1}. satır: Program / Alt Program müdürlüğünüzün kitabında yok. Listeden seçin.')
            if item['state'] and item['state'] not in PROJECT_STATES:
                sections.fail(f'Tablo 8, {index+1}. satır: Durumu listeden seçin.')
            for key in ('start', 'end'):
                try:
                    if item[key]: item[key] = date.fromisoformat(item[key]).isoformat()
                except ValueError:
                    sections.fail(f'Tablo 8, {index+1}. satır: Başlama – Bitiş tarihini kontrol edin.')
            if item['start'] and item['end'] and item['start'] > item['end']:
                sections.fail(f'Tablo 8, {index+1}. satır: Bitiş başlangıçtan önce olamaz. Tarihleri düzeltin.')
        result.append(item)
    return result


def save(db, user, document_id, kind, expected_revision, rows, no_projects=None):
    doc = writable(db, user, document_id, expected_revision, kind)
    source = book(db, doc)
    if kind in {'7', '8'} and source['publication_id'] is None:
        sections.fail(f'Tablo {kind}: Bağlı kitap bulunamadı. Strateji ile onaylı kitap sürümünü kontrol edin.', 409)
    if no_projects is not None and not isinstance(no_projects, bool):
        sections.fail('Tablo 8: Bu yıl proje yok seçimini kontrol edin.')
    if kind == '8' and ((no_projects is True and rows) or (no_projects is False and not rows)):
        sections.fail('Tablo 8: Bu yıl proje yok seçimi ile proje satırları çelişiyor. Proje yok seçin veya proje satırı girin.')
    normalized = normalize(kind, rows, source)
    value = {'rows': normalized}
    if kind in {'7', '8'}: value['publication_id'] = source['publication_id']
    if kind == '8': value['no_projects'] = no_projects
    record = stored(db, doc, kind)
    before = json.loads(record.payload_json) if record else None
    if not record:
        record = ARUnitTable(document_id=doc.id, kind=kind)
        db.add(record)
    record.payload_json = sections.numeric_canonical(value)
    sections.event(db, user, doc, TABLES[kind][0], 'unit_table_save', before, {'table': kind, **value})
    doc.revision += 1
    db.flush()
    return doc


def photo_activity(db, doc, activity_key):
    """Resolve historical labels from the immutable book the photo belongs to."""
    try:
        publication_id, activity_id = map(int, activity_key.split(':'))
    except (ValueError, TypeError):
        return f'Faaliyet kaydı: {activity_key}'
    publication = db.get(Publication, publication_id)
    if publication and publication.period_id == doc.period_id:
        snapshot = pinned_snapshot(db, publication)
        if snapshot is None:
            sections.fail('Fotoğrafın bağlı kitabı doğrulanamadı. Strateji ile fotoğraf kaydını ve kitap sürümünü kontrol edin.', 409)
        for department in snapshot.get('departments', []):
            if department['department_id'] == doc.department_id:
                for activity in department.get('activities', []):
                    if activity['id'] == activity_id:
                        return ' '.join(filter(None, [activity.get('code'), activity['name']]))
    return f'Faaliyet kaydı: {activity_key}'


def unit_data(db, doc):
    source = book(db, doc)
    tables = {}
    for kind, (code, section, title, columns) in TABLES.items():
        record = stored(db, doc, kind)
        data = json.loads(record.payload_json, parse_float=Decimal) if record else {'rows': []}
        rows = data['rows']
        if kind == '2':
            old = {r['key']: r for r in rows}
            rows = [old.get(key, {'key': key}) for key in STAFF]
        if kind == '7':
            old = {r['key']: r for r in rows}
            rows = [dict(old.get(a['key'], {}), **a) for a in source['activities']]
            for row in rows:
                row['total'] = row.get('inside') + row.get('outside') if all(row.get(k) is not None for k in ('inside', 'outside')) else None
        if kind == '8':
            names = {p['key']: p['label'] for p in source['programmes']}
            rows = [dict(row, programme_label=names.get(row['programme'], 'Program / Alt Program değişti; listeden yeniden seçin.')) for row in rows]
        totals = {key: {'value': sum((Decimal(str(r[key])) for r in rows if r.get(key) is not None), Decimal(0))
                                  if any(r.get(key) is not None for r in rows) else None,
                        'missing': sum(r.get(key) is None for r in rows)}
                  for key, _ in columns if key in NUMBERS and key != 'physical'}
        tables[kind] = dict(kind=kind, section_code=code, section_title=section, title=title,
                            columns=columns, rows=rows, totals=totals, saved=record is not None,
                            no_projects=data.get('no_projects'),
                            book_changed=bool(record and kind in {'7', '8'} and data.get('publication_id') != source['publication_id']))
    photos = []
    order = {a['key']: i for i, a in enumerate(source['activities'])}
    names = {a['key']: a['activity'] for a in source['activities']}
    records = db.scalars(select(ARUnitPhoto).where(ARUnitPhoto.document_id == doc.id,
        ~select(ARUnitPhotoRemoval.id).where(ARUnitPhotoRemoval.photo_id == ARUnitPhoto.id).exists())).all()
    for photo in sorted(records, key=lambda p: (order.get(p.activity_key, len(order)), p.id)):
        photos.append({'id': photo.id, 'document_id': doc.id, 'activity_key': photo.activity_key, 'caption': photo.caption,
                       'activity': names.get(photo.activity_key) or photo_activity(db, doc, photo.activity_key),
                       'orphaned': photo.activity_key not in order,
                       'label': f'Fotoğraf {len(photos)+1}', 'filename': photo.filename, 'sha256': photo.sha256,
                       'url': f'/activity-sections/reports/{doc.id}/unit-tables/photos/{photo.id}'})
    return {'tables': tables, 'photos': photos, 'programmes': source['programmes'],
            'publication_id': source['publication_id']}


def report_data(db, doc):
    if doc.department_id:
        return unit_data(db, doc)
    from .ar_unit_workflow_service import approved_sources
    sources, _ = approved_sources(db, doc)
    units, photo_number = [], 0
    for _, payload in sources:
        if not payload.get('unit_tables'):
            continue
        unit = dict(payload['unit_tables'], department=payload['department'], department_id=payload['department_id'])
        for photo in unit['photos']:
            photo_number += 1
            photo['label'] = f'Fotoğraf {photo_number}'
        units.append(unit)
    return {'units': units}


def blockers(payload):
    data = payload.get('unit_tables', {})
    result = []
    for photo in data.get('photos', []):
        if photo.get('orphaned'):
            result.append({'indicator': photo['label'], 'group': 'Faaliyet fotoğrafları',
                'link': f'/activity-sections/reports/{payload["id"]}/unit-tables#photos',
                'message': ORPHAN_PHOTO_WARNING})
    for kind, table in data.get('tables', {}).items():
        def missing(message, index=None, field=None):
            anchor = f'table-{kind}' if index is None else f'table-{kind}-row-{index}' + (f'-{field}' if field else '')
            result.append({'indicator': f'Tablo {kind}' + (f' · {index+1}. satır' if index is not None else ''),
                'group': f'Tablo {kind} — {table["title"]}',
                'link': f'/activity-sections/reports/{payload["id"]}/unit-tables#{anchor}', 'message': message})
        if table.get('book_changed'):
            missing('Bağlı kitap değişti. Güncel faaliyet ve program satırlarını gözden geçirip tabloyu yeniden kaydedin.')
        if kind == '8' and any(row.get('programme') and row['programme'] not in {p['key'] for p in data.get('programmes', [])} for row in table['rows']):
            missing('Program / Alt Program güncel kitapta yok. Proje satırındaki listeden yeniden seçin.')
        if not table['saved']:
            missing('Tablo henüz kaydedilmedi. Satırları gözden geçirip tabloyu kaydedin.')
        if kind in {'7', '8'} and not data.get('publication_id'):
            missing('Bağlı kitap bulunamadı. Strateji ile onaylı kitap sürümünü kontrol edin.')
        if kind == '8' and ((not table['rows'] and table['no_projects'] is not True) or
                            (table['rows'] and table['no_projects'] is not False)):
            missing('Proje satırı girin veya Bu yıl proje yok seçin ve tabloyu kaydedin.')
        for index, row in enumerate(table['rows']):
            if kind == '7' and row.get('not_applied'):
                if not row.get('reason', '').strip():
                    missing('Uygulanmadı için gerekçe girin.', index, 'reason')
                continue
            for key, label in table['columns']:
                if key in {'total', 'activity'}: continue
                if row.get(key) is None or row.get(key) == '':
                    missing(f'{label} eksik. Alanı doldurup tabloyu kaydedin.', index, key)
            if kind == '2' and all(row.get(k) is not None for k in ('women', 'men', 'actual')) and row['women'] + row['men'] != row['actual']:
                missing('Kadın + Erkek = Fiili Çalışan olmalıdır. Personel sayılarını düzeltin.', index, 'actual')
    return result


def require_complete(payload, missing_sections=None):
    problems = blockers(payload)
    if problems:
        message = 'Birim faaliyet raporu gönderilemedi. Aşağıdaki tablo ve fotoğraf uyarılarını giderin.'
        detail = {}
        if missing_sections:
            message = 'Birim faaliyet raporu gönderilemedi. Şu bölümleri tamamlayın: ' + '; '.join(missing_sections)
            detail['errors'] = [{'field': 'sections', 'message': message}]
            problems += [{'indicator': section['title'], 'group': 'Rapor bölümleri',
                'link': f"/activity-sections/reports/{payload['id']}?code={section['code']}",
                'message': 'Bölümün eksiklerini giderip Hazır veya gerekçeli Uygulanamaz seçin.'}
                for section in payload['sections'] if section['title'] in missing_sections]
        raise HTTPException(409, {'message': message, 'blockers': problems, **detail})


def upload(db, user, document_id, activity_key, expected_revision, caption, raw, filename):
    doc = writable(db, user, document_id, expected_revision, '7')
    if activity_key not in {a['key'] for a in book(db, doc)['activities']}:
        sections.fail('Fotoğrafın faaliyeti müdürlüğünüzün kitabında yok. Tablo 7 satırını seçin.')
    if not caption.strip() or len(caption) > 1000:
        sections.fail('Faaliyet fotoğrafı açıklaması eksik veya çok uzun. En fazla 1.000 karakterle açıklama girin.')
    if not raw or len(raw) > MAX_FILE:
        sections.fail(f'Faaliyet fotoğrafı boş veya {MAX_FILE // (1024*1024)} MB sınırını aşıyor. Daha küçük JPG/PNG yükleyin.')
    if Path(filename).suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
        sections.fail('Faaliyet fotoğrafı biçimi geçersiz. JPG/PNG yükleyin.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {'JPEG', 'PNG'}: raise ValueError()
                image.load()
                pixels = ImageOps.exif_transpose(image).convert('RGB')
                clean = Image.new('RGB', pixels.size)
                clean.paste(pixels)
                clean.thumbnail((1600, 1600))
                output = BytesIO()
                clean.save(output, format='PNG')
                content = output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        sections.fail('Faaliyet fotoğrafı açılamadı. Geçerli ve küçültülmüş JPG/PNG yükleyin.')
    photo = ARUnitPhoto(document_id=doc.id, activity_key=activity_key, caption=caption.strip(),
        filename=Path(filename).name[:200], sha256=hashlib.sha256(content).hexdigest(),
        file_data=content, created_by=user.id)
    db.add(photo)
    sections.event(db, user, doc, 'III.B.2', 'unit_photo_upload', None,
                   {'activity_key': activity_key, 'caption': photo.caption, 'sha256': photo.sha256})
    doc.revision += 1
    db.flush()
    return photo


def remove_photo(db, user, document_id, photo_id, expected_revision):
    doc = writable(db, user, document_id, expected_revision, '7')
    photo = db.get(ARUnitPhoto, photo_id)
    if not photo or photo.document_id != doc.id:
        sections.fail('Faaliyet fotoğrafı bulunamadı. Kendi raporunuzdaki fotoğrafı seçin.', 404)
    if db.scalar(select(ARUnitPhotoRemoval.id).where(ARUnitPhotoRemoval.photo_id == photo.id)):
        sections.fail('Faaliyet fotoğrafı zaten kaldırıldı. Güncel fotoğraf listesini görmek için sayfayı yenileyin.', 409)
    db.add(ARUnitPhotoRemoval(document_id=doc.id, photo_id=photo.id, created_by=user.id))
    sections.event(db, user, doc, 'III.B.2', 'unit_photo_remove',
        {'photo_id': photo.id, 'activity_key': photo.activity_key, 'caption': photo.caption, 'sha256': photo.sha256},
        {'photo_id': photo.id, 'removed': True})
    doc.revision += 1
    db.flush()
    return doc


def export_tables(data):
    """Pure renderer input, shared by Word/PDF and the consolidated view."""
    for unit in data.get('units', [data]):
        for kind, table in unit.get('tables', {}).items():
            columns = [('key', 'Personel Türü'), *table['columns']] if kind == '2' else table['columns']
            rows = []
            for row in table['rows']:
                rows.append([format_number(row.get(key), money=key in MONEY) if key in NUMBERS else
                    ('Uygulanmadı: ' + row.get('reason', '') if kind == '7' and key == 'outputs' and row.get('not_applied') else
                     row.get('programme_label', row.get(key)) if key == 'programme' else row.get(key)) for key, _ in columns])
            if table['totals']:
                rows.append(['TOPLAM', *[format_number(table['totals'][key]['value'], money=key in MONEY)
                    if key in table['totals'] else '' for key, _ in columns[1:]]])
            yield unit, table, columns, rows


def with_photo_labels(db, payload):
    """Display old immutable manifests with their original activity labels."""
    result = deepcopy(payload)
    data = result.get('unit_tables', {})
    for unit in data.get('units', [data]):
        for photo in unit.get('photos', []):
            if photo.get('activity'):
                continue
            doc = db.get(ARDocument, photo['document_id'])
            if (not doc or doc.organization_id != result['organization_id'] or
                    doc.period_id != result['period_id'] or
                    doc.department_id != unit.get('department_id', result.get('department_id'))):
                sections.fail('Fotoğrafın birim raporu doğrulanamadı. Strateji ile rapor sürümünü ve fotoğraf kaydını kontrol edin.', 409)
            photo['activity'] = photo_activity(db, doc, photo['activity_key'])
    return result


def with_export_photos(db, payload):
    """Hydrate immutable evidence bytes only for rendering, never for persistence.

    Submission/freezes keep IDs and SHA-256 manifests, matching indicator evidence.
    A detached copy prevents a Word/PDF download from changing the stored source.
    """
    result = with_photo_labels(db, payload)
    data = result.get('unit_tables', {})
    for unit in data.get('units', [data]):
        department_id = unit.get('department_id', result.get('department_id'))
        for photo in unit.get('photos', []):
            record = db.get(ARUnitPhoto, photo['id'])
            doc = db.get(ARDocument, photo['document_id'])
            if (not record or not doc or record.document_id != doc.id or
                    doc.organization_id != result['organization_id'] or doc.period_id != result['period_id'] or
                    doc.department_id != department_id or record.activity_key != photo['activity_key'] or
                    record.sha256 != photo['sha256'] or record.caption != photo['caption'] or
                    hashlib.sha256(record.file_data).hexdigest() != photo['sha256']):
                sections.fail('Faaliyet fotoğrafının sabit kaydı doğrulanamadı. Strateji ile rapor sürümünü ve fotoğraf kaydını kontrol edin.', 409)
            photo['image_base64'] = base64.b64encode(record.file_data).decode()
    return result
