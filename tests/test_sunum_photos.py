"""CIV-184 acceptance against disposable PostgreSQL and offline Chromium."""
from datetime import date
from hashlib import sha256
from io import BytesIO
import logging
import os
from pathlib import Path
import re
import struct
import zlib

from lxml import html
from PIL import Image, ImageDraw
import pytest
from sqlalchemy import func, select

from app import sunum_photos_service as photos
from app.models import ARDocument, Department, Organization, ReportingPeriod
from app.sunum.models import SunumPhoto
from test_activity_sections import section_client, login, ready_and_freeze
from test_sunum_browser import browser_options, deck_url
from test_sunum_idare import idare_fixture

pytestmark = pytest.mark.postgres


def image_bytes(seed=0, *, fmt='PNG', size=(1920, 1080), exif=False):
    image = Image.new('RGB', size, (114 + seed % 90, 169, 190))
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rectangle((0, h*.5, w, h), fill=(72, 116 + seed % 80, 66))
    draw.polygon([(w*.41, h*.5), (w*.59, h*.5), (w*.91, h), (w*.09, h)], fill=(88+seed % 20, 91, 92))
    for offset in range(6):
        y = h*.55 + offset*h*.08
        draw.rectangle((w*.495, y, w*.505, y+h*.035), fill='white')
    # Unique but deterministic fixture pixels; no network or real personal data.
    draw.rectangle((20, 20, 80+seed*2, 70), fill=(seed % 255, 100, 30))
    output = BytesIO()
    options = {}
    if exif:
        tags = Image.Exif()
        tags[274] = 6
        tags[34853] = {1: 'N', 2: (41, 1, 1), 3: 'E', 4: (28, 1, 1)}
        options['exif'] = tags
    image.save(output, fmt, **options)
    return output.getvalue()


def bomb_header():
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 20000, 20000, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0')) + chunk(b'IEND', b'')


@pytest.fixture
def photo_client(section_client, sample):
    client, docs, _, _ = section_client
    token = login(client, sample['strategy'].email)
    return client, docs, token


def upload(fixture, sample, raw=None, *, second=None, filename='work.png', **fields):
    client, docs, token = fixture
    data = dict(department_id=str(sample['department'].id), caption='Yol yenileme tamamlandı',
                kind='pair' if second is not None else 'single', consent='on',
                mahalle='Hürriyet Mahallesi', taken_on='2027-10-29')
    data.update(fields)
    files = {'file': (filename, raw if raw is not None else image_bytes(), 'image/jpeg')}
    if second is not None:
        files['after_file'] = ('after.png', second, 'image/png')
    return client.post(f"/activity-sections/reports/{docs['idare'].id}/photos",
                       headers={'X-CSRF-Token': token}, data=data, files=files)


def change(fixture, row, action, value):
    client, docs, token = fixture
    return client.post(f"/activity-sections/reports/{docs['idare'].id}/photos/{row.id}/{action}",
                       headers={'X-CSRF-Token': token}, data={'value': value})


def test_jpeg_orientation_metadata_thumbnail_and_original_not_retained(photo_client, db, sample):
    raw = image_bytes(fmt='JPEG', size=(2400, 1200), exif=True)
    assert Image.open(BytesIO(raw)).getexif().get(274) == 6
    assert Image.open(BytesIO(raw)).getexif().get_ifd(34853)
    assert upload(photo_client, sample, raw, filename='actually-jpeg.png').status_code == 303
    row = db.scalar(select(SunumPhoto))
    with Image.open(BytesIO(row.webp_data)) as stored:
        assert stored.format == 'WEBP'
        assert stored.size == (800, 1600) == (row.width, row.height)
        assert not stored.getexif()
        assert not {'exif', 'xmp', 'icc_profile', 'comment'} & stored.info.keys()
    with Image.open(BytesIO(row.thumb_data)) as thumb:
        assert thumb.size == (160, 320) and not thumb.getexif()
    assert row.webp_data != raw and row.thumb_data != raw
    assert row.sha256 == sha256(row.webp_data).hexdigest()
    assert row.byte_size == len(row.webp_data)
    assert row.consent_confirmed and row.created_by == sample['strategy'].id
    assert row.taken_on == date(2027, 10, 29)
    # Only these two binary columns exist; no original or original filename.
    assert {c.name for c in SunumPhoto.__table__.c if c.type.python_type is bytes} == {'webp_data', 'thumb_data'}
    client, docs, _ = photo_client
    base = f"/activity-sections/reports/{docs['idare'].id}/photos/{row.id}/image"
    response = client.get(base)
    assert response.content == row.webp_data
    assert response.headers['content-type'] == 'image/webp'
    assert response.headers['cache-control'] == 'private, no-store'
    assert client.get(base+'?thumbnail=true').content == row.thumb_data


