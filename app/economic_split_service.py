"""CIV-045: traceable, exact allocation of existing unallocated economic cells.

The caller commits once. Validation finishes before any replacement is staged;
source deletion, replacement rows and per-cell audits share that transaction.
"""
import hashlib
import json
import re
from datetime import datetime, UTC
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from .models import AuditLog, Department, EconomicValue
from .numbers import parse_number, format_number
from .program_service import PROGRAM_GROUPS, ECONOMIC_CATEGORIES, economic_columns, record
from .value_labels import value_kind_label, funding_label

SPLIT_GROUPS = {key: label for key, label in PROGRAM_GROUPS.items() if key != 'unallocated'}


def split_fingerprint(row):
    return hashlib.sha256(json.dumps(record(row), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def cell_label(row):
    return f'{row.year} {value_kind_label(row.value_kind)} / {ECONOMIC_CATEGORIES.get(row.category, row.category)} / {funding_label(row.funding_type)}'


def unallocated_cells(db, period_id, department_id, *, lock=False):
    query = select(EconomicValue).where(EconomicValue.period_id == period_id,
        EconomicValue.department_id == department_id, EconomicValue.program_group == 'unallocated').order_by(
        EconomicValue.year, EconomicValue.value_kind, EconomicValue.category, EconomicValue.funding_type, EconomicValue.id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    return db.scalars(query).all()


def split_review_state(row):
    # Import stores all review causes in issue. Remove ONLY its allocation cause;
    # an unrelated source discrepancy must still require explicit verification.
    allocation = (rf'Tablo {row.source_table_number}, {row.year} {re.escape(value_kind_label(row.value_kind))}: '
        r'Program grubu dağılımı kaynakta ayrılmamış\. Programlar: .*? '
        r'Tutarları program gruplarına göre doğrulayın\. Kaynak tabloyu kontrol edin\.')
    issue, resolved = re.subn(allocation, '', row.issue or '')
    issue = issue.strip()
    state = row.state
    if state == 'needs_review' and resolved and not issue:
        state = 'verified'
    return state, issue


def split_economic_cells(db, actor, period_id, department_id, cells, reason):
    from .main import editable_submission
    from .master_data_service import period_record

    if actor.role != 'strategy':
        raise HTTPException(403, 'Program grubu dağılımı yalnız Strateji Geliştirme tarafından yapılabilir. Yetkili hesabınızla giriş yapın.')
    # Period activation uses an UPDATE of this same row. Department is the lock
    # shared by released-flow submit, decisions and authorship tracking.
    period = period_record(db, period_id)
    db.refresh(period)
    if period.status == 'closed':
        raise HTTPException(409, f'{period.year} dönemi kapalı; dağılım kaydedilemez. Genel Bakış ekranından dönemi etkinleştirip tekrar deneyin.')
    dept = db.scalar(select(Department).where(Department.id == department_id).with_for_update())
    if not dept:
        raise HTTPException(404, 'Müdürlük bulunamadı. Müdürlük listesinden mevcut bir müdürlük seçin.')
    submission = editable_submission(db, department_id, period_id)
    if submission:
        db.refresh(submission)
    if submission and submission.status in {'submitted', 'approved'}:
        raise HTTPException(409, 'Müdürlük paketi incelemede veya onaylı; dağılım kaydedilemez. İnceleme kuyruğundan paketin iade edilmesini isteyin.')
    reason = str(reason or '').strip()
    if not reason:
        raise HTTPException(422, 'Dağılım gerekçesi zorunlu. Kaynak belgeyi ve dağılım nedenini yazın.')
    sources = unallocated_cells(db, period_id, department_id, lock=True)
    ids = [cell['id'] for cell in cells]
    if not sources or len(set(ids)) != len(ids) or set(ids) != {r.id for r in sources}:
        raise HTTPException(409, 'Dağıtılacak kaynak hücreler değişmiş veya eksik. Sayfayı yenileyip müdürlüğün tüm hücrelerini birlikte kaydedin.')
    by_id = {cell['id']: cell for cell in cells}
    plan = []
    for row in sources:
        cell = by_id[row.id]; label = cell_label(row)
        if cell.get('fingerprint') != split_fingerprint(row):
            raise HTTPException(409, f'{label}: kaynak kayıt değişmiş. Sayfayı yenileyip payları güncel kaynağa göre girin.')
        if row.amount is None or not row.amount.is_finite() or row.amount < 0:
            raise HTTPException(422, f'{label}: kaynak tutar doğrulanmamış. Önce kaynak tutarı doğrulayın, ardından dağılım yapın.')
        if (row.year, row.value_kind) not in economic_columns(period.year) or row.category not in ECONOMIC_CATEGORIES or row.funding_type not in {'inside', 'outside'}:
            raise HTTPException(422, f'{label}: kaynak boyutları geçersiz. Kaynak kaydın yıl, sütun, kategori ve finansman bilgisini kontrol edin.')
        shares = {}
        for group in SPLIT_GROUPS:
            raw = str(cell['shares'].get(group, '')).strip()
            try:
                amount = Decimal(0) if not raw else parse_number(raw, money=True)
                if amount is None:
                    raise ValueError('Çizgi yerine sayısal pay girin veya alanı boş bırakın.')
            except ValueError as exc:
                raise HTTPException(422, f'{label} / {SPLIT_GROUPS[group]}: {exc} Payı düzeltin.') from None
            shares[group] = amount
        total = sum(shares.values(), Decimal(0))
        if total != row.amount:
            raise HTTPException(422, f'{label}: paylar toplamı {format_number(total, money=True)}, '
                f'kaynak tutar {format_number(row.amount, money=True)} (fark {format_number(total-row.amount, money=True)}). Payları düzeltin.')
        targets = {g: a for g, a in shares.items() if a > 0}
        if row.amount == 0:
            group = cell.get('zero_group')
            if group not in SPLIT_GROUPS:
                raise HTTPException(422, f'{label}: sıfır kaynak tutarın atanacağı tek program grubunu seçin.')
            targets = {group: Decimal(0)}
        for group in targets:
            duplicate = db.scalar(select(EconomicValue).where(EconomicValue.period_id == period_id,
                EconomicValue.department_id == department_id, EconomicValue.year == row.year,
                EconomicValue.value_kind == row.value_kind, EconomicValue.category == row.category,
                EconomicValue.funding_type == row.funding_type, EconomicValue.program_group == group))
            if duplicate:
                raise HTTPException(409, f'{label} / {SPLIT_GROUPS[group]}: hedef hücre zaten var (kayıt {duplicate.id}). Kaynakları karşılaştırıp çakışmayı giderin; paylar birleştirilmez.')
        try:
            context = json.loads(row.source_context_json)
            if not isinstance(context, dict):
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(422, f'{label}: kaynak bağlamı geçersiz. Kaynak tablo bilgisini kontrol ettirin.') from None
        plan.append((row, shares, targets, context))

    timestamp = datetime.now(UTC).isoformat()
    # Preserve D-61 via the existing request-scoped authorship hook, including
    # service callers that do not enter through require_user.
    previous_actor = db.info.get('released_actor_id')
    db.info['released_actor_id'] = actor.id
    try:
        pending = []
        for row, shares, targets, context in plan:
            original = record(row)
            context['split_from'] = {'original_id': row.id, 'amount': str(row.amount),
                'raw_text': row.raw_text, 'actor': actor.id, 'time': timestamp, 'reason': reason,
                'state': row.state, 'issue': row.issue,
                'shares': {g: str(a) for g, a in shares.items()}}
            state, issue = split_review_state(row)
            resulting = []
            for group, amount in targets.items():
                replacement = EconomicValue(period_id=period_id, department_id=department_id,
                    year=row.year, value_kind=row.value_kind, category=row.category, program_group=group,
                    funding_type=row.funding_type, amount=amount, raw_text=row.raw_text, state=state, issue=issue,
                    source_card_id=row.source_card_id, source_table_number=row.source_table_number,
                    source_context_json=json.dumps(context, ensure_ascii=False))
                db.add(replacement); resulting.append(replacement)
            pending.append((row, original, resulting))
        db.flush()  # Allocate replacement IDs before recording the final result.
        for row, original, resulting in pending:
            db.add(AuditLog(user_id=actor.id, action='economic_programme_split', entity_type='economic_values',
                entity_id=row.id, details=json.dumps({'period_id':period_id, 'department_id':department_id,
                    'reason':reason, 'time':timestamp, 'original':original,
                    'resulting':[record(r) for r in resulting]}, ensure_ascii=False)))
            db.delete(row)
        db.flush()
    finally:
        if previous_actor is None:
            db.info.pop('released_actor_id', None)
        else:
            db.info['released_actor_id'] = previous_actor
    return len(plan)
