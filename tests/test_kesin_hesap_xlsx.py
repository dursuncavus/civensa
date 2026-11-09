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
              lead_layout=False, page_shift=0, dates=None, date_overrides=None, date_prefix=False,
              table_marker=False, header_size=6, amount_size=6, continuation_shift=0,
              closing_page=None, total_footer=None):
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
            canvas.drawRightString(900 if table_marker else 1130, 810,
                                   'Başlangıç Tarihi : ' + metadata['start'])
        if metadata['end'] is not None:
            canvas.drawRightString(1130, 810 if table_marker else 800,
                                   'Bitiş Tarihi : ' + metadata['end'])
        if len(headers) == 11 and metadata['period'] is not None:
            canvas.drawString(20, 800, 'Dönemi : ' + metadata['period'])
        if date_prefix:
            # Dotted title dates resemble code prefixes, but carry no amounts.
            canvas.drawString(20, 800, f'01.01.{year}')
        if table_marker:
            canvas.drawString(23, 786, '11' if table_marker is True else str(table_marker))
        canvas.setFont('Civ194Test', header_size)
        x = 20
        for column, (label, width) in enumerate(zip(headers, widths)):
            if closing_page == 'bad_header' and page_no == 2 and column == 0:
                label = label.replace('Kurum', 'Bilinmeyen')
            fragments = label.split('\n') if lead_layout else simpleSplit(label, 'Civ194Test', header_size, width - 10)
            for n, line in enumerate(fragments):
                if table_marker and column == 8 and n == 0:
                    canvas.drawCentredString(x + width, 770, line)
                elif centered:
                    canvas.drawCentredString(x + width / 2, 770 - n * 8, line)
                else:
                    canvas.drawString(x + 3, 770 - n * 8, line)
            x += width
        if len(headers) == 11 and not lead_layout:
            canvas.drawString(23, 738, 'I   II   III   IV   V')
        y = 710
        if closing_page and page_no == 2:
            signatures = [('Düzenleyen', 'Muhasebe Yetkilisi'),
                          ('Adı Soyadı :', 'Adı Soyadı :'),
                          ('Tarih :', 'Tarih :'), ('İmza :', 'İmza :')]
            if closing_page == 'missing_label':
                signatures.pop()
            for left, right in signatures if closing_page != 'header_only' else []:
                canvas.drawString(23, y, left)
                canvas.drawString(1030, y, right)
                y -= 16
            if closing_page in {'extra_text', 'amount', 'code'}:
                canvas.drawString(23, y, {'extra_text': 'Bilinmeyen ek bilgi',
                                         'amount': '1,00', 'code': '46 34 14 10'}[closing_page])
        for row in rows:
            if total_footer and row[1] == 'TOPLAM':
                canvas.setFont('Civ194Test', 6)
                canvas.drawString(20 + widths[0] + 3, y, 'TOPLAM')
                x = 20 + sum(widths[:2])
                for column, (value, width) in enumerate(zip(row[2:], widths[2:])):
                    raw = str(value)
                    complete = column in {5, 8} or total_footer == 'complete'
                    if not complete:
                        raw = raw[:-1] if column % 2 else raw.split(',')[0]
                    if total_footer == 'integer_mismatch' and column == 0:
                        raw = money(parse_number(value) + 1000).split(',')[0]
                    elif total_footer == 'short_integer' and column == 0:
                        raw = raw.rsplit('.', 1)[0]
                    elif total_footer == 'decimal_mismatch' and column == 1:
                        raw = raw[:-1] + '8'
                    elif total_footer in {'refund_mismatch', 'rate_mismatch'} and column == (
                            5 if total_footer == 'refund_mismatch' else 8):
                        raw = money(parse_number(value) + Decimal('.01'))
                    elif total_footer == 'truncated_refund' and column == 5:
                        raw = raw.split(',')[0]
                    if total_footer != 'missing_cell' or column != 1:
                        gap = 7 if total_footer == 'distant' else 6 if total_footer == 'six_points' else 4.7
                        canvas.drawRightString(x + width - 5, y if column in {5, 8} else y - gap, raw)
                    x += width
                if total_footer == 'extra_text':
                    canvas.drawString(23, y - 10, 'Bilinmeyen ek kayıt')
                for left, right in [('Düzenleyen', 'Muhasebe Yetkilisi'),
                                    ('Adı Soyadı :', 'Adı Soyadı :'),
                                    ('Tarih :', 'Tarih :'), ('İmza :', 'İmza :')]:
                    y -= 20
                    canvas.drawString(23, y, left)
                    canvas.drawString(900, y, right)
                continue
            x = 20
            height = 1
            for index, (value, width) in enumerate(zip(row, widths)):
                lines = str(value).split('\n')
                height = max(height, len(lines))
                for n, line in enumerate(lines):
                    if index >= (5 if len(headers) == 16 else 2):
                        canvas.setFont('Civ194Test', amount_size)
                        canvas.drawRightString(x + width - 5 + (continuation_shift if n else 0),
                                               y - n * 8, line)
                    else:
                        canvas.setFont('Civ194Test', 6)
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
                year=2026, dates=None, date_overrides=None, bad_header=None, date_prefix=False,
                table_marker=False, closing_page=None):
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
    if table_marker:
        headers[10:15] = ['Net\nÖdenek\nToplamı\nTL', 'Bütçe\nGideri\nToplamı\nTL',
                          'Ödenen\nBütçe\nGideri\nTL', 'Ödenek\nÜstü\nHarcama\nTL',
                          'İptal\nEdilen\nÖdenek\nTL']
    pages = [first, second]
    if closing_page:
        pages.append([])
        if closing_page == 'not_last':
            pages.append([])
    return pdf_table(tmp_path / 'gider.pdf', headers, [65, 55, 45, 50, 120] + [65] * 11,
                     pages, centered=centered, scale=scale, year=year,
                     lead_layout=lead_layout, page_shift=page_shift, dates=dates,
                     date_overrides=date_overrides, date_prefix=date_prefix, table_marker=table_marker,
                     closing_page=closing_page)


