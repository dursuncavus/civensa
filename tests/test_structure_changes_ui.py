"""Exercise all wizard steps in Chromium through actual login/session/CSRF."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import expect
from sqlalchemy import select

from app.db import get_db
from app.main import app
from app.models import StructureChange, StructureChangeTransfer
from app.security import hash_password
from tests.test_live_pilot_hardening import login
from tests.test_master_data_ui import route_to_client
from tests.test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


def capture(locator, name):
    folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
    if folder:
        path = Path(folder); path.mkdir(parents=True,exist_ok=True)
        locator.screenshot(path=str(path/name))


def test_split_wizard_summary_save_and_ar_closure_screenshot(browser,db,sample):
    user=sample['strategy']; user.password_hash=hash_password('browser-test-only');db.commit()
    app.dependency_overrides[get_db]=lambda:db
    try:
        with TestClient(app,follow_redirects=False) as client, browser.new_context(viewport={'width':1440,'height':1100}) as context:
            login(client,user.email,'browser-test-only');route_to_client(context,client)
            page=context.new_page();page.goto('http://testserver/structure')
            wizard=page.locator('#structure-wizard')
            wizard.locator('[name=change_type]').select_option('SPLIT')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.get_by_label('Yürürlük tarihi',exact=True).fill('2027-07-01')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.get_by_label('Meclis karar no',exact=True).fill('2027/48')
            wizard.get_by_label('Meclis karar tarihi',exact=True).fill('2027-06-20')
            wizard.get_by_label('Açıklama',exact=True).fill('Park ve bahçe hizmetlerinin iki müdürlüğe ayrılması')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.locator(f'[name=from_department_ids][value="{sample["department"].id}"]').check()
            wizard.get_by_label('Oluşturulacak müdürlükler',exact=False).fill('Park İşleri Müdürlüğü\nBahçe İşleri Müdürlüğü')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.locator(f'[name="transfer_activity_{sample["activity"].id}_{sample["department"].id}"]').select_option('new:0')
            wizard.locator(f'[name="transfer_indicator_{sample["indicator"].id}_{sample["department"].id}"]').select_option('new:1')
            wizard.locator(f'[name="transfer_official_{sample["official"].id}_{sample["department"].id}"]').select_option('new:0')
            wizard.get_by_label('Aktarım notu',exact=True).fill('Görev dağılımı meclis kararına göre düzenlendi')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            expect(page.locator('#structure-summary')).to_contain_text('Aktarılan işler: 3')
            expect(page.locator('#structure-summary')).to_contain_text('Bahçe İşleri Müdürlüğü')
            capture(page.locator('#structure-decisions'),'wizard-summary.png')
            wizard.get_by_role('button',name='Kararı ve aktarımları kaydet',exact=True).click()
            expect(page.get_by_role('heading',name='Kapanan müdürlüklerde etkin hesaplar')).to_be_visible()
            assert db.scalar(select(StructureChange)).change_type=='SPLIT'
            assert len(db.scalars(select(StructureChangeTransfer)).all())==3
            page.goto('http://testserver/activity-report?year=2027')
            note=page.locator('[data-closure-note]')
            expect(note).to_contain_text('01.07.2027 tarihinde kapandı/birleşti')
            expect(note).to_contain_text('Meclis kararı 2027/48')
            capture(page.locator('main'),'ar-closure-note.png')
    finally: app.dependency_overrides.clear()


def test_wizard_rejects_invalid_decision_and_keeps_inputs(browser,db,sample):
    user=sample['strategy'];user.password_hash=hash_password('browser-test-only');db.commit()
    app.dependency_overrides[get_db]=lambda:db
    try:
        with TestClient(app,follow_redirects=False) as client,browser.new_context() as context:
            login(client,user.email,'browser-test-only');route_to_client(context,client)
            page=context.new_page();page.goto('http://testserver/structure')
            wizard=page.locator('#structure-wizard')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            # Required date prevents advancing, using the browser's normal validation.
            wizard.get_by_role('button',name='İleri',exact=True).click()
            expect(wizard.get_by_label('Yürürlük tarihi',exact=True)).to_be_visible()
            wizard.get_by_label('Yürürlük tarihi',exact=True).fill('2028-01-01')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.get_by_label('Meclis karar no',exact=True).fill('Yanlış tarihli karar')
            wizard.get_by_label('Meclis karar tarihi',exact=True).fill('2029-01-01')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.locator(f'[name=from_department_ids][value="{sample["department"].id}"]').check()
            wizard.get_by_label('Yeni ad',exact=True).fill('Yeni Müdürlük')
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.get_by_role('button',name='İleri',exact=True).click()
            wizard.get_by_role('button',name='Kararı ve aktarımları kaydet',exact=True).click()
            expect(page.get_by_role('alert')).to_contain_text('Meclis karar tarihi yürürlük tarihinden sonra olamaz')
            expect(page.locator('[name=new_name]')).to_have_value('Yeni Müdürlük')
            expect(page.locator('[name=council_decision_no]')).to_have_value('Yanlış tarihli karar')
            assert not db.scalar(select(StructureChange.id))
    finally: app.dependency_overrides.clear()
