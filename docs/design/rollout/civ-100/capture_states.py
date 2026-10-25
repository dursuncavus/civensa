#!/usr/bin/env python3
"""024 mismatch states, real computed contrast, keyboard and PNG evidence.

GET-only browser replay with synthetic data on disposable local PostgreSQL 16+.
The PUT/reason regression is covered separately by test_department_design.py.
"""
from collections import Counter
from decimal import Decimal
import importlib.util
import json
import os
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(OUT))
from verify_rollout import shell, inventory
spec = importlib.util.spec_from_file_location('civ097states', ROOT / 'docs/design/rollout/civ-097/capture_states.py')
previous = importlib.util.module_from_spec(spec)
# The old state script imports its own verify_rollout; only COLLECT is reused.
spec.loader.exec_module(previous)
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m
from scripts.first_load_dryrun import disposable_database
from PIL import Image


def save_png(page_or_locator, name, screenshots):
    path = OUT / name
    page_or_locator.screenshot(path=str(path), animations='disabled', caret='hide', **({'full_page': True} if hasattr(page_or_locator, 'goto') else {}))
    with Image.open(path) as png:
        png.save(path, optimize=True)
        screenshots.append(dict(file=name, width=png.width, height=png.height, bytes=path.stat().st_size))
    assert path.stat().st_size <= 1_500_000


