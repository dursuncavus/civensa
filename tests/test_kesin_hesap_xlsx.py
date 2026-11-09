"""CIV-194: all PDFs and amounts here are invented, never municipal data."""
import csv
import io
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from app import activity_financial_service as finance
from app.numbers import parse_number
from scripts import kesin_hesap_xlsx as converter

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/kesin_hesap_xlsx.py'
GIDER_HEADERS = [
    'Kurum Kodu', 'Fonksiyonel Kodu', 'Finansal Kodu', 'Ekonomik Kodu', 'Açıklama',
    'Geçen Yıldan Devreden Ödenek', 'Bütçe İle Verilen Ödenek',
    'Ek Ve Olağanüstü Verilen Ödenek', 'Aktarma Suretiyle Eklenen (+)',
    'Düşülen (-)', 'Net Ödenek Toplamı', 'Bütçe Gideri Toplamı',
    'Ödenen Bütçe Gideri', 'Ödenek Üstü Harcama', 'İptal Edilen Ödenek',
    'Gelecek Yıla Devrolan Ödenek',
]


def money(value):
    return f'{Decimal(value):,.2f}'.translate(str.maketrans(',.', '.,'))


def vector(scale=1):
    # initial=1120.25, added=15, deducted=5, final=1130.25; all synthetic.
    return [Decimal(n) * scale for n in
            ('20.25', '1100', '5', '10', '5', '1130.25', '1080.15', '1070.15', '0', '40.10', '10')]


def pdf_table(path, headers, widths, pages, *, centered=False, scale=1, year=2026,
              lead_layout=False, page_shift=0, dates=None, date_overrides=None, date_prefix=False):
    """Separate PDF text objects, proportional Turkish font and right-aligned money."""
    if 'Civ194Test' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Civ194Test', str(ROOT / 'app/fonts/DejaVuSans.ttf')))
    canvas = Canvas(str(path), pagesize=landscape(A3))
    for page_no, rows in enumerate(pages):
        canvas.saveState()
        canvas.scale(scale, scale)
        canvas.translate(page_shift if page_no else 0, 0)
        canvas.setFont('Civ194Test', 6)
        canvas.drawString(20, 825, 'BÜTÇE GİDER KESİN HESAP' if len(headers) == 16
                          else 'GELİR CETVELİ KESİN HESAP DÖKÜMÜ')
        metadata = {'start': f'01/01/{year}', 'end': f'31/12/{year}', 'period': str(year)}
        metadata.update(dates or {})
        metadata.update((date_overrides or {}).get(page_no, {}))
        if metadata['start'] is not None:
            canvas.drawRightString(1130, 810, 'Başlangıç Tarihi : ' + metadata['start'])
        if metadata['end'] is not None:
            canvas.drawRightString(1130, 800, 'Bitiş Tarihi : ' + metadata['end'])
        if len(headers) == 11 and metadata['period'] is not None:
            canvas.drawString(20, 800, 'Dönemi : ' + metadata['period'])
        if date_prefix:
            # Dotted title dates resemble code prefixes, but carry no amounts.
            canvas.drawString(20, 800, f'01.01.{year}')
        x = 20
        for label, width in zip(headers, widths):
            fragments = label.split('\n') if lead_layout else simpleSplit(label, 'Civ194Test', 6, width - 10)
            for n, line in enumerate(fragments):
                if centered:
                    canvas.drawCentredString(x + width / 2, 770 - n * 8, line)
                else:
                    canvas.drawString(x + 3, 770 - n * 8, line)
            x += width
        if len(headers) == 11 and not lead_layout:
            canvas.drawString(23, 738, 'I   II   III   IV   V')
        y = 710
        for row in rows:
            x = 20
            height = 1
            for index, (value, width) in enumerate(zip(row, widths)):
                lines = str(value).split('\n')
                height = max(height, len(lines))
                for n, line in enumerate(lines):
                    if index >= (5 if len(headers) == 16 else 2):
                        canvas.drawRightString(x + width - 5, y - n * 8, line)
                    else:
                        canvas.drawString(x + 3, y - n * 8, line)
                x += width
            y -= height * 8 + 8
        canvas.drawString(20, 20, 'Sayfa 1')
        canvas.restoreState()
        canvas.showPage()
    canvas.save()
    return path


