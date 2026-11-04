"""CIV-179 / AR-13: InDesign Tagged Text in the 2025 Faaliyet Raporu book styles."""
import copy
import json
from pathlib import Path

import pytest

from app.ar_indesign import STYLE, escape, tagged_text, tr_upper
from test_activity_sections import section_client, login  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / 'artifacts' / 'civ086' / 'release-1.typeset.json'
ARTIFACTS = ROOT / 'artifacts' / 'civ179'


def contract():
    return json.loads(SAMPLE.read_text(encoding='utf-8'))


def text(data):
    raw = tagged_text(data)
    assert raw[:2] == b'\xff\xfe'
    return raw.decode('utf-16')


def unit(data):
    data = copy.deepcopy(data)
    data['document'].update(scope='birim', department='Sağlık İşleri Müdürlüğü', department_id=2)
    return data


def test_header_styles_and_determinism():
    data = contract()
    body = text(data)
    assert body.startswith('<UNICODE-WIN>\r\n<Version:19><FeatureSet:InDesign-Roman>')
    assert tagged_text(data) == tagged_text(copy.deepcopy(data))
    for style in ('chapter', 'heading', 'subheading', 'body', 'caption', 'head_cell', 'body_cell'):
        assert f'<ParaStyle:{STYLE[style]}>' in body or f'<CellStyle:{STYLE[style]}>' in body
    assert f'<TableStyle:{STYLE["table"]}>' in body
    assert body.count('<TableStart:') == body.count('<TableEnd:>')
    assert '<ParaStyle:TABLO>Tablo 1: ' in body


def test_unit_chapter_uses_book_headings_and_turkish_uppercase():
    body = text(unit(contract()))
    assert '<ParaStyle:BOLUM BASLİK>SAĞLIK İŞLERİ MÜDÜRLÜĞÜ\r\n' in body
    assert '<ParaStyle:arabaslik stun 2>Yetki, Görev ve Sorumluluklar\r\n' in body
    assert '<ParaStyle:arabaslik stun 2>Müdürlüğe İlişkin Bilgiler\r\n' in body
    assert '<ParaStyle:BOLUM BASLİK>GENEL BİLGİLER' not in body
    assert tr_upper('istihdam ışık') == 'İSTİHDAM IŞIK'


def test_escaping_line_breaks_bullets_and_draft_marker():
    data = contract()
    data['frozen'] = False
    section = next(s for s in data['sections'] if s['code'] == 'I.B')
    section['blocks'] = [{'type': 'paragraph', 'text': 'a <b> \\ c\nd'}, {'type': 'bullets', 'items': ['madde', ' ']}]
    body = text(data)
    assert 'TASLAK — bu metin onaylı rapor sürümü değildir.' in body
    assert 'a \\<b\\> \\\\ c<0x000A>d' in body
    assert '<ParaStyle:Metin>• madde\r\n' in body and body.count('• ') == 1
    assert escape(None) == ''


def test_empty_and_not_applicable_sections_print_no_heading():
    data = contract()
    for section in data['sections']:
        if section['code'] in {'I.D', 'V'}:
            section['values']['status'] = 'not_applicable' if section['code'] == 'V' else 'empty'
    body = text(data)
    assert 'Diğer Hususlar\r\n<ParaStyle:Metin>Sentetik örnek: D-' not in body
    assert '>ÖNERİ VE TEDBİRLER' not in body


def test_indicator_blank_actual_is_not_zero():
    data = contract()
    indicator = data['indicators'][0]['values']
    year = data['document']['year']
    indicator['targets'] = [{'year': year, 'state': 'verified', 'value': {'display': '10', 'exact': '10'}}]
    indicator['actual'] = {'exact': None, 'display': '—'}
    body = text(data)
    assert 'Kayıt yok' in body and f'{year} Hedef' in body
    indicator['actual'] = {'exact': '0', 'display': '0'}
    assert 'Kayıt yok' not in text(data)


def test_single_row_free_table_is_kept():
    data = contract()
    table = next(t for t in data['tables'] if t['kind'] == 'section')
    table['row_ids'] = table['row_ids'][:1]
    body = text(data)
    assert '<TableStart:1,2:1:0' in body and '>Hizmet<CellEnd:>' in body


def test_numbers_right_aligned_and_total_row_style():
    data = contract()
    table = next(t for t in data['tables'] if t['kind'] == 'section')
    body = text(data)
    assert '<ParaStyle:tablo yazı><pTextAlignment:Right>5<CellEnd:>' in body
    assert '<ParaStyle:tablo yazı>Örnek hizmet<CellEnd:>' in body
    assert '<CellStyle:tablo sonuç><StylePriority:1><CellStart:1,1><ParaStyle:tablo sonuç>Toplam<CellEnd:>' in body
    assert table['title']


def test_unknown_schema_refused():
    data = contract()
    data['schema_version'] = 'ar-typeset/2'
    with pytest.raises(ValueError):
        tagged_text(data)


def test_checked_in_samples_match_code():
    data = contract()
    assert (ARTIFACTS / 'idare-ornek-indesign.txt').read_bytes() == tagged_text(data)
    assert (ARTIFACTS / 'birim-ornek-indesign.txt').read_bytes() == tagged_text(unit(data))


@pytest.mark.postgres
@pytest.mark.parametrize('email,scope,expected', [
    ('test@example.invalid', 'own', 200), ('test@example.invalid', 'other', 403), ('test@example.invalid', 'idare', 403),
    ('strategy@example.invalid', 'own', 200), ('strategy@example.invalid', 'idare', 200)])
def test_download_matches_typeset_contract_and_access(section_client, sample, email, scope, expected):
    client, docs, other, _ = section_client
    login(client, email)
    doc = docs['idare' if scope == 'idare' else 'birim:' + str(other.id if scope == 'other' else sample['department'].id)]
    response = client.get(f'/activity-sections/reports/{doc.id}/indesign.txt')
    assert response.status_code == expected
    if expected == 200:
        source = client.get(f'/activity-sections/reports/{doc.id}/typeset.json').json()
        assert response.content == tagged_text(source)
        assert response.headers['cache-control'] == 'private, no-store'
        assert 'indesign.txt' in response.headers['content-disposition']
        assert 'InDesign metni' in client.get(f'/activity-sections/reports/{doc.id}').text