@pytest.mark.parametrize('fmt', ['PNG', 'WEBP'])
def test_real_formats_and_never_upscale(photo_client, db, sample, fmt):
    assert upload(photo_client, sample, image_bytes(fmt=fmt, size=(120, 60)), filename='misleading.jpg').status_code == 303
    row = db.scalar(select(SunumPhoto))
    assert (row.width, row.height) == (120, 60)


@pytest.mark.parametrize('case,message,status', [
    ('fake', 'Fotoğraf açılamadı', 422), ('gif', 'gerçek biçimi', 422),
    ('heic', 'iPhone fotoğrafını JPEG olarak kaydedip yükleyin.', 422),
    ('heic_magic', 'iPhone fotoğrafını JPEG olarak kaydedip yükleyin.', 422),
    ('bomb', 'piksel boyutu güvenlik sınırını', 422), ('oversize', '15 MB sınırını', 413),
    ('consent', 'izin onayı eksik', 422), ('duplicate', 'zaten yüklendi', 409),
    ('caption', 'açıklaması zorunludur', 422), ('mahalle', 'Mahalle en fazla 80', 422),
    ('missing_after', 'dosyası eksik', 422),
])
def test_rejection_is_turkish_and_atomic(photo_client, db, sample, case, message, status):
    raw, filename, fields = image_bytes(), 'work.jpg', {}
    if case == 'fake': raw = b'This is text, not a JPEG.'
    if case == 'gif': raw = image_bytes(fmt='GIF')
    if case == 'heic': filename = 'iphone.HEIC'
    if case == 'heic_magic': raw = b'\x00\x00\x00\x18ftypheic' + b'\0'*16
    if case == 'bomb': raw = bomb_header()
    if case == 'oversize': raw = b'x' * (photos.RAW_LIMIT + 1)
    if case == 'consent': fields['consent'] = ''
    if case == 'caption': fields['caption'] = ' '
    if case == 'mahalle': fields['mahalle'] = 'a'*81
    if case == 'missing_after': fields['kind'] = 'pair'
    if case == 'duplicate': assert upload(photo_client, sample, raw).status_code == 303
    count = db.scalar(select(func.count()).select_from(SunumPhoto))
    response = upload(photo_client, sample, raw, filename=filename, **fields)
    assert response.status_code == status, response.text[:600]
    assert message in response.text
    assert db.scalar(select(func.count()).select_from(SunumPhoto)) == count
    if case not in {'duplicate', 'missing_after'}:
        # A bad second image rolls back the whole pair, even with a valid first.
        response = upload(photo_client, sample, image_bytes(20), second=raw, filename=filename, **fields)
        assert response.status_code == status, response.text[:600]
        assert db.scalar(select(func.count()).select_from(SunumPhoto)) == count


@pytest.mark.parametrize('email', ['test@example.invalid', 'park@example.invalid', 'finance@example.invalid'])
def test_every_photo_route_requires_strategy(photo_client, sample, email):
    client, docs, _ = photo_client
    token = login(client, email)
    base = f"/activity-sections/reports/{docs['idare'].id}/photos"
    routes = [('GET', base), ('POST', base), ('GET', base+'/1/image'),
              ('GET', base+'/1/image?thumbnail=true')]
    routes += [('POST', base+'/1/'+action) for action in ['toggle', 'order', 'delete']]
    for method, path in routes:
        response = client.request(method, path, headers={'X-CSRF-Token': token})
        assert response.status_code == 403, (method, path, response.text)
        assert 'yalnızca Strateji' in response.text


