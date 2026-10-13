"""CIV-010: real 2027 source parity, coverage, and PostgreSQL persistence."""
import hashlib
import io
import json
from pathlib import Path

import pytest
from docx import Document
from sqlalchemy import func, select

from app.data_importer import parse_performance_docx
from app.import_service import apply_import_batch
from app.models import Activity, ImportBatch, Indicator
from test_word_import import import_client, import_context, word_document

pytestmark = pytest.mark.postgres
FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.fixture(scope='module')
def real_source():
    return (FIXTURES / 'pp2027_source_no_media.docx').read_bytes()


@pytest.fixture(scope='module')
def real_parsed(real_source):
    return parse_performance_docx(real_source)


def test_real_source_matches_960d62c_baseline(real_source, real_parsed):
    baseline = json.loads((FIXTURES / 'pp2027_baseline.json').read_text())
    assert hashlib.sha256(real_source).hexdigest() == baseline['fixture_sha256']
    summary = dict(real_parsed['summary'])
    # CIV-005 deliberately includes the one nested table, unlike 960d62c.
    assert summary.pop('table_count') == baseline['summary']['table_count'] + 1 == 162
    assert summary == {k: v for k, v in baseline['summary'].items() if k != 'table_count'}
    assert real_parsed['errors'] == real_parsed['warnings'] == []
    actual = [dict(name=d['name'], blocks=len(d['blocks']),
                   indicators=sum(len(b['indicators']) for b in d['blocks']),
                   activities=len(d['activities']), personnel_rows=len(d['personnel']),
                   budget_years=sorted({b['budget_year'] for b in d['blocks']}))
              for d in real_parsed['departments']]
    assert actual == baseline['departments']
    coverage = real_parsed['coverage_items']
    assert len(coverage) == 65
    assert [item['table_number'] for item in coverage[:28]] == list(range(1, 29))
    assert all(f"Tablo {item['table_number']}: {item['first_cell_text']}" in item['message']
               for item in coverage)


def test_real_source_preview_is_applicable(import_client, import_context, real_source, real_parsed):
    response = import_client.post(
        f'/api/periods/{import_context.period.id}/data-import-preview',
        files={'file': ('pp2027.docx', real_source)})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['summary']['unresolved_department_count'] == 0
    assert result['can_apply'] is True
    assert result['errors'] == []
    assert result['coverage_items'] == real_parsed['coverage_items']
    assert not any('Tablo ' in warning for warning in result['warnings'])
    detail = import_client.get(f"/api/import-batches/{result['batch_id']}").json()
    assert detail['can_apply'] is True
    assert detail['coverage_items'] == result['coverage_items']
    assert detail['errors'] == []


def test_real_source_apply_persists_all_records(db, import_context, real_parsed):
    assert db.bind.dialect.name == 'postgresql'
    assert db.scalar(select(func.count()).select_from(Indicator)) == 0
    assert db.scalar(select(func.count()).select_from(Activity)) == 0
    batch = ImportBatch(period_id=import_context.period.id, filename='pp2027.docx',
                        status='preview', payload_json=json.dumps(real_parsed),
                        created_by=import_context.user.id)
    db.add(batch)
    db.commit()
    result = apply_import_batch(db, batch)
    db.commit()
    assert result['indicators'] == real_parsed['summary']['indicator_count'] == 324
    assert result['activities'] == real_parsed['summary']['activity_count'] == 288
    assert db.scalar(select(func.count()).select_from(Indicator)) == 324
    assert db.scalar(select(func.count()).select_from(Activity)) == 288
    assert batch.status == 'applied'


@pytest.mark.parametrize('year,valid', [('2027/1', True), ('2027 / 2027', True),
                                       ('', False), ('2027/2028', False)])
def test_budget_year_extracts_one_distinct_year(year, valid):
    parsed = parse_performance_docx(word_document(year=year))
    assert bool(parsed['errors']) is not valid
    if valid:
        assert parsed['summary']['source_years'] == [2027]
    else:
        assert any('Tablo 1' in error and 'Bütçe Yılı' in error for error in parsed['errors'])


def test_punctuated_labels_and_section_title_before_plural_header():
    doc = Document(io.BytesIO(word_document(variant='plural')))
    table = doc.tables[0]
    table.cell(0, 0).text = 'BÜTÇE / YILI :'
    table.cell(1, 0).text = 'PROGRAM-ADI.'
    table.cell(2, 0).text = 'İdare/Birim   Adı:'
    title = table.add_row()
    title.cells[0].merge(title.cells[-1]).text = 'PERFORMANS GÖSTERGELERİ'
    table.rows[6]._tr.addprevious(title._tr)
    stream = io.BytesIO()
    doc.save(stream)
    parsed = parse_performance_docx(stream.getvalue())
    assert parsed['errors'] == []
    assert parsed['summary']['indicator_count'] == 1
    assert parsed['departments'][0]['blocks'][0]['program'] == 'Çevre Programı'


@pytest.mark.parametrize('label', ['Bütçe Yılı:', 'Program Adı', 'Performans Göstergesi', 'Faaliyetler'])
def test_malformed_data_table_remains_blocking(label):
    doc = Document(io.BytesIO(word_document()))
    doc.add_table(rows=1, cols=1).cell(0, 0).text = label
    stream = io.BytesIO()
    doc.save(stream)
    parsed = parse_performance_docx(stream.getvalue())
    assert len(parsed['errors']) == 1
    assert 'Tablo 3' in parsed['errors'][0]
    assert parsed['coverage_items'] == []
