"""Read-only book identities shared by packaged app and operational scripts."""

PREVIOUS_2027_BOOK = (
    '2027-performans-programi_ONAYLI.idml',
    'cbbf9018302d0a1d33d1dde0c4a64a2418d12b55cc29d046205371018673bd71',
)
FIRST_LOAD_BOOKS = {
    2026: ('2026-performans-programi_ONAYLI.idml', '1aaa0bb81c3cf4e245edaab42452a972b8a59ffc252814216c7628f6dbaf33d6'),
    2027: ('2027-performans-programi_SONN_duzeltilmis.idml', '66d9d692bd9c324f6d4f492eca4d75721f28c80e248a971a2a331adf1170bf6f'),
}
READ_ONLY_AUDITS = frozenset({
    ('operations_backup_export', 'database'),
    ('login', 'user'),
    ('department_export_docx', 'department'),
    ('activity_evidence_download', 'activity_evidence_file'),
})


def recognized_source(year, sha256):
    """Historical ONAYLI provenance remains readable until a guarded replacement."""
    sources = [FIRST_LOAD_BOOKS.get(year)]
    if year == 2027:
        sources.append(PREVIOUS_2027_BOOK)
    return next((source for source in sources if source and source[1] == sha256), None)


def active_first_loads(db, period_id):
    """Read history without treating superseded ONAYLI markers as a new load.

    Only the atomic replacement receipt can exclude those exact batch IDs.
    Ambiguous or incomplete receipts fail closed for both CLI and publication
    provenance. All historical rows remain available to the audit screens.
    """
    import json
    from sqlalchemy import select
    from .models import AuditLog, ImportBatch, ReportingPeriod

    loads = db.execute(select(AuditLog, ImportBatch).join(ImportBatch,
        ImportBatch.id == AuditLog.entity_id).where(AuditLog.action == 'first_load_department',
        AuditLog.entity_type == 'import_batch', ImportBatch.period_id == period_id)
        .order_by(AuditLog.id)).all()
    receipts = db.scalars(select(AuditLog).where(AuditLog.action == 'approved_book_2027_replaced',
        AuditLog.entity_type == 'reporting_period', AuditLog.entity_id == period_id)).all()
    if not receipts:
        return loads
    period = db.get(ReportingPeriod, period_id)
    if len(receipts) != 1 or not period or period.id != 2 or period.year != 2027:
        return None
    try:
        receipt = json.loads(receipts[0].details)
        old_ids = receipt['old_batch_ids']
        old = [(a, b) for a, b in loads if b.id in old_ids]
        current = [(a, b) for a, b in loads if b.id not in old_ids]
        if (receipt['year'] != 2027 or receipt['old_sha256'] != PREVIOUS_2027_BOOK[1]
                or receipt['new_sha256'] != FIRST_LOAD_BOOKS[2027][1]
                or len(old_ids) != 34 or len(set(old_ids)) != 34
                or {b.id for _, b in old} != set(old_ids) or len(old) != 34 or len(current) != 34):
            return None
        for audit, batch in old:
            proof = json.loads(audit.details)
            if (batch.status != 'superseded' or batch.filename != PREVIOUS_2027_BOOK[0]
                    or proof['book_sha256'] != PREVIOUS_2027_BOOK[1] or proof['year'] != 2027
                    or audit.id >= receipts[0].id):
                return None
        if any(b.status != 'applied' or b.filename != FIRST_LOAD_BOOKS[2027][0]
               or json.loads(a.details)['book_sha256'] != FIRST_LOAD_BOOKS[2027][1]
               or a.id >= receipts[0].id for a, b in current):
            return None
        return current
    except (KeyError, TypeError, ValueError):
        return None