def test_scope_csrf_and_required_fields(photo_client, db, sample):
    client, docs, token = photo_client
    assert upload(photo_client, sample).status_code == 303
    row = db.scalar(select(SunumPhoto))
    # A different institution/period cannot obtain image bytes through an ID.
    org = Organization(name='Diğer Belediye')
    period = ReportingPeriod(year=2028)
    db.add_all([org, period]); db.flush()
    other = ARDocument(organization_id=org.id, period_id=period.id, scope='idare',
                       definition_version=1, created_by=sample['strategy'].id)
    dep = Department(organization_id=org.id, name='Diğer Müdürlük')
    db.add_all([other, dep]); db.commit()
    base = f'/activity-sections/reports/{other.id}/photos/{row.id}'
    assert client.get(base+'/image').status_code == 404
    for action in ['toggle', 'order', 'delete']:
        assert client.post(base+'/'+action, headers={'X-CSRF-Token': token}, data={'value':'yes'}).status_code == 404
    own = docs[f"birim:{sample['department'].id}"]
    assert client.get(f'/activity-sections/reports/{own.id}/photos').status_code == 422
    assert upload(photo_client, sample, image_bytes(2), department_id=str(dep.id)).status_code == 422
    assert client.post(f"/activity-sections/reports/{docs['idare'].id}/photos/{row.id}/delete", data={'value':'yes'}).status_code == 403
    assert change(photo_client, row, 'delete', '').status_code == 422
    assert photos.list_photos(db, docs['idare'])


def test_pairs_selection_cap_global_order_and_delete(photo_client, db, sample):
    for i in range(15):
        assert upload(photo_client, sample, image_bytes(i), caption=f'İş {i}').status_code == 303
    assert upload(photo_client, sample, image_bytes(15), second=image_bytes(16), caption='Çift').status_code == 303
    rows = photos.list_photos(db, photo_client[1]['idare'])
    for row in rows[:15]: assert change(photo_client, row, 'toggle', 'on').status_code == 303
    response = change(photo_client, rows[15], 'toggle', 'on')
    assert response.status_code == 422 and 'en fazla 16 fotoğraf' in response.text
    db.expire_all()
    assert not rows[15].selected and not rows[16].selected
    assert change(photo_client, rows[0], 'toggle', '').status_code == 303
    assert change(photo_client, rows[15], 'toggle', 'on').status_code == 303
    assert change(photo_client, rows[0], 'toggle', 'on').status_code == 422
    db.expire_all()
    assert rows[15].selected and rows[16].selected
    assert change(photo_client, rows[15], 'order', 'up').status_code == 303
    assert photos.list_photos(db, photo_client[1]['idare'])[-3:] == [rows[15], rows[16], rows[14]]
    assert change(photo_client, rows[16], 'order', 'down').status_code == 303
    assert photos.list_photos(db, photo_client[1]['idare'])[-2:] == rows[15:]
    assert change(photo_client, rows[16], 'delete', 'yes').status_code == 303
    assert len(photos.list_photos(db, photo_client[1]['idare'])) == 15


def test_deck_order_skips_logs_limits_and_birim_bytes(photo_client, db, sample, caplog):
    client, docs, _ = photo_client
    own = docs[f"birim:{sample['department'].id}"]
    birim_before = client.get(f'/activity-sections/reports/{own.id}/sunum').content
    with caplog.at_level(logging.INFO):
        client.get(f"/activity-sections/reports/{docs['idare'].id}/sunum")
    assert 'Seçili fotoğraf yok' in caplog.text
    for i in range(14):
        assert upload(photo_client, sample, image_bytes(i), caption=f'Fotoğraf {i}').status_code == 303
    assert upload(photo_client, sample, image_bytes(14), second=image_bytes(15), caption='Önce ve sonra').status_code == 303
    assert upload(photo_client, sample, image_bytes(16), caption='Seçilmemiş fotoğraf').status_code == 303
    rows = photos.list_photos(db, docs['idare'])
    for row in rows[:16]:
        assert change(photo_client, row, 'toggle', 'on').status_code == 303
    assert change(photo_client, rows[1], 'order', 'up').status_code == 303
    response = client.get(f"/activity-sections/reports/{docs['idare'].id}/sunum")
    assert response.status_code == 200 and len(response.content) <= 8_000_000
    if os.getenv('CIVENSA_PHOTO_ARTIFACTS'):
        folder = Path(os.environ['CIVENSA_PHOTO_ARTIFACTS'])
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'sixteen-photos-size.txt').write_text(
            f'16 selected photos: {len(response.content)} bytes in self-contained deck\n'
            + '\n'.join(f'{p.width}x{p.height}: WebP {p.byte_size} bytes; thumbnail {len(p.thumb_data)} bytes'
                        for p in rows[:16]) + '\n')
    document = html.fromstring(response.content)
    slides = document.xpath('//section[@data-type="photo" or @data-type="before_after"]')
    assert [s.xpath('.//h2/text()')[0] for s in slides] == ['Fotoğraf 1', 'Fotoğraf 0'] + [f'Fotoğraf {i}' for i in range(2,14)] + ['Önce ve sonra']
    assert len(slides) == 15
    assert 'Seçilmemiş fotoğraf' not in response.text
    assert not re.search(rb'(?:src|href)=["\']https?://', response.content)
    assert all('data:image/webp;base64,' in s.xpath('.//*[@style]')[0].get('style') for s in slides)
    assert '29.10.2027' in response.text
    assert 'Fotoğraf: Test Müdürlüğü' in response.text
    assert all('—' not in ''.join(s.xpath('.//*[@class="meta" or @class="ba-meta"]//text()')) for s in slides)
    assert client.get(f'/activity-sections/reports/{own.id}/sunum').content == birim_before
    # Defensive rendering also handles legacy/corrupt incomplete selection.
    rows[15].selected = False
    db.commit()
    with caplog.at_level(logging.INFO):
        response = client.get(f"/activity-sections/reports/{docs['idare'].id}/sunum")
    assert 'Eksik önce/sonra çifti' in caplog.text
    assert 'data-type="before_after"' not in response.text