def expense_pdf(tmp_path, *, mismatch=None, blank=False, duplicate=False, centered=False,
                scale=1, directorate_mismatch=False, fund_split=False, foreign_code=False,
                lead_layout=False, transfer='Suratiyle', page_shift=0, dotted_first=None,
                year=2026, dates=None, date_overrides=None, bad_header=None, date_prefix=False):
    def row(kurum='', function='', fund='', economic='', name='', amounts=None):
        values = list(map(money, vector() if amounts is None else amounts))
        return [kurum, function, fund, economic, name, *values]

    total = vector(4)
    if mismatch is not None and not directorate_mismatch:
        total[mismatch] += Decimal('0.01')
    first = [row('46', name='BELEDİYE', amounts=vector(4)),
             row('46 34', name='SENTETİK İL', amounts=vector(4)),
             row('46 34 14', name='SENTETİK BELEDİYE', amounts=total),
             row('46 34 14 10', name='İNSAN KAYNAKLARI VE\nEĞİTİM MÜDÜRLÜĞÜ', amounts=vector(3)),
             row(function='01', name='GENEL HİZMETLER', amounts=vector(3)),
             row(function='01 3', name='ALT İŞLEV', amounts=vector(3)),
             row(function='01 3 9', name='ALT İŞLEV', amounts=vector(3)),
             row(function='01 3 9 00', name='İŞLEV', amounts=vector(2)),
             row(fund='5', name='FİNANSMAN', amounts=vector(2)),
             row(economic='01', name='PERSONEL GİDERLERİ'),
             row(economic='01 01', name='ALT TOPLAM'),
             row(economic='03', name='MAL VE HİZMET ALIMI')]
    second = [row(function='02 1 1 00', name='BAŞKA İŞLEV'),
              row(fund='5', name='FİNANSMAN'), row(economic='01', name='PERSONEL'),
              row('46 34 14 20', name='SENTETİK MÜDÜRLÜK'),
              row(function='01 3 9 00', name='İŞLEV'),
              row(fund='5', name='FİNANSMAN'), row(economic='02', name='SGK')]
    if directorate_mismatch:
        first[3][5 + mismatch] = money(vector(3)[mismatch] + Decimal('0.01'))
    if fund_split:
        half = vector(Decimal('0.5'))
        # Use even cents for this split; keep the original 01 aggregate intact.
        half = [v.quantize(Decimal('0.01')) for v in half]
        rest = [a - b for a, b in zip(vector(), half)]
        first[9] = row(economic='01', name='PERSONEL GİDERLERİ', amounts=half)
        first[11:11] = [row(fund='6', name='BAŞKA FİNANSMAN', amounts=rest),
                        row(economic='01', name='PERSONEL GİDERLERİ', amounts=rest)]
    if blank:
        first[-1][5] = ''
    if duplicate:
        second.insert(3, second[2])
    if foreign_code:
        second[-1][0] = '46 35 14 20'
    if lead_layout:
        functions = {'01': '09', '01 3': '09 1', '01 3 9': '09 1 1', '01 3 9 00': '09 1 1 00'}
        for row_data in first + second:
            row_data[1] = functions.get(row_data[1], row_data[1])
            if row_data[3] == '01 01':
                row_data[3] = '01 1'
    if dotted_first:
        if dotted_first == 'institution':
            first.extend(second[:3])
            second = second[3:]
        for row_data in first + second:
            for i in range(4):
                row_data[i] = row_data[i].replace(' ', '.')
    headers = list(GIDER_HEADERS)
    if lead_layout:
        headers = ['\nKurum\nKodu', '\nFonksiyonel\nKodu', '\nFinan\nsal\nKodu',
                   '\nEkonomik\nKodu', '\n\nAçıklama', 'Geçen Yıldan\nDevreden\nÖdenek\nTL',
                   'Bütçe İle\nVerilen\nÖdenek\nTL', 'Ek Ve\nOlağanüstü\nVerilen Ödenek\nTL',
                   f'Aktarma {transfer}\nEklenen (+)\n\nTL' if transfer else '\nEklenen (+)\n\nTL',
                   '\nDüşülen (-)\n\nTL', '\nNet Ödenek\nToplamı\nTL',
                   '\nBütçe Gideri\nToplamı\nTL', '\nÖdenen Bütçe\nGideri\nTL',
                   '\nÖdenek Üstü\nHarcama\nTL', '\nİptal Edilen\nÖdenek\nTL',
                   'Gelecek Yıla\nDevrolan\nÖdenek\nTL']
    if bad_header:
        headers[bad_header[0]] = bad_header[1]
    return pdf_table(tmp_path / 'gider.pdf', headers, [65, 55, 45, 50, 120] + [65] * 11,
                     [first, second], centered=centered, scale=scale, year=year,
                     lead_layout=lead_layout, page_shift=page_shift, dates=dates,
                     date_overrides=date_overrides, date_prefix=date_prefix)


