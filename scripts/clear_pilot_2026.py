#!/usr/bin/env python3
"""CIV-172 / D-389: 2026 pilot dönemi için salt okunur plan ve korumalı temizleme."""
import base64
import gzip
import hashlib
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import first_load_live as live
from scripts.clear_preprint_2027 import encoded, refuse

ACTION = 'pilot_2026_cleared'
CONFIRMATION = '2026 PILOT DONEMINI SIL'
# D-388, verified 3 November backup / rehearsal 41662709108. A new pilot
# fingerprint requires a new owner decision; never derive it from the target.
PINNED = dict(reporting_periods=1, programs=24, subprograms=40, indicators=220,
              indicator_values=1090, activities=174, activity_cost_values=1119,
              department_cost_values=99, submissions=34, import_batches=2,
              audit_log=136)
STATES = {'indicators': {'draft': 220}, 'submissions': {'approved': 3, 'draft': 31},
          'import_batches': {'applied': 1, 'preview': 1}}
RETAIN = {'reporting_periods', 'audit_log'}


def build_plan(db, organization_id, actor_id):
    from sqlalchemy import func, select, tuple_
    from app.db import Base
    from app import models as m
    from ops.pp2026_rehearsal import period_inventory_tables, period_audit_table

    live.require_head(db)
    orgs = list(db.scalars(select(m.Organization.id)))
    if orgs != [organization_id]:
        refuse('Tek kurum ve doğru --organization-id gerekli')
    actor = db.get(m.User, actor_id)
    if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
        refuse('--actor-id etkin Strateji/yönetici kullanıcısı olmalıdır')
    owned = period_inventory_tables(2026)
    owned['audit_log'] = period_audit_table(owned)
    counts = {name: db.scalar(select(func.count()).select_from(table))
              for name, table in sorted(owned.items())}
    for name in sorted(set(counts) | PINNED.keys()):
        expected, actual = PINNED.get(name, 0), counts.get(name, 0)
        if expected != actual:
            refuse(f'2026 {name} sayısı uyuşmuyor: beklenen {expected}, bulunan {actual}')
    period = db.scalar(select(m.ReportingPeriod).where(m.ReportingPeriod.year == 2026))
    if period.status != 'closed' or period.template_status != 'verified':
        refuse('2026 reporting_periods durumu closed/verified olmalıdır')
    for name, expected in STATES.items():
        table = owned[name]
        actual = dict(db.execute(select(table.c.status, func.count()).group_by(table.c.status)).all())
        if actual != expected:
            # Never echo arbitrary DB string values at the CLI boundary.
            for label, count in expected.items():
                found = actual.get(label, 0)
                if found != count:
                    refuse(f'2026 {name}.{label} sayısı uyuşmuyor: beklenen {count}, bulunan {found}')
            refuse(f'2026 {name} durum dağılımı onaylı envanterle uyuşmuyor')

    removed = {name: table for name, table in owned.items()
               if name not in RETAIN and counts[name]}
    # Direct period ownership takes precedence in discovery. Explicitly reject
    # cross-period references (including composite FKs) before any deletion;
    # neither ON DELETE CASCADE nor SET NULL may mutate a retained row.
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_key_constraints:
            parent = removed.get(fk.referred_table.name)
            if parent is None:
                continue
            local = [element.parent for element in fk.elements]
            remote = [parent.c[element.column.name] for element in fk.elements]
            left = local[0] if len(local) == 1 else tuple_(*local)
            condition = left.in_(select(*remote))
            if table.name in removed:
                keys = list(table.primary_key.columns)
                own_keys = [removed[table.name].c[c.name] for c in keys]
                key = keys[0] if len(keys) == 1 else tuple_(*keys)
                condition &= key.not_in(select(*own_keys))
            count = db.scalar(select(func.count()).select_from(table).where(condition))
            if count:
                refuse(f'2026 {table.name} dönem dışı bağlantı sayısı: beklenen 0, bulunan {count}')
    return period, counts, removed


