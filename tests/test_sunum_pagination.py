"""CIV-186: content-aware pagination, without a database or browser measurement."""
from copy import deepcopy

import pytest
from lxml import html

from app.sunum import engine


@pytest.mark.parametrize('kind,limit', [('table', 10), ('scorecard', 6), ('bullets', 5)])
def test_wrapped_items_reduce_page_size_without_losing_text(kind, limit):
    long = 'Afet İşleri ve Risk Değerlendirme Müdürlüğü ' * 5
    slide = dict(type=kind, title='Test', source='Rapor', headers=['Müdürlük', 'Adet', 'Oran', 'Durum'],
                 rows=[[long, 1, 2, 3]] * 13 if kind == 'table' else [dict(name=long)] * 13,
                 bullets=[long] * 13)
    before = deepcopy(slide)
    prepared = engine.prepare_slides([slide])
    key = 'bullets' if kind == 'bullets' else 'rows'
    assert max(len(s[key]) for s in prepared) < limit
    assert sum(len(s[key]) for s in prepared) == 13
    assert slide == before
    if kind == 'table':
        assert all(s['headers'] == slide['headers'] for s in prepared)
        assert all(s['numeric_columns'] == [False, True, True, True] for s in prepared)
        assert [s['continuation'] for s in prepared] == [f'Tablo {i}/{len(prepared)}' for i in range(1, len(prepared)+1)]


def test_oversize_row_is_alone_and_all_text_is_in_html():
    long = 'Afet İşleri ve Risk Değerlendirme Müdürlüğü ' * 35
    slide = dict(type='table', title='Test', source='Rapor', headers=['Müdürlük', 'Adet'],
                 rows=[['Önce', 1], [long, 2], ['Sonra', 3]])
    prepared = engine.prepare_slides([slide])
    assert [len(s['rows']) for s in prepared] == [1, 1, 1]
    document = html.fromstring(engine.render_deck([slide], title='Test', code='TASLAK'))
    assert document.xpath('//tbody/tr/td')[2].text == long


@pytest.mark.parametrize('kind,limit', [('table', 10), ('scorecard', 6), ('bullets', 5)])
def test_short_decks_are_byte_identical_to_fixed_count_pagination(monkeypatch, kind, limit):
    slide = dict(type=kind, title='Test', source='Rapor', headers=['Adı', 'Adet'],
                 rows=[[f'Bina {i}', i] for i in range(23)] if kind == 'table' else
                      [dict(name=f'Birim {i}', measured_display='5', met_display='3', width=60,
                            percentage='%60', css='w', status='İzlenmeli', expandable=False) for i in range(23)],
                 summary=[], bullets=[f'Görev {i}' for i in range(23)])
    actual = engine.render_deck([slide], title='Test', code='TASLAK')
    # Independent old behaviour, exercising the full template including IDs/delays.
    monkeypatch.setattr(engine, 'line_pages', lambda items, maximum, estimate: engine.pages(items, maximum))
    assert engine.render_deck([slide], title='Test', code='TASLAK') == actual


@pytest.mark.parametrize('kind', ['scorecard', 'bullets'])
def test_single_oversize_item_keeps_neighbours_on_separate_pages(kind):
    long = 'Ayrıntı ' * 500
    slide = dict(type=kind, rows=[dict(name=n) for n in ['Önce', long, 'Sonra']],
                 bullets=['Önce', long, 'Sonra'])
    key = 'rows' if kind == 'scorecard' else 'bullets'
    groups = engine.prepare_slides([slide])
    assert [len(s[key]) for s in groups] == [1, 1, 1]
    assert (groups[1]['rows'][0]['name'] if kind == 'scorecard' else groups[1]['bullets'][0]) == long


@pytest.mark.parametrize('kind', ['table', 'scorecard', 'bullets'])
def test_empty_paginated_slide_stays_empty(kind):
    assert engine.prepare_slides([dict(type=kind, rows=[], bullets=[], headers=['Adı'])]) == []