def revenue_pdf(tmp_path, *, ambiguous=False, total=True, mismatch=False, unproved=False,
                year=2026, centered=False, total_in_code=False, lead_layout=False,
                integer_wrap=False, split_code=False, dates=None, orphan=None,
                detail_first=False, unplaced=False, misplaced_code=False, carry_mismatch=False,
                misplaced_root=False, wrapped_description=False):
    headers = ['Gelirin Kodu', 'Açıklama', 'Bütçe ile Tahmin Edilen',
               f'{year - 1} Yılından Devreden Gelir', f'{year} Yılı Tahakkuku',
               'Toplam Tahakkuk', f'{year} Yılı Tahsilatı', 'Red ve İadeler',
               'Yılı Net Tahsilatı', f'{year + 1} Yılına Devreden Tahakkuk', 'Oran']
    values = ['1.250,00', '20,00', '1.180,00', '1.200,00', '1.150,2\n5', '10,00',
              '1.140,25', '59,75', '91,22']
    if ambiguous:
        values[4] = '1.150,2\n6'  # Does not satisfy Net = Tahsilat - Red.
    if unproved:
        values[0] = '1.250,0\n0'  # No row identity proves the estimate's repair.
    rows = [['01', 'SENTETİK VERGİ', *values],
            ['01 01', 'ALT TOPLAM — ÇİFT SAYILMAMALI', *[v.replace('\n', '') for v in values]],
            ['03', 'SENTETİK GELİR', '100,00', '0,00', '80,00', '80,00',
             '70,00', '0,00', '70,00', '10,00', '70,00']]
    if total:
        rows.append(['TOPLAM' if total_in_code else '', '' if total_in_code else 'GENEL TOPLAM',
                     '1.350,00', '20,00', '1.260,00', '1.280,00',
                     '1.220,25', '10,00', '1.210,25', '69,75', '89,65'])
    if mismatch:
        rows[-1][2] = '1.351,00'
    if carry_mismatch:
        rows[-1][9] = '69,76'
    if orphan:
        rows = [row for row in rows if row[0] != '03']
        rows.insert(2, [orphan, 'SENTETİK YETİM ALT GELİR', '100,00', '0,00', '80,00',
                        '80,00', '70,00', '0,00', '70,00', '10,00', '70,00'])
    if detail_first:
        rows[0], rows[1] = rows[1], rows[0]
    if integer_wrap:
        for row in rows:
            for i in range(2, 10):
                row[i] = row[i].replace('\n', '').replace(',', '\n,')
        rows[2][6] = '70\n,0'  # An explicit one-decimal suffix, proven by Net = Tahsilat - Red.
    if split_code:
        rows[0][0] = '0\n1'
    if misplaced_code:
        rows[0][0] = '0\n        1'
    if misplaced_root:
        rows[0][0] = '        0\n        1'
    if unplaced:
        rows[0][6] += '\nX'
    if wrapped_description:
        rows[0][1] += '\n\n' + 'SENTETİK UZUN HESAP ADININ DEVAMI ' * 6
    if lead_layout:
        headers = ['\n\nI   II   III   IV   V', '\n\nAçıklama',
                   '\nBütçe ile\nTahmin Edilen\nTL',
                   f'{year - 1}\nYılından\nDevreden Gelir\nTL',
                   f'{year}\nYılı\nTahakkuku\nTL', '\nToplam\nTahakkuk\nTL',
                   '\nYılı\nTahsilatı\nTL', '\nTahsilattan\nRed ve İadeler\nTL',
                   '\nYılı Net\nTahsilatı\nTL', f'{year + 1}\nYılına Devreden\nTahakkuk\nTL',
                   '\n\nOran']
    return pdf_table(tmp_path / 'gelir.pdf', headers, [90, 140] + [90] * 8 + [45],
                     [rows], centered=centered, year=year, lead_layout=lead_layout, dates=dates)


