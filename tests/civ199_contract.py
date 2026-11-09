"""CIV-199 deliberate screen changes, undone before the older frozen contracts.

Each function reverses exactly one change that tests/test_civ199_screen_cleanup.py
asserts directly; everything else on the page stays under the frozen contract.
"""
import re


def single_organization_as_select(html):
    """(2) A lone organization is shown as text plus a hidden id; frozen pages had a select."""
    return re.sub(
        r'<div class="single-organization"><span>Kurum</span><b>(.*?)</b>\s*'
        r'<input type="hidden" name="organization_id" value="(\d+)"></div>',
        lambda m: (f'<label>Kurum<select name="organization_id"{" required" if "/activity-reports/revisions" in html else ""}>'
                   f'<option value="{m.group(2)}">{m.group(1)}</option></select></label>'),
        html, flags=re.S)


def without_mapping_sentence(html):
    """(4) The plain-language sentence is new; the counters below it are unchanged."""
    return re.sub(r'<p class="mapping-sentence" data-mapping-sentence>.*?</p>\s*', '', html, flags=re.S)


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
    return re.sub(r'<script>\s*\(function\(\)\{\s*const input=document.getElementById\(\'bindingSearch\'\).*?</script>\s*',
                  '', html, flags=re.S)
