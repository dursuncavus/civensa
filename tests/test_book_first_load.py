"""CIV-042: IDML -> Word -> real import -> audited first-load catalogue."""
from copy import deepcopy
import json
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from fastapi import HTTPException
import pytest
from sqlalchemy import func, select

from app.data_importer import parse_performance_docx
from app.first_load_service import load_first_load_catalogue
from app.import_service import apply_import_batch, _source_activity_linkable
from app.models import (Activity, ActivityCatalogueLink, ActivityResponsibility, AuditLog,
                        Department, ImportBatch, OfficialActivity, ReportCard, SubProgram)
from app.program_service import save_activity_catalogue_links, save_catalogue_entry
from scripts.book_to_load_docx import extract_tables, generate_docx
from test_word_import import import_context

pytestmark = pytest.mark.postgres


def card_rows(subprogram):
    rows = [[label, value, *(['→'] * 7)] for label, value in [
        ('BÜTÇE YILI', '2027/1'), ('PROGRAM ADI', 'Çevre'),
        ('İDARE/BİRİM ADI', 'PARK BAHÇELER'), ('ALT PROGRAM ADI', subprogram),
        ('GEREKÇE ve AÇIKLAMALAR', 'Yeşil alan ihtiyacı'), ('ALT PROGRAMIN HEDEFİ', 'Parkları artırmak')]]
    rows += [['Performans Göstergesi', '→', 'Ölçü Birimi', '2025 Gerçekleşme', '2026 Planlanan',
              '2026 Yıl Sonu Tahmin', '2027 Hedef', '2028 Tahmin', '2029 Tahmin'],
             ['Park sayısı', '→', 'Adet', '1', '1', '1', '2', '3', '4']]
    rows += [[label, value, *(['→'] * 7)] for label, value in [
        ('Göstergeye İlişkin Açıklama', 'Parklar'), ('Hesaplama Yöntemi', 'Sayım'),
        ('Verinin Kaynağı', 'Kayıt'), ('Sorumlu İdare', 'PARK BAHÇELER')]]
    return rows


def synthetic_idml(path):
    costs = [['Faaliyetler', '2027 Bütçe', '2028 Tahmin', '2029 Tahmin']]
    for name in ['0001.Park yapımı', '0002.Ağaç dikimi']:
        costs.extend([[name, '100,00', '0,00', ''], ['Bütçe İçi', '100,00', '0,00', ''],
                      ['Bütçe Dışı', '0,00', '0,00', '']])
    costs += [['Personel ve SGK Giderleri', '0', '0', '0']]
    tables = [(1, card_rows('Parklar')), (1, [
        ['Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri', '→'],
        ['Faaliyetler', '2027 Bütçe'], ['0001.Park yapımının artırılması', '100,00']]),
        (2, card_rows('Ağaçlar')), (2, [
        ['Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri', '→'],
        ['Faaliyetler', '2027 Bütçe'], ['0002.Ağaç dikimi', '100,00']]), (3, costs)]
    design = ET.Element('Document')
    with ZipFile(path, 'w') as archive:
        for page, (number, rows) in enumerate(tables, 1):
            story_id = f'story{page}'
            entry = ET.SubElement(design, 'Story', src=f'Stories/{page}.xml')
            root = ET.Element('Package')
            story = ET.SubElement(root, 'Story', Self=story_id)
            table = ET.SubElement(story, 'Table', Self=f'table{page}', ColumnCount=str(len(rows[0])), BodyRowCount=str(len(rows)))
            for ri, row in enumerate(rows):
                for col, value in enumerate(row):
                    if value == '→':
                        continue
                    span = 1
                    while col + span < len(row) and row[col + span] == '→':
                        span += 1
                    cell = ET.SubElement(table, 'Cell', Name=f'{col}:{ri}', ColumnSpan=str(span))
                    ET.SubElement(cell, 'Content').text = value
            archive.writestr(entry.attrib['src'], ET.tostring(root))
            entry = ET.SubElement(design, 'Spread', src=f'Spreads/{page}.xml')
            root = ET.Element('Package')
            spread = ET.SubElement(root, 'Spread')
            ET.SubElement(spread, 'Page', Name=str(number))
            ET.SubElement(spread, 'TextFrame', ParentStory=story_id)
            archive.writestr(entry.attrib['src'], ET.tostring(root))
        archive.writestr('designmap.xml', ET.tostring(design))


