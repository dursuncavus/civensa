"""CIV-165: approved 2026 book beside protected 2027 PP, local PostgreSQL only."""
from copy import deepcopy
from decimal import Decimal
import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import first_load_service
from app.data_importer import _label_key, parse_performance_docx
from app.models import (Activity, ActivityCatalogueLink, ActivityCostValue, ActivityResponsibility,
                        Department, DepartmentScope, Indicator,
                        IndicatorValue, OfficialActivity, ReportingPeriod)
from app.structure_service import period_name
from scripts import first_load_live as live
from scripts.book_to_load_docx import (GUIDANCE_2026, extract_tables,
                                      generate_docx, norm, prepare_2026_tables, table_type)
from scripts.first_load_dryrun import (NAME_MAP, indicator_match_report, inspect_import,
                                      local_test_url, parse_book, summary_2026)
from tests.first_load_checkpoint import disposable_first_load_database
from test_first_load_live import printed, target, state

BOOK_2026 = live.book_config(2026)[0]


@pytest.fixture(scope='module')
def approved2026():
    return live.verify_book(BOOK_2026, year=2026)


@pytest.fixture
def beside2027(target, printed):
    engine, ids = target
    names = set(json.loads(NAME_MAP.read_text())['map'].values()) | {'Yapı Kontrol Müdürlüğü'}
    with Session(engine) as db:
        db.add_all(Department(organization_id=ids['organization_id'], name=n) for n in sorted(names))
        db.commit()
    one = live.department_payload(printed, printed['departments'][0])
    assert not live.execute(engine, one, **ids, apply=True)['failed']
    return engine, ids


def test_approved_2026_structure_values_and_guidance(approved2026):
    parsed = approved2026
    assert parsed['summary']['source_years'] == [2026]
    assert parsed['summary']['department_count'] == 33
    assert parsed['summary']['indicator_table_count'] == 105
    assert parsed['summary']['indicator_count'] == 226
    assert not parsed['errors']
    assert len(parsed['dropped_guidance']) == 210
    assert len(parsed['catalogue_descriptions']) == 111
    originals = {t['id']: t for t in extract_tables(BOOK_2026) if table_type(t) == 'card'}
    for department in parsed['departments']:
        for block in department['blocks']:
            source = originals[parsed['source_tables'][str(block['table_number'])]['id']]
            expected = next(r[1] or '' for r in source['rows'] if norm(r[0]) in ('altprogramhedefi', 'altprogramınhedefi'))
            assert block['goal'] == expected
    assert all(len(d['economic_tables']) == 1 for d in parsed['departments'])
    assert all({(v['year'], v['kind']) for v in i['values']} == {
        (2025, 'planned'), (2025, 'year_end_estimate'), (2026, 'target'),
        (2027, 'forecast'), (2028, 'forecast')}
        for d in parsed['departments'] for b in d['blocks'] for i in b['indicators'])
    assert not any(text in json.dumps(parsed['departments'], ensure_ascii=False) for text in GUIDANCE_2026)
    # Economic tables on the same page are assigned by physical placement, not export IDs.
    sources = {d['name']: parsed['source_tables'][str(d['economic_tables'][0]['table_number'])]['page']
               for d in parsed['departments']}
    assert sources['Park ve Bahçeler Müdürlüğü'] == sources['İmar ve Şehircilik Müdürlüğü'] == '224'
    assert sources['Etüd Proje Müdürlüğü'] == '225'


@pytest.mark.parametrize('path', [live.BOOK, BOOK_2026.with_name('2026-performans-programi_14102026.idml')])
def test_wrong_book_refused_before_connection(path, monkeypatch, tmp_path):
    if not path.exists():
        path = tmp_path / '14-oct-variant.idml'
        path.write_bytes(b'unapproved 14 October variant')
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *a, **k: pytest.fail('must not connect'))
    with pytest.raises(ValueError, match='SHA256'):
        parse_book(path, year=2026)
    assert live.main(['--year', '2026', '--book', str(path), '--organization-id', '1', '--actor-id', '1']) == 1


