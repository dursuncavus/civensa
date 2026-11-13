#!/usr/bin/env python3
"""CIV-222 / D-480: pilot test hesaplarını kapatma (salt okunur plan + korumalı uygulama).

CIV-221 envanteri (13 Kasım 2026) canlıda deneme verisi göstermedi; yalnız test
hesapları temizlenir. Hesaplar kimlik ve e-posta özetiyle sabitlenmiştir: canlı
hedef bu listeden farklıysa araç 0 yazmayla durur.

- Kalan: Strateji çalışma hesabı (1) ve Strateji Müdürü (36).
- Silinen: hiç kaydı olmayan 4 hesap (37, 38, 39, 40), CIV-207 kuralıyla.
- Pasife alınan: girişi olduğu için silinemeyen 34 test hesabı (2–35).

Uygulama tek işlemdir; her hesap için denetim kaydı yazılır (user_delete /
user_deactivate). Pasife alma geri alınabilir; silinen hesapların ad, e-posta,
rol ve müdürlüğü denetim kaydında kalır (parola özeti hariç).
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import first_load_live as live

CONFIRMATION = 'PILOT TEST HESAPLARINI KAPAT'
ACTION = 'pilot_accounts_cleared'
KEEP = (1, 36)
DELETE = (37, 38, 39, 40)
DEACTIVATE = tuple(range(2, 36))
# sha256(lower(e-mail))[:16] per id, from the CIV-221 live inventory (13 Nov 2026).
# Hashes, not addresses: the repository is public. 37 and 38 are personal addresses and
# are not pinned at all; they must instead be inactive department accounts without records.
PINNED = {
    1: 'e861907e30ff4cae', 2: 'cc24e714fd7937b6', 3: '354b60339bc4e3eb', 4: '6d08fbe57688d730',
    5: '1749e6c8e84c7d9b', 6: 'b6f4bdb9904ba4aa', 7: '5d3c21b93e7d68c2', 8: '63a4edae8e9a7492',
    9: '37f8f2a46039b93f', 10: 'f6a84116726ccb3b', 11: '7465c7e1b77c12f4', 12: 'eb36f669c7305a8a',
    13: '251459fb769a4ba1', 14: '099843cae9737beb', 15: '4a4499bbcb2a7d35', 16: '82b4f8d8dc2e5cdf',
    17: '6d0cb5cde668bada', 18: 'cedcdf4527bbeac7', 19: 'aa1fa600f91ea641', 20: '28a1b421b1c45f65',
    21: '8a0ae6416fe7e029', 22: '283c6f9f9de227d6', 23: 'cd295b166187a95a', 24: '6e28ceae18d53e78',
    25: 'afa6198f9d599abd', 26: 'd320c7f1a7738815', 27: '01635fb5169c7b81', 28: 'c6a9270f5afa0ea9',
    29: '3538d029641194c8', 30: 'f5416f212921909e', 31: '45d8cc4e24deb546', 32: '28b8d69801416b21',
    33: '778e634fc2a2ea20', 34: 'a38395522640ffb2', 35: 'fb01dcd6caa130c9', 36: 'd1ecb6457065455d',
    39: '897b40a5f3821112', 40: 'fceea4c447955a6d',
}


def email_hash(email):
    return hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()[:16]


def refuse(message):
    raise live.Refusal(message)


def build_plan(db, actor_id):
    from sqlalchemy import select
    from app.first_load_service import load_all_models
    from app.models import User
    from app.user_deletion import referenced_user_ids

    load_all_models()
    live.require_head(db)
    users = {u.id: u for u in db.scalars(select(User))}
    expected = set(KEEP) | set(DELETE) | set(DEACTIVATE)
    if set(users) != expected:
        refuse(f'Hesap listesi envanterle uyuşmuyor: beklenen {len(expected)} hesap, bulunan {len(users)}; '
               'yeni envanter alın ve sorumluya bildirin')
    for uid, digest in sorted(PINNED.items()):
        if email_hash(users[uid].email) != digest:
            refuse(f'Hesap {uid} e-postası envanterle uyuşmuyor; sorumluya bildirin')
    for uid in (37, 38):
        if users[uid].is_active or users[uid].role != 'department':
            refuse(f'Hesap {uid} envanterdeki gibi pasif müdürlük hesabı değil; sorumluya bildirin')
    if actor_id not in KEEP:
        refuse('--actor-id kalan Strateji hesaplarından biri olmalıdır (1 veya 36)')
    for uid in KEEP:
        if users[uid].role != 'strategy' or not users[uid].is_active:
            refuse(f'Kalacak hesap {uid} etkin Strateji hesabı değil; sorumluya bildirin')
    used = referenced_user_ids(db, list(DELETE))
    if used:
        refuse('Silinecek hesaplardan kaydı olan var: ' + ', '.join(map(str, sorted(used)))
               + '; yeni envanter alın')
    if any(users[uid].role == 'strategy' for uid in DELETE + DEACTIVATE):
        refuse('Kapatılacak listede Strateji hesabı var; sorumluya bildirin')
    return users


def execute(engine, *, actor_id, apply=False, confirmation=None):
    from sqlalchemy import delete, text
    from sqlalchemy.orm import Session
    from app.models import AuditLog
    from app.user_deletion import DISPOSABLE_TABLES, _user_columns

    if apply and confirmation != CONFIRMATION:
        refuse('Onay cümlesi uyuşmuyor; tam cümleyi yazın')
    with engine.connect() as connection, Session(connection) as db, db.begin():
        if not apply:
            db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        else:
            if not db.scalar(text('SELECT pg_try_advisory_xact_lock(:key)'), {'key': live.LOCK}):
                refuse('Başka bir canlı işlem çalışıyor; bitince yeniden plan alın')
            db.execute(text("SET LOCAL lock_timeout = '10s'"))
            db.execute(text('LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE'))
        users = build_plan(db, actor_id)
        result = dict(mode='apply' if apply else 'plan',
                      keep=[(u, users[u].full_name) for u in KEEP],
                      delete=[(u, users[u].full_name) for u in DELETE],
                      deactivate=[(u, users[u].full_name) for u in DEACTIVATE],
                      already_inactive=sorted(u for u in DEACTIVATE if not users[u].is_active))
        if not apply:
            return result
        for uid in DELETE:
            target = users[uid]
            details = json.dumps({'email': target.email, 'full_name': target.full_name, 'role': target.role,
                                  'department_id': target.department_id, 'position': target.position,
                                  'source': 'CIV-222'}, ensure_ascii=False)
            for table, column in _user_columns():
                if table.name in DISPOSABLE_TABLES:
                    db.execute(delete(table).where(column == uid))
            db.delete(target)
            db.add(AuditLog(user_id=actor_id, action='user_delete', entity_type='user', entity_id=uid,
                            details=details))
        db.flush()
        for uid in DEACTIVATE:
            target = users[uid]
            if target.is_active:
                target.is_active = False
                db.add(AuditLog(user_id=actor_id, action='user_deactivate', entity_type='user', entity_id=uid,
                                details='CIV-222'))
        db.add(AuditLog(user_id=actor_id, action=ACTION, entity_type='user', entity_id=None,
                        details=json.dumps({'decision': 'D-480', 'deleted': list(DELETE),
                                            'deactivated': list(DEACTIVATE), 'kept': list(KEEP)})))
        db.flush()
        return result


def format_summary(result):
    title = 'UYGULANDI' if result['mode'] == 'apply' else 'PLAN'
    lines = [f'ÖZET · {title}',
             'Kalacak: ' + ', '.join(f'{u} {n}' for u, n in result['keep']),
             f"Silinecek ({len(result['delete'])}): " + ', '.join(f'{u} {n}' for u, n in result['delete']),
             f"Pasife alınacak ({len(result['deactivate'])}): " + ', '.join(str(u) for u, _ in result['deactivate'])]
    if result['already_inactive']:
        lines.append('Zaten pasif: ' + ', '.join(map(str, result['already_inactive'])))
    if result['mode'] == 'plan':
        lines.append('Hedefe 0 satır yazıldı (salt okunur). Uygulamadan önce yeni yedek alın.')
    else:
        lines.append('İşlem tamamlandı; her hesap için denetim kaydı yazıldı.')
    return '\n'.join(lines)


def main(argv=None):
    parser = live.SafeParser(description=__doc__)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--apply', action='store_true', help='Tam terminal onayıyla uygula')
    args = parser.parse_args(argv)
    try:
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with live.environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = live.target_url()
            confirmation = None
            if args.apply:
                try:
                    confirmation = live.read_confirmation(f'Onay için "{CONFIRMATION}" yazın: ')
                except (EOFError, KeyboardInterrupt):
                    refuse('Onay alınamadı; etkileşimli terminalde yeniden deneyin')
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                                   connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                result = execute(engine, actor_id=args.actor_id, apply=args.apply, confirmation=confirmation)
            finally:
                engine.dispose()
        print(format_summary(result))
        return 0
    except live.Refusal as exc:
        print('DURDU: ' + str(exc), file=sys.stderr)
    except KeyboardInterrupt:
        print('DURDU: işlem kesildi; yeniden plan alın.', file=sys.stderr)
    except Exception:
        print('DURDU: işlem tamamlanamadı; bağlantı ayrıntıları gizlendi. Sorumluya bildirin.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