def revenue_pdf(tmp_path, *, ambiguous=False, total=True, mismatch=False, unproved=False,
                year=2026, centered=False, total_in_code=False, lead_layout=False,
                integer_wrap=False, split_code=False, dates=None, orphan=None,
                detail_first=False, unplaced=False, misplaced_code=False, carry_mismatch=False,
                misplaced_root=False, wrapped_description=False, deduction=None, deduction_error=None):
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
    if deduction is not None:
        rows.insert(3, ['09', 'Red ve İadeler (-)', deduction, *(['0,00'] * 8)])
        if total:
            rows[-1][2] = '1.099,75'
        if deduction_error == 'code':
            rows[3][0] = '04'
        elif deduction_error == 'label':
            rows[3][1] = 'SENTETİK NEGATİF GELİR'
        elif deduction_error == 'actual':
            rows[3][6] = rows[3][8] = '1,00'
            rows[-1][6], rows[-1][8] = '1.221,25', '1.211,25'
        elif deduction_error == 'blank':
            rows[3][9] = ''
        elif deduction_error == 'total':
            rows[-1][2] = '1.099,76'
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
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, deduction='- 250,25'),
                      csv_path=csv_path, out=tmp_path / 'revenue-out')
    assert result.returncode == 0, (out / 'report.md').read_text()
    preview = finance.preview_import(db, sample['strategy'], doc.id, 'revenue',
                                     (out / 'revenue.xlsx').read_bytes(), doc.revision)
    assert preview['errors'] == []
    assert len(preview['rows']) == 2


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


@pytest.mark.parametrize('centered', [False, True])
def test_bare_form_number_above_three_line_financial_header(tmp_path, centered):
    pdf = expense_pdf(tmp_path, lead_layout=True, table_marker=True, centered=centered)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'expenditure.xlsx').active.values)[1:]
    assert [(row[0], row[1]) for row in rows] == [(101, '01'), (101, '03'), (102, '02')]


