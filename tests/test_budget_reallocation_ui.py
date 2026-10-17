"""Real Chromium UI, real login/CSRF and local PostgreSQL only."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import expect
from sqlalchemy import select, func
from app.models import BudgetOperation, DepartmentScope, ReportingPeriod
from tests.test_budget_reallocation import budget
from tests.test_released_permissions import actors, http
from tests.test_sidebar_ui import browser

pytestmark=pytest.mark.postgres


def test_wizard_preview_apply_and_detail(browser,db,budget,http):
    client=http('strategy_director')
    previous = ReportingPeriod(year=2026)
    db.add(previous); db.flush()
    for index, leg in enumerate(budget['legs']):
        profile = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == budget['period_id'], DepartmentScope.department_id == leg['department_id']))
        if not profile:
            profile = DepartmentScope(period_id=budget['period_id'], department_id=leg['department_id'], status='required')
            db.add(profile)
        profile.display_name = f'Dönem Birimi {index + 1}'
        db.add(DepartmentScope(period_id=previous.id, department_id=leg['department_id'], display_name=f'Önceki Dönem Birimi {index + 1}', status='required'))
    db.commit()
    with browser.new_context(viewport={'width':1440,'height':1050}) as context:
        def serve(route):
            req=route.request
            response=client.request(req.method,req.url,content=req.post_data_buffer,
                headers={'content-type':req.headers.get('content-type',''),'X-CSRF-Token':req.headers.get('x-csrf-token','')},follow_redirects=True)
            headers=dict(response.headers);headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://testserver/budget-reallocations/new')
        selected = page.locator('.leg').first.locator('.department option:checked')
        expect(selected).to_have_text('Dönem Birimi 1')
        page.locator('#period').select_option(str(previous.id))
        expect(selected).to_have_text('Önceki Dönem Birimi 1')
        page.locator('#period').select_option(str(budget['period_id']))
        expect(selected).to_have_text('Dönem Birimi 1')
        for i,leg in enumerate(budget['legs']):
            row=page.locator('.leg').nth(i)
            row.locator('.department').select_option(str(leg['department_id']))
            row.locator('.direction').select_option(leg['direction'])
            row.locator('.leg-amount').fill('5.000.000,00')
        page.locator('#preview-button').click()
        expect(page.locator('#preview-result')).to_contain_text('5.000.000,00')
        expect(page.locator('#preview-result')).to_contain_text('Dönem Birimi 1')
        assert db.scalar(select(func.count(BudgetOperation.id)))==0
        folder=os.getenv('CIVENSA_UI_SCREENSHOTS')
        if folder:
            Path(folder).mkdir(parents=True,exist_ok=True)
            page.locator('#preview-section').evaluate("element => element.scrollIntoView({block:'start'})")
            page.screenshot(path=str(Path(folder)/'wizard-preview.png'))
        page.locator('#continue-reference').click()
        page.locator('#phase').select_option('after_adoption')
        expect(page.locator('#reference-label')).to_have_value('Meclis kararı')
        page.locator('#reference-date').fill('2026-10-01')
        page.locator('#reference-number').fill('2026/123')
        page.locator('#reason').fill('Yatırım öncelikleri doğrultusunda müdürlükler arası ödenek aktarımı.')
        page.locator('#apply-button').click()
        expect(page).to_have_url('http://testserver/budget-reallocations/1')
        expect(page.get_by_role('heading',name='Bütçe Aktarması #1')).to_be_visible()
        expect(page.get_by_text('Paketlerin onay durumu korundu.')).to_be_visible()
        expect(page.locator('main')).to_contain_text('Dönem Birimi 1')
        if folder:page.screenshot(path=str(Path(folder)/'operation-detail.png'))
        assert not errors,errors
        assert db.scalar(select(func.count(BudgetOperation.id)))==1
