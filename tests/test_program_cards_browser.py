"""CIV-202: full repository rehearsal fixture, all directorates at 1440×900.

Only the existing test book fixture is used; no external municipal files or DB.
Set CIVENSA_CIV202_ARTIFACTS to write repeatable before/after PR evidence.
"""
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import get_db
from app.main import app, require_user
from app.models import Department, User
from scripts.profile_strateji_steps import seed
from test_report_preparation_design import route_application
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def test_full_seed_every_directorate_fits(browser, db):
    result = seed(db.bind, tiny=False)
    assert result['counts'] == dict(cards=105, indicators=226, activities=182, economic_values=1270)
    user = db.scalar(select(User).where(User.role == 'strategy'))
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_user] = lambda: user
    folder = os.getenv('CIVENSA_CIV202_ARTIFACTS')
    baseline = (Path(__file__).parent / 'fixtures/program_pre_civ202.html').read_text()
    measurements = []
    card_count = 0
    maximum_height = 0
    try:
        with TestClient(app) as client, browser.new_context(viewport={'width': 1440, 'height': 900}) as context:
            route_application(context, client)
            page = context.new_page()
            for did in db.scalars(select(Department.id).order_by(Department.id)):
                url = f'http://testserver/program/{did}?period_id={result["period_id"]}'
                response = client.get(url)
                assert response.status_code == 200
                page.goto(url)
                page.evaluate('document.fonts.ready')
                expected = 6 + bool(response.context['reconciliation'])
                assert page.locator('[data-program-card]').count() == expected
                assert page.locator('dialog[open]').count() == 0
                assert page.locator('#rp-cards > details').count() == len(response.context['cards'])
                card_count += len(response.context['cards'])
                height = page.evaluate('document.documentElement.scrollHeight')
                assert height < 7200, (did, height)
                assert height <= 900, (did, height)
                maximum_height = max(maximum_height, height)
                assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
                if did in {1, 3, 11, 22}:
                    if folder:
                        Path(folder).mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(Path(folder) / f'program-{did}-after.png'))
                    old = response.template.environment.from_string(baseline).render(response.context)
                    def before_route(route):
                        route.fulfill(content_type='text/html', body=old)
                    context.route(url, before_route)
                    page.goto(url)
                    page.evaluate('document.fonts.ready')
                    before = page.evaluate('document.documentElement.scrollHeight')
                    if folder:
                        page.screenshot(path=str(Path(folder) / f'program-{did}-before.png'))
                    context.unroute(url)
                    measurements.append(dict(department=did, before=before, after=height))
            assert card_count == 105
            assert maximum_height <= 900
            if folder:
                (Path(folder) / 'heights.json').write_text(json.dumps(measurements, indent=2) + '\n')
    finally:
        app.dependency_overrides.clear()