def narrow_decimal_pdf(tmp_path, mode, *, wrong=False, invalid=None):
    """Invented amounts; integer and suffix use different baselines/alignment."""
    values = ['12.345.678,90', '12.345.678,12', '12.345.678,34', '24.691.356,46',
              '12.345.678,56', '1.234.567,12', '11.111.111,44', '13.580.245,02']
    headers = ['\n\nI   II   III   IV   V', '\n\nAçıklama', '\nBütçe ile\nTahmin Edilen\nTL',
               '2025\nYılından\nDevreden Gelir\nTL', '2026\nYılı\nTahakkuku\nTL',
               '\nToplam\nTahakkuk\nTL', '\nYılı\nTahsilatı\nTL',
               '\nTahsilattan\nRed ve İadeler\nTL', '\nYılı Net\nTahsilatı\nTL',
               '2027\nYılına Devreden\nTahakkuk\nTL', '\n\nOran']
    parts = []
    for i, value in enumerate(values):
        integer, decimals = value.split(',')
        form = 'comma' if mode == 'mixed' and i % 2 == 0 else 'digit' if mode == 'mixed' else mode
        parts.append(integer + '\n,' + decimals if form == 'comma'
                     else integer + ',' + decimals[0] + '\n' + decimals[1])
    if wrong:
        parts[4] = parts[4][:-1] + '7'  # Net identity must fail; never repair the amount.
    if invalid == 'orphan_digit':
        parts[0] = '12.345.678\n9'  # No preceding ,d to complete.
    if invalid == 'missing_suffix':
        parts[-1] = parts[-1].split('\n')[0]
    rows = [['0\n1', 'SENTETİK DAR HÜCRELİ GELİR', *parts, '90,00'],
            ['', 'GENEL TOPLAM', *[v.replace('\n', '') for v in parts], '90,00']]
    # Adjacent columns are deliberately too narrow for a complete amount.
    return pdf_table(tmp_path / 'dar-gelir.pdf', headers, [90, 140] + [36] * 8 + [30],
                     [rows], lead_layout=True, header_size=4, amount_size=4.5,
                     continuation_shift=5)


@pytest.mark.parametrize('mode', ['comma', 'digit', 'mixed'])
def test_decimal_continuations_in_adjacent_narrow_columns(tmp_path, mode):
    result, out = run(tmp_path, '--gelir', narrow_decimal_pdf(tmp_path, mode))
    assert result.returncode == 0, (out / 'report.md').read_text()
    row = list(load_workbook(out / 'revenue.xlsx').active.values)[1]
    assert row[0] == '01'
    assert [parse_number(v) for v in row[1:4]] == [Decimal('12345678.90'), Decimal('12345678.56'),
                                                 Decimal('1234567.12')]


def test_wrong_decimal_continuation_still_blocks_both_workbooks(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, lead_layout=True, table_marker=True),
                      '--gelir', narrow_decimal_pdf(tmp_path, 'mixed', wrong=True))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert '0,01' in (out / 'report.md').read_text()


@pytest.mark.parametrize('invalid', ['orphan_digit', 'missing_suffix'])
def test_incomplete_decimal_continuations_are_never_guessed(tmp_path, invalid):
    result, out = run(tmp_path, '--gelir', narrow_decimal_pdf(tmp_path, 'comma', invalid=invalid))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert 'sayfa 1' in (out / 'report.md').read_text()


def test_form_marker_filter_preserves_four_digit_year_evidence(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, lead_layout=True, table_marker='2025'))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert '2025' in (out / 'report.md').read_text()


@pytest.mark.parametrize('centered', [False, True])
def test_lead_signature_only_last_expenditure_page_is_reported_and_skipped(tmp_path, centered):
    pdf = expense_pdf(tmp_path, lead_layout=True, table_marker=True, closing_page='valid',
                      centered=centered, page_shift=-9)
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert len(list(load_workbook(out / 'expenditure.xlsx').active.values)) == 4
    report = (out / 'report.md').read_text()
    assert 'sayfa 3' in report and 'imza kapanış sayfası atlandı' in report


@pytest.mark.parametrize('invalid', ['header_only', 'missing_label', 'extra_text', 'amount',
                                     'code', 'not_last', 'bad_header'])
def test_other_dataless_expenditure_pages_stay_blocking(tmp_path, invalid):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, lead_layout=True,
                      table_marker=True, closing_page=invalid), '--gelir', revenue_pdf(tmp_path))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert 'kodlu veri satırı bulunamadı' in (out / 'report.md').read_text()


