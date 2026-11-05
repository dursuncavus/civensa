"""The sole storage boundary for council photos; never touches report payloads."""
import base64
from datetime import date
from hashlib import sha256
from io import BytesIO
import logging
from uuid import uuid4
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select

from .activity_sections_service import document, fail
from .models import ARDocument, Department, DepartmentScope, ReportingPeriod
from .sunum.models import SunumPhoto

logger = logging.getLogger(__name__)
RAW_LIMIT = 15 * 1024 * 1024
SELECTION_LIMIT = 16
CONSENT = 'Fotoğrafta tanınabilir kişi yoksa ya da kişilerin izni alındıysa işaretleyin.'


def scope(db, user, document_id, *, lock=False):
    doc = document(db, user, document_id)
    if doc.department_id is not None:
        fail('Meclis fotoğrafları için idare faaliyet raporunu açın.')
    if lock:
        # Serialize selection counts, ordering and atomic pair operations per year.
        db.execute(select(ARDocument.id).where(ARDocument.id == doc.id).with_for_update()).scalar_one()
    return doc


def query(doc):
    return select(SunumPhoto).where(SunumPhoto.organization_id == doc.organization_id,
                                    SunumPhoto.period_id == doc.period_id)


def list_photos(db, doc):
    return list(db.scalars(query(doc).order_by(SunumPhoto.sort_order, SunumPhoto.id)))


def departments(db, doc):
    return list(db.scalars(select(Department).join(DepartmentScope).where(
        Department.organization_id == doc.organization_id, DepartmentScope.period_id == doc.period_id,
        DepartmentScope.status != 'excluded').order_by(Department.name)))


