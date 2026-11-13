"""CIV-224: request-scoped reuse for read-only listing pages.

The EK-1 listing builds report data for every directorate in one GET request.
On the hosted database each query costs a network round trip (~6 ms), so the
period-wide rows that every directorate reads (İdare document, its budget rows,
the pinned publication, the indicator report, section definitions) are loaded
once per listing instead of once per directorate.

Only an explicit ``listing_memo(db)`` block turns reuse on. Write paths never
enter it, so outside a listing every helper queries exactly as before.
"""
from contextlib import contextmanager

KEY = 'civ224_listing_memo'


@contextmanager
def listing_memo(db):
    if KEY in db.info:
        yield db.info[KEY]
        return
    cache = {}
    db.info[KEY] = cache
    try:
        yield cache
    finally:
        db.info.pop(KEY, None)


def memo(db, key, load):
    cache = db.info.get(KEY)
    if cache is None:
        return load()
    if db.new or db.dirty or db.deleted:
        # A read-only listing never writes; if something does, stop reusing.
        cache.clear()
        return load()
    if key not in cache:
        cache[key] = load()
    return cache[key]