@pytest.mark.parametrize('amount', ['-250,25', '- 250,25', '-   250,25', '- 250\n,25'])
def test_lead_signed_planned_deduction_reconciles_without_positive_revenue(tmp_path, amount):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, lead_layout=True, deduction=amount))
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert [row[0] for row in rows] == ['01', '03']
    assert sum(parse_number(row[1]) for row in rows) == Decimal('1350')
    assert sum(parse_number(row[2]) - parse_number(row[3]) for row in rows) == Decimal('1210.25')
    report = (out / 'report.md').read_text()
    assert 'Gelir düzey 1 toplamı' in report
    assert '1.350,00 + (-250,25) = 1.099,75' in report
    assert 'XLSX brüt tahmin' in report and 'XLSX satırı üretilmedi' in report


def test_planned_deduction_requires_independent_pdf_total(tmp_path):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, deduction='- 250,25', total=False))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))


@pytest.mark.parametrize('invalid', ['code', 'label', 'actual', 'blank', 'total'])
def test_planned_deduction_exception_does_not_weaken_validation(tmp_path, invalid):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, closing_page='valid'),
                      '--gelir', revenue_pdf(tmp_path, deduction='- 250,25', deduction_error=invalid))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    if invalid == 'total':
        assert '0,01' in (out / 'report.md').read_text()


@pytest.mark.parametrize('amount', ['--250,25', '- -250,25', '+250,25', '- 250 ,25',
                                   '250,25 -', '- 250,25X'])
def test_only_detached_leading_minus_is_normalized(tmp_path, amount):
    result, out = run(tmp_path, '--gelir', revenue_pdf(tmp_path, deduction=amount))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))


def test_signature_only_closing_page_dates_still_have_to_match(tmp_path):
    pdf = expense_pdf(tmp_path, closing_page='valid', date_overrides={2: {'end': '30/12/2026'}})
    result, out = run(tmp_path, '--gider', pdf)
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    assert 'Tarihi sayfalar arasında tutarsız' in (out / 'report.md').read_text()


def test_both_lead_blockers_together_keep_all_reconciliations_exact(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path, lead_layout=True,
                      table_marker=True, closing_page='valid'),
                      '--gelir', revenue_pdf(tmp_path, lead_layout=True, deduction='- 250,25'))
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert {path.name for path in out.iterdir()} == {'expenditure.xlsx', 'revenue.xlsx', 'report.md'}
    # Every reconciliation table's last (difference) cell must stay zero.
    lines = (out / 'report.md').read_text().splitlines()
    differences = [line.rsplit('|', 2)[1].strip() for line in lines
                   if line.startswith('|') and line.count('|') == 5
                   and re.fullmatch(r'-?[\d.]+,\d{2}', line.rsplit('|', 2)[1].strip())]
    assert len(differences) == 42
    assert set(differences) == {'0,00'}


