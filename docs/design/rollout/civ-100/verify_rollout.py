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


def changed_pixels(before, after):
    from PIL import Image, ImageChops
    with Image.open(BytesIO(before)) as a, Image.open(BytesIO(after)) as b:
        assert a.size == b.size
        red, green, blue = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).split()
        return sum(ImageChops.lighter(ImageChops.lighter(red, green), blue).histogram()[1:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--base-ref', required=True)
    parser.add_argument('--capture-out', type=Path, default=Path('/tmp/civ100-after'))
    args = parser.parse_args()
    baseline_css = subprocess.check_output(['git', 'show', args.base_ref + ':app/static/design/data-entry.css'], cwd=ROOT, text=True)
    setup = guide.ui_setup
    results = []
    for width in (1440, 390):
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
            # Every other template must retain exact pixels. 024 role/state variants
            # are reported together because they share department.html.
            if not department:
                before = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                after = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                row['changed_pixels'] = changed_pixels(before, after)
                row['changed_resources_loaded'] = 0
            elif css.count() and not page.locator('.source-disagreement:visible, input[type=checkbox]:checked:visible').count():
                # Also prove unchanged 024 states when neither polished element is visible.
                before = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                css.evaluate('(el, text) => {const s=document.createElement("style");s.id="civ100-baseline-css";s.textContent=text;el.after(s);el.disabled=true}', baseline_css)
                try:
                    after = page.screenshot(full_page=shot.full, animations='disabled', caret='hide')
                finally:
                    css.evaluate('el => {el.disabled=false;document.getElementById("civ100-baseline-css").remove()}')
                row['unchanged_state_pixels'] = changed_pixels(before, after)
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
        assert guide.ui_main(SimpleNamespace(out=folder, viewport_width=width), shell.local_test_url()) == 0
        assert {s['filename'] for s in json.loads((folder / 'screens.json').read_text())['screens']} == set(baseline)
    failures = [r for r in results if r['missing'] or r['document'] != r['width'] or any(r[k] for k in ('overflow','clipped','overlaps','shell_issues')) or r.get('changed_pixels',0) or r.get('unchanged_state_pixels',0)]
    report = dict(baseline=args.base_ref, browser=json.loads((folder / 'screens.json').read_text())['browser'],
        captures=len(results), elements=sum(r['elements'] for r in results), failures=len(failures),
        pixel_method='Other templates load none of the changed resources; exact same-DOM screenshots, no masks. 024 unchanged states also compare the base stylesheet in its original cascade slot.', screens=results)
    (OUT / 'capture-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for row in failures:
        print(json.dumps(row, ensure_ascii=False))
    print(f'{len(results)} captures; {len(failures)} failures.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
