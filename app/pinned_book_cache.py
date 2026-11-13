"""Process-wide cache for parsed, sha256-pinned book publications (CIV-223).

A publication's snapshot never changes once written (its sha256 is pinned), so
a parsed or projected copy can be reused across requests. CIV-220 cached it per
DB session; on the live server the EK-1 listing still fetched and parsed the
multi-MB book on every request (~14 s, D-483).

Integrity is unchanged: once per DB session the stored snapshot is re-hashed
(on PostgreSQL inside the database, so the multi-MB text is not transferred)
and compared with the pinned sha256 before a cached copy is used.

Callers must treat returned objects as read-only and copy anything they hand
out. One entry is kept per kind: memory stays at the old per-request peak.
"""
from collections import OrderedDict
from threading import Lock

from sqlalchemy import func, select

from .activity_contract_service import digest

MAX_ENTRIES = 1
_entries = {}
_lock = Lock()


def _stored_digest(db, publication):
    if db.bind.dialect.name == 'postgresql':
        from .models import Publication
        column = Publication.__table__.c.snapshot_json
        return db.scalar(select(func.encode(func.sha256(func.convert_to(column, 'UTF8')), 'hex'))
                         .where(Publication.__table__.c.id == publication.id))
    return digest(publication.snapshot_json)


def verified(db, publication):
    """True when the stored snapshot still matches its pinned sha256 (memoized per session)."""
    seen = db.info.setdefault('pinned_book_verified', {})
    key = (publication.id, publication.sha256)
    if key not in seen:
        seen[key] = _stored_digest(db, publication) == publication.sha256
    return seen[key]


def get_or_build(db, kind, publication, build):
    """Parsed value for a pinned publication, or None when its digest fails.

    build(snapshot_text) parses the verified snapshot; it runs outside the lock.
    """
    if not verified(db, publication):
        return None
    key = (publication.id, publication.sha256)
    with _lock:
        bucket = _entries.setdefault(kind, OrderedDict())
        if key in bucket:
            bucket.move_to_end(key)
            return bucket[key]
    value = build(publication.snapshot_json)
    with _lock:
        bucket = _entries.setdefault(kind, OrderedDict())
        bucket[key] = value
        bucket.move_to_end(key)
        while len(bucket) > MAX_ENTRIES:
            bucket.popitem(last=False)
    return value


def clear():
    with _lock:
        _entries.clear()
