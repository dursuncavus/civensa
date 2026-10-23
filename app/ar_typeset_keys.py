"""Persisted identities for editable report tables (D-190)."""
import json
from collections import defaultdict, deque
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import String, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class uuid_default(FunctionElement):
    type = String()
    inherit_cache = True


@compiles(uuid_default, 'postgresql')
def pg_uuid(element, compiler, **kw):
    return 'gen_random_uuid()::text'


@compiles(uuid_default, 'sqlite')
def sqlite_uuid(element, compiler, **kw):
    return "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-a' || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))"


def new_key():
    return str(uuid4())


def fingerprint(value):
    """Equality for mutable rows; decimal scale never rotates an identity."""
    if isinstance(value, dict):
        return tuple((k, fingerprint(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(fingerprint(v) for v in value)
    if isinstance(value, (int, Decimal, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    return value


def invalid_key():
    raise HTTPException(422, 'Tablo veya satır anahtarı bu kayda ait değil ya da yinelenmiş. Sayfayı yenileyip kendi raporunuzdaki satırı düzenleyin.')


def checked_key(value):
    if value in (None, ''):
        return None
    try:
        if not isinstance(value, str) or str(UUID(value)) != value:
            invalid_key()
    except (ValueError, AttributeError):
        invalid_key()
    return value


def match_rows(existing, incoming, values):
    """Explicit keys own updates; unkeyed identical legacy saves retain records.

    Matching is only for mutable editor input, never for a historical payload.
    A changed unkeyed row is new; clients carry keys to update an existing row.
    """
    by_key = {r.stable_key: r for r in existing}
    reserved = [checked_key(item.get('stable_key')) for item in incoming if item.get('stable_key')]
    if len(set(reserved)) != len(reserved) or any(key not in by_key for key in reserved):
        invalid_key()
    exact = defaultdict(deque)
    for row in existing:
        exact[values(row)].append(row)
    used = set()
    result = []
    for item in incoming:
        key = checked_key(item.get('stable_key'))
        if key:
            row = by_key.get(key)
            if row is None or key in used:
                invalid_key()
        else:
            candidates = exact[values(item)]
            while candidates and (candidates[0].stable_key in used or candidates[0].stable_key in reserved):
                candidates.popleft()
            row = candidates.popleft() if candidates else None
        if row is not None:
            used.add(row.stable_key)
        result.append(row)
    return result, [r for r in existing if r.stable_key not in used]


def section_keys(db, content):
    from .models import ARSectionTableKey, ARSectionRowKey
    result = []
    for table in db.scalars(select(ARSectionTableKey).where(ARSectionTableKey.content_id == content.id)
                           .order_by(ARSectionTableKey.position, ARSectionTableKey.id)):
        result.append({'position': table.position, 'stable_key': table.stable_key,
            'rows': [r.stable_key for r in db.scalars(select(ARSectionRowKey).where(
                ARSectionRowKey.table_id == table.id).order_by(ARSectionRowKey.position, ARSectionRowKey.id))]})
    return result


def save_section_keys(db, content, blocks, keys=None):
    from .models import ARSectionTableKey, ARSectionRowKey
    old_blocks = json.loads(content.blocks_json)
    tables = list(db.scalars(select(ARSectionTableKey).where(ARSectionTableKey.content_id == content.id)
                            .order_by(ARSectionTableKey.position, ARSectionTableKey.id)))
    old = {t.stable_key: t for t in tables}
    if any(not isinstance(item, dict) or not isinstance(item.get('position'), int)
           or item['position'] < 0 or item['position'] >= len(blocks)
           or blocks[item['position']]['type'] != 'table' for item in (keys or [])):
        invalid_key()
    supplied = {item['position']: item for item in (keys or [])}
    if len(supplied) != len(keys or []):
        invalid_key()
    used = set()
    reserved = {checked_key(item.get('stable_key')) for item in (keys or []) if item.get('stable_key')}
    for position, block in enumerate(blocks):
        if block['type'] != 'table':
            continue
        identity = supplied.get(position, {})
        key = checked_key(identity.get('stable_key'))
        if key:
            table = old.get(key)
            if table is None or key in used:
                invalid_key()
        else:
            table = next((t for t in tables if t.stable_key not in used and t.stable_key not in reserved and
                t.position < len(old_blocks) and old_blocks[t.position] == block), None)
        if table is None:
            table = ARSectionTableKey(document_id=content.document_id, content_id=content.id,
                position=position, stable_key=new_key())
            db.add(table); db.flush()
            old_rows = []
        else:
            old_rows = old_blocks[table.position]['rows']
        used.add(table.stable_key)
        stored = list(db.scalars(select(ARSectionRowKey).where(ARSectionRowKey.table_id == table.id)
                                .order_by(ARSectionRowKey.position, ARSectionRowKey.id)))
        row_keys = identity.get('rows', [])
        if row_keys and len(row_keys) != len(block['rows']):
            invalid_key()
        incoming = [{'cells': cells, 'stable_key': row_keys[i] if row_keys else None}
                    for i, cells in enumerate(block['rows'])]
        def row_value(row):
            return json.dumps(row['cells'] if isinstance(row, dict) else old_rows[row.position], ensure_ascii=False)
        matched, removed = match_rows(stored, incoming, row_value)
        for row in removed:
            db.delete(row)
        for index, row in enumerate(matched):
            if row is None:
                row = ARSectionRowKey(document_id=content.document_id, table_id=table.id,
                    stable_key=new_key(), position=index)
                db.add(row)
            row.position = index
        table.position = position
    for table in tables:
        if table.stable_key not in used:
            for row in db.scalars(select(ARSectionRowKey).where(ARSectionRowKey.table_id == table.id)):
                db.delete(row)
            db.flush()
            db.delete(table)
    db.flush()
