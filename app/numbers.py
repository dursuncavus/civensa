"""Lossless Turkish input parsing. Never strip unknown source text into a number."""
from decimal import Decimal, InvalidOperation
import re


def parse_number(raw, *, money=False, source=False):
    text = str(raw if raw is not None else '').strip()
    if text in {'', '-', '–', '—'}:
        return None
    original = text
    text = re.sub(r'\s*(?:TL|₺)\s*$', '', text, flags=re.I).strip()
    multiplier = Decimal(1)
    scaled = re.search(r'\s+(Mn|milyon)\s*$', text, re.I)
    if scaled:
        multiplier = Decimal(1000000)
        text = text[:scaled.start()].strip()
    text = re.sub(r'\s+(?:İçerik|içerik)\s*$', '', text)
    if text.endswith('%'):
        text = text[:-1].strip()
    if isinstance(raw, (int, float, Decimal)) and not isinstance(raw, bool):
        text = str(raw)
    elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?', text):
        text = text.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[+-]?\d+(?:,\d+)?', text):
        if source and ',' in text and len(text.split(',')[1]) == 3:
            raise ValueError(f'Belirsiz sayı ayracı: {original}')
        text = text.replace(',', '.')
    elif re.fullmatch(r'[+-]?\d+\.\d+', text) and scaled:
        pass
    elif isinstance(raw, (int, float, Decimal)):
        text = str(raw)
    else:
        raise ValueError(f'Sayı biçimi doğrulanmalı: {original}')
    try:
        value = Decimal(text) * multiplier
    except InvalidOperation:
        raise ValueError(f'Sayı biçimi doğrulanmalı: {original}') from None
    if not value.is_finite() or abs(value) >= Decimal('1e20'):
        raise ValueError('Sonlu ve geçerli büyüklükte bir sayı girin.')
    precision = Decimal('.01') if money else Decimal('.000001')
    if value != value.quantize(precision):
        raise ValueError('Para için en fazla 2, gösterge için en fazla 6 ondalık basamak girin.')
    if money and value < 0:
        raise ValueError('Tutar negatif olamaz.')
    return value


def source_cell(raw, *, money=False):
    try:
        value = parse_number(raw, money=money, source=True)
        return {'number': str(value) if value is not None else None,
                'raw_text': str(raw if raw is not None else ''), 'state': 'verified' if value is not None else 'missing'}
    except ValueError as exc:
        return {'number': None, 'raw_text': str(raw if raw is not None else ''), 'state': 'needs_review', 'issue': str(exc)}


def format_number(value, money=False):
    if value is None:
        return '—'
    value = Decimal(str(value))
    if not value.is_finite():
        return 'Kontrol gerekli'
    text = f'{value:,.2f}' if money else f'{value:,.6f}'.rstrip('0').rstrip('.')
    return text.replace(',', '_').replace('.', ',').replace('_', '.')


def format_contract_targets(targets):
    """Display target diffs without leaking raw decimal strings or internal row ids."""
    if not targets:
        return 'Kayıt yok'
    return '; '.join(format_number(target['value']) if target.get('state') == 'verified'
                     and target.get('value') is not None else 'Doğrulanmalı'
                     for target in targets)
