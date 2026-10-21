"""Guarded PP deletion. Caller commits deletion and its complete audit together."""
import json

from fastapi import HTTPException
from sqlalchemy import select, func

from .models import (Activity, AuditLog, Department, DirectoratePackage, EconomicValue,
    Indicator, IndicatorIdentity, IndicatorDefinitionRevision, PackageDecision, PackageRevision, Publication,
    PublicationIndicatorBinding, ReportCard, ReportingPeriod, Submission, SubmissionEvent)
from .program_service import record
from .serialization import json_dumps


def removal_available(db, user, department_id, period):
    """Display permission only; every POST repeats the authoritative checks."""
    if user.role not in {'department', 'strategy'} or period.status == 'closed':
        return False
    if user.role == 'department' and user.department_id != department_id:
        return False
    submission = db.scalar(select(Submission).where(Submission.department_id == department_id,
        Submission.period_id == period.id).execution_options(populate_existing=True))
    packages = db.scalars(select(DirectoratePackage).where(
        DirectoratePackage.department_id == department_id, DirectoratePackage.period_id == period.id,
        DirectoratePackage.resource_scope == 'performance_program').execution_options(populate_existing=True)).all()
    return (not submission or submission.status in {'draft', 'returned'}) and all(
        package.state in {'draft', 'returned'} for package in packages)


def _contains_indicator(content, indicator):
    """Read known snapshot collections; never match unrelated numeric IDs."""
    if not isinstance(content, dict):
        return False
    for item in content.get('indicators', []):
        if item.get('id') == indicator.id or (indicator.persistent_indicator_id and
                item.get('persistent_indicator_id') == indicator.persistent_indicator_id):
            return True
    return any(_contains_indicator(item, indicator) for item in content.get('departments', []))


def _indicator_blockers(db, indicator):
    blockers = []
    identity = indicator.persistent_indicator_id
    if identity and db.scalar(select(Indicator.id).where(
            Indicator.persistent_indicator_id == identity, Indicator.period_id != indicator.period_id).limit(1)):
        blockers.append('kalıcı kimliği başka dönemde kullanılıyor')
    if identity and db.scalar(select(IndicatorDefinitionRevision.id).where(
            IndicatorDefinitionRevision.indicator_id == identity).limit(1)):
        blockers.append('donmuş gösterge tanımı bulunuyor')
    # Values have no separate origin column. Preserve raw source spellings and
    # verified/review decisions, including zero and blank source values.
    if indicator.values:
        blockers.append(f'{len(indicator.values)} kaynak veya doğrulanmış değer kaydı bulunuyor')
    if indicator.status != 'draft':
        blockers.append('gösterge taslak durumunda değil')
    if db.scalar(select(PublicationIndicatorBinding.id).join(Publication).where(
            Publication.period_id == indicator.period_id,
            PublicationIndicatorBinding.snapshot_indicator_id == indicator.id).limit(1)):
        blockers.append('yayımlanmış gösterge bağlantısı bulunuyor')
    snapshots = list(db.scalars(select(Publication.snapshot_json).where(
        Publication.period_id == indicator.period_id)))
    snapshots += list(db.scalars(select(SubmissionEvent.snapshot_json).where(
        SubmissionEvent.period_id == indicator.period_id,
        SubmissionEvent.department_id == indicator.department_id, SubmissionEvent.event_type == 'approve')))
    snapshots += list(db.scalars(select(PackageRevision.content_json).join(DirectoratePackage).where(
        DirectoratePackage.period_id == indicator.period_id,
        DirectoratePackage.department_id == indicator.department_id,
        DirectoratePackage.resource_scope == 'performance_program',
        PackageRevision.id.in_(select(PackageDecision.package_revision_id).where(
            PackageDecision.action.in_(['director_approve', 'strategy_approve']))))))
    for raw in snapshots:
        try:
            content = json.loads(raw)
        except (ValueError, TypeError):
            raise HTTPException(409, f'“{indicator.name}” kaldırılamadı: geçmiş kaydı okunamıyor. Strateji Geliştirme birimine başvurun.') from None
        if _contains_indicator(content, indicator):
            blockers.append('yayımlanmış veya onaylanmış geçmişte yer alıyor')
            break
    return blockers