def process_image(raw, filename=''):
    if len(raw) > RAW_LIMIT:
        fail('Fotoğraf 15 MB sınırını aşıyor. Daha küçük bir JPEG, PNG veya WebP yükleyin.', 413)
    if filename.lower().endswith(('.heic', '.heif')) or (raw[4:8] == b'ftyp' and any(
            brand in raw[8:40] for brand in (b'heic', b'heix', b'hevc', b'hevx', b'mif1'))):
        fail('iPhone fotoğrafını JPEG olarak kaydedip yükleyin.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as original:
                if original.format not in {'JPEG', 'PNG', 'WEBP'}:
                    fail('Fotoğrafın gerçek biçimi desteklenmiyor. JPEG, PNG veya WebP yükleyin.')
                original.load()
                oriented = ImageOps.exif_transpose(original)
                # A new pixel-only image drops EXIF/GPS, ICC, XMP and comments.
                mode = 'RGBA' if 'A' in oriented.getbands() or 'transparency' in oriented.info else 'RGB'
                clean = Image.new(mode, oriented.size)
                clean.paste(oriented.convert(mode))
                clean.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                output = BytesIO()
                clean.save(output, format='WEBP', quality=82)
                data = output.getvalue()
                width, height = clean.size
                clean.thumbnail((320, 320), Image.Resampling.LANCZOS)
                thumb = BytesIO()
                clean.save(thumb, format='WEBP', quality=82)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        fail('Fotoğrafın piksel boyutu güvenlik sınırını aşıyor. Küçültülmüş bir fotoğraf yükleyin.')
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        fail('Fotoğraf açılamadı; dosya bozuk veya gerçek biçimi desteklenmiyor. Geçerli bir JPEG, PNG veya WebP yükleyin.')
    return dict(webp_data=data, thumb_data=thumb.getvalue(), width=width, height=height,
                sha256=sha256(data).hexdigest(), byte_size=len(data))


def upload(db, doc, user, *, department_id, caption, taken_on='', mahalle='', kind,
           consent, images):
    if not consent:
        fail('Fotoğraf izin onayı eksik. ' + CONSENT)
    caption, mahalle = caption.strip(), mahalle.strip()
    if not caption or len(caption) > 140:
        fail('Fotoğraf açıklaması zorunludur ve en fazla 140 karakter olabilir. Açıklamayı düzeltin.')
    if len(mahalle) > 80:
        fail('Mahalle en fazla 80 karakter olabilir. Mahalle adını kısaltın.')
    try:
        department_id = int(department_id)
        taken_on = date.fromisoformat(taken_on) if taken_on else None
    except (ValueError, TypeError):
        fail('Fotoğrafın müdürlük veya tarih alanı geçersiz. Listeden müdürlük seçin ve tarihi kontrol edin.')
    if department_id not in {d.id for d in departments(db, doc)}:
        fail('Fotoğrafın müdürlüğü bu kurumun raporlama yılı kapsamında değil. Listeden bir müdürlük seçin.')
    if user.role != 'strategy' and department_id != user.department_id:
        fail('Başka müdürlük adına fotoğraf yükleyemezsiniz. Kendi müdürlüğünüzü seçin.', 403)
    if kind not in {'single', 'pair'} or len(images) != (2 if kind == 'pair' else 1):
        fail('Fotoğraf türünü ve dosyalarını kontrol edin. Önce/sonra çifti için iki fotoğraf yükleyin.')
    processed = [process_image(raw, name) for raw, name in images]
    hashes = [p['sha256'] for p in processed]
    year = db.get(ReportingPeriod, doc.period_id).year
    duplicate = db.scalar(select(SunumPhoto.id).where(SunumPhoto.organization_id == doc.organization_id,
        SunumPhoto.year == year, SunumPhoto.sha256.in_(hashes)).limit(1))
    if len(set(hashes)) != len(hashes) or duplicate:
        fail('Bu fotoğraf bu rapor yılına zaten yüklendi. Mevcut fotoğrafı kullanın veya farklı bir fotoğraf seçin.', 409)
    existing = list_photos(db, doc)
    order = max((p.sort_order for p in existing), default=-1) + 1
    pair_key = str(uuid4()) if kind == 'pair' else None
    rows = [SunumPhoto(organization_id=doc.organization_id, period_id=doc.period_id, year=year,
        department_id=department_id, caption=caption, taken_on=taken_on, mahalle=mahalle or None,
        kind=('before' if i == 0 else 'after') if pair_key else 'single', pair_key=pair_key,
        consent_confirmed=True, selected=False, sort_order=order, created_by=user.id, **image)
        for i, image in enumerate(processed)]
    db.add_all(rows)
    db.flush()
    return rows


def photo(db, doc, photo_id):
    row = db.scalar(query(doc).where(SunumPhoto.id == photo_id))
    if row is None:
        fail('Fotoğraf bu rapor yılında bulunamadı. Fotoğraf listesini yenileyin.', 404)
    return row


def group(rows, row):
    return [p for p in rows if p.pair_key == row.pair_key] if row.pair_key else [row]


def change(db, doc, photo_id, action, value):
    rows = list_photos(db, doc)
    row = photo(db, doc, photo_id)
    members = group(rows, row)
    if action == 'toggle':
        selected = value == 'on'
        if selected and sum(p.selected for p in rows if p not in members) + len(members) > SELECTION_LIMIT:
            fail('Sunumda en fazla 16 fotoğraf gösterilebilir. Başka bir fotoğrafın seçimini kaldırıp yeniden deneyin.')
        for p in members:
            p.selected = selected
    elif action == 'order':
        if value not in {'up', 'down'}:
            fail('Fotoğraf sırası değiştirilemedi. Yukarı veya aşağı düğmesini kullanın.')
        groups = []
        for p in rows:
            if not any(p in g for g in groups):
                groups.append(group(rows, p))
        index = next(i for i, g in enumerate(groups) if row in g)
        other = index + (-1 if value == 'up' else 1)
        if 0 <= other < len(groups):
            groups[index], groups[other] = groups[other], groups[index]
        for i, g in enumerate(groups):
            for p in g:
                p.sort_order = i
    elif action == 'delete':
        if value != 'yes':
            fail('Fotoğraf silinmedi. Silmek için silme onayını işaretleyin.')
        for p in members:
            db.delete(p)
    else:
        fail('Fotoğraf işlemi bulunamadı. Listedeki düğmeleri kullanın.', 404)
    db.flush()


def image_bytes(db, doc, photo_id, thumbnail=False):
    row = photo(db, doc, photo_id)
    return row.thumb_data if thumbnail else row.webp_data


def deck_slides(db, doc):
    rows = list_photos(db, doc)
    selected = [p for p in rows if p.selected]
    if len(selected) != len(rows):
        logger.info('Meclis sunumu %s: Seçilmeyen %s fotoğraf atlandı.', doc.id, len(rows) - len(selected))
    if not selected:
        logger.info('Meclis sunumu %s: Seçili fotoğraf yok; fotoğraf slaytları atlandı.', doc.id)
        return []
    result, seen = [], set()
    names = {d.id: d.name for d in db.scalars(select(Department).where(Department.organization_id == doc.organization_id))}

    def uri(p):
        return 'data:image/webp;base64,' + base64.b64encode(p.webp_data).decode('ascii')

    def meta(p):
        return ' · '.join(v for v in (p.mahalle, names.get(p.department_id),
            p.taken_on.strftime('%d.%m.%Y') if p.taken_on else None) if v)

    for p in selected:
        if p.pair_key and p.pair_key in seen:
            continue
        data = dict(title=p.caption, meta=meta(p), source=f'Fotoğraf: {names[p.department_id]}')
        if p.kind == 'single':
            result.append(dict(type='photo', image=uri(p), **data))
        else:
            seen.add(p.pair_key)
            pair = group(selected, p)
            if (len(pair) != 2 or {i.kind for i in pair} != {'before', 'after'}
                    or len({(i.department_id, i.year, i.period_id) for i in pair}) != 1):
                logger.info('Meclis sunumu %s: Eksik önce/sonra çifti %s; slayt atlandı.', doc.id, p.pair_key)
                continue
            before = next(i for i in pair if i.kind == 'before')
            after = next(i for i in pair if i.kind == 'after')
            result.append(dict(type='before_after', before=uri(before), after=uri(after),
                               before_date=before.taken_on.strftime('%d.%m.%Y') if before.taken_on else '',
                               after_date=after.taken_on.strftime('%d.%m.%Y') if after.taken_on else '', **data))
    return result
