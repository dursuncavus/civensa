"""CIV-199 deliberate screen changes, undone before the older frozen contracts.

Each function reverses exactly one change that tests/test_civ199_screen_cleanup.py
asserts directly; everything else on the page stays under the frozen contract.
"""
import re


def single_organization_as_select(html):
    """(2) A lone organization is shown as text plus a hidden id; frozen pages had a select."""
    return re.sub(
        r'<div class="single-organization" hidden><span>Kurum</span><b>(.*?)</b>\s*'
        r'<input type="hidden" name="organization_id" value="(\d+)"></div>',
        lambda m: (f'<label>Kurum<select name="organization_id"{" required" if "/activity-reports/revisions" in html else ""}>'
                   f'<option value="{m.group(2)}">{m.group(1)}</option></select></label>'),
        html, flags=re.S)


def without_mapping_sentence(html):
    """(4) The plain-language sentence and to-do list are new; the counters are folded but unchanged.
    The help text now names the real place for card/catalogue links, which each group links to."""
    html = re.sub(r'<p class="mapping-sentence" data-mapping-sentence>.*?</p>\s*', '', html, flags=re.S)
    html = re.sub(r'<ol class="mapping-todo" data-mapping-todo>.*?</ol>\s*', '', html, flags=re.S)
    html = re.sub(r'<details class="mapping-counts-details"><summary>Bütün sayılar</summary>\s*(<dl class="mapping-counts">.*?</dl>)\s*</details>',
                  r'\1', html, flags=re.S)
    html = re.sub(r'\s*<a class="button small" data-program-link href="[^"]*">Performans kartlarını aç</a>', '', html)
    html = re.sub(r'<span class="group-actions">(<a class="button small" href="[^"]*">Müdürlüğü Aç</a>)</span>', r'\1', html)
    return html.replace('Kart ve katalog bağlantıları müdürlüğün “Performans kartlarını aç” bağlantısındaki sayfada yapılır.',
                        'Kart ve katalog bağlantıları için “Performans Kartlarını Aç” adımını kullanın.')


def report_builder_original_order(html):
    """(3) Publication cards were below the page body; the reconciliation table was open."""
    start = min((html.find(marker) for marker in (
        '<section class="report-panel" id="approved-book-publication">',
        '<section class="report-panel report-publish">') if marker in html), default=-1)
    history = html.find('id="publication-history"')
    if start >= 0 and history >= 0:
        end = html.index('</section>', history) + len('</section>')
        block, html = html[start:end], html[:start] + html[end:]
        split = block.index('<section aria-label="Yayın sürümleri"')
        cards, history_block = block[:split], block[split:]
        # Original order: cards, the unmatched-attempt fallback (if any), history.
        fallback = re.search(r'<form class="record" method="post" action="[^"]*" enctype="multipart/form-data">\s*'
                             r'<h3>Kaydedilemeyen form</h3>.*?</form>', html, flags=re.S)
        if fallback:
            html = html[:fallback.start()] + cards + fallback.group(0) + history_block + html[fallback.end():]
        else:
            page_end = html.rindex('</div>', 0, html.index('</main>')) if '</main>' in html else len(html)
            html = html[:page_end] + cards + history_block + html[page_end:]
    html = re.sub(r'<p class="muted pp-reconciliation-scope">.*?</p>\s*', '', html, flags=re.S)
    html = re.sub(
        r'<details class="pp-reconciliation-table"><summary>(?:<span class="pp-reconciliation-alert">(\d+) satırda yayın engeli var</span> · )?Tabloyu göster \(\d+ satır\)</summary>\s*',
        lambda m: (f'<p class="warning-panel pp-reconciliation-alert">{m.group(1)} satırda yayın engeli var. '
                   'Ayrıntıyı ilgili satırdaki “Ayrıntı” bağlantısından açın.</p>\n') if m.group(1) else '',
        html, flags=re.S)
    html = re.sub(r'(</table></div>)\s*</details>(\s*</section>)', r'\1\2', html)
    return html


def bindings_without_search_and_saved(html):
    """(8) Search box, row anchors and the one-row "Kaydedildi" note are new on the bindings page."""
    html = re.sub(r'<div class="binding-search">.*?</div>\s*', '', html, count=1, flags=re.S)
    html = re.sub(r'<p class="status success binding-saved" role="status">.*?</p>\s*', '', html, flags=re.S)
    html = re.sub(r'<section class="binding-row(?: is-saved)?" id="gosterge-[^"]*" data-search="[^"]*">',
                  '<section class="binding-row">', html)
    return re.sub(r'<script src="/static/design/indicator-bindings.js" defer></script>\s*', '', html)


def sections_without_folds(html):
    """(10) EK-1 completion: directorate search, card grid with a sections dialog, folded exports are new."""
    html = re.sub(r'<div class="report-search">.*?</div>\s*', '', html, count=1, flags=re.S)
    html = re.sub(r'<div class="report-list(?: report-grid)?">\s*', '', html, count=1)
    html = re.sub(r'</div>\s*</section>(\s*<section class="index-panel"><h2>Word ve PDF)', r'</section>\1', html, count=1)
    html = re.sub(r'<button type="button" class="button report-open" data-open-dialog="[^"]*">Bölümleri aç</button>\s*'
                  r'<dialog class="report-dialog"[^>]*><div class="report-dialog-head"><h3[^>]*>.*?</h3><form method="dialog">'
                  r'<button class="button">Kapat</button></form></div>', '', html, flags=re.S)
    html = re.sub(r'</dialog>\s*</article>', '</article>', html)
    html = re.sub(r'<details class="exports-fold"><summary>\d+ müdürlük raporunun Word ve PDF dosyalarını göster</summary>\s*', '', html)
    html = re.sub(r'</details>\s*</section>', '</section>', html)
    # (12) owners on their own line; row warnings fold to one line.
    html = re.sub(r'<span class="summary-owners">(.*?)</span></p>', r' · \1</p>', html)
    html = re.sub(r'<details class="row-warnings"><summary>(<h4>.*?</h4>) · \d+</summary>(.*?)</details>', r'\1\2', html, flags=re.S)
    return re.sub(r'<script src="/static/design/section-index.js" defer></script>\s*', '', html)


def mapping_without_folds(html):
    """(10, 11) Many directorates become cards; each card opens its activities in a <dialog>."""
    html = html.replace('mapping-groups mapping-grid', 'mapping-groups').replace('mapping-group mapping-card', 'mapping-group')
    html = re.sub(r'\s*<button type="button" class="button small primary mapping-open" data-open-dialog="[^"]*">Faaliyetleri aç</button>', '', html)
    html = re.sub(r'<p class="muted mapping-hits" data-mapping-hits role="status"></p>\s*', '', html)
    html = re.sub(r'<dialog class="app-dialog mapping-dialog".*?</form></div>\s*', '', html, flags=re.S)
    return re.sub(r'\s*<div class="app-dialog-foot">.*?</dialog>', '', html, flags=re.S)


def bindings_without_department_folds(html):
    """(10) Indicator rows fold per directorate."""
    html = re.sub(r'<details class="binding-dept"(?: open)?>\s*<summary>.*?</summary>\s*', '', html, flags=re.S)
    html = re.sub(r'</section>\s*</details>', '</section>', html)
    # (11) or, with more than three directorates, a card whose indicators open in a <dialog>.
    html = html.replace('reports-panel binding-grid', 'reports-panel')
    html = re.sub(r'<article class="binding-card" data-binding-card>.*?</form></div>\s*', '', html, flags=re.S)
    return re.sub(r'</section>\s*</dialog>\s*</article>', '</section>', html)