def main():
    pairs, checks, screenshots = {}, [], []
    def audit(page):
        for row in page.evaluate(previous.COLLECT):
            fg, bg = tuple(row['color']), tuple(row['bg'])
            key = (shell.TOKENS.get(fg, str(fg)), shell.TOKENS.get(bg, str(bg)), row['kind'])
            pairs[key] = dict(ratio=shell.contrast.ratio(fg,bg), minimum=row['minimum'])
    with disposable_database(shell.local_test_url()) as engine:
        import app.db as app_db
        import app.main as app_main
        app_db.engine = app_main.engine = engine
        app_db.SessionLocal.configure(bind=engine)
        data = shell.guide.ui_setup(engine)
        with Session(engine) as db:
            activity = db.scalar(select(m.Activity).where(m.Activity.department_id == data['own']))
            activity.contract_bound = True
            total = db.scalar(select(m.ActivityCostValue).where(m.ActivityCostValue.activity_id == activity.id,
                m.ActivityCostValue.year == 2027, m.ActivityCostValue.funding_type == 'total'))
            total.source_amount = Decimal('13000.23')
            total.source_resolution_json = '{}'
            db.commit()
        with shell.guide.local_http(engine, data) as base, sync_playwright() as pw:
            with pw.chromium.launch(headless=True, executable_path=os.getenv('CIVENSA_CHROMIUM_PATH', '/usr/bin/chromium')) as browser:
                for width in (1440,390):
                    for actor in ('director','staff','strategy'):
                        account = 'strategy' if actor == 'strategy' else 'department'
                        email = f'ui.{"department" if actor == "director" else actor}@example.invalid'
                        assert data['_clients'][account].post('/login', data={'email':email,'password':data['password']}).status_code == 303
                        with browser.new_context(viewport={'width':width,'height':900}, device_scale_factor=1,
                            locale='tr-TR', timezone_id='Europe/Istanbul', reduced_motion='reduce',
                            extra_http_headers={'X-Guide-Account':account}) as context:
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
                            for state in ('draft','returned','submitted','approved','closed'):
                                with Session(engine) as db:
                                    submission = db.scalar(select(m.Submission).where(m.Submission.department_id == data['own']))
                                    submission.status = 'draft' if state == 'closed' else state
                                    period = db.get(m.ReportingPeriod, data['period'])
                                    period.status = 'closed' if state == 'closed' else 'active'
                                    db.commit()
                                before = shell.guide.ui_state_digest(engine)
                                response = page.goto(f'{base}/department/{data["own"]}?period_id={data["period"]}', wait_until='networkidle')
                                assert response.status == 200
                                page.evaluate('document.fonts.ready')
                                page.locator('[data-tab=activities]').click()
                                box = page.locator('.source-disagreement').first
                                panel = box.locator('details')
                                trigger = panel.locator('summary')
                                row = box.locator('xpath=ancestor::tr')
                                # Keep the affected column visible inside the existing local table scroller.
                                box.evaluate('el => {const region=el.closest(".activity-scroll");region.scrollLeft=el.closest("td").offsetLeft-16}')
                                closed = row.bounding_box()['height']
                                box.evaluate('el => el.hidden=true')
                                clean = row.bounding_box()['height']
                                box.evaluate('el => el.hidden=false')
                                assert closed <= clean + 16
                                closed_controls = page.evaluate(shell.guide.UI_DOM)['controls']
                                for opened in (False,True):
                                    if opened:
                                        trigger.focus(); page.keyboard.press('Enter')
                                        assert panel.evaluate('el => el.open')
                                    layout = page.evaluate(shell.LAYOUT)
                                    assert layout['document'] == width and not any(layout[k] for k in ('overflow','clipped','overlaps','shell_issues')), layout
                                    audit(page)
                                    trigger.hover(); trigger.focus(); audit(page)
                                    current = inventory(page)
                                    missing = Counter(shell.signature(c) for c in closed_controls) - Counter(shell.signature(c) for c in current)
                                    assert not missing
                                    checks.append(dict(width=width,actor=actor,state=state,open=opened,
                                        row_height=row.bounding_box()['height'],closed_height=closed,clean_height=clean,
                                        missing=list(missing.elements()),**layout))
                                    if actor == 'director' and state == 'draft':
                                        page.evaluate('document.activeElement.blur();window.scrollTo(0,0)')
                                        page.mouse.move(0,0)
                                        save_png(page,f'024-costs-{"open" if opened else "closed"}-{width}.png',screenshots)
                                reason = box.locator('.source-total-reason')
                                if actor != 'strategy' and state in ('draft','returned'):
                                    expect(reason).to_be_visible()
                                    reason.focus()
                                else:
                                    expect(reason).to_have_count(0)
                                    trigger.focus()
                                page.keyboard.press('Escape')
                                assert not panel.evaluate('el => el.open')
                                expect(trigger).to_be_focused()
                                assert shell.guide.ui_state_digest(engine) == before
                                assert not errors and not blocked
                                print(f'{width} {actor} {state}: closed/open/keyboard passed',flush=True)
                            if actor == 'director' and width == 1440:
                                checkbox = page.locator('.contract-bound').first
                                expect(checkbox).to_be_checked()
                                style = checkbox.evaluate('el => {const s=getComputedStyle(el,"::before");return {mask:s.maskImage,content:s.content,color:s.backgroundColor,accent:getComputedStyle(el).backgroundColor}}')
                                assert 'data:image/svg+xml' in style['mask'] and style['content'] == '""'
                                fg = tuple(map(int,shell.re.findall(r'\d+',style['color'])))
                                bg = tuple(map(int,shell.re.findall(r'\d+',style['accent'])))
                                ratio = shell.contrast.ratio(fg,bg)
                                assert ratio >= 3
                                pairs[('--surface','--accent','SVG seçim işareti')] = dict(ratio=ratio,minimum=3)
                                save_png(checkbox.locator('..'),'024-checkbox-checked.png',screenshots)
    failures = [key for key,row in pairs.items() if row['ratio'] < row['minimum']]
    lines = ['| Ön plan | Arka plan | Kullanım | Oran | AA eşiği | Sonuç |','| --- | --- | --- | ---: | ---: | --- |']
    for (fg,bg,kind),row in sorted(pairs.items()):
        lines.append(f'| `{fg}` | `{bg}` | {kind} | {row["ratio"]:.2f}:1 | {row["minimum"]:g}:1 | {"Geçti" if row["ratio"] >= row["minimum"] else "KALDI"} |')
    lines += ['',f'{len(pairs)} kullanım çifti; {len(failures)} başarısız. Gerçek hesaplanmış renkler, açık/kapalı, odak ve hover durumları. SVG maskesinin boyadığı renk ayrıca ölçüldü.']
    (OUT/'contrast.md').write_text('\n'.join(lines)+'\n')
    (OUT/'states-summary.json').write_text(json.dumps(dict(checks=checks,count=len(checks),failures=len(failures)),ensure_ascii=False,indent=2)+'\n')
    (OUT/'screenshots.json').write_text(json.dumps(screenshots,ensure_ascii=False,indent=2)+'\n')
    assert not failures, failures
    print(f'{len(checks)} state checks; {len(pairs)} contrast pairs; 0 failures.')


if __name__ == '__main__':
    main()