def departments(tmp_path, ids=(101, 102), unknown=False):
    path = tmp_path / 'departments.csv'
    with path.open('w', newline='', encoding='utf-8-sig') as output:
        writer = csv.writer(output)
        writer.writerow(['budget_code', 'department_id', 'department_name'])
        writer.writerow(['10', ids[0], 'İnsan Kaynakları ve Eğitim Müdürlüğü'])
        if not unknown:
            writer.writerow(['20', ids[1], 'Sentetik Müdürlük'])
    return path


def run(tmp_path, *args, csv_path=None, out=None, year=2026):
    output = out or tmp_path / 'out'
    result = subprocess.run([sys.executable, str(SCRIPT), '--year', str(year),
                             '--departments', str(csv_path or departments(tmp_path)),
                             '--out', str(output), *map(str, args)],
                            capture_output=True, text=True, cwd=tmp_path)
    return result, output


@pytest.mark.parametrize('centered,scale', [(False, 1), (True, 1), (True, 0.7)])
def test_expenditure_template_aggregation_and_wrapped_name(tmp_path, centered, scale):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, centered=centered, scale=scale))
    assert result.returncode == 0, result.stderr + (out / 'report.md').read_text()
    book = load_workbook(out / 'expenditure.xlsx')
    template = load_workbook(io.BytesIO(finance.template('expenditure')))
    assert book.active.title == template.active.title
    assert list(book.active.values)[0] == list(template.active.values)[0]
    rows = list(book.active.values)[1:]
    assert [(r[0], r[1]) for r in rows] == [(101, '01'), (101, '03'), (102, '02')]
    assert [parse_number(v) for v in rows[0][2:9]] == [
        Decimal(n) for n in ('2240.50', '30', '10', '2260.50', '2160.30', '80.20', '20')]
    report = (out / 'report.md').read_text()
    assert 'İNSAN KAYNAKLARI VE EĞİTİM MÜDÜRLÜĞÜ' in report
    assert 'Ödenen Bütçe Gideri' in report and 'fark' in report.lower()


def test_unknown_budget_code_lists_pdf_name(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path),
                      csv_path=departments(tmp_path, unknown=True))
    assert result.returncode != 0
    report = (out / 'report.md').read_text()
    assert '20' in report and 'SENTETİK MÜDÜRLÜK' in report
    assert not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('column', range(11))
