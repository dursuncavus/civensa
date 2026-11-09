#!/usr/bin/env python3
"""Offline, fail-closed final-account PDF to Civensa financial import converter."""
import sys

# CLI execution must not leave import caches outside --out or load app/db.py.
if __name__ == '__main__':
    sys.dont_write_bytecode = True

import argparse
from collections import defaultdict
from copy import copy
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import io
import os
from pathlib import Path
import re
import tempfile
import unicodedata

from openpyxl import Workbook
from pypdf import PdfReader, Transformation
from pypdf.errors import PyPdfError


EXPENSE_SOURCE = (
    'Geçen Yıldan Devreden Ödenek', 'Bütçe İle Verilen Ödenek',
    'Ek Ve Olağanüstü Verilen Ödenek', 'Aktarma Suretiyle Eklenen (+)',
    'Düşülen (-)', 'Net Ödenek Toplamı', 'Bütçe Gideri Toplamı',
    'Ödenen Bütçe Gideri', 'Ödenek Üstü Harcama', 'İptal Edilen Ödenek',
    'Gelecek Yıla Devrolan Ödenek',
)
EXPENSE_HEADERS = ('Müdürlük No', 'Ekonomik Kod', 'Başlangıç Ödeneği', 'Eklenen Ödenek',
                   'Düşülen Ödenek', 'Bildirilen Yıl Sonu Ödeneği', 'Harcama (Gerçekleşme)',
                   'İptal Edilen Ödenek', 'Ertesi Yıla Devreden Ödenek', 'Sapma Açıklaması')
REVENUE_HEADERS = ('Ekonomik Kod', 'Bütçe Tahmini', 'Tahsilat (Gerçekleşme)',
                   'Red ve İadeler', 'Sapma Açıklaması')
REVENUE_CODES = {'01', '03', '04', '05', '06', '08', '09'}
MONEY = re.compile(r'(?:-[ \t]*)?(?:0|[1-9]\d*|[1-9]\d{0,2}(?:\.\d{3})*),\d{2}\Z')
WRAPPED_MONEY = re.compile(MONEY.pattern.replace(r'\d{2}\Z', r'\d{1,2}\Z'))
MONEY_PREFIX = re.compile(MONEY.pattern.replace(r',\d{2}\Z', r'(?:,\d{1,2})?\Z'))

MAPPING = """## Sütun eşlemesi

| XLSX alanı | PDF kaynağı |
| --- | --- |
| Müdürlük No | CSV department_id; budget_code ile eşleşir |
| Ekonomik Kod | Yalnız düzey 1; gider 01–09 |
| Başlangıç Ödeneği | Geçen Yıldan Devreden Ödenek + Bütçe İle Verilen Ödenek |
| Eklenen Ödenek | Ek Ve Olağanüstü Verilen Ödenek + Aktarma Suretiyle Eklenen (+) |
| Düşülen Ödenek | Aktarma Düşülen (-) |
| Bildirilen Yıl Sonu Ödeneği | Net Ödenek Toplamı |
| Harcama (Gerçekleşme) | Bütçe Gideri Toplamı |
| İptal Edilen Ödenek | İptal Edilen Ödenek |
| Ertesi Yıla Devreden Ödenek | Gelecek Yıla Devrolan Ödenek |
| Bütçe Tahmini (gelir) | Bütçe ile Tahmin Edilen |
| Tahsilat (Gerçekleşme, gelir) | Yılı Tahsilatı (brüt) |
| Red ve İadeler (gelir) | Red ve İadeler |
| Sapma Açıklaması | Boş; operatör önizlemede tamamlar |

Gider düzey 1 tutarları fonksiyonel/finansal dallar üzerinden toplanır.
Alt ekonomik düzeyler ve ara toplamlar yeniden eklenmez.
Tutarlar kuruş kaybını önlemek için XLSX'e Türkçe sayı metni olarak yazılır;
mevcut XLSX önizlemesi bu biçimi okur. Boş hücre sıfır sayılmaz.
09 Red ve İadeler (-) plan kesintisi varsa eksi işareti kaynak mutabakatında
korunur; XLSX brüt tahmin içerir. Kesinti ve brüt/net köprüsü aşağıdaki kaynak
izlerinde ayrıca açıklanır; plan kesintisi gerçekleşen iade alanına taşınmaz.
"""


class ConversionError(ValueError):
    """An operator-actionable blocking conversion error."""