def remove_draft(db, user, department_id, period_id, model, record_id):
    from .main import check_pp_access, ensure_department_editable

    # Share the department lock with submit/review and the period lock with close.
    department = db.scalar(select(Department).where(Department.id == department_id)
        .with_for_update().execution_options(populate_existing=True))
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.id == period_id)
        .with_for_update().execution_options(populate_existing=True))
    if not department or not period:
        raise HTTPException(404, 'Müdürlük veya dönem bulunamadı. Sayfayı yenileyip tekrar deneyin.')
    check_pp_access(db, user, department_id, period)
    obj = db.scalar(select(model).where(model.id == record_id).with_for_update()
        .execution_options(populate_existing=True))
    if not obj:
        raise HTTPException(404, 'Kaldırılacak kayıt bulunamadı. Sayfayı yenileyin.')
    if obj.department_id != department_id:
        raise HTTPException(403, 'Kayıt bu müdürlüğe ait değil. Kaydın müdürlük ekranını açın.')
    if obj.period_id != period_id:
        record_period = db.get(ReportingPeriod, obj.period_id)
        raise HTTPException(409, f'Kayıt {record_period.year} yılına ait; seçilen dönem {period.year}. Kaydın yılını açıp tekrar deneyin.')
    label = obj.name if model is Indicator else obj.source_title or 'Performans kartı'
    # Refresh workflow projections after waiting for the department lock.
    available = removal_available(db, user, department_id, period)
    try:
        ensure_department_editable(db, user, department_id, period_id, allow_strategy=True)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        raise HTTPException(409, f'“{label}” kaldırılamadı: {exc.detail} Dönem ve paket durumunu Strateji Geliştirme birimiyle kontrol edin.') from None
    if not available:
        raise HTTPException(409, f'“{label}” kaldırılamadı: Müdürlük paketi taslak veya iade durumunda değil. Paketin iade edilmesini isteyin.')
    previous = record(obj)
    if model is Indicator:
        if obj.persistent_indicator_id:
            db.scalar(select(IndicatorIdentity).where(
                IndicatorIdentity.indicator_id == obj.persistent_indicator_id).with_for_update())
        blockers = _indicator_blockers(db, obj)
        if blockers:
            hint = ('Önce göstergenin değerlerini silip kaydedin, sonra kaldırın.'
                if len(blockers) == 1 and obj.values else
                'Geçmişi korumak için kaydı saklayın; Strateji Geliştirme birimine başvurun.')
            raise HTTPException(409, f'“{obj.name}” kaldırılamadı: ' + '; '.join(blockers) + '. ' + hint)
        previous['values'] = [record(value) for value in obj.values]
    else:
        economic_ids = set(db.scalars(select(EconomicValue.id).where(EconomicValue.source_card_id == obj.id)))
        # Imported economic tables can span several cards. source_card_id holds
        # only the last card; source_context_json retains every contributing card.
        for value in db.scalars(select(EconomicValue).where(EconomicValue.period_id == period_id,
                EconomicValue.department_id == department_id)):
            try:
                source = json.loads(value.source_context_json)
            except (ValueError, TypeError):
                continue
            if isinstance(source, dict) and isinstance(source.get('card_ids'), list) and obj.id in source['card_ids']:
                economic_ids.add(value.id)
        counts = [(db.scalar(select(func.count()).select_from(child).where(column == obj.id)), label)
            for child, column, label in [(Indicator, Indicator.card_id, 'gösterge'),
                (Activity, Activity.card_id, 'faaliyet')]]
        counts.append((len(economic_ids), 'ekonomik değer'))
        children = ' ve '.join(f'{count} {label}' for count, label in counts if count)
        if children:
            raise HTTPException(409, f'“{obj.source_title or "Performans kartı"}”: Bu kartta {children} var; önce bunları kaldırın veya başka karta taşıyın.')
    db.add(AuditLog(user_id=user.id, action='indicator_remove' if model is Indicator else 'card_remove',
        entity_type='indicator' if model is Indicator else 'report_card', entity_id=obj.id,
        details=json_dumps({'period_id': period_id, 'department_id': department_id, 'previous': previous}, ensure_ascii=False)))
    # Identity rows and frozen/linked history are deliberately never deleted.
    db.delete(obj)
    db.flush()
