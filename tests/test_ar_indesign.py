"""CIV-179 / AR-13: InDesign Tagged Text in the 2025 Faaliyet Raporu book styles."""
import copy
import re
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


def test_column_widths_fit_book_frame_and_indicator_scale_trimmed():
    body = text(contract())
    widths = [float(w) for w in re.findall(r'<tColAttrWidth:([0-9.]+)>', body)]
    assert widths and all(w > 0 for w in widths)
    tables = re.findall(r'<TableStart:\d+,(\d+):[^>]*>>((?:<ColStart:<tColAttrWidth:[0-9.]+>>)+)', body)
    for cols, spec in tables:
        total = sum(float(w) for w in re.findall(r'([0-9.]+)>>', spec))
        assert abs(total - (222.52 if int(cols) <= 4 else 467.72)) < 0.05
    assert '12.500,230000' not in body and '12.500,23' in body


def test_hidden_unit_heading_prints_when_it_has_text():
    body = text(unit(contract()))
    assert '<ParaStyle:arabaslik stun 2>GENEL BİLGİLER\r\n<ParaStyle:Metin>Sentetik örnek: I- GENEL BİLGİLER' in body


def test_budget_tables_keep_identifying_number_columns():
    data = contract()
    table = next(t for t in data['tables'] if t['kind'] == 'budget' and any(c[0] == 'program_id' for c in t.get('columns', [])))
    row_id = table['id'] + ':row:test'
    table['row_ids'] = [row_id]
    data['rows'].append({'id': row_id, 'table_id': table['id'], 'values': {'program_id': 7, 'subprogram_id': 9,
        'department_id': 2, 'actual': {'display': '1.000,00', 'exact': '1000.00'}}})
    body = text(data)
    assert '>7<CellEnd:>' in body and '>9<CellEnd:>' in body
    labels = dict(table['columns'])
    assert f">{labels['program_id']}<CellEnd:>" in body and f">{labels['subprogram_id']}<CellEnd:>" in body


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

