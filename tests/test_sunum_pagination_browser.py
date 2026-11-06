"""CIV-186: offline 1920×1080 layout acceptance, normal and #pdf."""
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.sunum.engine import render_deck


LONG_ROW = 'Uzun açıklama ve ayrıntı ' * 26


@pytest.fixture
def pagination_deck():
    # 2026 PP Sorumlu İdare names, with the reference builder's three aliases.
    names = json.loads((Path(__file__).parent / 'fixtures/sunum_33_departments.json').read_text())
    assert len(names) == 33
    common = dict(source='2026 Performans Programı · 2025 Planlanan ve 2025 Yıl Sonu Gerçekleşme Tahmini',
                  eyebrow='2025 Faaliyet Raporu')
    return [dict(common, type='table', title='Müdürlüklere göre gösterge özeti',
                 headers=['Müdürlük', 'Gösterge sayısı', 'Tahmini girilen', 'Ortalama oran (%)'],
                 rows=[[name, 12, 11, '75,6'] for name in names]),
            dict(common, type='scorecard', title='Müdürlük karnesi', summary=[dict(css='ok', display='33', label='müdürlük')],
                 rows=[dict(name=name + ' · ' + name, measured_display='12', met_display='9', width=75,
                            percentage='%75', css='ok', status='Hedefte', expandable=False) for name in names]),
            dict(common, type='bullets', title='Görev ve sorumluluklar',
                 bullets=[name + ': ' + 'Vatandaş taleplerini değerlendirerek hizmetleri planlamak ve sonuçları raporlamak. ' * 2 for name in names]),
            # Mixed lengths: two wrapped names + four short ones must stay one compact page of six.
            dict(common, type='scorecard', title='Karma karne', summary=[dict(css='ok', display='6', label='müdürlük')],
                 rows=[dict(name=name, measured_display='12', met_display='9', width=75, percentage='%75',
                            css='ok', status='Hedefte', expandable=False)
                       for name in [names[0] + ' · ' + names[0], names[1] + ' · ' + names[1]] + names[2:6]]),
            # Over the 10-unit budget by estimate, but still physically fits on its own slide.
            dict(common, type='table', title='Tek uzun satır', headers=['Açıklama', 'Adet'],
                 rows=[['Önce', 1], [LONG_ROW, 1], ['Sonra', 1]])]


@pytest.mark.parametrize('pdf', [False, True], ids=['normal', 'pdf'])
def test_all_paginated_slides_clear_footer(tmp_path, pagination_deck, pdf):
    content = render_deck(pagination_deck, title='CIV-186 · 33 müdürlük', code='DENEME')
    folder = Path(os.environ.get('CIVENSA_SUNUM_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'pagination.html').write_bytes(content)
    options = {'headless': True}
    if os.getenv('CIVENSA_CHROMIUM_PATH'):
        options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, reduced_motion='no-preference' if pdf else 'reduce', offline=True)
        url = 'http://testserver/pagination.html'
        page.route(url, lambda route: route.fulfill(content_type='text/html', body=content))
        page.goto(url + ('#pdf' if pdf else ''))
        page.wait_for_function('() => window.sunumRendered === true')
        if pdf:
            # Reveal print pages are painted by its print stylesheet.
            page.emulate_media(media='print')
        sections = page.locator('section[data-type]')
        counts = {'table': 0, 'scorecard': 0, 'bullets': 0}
        for i in range(sections.count()):
            section = sections.nth(i)
            kind = section.get_attribute('data-type')
            counts[kind] += 1
            if not pdf:
                page.evaluate('(i) => deck.slide(i, 0, 999)', i)
                page.wait_for_function('(i) => document.querySelectorAll("section[data-type]")[i].classList.contains("present")', arg=i)
                # Finish Reveal's slide transition before measuring or capturing.
                page.wait_for_timeout(850)
            measurement = section.evaluate('''section => {
                const rows = [...section.querySelectorAll('tbody tr, .score .r, ul.b li')];
                const last = rows.at(-1).getBoundingClientRect();
                const footer = section.querySelector('.foot').getBoundingClientRect();
                return {bottom: last.bottom, footer: footer.top,
                        right: last.right, slideRight: section.getBoundingClientRect().right};
            }''')
            assert measurement['bottom'] < measurement['footer'], (i, kind, measurement)
            assert measurement['right'] <= measurement['slideRight'], (i, kind, measurement)
            # All requested table pages, long scorecard/items and the same #pdf table.
            target = section.locator('xpath=..') if pdf else page.locator('body')
            target.screenshot(path=str(folder / f'{"pdf" if pdf else "normal"}-{kind}-{counts[kind]:02}.png'))
        assert all(count > 1 for count in counts.values())
        mixed = sections.filter(has=page.locator('h2', has_text='Karma karne'))
        assert mixed.count() == 1 and mixed.first.locator('.score .r').count() == 6
        long_sections = sections.filter(has=page.locator('h2', has_text='Tek uzun satır'))
        assert long_sections.count() == 3
        assert long_sections.nth(1).locator('tbody tr').count() == 1
        assert long_sections.nth(1).locator('tbody td').first.inner_text() == LONG_ROW.strip()
        browser.close()
