#!/usr/bin/env python3
"""Capture/audit CIV-123 with real routes on disposable PostgreSQL only.

CIVENSA_TEST_POSTGRES_URL=<local disposable URL> CIVENSA_CHROMIUM_PATH=/usr/bin/chromium \
  python docs/design/rollout/civ-123/verify_rollout.py --phase before|after
"""
import argparse
import json
import logging
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ.pop('MIGRATION_DATABASE_URL', None)
os.environ.update(CIVENSA_ENV='development', DEMO_SEED='0', COOKIE_SECURE='0',
                  SESSION_SECRET=secrets.token_urlsafe(48))
logging.disable(logging.CRITICAL)
from scripts import guide_screenshots as guide
from scripts.first_load_dryrun import disposable_database, local_test_url
from test_section_index_design import TEXT_PAIRS, contrast
from PIL import Image
from playwright.sync_api import sync_playwright

# Exact screen-map numbers; routes resolve against freshly seeded IDs.
CASES = [
    ('009', '/activity-sections', 'strategy', '.section-index-page'),
    ('010', '/activity-sections', 'department', '.section-index-page'),
    ('011', '/activity-sections/reports/{document_id}', 'strategy', '.section-editor-page'),
    ('012', '/activity-sections/reports/{document_id}', 'department', '.section-editor-page'),
    ('021', '/dashboard', 'strategy', '.dashboard-page'),
    ('022', '/dashboard', 'department', '.dashboard-page'),
    ('024', '/department/{department_id}', 'department', '.data-entry-page'),
    ('029', '/internal-control/monitoring/batches/{batch_id}', 'department', '.ic-wrap'),
    ('030', '/internal-control/our-actions', 'department', '.ic-our-actions-page'),
    ('033', '/modules', 'strategy', '.module-list'),
    ('034', '/modules', 'department', '.module-list'),
    ('041', '/report-builder/manifest', 'strategy', '.pp-manifest-page'),
    ('042', '/review', 'strategy', '.review-page'),
    ('046', '/submit-authorizations', 'department', '.submit-authorizations-page'),
]

METRICS = r"""root => {
  const rows = selector => [...root.querySelectorAll(selector)].map(el => {
    const r = el.getBoundingClientRect();
    return {width:r.width, height:r.height, x:r.x, right:r.right, text:el.innerText};
  });
  return {scroll:document.documentElement.scrollWidth, viewport:innerWidth,
    summary:rows('.dashboard-summary .card'), records:rows('.record-head'),
    headings:rows('.report-heading'), sections:rows('.ar-tree a'), definitions:rows('dl')};
}"""


def assert_rows(page, number):
    selectors = {'009': '.report-heading', '010': '.report-heading',
                 '011': '.ar-tree a', '012': '.ar-tree a', '024': '.record-head',
                 '030-approved': '.ic-our-actions-page dl'}
    if number == '021':
        rows = page.locator('.dashboard-summary .card')
        assert rows.count() == 3
        for row in rows.all():
            assert row.bounding_box()['height'] <= 44.1, row.inner_text()
            label, value = row.locator('span'), row.locator('b')
            l, v = label.bounding_box(), value.bounding_box()
            assert v['x'] >= l['x'] + l['width'] - 1
            assert v['x'] - (l['x'] + l['width']) <= 17
            assert v['y'] < l['y'] + l['height']
            assert 'tabular-nums' in value.evaluate('el => getComputedStyle(el).fontVariantNumeric')
            assert row.evaluate("el => getComputedStyle(el).borderLeftWidth === '0px' && getComputedStyle(el).borderRadius === '0px'")
    if number in selectors:
        rows = page.locator(selectors[number])
        assert rows.count() > 0
        for row in rows.all():
            box = row.bounding_box()
            assert box['width'] <= 44 * 16 + 1, (number, box)
            for child in row.locator(':scope > *').all():
                b = child.bounding_box()
                if b:
                    assert b['x'] >= box['x'] - 1 and b['x'] + b['width'] <= box['x'] + box['width'] + 1
        if number in ('009', '010', '011', '012') and page.viewport_size['width'] == 1440:
            badge = '.report-badges' if number in ('009', '010') else 'small'
            # Each column has a common starting edge for its statuses.
            columns = {}
            for row in rows.all():
                columns.setdefault(round(row.bounding_box()['x']), []).append(round(row.locator(badge).bounding_box()['x']))
            assert all(max(xs) - min(xs) <= 1 for xs in columns.values()), columns


