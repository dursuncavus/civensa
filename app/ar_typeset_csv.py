"""Optional flat CSVs for a designer's merge script; IDs remain the primary key."""
import csv
import io
import json


def flatten(value, prefix=''):
    if isinstance(value, dict):
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
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator='\n')
    writer.writeheader(); writer.writerows(records)
    return output.getvalue().encode('utf-8-sig')