def test_photos_never_change_approved_payload_or_verification(photo_client, db, sample):
    client, docs, token = photo_client
    doc = docs['idare']
    ready_and_freeze(client, token, doc)
    export_before = client.get(f'/activity-sections/reports/{doc.id}/export.json').content
    deck_before = client.get(f'/activity-sections/reports/{doc.id}/sunum').text
    code = re.search(r'Doğrulama kodu <b>([^<]+)</b>', deck_before).group(1)
    assert upload(photo_client, sample).status_code == 303
    row = db.scalar(select(SunumPhoto))
    assert change(photo_client, row, 'toggle', 'on').status_code == 303
    after = client.get(f'/activity-sections/reports/{doc.id}/sunum').text
    assert 'data-type="photo"' in after
    assert f'Doğrulama kodu <b>{code}</b>' in after
    assert client.get(f'/activity-sections/reports/{doc.id}/export.json').content == export_before
    assert client.get(f'/activity-sections/reports/{doc.id}/export.json?version=1').content == export_before


def test_photo_group_follows_budget_and_preserves_council_scorecard(idare_fixture, db, sample):
    fixture = idare_fixture
    client, doc = fixture['client'], fixture['idare']
    url = f'/activity-sections/reports/{doc.id}/sunum'
    before = client.get(url).content
    upload_fixture = client, fixture['docs'], fixture['token']
    assert upload(upload_fixture, sample, image_bytes(42)).status_code == 303
    # Unselected assets must not even change the no-photo council HTML.
    assert client.get(url).content == before
    row = db.scalar(select(SunumPhoto))
    assert change(upload_fixture, row, 'toggle', 'on').status_code == 303
    document = html.fromstring(client.get(url).content)
    kinds = document.xpath('//section/@data-type')
    assert kinds.index('budget') < kinds.index('photo') < kinds.index('scorecard')
    titles = document.xpath('//section[@data-type="separator"]//*[@class="t"]/text()')
    assert titles == ['Kurumumuz', 'Bütçe', 'Tamamlanan işler', 'Göstergeler']


