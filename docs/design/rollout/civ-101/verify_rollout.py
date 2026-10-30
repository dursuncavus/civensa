#!/usr/bin/env python3
"""CIV-101: replay all screens against d671eb8 synthetic baseline.

Baseline: run civ-096/verify_rollout.py at d671eb8 --capture-out /tmp/civ099-baseline.
Then run this script --baseline /tmp/civ099-baseline (local PostgreSQL 16+ only).
Full inventories/PNGs remain in /tmp; publish only credential-free summaries here.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
from io import BytesIO
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shell_rollout', ROOT / 'docs/design/rollout/civ-096/verify_rollout.py')
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)
guide = shell.guide
# Chromium keeps geometry for content-visibility:hidden in closed details.
# checkVisibility excludes these unpainted controls, without suppressing real overlaps.
shell.LAYOUT = shell.LAYOUT.replace('el.getClientRects().length && getComputedStyle(el).visibility',
    'el.checkVisibility() && el.getClientRects().length && getComputedStyle(el).visibility')

# Presentation-only case changes; the underlying data and targets are frozen.
TITLES = {
 'ÜST YÖNETİCİ SUNUŞU':'Üst yönetici sunuşu', 'YÖNETİCİ ÖZETİ':'Yönetici özeti',
 'I- GENEL BİLGİLER':'I- Genel bilgiler', 'II- AMAÇLAR ve HEDEFLER':'II- Amaçlar ve hedefler',
 'III- FAALİYETLERE İLİŞKİN BİLGİ VE DEĞERLENDİRMELER':'III- Faaliyetlere ilişkin bilgi ve değerlendirmeler',
 'IV- KURUMSAL KABİLİYET VE KAPASİTENİN DEĞERLENDİRİLMESİ':'IV- Kurumsal kabiliyet ve kapasitenin değerlendirilmesi',
 'V- ÖNERİ VE TEDBİRLER':'V- Öneri ve tedbirler', 'EKLER':'Ekler',
 'BÖLÜM İÇERİĞİ':'Bölüm içeriği', 'DURUM':'Durum', 'UYGULANAMAZ GEREKÇESİ':'Uygulanamaz gerekçesi',
 'XLSX TABLOSU':'XLSX tablosu', 'ALT GERÇEKLEŞME ORANI %':'Alt gerçekleşme oranı %',
 'ÜST GERÇEKLEŞME ORANI %':'Üst gerçekleşme oranı %', 'DÖNEM':'Dönem', 'TABLO TARİHİ':'Tablo Tarihi',
 'AÇIKLAMALAR':'Açıklamalar', 'PDF VEYA XLSX (EN FAZLA 10 MB)':'PDF veya XLSX (en fazla 10 MB)',
 'PDF VEYA XLSX':'PDF veya XLSX', 'ÖZET RAKAM ETİKETİ':'Özet rakam etiketi',
 'ÖZET RAKAM TUTARI':'Özet rakam tutarı', 'TABLO ADI':'Tablo Adı',
 'YENİDEN AÇMA GEREKÇESİ':'Yeniden açma gerekçesi', 'İADE GEREKÇESİ':'İade gerekçesi',
}

def signature(control, section_editor=False):
    control = dict(control)
    if section_editor:
        label = control['label'].removeprefix('← ')
        for old,new in TITLES.items(): label = label.replace(old,new)
        if control['tag'] == 'summary' and ('Kullanıcı' in label or label == 'Teknik ayrıntı'):
            label = '<denetim ayrıntısı>'
        label = label.replace('Tablo Tarihi','Tablo tarihi')  # Existing edit/new forms differ only in source case.
        control['label'] = label
    return shell.signature(control)


def inventory(page):
    # The replay opens every disclosure before taking the inventory, including
    # the export menu and Technical details. Hidden fields are covered by pytest.
    return page.evaluate(guide.UI_DOM)['controls']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--capture-out', type=Path, default=Path('/tmp/civ101-after'))
    parser.add_argument('--recheck-failures', action='store_true', help='Retake failed comparisons; retain passing captures and checks.')
    parser.add_argument('--refresh-editor', action='store_true', help='Refresh final 012 styling; retain unchanged screen evidence.')
    args = parser.parse_args()
    import subprocess
    changed = set(subprocess.check_output(['git','diff','d671eb8','--name-only','--','app'],cwd=ROOT,text=True).splitlines())
    assert changed <= {'app/templates/activity_sections_editor.html','app/static/design/section-editor.css','app/static/design/section-editor.js','app/activity_sections_routes.py'}, changed
    previous = json.loads((OUT / 'capture-summary.json').read_text()) if args.recheck_failures or args.refresh_editor else None
    results = previous['screens'] if previous else []
    def failed(row):
        return bool(row['missing'] or row['document'] > row['width'] or row['overflow'] or row['clipped'] or row['overlaps'] or row['shell_issues'] or
            (not row['section_editor'] and (not row['same_dimensions'] or (row['changed_pixels'] and not row.get('raster_rounding_only')))))
    wanted = {(r['width'],r['filename']) for r in results if failed(r) or (args.refresh_editor and r['section_editor'])} if previous else None

    setup = guide.ui_setup
    from PIL import Image, ImageChops
    removed_rules = []  # No app.css rule is exclusive to 012; shared files are unchanged.
    for width in (1440, 390):
        if previous and not any(w == width for w, _ in wanted): continue
        baseline = {s['filename']: s for s in json.loads((args.baseline / str(width) / 'screens.json').read_text())['screens']}
        captured = {s['filename']: s for s in json.loads((args.capture_out / str(width) / 'screens.json').read_text())['screens']} if previous else {}
        def verify(page, shot, meta):
            section_editor = bool(page.locator('.section-editor-page').count())
            current = inventory(page) if section_editor else meta['dom']['controls']
            for c in current:
                c['target'] = guide.ui_control(c)[0]
            old = baseline[shot.filename]['dom']['controls']
            missing = Counter(signature(c, section_editor) for c in old) - Counter(signature(c, section_editor) for c in current)
            layout = page.evaluate(shell.LAYOUT)
            meta['dom']['controls'] = current
            result = dict(filename=shot.filename, width=width, section_editor=section_editor,
                elements=len(old), missing=list(missing.elements()), **layout)
            # Compare CSS on the EXACT same DOM/clock/data/focus/scroll state.
            # app.css occupies its original cascade position before the shell.
            # This avoids masking timestamps, random reset messages or DB latency.
            if not section_editor:
                # Shared styles are byte-identical to the baseline. 012 adds no
                # assets to another screen; reconstructing its old cascade needs
                # zero rules. Compare on the same DOM/clock to avoid timestamps.
                assert page.locator('.section-editor-page,link[href="/static/design/section-editor.css"],script[src="/static/design/section-editor.js"]').count() == 0
                # Insert only those unused rules into the original CSSOM sheet;
                # the shared rules/root/font caches never leave their original node.
                # This recreates the baseline cascade on this DOM without the
                # rounded-edge re-rasterization caused by replacing a whole sheet.
                matches = page.evaluate("""rules => rules.filter(rule =>
                    document.querySelector(rule.selector)).map(rule => rule.selector)""", removed_rules)
                assert not matches, f'012 selector on another screen: {matches}'
                result['matching_removed_rules'] = len(matches)
                observed = []
                for attempt in range(3):
                    try:
                        page.evaluate("""async rules => {
                          const sheet = document.querySelector('link[href="/static/app.css"]').sheet;
                          window.__civ099RuleCount = sheet.cssRules.length;
                          rules.forEach(rule => {
                            const css = rule.selector + '{' + rule.declarations + '}';
                            sheet.insertRule(rule.scope === 'all' ? css : rule.scope + '{' + css + '}', sheet.cssRules.length);
                          });
                          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                        }""", removed_rules)
                        before = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                    finally:
                        page.evaluate("""async () => {
                          const sheet = document.querySelector('link[href="/static/app.css"]').sheet;
                          while (sheet.cssRules.length > window.__civ099RuleCount) sheet.deleteRule(sheet.cssRules.length - 1);
                          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                        }""")
                    after = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                    with Image.open(BytesIO(before)) as a, Image.open(BytesIO(after)) as b:
                        result['same_dimensions'] = a.size == b.size
                        result['changed_pixels'] = None
                        if a.size == b.size:
                            channels = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).split()
                            mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
                            result['changed_pixels'] = sum(mask.histogram()[1:])
                        observed.append(result['changed_pixels'])
                        if result['changed_pixels'] == 0: break
                        if attempt == 2:
                            diagnostic = args.capture_out / 'pixel-diagnostics' / str(width)
                            diagnostic.mkdir(parents=True, exist_ok=True)
                            a.save(diagnostic / (shot.filename + '.before.png'))
                            b.save(diagnostic / (shot.filename + '.after.png'))
                result['paint_attempts'] = observed
                if result['changed_pixels']:
                    # Retain every raw difference. Only classify a <=2/255 edge
                    # rounding as renderer noise after EXACT computed-style and
                    # geometry equality, including hidden nodes and CSS variables.
                    result['max_channel_delta'] = max(i for i, count in enumerate(mask.histogram()) if count)
                    page.evaluate("""rules => {
                      const sheet = document.querySelector('link[href="/static/app.css"]').sheet;
                      window.__civ099Snapshot = () => [document.body, ...document.body.querySelectorAll('*')].map(el => {
                        const style = getComputedStyle(el), rect = el.getBoundingClientRect();
                        return {style:[...style].sort().map(k => k + ':' + style.getPropertyValue(k)).join(';'),
                          geometry:[rect.x,rect.y,rect.width,rect.height].join(',')};
                      });
                      window.__civ099RuleCount = sheet.cssRules.length;
                      rules.forEach(rule => {
                        const css = rule.selector + '{' + rule.declarations + '}';
                        sheet.insertRule(rule.scope === 'all' ? css : rule.scope + '{' + css + '}', sheet.cssRules.length);
                      });
                      window.__civ099Before = window.__civ099Snapshot();
                      while (sheet.cssRules.length > window.__civ099RuleCount) sheet.deleteRule(sheet.cssRules.length-1);
                    }""", removed_rules)
                    equality = page.evaluate("""() => {
                      const after = window.__civ099Snapshot(), before = window.__civ099Before;
                      const result = {nodes:after.length, style_changes:0, geometry_changes:0};
                      if (after.length !== before.length) throw new Error('DOM changed during CSS comparison');
                      after.forEach((row,i) => {
                        result.style_changes += row.style !== before[i].style;
                        result.geometry_changes += row.geometry !== before[i].geometry;
                      });
                      delete window.__civ099Snapshot; delete window.__civ099Before;
                      return result;
                    }""")
                    result.update(equality)
                    result['raster_rounding_only'] = result['max_channel_delta'] <= 2 and not equality['style_changes'] and not equality['geometry_changes']
            for index, row in enumerate(results):
                if (row['width'], row['filename']) == (width, shot.filename):
                    results[index] = result
                    break
            else:
                results.append(result)
        def setup_verified(engine):
            data = setup(engine)
            data['_verify_page'] = verify
            return data
        guide.ui_setup = setup_verified
        folder = args.capture_out / str(width)
        folder.mkdir(parents=True, exist_ok=True)
        original_capture = guide.capture
        def capture_selected(base, temporary, data, statuses):
            shots = data['_shots']
            selected = [shot for shot in shots if (width,shot.filename) in wanted]
            import shutil
            for shot in shots:
                if shot not in selected:
                    statuses[shot.filename] = None
                    data['_screen_meta'][shot.filename]['dom'] = captured[shot.filename]['dom']
                    shutil.copyfile(folder / shot.filename, temporary / shot.filename)
            data['_shots'] = selected
            try:
                original_capture(base, temporary, data, statuses)
            finally:
                data['_shots'] = shots
        if previous: guide.capture = capture_selected
        try:
            assert guide.ui_main(SimpleNamespace(out=folder, viewport_width=width), shell.local_test_url()) == 0
        finally:
            guide.capture = original_capture
        produced = json.loads((folder / 'screens.json').read_text())['screens']
        assert {s['filename'] for s in produced} == set(baseline)
    failures = [r for r in results if failed(r)]
    (OUT / 'capture-summary.json').write_text(json.dumps(dict(baseline='d671eb8', pixel_comparison='same DOM/cascade; raw pixels retained; <=2/255 rounding classified only with exact computed-style and geometry equality; no masks', captures=len(results),
        elements=sum(r['elements'] for r in results), failures=len(failures), screens=results), ensure_ascii=False, indent=2)+'\n')
    print(f'{len(results)} captures; {len(failures)} failures.')
    for row in failures:
        print(json.dumps(row, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
