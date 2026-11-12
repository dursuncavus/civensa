"""CIV-218: the İç Kontrol question form keeps its save buttons on screen.

With 79 questions the buttons sat below ~80 rows; staff had to scroll to the
very end to save. The action bar is now sticky at the bottom of the viewport.
Static markup mirrors questionnaire_form.html (frozen) and uses the real CSS.
"""
from pathlib import Path

import pytest

from test_sidebar_ui import browser  # noqa: F401  (fixture)

ROOT = Path(__file__).resolve().parents[1]


def page_html(rows=79):
    tokens = (ROOT / 'app/static/design/tokens.css').read_text()
    css = (ROOT / 'app/static/design/internal-control.css').read_text()
    script = (ROOT / 'app/static/design/sticky-actions.js').read_text()
    body = ''.join(
        f'<tr><th scope="row">{n:02d} KOS<p>Soru metni {n}</p></th>'
        f'<td><label class="ic-choice"><input type="radio" name="a{n}">Evet</label></td>'
        f'<td><label>Açıklama<textarea name="e{n}"></textarea></label></td></tr>'
        for n in range(1, rows + 1))
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>{tokens}\n{css}</style></head>'
            '<body><div class="internal-control-page"><section class="card questionnaire-form"><h2>Soru formu</h2>'
            '<form method="post" action="/internal-control/questionnaires/batches/1/answers">'
            '<div class="ic-scroll" role="region" aria-label="Soru yanıtları" tabindex="0"><table class="ic-question-grid ic-question-form-table"><thead><tr>'
            '<th>Kod / Soru</th><th>Yanıt</th><th>Açıklama</th></tr></thead><tbody>'
            f'{body}</tbody></table></div><div class="ic-actions"><button class="button" id="save">Yanıtları kaydet</button>'
            '<button class="button primary" id="submit">Kaydet ve incelemeye gönder</button></div></form>'
            '<form method="post" action="/internal-control/questionnaires/batches/1/transition" id="transition">'
            '<label>İade / yeniden açma gerekçesi<textarea name="reason" id="reason"></textarea></label>'
            '<div class="ic-actions"><button class="button" id="return">Gerekçeli iade</button>'
            '<button class="button primary">Onayla</button></div></form>'
            f'</section></div><script>{script}</script></body></html>')


@pytest.mark.parametrize('width', [1440, 390])
def test_save_buttons_visible_at_top_middle_and_end(browser, width):  # noqa: F811
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        page = context.new_page()
        page.set_content(page_html())
        height = page.evaluate('document.documentElement.scrollHeight')
        assert height > 3 * 900, 'form must be much longer than the screen for this test'
        for y in (0, height // 2, height):
            page.evaluate(f'window.scrollTo(0, {y})')
            for button in ('#save', '#submit'):
                box = page.locator(button).bounding_box()
                assert box and 0 <= box['y'] and box['y'] + box['height'] <= 900, (y, button, box)
        # The bar must not hide the last question when scrolled to the end.
        last = page.locator('tbody tr').last.bounding_box()
        bar = page.locator('form[action$="/answers"] > .ic-actions').bounding_box()
        assert last['y'] + last['height'] <= bar['y'] + 1


def test_strategy_transition_form_is_not_sticky(browser):  # noqa: F811
    """Codex P2: the return/approve form in the same section keeps normal flow."""
    with browser.new_context(viewport={'width': 1440, 'height': 900}) as context:
        page = context.new_page()
        page.set_content(page_html())
        assert page.evaluate("getComputedStyle(document.querySelector('#transition .ic-actions')).position") == 'static'
        page.locator('#reason').scroll_into_view_if_needed()
        reason = page.locator('#reason').bounding_box()
        actions = page.locator('#transition .ic-actions').bounding_box()
        assert actions['y'] >= reason['y'] + reason['height']


@pytest.mark.parametrize('width', [1440, 390])
def test_keyboard_focus_never_hides_behind_the_bar(browser, width):  # noqa: F811
    """Codex P2: tabbing through intermediate rows keeps each control above the bar."""
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        page = context.new_page()
        page.set_content(page_html(rows=30))
        # Real keyboard entry: Tab from the page start reaches the focusable
        # scroll region first (Codex P2: it must not jump to the table end).
        page.keyboard.press('Tab')
        assert page.evaluate("document.activeElement.classList.contains('ic-scroll')")
        assert page.evaluate('window.scrollY') < 200  # browser's own small focus scroll only
        page.keyboard.press('Tab')
        checked = 0
        for _ in range(70):
            info = page.evaluate('''() => {
                const el = document.activeElement;
                if (!el.closest('tbody')) return null;
                const r = el.getBoundingClientRect();
                const bar = document.querySelector('form[action$="/answers"] > .ic-actions').getBoundingClientRect();
                return {bottom: r.bottom, barTop: bar.top, name: el.name};
            }''')
            if info is None:
                break
            assert info['bottom'] <= info['barTop'] + 0.5, info
            checked += 1
            page.keyboard.press('Tab')
        assert checked >= 50