def test_detached_minus_with_grouped_millions_stays_in_its_column(tmp_path):
    headers = ['Gelirin Kodu', 'Açıklama', *converter.revenue_labels(2026), 'Oran']
    rows = [['01', 'SENTETİK GELİR', '5.000.000,00', *(['0,00'] * 8)],
            ['09', 'Red ve İadeler (-)', '- 2.345.678,91', *(['0,00'] * 8)],
            ['', 'GENEL TOPLAM', '2.654.321,09', *(['0,00'] * 8)]]
    pdf = pdf_table(tmp_path / 'large-synthetic.pdf', headers, [90, 140] + [90] * 8 + [45], [rows])
    result, out = run(tmp_path, '--gelir', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    assert list(load_workbook(out / 'revenue.xlsx').active.values)[1] == (
        '01', '5.000.000,00', '0,00', '0,00', None)
    assert '5.000.000,00 + (-2.345.678,91) = 2.654.321,09' in (out / 'report.md').read_text()


def straddled_code_pdf(tmp_path, *, first=True, centered=False, invalid=None):
    """Code above/below the amount baseline; suffixes follow the lower digit."""
    headers = ['Gelirin Kodu', 'Açıklama', *converter.revenue_labels(2026), 'Oran']
    v = list(map(Decimal, ['1250.25', '20.25', '1180.50', '1200.75',
                           '1150.25', '10.10', '1140.15', '60.60']))
    extra = list(map(Decimal, ['100', '0', '80', '80', '70', '0', '70', '10']))
    wrapped = []
    for column, value in enumerate(v):
        raw = money(value)
        if column == 5:
            wrapped.append('\n' + raw)
        elif column in {4, 7}:
            wrapped.append('\n' + raw[:-1] + '\n\n' + raw[-1])
        else:
            whole, decimals = raw.split(',')
            wrapped.append('\n' + whole + '\n\n,' + decimals)
    if invalid == 'wrong_digit':
        wrapped[4] = wrapped[4][:-1] + '6'
    elif invalid == 'missing_suffix':
        wrapped[0] = wrapped[0].split('\n\n')[0]
    elif invalid == 'misaligned_suffix':
        # Right-aligned drawing: trailing spaces displace the visible suffix.
        wrapped[0] += ' ' * 80
    code = '0\n\n5'
    if invalid == 'wrong_code_column':
        code = '0\n\n        5'
    elif invalid == 'extra_code':
        code = '0\n\n5 1'
    elif invalid == 'intervening_text':
        code = '0\n\nX'
    elif invalid == 'missing_lower_code':
        code = '0'
    elif invalid == 'ambiguous_code':
        wrapped = ['\n' + money(value) for value in v]
    rows = [[code, '\nDiğer Gelirler', *wrapped, '\n91,22'],
            ['0\n\n6', '\nSermaye Gelirleri', *['\n' + money(value) for value in extra], '\n70,00']]
    if invalid == 'ambiguous_code':
        rows[1][0] = ''
    total = [a + b for a, b in zip(v, extra)]
    if not first:
        rows.insert(0, ['01', 'SENTETİK ÖNCEKİ GELİR', *map(money, extra), '70,00'])
        total = [a + b for a, b in zip(total, extra)]
    rows.append(['', 'GENEL TOPLAM', *map(money, total), '89,00'])
    return pdf_table(tmp_path / 'straddled.pdf', headers, [90, 140] + [90] * 8 + [45], [rows],
                     centered=centered)


@pytest.mark.parametrize('first', [False, True])
@pytest.mark.parametrize('centered', [False, True])
def test_lead_code_straddles_amount_baseline_and_decimal_follows_two_lines_later(tmp_path, first, centered):
    pdf = straddled_code_pdf(tmp_path, first=first, centered=centered)
    lines = converter.PdfReader(pdf).pages[0].extract_text(extraction_mode='layout',
                                                         layout_mode_space_vertically=False).splitlines()
    baseline = next(i for i, line in enumerate(lines) if 'Diğer Gelirler' in line)
    assert lines[baseline - 1].strip() == '0'
    assert lines[baseline + 1].strip() == '5'
    assert lines[baseline + 2].strip().startswith(',25')
    result, out = run(tmp_path, '--gelir', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert [row[0] for row in rows] == (['05', '06'] if first else ['01', '05', '06'])
    row = next(row for row in rows if row[0] == '05')
    assert list(map(parse_number, row[1:4])) == list(map(Decimal, ['1250.25', '1150.25', '10.10']))
    assert 'bağımsız genel toplam sütunuyla doğrulandı' in (out / 'report.md').read_text()


@pytest.mark.parametrize('invalid', ['wrong_digit', 'missing_suffix', 'misaligned_suffix',
                                     'wrong_code_column', 'extra_code', 'intervening_text',
                                     'missing_lower_code', 'ambiguous_code'])
def test_straddled_code_keeps_invalid_continuations_blocking(tmp_path, invalid):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path),
                      '--gelir', straddled_code_pdf(tmp_path, invalid=invalid))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    report = (out / 'report.md').read_text()
    assert 'sayfa 1' in report
    if invalid == 'wrong_digit':
        assert '0,01' in report
    elif invalid == 'ambiguous_code':
        assert 'kayıtlar arasında kod tahmin edilmedi' in report


