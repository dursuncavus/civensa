#!/usr/bin/env python3
"""Replay every screen at both widths against a pre-change synthetic capture.

Before changes, replay guide.ui_main from a detached base worktree into --baseline.
Only local disposable PostgreSQL is used. Complete PNGs/inventories stay in /tmp.
For other screens compare baseline/current CSS on the SAME DOM, clock and focus.
"""
import argparse
from collections import Counter
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('civ096', ROOT / 'docs/design/rollout/civ-096/verify_rollout.py')
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)
guide = shell.guide


def inventory(page):
    """Union open/closed controls with multiplicities; disclose without writing."""
    controls = Counter(json.dumps(c, sort_keys=True, ensure_ascii=False)
        for c in page.evaluate(guide.UI_DOM)['controls'])
    for panel in page.locator('.source-disclosure').all():
        was_open = panel.evaluate('el => el.open')
        panel.evaluate('el => el.open = true')
        controls |= Counter(json.dumps(c, sort_keys=True, ensure_ascii=False)
            for c in page.evaluate(guide.UI_DOM)['controls'])
        panel.evaluate('(el, value) => el.open = value', was_open)
    return [json.loads(c) for c in controls.elements()]


def pixel_difference(before, after):
    from PIL import Image, ImageChops
    with Image.open(BytesIO(before)) as a, Image.open(BytesIO(after)) as b:
        assert a.size == b.size
        red, green, blue = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).split()
        histogram = ImageChops.lighter(ImageChops.lighter(red, green), blue).histogram()
        return sum(histogram[1:]), max(i for i, count in enumerate(histogram) if count)


SNAPSHOT = r"""() => [document.body, ...document.body.querySelectorAll('*')].map(el => {
  const style=getComputedStyle(el), r=el.getBoundingClientRect();
  return {style:[...style].sort().map(k=>k+':'+style.getPropertyValue(k)).join(';'),
    geometry:[r.x,r.y,r.width,r.height].join(',')};
})"""


