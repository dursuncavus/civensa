"""Queue labels, repair links and post-save readiness in a real browser."""
import pytest
from playwright.sync_api import expect

from test_sidebar_ui import browser
from test_activity_mapping_gaps import strategy_client, remove_link

pytestmark = pytest.mark.postgres


def test_queue_labels_remain_after_subprogram_save(browser, strategy_client, db, sample):
    activity = sample['activity']
    remove_link(db, activity, 'subprogram')
    remove_link(db, activity, 'card')
    remove_link(db, activity, 'catalogue')
    with browser.new_context(viewport={'width': 1366, 'height': 900}) as context:
        writes = []

        def serve(route):
            request = route.request
            response = strategy_client.request(
                request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')},
                follow_redirects=False,
            )
            if '/activity-mappings/bulk' in request.url:
                writes.append((request.url, response.status_code, response.json()))
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto('http://testserver/activity-mapping?period_id=1')
        row = page.locator(f'.mapping-row[data-activity="{activity.id}"]')
        expect(row.locator('.mapping-states')).to_contain_text('Alt program: Eksik')
        expect(row).to_contain_text('Alt program seçilmedi: bu faaliyet için Program / Alt Program seçip kaydedin.')
        expect(row).to_contain_text('Kart seçilmedi: faaliyeti bir performans kartına bağlayın.')
        expect(row).to_contain_text('Resmî katalog bağlantısı yok: faaliyeti resmî faaliyet kataloğundaki bir kayda bağlayın.')
        expect(row.get_by_role('link', name='Performans Kartlarını Aç')).to_have_attribute('href', '/program/1?period_id=1')
        page.on('dialog', lambda dialog: dialog.accept())
        row.locator('.mapping-select').select_option(str(sample['subprogram'].id))
        with page.expect_navigation():
            page.locator('#saveAllMappings').click()
        assert writes[0][1] == 200
        assert 'period_id=1' in writes[0][0]
        assert writes[0][2]['remaining'] == 1
        expect(page.locator('.mapping-summary')).to_contain_text('Kontrol gerekli')
        expect(row.locator('.mapping-states')).to_contain_text('Alt program: Tamam')
        expect(row.locator('.mapping-states')).to_contain_text('Kart: Eksik')
        expect(row.locator('.mapping-states')).to_contain_text('Resmî katalog: Eksik')
        expect(row.locator('.mapping-select')).to_have_count(0)
        # The queue must still support filtering when only card/catalogue gaps remain.
        page.locator('#mappingSearch').fill('Bulunmayan faaliyet')
        expect(row).to_be_hidden()
        page.locator('#mappingSearch').fill('')
        expect(row).to_be_visible()
        from app.models import ActivityCatalogueLink
        activity.card_id = sample['card'].id
        db.add(ActivityCatalogueLink(activity_id=activity.id, official_activity_id=sample['official'].id))
        db.commit()
        page.reload()
        expect(page.locator('.mapping-summary')).to_contain_text('Hazır')
        expect(page.locator('.mapping-row')).to_have_count(0)
