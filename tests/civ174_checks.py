"""Reproduce RULES 1 on the unchanged CIV-169 first-load fixture.

Run from the repository root: python -m tests.civ174_checks
Requires CIVENSA_TEST_POSTGRES_URL pointing only to disposable local PostgreSQL.
"""
from copy import deepcopy
import gzip
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReportingPeriod
from app.program_service import publication_checks
from scripts import first_load_live as live
from scripts.first_load_dryrun import disposable_database, inspect_import, local_test_url


def main():
    destination = Path('docs/reports/civ-174')
    destination.mkdir(parents=True, exist_ok=True)
    lines = ['# CIV-174 — İlk yüklemeden sonra yayın kontrolleri', '',
        'CIV-169 `loaded_books` hazırlığıyla aynı `inspect_import(..., year=2026)`; geçici, Alembic head seviyesine taşınmış PostgreSQL 16. Yayın/onay hazırlığı yapılmadı.', '',
        'Tekrar üretme: yerel `CIVENSA_TEST_POSTGRES_URL` ile `python -m tests.civ174_checks`.', '',
        '| Yıl | Check id ailesi | Kontrol sayısı | Hata sayısı | Bir örnek |',
        '|---|---|---:|---:|---|']
    details = []
    with disposable_database(local_test_url()) as engine, Session(engine) as db:
        parsed = live.verify_book(live.book_config(2026)[0], year=2026)
        result = inspect_import(db, deepcopy(parsed), live.book_config(2026)[0].name, year=2026)
        assert not result['apply_error']
        assert result['protected_2027_before'] == result['protected_2027_after']
        for year in (2026, 2027):
            period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
            checks = publication_checks(db, period.id)
            families = {key:dict(checks=0, errors=[]) for key in
                        ('scope', 'data', 'approval', 'sections', 'catalogue', 'subtotal')}
            for check in checks:
                entry = families[check['id'].split(':')[0]]
                entry['checks'] += 1
                entry['errors'].extend(check['errors'])
            for family, entry in families.items():
                example = entry['errors'][0].replace('|', '/') if entry['errors'] else '—'
                lines.append(f"| {year} | `{family}` | {entry['checks']} | {len(entry['errors'])} | {example} |")
            details += ['', f'## {year}: tüm hatalar', '']
            for check in checks:
                details.extend(f"- `{check['id']}`: {error}" for error in check['errors'])
            print(year, {key:len(entry['errors']) for key,entry in families.items()})
    with gzip.GzipFile(str(destination / 'all-errors.md.gz'), 'wb', mtime=0) as stream:
        stream.write(('\n'.join(details) + '\n').encode())
    lines += ['', 'Her kontrolün bütün hata mesajları, tekrarları ve check id değerleriyle '
              '[all-errors.md.gz](all-errors.md.gz) dosyasındadır (`gzip -dc` ile okunabilir).', '']
    (destination / 'checks.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
