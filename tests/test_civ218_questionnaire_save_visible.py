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
    body = ''.join(
        f'<tr><th scope="row">{n:02d} KOS<p>Soru metni {n}</p></th>'
        f'<td><label class="ic-choice"><input type="radio" name="a{n}">Evet</label></td>'
        f'<td><label>Açıklama<textarea name="e{n}"></textarea></label></td></tr>'
        for n in range(1, rows + 1))
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>{tokens}\n{css}</style></head>'
            '<body><div class="internal-control-page"><section class="card questionnaire-form"><h2>Soru formu</h2>'
            '<form><div class="ic-scroll"><table class="ic-question-grid ic-question-form-table"><thead><tr>'
            '<th>Kod / Soru</th><th>Yanıt</th><th>Açıklama</th></tr></thead><tbody>'
            f'{body}</tbody></table></div><div class="ic-actions"><button class="button" id="save">Yanıtları kaydet</button>'
            '<button class="button primary" id="submit">Kaydet ve incelemeye gönder</button></div></form>'
            '</section></div></body></html>')


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
        bar = page.locator('.ic-actions').bounding_box()
        assert last['y'] + last['height'] <= bar['y'] + 1


def test_rule_targets_only_the_question_form():
    css = (ROOT / 'app/static/design/internal-control.css').read_text()
    assert '.questionnaire-form form > .ic-actions { position: sticky; bottom: 0;' in css