def failed(row):
    return bool(row['missing'] or row['document'] != row['width'] or
        any(row[k] for k in ('overflow','clipped','overlaps','shell_issues')) or
        ((row.get('changed_pixels',0) or row.get('unchanged_state_pixels',0)) and not row.get('raster_rounding_only')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--base-ref', required=True)
    parser.add_argument('--recheck-failures', action='store_true', help='Retain successful captures; repeat failed comparisons with raw pixel/style/geometry diagnostics.')
    parser.add_argument('--capture-out', type=Path, default=Path('/tmp/civ100-after'))
    args = parser.parse_args()
    baseline_css = subprocess.check_output(['git', 'show', args.base_ref + ':app/static/design/data-entry.css'], cwd=ROOT, text=True)
    setup = guide.ui_setup
    previous = json.loads((OUT / 'capture-summary.json').read_text()) if args.recheck_failures else None
    results = previous['screens'] if previous else []
    wanted = {(r['width'],r['filename']) for r in results if failed(r)} if previous else None
    for width in (1440, 390):
        if previous and not any(w == width for w, _ in wanted):
            continue
        captured = {s['filename']:s for s in json.loads((args.capture_out / str(width) / 'screens.json').read_text())['screens']} if previous else {}
        baseline = {s['filename']:s for s in json.loads((args.baseline / str(width) / 'screens.json').read_text())['screens']}
        def verify(page, shot, meta):
            current = inventory(page)
            for c in current:
                c['target'] = guide.ui_control(c)[0]
            old = baseline[shot.filename]['dom']['controls']
            missing = Counter(map(shell.signature, old)) - Counter(map(shell.signature, current))
            layout = page.evaluate(shell.LAYOUT)
            department = page.locator('.data-entry-page').count() > 0
            row = dict(filename=shot.filename, width=width, template_024=department,
                elements=len(old), missing=list(missing.elements()), **layout)
            # The only template/JS edits are in 024. All CSS rules are scoped there.
            # Swap its sheet in its original cascade slot, never replace shared CSS.
            # On every other template this sheet must be absent (zero resource impact).
            if not department:
                assert not page.locator('[href="/static/design/data-entry.css"], [src="/static/design/data-entry.js"], .source-disclosure').count()
            css = page.locator('link[href="/static/design/data-entry.css"]')
            compare = not department or css.count() and not page.locator('.source-disagreement:visible, input[type=checkbox]:checked:visible').count()
            if compare:
                attempts = []
                for attempt in range(3):
                    styles_before = page.evaluate(SNAPSHOT)
                    before = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                    if css.count():
                        css.evaluate('''(el, text) => {
                          const sheet=el.sheet, baseline=new CSSStyleSheet();
                          window.__civ100Rules=[...sheet.cssRules].map(rule=>rule.cssText);
                          baseline.replaceSync(text);
                          while(sheet.cssRules.length) sheet.deleteRule(0);
                          [...baseline.cssRules].forEach(rule=>sheet.insertRule(rule.cssText,sheet.cssRules.length));
                        }''', baseline_css)
                    try:
                        after = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                        styles_after = page.evaluate(SNAPSHOT)
                    finally:
                        if css.count():
                            css.evaluate('''el => {
                              const sheet=el.sheet;
                              while(sheet.cssRules.length) sheet.deleteRule(0);
                              window.__civ100Rules.forEach(rule=>sheet.insertRule(rule,sheet.cssRules.length));
                              delete window.__civ100Rules;
                            }''')
                    pixels, delta = pixel_difference(before, after)
                    assert len(styles_before) == len(styles_after)
                    row.update(nodes=len(styles_before),
                        style_changes=sum(a['style'] != b['style'] for a,b in zip(styles_before,styles_after)),
                        geometry_changes=sum(a['geometry'] != b['geometry'] for a,b in zip(styles_before,styles_after)),
                        max_channel_delta=delta)
                    attempts.append(pixels)
                    row['unchanged_state_pixels' if department else 'changed_pixels'] = pixels
                    if not department:
                        row['changed_resources_loaded'] = 0
                    if not pixels:
                        break
                row['paint_attempts'] = attempts
                row['raster_rounding_only'] = bool(pixels and delta <= 2 and not row['style_changes'] and not row['geometry_changes'])
                if pixels:
                    diagnostic = args.capture_out / 'pixel-diagnostics' / str(width)
                    diagnostic.mkdir(parents=True, exist_ok=True)
                    (diagnostic / (shot.filename + '.before.png')).write_bytes(before)
                    (diagnostic / (shot.filename + '.after.png')).write_bytes(after)
            for index, old_row in enumerate(results):
                if (old_row['width'],old_row['filename']) == (width,shot.filename):
                    row['first_sweep_pixels'] = old_row.get('first_sweep_pixels',old_row.get('changed_pixels',old_row.get('unchanged_state_pixels',0)))
                    results[index] = row
                    break
            else:
                results.append(row)
            # Preserve the capture's original DOM. Open-disclosure inventories are
            # comparison evidence only; closed captures retain their exact state.
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
        if previous:
            guide.capture = capture_selected
        try:
            assert guide.ui_main(SimpleNamespace(out=folder, viewport_width=width), shell.local_test_url()) == 0
        finally:
            guide.capture = original_capture
        assert {s['filename'] for s in json.loads((folder / 'screens.json').read_text())['screens']} == set(baseline)
    failures = [r for r in results if failed(r)]
    report = dict(baseline=args.base_ref, browser=json.loads((folder / 'screens.json').read_text())['browser'],
        captures=len(results), elements=sum(r['elements'] for r in results), failures=len(failures),
        pixel_method='Other templates load no changed resources. Same-DOM screenshots, no masks; raw pixel differences/attempts retained. Only <=2/255 raster rounding with exact computed-style and geometry equality is classified as renderer noise. 024 unchanged states also compare the base stylesheet in its original cascade slot.', screens=results)
    (OUT / 'capture-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for row in failures:
        print(json.dumps(row, ensure_ascii=False))
    print(f'{len(results)} captures; {len(failures)} failures.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
