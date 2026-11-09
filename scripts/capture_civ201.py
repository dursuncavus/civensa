#!/usr/bin/env python3
"""Capture CIV-201 at 1440x900 using only the approved full synthetic seed.

Creates a disposable SQLite database, runs the real form creation paths, and
captures both the pinned phase5 templates/assets and the working tree. Production
configuration is never read as a database target. PostgreSQL browser regressions
live in tests/test_civ201_pilot_browser.py.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'e1eb2bff298c9a23680db3fc433d84a2ff21bf6c'
PAGES = [
    ('source-comparison', '/source-comparison?period_id=1'),
    ('operations', '/operations?period_id=1'),
    ('indicator-report', '/activity-reports/revisions/1'),
    ('financial-overview', '/activity-sections/reports/1?code=III.A'),
    ('financial-budget', '/activity-sections/reports/1?code=III.A.1'),
]
TEMPLATES = ['base.html', 'source_comparison.html', 'pp_reconciliation.html',
             'operations.html', 'activity_contract_detail.html', 'activity_financial.html',
             'activity_sections_editor.html']
ASSETS = ['design/source-comparison.css', 'design/source-comparison.js', 'design/operations.css']


def base_file(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def capture(output):
    # Set the isolated target before importing any application module.
    with tempfile.TemporaryDirectory(prefix='civ201-capture-') as temporary:
        database = Path(temporary) / 'synthetic.db'
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(database)
        os.environ['DEMO_SEED'] = '0'
        sys.path.insert(0, str(ROOT))
        from jinja2 import ChoiceLoader, DictLoader
        from playwright.sync_api import sync_playwright
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        from app import main
        from app.db import engine
        from app.models import User
        from app.security import hash_password
        from scripts.profile_strateji_steps import create_schema, seed, Client

        create_schema(engine)
        seeded = seed(engine, tiny=False)
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
            connection.execute(text('INSERT INTO alembic_version VALUES (:head)'), {'head': main.migration_head()})
        harness = Client(database, 1, 1)
        client = harness.client
        try:
            form = dict(period_id=1, organization_id=1, csrf_token=harness.csrf_token,
                        approval_reference='SENTETİK CIV-201; gerçek karar değildir.')
            assert client.post('/report-builder/publish-approved-book', data=form).status_code == 303
            assert client.post('/activity-sections/years', data=form).status_code == 303
            with Session(engine) as db:
                db.add(User(email='editor@example.invalid', full_name='SENTETİK Editör', role='strategy',
                            department_id=1, password_hash=hash_password('Civ201-local-test-only!')))
                db.commit()
            assert client.post('/login', data={'email': 'editor@example.invalid', 'password': 'Civ201-local-test-only!'}).status_code == 303
            import re
            token = re.search(r'name="csrf_token" value="([^"]+)"', client.get('/modules').text).group(1)
            assert client.post('/activity-reports/revisions', data={'publication_id': 1, 'organization_id': 1, 'csrf_token': token}).status_code == 303
            harness._login()
            baseline = {name: base_file('app/templates/' + name).decode() for name in TEMPLATES}
            baseline_assets = {'/static/' + name: base_file('app/static/' + name) for name in ASSETS}
            loader = main.templates.env.loader
            output.mkdir(parents=True, exist_ok=True)
            (output / 'shots').mkdir(exist_ok=True)
            measurements = {}
            with sync_playwright() as pw:
                options = {'headless': True}
                if os.getenv('CIVENSA_CHROMIUM_PATH'):
                    options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
                browser = pw.chromium.launch(**options)
                for phase in ('before', 'after'):
                    main.templates.env.loader = ChoiceLoader([DictLoader(baseline), loader]) if phase == 'before' else loader
                    main.templates.env.cache.clear()
                    with browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1) as context:
                        def serve(route):
                            from urllib.parse import urlsplit
                            request = route.request
                            path = urlsplit(request.url).path
                            if phase == 'before' and path in baseline_assets:
                                route.fulfill(status=200, content_type='text/css' if path.endswith('.css') else 'text/javascript', body=baseline_assets[path])
                                return
                            response = client.request(request.method, request.url, follow_redirects=False)
                            headers = dict(response.headers)
                            headers.pop('set-cookie', None)
                            route.fulfill(status=response.status_code, headers=headers, body=response.content)
                        context.route('http://testserver/**', serve)
                        page = context.new_page()
                        measurements[phase] = {}
                        for name, url in PAGES:
                            response = page.goto('http://testserver' + url, timeout=180000)
                            assert response.status == 200, (url, response.status)
                            page.evaluate('document.fonts.ready')
                            height = page.evaluate('document.documentElement.scrollHeight')
                            if phase == 'after':
                                assert height < 7200, (name, height)
                            measurements[phase][name] = height
                            page.screenshot(path=str(output / 'shots' / f'{name}-{phase}.png'))
                            print(f'{phase} {name}: {height} px', flush=True)
                browser.close()
            main.templates.env.loader = loader
            main.templates.env.cache.clear()
            (output / 'heights.json').write_text(json.dumps(dict(base=BASE, viewport=[1440, 900], seed=seeded, heights=measurements), ensure_ascii=False, indent=2) + '\n')
        finally:
            harness.close()
            engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/reports/civ-201')
    capture(parser.parse_args().output_dir)