@pytest.fixture
def book(tmp_path):
    idml = tmp_path / 'book.idml'
    synthetic_idml(idml)
    mapping = tmp_path / 'map.json'
    mapping.write_text(json.dumps({'map': {'PARK BAHÇELER': 'Park Bahçeler Müdürlüğü'}}))
    word = tmp_path / 'load.docx'
    conversion = generate_docx(idml, mapping, word)
    return parse_performance_docx(word.read_bytes()), conversion, word


def import_book(db, context, parsed):
    batch = ImportBatch(period_id=context.period.id, filename='generated.docx', status='preview',
                        payload_json=json.dumps(parsed), created_by=context.user.id)
    db.add(batch)
    db.commit()
    result = apply_import_batch(db, batch)
    db.flush()
    return result


def test_generator_retains_membership_units_blanks_and_provenance(book):
    parsed, conversion, _ = book
    assert not conversion['unmapped']
    assert conversion['counts'] == dict(card=2, membership=2, cost=1)
    assert not parsed['errors']
    assert parsed['summary']['activity_count'] == 2  # Membership amounts are not duplicated costs.
    department = parsed['departments'][0]
    assert _source_activity_linkable(department)
    assert department['blocks'][0]['indicators'][0]['unit'] == 'Adet'
    assert department['activities'][0]['source_memberships'][0]['block_table_number'] == 1
    blank = next(v for v in department['activities'][0]['costs'] if v['year'] == 2029)
    assert blank['amount'] is None and blank['raw_text'] == ''
    assert parsed['source_tables']['1']['page'] == '1'


def test_xml_spans_breaks_unplaced_stories_and_unmapped_names_are_reported(tmp_path):
    path = tmp_path / 'book.idml'
    synthetic_idml(path)
    with ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files['Stories/1.xml'])
    table = ET.SubElement(root[0], 'Table', Self='span-test', ColumnCount='2', BodyRowCount='2')
    cell = ET.SubElement(table, 'Cell', Name='0:0', RowSpan='2')
    ET.SubElement(cell, 'Content').text = 'A'
    ET.SubElement(cell, 'Br')
    ET.SubElement(cell, 'Content').text = 'B'
    ET.SubElement(ET.SubElement(table, 'Cell', Name='1:0'), 'Content').text = 'C'
    ET.SubElement(ET.SubElement(table, 'Cell', Name='1:1'), 'Content').text = 'D'
    files['Stories/1.xml'] = ET.tostring(root)
    unplaced = ET.fromstring(files['Stories/3.xml'])
    unplaced[0].set('Self', 'unplaced')
    files['Stories/unplaced.xml'] = ET.tostring(unplaced)
    design = ET.fromstring(files['designmap.xml'])
    ET.SubElement(design, 'Story', src='Stories/unplaced.xml')
    files['designmap.xml'] = ET.tostring(design)
    with ZipFile(path, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    extracted = extract_tables(path)
    assert next(t['rows'] for t in extracted if t['id'] == 'span-test') == [['A B', 'C'], ['↓', 'D']]
    mapping = tmp_path / 'map.json'
    mapping.write_text('{"map": {}}')
    output = tmp_path / 'load.docx'
    conversion = generate_docx(path, mapping, output)
    assert conversion['unmapped'] == ['PARK BAHÇELER']
    assert conversion['unplaced'] == [{'id': 'table3', 'type': 'card'}]
    assert json.loads((tmp_path / 'load.docx.report.json').read_text()) == conversion


def test_import_links_each_activity_to_its_explicit_card(db, import_context, book):
    parsed, _, _ = book
    result = import_book(db, import_context, parsed)
    assert result['unlinked_activities'] == 0
    activities = db.scalars(select(Activity).order_by(Activity.name)).all()
    assert [db.get(SubProgram, a.subprogram_id).name for a in activities] == ['Parklar', 'Ağaçlar']
    assert all(db.get(ReportCard, a.card_id).subprogram_id == a.subprogram_id for a in activities)


def test_shared_catalogue_is_idempotent_and_audited(db, import_context, book):
    parsed = deepcopy(book[0])
    shared = deepcopy(parsed['departments'][0])
    shared['name'] = 'Diğer Müdürlük'
    parsed['departments'].append(shared)
    db.add(Department(organization_id=import_context.org.id, name=shared['name']))
    db.commit()
    import_book(db, import_context, parsed)
    actor = import_context.user
    assert actor.role == 'strategy'
    first = load_first_load_catalogue(db, import_context.period.id, parsed, actor)
    db.commit()
    assert first == dict(entries=2, created_entries=2, responsibilities=4, links=4)
    audits = db.scalars(select(AuditLog).where(AuditLog.action.in_(['catalogue_create', 'catalogue_link']))).all()
    assert len(audits) == 6 and all(a.user_id == actor.id for a in audits)
    assert json.loads(audits[0].details)['source'][0]['page'] == '1'
    second = load_first_load_catalogue(db, import_context.period.id, parsed, actor)
    db.commit()
    assert second['created_entries'] == 0
    for model, count in [(OfficialActivity, 2), (ActivityResponsibility, 4), (ActivityCatalogueLink, 4)]:
        assert db.scalar(select(func.count()).select_from(model)) == count
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action.in_(
        ['catalogue_create', 'catalogue_link']))) == 6


