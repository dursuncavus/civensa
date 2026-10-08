from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import IndicatorValue


@pytest.mark.parametrize('field,value', [('name', 'a' * 301), ('unit', 'a' * 51), ('name', '   '), ('unit', '   ')])
def test_invalid_indicator_text_leaves_record_unchanged(client, db, sample, field, value):
    indicator = sample['indicator']
    original = (indicator.name, indicator.unit, indicator.explanation)
    response = client.post(f'/api/indicators/{indicator.id}/save', json={
        field: value, 'explanation': 'Kaydedilmemeli', 'value_2027_target': '99',
    })
    assert response.status_code == 422
    assert response.json()['detail'] == 'Gösterge adı ve birimini kontrol edin.'
    db.expire_all()
    assert (indicator.name, indicator.unit, indicator.explanation) == original
    number = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == indicator.id))
    assert number.value == Decimal('1.75')


def test_indicator_text_limits_and_trimming(client, db, sample):
    indicator = sample['indicator']
    response = client.post(f'/api/indicators/{indicator.id}/save', json={
        'name': '  ' + 'İ' * 300 + '  ', 'unit': '  ' + 'Ö' * 50 + '  ',
        'value_2027_target': '2,5',
    })
    assert response.status_code == 200
    assert response.json()['ok'] is True
    db.expire_all()
    assert indicator.name == 'İ' * 300
    assert indicator.unit == 'Ö' * 50
    number = db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id == indicator.id))
    assert number.value == Decimal('2.5')


def test_omitted_indicator_text_is_preserved(client, db, sample):
    indicator = sample['indicator']
    original = (indicator.name, indicator.unit)
    response = client.post(f'/api/indicators/{indicator.id}/save', json={'explanation': 'Yeni açıklama'})
    assert response.status_code == 200
    db.expire_all()
    assert (indicator.name, indicator.unit) == original
    assert indicator.explanation == 'Yeni açıklama'