@pytest.mark.parametrize('directorate', [False, True])
def test_every_source_expenditure_column_reconciles(tmp_path, column, directorate):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, mismatch=column,
                                                    directorate_mismatch=directorate))
    assert result.returncode != 0
    assert '0,01' in (out / 'report.md').read_text()
    assert not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('options', [{'blank': True}, {'duplicate': True}, {'foreign_code': True}])
def test_blank_or_duplicate_is_blocking(tmp_path, options):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, **options))
    assert result.returncode != 0
    assert not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('total,centered,year', [(True, False, 2026), (False, True, 2027)])
def test_revenue_wrapped_gross_collection_not_net(tmp_path, total, centered, year):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, total=total, centered=centered,
                                                    year=year), year=year)
    assert result.returncode == 0, result.stderr + (out / 'report.md').read_text()
    book = load_workbook(out / 'revenue.xlsx')
    template = load_workbook(io.BytesIO(finance.template('revenue')))
    assert book.active.title == template.active.title
    assert list(book.active.values)[0] == list(template.active.values)[0]
    rows = list(book.active.values)[1:]
    assert len(rows) == 2 and rows[0][0] == '01'
    assert parse_number(rows[0][2]) == Decimal('1150.25')
    assert parse_number(rows[0][3]) == Decimal('10')
    assert '1.150,2' in (out / 'report.md').read_text()
    if not total:
        assert 'toplam satırı yok' in (out / 'report.md').read_text().lower()


@pytest.mark.parametrize('options', [{'ambiguous': True}, {'mismatch': True},
                                    {'unproved': True, 'total': False}])
def test_unreconciled_revenue_blocks_both_workbooks(tmp_path, options):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path), '--gelir',
                      revenue_pdf(tmp_path, **options))
    assert result.returncode != 0
    assert 'Hata' in (out / 'report.md').read_text()
    assert not list(out.glob('*.xlsx'))


def test_wrong_year_and_non_pdf_are_reported(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, year=2025))
    assert result.returncode != 0
    assert not list(out.glob('*.xlsx'))
    bad = tmp_path / 'bozuk.pdf'
    bad.write_bytes(b'not a PDF')
    result, out = run(tmp_path, '--gider', bad, out=tmp_path / 'bad-out')
    assert result.returncode != 0 and (out / 'report.md').exists()


def test_duplicate_csv_id_and_existing_output_are_not_overwritten(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path),
                      csv_path=departments(tmp_path, ids=(101, 101)))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    (out / 'expenditure.xlsx').write_bytes(b'keep existing output')
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path), out=out)
    assert result.returncode != 0
    assert (out / 'expenditure.xlsx').read_bytes() == b'keep existing output'


@pytest.mark.postgres
def test_existing_preview_import_accepts_workbook(tmp_path, db, sample):
    from app import activity_sections_service as sections
    from app.models import ARSectionDefinition, Department, DepartmentScope
    from test_activity_sections import MIGRATION

    db.add_all([ARSectionDefinition(**row) for row in MIGRATION.SECTION_SEED])
    other = Department(organization_id=sample['department'].organization_id, name='Sentetik Müdürlük')
    db.add(other)
    db.flush()
    db.add(DepartmentScope(period_id=sample['period'].id, department_id=other.id, status='required'))
    db.flush()
    sections.create_year(db, sample['strategy'], sample['department'].organization_id,
                         sample['period'].id)
    # Locate the idare document using the service's own model rather than API writes.
    from sqlalchemy import select
    from app.models import ARDocument
    doc = db.scalar(select(ARDocument).where(ARDocument.scope == 'idare'))
    csv_path = departments(tmp_path, ids=(sample['department'].id, other.id))
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path), csv_path=csv_path)
    assert result.returncode == 0, result.stderr
    preview = finance.preview_import(db, sample['strategy'], doc.id, 'expenditure',
                                     (out / 'expenditure.xlsx').read_bytes(), doc.revision)
    assert preview['errors'] == []
    assert len(preview['rows']) == 3


