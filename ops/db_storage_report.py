"""Read-only PostgreSQL storage audit; emits sizes and numeric row IDs only.

Run from the repository root: python -m ops.db_storage_report
No application startup, migrations, or ORM models are loaded.
"""
import argparse
from contextlib import contextmanager
import json
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


# Text columns which can contain image base64, including frozen/copy payloads.
# Keep this inventory in sync with docs/operations/db-storage.md.
BASE64_COLUMNS = {
    ('report_sections', 'content_json'),
    ('import_batches', 'payload_json'),
    ('import_batches', 'snapshot_json'),
    ('publications', 'snapshot_json'),
    ('report_candidates', 'payload_json'),
    ('report_artifacts', 'content_json'),
}


@contextmanager
def read_only_connection(engine):
    with engine.connect() as connection:
        with connection.begin():
            # This must precede every report query, including catalog discovery.
            connection.execute(text('SET TRANSACTION READ ONLY'))
            connection.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ'))
            try:
                yield connection
            finally:
                connection.rollback()


def collect_report(connection, schema='public'):
    """Measure logical column bytes; table/database sizes include physical overhead."""
    quote = connection.dialect.identifier_preparer.quote_identifier
    report = {
        'database_bytes': connection.scalar(text('SELECT pg_database_size(current_database())')),
        'schema': schema,
        'tables': [],
        'columns': [],
        'missing_base64_columns': [],
        'skipped_tables': [],
    }
    tables = connection.execute(text("""
        SELECT c.relname AS name, pg_total_relation_size(c.oid) AS total_bytes
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = :schema AND c.relkind IN ('r', 'p', 'm')
        ORDER BY total_bytes DESC, c.relname
    """), {'schema': schema}).mappings()
    report['tables'] = [dict(row) for row in tables]
    columns = connection.execute(text("""
        SELECT c.relname AS table_name, a.attname AS column_name,
               t.typname AS type_name
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
        WHERE n.nspname = :schema AND c.relkind IN ('r', 'p', 'm')
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attname
    """), {'schema': schema}).mappings().all()
    found = {(row['table_name'], row['column_name']) for row in columns}
    report['missing_base64_columns'] = [
        f'{table}.{column}' for table, column in sorted(BASE64_COLUMNS - found)
    ]
    for row in columns:
        table, column = row['table_name'], row['column_name']
        if row['type_name'] != 'bytea' and (table, column) not in BASE64_COLUMNS:
            continue
        if (table, 'id') not in found:
            if not any(item['table'] == table for item in report['skipped_tables']):
                report['skipped_tables'].append({'table': table, 'reason': 'id sütunu bulunmadığı için kayıt boyutları ölçülemedi. Tablo anahtarını kontrol edin.'})
            continue
        relation = f'{quote(schema)}.{quote(table)}'
        size = f'octet_length({quote(column)})'
        stats = dict(connection.execute(text(f'''
            SELECT count(*) AS row_count, count({quote(column)}) AS value_count,
                   coalesce(sum({size}), 0) AS total_bytes,
                   coalesce(max({size}), 0) AS max_bytes FROM {relation}
        ''')).mappings().one())
        largest = connection.execute(text(f'''
            SELECT id, {size} AS bytes FROM {relation}
            WHERE {quote(column)} IS NOT NULL
            ORDER BY bytes DESC, id LIMIT 5
        ''')).mappings()
        report['columns'].append({
            'table': table, 'column': column,
            'storage': 'binary' if row['type_name'] == 'bytea' else 'base64_json_text',
            **stats, 'largest_rows': [dict(item) for item in largest],
        })
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='PostgreSQL depolama boyutlarını salt okunur ölçer.')
    parser.add_argument('--schema', default='public', help='Ölçülecek şema (varsayılan: public)')
    args = parser.parse_args(argv)
    engine = None
    try:
        raw = os.environ.get('DATABASE_URL')
        if not raw:
            print('DATABASE_URL ortam değişkeni eksik. Depolama raporu için yerel PostgreSQL bağlantısını ayarlayıp yeniden deneyin.', file=sys.stderr)
            return 1
        url = make_url(raw)
        if url.drivername == 'postgres' or url.drivername == 'postgresql':
            url = url.set(drivername='postgresql+psycopg')
        if url.get_backend_name() != 'postgresql':
            print('Bu rapor yalnızca PostgreSQL üzerinde çalışır. Yerel PostgreSQL bağlantısı seçip yeniden deneyin.', file=sys.stderr)
            return 1
        engine = create_engine(url, echo=False, hide_parameters=True)
        with read_only_connection(engine) as connection:
            report = collect_report(connection, args.schema)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception:
        # Driver errors may contain credentials or SQL parameters. Never echo them.
        print('Depolama raporu alınamadı. Bağlantı, şema ve salt okunur erişim yetkilerini kontrol edin.', file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
