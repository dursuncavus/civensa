"""CIV-199: Strateji screens are scannable and safe against double submission."""
import re
from html import unescape
from pathlib import Path

import pytest
from sqlalchemy import delete, select

from app.main import app, require_user, templates
from app.activity_sections_routes import GENERIC_SECTION_HINT, completion_view, fold_department_messages
from app.models import ActivityCatalogueLink, ActivityReport, ActivityReportRevision, Organization, ReportingPeriod
from test_activity_contract import publish, new_report
from test_activity_sections import section_client  # noqa: F401  (fixture)

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def strategy_client(client, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    return client


def text(html):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', html))).strip()


# (1) double-submit guard -------------------------------------------------------

def test_double_submit_guard_is_global_and_leaves_custom_handlers_alone():
    js = (ROOT / 'app/static/app.js').read_text(encoding='utf-8')
    guard = js[js.index('CIV-199: one submission per normal POST form'):]
    assert "document.addEventListener('submit'" in guard
    assert 'event.defaultPrevented' in guard          # custom fetch handlers prevent default
    assert "form.dataset.busy" in guard and 'stopImmediatePropagation' in guard
    assert 'İşleniyor…' in guard and 'Sayfayı yenilemeyin' in guard
    assert "addEventListener('pageshow'" in guard and 'event.persisted' in guard
    assert "toLowerCase()==='post'" in guard and 'data-no-busy' in guard
    css = (ROOT / 'app/static/app.css').read_text(encoding='utf-8')
    assert '.is-busy::before' in css and 'prefers-reduced-motion' in css


def pub_year(db, pub):
    return db.get(ReportingPeriod, pub.period_id).year


# (2) single organization ----------------------------------------------------------

def test_single_organization_is_shown_as_text_with_hidden_id(strategy_client, db, sample):
    publish(strategy_client, db, sample)
    org = db.scalar(select(Organization))
    for path in ('/activity-reports', '/activity-sections'):
        html = strategy_client.get(path).text
        assert '<select name="organization_id"' not in html, path
        assert f'<input type="hidden" name="organization_id" value="{org.id}">' in html, path
        # (2b) owner, 9 Nov 2026: with one organization its name is not shown at all.
        assert '<div class="single-organization" hidden>' in html, path


def test_two_organizations_keep_the_select(strategy_client, db, sample):
    publish(strategy_client, db, sample)
    db.add(Organization(name='İkinci Belediye')); db.commit()
    for path in ('/activity-reports', '/activity-sections'):
        html = strategy_client.get(path).text
        assert '<select name="organization_id"' in html, path
        assert 'single-organization' not in html, path


# (3) report builder order and collapsed reconciliation ---------------------------

def test_report_builder_publication_actions_precede_reconciliation(strategy_client, sample):
    html = strategy_client.get(f'/report-builder?period_id={sample["period"].id}').text
    publish_at = html.index('Kontrol Et ve Nihai Sürümü Oluştur')
    history_at = html.index('id="publication-history"')
    scope_at = html.index('id="department-scope"')
    assert publish_at < history_at < scope_at
    if 'id="pp-reconciliation"' in html:
        assert history_at < html.index('id="pp-reconciliation"')


def test_collapsed_reconciliation_summary_and_scope_note():
    rows = [dict(level='program', label='P', path='P', year=2026, value_kind='budget', complete=False,
                 amount=None, source_amount=None, difference=None, status='Yayın engeli',
                 errors=['eksik'], warnings=[])] * 3
    collapsed = templates.env.get_template('pp_reconciliation.html').render(reconciliation=rows, reconciliation_collapsed=True)
    assert '<details class="pp-reconciliation-table">' in collapsed
    assert '3 satırda yayın engeli var' in text(collapsed) and 'Tabloyu göster (3 satır)' in text(collapsed)
    assert 'yalnız “Nihai Sürüm” için geçerlidir' in text(collapsed)
    plain = templates.env.get_template('pp_reconciliation.html').render(reconciliation=rows)
    assert 'pp-reconciliation-table' not in plain
    assert '3 satırda yayın engeli var. Ayrıntıyı ilgili satırdaki “Ayrıntı” bağlantısından açın.' in plain


# (4) activity mapping sentence ------------------------------------------------------

@pytest.mark.parametrize('kind,expected', [
    ('subprogram', '1 müdürlükte 1 faaliyetin alt programı seçilmeli'),
    ('card', 'Alt program seçimi tamam. 1 faaliyette kart, 0 faaliyette resmî katalog bağlantısı eksik; bunlar müdürlüğün performans kartları sayfasında tamamlanır.'),
    (None, 'Bütün faaliyetlerin alt program, kart ve resmî katalog bağlantıları tamam.'),
])
def test_mapping_summary_is_one_plain_sentence(strategy_client, db, sample, kind, expected):
    if kind:
        setattr(sample['activity'], kind + '_id', None)
        db.commit()
    html = strategy_client.get(f'/activity-mapping?period_id={sample["period"].id}').text
    sentence = re.search(r'<p class="mapping-sentence" data-mapping-sentence>(.*?)</p>', html, re.S)
    assert sentence and expected in text(sentence.group(1))
    assert '<dl class="mapping-counts">' in html  # counters stay, folded under "Bütün sayılar"
    assert '<details class="mapping-counts-details"><summary>Bütün sayılar</summary>' in html
    todo = re.search(r'<ol class="mapping-todo" data-mapping-todo>(.*?)</ol>', html, re.S)
    if kind:
        assert todo and text(todo.group(1)).count('—') == 3
        assert ('Kart bağlantısı — 1 faaliyet.' in text(todo.group(1))) == (kind == 'card')
        assert f'href="/program/{sample["department"].id}?period_id={sample["period"].id}"' in html
    else:
        assert todo is None


# (5) EK-1 completion view -------------------------------------------------------------

def test_repeated_department_problems_are_folded_once():
    names = {'Fen İşleri Müdürlüğü', 'Park ve Bahçeler Müdürlüğü'}
    folded = fold_department_messages([
        'Fen İşleri Müdürlüğü: Ekonomik kod gider satırları eksik.',
        'Park ve Bahçeler Müdürlüğü: Ekonomik kod gider satırları eksik.',
        'Sağlık İşleri Müdürlüğü: Program / alt program gider satırları eksik.',
        'Genel bir uyarı.'], names)
    assert folded[0] == {'problem': 'Ekonomik kod gider satırları eksik.',
                         'departments': ['Fen İşleri Müdürlüğü', 'Park ve Bahçeler Müdürlüğü']}
    assert folded[1] == {'text': 'Sağlık İşleri Müdürlüğü: Program / alt program gider satırları eksik.'}
    assert folded[2] == {'text': 'Genel bir uyarı.'}


def test_completion_view_groups_by_owner_and_drops_generic_hint():
    matches = [
        dict(code='I.A', title='A', status='empty', owner='strategy', missing=[GENERIC_SECTION_HINT]),
        dict(code='I.B', title='B', status='empty', owner='strategy', missing=[GENERIC_SECTION_HINT]),
        dict(code='I.C', title='C', status='empty', owner='strategy', missing=[GENERIC_SECTION_HINT]),
        dict(code='I.D', title='D', status='empty', owner='strategy', missing=[GENERIC_SECTION_HINT]),
        dict(code='III.A.1', title='C', status='empty', owner='finance',
             missing=[GENERIC_SECTION_HINT, 'Fen İşleri Müdürlüğü: X eksik.', 'Zabıta Müdürlüğü: X eksik.']),
        dict(code='IV', title='D', status='ready', owner='directorate', missing=[]),
    ]
    view = completion_view(matches, set())
    assert view['status_counts'] == {'empty': 5, 'ready': 1}
    assert [g['owner'] for g in view['owner_groups']] == ['strategy', 'finance', 'directorate']
    strategy, finance, directorate = view['owner_groups']
    assert not strategy['open'] and strategy['rows'][0]['problems'] == [] and strategy['rows'][0]['needs_review']
    assert finance['rows'][0]['problems'] == [
        {'problem': 'X eksik.', 'departments': ['Fen İşleri Müdürlüğü', 'Zabıta Müdürlüğü']}]
    assert finance['problem_rows'] == 1
    assert finance['open'] and directorate['open']                  # short groups (<= 3 rows) stay open
    mixed = completion_view(matches[:3] + [dict(matches[3], status='ready')], set())
    assert mixed['owner_groups'][0]['open']                          # mixed statuses stay open


def test_completion_page_shows_hint_once_and_groups(section_client, sample):
    client, docs, _, _ = section_client
    html = client.get(f'/activity-sections?period_id={sample["period"].id}').text
    assert html.count('completion-hint') == 1
    assert GENERIC_SECTION_HINT not in html                      # no longer repeated per row
    assert 'data-completion-summary' in html
    owners = re.findall(r'<details class="owner-group" data-owner="(\w+)"', html)
    assert owners and set(owners) <= {'strategy', 'finance', 'directorate'}
    assert 'Gözden geçirilmeli' in html
    # every report still links every section exactly as before
    for doc in docs.values():
        assert f'href="/activity-sections/reports/{doc.id}?code=I.A"' in html


# (6) error page ------------------------------------------------------------------------

def test_duplicate_report_error_links_existing_report_and_shows_names(strategy_client, db, sample):
    pub = publish(strategy_client, db, sample)
    new_report(strategy_client, pub, sample)
    org = db.get(Organization, sample['department'].organization_id)
    response = strategy_client.post('/activity-reports/revisions',
                                    data={'publication_id': pub.id, 'organization_id': org.id})
    assert response.status_code == 409
    html = response.text
    assert 'kurum ve yıl' in html and 'mevcut raporu açıp yeni revizyon' in html  # message unchanged
    report = db.scalar(select(ActivityReport))
    revision = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id,
                                                              ActivityReportRevision.revision == report.current_revision))
    assert f'href="/activity-reports/revisions/{revision.id}" data-existing-record' in html
    assert f'Mevcut raporu aç: {pub_year(db, pub)} · Rapor revizyon {revision.revision}' in html
    assert org.name not in html.split('data-existing-record>')[1].split('</a>')[0]  # (2b) single organization
    db.add(Organization(name='İkinci Belediye')); db.commit()
    again = strategy_client.post('/activity-reports/revisions', data={'publication_id': pub.id, 'organization_id': org.id}).text
    assert f'Mevcut raporu aç: {org.name} ·' in again
    assert 'Düzeltilen bilgileri yeniden gönder' not in html
    assert '<textarea name="organization_id"' not in html


def test_other_errors_show_ids_read_only_with_labels(strategy_client, db, sample):
    pub = publish(strategy_client, db, sample)
    org = db.get(Organization, sample['department'].organization_id)
    response = strategy_client.post('/activity-reports/revisions',
                                    data={'publication_id': pub.id + 999, 'organization_id': org.id})
    assert response.status_code >= 400
    html = response.text
    assert '<textarea name="organization_id"' not in html and '<textarea name="publication_id"' not in html
    # (2b) single organization: the Kurum row is a bare hidden field.
    assert '<span>Kurum</span>' not in html
    assert f'<input type="hidden" name="organization_id" value="{org.id}">' in html
    db.add(Organization(name='İkinci Belediye')); db.commit()
    again = strategy_client.post('/activity-reports/revisions',
                                 data={'publication_id': pub.id + 999, 'organization_id': org.id}).text
    assert f'<span>Kurum</span> <b>{org.name}</b>' in again
