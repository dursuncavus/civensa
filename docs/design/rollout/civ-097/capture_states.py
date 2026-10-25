#!/usr/bin/env python3
"""024 synthetic states, both positions/tabs/widths; contrast and keyboard checks.

CIVENSA_TEST_POSTGRES_URL must be disposable local PostgreSQL 16+.
All browser traffic is GET to the loopback TestClient bridge. No live service.
"""
import argparse
import json
import os
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(OUT))
from verify_rollout import shell, inventory
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from scripts.first_load_dryrun import disposable_database
from playwright.sync_api import sync_playwright, expect
from PIL import Image

COLLECT = shell.contrast.COLLECT.replace(
    "const scope = modal || document.body;", "const scope = modal || document.querySelector('.data-entry-page');")
# Include the checkmark painted over the selected native replacement checkbox.
COLLECT = COLLECT.replace('  return rows;', '''  for (const el of scope.querySelectorAll('input[type=checkbox]:checked')) {
    if (visible(el)) add(el, rgb(getComputedStyle(el).color).slice(0,3), background(el), 'Seçim işareti', 3);
  }
  for (const el of scope.querySelectorAll('input[placeholder],textarea[placeholder]')) {
    if (visible(el) && !el.value) add(el, rgb(getComputedStyle(el,'::placeholder').color).slice(0,3), background(el), 'Yer tutucu', 4.5);
  }
  return rows;''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish-only', action='store_true', help='Refresh the eight PNGs after a complete state audit; retain its report.')
    args = parser.parse_args()
    pairs, report, screenshots = {}, [], []
    def audit(page):
        rows = page.evaluate(COLLECT)
        for row in rows:
            fg, bg = tuple(row['color']), tuple(row['bg'])
            key = (shell.TOKENS.get(fg, str(fg)), shell.TOKENS.get(bg, str(bg)), row['kind'])
            assert fg in shell.TOKENS and bg in shell.TOKENS, f'Token dışı renk: {row}'
            pairs[key] = dict(ratio=shell.contrast.ratio(fg,bg), minimum=row['minimum'], example=row['example'])
    with disposable_database(shell.local_test_url()) as engine:
        data = shell.guide.ui_setup(engine)
        # Exercise unresolved source totals and history with wholly synthetic evidence.
        from decimal import Decimal
        from datetime import datetime
        with Session(engine) as db:
            activity = db.scalar(select(m.Activity).where(m.Activity.department_id == data['own']))
            total = db.scalar(select(m.ActivityCostValue).where(m.ActivityCostValue.activity_id == activity.id,
                m.ActivityCostValue.year == 2027, m.ActivityCostValue.funding_type == 'total'))
            total.source_amount = Decimal('13000.23')
            total.source_resolution_json = '{}'
            submission = db.scalar(select(m.Submission).where(m.Submission.department_id == data['own']))
            user = db.scalar(select(m.User).where(m.User.email == 'ui.department@example.invalid'))
            for event_type, note, day in [('submitted', '', 21), ('return', 'Sentetik kontrol: hedefin dayanağını açıklayın.', 22)]:
                db.add(m.SubmissionEvent(submission_id=submission.id, department_id=data['own'], period_id=data['period'],
                    actor_user_id=user.id, event_type=event_type, revision=1, note=note,
                    created_at=datetime(2026, 10, day, 9)))
            db.commit()
        with shell.guide.local_http(engine, data) as base, sync_playwright() as pw:
            with pw.chromium.launch(headless=True, executable_path=os.getenv('CIVENSA_CHROMIUM_PATH', '/usr/bin/chromium')) as browser:
                for width in (1440, 390):
                    for position in (('director',) if args.publish_only else ('director', 'staff')):
                        with Session(engine) as db:
                            user = db.scalar(select(m.User).where(m.User.email == f'ui.{"department" if position == "director" else "staff"}@example.invalid'))
                            email = user.email
                        client = data['_clients']['department']
                        assert client.post('/login', data={'email': email, 'password': data['password']}).status_code == 303
                        with browser.new_context(viewport={'width': width, 'height': 900}, device_scale_factor=1, color_scheme='light', locale='tr-TR', timezone_id='Europe/Istanbul', reduced_motion='reduce', extra_http_headers={'X-Guide-Account': 'department'}) as context:
                            blocked, errors = [], []
                            def guard(route):
                                from urllib.parse import urlsplit
                                if route.request.method == 'GET' and urlsplit(route.request.url).netloc == urlsplit(base).netloc:
                                    route.continue_()
                                else:
                                    blocked.append(route.request.method)
                                    route.abort()
                            context.route('**/*', guard)
                            page = context.new_page()
                            page.on('pageerror', lambda error: errors.append(str(error)))
                            for state in (('draft-issues', 'returned', 'submitted') if args.publish_only else ('draft-issues', 'draft-clean', 'returned', 'submitted', 'approved')):
                                with Session(engine) as db:
                                    submission = db.scalar(select(m.Submission).where(m.Submission.department_id == data['own']))
                                    submission.status = 'draft' if state.startswith('draft') else state
                                    submission.return_note = '2027 hedefinin dayanağını açıklayın ve hizmet kayıtlarıyla karşılaştırın. (Sentetik iade notu)' if state == 'returned' else ''
                                    indicator = db.scalar(select(m.Indicator).where(m.Indicator.department_id == data['own']))
                                    indicator.explanation = '' if state == 'draft-issues' else 'Hizmet noktalarında tamamlanan işlemler yıllık kayıtlarla karşılaştırılır. (Sentetik)'
                                    db.commit()
                                before = shell.guide.ui_state_digest(engine)
                                response = page.goto(f'{base}/department/{data["own"]}?period_id={data["period"]}', wait_until='networkidle')
                                assert response.status == 200
                                page.evaluate('document.fonts.ready')
                                for tab in ('indicators', 'activities'):
                                    page.locator(f'[data-tab={tab}]').click()
                                    layout = page.evaluate(shell.LAYOUT)
                                    assert layout['document'] == width and not any(layout[k] for k in ('overflow','clipped','overlaps','shell_issues')), layout
                                    audit(page)
                                    # Every currently visible control must retain an accent keyboard focus.
                                    page.keyboard.press('Tab')
                                    for control in page.locator('.data-entry-page :is(a,button,input,select,textarea,summary,[tabindex])').all():
                                        if not control.is_visible() or control.is_disabled():
                                            continue
                                        control.focus()
                                        style = control.evaluate('el => {const s=getComputedStyle(el); return [s.outlineColor,s.outlineWidth,s.outlineStyle]}')
                                        assert style == ['rgb(30, 107, 101)', '2px', 'solid'], style
                                    # Real hover/focus states for each distinct component, including readonly.
                                    for selector in ('.button', '.button.primary', '.button.danger', '.tab.active', '.tab:not(.active)', '.issue-jump', 'input', 'textarea', 'select', 'summary', '.activity-scroll'):
                                        control = page.locator('.data-entry-page ' + selector).first
                                        if control.count() and control.is_visible():
                                            control.hover()
                                            control.focus()
                                            audit(page)
                                    if tab == 'indicators' and page.locator('.draft-removal summary').count():
                                        trigger = page.locator('.draft-removal summary').first
                                        trigger.click()
                                        expect(page.locator('.removal-dialog[open] [data-cancel-removal]')).to_be_focused()
                                        audit(page)
                                        for control in page.locator('.removal-dialog[open] button').all():
                                            control.hover(); control.focus(); audit(page)
                                        page.keyboard.press('Escape')
                                        expect(trigger).to_be_focused()
                                    report.append(dict(width=width, position=position, state=state, tab=tab, **layout))
                                    publish = position == 'director' and ((tab == 'indicators' and state in {'draft-issues','returned','submitted'}) or (tab == 'activities' and state == 'draft-issues'))
                                    if publish:
                                        name = f'024-{"costs" if tab == "activities" else state}-{width}.png'
                                        page.evaluate('document.activeElement.blur(); document.querySelectorAll(".activity-scroll").forEach(region => region.scrollLeft = 0); window.scrollTo(0,0)')
                                        page.mouse.move(0,0)
                                        page.screenshot(path=str(OUT / name), full_page=True, animations='disabled', caret='hide')
                                        with Image.open(OUT / name) as png:
                                            png.save(OUT / name, optimize=True)
                                            if (OUT / name).stat().st_size > 1_500_000:
                                                png.convert('RGB').quantize(colors=256).save(OUT / name, optimize=True)
                                            screenshots.append(dict(file=name, width=png.width, height=png.height, bytes=(OUT / name).stat().st_size))
                                        assert screenshots[-1]['bytes'] <= 1_500_000
                                    if state == 'draft-issues' and position == 'director':
                                        if tab == 'activities':
                                            checkbox = page.locator('.contract-bound').first
                                            original = checkbox.is_checked()
                                            checkbox.evaluate('el => el.checked = true')
                                            audit(page)  # checkmark/icon contrast; no change event or write
                                            checkbox.evaluate('(el, checked) => el.checked = checked', original)
                                            page.locator('#addActivity').click()
                                            audit(page)  # editable fields and placeholders
                                            page.locator('.cancel-new').click()
                                            page.locator('.edit-activity').first.click()
                                            audit(page)
                                            # Cancel uses the existing GET reload and preserves persisted values.
                                            page.locator('.delete-activity').first.click()
                                            page.wait_for_load_state('networkidle')
                                            page.locator('[data-tab=activities]').click()
                                        else:
                                            field = page.locator('.record [data-field=explanation]').first
                                            field.fill('Sentetik kaydedilmemiş açıklama')
                                            audit(page)
                                            page.locator('.page-actions a').click()
                                            expect(page.locator('.draft-confirm[open]')).to_be_visible()
                                            audit(page)
                                            page.keyboard.press('Escape')
                                            page.evaluate("drafts.error(document.querySelector('[data-draft-record]'), 'Sentetik kayıt hatası: açıklamayı kontrol edin.', ['explanation'])")
                                            audit(page)
                                            page.evaluate("drafts.saved(document.querySelector('[data-draft-record]'), drafts.values(document.querySelector('[data-draft-record]')))")
                                            audit(page)  # saved status foreground/background
                                            page.evaluate('drafts.allowNavigation()')
                                            page.reload(wait_until='networkidle')
                                    assert not blocked and not errors
                                assert before == shell.guide.ui_state_digest(engine), 'Browser changed persisted state'
                                print(f'{width} {position} {state}: both tabs passed', flush=True)
    failures = []
    lines = ['| Ön plan | Arka plan | Kullanım | Oran | AA eşiği | Sonuç |', '| --- | --- | --- | ---: | ---: | --- |']
    for (fg,bg,kind), row in sorted(pairs.items()):
        passed = row['ratio'] >= row['minimum']
        if not passed: failures.append((fg,bg,kind))
        lines.append(f'| `{fg}` | `{bg}` | {kind} | {row["ratio"]:.2f}:1 | {row["minimum"]:g}:1 | {"Geçti" if passed else "KALDI"} |')
    lines += ['', f'{len(pairs)} kullanım çifti · {len(failures)} başarısız.']
    if not args.publish_only:
        (OUT / 'contrast.md').write_text('\n'.join(lines)+'\n')
        (OUT / 'states-summary.json').write_text(json.dumps(dict(captures=len(report), failures=len(failures), checks=report), ensure_ascii=False, indent=2)+'\n')
    else:
        assert json.loads((OUT / 'states-summary.json').read_text())['captures'] == 40
        assert not failures
    (OUT / 'screenshots.json').write_text(json.dumps(screenshots, ensure_ascii=False, indent=2)+'\n')
    print(f'{len(report)} state/tab/width/position checks; {len(pairs)} contrast pairs; {len(failures)} failures.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