def test_converter_does_not_import_application_or_use_network(tmp_path, monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        pytest.fail('Offline converter attempted a network connection')
    monkeypatch.setattr(socket, 'socket', forbidden)
    args = ['--gider', str(expense_pdf(tmp_path)), '--year', '2026', '--departments',
            str(departments(tmp_path)), '--out', str(tmp_path / 'offline')]
    assert converter.main(args) == 0


def test_multiple_financial_codes_are_aggregated(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, fund_split=True))
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'expenditure.xlsx').active.values)[1:]
    assert len(rows) == 3
    assert parse_number(rows[0][6]) == Decimal('2160.30')


def test_explicit_zero_is_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(sys.modules[__name__], 'vector', lambda scale=1: [Decimal(0)] * 11)
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path))
    assert result.returncode == 0
    row = list(load_workbook(out / 'expenditure.xlsx').active.values)[1]
    assert all(parse_number(v) == 0 for v in row[2:9])


def test_both_valid_inputs_and_reordered_csv_columns(tmp_path):
    csv_path = tmp_path / 'mapping.csv'
    csv_path.write_text('department_name,department_id,budget_code\n'
                        'Sentetik A,101,10\nSentetik B,102,20\n', encoding='utf-8')
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path), '--gelir', revenue_pdf(tmp_path),
                      csv_path=csv_path)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert {p.name for p in out.iterdir()} == {'expenditure.xlsx', 'revenue.xlsx', 'report.md'}


def test_revenue_total_label_in_code_column(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, total_in_code=True))
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert 'Gelir düzey 1 toplamı' in (out / 'report.md').read_text()


@pytest.mark.parametrize('name', ['report.md', 'expenditure.xlsx', 'revenue.xlsx'])
def test_output_symlinks_never_write_outside_out(tmp_path, name):
    out = tmp_path / 'out'
    out.mkdir()
    outside = tmp_path / 'outside'
    # Include a dangling link; exists() alone does not protect this case.
    (out / name).symlink_to(outside)
    result, _ = run(tmp_path, '--gider', expense_pdf(tmp_path), '--gelir', revenue_pdf(tmp_path), out=out)
    assert result.returncode != 0
    assert not outside.exists()


def test_staging_failure_removes_only_new_workbooks(tmp_path, monkeypatch):
    original_link = converter.os.link
    calls = []
    def fail_second(source, target):
        calls.append(target)
        if len(calls) == 2:
            raise OSError('synthetic disk failure')
        return original_link(source, target)
    monkeypatch.setattr(converter.os, 'link', fail_second)
    existing = tmp_path / 'operator.txt'
    existing.write_text('keep')
    with pytest.raises(OSError):
        converter.write_outputs(tmp_path, {'expenditure': [], 'revenue': []}, 'test')
    assert list(tmp_path.iterdir()) == [existing]