def test_unknown_full_width_and_duplicate_headers_refused():
    extracted = extract_tables(BOOK_2026, reading_order=True)
    card = deepcopy(next(t for t in extracted if table_type(t) == 'card'))
    responsible = next(r[1] for r in card['rows'] if norm(r[0]) == 'sorumluidare')
    names = {norm(responsible): responsible}
    card['rows'].insert(1, ['Bilinmeyen yönerge', *(['→'] * 7)])
    with pytest.raises(ValueError, match='s.177.*Bilinmeyen yönerge'):
        prepare_2026_tables([card], names)
    card['rows'].pop(1)
    header = next(r for r in card['rows'] if norm(r[0]) == 'performansgöstergesi')
    header[5] = header[6]
    with pytest.raises(ValueError, match='başlık yıl/değer türü tekil değil'):
        prepare_2026_tables([card], names)


def test_2026_headers_can_move_without_moving_their_meaning(tmp_path):
    from docx import Document
    # Exercise the actual generated Word, then reorder independent year cells.
    word = tmp_path / 'generated.docx'
    generate_docx(BOOK_2026, NAME_MAP, word, year=2026)
    document = Document(word)
    table = document.tables[0]
    header = next(n for n, r in enumerate(table.rows) if _label_key(r.cells[0].text) == 'performansgostergesi')
    table.rows[header + 1].cells[3].text = '7'
    table.rows[header + 1].cells[5].text = '91'
    for row in list(table.rows)[header:]:
        # Only numeric indicator rows and the header have independent grid cells.
        if row.cells[3]._tc is row.cells[5]._tc:
            continue
        row.cells[3].text, row.cells[5].text = row.cells[5].text, row.cells[3].text
    document.save(word)
    parsed = parse_performance_docx(word.read_bytes())
    assert not parsed['errors']
    indicator = parsed['departments'][0]['blocks'][0]['indicators'][0]
    values = {(v['year'], v['kind']): v['raw_text'] for v in indicator['values']}
    assert values[(2025, 'planned')] == '7'
    assert values[(2026, 'target')] == '91'
    assert indicator['values'][0]['year'] == 2026


@pytest.mark.postgres
def test_full_2026_rehearsal_beside_full_2027_and_candidate_report(approved2026, tmp_path):
    with disposable_first_load_database(local_test_url()) as engine, Session(engine, expire_on_commit=False) as db:
        inspection = inspect_import(db, deepcopy(approved2026), BOOK_2026.name, year=2026)
        summary = summary_2026(approved2026, inspection)
        assert summary['refusals'] == summary['amount_differences'] == 0
        assert (summary['cards'], summary['indicators']) == (105, 226)
        assert summary['protected_2027_unchanged']
        assert summary['persistent_indicator_links'] == 0
        period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2026))
        other = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
        for department in db.scalars(select(Department)):
            book_name = approved2026['book_department_names'].get(department.name)
            scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period.id,
                                                           DepartmentScope.department_id == department.id))
            if book_name:
                assert scope.display_name == (book_name if book_name != department.name else '')
                assert period_name(db, period.id, department) == book_name
            assert period_name(db, other.id, department) == department.name
        assert not db.scalar(select(Indicator.id).where(Indicator.persistent_indicator_id.is_not(None)))
        reports = indicator_match_report(approved2026, inspection['baseline_parsed'], tmp_path / 'matches.md')
        assert len(reports) == 226
        assert any(r['candidates'] for r in reports)
        assert any(not r['candidates'] for r in reports)
        assert json.loads((tmp_path / 'matches.json').read_text()) == reports
        # All description tuples, including descriptions, survive in catalogue audit provenance.
        descriptions = {(s['program'], s['subprogram'], s['name'], s['explanation'])
                        for s in approved2026['catalogue_descriptions']}
        assert summary['catalogue_entries'] == len(descriptions)
        assert summary['catalogue_links'] + summary['unlinked_catalogue_activities'] == summary['activities']
        # The amount audit must check later same-name activities independently.
        damaged = deepcopy(inspection)
        result = next(r for r in damaged['results'] if r['name'] == 'Etüd Proje Müdürlüğü')
        seen = set()
        for activity in result['stored']['activities']:
            if activity['name'] in seen and activity['costs']:
                value = activity['costs'][0]
                value['amount'] = str(Decimal(value['amount'] or '0') + 1)
                break
            seen.add(activity['name'])
        else:
            pytest.fail('Expected repeated cost activity name in approved 2026 source')
        assert summary_2026(approved2026, damaged)['amount_differences'] == 1