def truncated_total_pdf(tmp_path, *, invalid=None, deduction=False):
    headers = ['Gelirin Kodu', 'Açıklama', *converter.revenue_labels(2026), 'Oran']
    values = list(map(Decimal, ['11222333.45', '1234567.89', '8765432.11', '10000000',
                               '9876543.21', '123456.78', '9753086.43', '246913.57']))
    extra = list(map(Decimal, ['1000.11', '0.10', '50.20', '50.30', '30.22', '0.11', '30.11', '20.19']))
    summed = [a + b for a, b in zip(values, extra)]
    if deduction:
        summed[0] -= Decimal('250.25')
    rate = (summed[6] / summed[0] * 100).quantize(Decimal('.01'))
    rows = [['01', 'SENTETİK GELİR', *map(money, values), '86,91'],
            ['05', 'SENTETİK EK GELİR', *map(money, extra), '3,01'],
            ['', 'TOPLAM', *map(money, summed), money(rate)]]
    if deduction:
        rows.insert(2, ['09', 'Red ve İadeler (-)', '- 250,25', *(['0,00'] * 8)])
    if invalid == 'body_truncation':
        rows[0][2] = rows[0][2].split(',')[0]
    elif invalid == 'wrapped_data':
        rows[0][2] = rows[0][2].replace(',', '\n,')
    elif invalid == 'unproved_one_decimal_data':
        rows[0][2] = rows[0][2][:-1].replace(',', '\n,')
    return pdf_table(tmp_path / 'truncated-total.pdf', headers, [90, 140] + [65] * 8 + [45], [rows],
                     header_size=5, total_footer=invalid or 'valid')


def test_lead_total_with_absent_decimals_is_only_a_prefix_check(tmp_path):
    pdf = truncated_total_pdf(tmp_path)
    result, out = run(tmp_path, '--gelir', pdf)
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert [row[0] for row in rows] == ['01', '05']
    assert sum(parse_number(row[1]) for row in rows) == Decimal('11223333.56')
    report = (out / 'report.md').read_text()
    assert 'TOPLAM önek kontrolü' in report and 'eksik haneler tahmin edilmedi' in report


def test_lead_truncated_total_integer_mismatch_blocks_both_workbooks(tmp_path):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path),
                      '--gelir', truncated_total_pdf(tmp_path, invalid='integer_mismatch'))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    report = (out / 'report.md').read_text()
    assert 'sayfa 1' in report and 'Bütçe ile Tahmin Edilen' in report
    assert 'TOPLAM öneki uyuşmuyor' in report


@pytest.mark.parametrize('invalid,label', [
    ('short_integer', 'Bütçe ile Tahmin Edilen'), ('decimal_mismatch', 'Yılından Devreden Gelir'),
    ('refund_mismatch', 'Red ve İadeler'), ('rate_mismatch', 'Oran'),
    ('truncated_refund', 'Red ve İadeler'), ('missing_cell', 'Yılından Devreden Gelir'),
    ('distant', '6 punto'), ('extra_text', 'TOPLAM'), ('body_truncation', 'sütun'),
    ('unproved_one_decimal_data', 'önekten rakam tahmin edilmedi')])
def test_total_prefix_exception_keeps_other_checks_blocking(tmp_path, invalid, label):
    result, out = run(tmp_path, '--gider', expense_pdf(tmp_path),
                      '--gelir', truncated_total_pdf(tmp_path, invalid=invalid))
    assert result.returncode != 0 and not list(out.glob('*.xlsx'))
    report = (out / 'report.md').read_text()
    assert 'sayfa 1' in report and label in report


@pytest.mark.parametrize('shape', ['six_points', 'complete', 'wrapped_data'])
def test_total_footer_boundaries_and_source_digits_are_preserved(tmp_path, shape):
    result, out = run(tmp_path, '--gelir', truncated_total_pdf(tmp_path, invalid=shape))
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert len(rows) == 2 and rows[0][1] == '11.222.333,45'
    if shape == 'wrapped_data':
        assert 'TOPLAM’da bulunmayan ondalıklar bağımsız doğrulanamadı' in (out / 'report.md').read_text()


def test_truncated_total_keeps_detached_minus_deduction_signed(tmp_path):
    result, out = run(tmp_path, '--gelir', truncated_total_pdf(tmp_path, deduction=True))
    assert result.returncode == 0, (out / 'report.md').read_text()
    rows = list(load_workbook(out / 'revenue.xlsx').active.values)[1:]
    assert [row[0] for row in rows] == ['01', '05']
    report = (out / 'report.md').read_text()
    assert '11.223.333,56 + (-250,25) = 11.223.083,31' in report
    assert 'hesaplanan net tahmin (PDF TOPLAM önek kontrolü)' in report
