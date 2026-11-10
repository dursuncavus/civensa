"""CIV-207 · delete an account only while nothing in the system points at it.

Any row that names the user through a foreign key (a login, an edit, a
submission, an approval, a grant ...) makes the account part of the record:
it can then only be deactivated. Inbox rows (notification recipients) are not
work and go with the account. The deletion itself is audited with the
account's name and e-mail; earlier audit rows about the account keep its id.
"""
import json

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from . import released_permissions
from .db import Base
from .models import AuditLog, User

# Rows that belong to the account itself rather than to its work.
DISPOSABLE_TABLES = {'notification_recipients'}


def _user_columns():
    users = Base.metadata.tables['users']
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            if fk.column.table is users and fk.column.name == 'id':
                yield table, fk.parent


def referenced_user_ids(db, user_ids):
    """Ids among user_ids that some non-disposable row refers to."""
    ids, used = set(user_ids), set()
    if not ids:
        return used
    for table, column in _user_columns():
        if table.name in DISPOSABLE_TABLES:
            continue
        used.update(db.scalars(select(column).where(column.in_(ids)).distinct()).all())
        if used >= ids:
            break
    return used


def deletable_user_ids(db, actor, users):
    candidates = [u.id for u in users if u.id != actor.id and not protected(db, u)]
    return sorted(set(candidates) - referenced_user_ids(db, candidates))


def protected(db, target):
    return target.position == 'director' and released_permissions.is_strategy_user(db, target)


def delete_user(db, actor, target):
    actor, target = released_permissions.lock_user_administration(db, actor, target)
    if target.id == actor.id:
        raise HTTPException(409, "Kendi hesabınızı silemezsiniz.")
    if protected(db, target):
        raise HTTPException(409, "Strateji Müdürü hesabı silinemez. Gerekirse devre dışı bırakın.")
    if referenced_user_ids(db, [target.id]):
        raise HTTPException(409, "Bu hesabın sistemde kaydı var (giriş veya işlem). Hesap silinemez; Devre dışı bırak düğmesini kullanın.")
    details = json.dumps({'email': target.email, 'full_name': target.full_name, 'role': target.role,
                          'department_id': target.department_id, 'position': target.position}, ensure_ascii=False)
    for table, column in _user_columns():
        if table.name in DISPOSABLE_TABLES:
            db.execute(delete(table).where(column == target.id))
    target_id = target.id
    db.delete(target)
    db.add(AuditLog(user_id=actor.id, action='user_delete', entity_type='user', entity_id=target_id, details=details))
    try:
        db.commit()
    except IntegrityError:
        # A reference the model metadata does not know about: keep the account.
        db.rollback()
        raise HTTPException(409, "Bu hesabın sistemde kaydı var. Hesap silinemez; Devre dışı bırak düğmesini kullanın.") from None
    return target_id
