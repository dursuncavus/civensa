"""Strategy master data validation; frozen snapshots are never rewritten."""
import json
import unicodedata
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select

from .models import AuditLog, Department, Organization, ReportingPeriod


def normalized_name(value):
    value = unicodedata.normalize('NFC', value)
    return ' '.join(value.split()).translate(str.maketrans({'I': 'ı', 'İ': 'i'})).lower()


def name_value(value, label, limit):
    name = ' '.join(str(value or '').split())
    if not name or len(name) > limit:
        raise HTTPException(422, f'{label} boş veya çok uzun. {label} alanına 1–{limit} karakter girin.')
    return name


def department_duplicates(departments):
    groups = defaultdict(list)
    for item in departments:
        groups[item.organization_id, normalized_name(item.name)].append(item)
    return [items for items in groups.values() if len(items) > 1]


def check_department_name(db, organization_id, name, exclude_id=None):
    # Serialize app-created/renamed departments per institution, without a DB
    # name constraint that would reject existing pilot duplicates.
    org = db.scalar(select(Organization).where(Organization.id == organization_id).with_for_update())
    if not org:
        raise HTTPException(422, 'Kurum bulunamadı. Kurum alanından mevcut bir kurum seçin.')
    for existing in db.scalars(select(Department).where(Department.organization_id == organization_id).order_by(Department.id)):
        if existing.id != exclude_id and normalized_name(existing.name) == normalized_name(name):
            raise HTTPException(409, f'Müdürlük adı “{existing.name}” kaydıyla aynı. Müdürlük adı alanında bu kaydı kullanın veya farklı bir ad girin.')


def active_department(db, department_id):
    dept = db.scalar(select(Department).where(Department.id == department_id).with_for_update().execution_options(populate_existing=True))
    if not dept:
        raise HTTPException(422, 'Müdürlük bulunamadı. Müdürlük alanından mevcut bir kayıt seçin.')
    if not dept.is_active:
        raise HTTPException(422, f'“{dept.name}” müdürlüğü pasif; yeni hesap veya kapsam atanamaz. Kurum Yapısı ekranında müdürlüğü yeniden etkinleştirin veya etkin bir müdürlük seçin.')
    return dept


def period_record(db, period_id):
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.id == period_id).with_for_update())
    if not period:
        raise HTTPException(422, 'Raporlama dönemi bulunamadı. Dönem alanından mevcut bir dönem seçin veya Genel Bakış ekranında dönem oluşturun.')
    return period


def audit_change(db, user, action, obj, old, new):
    db.flush()
    db.add(AuditLog(user_id=user.id, action=action, entity_type=obj.__tablename__, entity_id=getattr(obj, 'id', None),
                    details=json.dumps({'old': old, 'new': new}, ensure_ascii=False, sort_keys=True)))