def execute(engine, *, organization_id, actor_id, apply=False, backup=None, confirmation=None):
    """Plan is a read-only snapshot; apply guards, archive and deletes are atomic.

    CLI confirmation comes from /dev/tty. The disposable rehearsal instead passes
    the owner's explicit workflow input. Both entry paths require a fresh proof.
    """
    from sqlalchemy import select, text, tuple_
    from sqlalchemy.orm import Session
    from app.db import Base
    from app.models import AuditLog
    from app.first_load_service import period_rows_hash

    if apply:
        if confirmation != CONFIRMATION:
            refuse('2026 pilot temizleme onayı uyuşmuyor; tam onay cümlesini kullanın')
        live.verify_backup(backup)
    with engine.connect() as connection, Session(connection) as db, db.begin():
        if not apply:
            db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        else:
            if not db.scalar(text('SELECT pg_try_advisory_xact_lock(:key)'), {'key': live.LOCK}):
                refuse('Başka ilk yükleme/temizleme çalışıyor; işlem bitince yeniden plan alın')
            db.execute(text("SET LOCAL lock_timeout = '10s'"))
            names = ', '.join('"' + t.name + '"' for t in Base.metadata.sorted_tables)
            db.execute(text('LOCK TABLE ' + names + ' IN SHARE ROW EXCLUSIVE MODE'))
        period, counts, removed = build_plan(db, organization_id, actor_id)
        protected = period_rows_hash(db, year=2027)
        result = dict(mode='clear-pilot-apply' if apply else 'clear-pilot-plan', counts=counts,
                      removed_counts={name: counts[name] for name in removed},
                      protected_2027_before=protected, protected_2027_after=protected)
        if not apply:
            return result

        archive = {name: sorted([dict(row) for row in db.execute(select(table)).mappings()], key=encoded)
                   for name, table in sorted(removed.items())}
        raw = encoded(archive).encode('utf-8')
        sha256 = hashlib.sha256(raw).hexdigest()
        receipt = dict(version=1, decision='D-389', year=2026, head=live.HEAD,
                       counts=counts, removed_counts=result['removed_counts'],
                       archive_encoding='gzip+base64', archive_sha256=sha256,
                       archive=base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii'),
                       period_before={c.name: getattr(period, c.name) for c in period.__table__.columns})
        live.verify_backup(backup)  # Lock waits and archive work cannot bypass freshness.
        db.add(AuditLog(user_id=actor_id, action=ACTION, entity_type='reporting_period',
                        entity_id=period.id, details=encoded(receipt)))
        db.flush()
        for table in reversed(Base.metadata.sorted_tables):
            if table.name not in removed:
                continue
            keys = list(table.primary_key.columns)
            selected = [removed[table.name].c[c.name] for c in keys]
            key = keys[0] if len(keys) == 1 else tuple_(*keys)
            count = db.execute(table.delete().where(key.in_(select(*selected)))).rowcount
            if count != counts[table.name]:
                refuse(f'2026 {table.name} silme sayısı uyuşmuyor: beklenen {counts[table.name]}, bulunan {count}')
        period.status, period.template_status = 'draft', 'verified'
        db.flush()
        after = period_rows_hash(db, year=2027)
        if protected != after:
            refuse('2027 dönem hash değeri değişti; işlem geri alındı, yeniden plan alın')
        result.update(archive_sha256=sha256, protected_2027_after=after)
        return result


def format_summary(result):
    lines = ['ÖZET', 'Mod: ' + ('TEMİZLEME' if result['mode'] == 'clear-pilot-apply' else 'PLAN') + ' · Yıl: 2026']
    counts = result['counts']
    nonzero = [(name, count) for name, count in counts.items() if count]
    lines += [' · '.join(f'{name}: {count}' for name, count in nonzero[i:i + 3])
              for i in range(0, len(nonzero), 3)]
    lines += [f'Diğer {sum(count == 0 for count in counts.values())} dönem tablosu: 0',
              'Dönem: closed/verified → draft/verified; dönem kimliği ve denetim kayıtları korunur.',
              'Silinecek/silinen toplam: ' + str(sum(result['removed_counts'].values())),
              '2027 korunuyor: EVET']
    if 'archive_sha256' in result:
        lines.append('Arşiv SHA256: ' + result['archive_sha256'])
    else:
        lines.append('Hedefe 0 satır yazıldı. Uygulamadan önce yeni doğrulanmış yedek alın.')
    return '\n'.join(lines)


def main(argv=None):
    parser = live.SafeParser(description=__doc__)
    parser.add_argument('--organization-id', type=int, required=True)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--apply', action='store_true', help='Yeni yedek ve tam terminal onayıyla temizle')
    parser.add_argument('--backup', type=Path, help='Doğrulanmış, 60 dakikadan yeni .dump dosyası')
    args = parser.parse_args(argv)
    try:
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with live.environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = live.target_url()
            confirmation = None
            if args.apply:
                live.verify_backup(args.backup)
                try:
                    confirmation = live.read_confirmation(f'Temizleme onayı: {CONFIRMATION} yazın: ')
                except (EOFError, KeyboardInterrupt):
                    refuse('2026 pilot temizleme onayı alınamadı; etkileşimli terminalde yeniden plan alın')
                if confirmation != CONFIRMATION:
                    refuse('2026 pilot temizleme onayı uyuşmuyor; tam onay cümlesini kullanın')
                live.verify_backup(args.backup)
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                                   connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                result = execute(engine, organization_id=args.organization_id, actor_id=args.actor_id,
                                 apply=args.apply, backup=args.backup, confirmation=confirmation)
            finally:
                engine.dispose()
        print(format_summary(result))
        return 0
    except live.Refusal as exc:
        print('DURDU: ' + str(exc), file=sys.stderr)
    except KeyboardInterrupt:
        print('DURDU: 2026 temizleme kesildi; uygulamadan önce yeniden plan alın.', file=sys.stderr)
    except Exception:
        print('DURDU: 2026 pilot temizleme tamamlanamadı; bağlantı/dosya ayrıntıları gizlendi. '
              'Uygulamadan önce yeniden plan alın ve sorumluya bildirin.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
