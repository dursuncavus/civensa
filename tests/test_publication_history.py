"""CIV-076: read-only publication labels, scoped reopen trace and downloads."""
from datetime import datetime, timedelta
import os
from pathlib import Path

from lxml.html import fromstring
import pytest
from playwright.sync_api import expect
from sqlalchemy import event, select

from app.models import Department, DepartmentScope, Publication, ReportingPeriod, ReportSection, Submission, SubmissionEvent
from app.publication_history import publication_history
from tests.test_released_permissions import actors, http
from tests.test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
REASON = 'Gösterge hedefini kaynak belgeye göre düzeltin.'


@pytest.fixture
def ready(db, sample, http):
    strategy = http('strategy_director')
    sub = db.scalar(select(Submission))
    sub.status = 'approved'
    db.add(ReportSection(period_id=sub.period_id, title='Genel Bilgiler', kind='text',
                         content_json='{"text":"Onaylı içerik"}'))
    for dep in db.scalars(select(Department).where(Department.id != sub.department_id)):
        db.add(DepartmentScope(period_id=sub.period_id, department_id=dep.id,
                               status='excluded', reason='Bu dönem PP verisi yok.'))
    db.commit()
    return strategy, sub


def publish(strategy, pid):
    response = strategy.post('/report-builder/publish', data={'period_id': pid})
    assert response.status_code == 303, response.text


def section(strategy, pid):
    response = strategy.get(f'/report-builder?period_id={pid}')
    assert response.status_code == 200, response.text
    return response.text.split('<section aria-label="Yayın sürümleri"')[1].split('</section>')[0]


def reopen(strategy, sub, reason=REASON):
    response = strategy.post(f'/api/submissions/{sub.id}/reopen?period_id={sub.period_id}',
                             json={'reason': reason})
    assert response.status_code == 200, response.text


def test_empty_and_single_publication(ready, db):
    strategy, sub = ready
    assert 'Güncel sürüm' not in section(strategy, sub.period_id)
    publish(strategy, sub.period_id)
    text = section(strategy, sub.period_id)
    assert 'Sürüm 1 Güncel sürüm' in ' '.join(fromstring(text).text_content().split())
    assert 'Önceki sürüm' not in text
    assert 'düzeltme için açılan paketler' not in text
    assert 'role="alert"' not in text


def test_real_reopen_reapprove_republish_preserves_downloads(ready, db, sample, http, monkeypatch):
    # Export containers embed wall-clock metadata. Stabilize only that metadata
    # to compare actual Word/PDF bytes from the unchanged download endpoints.
    import zipfile
    from reportlab import rl_config
    monkeypatch.setattr(zipfile.time, 'localtime', lambda *_: (2026, 10, 22, 12, 0, 0, 3, 295, 0))
    monkeypatch.setattr(rl_config, 'invariant', 1)
    strategy, sub = ready
    publish(strategy, sub.period_id)
    old = db.scalar(select(Publication))
    before = (old.snapshot_json, old.sha256)
    def downloads():
        result = {}
        for fmt in ('docx', 'pdf', 'json'):
            response = strategy.get(f'/publications/{old.id}.{fmt}')
            assert response.status_code == 200
            result[fmt] = response.content
        return result
    old_bytes = downloads()
    reopen(strategy, sub)
    warning = section(strategy, sub.period_id)
    assert 'Güncel sürümden sonra şu müdürlüklerin paketi gerekçeyle açıldı: Test Müdürlüğü.' in warning
    assert 'Yeniden onaydan sonra yeni sürüm oluşturun.' in warning
    assert downloads() == old_bytes
    department = http('director')
    response = department.post(f'/api/indicators/{sample["indicator"].id}/save?period_id={sub.period_id}',
                               json={'value_2027_target': '2,5'})
    assert response.status_code == 200, response.text
    assert department.post(f'/api/departments/{sub.department_id}/submit?period_id={sub.period_id}').status_code == 200
    assert strategy.post(f'/api/submissions/{sub.id}/decision?period_id={sub.period_id}',
                         json={'decision': 'approve'}).status_code == 200
    publish(strategy, sub.period_id)
    text = section(strategy, sub.period_id)
    labels = ' '.join(fromstring(text).text_content().split())
    assert labels.index('Sürüm 2 Güncel sürüm') < labels.index('Sürüm 1 Önceki sürüm · Sürüm 2 ile değiştirildi')
    current, previous = text.split('data-publication-version="1"')
    assert REASON in current and REASON not in previous
    assert 'Test Müdürlüğü' in current and 'Strateji' in current
    assert 'role="alert"' not in text
    assert downloads() == old_bytes
    db.refresh(old)
    assert (old.snapshot_json, old.sha256) == before
    reopen(strategy, sub, 'İkinci düzeltme gerekçesi.')
    assert 'role="alert"' in section(strategy, sub.period_id)
    assert downloads() == old_bytes
    # Department sessions cannot reach another department's reasons or downloads.
    assert http('other').get(f'/report-builder?period_id={sub.period_id}').status_code == 403
    assert http('other').get(f'/publications/{old.id}.json').status_code == 403