def capture(browser, base, data, phase, case, report):
    number, pattern, role, root_selector = case
    with browser.new_context(viewport={'width': 1440, 'height': 900}, locale='tr-TR',
                             timezone_id='Europe/Istanbul', device_scale_factor=1,
                             color_scheme='light', reduced_motion='reduce',
                             extra_http_headers={'X-Guide-Account': role}) as context:
        context.route('**/*', lambda route: route.continue_() if route.request.method == 'GET'
                      and route.request.url.startswith(base + '/') else route.abort())
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        path = guide.ui_path(pattern, data, role)
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 900})
            response = page.goto(base + path, wait_until='networkidle')
            assert response.status == 200, (number, response.status)
            page.evaluate('document.fonts.ready')
            root = page.locator(root_selector)
            assert root.count() == 1
            metrics = root.evaluate(METRICS)
            if phase == 'after':
                assert metrics['scroll'] == width, (number, width, metrics)
                if width == 1440:
                    assert_rows(page, number)
                # 029 keeps its legacy appearance; no new palette is applied.
                if number not in ('029', '029-approved'):
                    pairs = page.evaluate(TEXT_PAIRS.replace('.section-index-page', root_selector))
                    ratios = [contrast(pair) for pair in pairs]
                    assert min(ratios) >= 4.5, (number, min(ratios))
                    metrics['minimum_text_contrast'] = round(min(ratios), 3)
            target = OUT / f'{number}-{phase}-{width}.png'
            page.screenshot(path=str(target), full_page=True)
            with Image.open(target) as image:
                image.save(target, optimize=True)
            if target.stat().st_size > 1_500_000:
                with Image.open(target) as image:
                    image.quantize(colors=256).save(target, optimize=True)
            assert target.stat().st_size <= 1_500_000
            metrics.update(screen=number, width=width, png=target.name, bytes=target.stat().st_size)
            report.append(metrics)
        assert not errors, (number, errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('before', 'after'), required=True)
    parser.add_argument('--screen', action='append', help='Recapture selected screens after a base-branch update.')
    args = parser.parse_args()
    report = []
    with disposable_database(local_test_url()) as engine:
        import app.db as app_db
        import app.main as app_main
        app_db.engine.dispose()
        app_db.engine = app_main.engine = engine
        app_db.SessionLocal.configure(bind=engine)
        data = guide.ui_setup(engine)
        data.update(ui_map=True, _shots=[], _screen_meta={}, _unexpected=[])
        with guide.local_http(engine, data) as base, sync_playwright() as pw:
            with pw.chromium.launch(headless=True, executable_path=os.getenv('CIVENSA_CHROMIUM_PATH')) as browser:
                digest = guide.ui_state_digest(engine)
                for case in CASES:
                    if args.screen and case[0] not in args.screen:
                        continue
                    capture(browser, base, data, args.phase, case, report)
                assert digest == guide.ui_state_digest(engine)
                # Real submitted/approved read-only definition lists, same fixture in both phases.
                from sqlalchemy import select
                from sqlalchemy.orm import Session
                from app.models import User
                from app import internal_control_monitoring_service as monitoring
                with Session(engine) as db:
                    for role, action in [('department', 'submit'), ('strategy', 'approve')]:
                        actor = db.scalar(select(User).where(User.email == data['accounts'][role]))
                        monitoring.transition(db, actor, data['ic_batch'], action,
                                              monitoring.state(db, data['ic_batch'])[1])
                        db.commit()
                digest = guide.ui_state_digest(engine)
                if not args.screen or '030' in args.screen:
                    capture(browser, base, data, args.phase,
                            ('030-approved', '/internal-control/our-actions', 'department', '.ic-our-actions-page'), report)
                assert digest == guide.ui_state_digest(engine)
                version = browser.version
    target = OUT / f'{args.phase}.json'
    if args.screen and target.exists():
        replaced = {row['screen'] for row in report}
        report = [row for row in json.loads(target.read_text())['results'] if row['screen'] not in replaced] + report
    target.write_text(json.dumps(dict(browser=version, results=report), ensure_ascii=False, indent=2) + '\n')
    print(f'{args.phase}: {len(report)} screenshots; layout, read-only capture and PNG size verified.')


if __name__ == '__main__':
    main()