def test_photo_browser_drag_keyboard_pdf_and_screenshots(photo_client, db, sample, tmp_path):
    from playwright.sync_api import sync_playwright, expect
    from pypdf import PdfReader
    client, docs, _ = photo_client
    assert upload(photo_client, sample, image_bytes(0), caption='Hürriyet Mahallesi yol yenilemesi tamamlandı').status_code == 303
    assert upload(photo_client, sample, image_bytes(30), second=image_bytes(0), caption='100. Yıl Caddesi', mahalle='Karaağaç Mahallesi').status_code == 409
    assert upload(photo_client, sample, image_bytes(30), second=image_bytes(1), caption='100. Yıl Caddesi', mahalle='Karaağaç Mahallesi').status_code == 303
    for row in photos.list_photos(db, docs['idare']):
        assert change(photo_client, row, 'toggle', 'on').status_code == 303
    folder = Path(os.getenv('CIVENSA_PHOTO_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    content = client.get(f"/activity-sections/reports/{docs['idare'].id}/sunum").content
    path = tmp_path/'photos.html'
    path.write_bytes(content)
    sizes = [dict(webp=p.byte_size, thumbnail=len(p.thumb_data)) for p in photos.list_photos(db, docs['idare'])]
    (folder/'sizes.txt').write_text(f'Deck: {len(content)} bytes\nPhotos (WebP/thumbnail bytes): {sizes}\n')
    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_options())
        page = browser.new_page(viewport=dict(width=1920, height=1080), offline=True)
        errors, network = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda r: network.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
        url = deck_url(page, path)
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        page.evaluate('deck.slide(deck.getIndices(document.querySelector("[data-type=photo]")).h)')
        page.wait_for_timeout(1000)
        page.screenshot(path=str(folder/'photo-slide-1920.png'))
        page.evaluate('deck.slide(deck.getIndices(document.querySelector("[data-type=before_after]")).h)')
        page.wait_for_timeout(1800)
        wrap = page.locator('section.present .ba-wrap')
        handle = wrap.locator('.handle')
        expect(handle).to_have_attribute('aria-valuenow', '50')
        box = wrap.bounding_box()
        page.mouse.move(box['x']+box['width']/2, box['y']+box['height']/2)
        page.mouse.down()
        page.mouse.move(box['x']+box['width']*.65, box['y']+box['height']/2, steps=12)
        assert handle.get_attribute('aria-valuenow') == '65'
        assert float(wrap.evaluate('e=>e.style.getPropertyValue("--x")').rstrip('%')) == pytest.approx(65, abs=.1)
        page.screenshot(path=str(folder/'before-after-drag-1920.png'))
        page.mouse.up()
        index = page.evaluate('deck.getIndices().h')
        handle.focus()
        page.keyboard.press('ArrowLeft')
        expect(handle).to_have_attribute('aria-valuenow', '60')
        page.keyboard.press('ArrowRight')
        expect(handle).to_have_attribute('aria-valuenow', '65')
        assert page.evaluate('deck.getIndices().h') == index
        title = page.locator('section.present h2')
        original_title = title.inner_text()
        title.evaluate('(el)=>el.textContent=("Tamamlanan altyapı ve yol yenileme çalışmaları ".repeat(4)).slice(0,140)')
        metadata = page.locator('section.present .ba-meta').bounding_box()
        footer = page.locator('section.present .foot').bounding_box()
        assert metadata['y'] + metadata['height'] < footer['y']
        assert wrap.bounding_box()['height'] > 300
        title.evaluate('(el,text)=>el.textContent=text', original_title)
        assert not errors
        assert network == ([url] if url.startswith('http:') else [])
        page.goto(url+'#pdf')
        page.wait_for_function('() => window.sunumRendered === true && document.documentElement.classList.contains("pdf")')
        wrap = page.locator('.ba-wrap')
        assert wrap.locator('.handle').is_hidden()
        assert wrap.evaluate('e=>getComputedStyle(e).display') == 'grid'
        assert wrap.locator('.after-clip').evaluate('e=>getComputedStyle(e).clipPath') == 'none'
        left = wrap.locator(':scope > .img').bounding_box()
        right = wrap.locator('.after-clip').bounding_box()
        assert right['x'] > left['x'] + left['width']
        page.locator('.pdf-page').filter(has=wrap).screenshot(path=str(folder/'before-after-pdf-1920.png'))
        pdf = PdfReader(BytesIO(page.pdf(prefer_css_page_size=True, print_background=True)))
        assert len(pdf.pages) == page.locator('.pdf-page').count()
        assert sum('100. Yıl Caddesi' in p.extract_text() for p in pdf.pages) == 1
        # Render the real management response with its actual CSP and assets.
        page = browser.new_page(viewport=dict(width=1920, height=1080))
        def serve(route):
            response = client.get(route.request.url.replace('http://testserver', ''))
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        page.route('http://testserver/**', serve)
        page.goto(f"http://testserver/activity-sections/reports/{docs['idare'].id}/photos")
        expect(page.get_by_role('heading', name='Meclis sunumu fotoğrafları')).to_be_visible()
        assert page.locator('.photo-card img').evaluate_all('els=>els.every(e=>e.complete && e.naturalWidth>0)')
        page.locator('.photo-grid').first.scroll_into_view_if_needed()
        page.screenshot(path=str(folder/'photo-page-1920.png'))
        page.set_viewport_size(dict(width=390, height=844))
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(folder/'photo-page-390.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors
        browser.close()