@pytest.mark.postgres
@pytest.mark.parametrize('change', ['indicator', 'historical_value', 'scope', 'activity_cost', 'catalogue'])
def test_2027_hash_covers_owned_rows_and_rolls_back_whole_run(beside2027, approved2026, monkeypatch, change):
    engine, ids = beside2027
    before = state(engine)[0]
    with Session(engine) as db:
        baseline_hash = first_load_service.period_rows_hash(db)
    real_apply = first_load_service._apply_first_load_batch
    def change_2027(db, batch, actor):
        result = real_apply(db, batch, actor)
        # Inject at the LAST directorate: all earlier 2026 savepoints must roll back too.
        source = json.loads(batch.payload_json)['departments'][0]['name']
        if source != approved2026['departments'][-1]['name']:
            return result
        period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
        if change == 'indicator':
            row = db.scalar(select(Indicator).where(Indicator.period_id == period.id)); row.name = 'Yanlış değişiklik'
        elif change == 'historical_value':
            row = db.scalar(select(IndicatorValue).join(Indicator).where(Indicator.period_id == period.id,
                                                                       IndicatorValue.year == 2026)); row.value = 98765
        elif change == 'scope':
            did = db.scalar(select(Indicator.department_id).where(Indicator.period_id == period.id))
            db.add(DepartmentScope(period_id=period.id, department_id=did, display_name='Yanlış ad'))
        elif change == 'activity_cost':
            row = db.scalar(select(ActivityCostValue).join(Activity).where(Activity.period_id == period.id)); row.amount = 98765
        else:
            row = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == period.id)); row.name = 'Yanlış katalog'
        db.flush()
        return result
    monkeypatch.setattr(first_load_service, '_apply_first_load_batch', change_2027)
    result = live.execute(engine, deepcopy(approved2026), **ids, apply=True, year=2026)
    assert result['failed'] and '2027 satırları değişecekti' in result['failed'][0]['reason']
    assert all(v == 0 for v in result['counts'].values())
    assert state(engine)[0] == before
    with Session(engine) as db:
        assert first_load_service.period_rows_hash(db) == baseline_hash
        assert not db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2026))


@pytest.mark.postgres
def test_2026_plan_repeat_and_resume_keep_corrections(beside2027, approved2026):
    engine, ids = beside2027
    before = state(engine)
    plan = live.execute(engine, deepcopy(approved2026), **ids, year=2026)
    assert not plan['skipped'] and not plan['failed']
    assert state(engine) == before
    result = live.execute(engine, deepcopy(approved2026), **ids, apply=True, year=2026)
    assert result['counts']['indicators'] == 226 and not result['failed']
    with pytest.raises(live.Refusal, match='2026 PP verisi zaten var'):
        live.execute(engine, approved2026, **ids, apply=True, year=2026)
    with Session(engine) as db:
        period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2026))
        indicator = db.scalar(select(Indicator).where(Indicator.period_id == period.id))
        indicator.explanation = 'Strateji tarafından sonradan kaydedilen düzeltme'
        indicator_id, explanation = indicator.id, indicator.explanation
        db.commit()
    before = state(engine)
    resumed = live.execute(engine, approved2026, **ids, apply=True, resume=True, year=2026)
    assert resumed['counts']['indicators'] == 0
    assert len(resumed['skipped']) == 33
    assert state(engine) == before
    with Session(engine) as db:
        assert db.scalar(select(Indicator.explanation).where(Indicator.id == indicator_id)) == explanation


@pytest.mark.postgres
def test_unmapped_2026_department_refuses_all_before_writes(beside2027, approved2026):
    engine, ids = beside2027
    parsed = deepcopy(approved2026)
    parsed['departments'][-1]['name'] = 'Eşlenmemiş Müdürlük'
    before = state(engine)
    with pytest.raises(live.Refusal, match='Eşlenmemiş Müdürlük'):
        live.execute(engine, parsed, **ids, apply=True, year=2026)
    assert state(engine) == before