def test_cli_audit_forbids_network_app_imports_and_external_writes(tmp_path):
    out = tmp_path / 'out'
    pdf = expense_pdf(tmp_path)
    mapping = departments(tmp_path)
    harness = r'''
import os, sys
from pathlib import Path
sys.dont_write_bytecode = True
script, output, *args = sys.argv[1:]
allowed = Path(output).resolve()
def audit(event, args):
    if event == 'socket.connect':
        raise AssertionError('network access')
    if event == 'import' and (args[0] == 'app' or args[0].startswith('app.')
                              or args[0].startswith('sqlalchemy')):
        raise AssertionError('application/database import')
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            if not Path(os.fsdecode(path)).resolve().is_relative_to(allowed):
                raise AssertionError('write outside --out: ' + os.fsdecode(path))
sys.addaudithook(audit)
sys.argv = [script, '--out', output, *args]
exec(compile(Path(script).read_bytes(), script, 'exec'), {'__name__': '__main__'})
'''
    result = subprocess.run([sys.executable, '-c', harness, str(SCRIPT), str(out),
                             '--gider', str(pdf), '--departments', str(mapping), '--year', '2026'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert {p.name for p in out.iterdir()} == {'expenditure.xlsx', 'report.md'}


@pytest.mark.parametrize('transfer', ['Suratiyle', 'Suretiyle', ''])
def test_lead_points_1_2_four_header_lines_and_documented_variants(tmp_path, transfer):
    pdf = expense_pdf(tmp_path, lead_layout=True, transfer=transfer)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert len(list(load_workbook(out / 'expenditure.xlsx').active.values)) == 4


@pytest.mark.parametrize('shift', [-12, 11])
def test_lead_point_4_per_page_shifted_hierarchy_bounds(tmp_path, shift):
    pdf = expense_pdf(tmp_path, lead_layout=True, page_shift=shift)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert 'Müdürlük 20' in (out / 'report.md').read_text()


@pytest.mark.parametrize('options', [{'lead_layout': True}, {'integer_wrap': True},
                                    {'split_code': True},
                                    {'lead_layout': True, 'integer_wrap': True, 'split_code': True}])
def test_lead_points_5_6_7_revenue_headers_suffixes_and_vertical_code(tmp_path, options):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, **options))
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert [(row[0], parse_number(row[1]), parse_number(row[2])) for row in rows] == [
        ('01', Decimal('1250'), Decimal('1150.25')), ('03', Decimal('100'), Decimal('70'))]
    # Every reported monetary comparison must be exact, including unimported columns.
    comparisons = [line for line in (out / 'report.md').read_text().splitlines()
                   if re.fullmatch(r'\| .* \| -?[\d.,]+ \| -?[\d.,]+ \| -?[\d.,]+ \|', line)]
    assert comparisons and all(line.endswith('| 0,00 |') for line in comparisons)


@pytest.mark.parametrize('kind', ['gider', 'gelir'])
@pytest.mark.parametrize('dates', [{'start': None}, {'end': None},
                                 {'start': '01/01/2025'}, {'end': '31/12/2025'},
                                 {'start': '31/02/2026'},
                                 {'start': '31/12/2026', 'end': '01/01/2026'}])
def test_lead_point_3_missing_invalid_or_mismatched_source_dates_block_both(tmp_path, kind, dates):
    gider = expense_pdf(tmp_path, dates=dates if kind == 'gider' else None)
    gelir = revenue_pdf(tmp_path, dates=dates if kind == 'gelir' else None)
    result, out = run(tmp_path, '--gider', gider, '--gelir', gelir)
    assert result.returncode != 0
    assert not list(out.glob('*.xlsx'))
    assert 'Tarih' in (out / 'report.md').read_text() or 'tarih' in (out / 'report.md').read_text()


@pytest.mark.parametrize('period', [None, '2025'])
def test_revenue_period_metadata_is_required_and_consistent(tmp_path, period):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, dates={'period': period}))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))


def test_continuation_page_conflicting_dates_are_rejected(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(
        tmp_path, lead_layout=True, date_overrides={1: {'end': '30/12/2026'}}))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('label', ['Bilinmeyen Tutar', '', 'Bütçe Gideri Toplamı'])
def test_unknown_missing_or_duplicate_header_remains_blocking(tmp_path, label):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, lead_layout=True,
                                                    bad_header=(10, label)))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))


def test_wrapped_estimate_can_be_proven_by_independent_total(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, unproved=True))
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert 'genel toplam' in (out / 'report.md').read_text().lower()


@pytest.mark.parametrize('root', ['03 01', '99 01'])
def test_revenue_detail_missing_or_unknown_parent_without_total_is_blocking(tmp_path, root):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, total=False, orphan=root))
    assert result.returncode != 0
    assert root.split()[0] in (out / 'report.md').read_text()
    assert not list(out.glob('*.xlsx'))


def test_revenue_parent_may_appear_after_detail(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, total=False, detail_first=True))
    assert result.returncode == 0, (out / 'report.md').read_text()


