#!/usr/bin/env python3
"""CIV-221 / D-478: salt okunur pilot envanteri (hesaplar ve müdürlük verisi).

Gerçek veri girişinden önce test hesaplarını ve deneme verisini ayırmak için
canlı veritabanını yalnız okur. Hiçbir satır yazmaz; işlem READ ONLY açılır.

Çıktı iki bölümdür:
1. HESAPLAR: her kullanıcı için kimlik, rol, görev, müdürlük, etkinlik, son
   giriş ve hesaba bağlı kayıt sayısı (CIV-207 kuralı: kaydı olan hesap
   silinmez, yalnız devre dışı bırakılır).
2. MÜDÜRLÜK VERİSİ: department_id taşıyan her tabloda müdürlük başına satır
   sayısı; 2026 dönemine ait olanlar ayrıca sayılır.

Çıktıda ad ve e-posta bulunur: yalnız sahip ve lider görür, repoya yazılmaz.
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import first_load_live as live

DISPOSABLE = {'notification_recipients'}


def user_reference_columns():
    from app.db import Base
    users = Base.metadata.tables['users']
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            if fk.column.table is users and fk.column.name == 'id' and table.name not in DISPOSABLE:
                yield table, fk.parent


def department_columns():
    from app.db import Base
    departments = Base.metadata.tables['departments']
    for table in Base.metadata.sorted_tables:
        if table.name == 'users':
            continue
        for fk in table.foreign_keys:
            if fk.column.table is departments and fk.column.name == 'id':
                yield table, fk.parent


def collect(db, year=2026):
    from sqlalchemy import func, select
    from app.first_load_service import load_all_models
    from app import models as m
    from ops.pp2026_rehearsal import period_inventory_tables

    load_all_models()
    live.require_head(db)
    departments = {d.id: d.name for d in db.scalars(select(m.Department))}

    references = {}
    for table, column in user_reference_columns():
        for user_id, count in db.execute(select(column, func.count()).where(column.is_not(None))
                                         .group_by(column)).all():
            per_user = references.setdefault(user_id, {})
            key = f'{table.name}.{column.name}' if table.name == 'audit_log' else table.name
            per_user[key] = per_user.get(key, 0) + count
    audit = m.AuditLog.__table__
    last_login = dict(db.execute(select(audit.c.user_id, func.max(audit.c.created_at))
                                 .where(audit.c.action == 'login').group_by(audit.c.user_id)).all())
    users = []
    for user in db.scalars(select(m.User).order_by(m.User.department_id, m.User.id)):
        refs = references.get(user.id, {})
        users.append(dict(id=user.id, full_name=user.full_name, email=user.email, role=user.role,
                          position=user.position, can_submit=user.can_submit, active=user.is_active,
                          must_change_password=user.must_change_password,
                          department=departments.get(user.department_id, '-'),
                          department_id=user.department_id,
                          last_login=last_login.get(user.id), references=refs,
                          reference_total=sum(refs.values())))

    owned = period_inventory_tables(year)
    data = {}
    for table, column in department_columns():
        rows = db.execute(select(column, func.count()).select_from(table).where(column.is_not(None))
                          .group_by(column)).all()
        period_rows = {}
        if table.name in owned:
            cte = owned[table.name]
            period_rows = dict(db.execute(select(cte.c[column.name], func.count())
                                          .where(cte.c[column.name].is_not(None))
                                          .group_by(cte.c[column.name])).all())
        for department_id, count in rows:
            entry = data.setdefault(department_id, {})
            entry[table.name] = (count, period_rows.get(department_id, 0))
    return dict(year=year, users=users, departments=departments, data=data)


def execute(engine, year=2026):
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    with engine.connect() as connection, Session(connection) as db, db.begin():
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        db.execute(text("SET LOCAL TIME ZONE 'UTC'"))
        return collect(db, year=year)


def format_report(result):
    year = result['year']
    lines = ['HESAPLAR (' + str(len(result['users'])) + ')',
             'id | ad soyad | e-posta | rol/görev | müdürlük | etkin | son giriş (UTC) | bağlı kayıt']
    for u in result['users']:
        login = u['last_login'].strftime('%Y-%m-%d %H:%M') if u['last_login'] else 'hiç'
        lines.append(' | '.join([str(u['id']), u['full_name'], u['email'], f"{u['role']}/{u['position']}",
                                 u['department'], 'evet' if u['active'] else 'hayır', login,
                                 str(u['reference_total'])]))
        if u['references']:
            lines.append('    ' + ', '.join(f'{k}: {v}' for k, v in sorted(u['references'].items())))
    lines += ['', f'MÜDÜRLÜK VERİSİ (toplam / {year} dönemi)']
    for department_id in sorted(result['data'], key=lambda d: result['departments'].get(d, '')):
        tables = result['data'][department_id]
        total = sum(c for c, _ in tables.values())
        in_year = sum(p for _, p in tables.values())
        lines.append(f"{result['departments'].get(department_id, department_id)}: {total} / {in_year}")
        lines.append('    ' + ', '.join(f'{name}: {c}/{p}' for name, (c, p) in sorted(tables.items())))
    lines += ['', 'Hedefe 0 satır yazıldı (salt okunur).']
    return '\n'.join(lines)


def main(argv=None):
    parser = live.SafeParser(description=__doc__)
    parser.add_argument('--year', type=int, default=2026)
    args = parser.parse_args(argv)
    try:
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with live.environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = live.target_url()
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                                   connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                result = execute(engine, year=args.year)
            finally:
                engine.dispose()
        print(format_report(result))
        return 0
    except live.Refusal as exc:
        print('DURDU: ' + str(exc), file=sys.stderr)
    except KeyboardInterrupt:
        print('DURDU: envanter kesildi.', file=sys.stderr)
    except Exception:
        print('DURDU: pilot envanteri tamamlanamadı; bağlantı ayrıntıları gizlendi. Sorumluya bildirin.',
              file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
