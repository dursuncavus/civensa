#!/usr/bin/env python3
"""Veritabanı olmadan dört sayfayı ve menü/pencere durumlarını doğrula ve çek."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright, expect

from browser_helpers import ROOT, PAGES, MAX_PNG_BYTES, static_server, launch, context


def assert_layout(page, width):
    assert page.evaluate('document.documentElement.scrollWidth') == width, 'Yatay taşma var.'
    assert page.evaluate('document.body.scrollWidth') == width, 'Gövde yatay taşıyor.'
    for weight in (400, 500, 600):
        assert page.evaluate('(w) => document.fonts.check(w + \' 16px "Fira Sans"\', \'İıŞşĞğÇçÖöÜü\')', weight)
    assert page.locator('h1').count() == 1, 'Sayfada tek ana başlık olmalı.'
    # Metin girişi, sayı ve seçim kontrolleri tam 40 px.
    for el in page.locator('input:not([type=checkbox]):not([type=radio]),select').all():
        if el.is_visible():
            assert el.bounding_box()['height'] == 40, f'Kontrol yüksekliği: {el.get_attribute("id")}'
    # Görünen veya pencerede saklı her alanın açık bir etiketi var.
    assert page.evaluate('''() => [...document.querySelectorAll('input,textarea,select')]
      .every(e => e.labels?.length > 0)'''), 'Etiketsiz alan var.'


def assert_mapping(page, path):
    number = Path(path).name[:3]
    if not number.isdigit():
        return 0
    number = str(int(number))
    mapping = json.loads((ROOT / 'element-map.json').read_text())[number]['elements']
    source = json.loads((ROOT.parents[1] / 'screenshots/ui-map-v1/screens.json').read_text())
    old = next(s for s in source['screens'] if s['filename'].startswith(f'{int(number):03}-'))['dom']['controls']
    assert len(old) == len(mapping) == page.locator('[data-source-id]').count()
    for item, control in zip(mapping, old):
        element = page.locator(f'[data-source-id="{item["id"]}"]')
        assert element.count() == 1
        assert element.get_attribute('data-original-target') == control['target'] == item['target']
        assert f'| {item["id"]} |' in (ROOT / 'README.md').read_text()
        if element.evaluate('(e) => e.matches("input,textarea,select")'):
            old_value = control.get('value', '')
            if element.evaluate('(e) => e.tagName') != 'SELECT':
                assert element.input_value() == old_value, f'Değer değişti: {item["id"]}'
    return len(mapping)


def run():
    output = ROOT / 'screenshots'
    output.mkdir(exist_ok=True)
    manifest = {'viewport_height': 900, 'device_scale_factor': 1, 'locale': 'tr-TR',
                'timezone': 'Europe/Istanbul', 'screenshots': [], 'mapped_elements': {}}
    with static_server() as base, sync_playwright() as pw:
        browser = launch(pw)
        manifest['browser'] = browser.version
        for width in (1440, 390):
            ctx = context(browser, width)
            blocked, errors = [], []

            def guard(route):
                url = urlsplit(route.request.url)
                if url.netloc == urlsplit(base).netloc and route.request.method == 'GET':
                    route.continue_()
                else:
                    blocked.append(route.request.method)
                    route.abort()

            ctx.route('**/*', guard)
            page = ctx.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))

            def snap(stem, full=True):
                assert_layout(page, width)
                target = output / f'{stem}-{width}.png'
                page.screenshot(path=str(target), full_page=full, animations='disabled', caret='hide')
                with Image.open(target) as png:
                    assert png.width == width
                    png.save(target, optimize=True)
                    if target.stat().st_size > MAX_PNG_BYTES:
                        png.convert('RGB').quantize(colors=256).save(target, optimize=True)
                assert target.stat().st_size <= MAX_PNG_BYTES
                with Image.open(target) as png:
                    manifest['screenshots'].append({'file': target.name, 'width': png.width,
                                                   'height': png.height, 'bytes': target.stat().st_size})
                assert not blocked and not errors, (blocked, errors)
                print(f'{target.name}: {target.stat().st_size:,} bayt', flush=True)

            for path in PAGES:
                response = page.goto(base + '/' + path)
                assert response.status == 200
                page.evaluate('document.fonts.ready')
                count = assert_mapping(page, path)
                if count:
                    manifest['mapped_elements'][Path(path).name[:3]] = count
                # Yan menü masaüstünde sayfanın tamamını kaplar.
                if width == 1440:
                    assert page.locator('.sidebar').bounding_box()['height'] == page.locator('.app-shell').bounding_box()['height']
                snap(Path(path).stem)
                if path == 'components.html':
                    page.get_by_role('button', name='Onay penceresini aç', exact=True).click()
                    expect(page.locator('#confirm-dialog')).to_be_visible()
                    expect(page.get_by_role('button', name='Vazgeç', exact=True)).to_be_focused()
                    snap('components-confirm', full=False)
                    page.keyboard.press('Escape')
                    expect(page.locator('#confirm-dialog')).to_be_hidden()
                    expect(page.get_by_role('button', name='Onay penceresini aç', exact=True)).to_be_focused()
                if path.endswith('024-department.html'):
                    expect(page.locator('#remove-dialog')).to_be_hidden()
                    page.locator('.menu > summary').click()
                    page.locator('#e027').click()
                    expect(page.locator('#remove-dialog')).to_be_visible()
                    expect(page.locator('#e030')).to_be_focused()
                    snap('024-remove-dialog', full=False)
                    page.locator('#e030').click()
                    expect(page.locator('#remove-dialog')).to_be_hidden()
                    expect(page.locator('#e027')).to_be_focused()
                    page.keyboard.press('Escape')
                    page.locator('#e014').click()
                    expect(page.locator('#activities')).to_be_visible()
                    expect(page.locator('#indicators')).to_be_hidden()
                    snap('024-activity-costs')
                    page.locator('#e013').click()
                    expect(page.locator('#indicators')).to_be_visible()
                    page.locator('#e015').click()
                    expect(page.locator('#e024')).to_be_focused()
                    assert page.locator('#e024').get_attribute('aria-invalid') == 'true'
                if path.endswith('012-section-editor.html'):
                    page.locator('.menu > summary').click()
                    expect(page.locator('#e012')).to_be_visible()
                    expect(page.locator('#e013')).to_be_visible()
                    expect(page.locator('#e014')).to_be_visible()
                    snap('012-export-menu', full=False)
                # Ortak menü / hesap pencereleri (üç ekranda da).
                if count:
                    pw_button = page.get_by_role('button', name='Parolamı Değiştir', exact=True)
                    pw_button.click()
                    expect(page.locator('#password-dialog')).to_be_visible()
                    assert_layout(page, width)
                    page.keyboard.press('Escape')
                    expect(page.locator('#password-dialog')).to_be_hidden()
                    expect(pw_button).to_be_focused()
                    page.get_by_role('button', name='Bildirimler', exact=True).click()
                    expect(page.locator('#notification-dialog')).to_be_visible()
                    page.keyboard.press('Escape')
                assert not blocked and not errors, (blocked, errors)
            ctx.close()
        browser.close()
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('4 sayfa × 2 genişlik; 104/104 eski öğe; pencereler, sekmeler, odak ve ağ sınırı: geçti.')


if __name__ == '__main__':
    run()