def norm(value):
    value = value.translate(str.maketrans('ıİ', 'iI')).lower()
    value = ''.join(c for c in unicodedata.normalize('NFKD', value)
                    if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', value))


def money(value):
    return f'{value:,.2f}'.translate(str.maketrans(',.', '.,'))


def safe(value):
    """Keep source text inside one Markdown table cell."""
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


@dataclass
class Row:
    cells: list[list[str]]
    where: str
    code_positions: list[list[int]] | None = None
    level_one_end: int | None = None
    check_prefixes: bool = False

    def text(self, column):
        return ' '.join(self.cells[column])

    def amounts(self, start, labels, *, revenue=False, notes=None):
        values = []
        wrapped = []
        for offset, label in enumerate(labels):
            parts = self.cells[start + offset]
            raw = ''.join(parts)
            pattern = WRAPPED_MONEY if revenue and len(parts) > 1 else MONEY
            if not pattern.fullmatch(raw):
                raise ConversionError(f'{self.where}, {label}: tutar boş veya okunamadı '
                                      f'({safe(" / ".join(parts)) or "boş"}). '
                                      'PDF hücresini kontrol edip dosyayı yeniden dönüştürün.')
            if len(parts) > 1:
                if not revenue:
                    raise ConversionError(f'{self.where}, {label}: bölünmüş tutar bağımsız '
                                          'satır eşitliğiyle doğrulanamıyor. Kaynak PDF düzenini kontrol edin.')
                wrapped.append((offset, label, parts, raw))
            value = Decimal(compact_sign(raw).replace('.', '').replace(',', '.'))
            values.append(value)
        if revenue:
            for label, actual, expected in (
                ('Toplam Tahakkuk = Devreden + Yılı Tahakkuku', values[3], values[1] + values[2]),
                ('Net = Tahsilat − Red', values[6], values[4] - values[5]),
            ):
                if actual != expected:
                    raise ConversionError(f'{self.where}: {label} tutarsız; PDF {money(actual)}, '
                                          f'hesaplanan {money(expected)}, fark {money(actual - expected)}. '
                                          'Bölünmüş rakamları ve kaynak satırı kontrol edin; tahmin yapılmadı.')
            for offset, label, parts, raw in wrapped:
                if offset in {1, 2, 3, 4, 5, 6}:
                    notes.append(f'{self.where}, {label}: {safe(" / ".join(parts))} → {raw}; '
                                 'ilgili satır eşitliği doğrulandı.')
        return values


def revenue_labels(year):
    return ('Bütçe ile Tahmin Edilen', f'{year - 1} Yılından Devreden Gelir',
            f'{year} Yılı Tahakkuku', 'Toplam Tahakkuk', f'{year} Yılı Tahsilatı',
            'Red ve İadeler', 'Yılı Net Tahsilatı', f'{year + 1} Yılına Devreden Tahakkuk')


def header_key(label):
    """Only documented spelling, unit, split-word and heading variants."""
    words = norm(label).split()
    words = [word for word in words if word != 'tl'
             and not re.fullmatch(r'\d{4}', word)]
    roman = ['i', 'ii', 'iii', 'iv', 'v']
    if words == roman or words == ['gelirin', 'kodu', *roman]:
        return 'gelirinkodu'
    key = ''.join(words)
    for transfer in ('eklenen', 'dusulen'):
        if key in {f'aktarma{transfer}', f'aktarmasuretiyle{transfer}', f'aktarmasuratiyle{transfer}'}:
            return transfer
    if key == 'tahsilattanredveiadeler':
        return 'redveiadeler'
    return key


def header_matches(actual, expected, year):
    years = re.findall(r'\b\d{4}\b', actual)
    expected_years = re.findall(r'\b\d{4}\b', expected) or [str(year)]
    return (all(value in expected_years for value in years)
            and header_key(actual) == header_key(expected))


NUMBER_FRAGMENT = re.compile(r'(?:-[ \t]*)?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?\Z|,\d{1,2}\Z')


def compact_sign(value):
    """Only whitespace immediately following a leading minus is ignorable."""
    return re.sub(r'^-[ \t]+', '-', value)


def numeric_spans(line, after=0):
    return [match for match in re.finditer(r'-[ \t]*\d[\d.,]*(?=\s|$)|\S+', line)
            if match.start() >= after and NUMBER_FRAGMENT.fullmatch(match.group())]


def decimal_fragments(line, after):
    """Recognize suffix-only baselines; record text is never a continuation."""
    if re.search(r'[^\W\d_]', line):
        return []
    words = [word for word in re.finditer(r'\S+', line) if word.start() >= after]
    if words and all(re.fullmatch(r',\d{1,2}|\d', word.group()) for word in words):
        return words
    return []


def description_anchor(lines, where):
    for line in lines:
        for word in re.finditer(r'\S+', line):
            if norm(word.group()) == 'aciklama':
                return word.start()
    raise ConversionError(f'{where}: Açıklama başlığı bulunamadı. Başlıklı metin PDF kullanın.')


def financial_samples(lines, count, after):
    """Only complete amount-bearing baselines establish monetary column order.

    Code/date/title lines and text-only continuations provide no geometry.
    Partial monetary continuations are checked against the resulting bands.
    """
    result = []
    for i, line in enumerate(lines):
        if decimal_fragments(line, after):
            continue
        spans = numeric_spans(line, after)
        if len(spans) >= count:
            result.append((i, spans[-count:]))
    return result


def code_fragment(line, after):
    match = re.fullmatch(r'\s*(\d{1,2})\s*', line)
    return match if match and match.end(1) <= after else None


def normalize_revenue_code_prefixes(lines, samples, after, where, notes):
    """Place a lone code above a baseline in that baseline's empty code band.

    Keep all original line indexes and x positions, so the normal code-column
    checks still prove I-level placement, alignment and the final two digits.
    """
    result = list(lines)
    baselines = {index for index, _ in samples}
    for index, spans in samples:
        if not index or numeric_spans(lines[index][:after]):
            continue
        if norm(lines[index][:spans[0].start()]) in {'toplam', 'genel toplam'}:
            continue
        fragment = code_fragment(lines[index - 1], after)
        if fragment is None:
            continue
        if lines[index][:fragment.end(1)].strip():
            continue
        previous = numeric_spans(result[index - 2][:after]) if index - 2 in baselines else []
        if index - 2 in baselines and (not previous or any(
                not re.fullmatch(r'\d{2}', token.group()) for token in previous)):
            raise ConversionError(f'{where}, satır {index}: kod parçası önceki ve sonraki '
                                  'tutar satırına aynı yakınlıkta. Kaynak kod konumlarını kontrol '
                                  'edin; kayıtlar arasında kod tahmin edilmedi.')
        left, right = fragment.span(1)
        result[index] = lines[index][:left] + fragment[1] + lines[index][right:]
        result[index - 1] = ''
        if notes is not None:
            notes.append(f'{where}, satır {index}: üst kod parçası {fragment[1]}, x={left}; '
                         f'satır {index + 1} tutar kaydının boş kod alanına aynı konumda bağlandı. '
                         'Alt parça ve I düzeyi konumu ayrıca doğrulanır.')
    return result


def normalize_decimal_lines(body, samples, after, where):
    """Join uniquely placed suffixes before geometry or monetary validation.

    Baseline amount columns establish provisional position bands. Horizontal
    order, bounded column distance and the preceding number's syntax must
    identify exactly one assignment; no numerical digit is inferred.
    """
    count = len(samples[0][1])
    anchors = [(min(row[i].end() for _, row in samples) + max(row[i].end() for _, row in samples)) / 2
               for i in range(count)]
    pitches = [min(abs(anchor - other) for j, other in enumerate(anchors) if j != i)
               for i, anchor in enumerate(anchors)]
    baselines = {i + 1: spans for i, spans in samples}
    values = {}
    result = []
    active = None
    integer = MONEY.pattern.rsplit(',', 1)[0]
    for line_no, line in body:
        spans = baselines.get(line_no)
        if spans is not None:
            values[line_no] = [[span.group()] for span in spans]
            active = line_no
            result.append((line_no, line))
            continue
        if code_fragment(line, after):
            # The lower code digit can sit between the amounts and suffixes.
            # It remains a code fragment; it neither ends nor supplies money.
            result.append((line_no, line))
            continue
        suffixes = decimal_fragments(line, after)
        if not suffixes:
            # A new incomplete coded record cannot borrow the prior record's
            # amounts. Description-only wraps keep the active record.
            if re.search(r'[^\W\d_]', line) and numeric_spans(line[:after]):
                active = None
            result.append((line_no, line))
            continue
        if active is None:
            raise ConversionError(f'{where}, satır {line_no}: sahipsiz ondalık devamı. '
                                  'Önceki kayıt ve tutar parçalarını kontrol edin.')
        previous = values[active]

        def compatible(column, fragment):
            raw = ''.join(previous[column])
            suffix = fragment.group()
            syntax = (re.fullmatch(integer, raw) if suffix.startswith(',') else
                      re.fullmatch(integer + r',\d', raw))
            return bool(syntax) and abs(fragment.end() - anchors[column]) < pitches[column]

        @lru_cache(maxsize=None)
        def assignments(index, first):
            if index == len(suffixes):
                return ((),)
            matches = []
            for column in range(first, count):
                if compatible(column, suffixes[index]):
                    for tail in assignments(index + 1, column + 1):
                        matches.append((column, *tail))
                        if len(matches) == 2:
                            return tuple(matches)
            return tuple(matches)

        matches = assignments(0, 0)
        if len(matches) != 1:
            raise ConversionError(f'{where}, satır {line_no}: ondalık devamı önceki tutarın '
                                  'aynı sütunuyla tekil eşleşmedi. PDF hücre konumlarını ve '
                                  'önceki ,d parçasını kontrol edin; tahmin yapılmadı.')
        stripped = list(line)
        for column, fragment in zip(matches[0], suffixes):
            previous[column].append(fragment.group())
            stripped[fragment.start():fragment.end()] = ' ' * (fragment.end() - fragment.start())
        # Preserve separately positioned code fragments (e.g. 0 / 1).
        if ''.join(stripped).strip():
            result.append((line_no, ''.join(stripped)))
    return result, values


def header_bounds(lines, body, samples, expected, where, code_count, year, amounts=None):
    """Fit column bands to data-only gutters and the complete header schema.

    Centred words need not share an x0 or overlap other header lines. Each
    word is assigned by majority overlap with its band. Header whitespace
    never constrains the data gutters, and text-only wraps never enter them.
    """
    fragments = []
    level_one_end = None
    for line in lines:
        numerals = list(re.finditer(r'\b(?:III|II|IV|I|V)\b', line))
        if code_count == 1 and [match.group() for match in numerals] == ['I', 'II', 'III', 'IV', 'V']:
            level_one_end = numerals[1].start()
        for word in re.finditer(r'\S+', line):
            if norm(word.group()) in {'tl', 'aktarma', 'suratiyle', 'suretiyle'}:
                continue
            fragments.append((word.start(), word.end(), word.group()))
    if not fragments or not samples:
        raise ConversionError(f'{where}: başlık bloğu veya tutarlı tutar satırı bulunamadı. '
                              'Tam metin PDF kullanın.')
    count = len(samples[0])
    groups = [(min(row[i].start() for row in samples), max(row[i].end() for row in samples))
              for i in range(count)]
    first_money = code_count + 1
    # Exclude prose crossing numeric columns. Keep full records, numeric-only
    # suffix baselines, and partial records whose monetary tail is numeric.
    after = description_anchor(lines, where)
    data = [(i, line) for i, line in body if numeric_spans(line, after)
            and not re.search(r'[^\W\d_]', line[groups[0][0]:])]
    if not data:
        raise ConversionError(f'{where}: tutar taşıyan veri satırı yok. PDF tutarlarını kontrol edin.')
    width = max([len(line) for _, line in data] + [right for _, right, _ in fragments]) + 1

    def gutter(position):
        return all(not line[position - 1:position + 1].strip() for _, line in data)

    candidates = []
    for column in range(len(expected) - 1):
        if column < first_money:
            low, high = 1, groups[0][0]
        else:
            i = column - first_money
            low, high = groups[i][1], groups[i + 1][0]
        candidates.append(tuple(position for position in range(low, high + 1) if gutter(position)))

    @lru_cache(maxsize=None)
    def label(left, right):
        words = [word for start, end, word in fragments
                 if 2 * max(0, min(end, right) - max(start, left)) > end - start]
        return ' '.join(words)

    @lru_cache(maxsize=None)
    def valid(column, left, right):
        if not header_matches(label(left, right), expected[column], year):
            return False
        cells = [line[left:right].strip() for _, line in data]
        if column < code_count:
            pattern = (r'\d{1,2}(?:[ .]+\d{1,2}){0,4}' if code_count == 1 else
                       (r'46(?:[ .]+\d{1,2}){0,3}',
                        r'\d{2}(?:[ .]+\d{1,2}){0,3}', r'\d',
                        r'\d{2}(?:[ .]+\d{1,2}){0,3}')[column])
            return all(not cell or re.fullmatch(pattern, cell)
                       or (code_count == 1 and norm(cell) in {'toplam', 'genel toplam'})
                       for cell in cells)
        if column == code_count:
            return all(not re.search(r'\d,\d{2}(?:\s|$)', cell) for cell in cells)
        if not (any(cells) and all(not cell or re.fullmatch(r'(?:-[ \t]*)?[\d.,]+', cell) for cell in cells)):
            return False
        if amounts is not None and column < len(expected) - 1:
            for line_no, _ in data:
                if line_no in amounts:
                    parts = amounts[line_no][column - first_money]
                    pattern = WRAPPED_MONEY if len(parts) > 1 else MONEY
                    if not pattern.fullmatch(''.join(parts)):
                        return False
        return True

    @lru_cache(maxsize=None)
    def solve(column, left):
        if column == len(expected) - 1:
            return () if valid(column, left, width) else None
        for right in candidates[column]:
            if right <= left or not valid(column, left, right):
                continue
            tail = solve(column + 1, right)
            if tail is not None:
                return (right, *tail)
        return None

    solution = solve(0, 0)
    if solution is None:
        raise ConversionError(f'{where}: sütun başlıkları, veri hücreleri veya rapor yılı doğrulanamadı. '
                              'Başlık adayını ve PDF sütunlarını kontrol edin; belirsiz eşleme yapılmadı.')
    bounds = [0, *solution]
    for start, end, word in fragments:
        matches = [column for column, (left, right) in enumerate(zip(bounds, [*bounds[1:], width]))
                   if 2 * max(0, min(end, right) - max(start, left)) > end - start]
        if len(matches) != 1:
            raise ConversionError(f'{where}: başlık parçası yerleştirilemedi ({safe(word)}). '
                                  'PDF başlık hücrelerini kontrol edin.')
    return bounds, level_one_end


def read_metadata(lines, where, metadata, year):
    """Return the end of the title block, retaining every later header line."""
    end = -1
    for i, line in enumerate(lines):
        text = norm(line)
        if 'kesin hesap' in text:
            end = i
        for key, label in (('start', 'baslangic tarihi'), ('end', 'bitis tarihi')):
            if label not in text:
                continue
            end = i
            match = re.search(r'\b' + label + r' (\d{2}) (\d{2}) (\d{4})\b', text)
            try:
                if match is None:
                    raise ValueError()
                day, month, source_year = map(int, match.groups())
                value = date(source_year, month, day)
                if value.year != year:
                    raise ValueError()
            except ValueError:
                display = 'Başlangıç Tarihi' if key == 'start' else 'Bitiş Tarihi'
                raise ConversionError(f'{where}, satır {i + 1}: {display} okunamadı veya '
                                      f'--year {year} ile uyuşmuyor. Kaynak tarihini ve yılı kontrol edin.') from None
            metadata[key].append((value, f'{where}, satır {i + 1}'))
        if 'donemi' in text:
            end = i
            match = re.search(r'\bdonemi (\d{4})\b', text)
            if match is None or int(match[1]) != year:
                raise ConversionError(f'{where}, satır {i + 1}: Dönemi ile --year {year} '
                                      'uyuşmuyor. Kaynak dönemini kontrol edin.')
            metadata['period'].append((year, where))
    return end + 1


def validate_metadata(metadata, where, expense, notes):
    for key, label in (('start', 'Başlangıç Tarihi'), ('end', 'Bitiş Tarihi')):
        if not metadata[key]:
            raise ConversionError(f'{where}: {label} eksik. Tarihleri içeren tam kesin hesap PDF kullanın.')
        if len({value for value, _ in metadata[key]}) != 1:
            raise ConversionError(f'{metadata[key][-1][1]}: {label} sayfalar arasında tutarsız. '
                                  'Kaynak tarihlerini kontrol edin.')
    start, end = metadata['start'][0][0], metadata['end'][0][0]
    if start > end:
        raise ConversionError(f'{where}: Başlangıç Tarihi, Bitiş Tarihi sonrasında. Kaynak tarihlerini düzeltin.')
    if not expense and not metadata['period']:
        raise ConversionError(f'{where}: Dönemi eksik. Dönem bilgisi içeren tam gelir PDF kullanın.')
    if notes is not None:
        notes.append(f'{safe(where)}: Başlangıç Tarihi {start:%d/%m/%Y}, Bitiş Tarihi {end:%d/%m/%Y}; '
                     'kaynak yılı ve dönem doğrulandı.')


def joined_revenue_code(row):
    if row.level_one_end is not None and any(positions and positions[0] >= row.level_one_end
                                            for positions in row.code_positions or []):
        raise ConversionError(f'{row.where}: gelir kodunda I düzeyi eksik; parçalar sonraki alt sütunda. '
                              'Kaynak PDF kod sütunlarını kontrol edin; üst kod tahmin edilmedi.')
    parts = [codes(part) for part in row.cells[0]]
    if len(parts) == 1:
        return row.text(0)
    if not parts or len({len(part) for part in parts}) != 1:
        raise ConversionError(f'{row.where}: bölünmüş gelir kodunun sütunları belirsiz. PDF kodlarını kontrol edin.')
    if row.code_positions is None or any(max(column) - min(column) > 1
                                         for column in zip(*row.code_positions)):
        raise ConversionError(f'{row.where}: gelir kodu parçaları aynı alt sütunda değil. '
                              'PDF kod konumlarını kontrol edin.')
    result = [''.join(column) for column in zip(*parts)]
    if not all(re.fullmatch(r'\d{2}', part) for part in result):
        raise ConversionError(f'{row.where}: bölünmüş gelir kodu doğrulanamadı. PDF kodlarını kontrol edin.')
    return ' '.join(result)


def header_error(error, header, start, where, notes):
    candidate = '\n'.join(f'    {i}: {line}' for i, line in enumerate(header, start + 1))
    if notes is not None:
        notes.append(f'\n### Başlık adayı — {safe(where)}\n\n{candidate}\n')
    return ConversionError(f'{error} Başlık adayı: {safe(" / ".join(header))}')


def signature_block(lines):
    signatures = [('duzenleyen', 'muhasebe yetkilisi'),
                  ('adi soyadi', 'adi soyadi'), ('tarih', 'tarih'), ('imza', 'imza')]
    if len(lines) != 4:
        return False
    for index, (line, expected) in enumerate(zip(lines, signatures)):
        cells = re.split(r'[ \t]{2,}', line.strip())
        if len(cells) != 2 or tuple(map(norm, cells)) != expected:
            return False
        # Reject digits, amounts, filled-in names, and unrecognised punctuation.
        for cell in cells:
            if (not re.fullmatch(r'[^\W\d_]+(?: [^\W\d_]+)*' + (r'\s*:' if index else ''),
                                 cell)):
                return False
    return True


def signature_closing_page(lines, previous_header, previous_preamble, where, metadata, year):
    """Accept only the documented two-column signature block after a known header.

    A data-less page cannot establish new column geometry. Its complete header
    must therefore repeat the preceding validated page's header text/order.
    """
    content = [line for line in lines if line.strip() and not re.fullmatch(
        r'\s*Sayfa\s+\d+(?:\s*/\s*\d+)?\s*', line, re.IGNORECASE)]
    if not previous_header or not signature_block(content[-4:]):
        return False
    prefix = content[:-4]
    start = read_metadata(prefix, where, metadata, year)
    validate_metadata(metadata, where, True, None)
    if start and [' '.join(line.split()) for line in prefix[:start]] != previous_preamble:
        return False
    while start < len(prefix) and re.fullmatch(r'\s*\d{1,3}\s*', prefix[start]):
        start += 1
    return ([' '.join(line.split()) for line in prefix[start:]]
            == [' '.join(line.split()) for line in previous_header if line.strip()])


def revenue_total_footer(lines, where):
    """Isolate the documented truncated check row before fitting data columns.

    Ordinary exact totals and their decimal continuations retain the existing
    path. No footer text is discarded unless its whole shape is recognised.
    """
    label = re.compile(r'^\s*(?:GENEL\s+)?TOPLAM(?:\s|$)', re.IGNORECASE)
    indexes = [i for i, line in enumerate(lines) if label.match(line)]
    if len(indexes) > 1:
        raise ConversionError(f'{where}: gelir toplamı yinelenmiş. Tek toplamlı PDF kullanın.')
    if not indexes:
        return lines, None
    start = indexes[0]
    tail = [(i + 1, line) for i, line in enumerate(lines) if i >= start and line.strip()
            and not re.fullmatch(r'\s*Sayfa\s+\d+(?:\s*/\s*\d+)?\s*', line, re.IGNORECASE)]
    signatures = signature_block([line for _, line in tail[-4:]])
    if signatures:
        tail = tail[:-4]
    text = label.sub('', tail[0][1]) + ' ' + ' '.join(line for _, line in tail[1:])
    tokens = re.findall(r'(?:-[ \t]*)?\S+', text)
    truncated = len(tokens) == 9 and any(not MONEY.fullmatch(raw) for raw in tokens[:8])
    if not signatures and not truncated:
        return lines, None
    if any(not MONEY_PREFIX.fullmatch(raw) for raw in tokens):
        raise ConversionError(f'{where}, satır {start + 1}: TOPLAM altbilgisinde tanınmayan '
                              'metin veya tutar var. Kaynak toplamını ve imza bloğunu kontrol edin.')
    return [*lines[:start], *([''] * (len(lines) - start))], tail


def display_transform(page, where):
    """Map unrotated PDF user space to displayed bottom-left page space."""
    left, bottom, right, top = map(float, page.mediabox)
    rotation = page.rotation
    matrices = {
        0: (1, 0, 0, 1, -left, -bottom),
        90: (0, -1, 1, 0, -bottom, right),
        180: (-1, 0, 0, -1, right, top),
        270: (0, 1, -1, 0, top, -left),
    }
    if rotation not in matrices:
        raise ConversionError(f'{where}: desteklenmeyen sayfa dönüşü {rotation}. '
                              '0, 90, 180 veya 270 derece dönüşlü PDF kullanın.')
    return Transformation(matrices[rotation])


def total_check_row(page, footer, bounds, where, year):
    """Bucket printed prefixes with the validated data bands, then verify y."""
    labels = (*revenue_labels(year), 'Oran')
    columns = [[] for _ in labels]
    total_labels = []
    for line_no, line in footer:
        cells = [line[left:right].strip() for left, right in
                 zip(bounds, [*bounds[1:], len(line) + 1])]
        if any(len(line) > b and line[b - 1:b + 1].strip()
               and not line[b - 1].isspace() and not line[b].isspace() for b in bounds[1:]):
            raise ConversionError(f'{where}, satır {line_no}: TOPLAM hücre sınırı belirsiz. '
                                  'Kaynak toplam sütunlarını kontrol edin.')
        total_labels.extend(cell for cell in cells[:2] if cell)
        for column, cell in zip(columns, cells[2:]):
            if cell:
                column.append(cell)
    if len(total_labels) != 1 or norm(total_labels[0]) not in {'toplam', 'genel toplam'}:
        raise ConversionError(f'{where}: TOPLAM etiketi veya kod alanı belirsiz. Kaynak altbilgisini kontrol edin.')
    raw = []
    for label, parts in zip(labels, columns):
        if len(parts) != 1 or not MONEY_PREFIX.fullmatch(parts[0]):
            raise ConversionError(f'{where}, TOPLAM, {label}: basılı tutar eksik veya yinelenmiş. '
                                  'Kaynak toplam hücresini kontrol edin; boş sıfır sayılmadı.')
        raw.append(parts[0])

    fragments = []
    transform = display_transform(page, where)
    def visit(text, cm, tm, font, size):
        if text.strip():
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            x, y = transform.apply_on((x, y))
            fragments.append((text.strip(), x, y))
    page.extract_text(visitor_text=visit)
    # The column header can itself contain a separate "Toplam" fragment.
    # Only the label owning the nine already-parsed footer cells is eligible.
    positions = []
    for text, label_x, label_y in fragments:
        if norm(text) not in {'toplam', 'genel toplam'}:
            continue
        printed = sorted((x, y, value) for value, x, y in fragments
                         if x > label_x and y <= label_y + .01 and MONEY_PREFIX.fullmatch(value))
        if (len(printed) == 9
                and [compact_sign(value) for _, _, value in printed] == list(map(compact_sign, raw))):
            positions.append((label_x, label_y, printed))
    if len(positions) != 1:
        raise ConversionError(f'{where}: TOPLAM konumu tekil değil. Kaynak toplam etiketini kontrol edin.')
    _, label_y, printed = positions[0]
    for offset, ((_, y, _), label) in enumerate(zip(printed, labels)):
        if label_y - y > 6.01 or (offset in {5, 8} and abs(label_y - y) > .01):
            raise ConversionError(f'{where}, TOPLAM, {label}: tutar etiket satırında veya en fazla '
                                  '6 punto altında değil. Kaynak toplam yerleşimini kontrol edin.')
        if offset in {5, 8} and not MONEY.fullmatch(raw[offset]):
            raise ConversionError(f'{where}, TOPLAM, {label}: bu hücre tam iki ondalıkla basılmalı. '
                                  'Tam toplamı içeren PDF kullanın.')
    return Row([[], ['TOPLAM'], *[[value] for value in raw]],
               f'{where}, satır {footer[0][0]}, TOPLAM', check_prefixes=True)


def pdf_rows(path, kind, year, notes=None):
    expense = kind == 'expenditure'
    expected = (('Kurum Kodu', 'Fonksiyonel Kodu', 'Finansal Kodu', 'Ekonomik Kodu',
                 'Açıklama', *EXPENSE_SOURCE) if expense else
                ('Gelirin Kodu', 'Açıklama', *revenue_labels(year), 'Oran'))
    code_count = 4 if expense else 1
    description = code_count
    rows = []
    previous_header = None
    previous_preamble = None
    metadata = {'start': [], 'end': [], 'period': []}
    with path.open('rb') as source:
        reader = PdfReader(source)
        if reader.is_encrypted:
            raise ConversionError(f'{path.name}: şifreli PDF okunamadı. Şifresiz metin PDF kullanın.')
        for page_no, page in enumerate(reader.pages, 1):
            where = f'{path.name}, sayfa {page_no}'
            # pypdf layout extraction ignores /Rotate. Give it the same frame
            # as the visitor checks without modifying the reader's source page.
            transform = display_transform(page, where)
            layout_page = copy(page)
            layout_page.indirect_reference = None
            layout_page.add_transformation(transform)
            layout_page.rotation = 0
            lines = layout_page.extract_text(extraction_mode='layout',
                                      layout_mode_space_vertically=False).splitlines()
            footer = None
            if not expense:
                lines, footer = revenue_total_footer(lines, where)
            try:
                after = description_anchor(lines, where)
                samples = financial_samples(lines, 11 if expense else 9, after)
                if not samples:
                    if (expense and page_no == len(reader.pages) and rows
                            and signature_closing_page(lines, previous_header, previous_preamble,
                                                       where, metadata, year)):
                        if notes is not None:
                            notes.append(f'{where}: doğrulanmış başlık ve yalnız iki sütunlu imza '
                                         'bloğu içeren imza kapanış sayfası atlandı; kod/tutar yok.')
                        continue
                    raise ConversionError(f'{where}: kodlu veri satırı bulunamadı. PDF tablosunu kontrol edin.')
            except ConversionError as exc:
                raise header_error(exc, lines[:12], 0, where, notes) from None
            body = samples[0][0]
            if not expense:
                lines = normalize_revenue_code_prefixes(lines, samples, after, where, notes)
            start = read_metadata(lines[:body], where, metadata, year)
            preamble = [' '.join(line.split()) for line in lines[:start] if line.strip()]
            # Short bare form/page counters precede the table, while four-digit
            # revenue year labels remain part of the actual header block.
            while start < body and (not lines[start].strip()
                                   or re.fullmatch(r'\s*\d{1,3}\s*', lines[start])):
                start += 1
            header = lines[start:body]
            body_lines = [(i, line) for i, line in enumerate(lines[body:], body + 1)
                          if line.strip() and not re.fullmatch(
                              r'\s*Sayfa\s+\d+(?:\s*/\s*\d+)?\s*', line, re.IGNORECASE)]
            located = f'{where}, satırlar {body + 1}–{len(lines)}'
            amounts = None
            if not expense:
                body_lines, amounts = normalize_decimal_lines(body_lines, samples, after, where)
            try:
                bounds, level_one_end = header_bounds(header, body_lines,
                    [spans for _, spans in samples], expected, located, code_count, year, amounts)
            except ConversionError as exc:
                raise header_error(exc, header, start, where, notes) from None
            previous_header = header
            previous_preamble = preamble
            current = None
            for line_no, line in body_lines:
                first = len(line) - len(line.lstrip())
                money_start = bounds[description + 1]
                # A description-only continuation may overflow all monetary
                # bands. Its starting position still belongs to Açıklama.
                if (bounds[description] <= first < money_start
                        and not any(line[left:right].strip() for left, right in
                                    zip(bounds[:description], bounds[1:description + 1]))
                        and not re.search(r'\d,\d{1,2}(?:\s|$)|,\d{1,2}(?:\s|$)', line[money_start:])
                        and not (numeric_spans(line, money_start)
                                 and not re.search(r'[^\W\d_]', line[money_start:]))):
                    if current is None:
                        raise ConversionError(f'{where}, satır {line_no}: sahipsiz açıklama. PDF satırını kontrol edin.')
                    current.cells[description].append(line[bounds[description]:].strip())
                    continue
                cells = [line[left:right].strip()
                         for left, right in zip(bounds, [*bounds[1:], len(line) + 1])]
                # Reject text crossing a detected gutter; silently shifting a
                # digit between cells would invalidate the monetary evidence.
                if any(len(line) > b and line[b - 1:b + 1].strip()
                       and not line[b - 1].isspace() and not line[b].isspace()
                       for b in bounds[1:]):
                    raise ConversionError(f'{where}, satır {line_no}: hücre sınırı belirsiz. '
                                          'PDF sütun düzenini kontrol edin.')
                codes = cells[:code_count]
                code_positions = [match.start() for match in re.finditer(r'\d+', line[:bounds[1]])]
                is_total = norm(cells[description]) in {'toplam', 'genel toplam'}
                if not expense and norm(cells[0]) in {'toplam', 'genel toplam'}:
                    if cells[description] and not is_total:
                        raise ConversionError(f'{where}, satır {line_no}: toplam etiketi belirsiz. '
                                              'PDF toplam satırını kontrol edin.')
                    cells[description], cells[0] = cells[0], ''
                    codes, is_total = [''], True
                new_row = (any(codes) or is_total) if expense else bool(cells[description] or is_total)
                if new_row:
                    if not expense and not any(codes) and not is_total:
                        raise ConversionError(f'{where}, satır {line_no}: gelir kodu eksik. PDF satırını kontrol edin.')
                    current = Row([[cell] if cell else [] for cell in cells],
                                  f'{where}, satır {line_no}',
                                  [code_positions] if not expense and cells[0] else [], level_one_end)
                    if amounts is not None and line_no in amounts:
                        current.cells[description + 1:] = amounts[line_no]
                    rows.append(current)
                elif current is not None:
                    for index, cell in enumerate(cells):
                        if cell:
                            current.cells[index].append(cell)
                    if not expense and cells[0]:
                        current.code_positions.append(code_positions)
                else:
                    raise ConversionError(f'{where}, satır {line_no}: sahipsiz hücre. PDF düzenini kontrol edin.')
            if footer is not None:
                rows.append(total_check_row(page, footer, bounds, where, year))
    if not rows:
        raise ConversionError(f'{path.name}: veri bulunamadı. Metin PDF kullanın.')
    validate_metadata(metadata, path.name, expense, notes)
    for row in rows:
        if not expense and row.cells[0]:
            row.cells[0] = [joined_revenue_code(row)]
        if any(row.text(i) and not re.fullmatch(r'\d+(?:[ .]+\d+)*', row.text(i))
               for i in range(code_count)):
            raise ConversionError(f'{row.where}: kod okunamadı. PDF kod alanlarını kontrol edin.')
    return rows


def load_departments(path):
    result = {}
    ids = set()
    columns = ('budget_code', 'department_id', 'department_name')
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or len(reader.fieldnames) != 3 or set(reader.fieldnames) != set(columns):
            raise ConversionError('Müdürlük CSV başlıkları geçersiz. '
                                  'budget_code,department_id,department_name sütunlarını kullanın.')
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ConversionError(f'CSV {line}. satır: sütun sayısı geçersiz. Üç alanı doldurun.')
            code, dep_id, name = (row[key].strip() for key in columns)
            if not re.fullmatch(r'\d{1,2}', code) or not re.fullmatch(r'[1-9]\d*', dep_id) or not name:
                raise ConversionError(f'CSV {line}. satır: müdürlük eşlemesi geçersiz. '
                                      'Bütçe kodunu, pozitif müdürlük numarasını ve adını kontrol edin.')
            code = code.zfill(2)
            if code in result or int(dep_id) in ids:
                raise ConversionError(f'CSV {line}. satır: yinelenen bütçe kodu veya müdürlük numarası '
                                      f'({code}). Tek ve açık bir eşleme sağlayın; birleşim yapılmadı.')
            result[code] = (int(dep_id), name)
            ids.add(int(dep_id))
    if not result:
        raise ConversionError('Müdürlük CSV boş. Rapor yılına ait kurum yapısı eşlemesini dışa aktarın.')
    return result


def codes(text):
    return tuple(re.split(r'[ .]+', text)) if text else ()


def sum_vectors(vectors, size):
    result = [Decimal(0)] * size
    for vector in vectors:
        result = [a + b for a, b in zip(result, vector)]
    return result


def reconcile(label, actual, expected, labels, notes, errors):
    notes.append(f'\n### {safe(label)}\n\n| Sütun | PDF | Hesaplanan | Fark (hesaplanan − PDF) |\n'
                 '| --- | ---: | ---: | ---: |')
    for name, value, target in zip(labels, actual, expected):
        diff = value - target
        notes.append(f'| {name} | {money(target)} | {money(value)} | {money(diff)} |')
        if diff:
            errors.append(f'{label}, {name}: PDF {money(target)}, hesaplanan {money(value)}, '
                          f'fark {money(diff)}. Kaynak toplamları ve tüm kod dallarını kontrol edin.')


def expenditure(rows, departments, notes, errors):
    totals = {}
    names = {}
    emitted = defaultdict(list)
    municipality = None
    prefix = None
    department = None
    function = ()
    fund = ()
    seen = set()
    for row in rows:
        institution, new_function, new_fund, economic = [codes(row.text(i)) for i in range(4)]
        if institution:
            if len(institution) not in {1, 2, 3, 4} or institution[0] != '46':
                raise ConversionError(f'{row.where}: kurum kodu desteklenmiyor. 46 kurum hiyerarşisini kontrol edin.')
            if len(institution) == 3:
                if municipality is not None:
                    raise ConversionError(f'{row.where}: birden çok belediye toplamı var. Tek belediye PDF kullanın.')
                municipality = row.amounts(5, EXPENSE_SOURCE)
                prefix = institution
            if prefix and institution[:min(3, len(institution))] != prefix[:len(institution)]:
                raise ConversionError(f'{row.where}: kurum kodu belediye kapsamıyla uyuşmuyor. '
                                      'Tek belediyeye ait kurum kodlarını kontrol edin.')
            if len(institution) < 4:
                department, function, fund = None, (), ()
            if len(institution) == 4 and not any((new_function, new_fund, economic)):
                if prefix != institution[:3]:
                    raise ConversionError(f'{row.where}: müdürlük belediye toplamına bağlı değil. Kurum kodlarını kontrol edin.')
                department = institution[-1].zfill(2)
                if department in totals:
                    raise ConversionError(f'{row.where}: {department} müdürlük toplamı yinelenmiş. '
                                          'Tekrarlanan sayfa/satırı kaynakta kontrol edin.')
                totals[department] = row.amounts(5, EXPENSE_SOURCE)
                names[department] = row.text(4)
                function, fund = (), ()
            elif len(institution) == 4 and institution[-1].zfill(2) != department:
                raise ConversionError(f'{row.where}: müdürlük üst toplamı eksik. PDF hiyerarşisini kontrol edin.')
            elif len(institution) < 3 and (new_function or new_fund or economic):
                raise ConversionError(f'{row.where}: kurum hiyerarşisi belirsiz. PDF düzenini kontrol edin.')
        if new_function:
            function, fund = new_function, ()
        if new_fund:
            fund = new_fund
        if not economic:
            continue
        if len(economic) > 1:
            continue
        code = economic[0]
        if code not in {f'{n:02}' for n in range(1, 10)}:
            raise ConversionError(f'{row.where}: bilinmeyen gider ekonomik kodu {code}. Düzey 1 kodunu kontrol edin.')
        if department is None or len(function) != 4 or len(fund) != 1:
            raise ConversionError(f'{row.where}, ekonomik kod {code}: müdürlük/fonksiyon/finansman '
                                  'bağlamı eksik. PDF hiyerarşisini kontrol edin.')
        key = department, function, fund, code
        if key in seen:
            raise ConversionError(f'{row.where}: yinelenen ekonomik dal {safe(key)}. '
                                  'Tekrarlanan satırı kontrol edin; sessiz birleşim yapılmadı.')
        seen.add(key)
        emitted[department, code].append(row.amounts(5, EXPENSE_SOURCE))
    if municipality is None or not totals or not emitted:
        raise ConversionError('Gider: belediye/müdürlük toplamı veya ekonomik satırlar eksik. Tam PDF kullanın.')
    for department, expected in totals.items():
        vectors = [v for (dep, _), group in emitted.items() if dep == department for v in group]
        if not vectors:
            errors.append(f'Müdürlük {department} {names[department]}: ekonomik satır yok. Tam PDF kullanın.')
        if department not in departments:
            errors.append(f'Bilinmeyen bütçe kodu {department}: {names[department]}. '
                          'Rapor yılına ait CSV eşlemesini tamamlayın; satır atılmadı.')
        else:
            dep_id, dep_name = departments[department]
            notes.append(f'Müdürlük {department}: {safe(names[department])} → '
                         f'{dep_id} ({safe(dep_name)}).')
        reconcile(f'Müdürlük {department} {names[department]}', sum_vectors(vectors, 11),
                  expected, EXPENSE_SOURCE, notes, errors)
    reconcile('Belediye ' + ' '.join(prefix), sum_vectors(totals.values(), 11), municipality,
              EXPENSE_SOURCE, notes, errors)
    output = []
    for (dep, code), vectors in sorted(emitted.items()):
        v = sum_vectors(vectors, 11)
        mapped = [v[0] + v[1], v[2] + v[3], v[4], v[5], v[6], v[9], v[10]]
        validate_output(mapped, f'Müdürlük {dep}, ekonomik kod {code}')
        if mapped[0] + mapped[1] - mapped[2] != mapped[3]:
            errors.append(f'Müdürlük {dep}, ekonomik kod {code}: yıl sonu ödeneği '
                          'başlangıç + eklenen − düşülen ile uyuşmuyor. Kaynak ödenekleri kontrol edin.')
        if dep in departments:
            output.append([departments[dep][0], code, *map(money, mapped), ''])
    return output


def check_total_prefixes(row, summed, year, notes, errors):
    if summed[0] <= 0:
        raise ConversionError(f'{row.where}, Oran: toplam bütçe tahmini pozitif değil; '
                              'yüzde doğrulanamıyor. Kaynak toplam ve tahminleri kontrol edin.')
    expected = [*summed, (summed[6] / summed[0] * 100).quantize(Decimal('.01'))]
    labels = (*revenue_labels(year), 'Oran')
    matches = set()
    notes.extend(['\n### TOPLAM önek kontrolü\n',
                  'Bu satır kontrol altbilgisidir; XLSX verisi yapılmadı, eksik haneler tahmin edilmedi. '
                  'Basılmayan ondalıklar bağımsız olarak doğrulanamaz. Oran = net tahsilat / bütçe tahmini × 100.',
                  '\n| Sütun | Basılı PDF | Düzey 1 toplamı | Kontrol |', '| --- | --- | --- | --- |'])
    for offset, (label, value) in enumerate(zip(labels, expected)):
        raw = compact_sign(row.text(2 + offset))
        formatted = money(value)
        complete = bool(MONEY.fullmatch(raw))
        matched = (Decimal(raw.replace('.', '').replace(',', '.')) == value if complete else
                   raw.split(',')[0] == formatted.split(',')[0] and formatted.startswith(raw))
        status = 'tam tutar eşit' if complete else 'basılı önek eşit; kalan haneler PDF’de yok'
        if not matched:
            status = 'UYUŞMAZLIK'
            errors.append(f'{row.where}, {label}: TOPLAM öneki uyuşmuyor; basılı PDF {raw}, '
                          f'düzey 1 toplamı {formatted}. Tam sayı kısmını ve basılı ondalıkları '
                          'kontrol edin; eksik rakam tahmin edilmedi.')
        else:
            matches.add(offset)
        notes.append(f'| {label} | {raw} | {formatted} | {status} |')
    return matches


def revenue(rows, year, notes, errors):
    labels = revenue_labels(year)
    emitted = {}
    total = None
    prefix_total = None
    details = []
    pending = []
    planned_deduction = None
    for row in rows:
        if row.check_prefixes:
            if total is not None or prefix_total is not None:
                raise ConversionError(f'{row.where}: gelir toplamı yinelenmiş. Tek toplamlı PDF kullanın.')
            prefix_total = row
            continue
        code = codes(row.text(0))
        if code and code[0] not in REVENUE_CODES:
            raise ConversionError(f'{row.where}: bilinmeyen gelir üst kodu {code[0]}. '
                                  'Geçerli düzey 1 üst kodunu ve satırını kontrol edin.')
        if len(code) > 1:
            details.append((code[0], row.where))
            continue
        for offset in (0, 7):
            parts = row.cells[2 + offset]
            if len(parts) > 1:
                pending.append((offset, row.where, parts))
        if not code:
            if total is not None or prefix_total is not None:
                raise ConversionError(f'{row.where}: gelir toplamı yinelenmiş. Tek toplamlı PDF kullanın.')
            total = row.amounts(2, labels, revenue=True, notes=notes)
            continue
        if code[0] not in REVENUE_CODES or code[0] in emitted:
            raise ConversionError(f'{row.where}: gelir kodu bilinmiyor veya yinelenmiş ({code[0]}). '
                                  'Düzey 1 kodlarını kontrol edin.')
        emitted[code[0]] = row.amounts(2, labels, revenue=True, notes=notes)
        v = emitted[code[0]]
        if v[0] < 0:
            if (code[0] != '09' or norm(row.text(1)) != 'red ve iadeler'
                    or not re.search(r'\(\s*-\s*\)', row.text(1)) or any(v[1:])):
                raise ConversionError(f'{row.where}: negatif gelir tahmini yalnız 09 Red ve İadeler (-) '
                                      'plan kesintisinde, diğer yedi parasal alan açık sıfırken desteklenir. '
                                      'Kaynak satırı kontrol edin; tutar pozitif gelire çevrilmedi.')
            planned_deduction = row
    if not emitted:
        raise ConversionError('Gelir: düzey 1 satır bulunamadı. Tam gelir cetvelini kullanın.')
    for parent, where in details:
        if parent not in emitted:
            raise ConversionError(f'{where}: gelir alt kodunun {parent} düzey 1 üst satırı eksik. '
                                  'Üst satırı içeren tam gelir PDF kullanın; alt gelir atılmadı.')
    notes.append('Gelir Oran sütunu yüzde olduğu için toplanmaz; sekiz parasal kaynak sütunu karşılaştırılır.')
    summed = sum_vectors(emitted.values(), 8)
    if prefix_total is not None:
        matched = check_total_prefixes(prefix_total, summed, year, notes, errors)
        for offset, where, parts in pending:
            if (not MONEY.fullmatch(''.join(parts))
                    and not MONEY.fullmatch(prefix_total.text(2 + offset))):
                errors.append(f'{where}, {labels[offset]}: bölünmüş tutar iki ondalıkla '
                              'tamamlanmadı ve TOPLAM’da da tam ondalık yok. Kaynak hücredeki '
                              'eksik rakamları kontrol edin; önekten rakam tahmin edilmedi.')
            elif offset in matched:
                notes.append(f'{where}, {labels[offset]}: {safe(" / ".join(parts))} → '
                             f'{"".join(parts)}; açık kaynak parçaları korundu, TOPLAM basılı öneğiyle '
                             'karşılaştırıldı. TOPLAM’da bulunmayan ondalıklar bağımsız doğrulanamadı.')
    elif total is not None:
        reconcile('Gelir düzey 1 toplamı', summed, total, labels, notes, errors)
        for offset, where, parts in pending:
            if summed[offset] == total[offset]:
                notes.append(f'{where}, {labels[offset]}: {safe(" / ".join(parts))} → '
                             f'{"".join(parts)}; bağımsız genel toplam sütunuyla doğrulandı.')
    else:
        if planned_deduction is not None:
            errors.append(f'{planned_deduction.where}: negatif plan kesintisi bağımsız genel toplam '
                          'olmadan doğrulanamaz. Genel toplamı içeren tam gelir PDF kullanın.')
        for offset, where, parts in pending:
            errors.append(f'{where}, {labels[offset]}: bölünmüş tutar '
                          f'({safe(" / ".join(parts))}) satır eşitliği veya genel toplamla '
                          'doğrulanamıyor. Genel toplamı içeren kaynak PDF kullanın.')
        notes.append('Gelir PDF toplam satırı yok; genel toplam karşılaştırması yapılamadı. '
                     'Düzey 1 satırlarının tahakkuk ve net tahsilat eşitlikleri doğrulandı.')
    output = []
    for code, v in sorted(emitted.items()):
        if code == '09' and planned_deduction is not None:
            continue
        validate_output([v[0], v[4], v[5]], f'Gelir {code}')
        output.append([code, money(v[0]), money(v[4]), money(v[5]), ''])
    if planned_deduction is not None:
        gross = sum((v[0] for code, v in emitted.items() if code != '09'), Decimal(0))
        deduction = emitted['09'][0]
        if total is not None:
            reconcile('Gelir XLSX brüt tahmin + plan kesintisi', [gross + deduction],
                      total[:1], labels[:1], notes, errors)
        net_label = ('hesaplanan net tahmin (PDF TOPLAM önek kontrolü)' if prefix_total is not None
                     else 'PDF net tahmini')
        notes.append(f'{planned_deduction.where}: 09 Red ve İadeler (-) kaynak plan kesintisi '
                     f'{money(deduction)}; XLSX satırı üretilmedi. Mevcut önizleme negatif tahmini '
                     'desteklemediğinden XLSX brüt tahmin içerir; net bütçe tahmini içermez. '
                     f'XLSX brüt tahmin + kaynak plan kesintisi = {net_label}: '
                     f'{money(gross)} + ({money(deduction)}) = {money(gross + deduction)}. '
                     'Kesinti kaynak mutabakatına eksi işaretiyle dahil edildi; pozitif gelir, '
                     'tahsilat veya gerçekleşen Red ve İadeler alanına aktarılmadı. '
                     'Net bütçe tahmininin uygulamada temsili ayrı bir app/ değişikliği gerektirir.')
    return output


def validate_output(values, where):
    if any(v < 0 or v >= Decimal('1e16') for v in values):
        raise ConversionError(f'{where}: tutar mevcut XLSX içe aktarma sınırının dışında '
                              '(negatif veya 16 basamak). Kaynak tutarları kontrol edin.')


def workbook(kind, rows):
    book = Workbook()
    sheet = book.active
    sheet.title = 'Malî Bilgiler'
    sheet.freeze_panes = 'A2'
    sheet.append(EXPENSE_HEADERS if kind == 'expenditure' else REVENUE_HEADERS)
    for row in rows:
        sheet.append(row)
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = 28
        for cell in column[1:]:
            if isinstance(cell.value, str):
                cell.number_format = '@'
    result = io.BytesIO()
    book.save(result)
    book.close()
    return result.getvalue()


def write_outputs(out, outputs, report):
    """Stage inside --out, publish exclusively, roll back on an I/O failure.

    Even with a BytesIO destination, openpyxl uses temporary worksheet files.
    Its standard-library temporary directory is scoped here to our staging
    directory so the CLI never writes worksheet XML into the system /tmp.
    """
    created = []
    with tempfile.TemporaryDirectory(prefix='.civ194-', dir=out) as scratch:
        scratch = Path(scratch)
        previous_tempdir = tempfile.tempdir
        try:
            tempfile.tempdir = str(scratch)
            for kind, rows in outputs.items():
                (scratch / f'{kind}.xlsx').write_bytes(workbook(kind, rows))
        finally:
            tempfile.tempdir = previous_tempdir
        (scratch / 'report.md').write_text(report + '\n', encoding='utf-8')
        try:
            for kind in outputs:
                destination = out / f'{kind}.xlsx'
                # Same-filesystem hard link is atomic and refuses every existing
                # destination, including a symlink created after preflight.
                os.link(scratch / destination.name, destination)
                created.append(destination)
            os.replace(scratch / 'report.md', out / 'report.md')
        except OSError:
            for destination in created:
                destination.unlink()
            raise


def render_report(year, notes, errors):
    report = (f'# Kesin hesap dönüştürme raporu — {year}\n\n'
              + ('Durum: Hata — XLSX üretilmedi.\n' if errors else 'Durum: Başarılı.\n')
              + '\n' + MAPPING + '\n## Kontroller ve kaynak izleri\n\n' + '\n'.join(notes))
    if errors:
        report += '\n\n## Hatalar\n\n' + '\n'.join(f'- {error}' for error in errors)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Kesin hesap metin PDF → Civensa malî bilgiler XLSX (çevrimdışı).', add_help=False)
    parser.add_argument('-h', '--help', action='help', help='Kullanımı göster ve çık')
    parser._optionals.title = 'Seçenekler'
    parser.add_argument('--gider', type=Path, help='Bütçe Gider Kesin Hesap PDF')
    parser.add_argument('--gelir', type=Path, help='Gelir Cetveli Kesin Hesap PDF')
    parser.add_argument('--year', type=int, required=True, help='Kesin hesap yılı')
    parser.add_argument('--departments', type=Path, required=True, help='Rapor yılı müdürlük eşlemesi CSV')
    parser.add_argument('--out', type=Path, required=True, help='Çıktı dizini; mevcut XLSX üzerine yazılmaz')
    args = parser.parse_args(argv)
    if not (args.gider or args.gelir) or not 1900 <= args.year <= 9998:
        parser.error('--gider ve/veya --gelir ile 1900–9998 arası --year belirtin.')
    notes = ['Eşleme CSV’si kesin hesap yılına ait olmalıdır; kod değişiklikleri CSV dışında tahmin edilmez.']
    errors = []
    outputs = {}
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        # Unsafe report targets cannot receive even an error report.
        report_path = args.out / 'report.md'
        if report_path.is_symlink() or (report_path.exists() and not report_path.is_file()):
            raise ConversionError('report.md normal dosya değil. Yeni bir çıktı dizini kullanın.')
        targets = {(args.out / name).resolve() for name in ('report.md', 'expenditure.xlsx', 'revenue.xlsx')}
        inputs = [path for path in (args.departments, args.gider, args.gelir) if path]
        if any(path.resolve() in targets for path in inputs):
            raise ConversionError('Girdi ile çıktı yolu çakışıyor. Ayrı bir çıktı dizini kullanın.')
    except ConversionError as exc:
        print(safe(exc), file=sys.stderr)
        return 1
    except OSError:
        print('Çıktı dizini hazırlanamadı. --out yolunu ve dizin izinlerini kontrol edin.', file=sys.stderr)
        return 1
    try:
        for kind, path in (('expenditure', args.gider), ('revenue', args.gelir)):
            destination = args.out / f'{kind}.xlsx'
            if path and (destination.exists() or destination.is_symlink()):
                raise ConversionError(f'{kind}.xlsx zaten var. Mevcut dosya korunuyor; yeni çıktı dizini kullanın.')
        departments = load_departments(args.departments)
        notes.append(f'Müdürlük CSV SHA-256: {hashlib.sha256(args.departments.read_bytes()).hexdigest()}')
        for kind, path in (('expenditure', args.gider), ('revenue', args.gelir)):
            if not path:
                continue
            try:
                notes.append(f'{safe(path.name)} SHA-256: {hashlib.sha256(path.read_bytes()).hexdigest()}')
                rows = pdf_rows(path, kind, args.year, notes)
                output = (expenditure(rows, departments, notes, errors) if kind == 'expenditure'
                          else revenue(rows, args.year, notes, errors))
                if len(output) > 5000:
                    raise ConversionError(f'{path.name}: 5.000 XLSX satır sınırı aşıldı. Kaynak kapsamını kontrol edin.')
                outputs[kind] = output
                notes.append(f'{path.name}: {len(rows)} kaynak satır → {len(output)} düzey 1 XLSX satırı.')
            except ConversionError as exc:
                errors.append(f'{path.name}: {safe(exc)}')
            except (PyPdfError, OSError, ValueError, InvalidOperation) as exc:
                errors.append(f'{path.name}: PDF okunamadı ({safe(exc)}). '
                              'Dosyanın erişilebilir, bozulmamış metin PDF olduğunu kontrol edin.')
    except ConversionError as exc:
        errors.append(safe(exc))
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f'Müdürlük CSV okunamadı ({safe(exc)}). Dosya yolunu, UTF-8 kodlamasını '
                      've virgülle ayrılmış üç sütunu kontrol edin.')
    try:
        write_outputs(args.out, {} if errors else outputs, render_report(args.year, notes, errors))
    except (OSError, ValueError):
        print('Çıktı dosyaları yazılamadı. --out dizininin yazma izinlerini ve boş disk alanını '
              'kontrol edip yeni çıktı diziniyle tekrar deneyin.', file=sys.stderr)
        return 1
    if errors:
        print('Dönüştürme durduruldu. Hatalar ve düzeltme adımları: ' + str(args.out / 'report.md'), file=sys.stderr)
        return 1
    print('Dönüştürme tamamlandı: ' + str(args.out / 'report.md'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