@pytest.mark.parametrize('first', ['institution', 'function'])
def test_dotted_codes_on_first_row_of_continuation_page(tmp_path, first):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, dotted_first=first, page_shift=-10))
    assert result.returncode == 0, (out / 'report.md').read_text()


def test_unplaceable_revenue_fragment_is_a_located_error(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, lead_layout=True, unplaced=True))
    assert result.returncode != 0
    report = (out / 'report.md').read_text()
    assert 'sayfa 1' in report and 'satır' in report
    assert not list(out.glob('*.xlsx'))


def test_vertical_code_fragments_must_share_the_same_subcolumn(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, lead_layout=True, misplaced_code=True))
    assert result.returncode != 0
    assert 'alt sütun' in (out / 'report.md').read_text()
    assert not list(out.glob('*.xlsx'))


def test_revenue_root_cannot_start_in_level_ii(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, lead_layout=True, misplaced_root=True))
    assert result.returncode != 0
    assert 'I düzeyi' in (out / 'report.md').read_text()
    assert not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('error', ['expenditure', 'revenue', 'carry', 'missing_total'])
def test_lead_layout_reconciliation_stays_blocking_for_both_outputs(tmp_path, error):
    gider = expense_pdf(tmp_path, lead_layout=True, mismatch=7 if error == 'expenditure' else None)
    gelir = revenue_pdf(tmp_path, lead_layout=True, integer_wrap=True, split_code=True,
                        ambiguous=error == 'revenue', carry_mismatch=error == 'carry',
                        total=error != 'missing_total')
    result, out = run(tmp_path, '--gider', gider, '--gelir', gelir)
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    report = (out / 'report.md').read_text()
    assert 'Hatalar' in report
    if error in {'expenditure', 'revenue', 'carry'}:
        assert '0,01' in report


@pytest.mark.parametrize('centered', [False, True])
def test_lead_retest_title_date_is_not_the_expenditure_body(tmp_path, centered):
    pdf = expense_pdf(tmp_path, lead_layout=True, centered=centered, date_prefix=True, page_shift=-9)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert len(list(load_workbook(out / 'expenditure.xlsx').active.values)) == 4


@pytest.mark.parametrize('centered', [False, True])
def test_lead_retest_centered_header_fragments_use_column_bands(tmp_path, centered):
    pdf = expense_pdf(tmp_path, lead_layout=True, centered=centered, page_shift=11)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()


@pytest.mark.parametrize('layout', [False, True])
def test_lead_retest_text_only_description_can_cross_amount_columns(tmp_path, layout):
    pdf = revenue_pdf(tmp_path, lead_layout=layout, integer_wrap=layout,
                      split_code=layout, wrapped_description=True)
    result, out = run(tmp_path, '--gelir', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    source_rows = converter.pdf_rows(pdf, 'revenue', 2026)
    assert source_rows[0].text(1).count('SENTETİK UZUN HESAP ADININ DEVAMI') == 6
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert rows[0][0] == '01' and parse_number(rows[0][2]) == Decimal('1150.25')


@pytest.mark.parametrize('column', [4, 10])
def test_failed_header_reports_the_candidate_block(tmp_path, column):
    pdf = expense_pdf(tmp_path, lead_layout=True, centered=True, date_prefix=True,
                      bad_header=(column, 'Bilinmeyen Tutar'))
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode != 0
    report = (out / 'report.md').read_text()
    assert 'Başlık adayı' in report and 'Bilinmeyen' in report and 'Geçen' in report
    assert not list(out.glob('*.xlsx'))


def test_text_only_continuation_does_not_bypass_reconciliation(tmp_path):
    pdf = revenue_pdf(tmp_path, lead_layout=True, integer_wrap=True, split_code=True,
                      wrapped_description=True, ambiguous=True)
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path), '--gelir', pdf)
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert '0,01' in (out / 'report.md').read_text()