def seed_history(db, sample):
    start = datetime(2026, 10, 20, 9)
    pubs = []
    for version in (1, 2, 3):
        pub = Publication(period_id=sample['period'].id, version=version,
            snapshot_json='{}', sha256='unused', created_by=sample['strategy'].id,
            created_at=start + timedelta(hours=version))
        db.add(pub); pubs.append(pub)
    db.flush()
    sub = db.scalar(select(Submission))
    def add(at, note, department_id=None, kind='reopen', period_id=None):
        row = SubmissionEvent(submission_id=sub.id, period_id=period_id or sub.period_id,
            department_id=department_id or sub.department_id, actor_user_id=sample['strategy'].id,
            event_type=kind, note=note, created_at=at)
        db.add(row)
        return row
    db.commit()
    return pubs, add


def test_intervals_scope_and_no_history_before_first(db, sample):
    pubs, add = seed_history(db, sample)
    t1, t2, t3 = [p.created_at for p in pubs]
    add(t1 - timedelta(seconds=1), 'Before first')
    add(t1, 'At first')
    add(t1 + timedelta(seconds=1), 'For v2')
    add(t2, 'At v2')
    add(t2 + timedelta(seconds=1), 'For v3')
    add(t3, 'At v3')
    add(t3 + timedelta(seconds=1), 'Stale')
    add(t3 + timedelta(seconds=2), 'Stale again')
    add(t2, 'Not reopen', kind='return')
    other = Department(organization_id=sample['department'].organization_id, name='Gizli Müdürlük')
    db.add(other); db.flush()
    add(t2, 'Başka müdürlüğün gizli gerekçesi', other.id)
    db.commit()
    result = publication_history(db, sample['period'].id, sample['user'], {sample['department'].id: 'Dönem adı'})
    assert [p.version for p in result['publications']] == [3, 2, 1]
    assert result['superseded_by'] == {pubs[0].id: 2, pubs[1].id: 3}
    assert result['publication_reopens'][pubs[0].id] == []
    notes = lambda p: [item['event'].note for item in result['publication_reopens'][p.id]]
    assert notes(pubs[1]) == ['For v2', 'At v2']
    assert notes(pubs[2]) == ['For v3', 'At v3']
    assert result['stale_departments'] == ['Dönem adı']
    assert all(item['department_name'] == 'Dönem adı' for group in result['publication_reopens'].values() for item in group)


