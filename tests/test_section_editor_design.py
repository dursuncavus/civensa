"""012: frozen PostgreSQL controls, audit safety and disclosure keyboard behavior."""
from datetime import datetime, UTC
from collections import Counter
from html.parser import HTMLParser
import json
import re
from pathlib import Path

import pytest
from sqlalchemy import select
from app import activity_sections_service as sections
from app.activity_contract_service import digest
from app.models import ARContentEvent, ARUnitWorkflowEvent
from test_activity_sections import section_client, login
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
CONTRACT = Path(__file__).parent / 'fixtures' / 'section_editor_012_contract.json'
CODES = ['I.A', 'I.C.1', 'III.A.1', 'III.B.1', 'III.B.2.i', 'EKLER']


class Controls(HTMLParser):
    """Hidden fields/options/disclosures included; no field values or CSRF secrets."""
    def __init__(self, html):
        super().__init__()
        self.controls = []
        self.in_main = False
        self.export = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main': self.in_main = True
        if tag == 'details' and 'data-section-export' in attrs: self.export = True
        if not self.in_main or tag not in {'a','button','form','input','select','textarea','summary','option'}:
            return
        if tag == 'summary' and self.export: return  # Only newly added presentation control.
        self.controls.append([tag, sorted([k,v] for k,v in attrs.items()
            if k not in {'value','class','style','tabindex'} )])

    def handle_endtag(self, tag):
        if tag == 'main': self.in_main = False
        if tag == 'details': self.export = False


def configure(db, sample, doc, state, actor):
    sample['strategy'].position = 'staff'
    db.flush()
    user = sample['user']
    user.position = 'director' if actor == 'director' else 'staff'
    user.can_submit = actor == 'delegated'
    if state != 'draft-empty':
        sections.save_section(db, user, doc.id, 'I.A',
            [{'type':'paragraph','text':'Sentetik hizmet değerlendirmesi.'}], 'draft', '', doc.revision)
    if state in {'submitted','returned','approved'}:
        payload = sections.numeric_canonical(sections.report_data(db, user, doc.id, use_freeze=False, include_typeset=True))
        for index, (action, before, after) in enumerate(
            [('submit','draft','submitted')] +
            ([('return','submitted','returned')] if state == 'returned' else
             [('approve','submitted','approved')] if state == 'approved' else []), 1):
            db.add(ARUnitWorkflowEvent(document_id=doc.id, revision=doc.revision+index,
                action=action, from_status=before, to_status=after,
                reason='Sentetik iade notu: hizmet kaynağını açıklayın.' if action == 'return' else '',
                actor_id=sample['strategy'].id, actor_name='Sentetik Strateji Müdürü',
                payload_json=payload if action != 'return' else None,
                sha256=digest(payload) if action != 'return' else None,
                content_event_cursor=0, created_at=datetime(2026,10,25,9,tzinfo=UTC)))
    db.flush()
    if actor == 'strategy': sample['strategy'].position = 'director'
    db.commit()


@pytest.mark.parametrize('actor', ['staff','delegated','director','strategy'])
@pytest.mark.parametrize('state', ['draft-empty','draft-content','returned','submitted','approved'])
def test_012_preserves_all_fields_and_action_targets(section_client, db, sample, actor, state):
    client, docs, _, _ = section_client
    doc = docs['birim:'+str(sample['department'].id)]
    configure(db, sample, doc, state, actor)
    login(client, sample['strategy'].email if actor == 'strategy' else sample['user'].email)
    frozen = json.loads(CONTRACT.read_text())
    template = (CONTRACT.parents[2] / 'app/templates/activity_sections_editor.html').read_text()
    assert not Counter(frozen['template_blocks']) - Counter(re.findall(r'{%.*?%}',template))
    assert not Counter(frozen['template_targets']) - Counter(re.findall('(?<=\\s)(?:(?:id|name|href|action|method|role)="[^"]*"|data-[\\w-]+(?:="[^"]*")?)',template))
    for code in CODES:
        response = client.get(f'/activity-sections/reports/{doc.id}?code={code}')
        assert response.status_code == 200
        key = f'{actor}/{state}/{code}'
        actual = Controls(response.text).controls
        expected = frozen['contracts'][frozen['cases'][key]]
        assert Counter(json.dumps(c, sort_keys=True) for c in actual) == Counter(json.dumps(c, sort_keys=True) for c in expected), key


@pytest.mark.parametrize('width', [1440,390])
def test_012_export_audit_focus_and_safe_summary(browser, section_client, db, sample, width):
    from playwright.sync_api import expect
    client, docs, _, _ = section_client
    doc = docs['birim:'+str(sample['department'].id)]
    configure(db, sample, doc, 'draft-content', 'director')
    login(client, sample['user'].email)
    # Untrusted content is rendered as text; malformed old payloads degrade safely.
    db.add(ARContentEvent(document_id=doc.id, section_code='I.A', action='section_save',
        before_json='invalid', after_json='<script>window.bad=true</script>', actor_id=sample['user'].id))
    db.add(ARContentEvent(document_id=doc.id, section_code='I.A', action='section_save',
        before_json='{}', after_json='{"reason":""}', actor_id=sample['user'].id))
    db.commit()
    with browser.new_context(viewport={'width':width,'height':900}) as context:
        errors = []
        def serve(route):
            assert route.request.method == 'GET'
            response = client.get(route.request.url)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}?code=I.A')
        trigger = page.locator('[data-section-export] > summary')
        trigger.focus(); page.keyboard.press('Enter')
        expect(page.locator('[data-section-export]')).to_have_attribute('open','')
        page.keyboard.press('Tab')
        expect(page.get_by_role('link',name='Word olarak indir',exact=True)).to_be_focused()
        page.keyboard.press('Escape'); expect(trigger).to_be_focused()
        expect(page.locator('[data-section-audit]').first.locator('[data-section-change]')).to_have_text(
            'Kayıt ayrıntılarını Teknik ayrıntı bölümünde inceleyebilirsiniz.')
        audit = page.locator('[data-section-audit]').last
        expect(audit.locator('[data-section-change]')).to_contain_text('Durum: Boş → Taslak')
        expect(audit.locator('[data-section-change]')).to_contain_text('İçerik: 1 paragraf eklendi')
        expect(audit.locator('pre').first).not_to_be_visible()
        detail = audit.locator('summary')
        detail.focus(); page.keyboard.press('Enter')
        expect(audit.locator('pre').first).to_be_visible()
        page.keyboard.press('Escape'); expect(detail).to_be_focused()
        assert page.locator('[data-section-audit] script').count() == 0
        assert page.evaluate('window.bad === undefined')
        field = page.locator('[name=text]'); field.focus()
        style = field.evaluate('el => {const s=getComputedStyle(el);return [s.outlineColor,s.outlineWidth,s.boxShadow,s.borderColor]}')
        assert style == ['rgb(30, 107, 101)','2px','none','rgb(84, 91, 100)']
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert not errors
