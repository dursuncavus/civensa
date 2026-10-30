"""Optional flat CSVs for a designer's merge script; IDs remain the primary key."""
import csv
import io
import json
from decimal import Decimal
from .csv_safety import csv_row


class CsvNumber(Decimal):
    """Only validated numbers bypass text escaping, including Turkish display."""
    def __new__(cls, value, localized=False):
        result = super().__new__(cls, value)
        if not result.is_finite():
            raise ValueError('CSV sayısı sonlu değil. Dizgi dosyasını yeniden indirin.')
        result.localized = localized
        return result

    def __str__(self):
        if not self.localized:
            return format(self, 'f')
        return format(self, ',f').replace(',', '_').replace('.', ',').replace('_', '.')


def flatten(value, prefix=''):
    if isinstance(value, dict):
        if 'exact' in value and 'display' in value and value['exact'] is not None:
            exact = CsvNumber(value['exact'])
            display = CsvNumber(value['exact'], localized=True)
            if str(exact) != value['exact'] or str(display) != value['display']:
                raise ValueError('CSV sayı metni ile gösterimi uyuşmuyor. Dizgi dosyasını yeniden indirin.')
            value = {**value, 'exact': exact, 'display': display}
        result = {}
        for key, item in value.items():
            result.update(flatten(item, (prefix + '.' if prefix else '') + key))
        return result
    if isinstance(value, list):
        return {prefix: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
    return {prefix: '' if value is None else value}


def table_csv(contract, table_id):
    table = next(t for t in contract['tables'] if t['id'] == table_id)
    registry = {row['id']: row for kind in ('rows', 'indicators', 'activities') for row in contract[kind]}
    records = []
    for identity in table['row_ids']:
        data = registry[identity]['values']
        if isinstance(data, list):
            data = {f'cell_{index+1}': value for index, value in enumerate(data)}
        record = flatten(data)
        if 'id' in record:
            record['source_record_id'] = record.pop('id')
        records.append({'id': identity, **record})
    columns = ['id'] + sorted({key for row in records for key in row} - {'id'})
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(csv_row(columns))
    for row in records:
        writer.writerow(csv_row([row.get(column, '') for column in columns]))
    return output.getvalue().encode('utf-8-sig')