def test_builder_query_count_constant_with_many_versions(ready, db, sample):
    strategy, sub = ready
    publish(strategy, sub.period_id)
    def measured():
        db.expire_all()
        statements = []
        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)
        event.listen(db.get_bind(), 'before_cursor_execute', record)
        try:
            section(strategy, sub.period_id)
        finally:
            event.remove(db.get_bind(), 'before_cursor_execute', record)
        return statements
    first = measured()
    old = db.scalar(select(Publication))
    for version in range(2, 27):
        db.add(Publication(period_id=sub.period_id, version=version,
            snapshot_json=old.snapshot_json, sha256=old.sha256, created_by=sample['strategy'].id))
        db.add(SubmissionEvent(submission_id=sub.id, department_id=sub.department_id,
            period_id=sub.period_id, actor_user_id=sample['strategy'].id, event_type='reopen', note=REASON))
    db.commit()
    many = measured()
    assert len(many) == len(first)
    assert sum('FROM ' in s and 'submission_events' in s for s in many) == 1


def test_period_isolation_and_warning_departments_are_unique(db, sample):
    pubs, add = seed_history(db, sample)
    other = Department(organization_id=sample['department'].organization_id, name='İkinci Müdürlük')
    period = ReportingPeriod(year=2028, status='draft')
    db.add_all([other, period]); db.flush()
    db.add(Publication(period_id=period.id, version=99, snapshot_json='{}', sha256='unused',
        created_by=sample['strategy'].id, created_at=pubs[-1].created_at))
    later = pubs[-1].created_at + timedelta(seconds=1)
    add(later, 'Başka dönem gerekçesi', period_id=period.id)
    add(later, 'İlk açma')
    add(later, 'İkinci açma')
    add(later, 'Diğer müdürlük açma', department_id=other.id)
    db.commit()
    result = publication_history(db, sample['period'].id, sample['strategy'], {})
    assert [p.version for p in result['publications']] == [3, 2, 1]
    assert result['stale_departments'] == ['Test Müdürlüğü', 'İkinci Müdürlük']
    assert all(not items for items in result['publication_reopens'].values())


@pytest.mark.parametrize('viewport', [(1366, 1000), (390, 844)])
def test_chromium_turkish_history(browser, ready, db, sample, viewport):
    strategy, sub = ready
    pubs, add = seed_history(db, sample)
    add(pubs[1].created_at, REASON)
    add(pubs[2].created_at, 'Mali tablo kaynak tutarı düzeltildi.')
    add(pubs[2].created_at + timedelta(seconds=1), 'Yeni düzeltme gerekiyor.')
    db.commit()
    errors = []
    with browser.new_context(viewport={'width': viewport[0], 'height': viewport[1]}) as context:
        def serve(route):
            request = route.request
            response = strategy.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/report-builder?period_id={sub.period_id}#publication-history')
        history = page.get_by_role('region', name='Yayın sürümleri')
        expect(history.get_by_role('heading', name='Sürüm 3 Güncel sürüm', exact=True)).to_be_visible()
        expect(history.get_by_role('alert')).to_contain_text('Yeniden onaydan sonra yeni sürüm oluşturun.')
        expect(history.locator('article')).to_have_count(3)
        expect(history.locator('article').nth(1)).to_contain_text('Önceki sürüm · Sürüm 3 ile değiştirildi')
        expect(history.locator('article').nth(1)).to_contain_text(REASON)
        expect(history.locator('article').nth(1)).to_contain_text('20.10.2026 14:00')
        expect(history.locator('article').last).not_to_contain_text('düzeltme için açılan paketler')
        for article in history.locator('article').all():
            for label, fmt in [('Word', 'docx'), ('PDF', 'pdf'), ('Veri Arşivi', 'json')]:
                expect(article.get_by_role('link', name=label, exact=True)).to_have_attribute('href', f'/publications/{pubs[int(article.get_attribute("data-publication-version"))-1].id}.{fmt}')
        assert page.locator('html').evaluate('(el) => el.scrollWidth <= el.clientWidth')
        assert history.evaluate('(el) => el.scrollWidth <= el.clientWidth')
        folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
        if folder:
            target = Path(folder); target.mkdir(parents=True, exist_ok=True)
            history.screenshot(path=str(target / f'publication-history-{viewport[0]}.png'))
        assert not errors
