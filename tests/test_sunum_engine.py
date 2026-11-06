"""CIV-180: data fidelity, generic pagination and offline rendering."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import logging
import re

from lxml import html
import pytest

from app.activity_sections_service import numeric_canonical
from app.sunum import activity_report, render_deck, verification_code
from app.sunum.engine import DeckTooLarge, MAX_BYTES, prepare_slides


@pytest.fixture
def presentation_payload():
    return {'id': 180, 'year': 2027, 'department_id': 1, 'department': 'Test Müdürlüğü',
        'organization': 'Test Belediyesi', 'frozen': False,
        'sections': [
            {'code': 'I.B', 'title': 'Yetki, Görev ve Sorumluluklar', 'blocks': [
                {'type': 'bullets', 'items': ['Vatandaş taleplerini değerlendirmek', 'Hizmetleri planlamak',
                    'Kaynakları verimli kullanmak', 'Çalışmaları denetlemek', 'Sonuçları raporlamak', 'Altıncı görev']}]},
            {'code': 'II.B', 'title': 'Stratejik Amaç ve Hedefler', 'blocks': [
                {'type': 'paragraph', 'text': 'Erişilebilir ve sürdürülebilir kamusal alanlar oluşturmak.'},
                {'type': 'paragraph', 'text': 'Vatandaş katılımını destekleyen hizmetler sunmak.'}]},
            {'code': 'III.B.1', 'title': 'Faaliyet Bilgileri', 'blocks': [
                {'type': 'table', 'rows': [['Faaliyet', 'Maliyet (TL)', 'Durum'],
                    ['Park bakımı', '12.500,23', 'Tamamlandı'], ['Yol yenileme', '', 'Sürüyor']]}]}],
        'resources': {'employment': {'rows': [{'category': 'Memur', 'count': 18},
            {'category': 'İşçi', 'count': 4}, {'category': 'Şirket personeli', 'count': 110}]},
            'buildings': {'rows': [{'name': 'Merkez hizmet binası', 'category': 'Hizmet binası',
                'address': 'Merkez', 'area': Decimal('12500.23'), 'ownership': 'mülk'},
                {'name': 'Saha ofisi', 'area': None}]}},
        'financial': {'tables': {'expenditure': {'rows': [
            {'initial': Decimal('710000000'), 'final': Decimal('811776000'), 'actual': Decimal('613713763.78')}]} }},
        'core': {'indicators': [{'name': 'Hizmet sayısı', 'targets': [{'value': '100', 'state': 'verified'}],
            'actual': 75, 'actual_state': 'verified'}]}}


def render(payload):
    return render_deck(activity_report(payload), title='Test raporu', code=verification_code(payload, numeric_canonical(payload)))


def test_table_23_rows_and_bullets_paginate_without_mutation():
    slides = [dict(type='table', title='Binalar', headers=['Adı', 'Alan'], source='Rapor',
        rows=[[f'Bina {i}', None if i else 0] for i in range(23)]),
        dict(type='bullets', title='Görevler', bullets=[str(i) for i in range(12)], source='Rapor')]
    original = deepcopy(slides)
    prepared = prepare_slides(slides)
    assert [s['continuation'] for s in prepared[:3]] == ['Tablo 1/3', 'Tablo 2/3', 'Tablo 3/3']
    assert [len(s['rows']) for s in prepared[:3]] == [10, 10, 3]
    assert [len(s['bullets']) for s in prepared[3:]] == [5, 5, 2]
    assert prepared[0]['rows'][:2] == [['Bina 0', '0'], ['Bina 1', '—']]
    assert all(max(s['row_delays']) + 350 <= 1500 for s in prepared[:3])
    assert slides == original
    document = html.fromstring(render_deck(slides, title='Test', code='TASLAK'))
    assert len(document.xpath('//section[@data-type="table"]')) == 3
    assert all(len(s.xpath('.//tbody/tr')) <= 10 for s in document.xpath('//section[@data-type="table"]'))


@pytest.mark.parametrize('code', ['TASLAK', 'ABCD-1234'])
def test_separator_has_no_source_or_verification_footer(presentation_payload, code):
    document = html.fromstring(render_deck(activity_report(presentation_payload), title='Test', code=code))
    separators = document.xpath('//section[@data-type="separator"]')
    assert separators
    for section in separators:
        assert not section.xpath('.//div[@class="foot"]')
        assert 'Kaynak:' not in section.text_content()
        assert 'Doğrulama kodu' not in section.text_content()
        assert section.xpath('.//img[@class="sep-logo"]')
        assert section.xpath('.//div[@class="tile"]')
    assert all(section.xpath('.//div[@class="foot"]') for section in
               document.xpath('//section[@data-type!="separator"]'))


def test_numeric_columns_align_headers_and_blanks_across_all_pages():
    # Classification uses the entire source table, including a last-page value
    # and a last-page text cell; blank pages keep the column's alignment.
    rows = [[f'Bina {i}', None, '12.500,23', 0, '75,6', '12', ''] for i in range(23)]
    rows[-1][1] = Decimal('12500.23')
    rows[-1][5] = 'Kontrol gerekli'
    rows[0][2] = '—'
    rows[0][4] = ''
    slide = dict(type='table', title='Test', source='Rapor',
        headers=['Adı', 'Alan (m²)', 'Tutar', 'Adet', 'Oran', 'Karma', 'Boş'], rows=rows)
    document = html.fromstring(render_deck([slide], title='Test', code='TASLAK'))
    for table in document.xpath('//table'):
        assert [cell.get('class') == 'n' for cell in table.xpath('./thead/tr/th')] == [False, True, True, True, True, False, False]
        for row in table.xpath('./tbody/tr'):
            assert [cell.get('class') == 'n' for cell in row] == [False, True, True, True, True, False, False]
    assert document.xpath('//td[@class="n" and text()="—"]')


@pytest.mark.parametrize('variant', ['horizontal', 'stacked'])
def test_horizontal_chart_descending_order_preserves_labels_and_values(variant):
    slide = dict(type='chart', title='Test', variant=variant,
        categories=['Küçük', 'Büyük', 'Boş', 'Orta'],
        series=[dict(name='Adet', values=[3, 15, None, 8])])
    before = deepcopy(slide)
    prepared = prepare_slides([slide])[0]
    assert prepared['categories'] == ['Büyük', 'Orta', 'Küçük', 'Boş']
    assert prepared['series'][0]['values'] == [15, 8, 3, None]
    assert prepared['series'][0]['display'] == ['15', '8', '3', '—']
    assert prepared['height'] == 256
    assert slide == before


@pytest.mark.parametrize('count, height', [(1, 240), (3, 240), (8, 512), (20, 640)])
def test_horizontal_chart_height_tracks_category_count(count, height):
    slide = dict(type='chart', title='Test', variant='horizontal', categories=list(range(count)),
        series=[dict(name='Adet', values=list(range(count)))])
    assert prepare_slides([slide])[0]['height'] == height


def test_recipe_all_types_formatting_and_no_manual_values(presentation_payload):
    original = deepcopy(presentation_payload)
    slides = activity_report(presentation_payload)
    assert {s['type'] for s in slides} == {'cover', 'map', 'separator', 'kpi', 'chart', 'table', 'bullets', 'quote', 'closing'}
    assert presentation_payload == original
    document = html.fromstring(render(presentation_payload))
    body = document.xpath('//div[@class="slides"]')[0].text_content()
    for value in ['132', '811,78', '613,71', '75,6', '12.500,23', '—']:
        assert value in body
    assert 'Altıncı görev' not in body
    figures = next(s['figures'] for s in slides if s.get('title') == 'Bütçe bir bakışta')
    assert figures[0]['value'] == Decimal('75.60')
    prepared = prepare_slides(slides)
    staff = next(s for s in prepared if s.get('title') == 'Ekibimiz')
    assert [f['decimals'] for f in staff['figures']] == [0, 0, 0, 0]
    budget = next(s for s in prepared if s.get('title') == 'Bütçe bir bakışta')
    assert [f['decimals'] for f in budget['figures']] == [2, 2, 2]
    assert next(s for s in prepared if s.get('title') == 'Ödenekten harcamaya')['unit'] == 'milyon TL'


@pytest.mark.parametrize('budget', [{}, {'rows': []}, {'rows': [{'final': None, 'actual': 0}]}])
def test_missing_budget_skipped_and_logged(presentation_payload, caplog, budget):
    presentation_payload['financial']['tables']['expenditure'] = budget
    with caplog.at_level(logging.INFO):
        slides = activity_report(presentation_payload)
    assert not any(s.get('section') == 't2' and s['type'] in {'chart', 'kpi'} for s in slides)
    assert not any(s.get('title') == 'Bütçe' for s in slides)
    assert 'Bu raporda eksiksiz bütçe bilgisi yok' in caplog.text
    assert 'bilgisi yok' not in html.fromstring(render(presentation_payload)).xpath('//div[@class="slides"]')[0].text_content()


def test_zero_budget_is_real_and_incomplete_personnel_never_summed(presentation_payload):
    presentation_payload['financial']['tables']['expenditure']['rows'] = [dict(final=0, actual=0)]
    presentation_payload['resources']['employment']['rows'][0]['count'] = None
    slides = prepare_slides(activity_report(presentation_payload))
    budget = next(s for s in slides if s.get('title') == 'Bütçe bir bakışta')
    assert [f['display'] for f in budget['figures']] == ['—', '0,00', '0,00']
    staff = next(s for s in slides if s.get('title') == 'Ekibimiz')
    assert all(f['label'] != 'Toplam personel' for f in staff['figures'])


def test_unverified_or_multiple_indicator_targets_have_no_invented_rate(presentation_payload):
    indicator = presentation_payload['core']['indicators'][0]
    indicator['targets'].append(dict(value='200', state='verified'))
    indicator['actual_state'] = 'needs_review'
    table = next(s for s in activity_report(presentation_payload) if s.get('title') == 'Gösterge gerçekleşmeleri')
    assert table['rows'][0] == ['Hizmet sayısı', '100; 200', '—', '—']


def test_offline_assets_size_escaping_and_verification(presentation_payload):
    presentation_payload['department'] = '</script><script>window.bad=true</script>'
    presentation_payload['resources']['employment']['rows'][0]['category'] = '</script><img src=https://invalid>'
    content = render(presentation_payload)
    assert len(content) <= MAX_BYTES
    document = html.fromstring(content)
    assert not document.xpath('//*[@src and not(starts-with(@src,"data:"))]')
    assert not document.xpath('//*[@href and not(starts-with(@href,"#"))]')
    assert not re.search(rb'(?:src|href)=["\']https?://', content)
    assert b'data:font/woff2;base64,' in content
    assert b'data:image/svg+xml;base64,' in content
    assert b'window.bad=true</script>' not in content
    assert b'reveal.js' in content and b'echarts' in content
    assert "connect-src 'none'" in document.xpath('//meta[@http-equiv="Content-Security-Policy"]/@content')[0]
    assert verification_code(presentation_payload, 'draft') == 'TASLAK'
    presentation_payload['frozen'] = True
    canonical = numeric_canonical(presentation_payload)
    expected = sha256(canonical.encode()).hexdigest()[:8].upper()
    assert verification_code(presentation_payload, canonical) == expected[:4] + '-' + expected[4:]


def test_limit_rejects_large_deck():
    with pytest.raises(DeckTooLarge):
        render_deck([dict(type='quote', title='Test', quotes=['a' * MAX_BYTES], source='Test')], title='Test', code='TASLAK')


@pytest.mark.parametrize('count', [1, 9])
def test_kpi_bounds(count):
    with pytest.raises(ValueError):
        prepare_slides([dict(type='kpi', figures=[dict(value=1, label='Test')] * count)])


def test_existing_recipe_fixture_bytes_match_legacy_pagination(presentation_payload, monkeypatch):
    from app.sunum import engine

    current = render(presentation_payload)
    monkeypatch.setattr(engine, 'line_pages', lambda items, maximum, estimate: engine.pages(items, maximum))
    assert render(presentation_payload) == current