def test_membership_never_falls_back_when_missing_or_ambiguous(db, import_context, book):
    parsed = deepcopy(book[0])
    activities = parsed['departments'][0]['activities']
    activities[0]['source_memberships'] = []
    activities[1]['source_memberships'].append({'block_table_number': 1})
    assert not _source_activity_linkable(parsed['departments'][0])
    result = import_book(db, import_context, parsed)
    assert result['unlinked_activities'] == 2
    assert all(a.card_id is None and a.subprogram_id is None for a in db.scalars(select(Activity)))


def test_orphan_membership_is_catalogued_without_inventing_costs(db, import_context, book):
    parsed = deepcopy(book[0])
    block = parsed['departments'][0]['blocks'][0]
    block['activity_memberships'].append(dict(name='0006.Emekli ikramiyesi', table_number=2, row_number=4))
    import_book(db, import_context, parsed)
    result = load_first_load_catalogue(db, import_context.period.id, parsed, import_context.user)
    db.commit()
    assert (result['entries'], result['responsibilities'], result['links']) == (3, 3, 2)
    assert db.scalar(select(func.count()).select_from(Activity)) == 2


def test_catalogue_loader_rolls_back_writes_and_audit_together(db, import_context, book, monkeypatch):
    from app import first_load_service
    parsed = book[0]
    import_book(db, import_context, parsed)
    db.commit()

    def reject_links(*args, **kwargs):
        raise ValueError('Katalog bağlantısı reddedildi.')

    monkeypatch.setattr(first_load_service, 'save_activity_catalogue_links', reject_links)
    with pytest.raises(ValueError, match='reddedildi'):
        load_first_load_catalogue(db, import_context.period.id, parsed, import_context.user)
    db.commit()
    assert db.scalar(select(func.count()).select_from(OfficialActivity)) == 0
    assert db.scalar(select(func.count()).select_from(ActivityResponsibility)) == 0
    assert db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action.in_(['catalogue_create', 'catalogue_link']))) == 0


def test_catalogue_services_preserve_scope_guards(db, sample):
    official, activity, actor = sample['official'], sample['activity'], sample['strategy']
    values = {f: getattr(official, f) for f in ['program_code', 'program_name', 'subprogram_code', 'subprogram_name', 'code', 'name']}
    other = Department(organization_id=sample['department'].organization_id, name='Diğer Müdürlük')
    db.add(other)
    db.flush()
    with pytest.raises(HTTPException) as error:
        save_catalogue_entry(db, sample['period'].id, values, [other.id], actor, obj=official)
    assert error.value.status_code == 409
    db.delete(db.scalar(select(ActivityResponsibility)))
    db.flush()
    with pytest.raises(HTTPException) as error:
        save_activity_catalogue_links(db, activity, [official.id], actor)
    assert error.value.status_code == 422


def test_catalogue_link_route_uses_shared_service_with_audit(client, db, sample):
    activity = sample['activity']
    response = client.post(f'/program/{activity.department_id}/catalogue-link', data={
        'period_id': activity.period_id, 'activity_id': activity.id}, follow_redirects=False)
    assert response.status_code == 303
    assert db.scalar(select(func.count()).select_from(ActivityCatalogueLink)) == 0
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'catalogue_link'))
    assert audit.user_id == sample['user'].id
    assert json.loads(audit.details)['official_ids'] == []
