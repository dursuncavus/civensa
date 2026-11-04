"""CIV-180 HTTP acceptance on disposable PostgreSQL, including approved copies."""
from hashlib import sha256
import re

import pytest

from test_activity_sections import section_client, login, ready_and_freeze, resource

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('email', ['test@example.invalid', 'strategy@example.invalid'])
def test_own_strategy_download_and_cross_department_forbidden(section_client, sample, email):
    client, docs, other, _ = section_client
    own = docs[f"birim:{sample['department'].id}"]
    login(client, email)
    for doc in [own, docs[f'birim:{other.id}'], docs['idare']]:
        expected = 200 if doc == own or email == 'strategy@example.invalid' else 403
        for suffix in ['sunum', 'sunum.html']:
            response = client.get(f'/activity-sections/reports/{doc.id}/{suffix}')
            assert response.status_code == expected, response.text[:500]
            if expected == 403:
                assert "script-src 'self'" in response.headers['content-security-policy']
                assert response.json() == client.get(f'/activity-sections/reports/{doc.id}/export.pdf').json()
                assert 'Kendi birim raporunuzu açın' in response.json()['detail']
            else:
                assert "script-src 'unsafe-inline'" in response.headers['content-security-policy']
                assert "frame-ancestors 'none'" in response.headers['content-security-policy']
                assert response.headers['content-type'].startswith('text/html')
                assert response.headers['cache-control'] == 'private, no-store'
                assert response.headers['x-content-type-options'] == 'nosniff'
                assert response.headers['content-disposition'].startswith('attachment' if suffix.endswith('.html') else 'inline')
                assert len(response.content) <= 3_000_000
    client.cookies.clear()
    assert client.get(f'/activity-sections/reports/{own.id}/sunum').status_code == 401


def test_draft_links_and_bad_report(section_client, sample):
    client, docs, _, _ = section_client
    own = docs[f"birim:{sample['department'].id}"]
    deck = client.get(f'/activity-sections/reports/{own.id}/sunum')
    assert b'TASLAK' in deck.content
    page = client.get(f'/activity-sections/reports/{own.id}').text
    assert 'Sunumu aç' in page and 'Sunumu indir' in page
    assert f'/reports/{own.id}/sunum.html' in page
    assert re.search(r'data-sunum-verification>.*TASLAK', page)
    missing = client.get('/activity-sections/reports/999999/sunum.html')
    assert missing.status_code == 404
    assert 'Rapor listesinden' in missing.json()['detail']


def test_draft_editor_does_not_canonicalize_payload(section_client, sample, monkeypatch):
    from app import activity_sections_service
    client, docs, _, _ = section_client
    own = docs[f"birim:{sample['department'].id}"]
    def unexpected_serialization(*args, **kwargs):
        raise AssertionError('Draft editor must not canonicalize the report')
    monkeypatch.setattr(activity_sections_service, 'numeric_canonical', unexpected_serialization)
    response = client.get(f'/activity-sections/reports/{own.id}')
    assert response.status_code == 200
    assert re.search(r'data-sunum-verification>.*TASLAK', response.text)


@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('scope', ['birim', 'idare'])
def test_frozen_code_matches_export_bytes_and_report_page(section_client, sample, legacy, scope):
    client, docs, _, _ = section_client
    doc = docs['idare' if scope == 'idare' else f"birim:{sample['department'].id}"]
    token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc, legacy=legacy)
    canonical = client.get(f'/activity-sections/reports/{doc.id}/export.json').content
    short = sha256(canonical).hexdigest()[:8].upper()
    expected = short[:4] + '-' + short[4:]
    deck = client.get(f'/activity-sections/reports/{doc.id}/sunum').text
    page = client.get(f'/activity-sections/reports/{doc.id}').text
    assert f'Doğrulama kodu <b>{expected}</b>' in deck
    assert f'Doğrulama kodu <strong>{expected}</strong>' in page
    assert '<b class="sample">TASLAK</b>' not in deck
    if scope == 'idare' or legacy:
        versioned = client.get(f'/activity-sections/reports/{doc.id}/sunum?version=1')
        assert versioned.status_code == 200 and expected in versioned.text
    else:
        assert client.get(f'/activity-sections/reports/{doc.id}/sunum?version=999').status_code == 404


def test_23_resource_rows_render_three_tables_via_http(section_client, sample):
    from lxml import html
    client, docs, _, _ = section_client
    own = docs[f"birim:{sample['department'].id}"]
    token = login(client, 'strategy@example.invalid')
    assert resource(client, token, own, 'buildings', [dict(name=f'Bina {i}', category='Hizmet',
        address='Merkez', area=None if i else 0, ownership='mülk') for i in range(23)]).status_code == 200
    document = html.fromstring(client.get(f'/activity-sections/reports/{own.id}/sunum.html').content)
    tables = document.xpath('//section[@data-type="table"]')
    assert len(tables) == 3
    assert [len(table.xpath('.//tbody/tr')) for table in tables] == [10, 10, 3]
    assert [table.xpath('.//p[@class="cont"]/text()')[0] for table in tables] == ['Tablo 1/3', 'Tablo 2/3', 'Tablo 3/3']


def test_sunum_missing_assets_and_size_errors_are_actionable(section_client, sample, monkeypatch):
    from app import sunum
    from app.sunum.engine import DeckTooLarge
    client, docs, _, _ = section_client
    own = docs[f"birim:{sample['department'].id}"]
    for error, status in [(OSError('missing'), 503), (DeckTooLarge(), 422)]:
        def fail(*args, **kwargs):
            raise error
        monkeypatch.setattr(sunum, 'render_deck', fail)
        response = client.get(f'/activity-sections/reports/{own.id}/sunum')
        assert response.status_code == status
        assert '2027 Test Müdürlüğü' in response.json()['detail']
