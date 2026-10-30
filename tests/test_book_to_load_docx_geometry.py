"""Printed-story selection must be shared by loading and institution checks."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from scripts.book_to_load_docx import extract_tables, generate_docx
from scripts.first_load_dryrun import parse_book, report


def geometry_book(path):
    design = ET.Element('Document')
    spread = ET.Element('Spread')
    # Local page coordinates need translation into the spread.
    ET.SubElement(spread, 'Page', Name='38', GeometricBounds='0 0 100 100',
                  ItemTransform='1 0 0 1 -100 -50')
    ET.SubElement(spread, 'Page', Name='39', GeometricBounds='0 0 100 100',
                  ItemTransform='1 0 0 1 0 -50')

    def frame(parent, sid, transform):
        node = ET.SubElement(parent, 'TextFrame', ParentStory=sid, ItemTransform=transform)
        points = ET.SubElement(ET.SubElement(node, 'Properties'), 'PathPointArray')
        for anchor in ('0 0', '20 0', '20 20', '0 20'):
            ET.SubElement(points, 'PathPointType', Anchor=anchor)
        return node

    frame(spread, 'on', '1 0 0 1 -80 -30')
    frame(spread, 'off', '1 0 0 1 200 0')
    frame(spread, 'partial', '1 0 0 1 95 40')
    frame(spread, 'thread', '1 0 0 1 200 0').set('NextTextFrame', 'next')
    frame(spread, 'thread', '1 0 0 1 20 0').set('Self', 'next')
    # Group and rotation transforms also participate in spread geometry.
    group = ET.SubElement(spread, 'Group', ItemTransform='1 0 0 1 -90 0')
    frame(group, 'group', '0 1 -1 0 20 0')
    files = {'Spreads/one.xml': ET.tostring(spread)}
    ET.SubElement(design, 'Spread', src='Spreads/one.xml')
    for sid in ('on', 'off', 'partial', 'thread', 'anchored', 'nested', 'off_anchor', 'group', 'unplaced'):
        story = ET.Element('Story', Self=sid)
        if sid in ('on', 'anchored', 'off'):
            frame(story, {'on': 'anchored', 'anchored': 'nested', 'off': 'off_anchor'}[sid],
                  '1 0 0 1 900 900')
        table = ET.SubElement(story, 'Table', Self='table_' + sid, ColumnCount='2', BodyRowCount='2')
        for row, values in enumerate((('Müdürlük Adı', 'Oran'), (sid, '0,00'))):
            for column, value in enumerate(values):
                ET.SubElement(ET.SubElement(table, 'Cell', Name=f'{column}:{row}'), 'Content').text = value
        root = ET.Element('Package')
        root.append(story)
        filename = f'Stories/{sid}.xml'
        files[filename] = ET.tostring(root)
        ET.SubElement(design, 'Story', src=filename)
    files['designmap.xml'] = ET.tostring(design)
    with ZipFile(path, 'w') as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def test_printed_frames_threading_anchors_and_exclusion_evidence(tmp_path):
    path = tmp_path / 'geometry.idml'
    geometry_book(path)
    excluded = []
    tables = extract_tables(path, excluded=excluded)
    assert {t['story'] for t in tables} == {'on', 'partial', 'thread', 'anchored', 'nested', 'group'}
    assert {t['story']: t['page'] for t in tables} == {
        'on': '38', 'partial': '39', 'thread': '39', 'anchored': '38', 'nested': '38', 'group': '38'}
    off = next(t for t in excluded if t['story'] == 'off')
    assert off['spread_pages'] == ['38', '39']
    assert off['rows'][0] == ['Müdürlük Adı', 'Oran']
    mapping = tmp_path / 'map.json'
    mapping.write_text(json.dumps({'map': {}}))
    parsed, conversion = parse_book(path, name_map=mapping)
    assert {t['story'] for t in parsed['institution_tables']} == {t['story'] for t in tables}
    inspection = dict(results=[], errors=[], plan={'conflicts': []}, unresolved=[], pending=[],
                      applied=None, conversion=conversion)
    content = report(parsed, inspection, path, 'test')
    assert 'Basılmayan (pasteboard) tablolar — yüklenmedi' in content
    assert '| off | 38–39 | table_off | Müdürlük Adı / Oran |' in content
    assert 'off_anchor' in content and 'unplaced' in content


def test_approved_source_excludes_exactly_seven_pasteboard_tables():
    path = Path(__file__).parent / 'fixtures/first_load/source/2027-performans-programi_ONAYLI.idml'
    excluded = []
    tables = extract_tables(path, excluded=excluded)
    assert len(tables) == 229
    pasteboard = [t for t in excluded if t['reason'] == 'pasteboard']
    assert len(excluded) == 11  # Four legacy unplaced tables plus seven pasteboard tables.
    assert {t['story'] for t in pasteboard} == {
        'u174d', 'u2a14', 'u409e', 'u40b4', 'u40ca', 'u40e0', 'u40f6'}
    assert len(pasteboard) == 7
    assert next(t for t in excluded if t['story'] == 'u40f6')['spread_pages'] == ['244', '245']


def test_word_generator_also_omits_pasteboard_cost_table(tmp_path):
    path = tmp_path / 'geometry.idml'
    geometry_book(path)
    with ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    for sid in ('on', 'off'):
        name = f'Stories/{sid}.xml'
        root = ET.fromstring(files[name])
        root.find('.//Table/Cell/Content').text = 'Faaliyetler'
        files[name] = ET.tostring(root)
    with ZipFile(path, 'w') as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    mapping = tmp_path / 'map.json'
    mapping.write_text(json.dumps({'map': {}}))
    conversion = generate_docx(path, mapping, tmp_path / 'load.docx')
    assert conversion['counts'] == {'cost': 1}
    assert [t['id'] for t in conversion['tables']] == ['table_on']
    assert next(t for t in conversion['non_printed'] if t['id'] == 'table_off')['reason'] == 'pasteboard'
