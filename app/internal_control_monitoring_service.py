"""CIV-079 six-month monitoring, scoped reads and serialized append-only writes."""
from datetime import date
from zoneinfo import ZoneInfo
from sqlalchemy import select, update
from . import authorization_service as auth
from .internal_control_service import require_access
from .internal_control_models import ICPlan, ICAction, ICActionParty, ICCondition, STANDARD_COMPONENTS
from .internal_control_monitoring_models import (ICMonitoringPeriod as Period,
    ICMonitoringPeriodEvent as PeriodEvent, ICMonitoringBatch as Batch,
    ICMonitoringTarget as Target, ICMonitoringEvent as Event, ICMonitoringEntry as Entry,
    ICMonitoringNote as Note)
from .models import Department, User
from .pp_errors import pp_error
from .released_permissions import require_submit, require_strategy_director, SOD_ERROR

STATUSES = {'completed': 'Tamamlandı', 'ongoing': 'Devam ediyor',
            'not_started': 'Başlanmadı', 'delayed': 'Gecikmede'}
STATES = {'draft': 'Taslak', 'submitted': 'Gönderildi', 'returned': 'İade edildi', 'approved': 'Onaylandı'}
TSI = ZoneInfo('Europe/Istanbul')


def fail(message, field='request', status=422):
    raise pp_error(status, message, field)


def number(value, field='expected_revision'):
    value = str(value).strip()
    if not value.isascii() or not value.isdecimal() or len(value) > 9:
        fail('Sayısal alan geçersiz. İlgili alanı kontrol edip yeniden girin.', field)
    return int(value)


def period_label(period):
    return f'{period.year} · ' + ('I. dönem Ocak–Haziran' if period.half == 1 else 'II. dönem Temmuz–Aralık')


def tsi(value):
    return value.astimezone(TSI).strftime('%d.%m.%Y %H:%M TSİ')


def today(db):
    return auth.server_now(db).astimezone(TSI).date()


def get_period(db, actor, period_id, *, lock=False, writable=False):
    require_access(db, actor)
    query = select(Period).where(Period.id == period_id).execution_options(populate_existing=True)
    period = db.scalar(query.with_for_update() if lock else query)
    if not period:
        fail('İzleme dönemi bulunamadı. Dönem listesinden yeniden seçin.', 'period_id', 404)
    if writable and period.closed_at:
        fail('İzleme dönemi kapalı. Strateji Geliştirme birimiyle dönem durumunu kontrol edin.', 'period_id', 409)
    return period


def lock_actor(db, actor, *, strategy=False):
    # Serialize grants/revocations with decisions, then reload current authority.
    db.scalar(select(User).where(User.id == actor.id).with_for_update()
              .execution_options(populate_existing=True))
    return require_access(db, actor, strategy=strategy)


def open_period(db, actor, plan_id, year, half, deadline):
    actor = require_access(db, actor, strategy=True)
    plan = db.scalar(select(ICPlan).where(ICPlan.id == plan_id).with_for_update().execution_options(populate_existing=True))
    actor = lock_actor(db, actor, strategy=True)
    if not plan or plan.status != 'active':
        fail('Etkin plan bulunamadı. İzleme açmadan önce etkin planı seçin.', 'plan_id')
    year, half = number(year, 'year'), number(half, 'half')
    if half not in (1, 2) or not plan.start_year <= year <= plan.end_year:
        fail('Dönem plan yılları dışında veya yarıyıl geçersiz. Plan yılı ve I/II dönem seçin.', 'year')
    try:
        deadline = date.fromisoformat(str(deadline))
    except ValueError:
        fail('Son giriş tarihi geçersiz. Takvimden tarih seçin.', 'deadline')
    if deadline < today(db):
        fail('Son giriş tarihi geçmişte. Bugün veya sonraki bir tarihi seçin.', 'deadline')
    if db.scalar(select(Period.id).where(Period.plan_id == plan.id, Period.closed_at.is_(None))):
        fail('Bu planın açık izleme dönemi var. Önce açık dönemi kapatın.', 'period_id', 409)
    if db.scalar(select(Period.id).where(Period.plan_id == plan.id, Period.year == year, Period.half == half)):
        fail('Bu yarıyıl için izleme dönemi zaten var. Mevcut dönemi açın.', 'half', 409)
    period = Period(plan_id=plan.id, year=year, half=half, deadline=deadline)
    db.add(period)
    db.flush()
    db.add(PeriodEvent(period_id=period.id, action='open', actor_id=actor.id,
                       actor_name=actor.full_name, reason='', created_at=auth.server_now(db)))
    departments = {d.id: d for d in db.scalars(select(Department).where(Department.is_active.is_(True)))}
    batches, seen = {}, set()
    parties = db.scalars(select(ICActionParty).join(ICAction).where(
        ICAction.plan_id == plan.id, ICActionParty.role == 'responsible').order_by(ICActionParty.id)).all()
    for party in parties:
        owners = list(departments) if party.all_departments else [party.department_id]
        for did in owners:
            # An explicitly assigned inactive directorate remains a named obligation.
            dep = db.get(Department, did) if did else None
            key = f'd:{did}' if did else f'b:{party.body_name}'
            if key not in batches:
                batch = Batch(period_id=period.id, scope_key=key, department_id=did,
                    body_name=party.body_name if not did else None, label=dep.name if dep else party.body_name)
                db.add(batch)
                db.flush()
                batches[key] = batch
            batch = batches[key]
            if (batch.id, party.action_id) not in seen:
                db.add(Target(batch_id=batch.id, action_id=party.action_id))
                seen.add((batch.id, party.action_id))
    db.flush()
    return period


def close_period(db, actor, period_id, expected_revision, reason):
    actor = require_access(db, actor, strategy=True)
    period = get_period(db, actor, period_id, lock=True, writable=True)
    actor = lock_actor(db, actor, strategy=True)
    if number(expected_revision) != 1:
        conflict()
    reason = reason.strip()
    if not reason:
        fail('Dönem kapatma gerekçesi eksik. Gerekçe yazıp yeniden kapatın.', 'reason')
    stamp = auth.server_now(db)
    db.add(PeriodEvent(period_id=period.id, action='close', actor_id=actor.id,
        actor_name=actor.full_name, reason=reason, created_at=stamp))
    db.flush()
    db.execute(update(Period).where(Period.id == period.id, Period.closed_at.is_(None)).values(closed_at=stamp))
    db.expire(period)
    return period


def conflict():
    fail('İzleme kaydı başka bir işlemle değişti. Sayfayı yenileyip güncel kayıt üzerinden yeniden deneyin.', status=409)


def latest_event(db, batch_id):
    return db.scalar(select(Event).where(Event.batch_id == batch_id).order_by(Event.revision.desc()).limit(1))


def state(db, batch_id):
    event = latest_event(db, batch_id)
    return (event.to_status, event.revision) if event else ('draft', 0)


def get_batch(db, actor, batch_id, *, lock=False, writable=False, expected_revision=None):
    actor = require_access(db, actor)
    batch = db.get(Batch, batch_id)
    if not batch:
        fail('İzleme paketi bulunamadı. Dönem listesinden yeniden seçin.', status=404)
    if actor.role == 'department' and batch.department_id != actor.department_id:
        fail('Bu müdürlüğün izleme kayıtlarına erişiminiz yok. Kendi müdürlüğünüzün ekranını açın.', status=403)
    # Global order: period, batch. Closing and exporting use the same period lock.
    period = get_period(db, actor, batch.period_id, lock=lock, writable=writable)
    if lock:
        batch = db.scalar(select(Batch).where(Batch.id == batch_id).with_for_update())
        actor = lock_actor(db, actor)
        if actor.role == 'department' and batch.department_id != actor.department_id:
            fail('Müdürlük yetkiniz değişti. Oturumu yenileyip kendi müdürlüğünüzü açın.', status=403)
    status, revision = state(db, batch_id)
    if expected_revision is not None and number(expected_revision) != revision:
        conflict()
    return actor, period, batch, status, revision


def rows(db, batch):
    targets = db.scalars(select(Target).where(Target.batch_id == batch.id).order_by(Target.id)).all()
    versions = db.scalars(select(Entry).join(Target).where(Target.batch_id == batch.id).order_by(Entry.id)).all()
    latest = {v.target_id: v for v in versions}
    return [{'target': t, 'action': db.get(ICAction, t.action_id), 'entry': latest.get(t.id)} for t in targets]


def validate_entry(db, action, data):
    status = str(data.get('status', ''))
    if status not in STATUSES:
        fail(f'{action.action_code_raw} durum alanı geçersiz. Listeden durum seçin.', 'status')
    raw = str(data.get('percentage', '')).strip()
    percentage = number(raw, 'percentage') if raw else None
    if percentage is not None and percentage > 100 or percentage is None and status != 'not_started':
        fail(f'{action.action_code_raw} gerçekleşme oranı geçersiz. 0–100 girin; yalnız Başlanmadı durumunda boş bırakın.', 'percentage')
    reason = str(data.get('reason', '')).strip()
    if status != 'completed' and (status == 'delayed' or action.due_date and action.due_date < today(db)) and not reason:
        fail(f'{action.action_code_raw} tamamlanmama nedeni eksik. Süresi geçen veya geciken eylemin nedenini yazın.', 'reason')
    result = dict(status=status, percentage=percentage, reason=reason)
    for key in ('explanation', 'evidence'):
        result[key] = str(data.get(key, '')).strip()
    if any(len(result[k]) > 10000 for k in ('reason', 'explanation', 'evidence')):
        fail('İzleme açıklaması çok uzun. Açıklama, neden ve kanıt alanlarını 10.000 karaktere kadar kısaltın.', 'explanation')
    return result


def event(db, actor, batch, revision, action, origin, destination, reason='', snapshot=None):
    record = Event(batch_id=batch.id, revision=revision + 1, action=action,
        from_status=origin, to_status=destination, actor_id=actor.id, actor_name=actor.full_name,
        reason=reason, snapshot_json=auth.encode(snapshot or []), created_at=auth.server_now(db))
    db.add(record)
    db.flush()
    return record


def save_entry(db, actor, batch_id, target_id, expected_revision, data):
    actor, period, batch, status, revision = get_batch(db, actor, batch_id, lock=True,
        writable=True, expected_revision=expected_revision)
    if (batch.department_id and actor.role != 'department') or (not batch.department_id and actor.role != 'strategy'):
        fail('Sorumlu birimin kaydını değiştiremezsiniz. Kendi biriminizin giriş ekranını açın.', status=403)
    if today(db) > period.deadline:
        fail('İzleme giriş süresi doldu. Son giriş tarihini Strateji Geliştirme birimiyle kontrol edin.', status=409)
    if status not in ('draft', 'returned'):
        fail('İzleme paketi incelemede veya onaylı. Strateji biriminden gerekçeli iade ya da yeniden açma isteyin.', status=409)
    target = db.get(Target, target_id)
    if not target or target.batch_id != batch.id:
        fail('Eylem bu izleme paketine ait değil. Sayfayı yenileyip listeden seçin.', 'target_id', 404)
    values = validate_entry(db, db.get(ICAction, target.action_id), data)
    record = event(db, actor, batch, revision, 'save', status, status)
    entry = Entry(target_id=target.id, event_id=record.id, **values)
    db.add(entry)
    db.flush()
    return entry


def snapshot(db, batch):
    result = []
    for row in rows(db, batch):
        entry, action = row['entry'], row['action']
        if not entry:
            fail(f'{batch.label}: {action.action_code_raw} izleme girişi eksik. Eylemin durumunu ve oranını kaydedin.', 'status')
        validate_entry(db, action, {k: getattr(entry, k) if getattr(entry, k) is not None else ''
                                   for k in ('status', 'percentage', 'reason', 'explanation', 'evidence')})
        result.append({'target_id': row['target'].id, 'entry_id': entry.id})
    return result


def transition(db, actor, batch_id, action, expected_revision, reason=''):
    actor, period, batch, status, revision = get_batch(db, actor, batch_id, lock=True,
        writable=True, expected_revision=expected_revision)
    if action == 'submit':
        if batch.department_id:
            if actor.role != 'department' or actor.department_id != batch.department_id:
                fail('Bu izleme paketini gönderemezsiniz. Sorumlu müdürlüğün yetkili hesabıyla giriş yapın.', status=403)
        else:
            require_access(db, actor, strategy=True)
        require_submit(actor)
        if today(db) > period.deadline:
            fail('İzleme gönderim süresi doldu. Son giriş tarihini Strateji birimiyle kontrol edin.', status=409)
        destination = 'submitted'
        if status not in ('draft', 'returned'):
            conflict()
    elif action in ('approve', 'return', 'reopen'):
        require_strategy_director(actor)
        destination = {'approve': 'approved', 'return': 'returned', 'reopen': 'draft'}[action]
        if status != ('approved' if action == 'reopen' else 'submitted'):
            conflict()
    else:
        fail('İzleme işlemi tanınmıyor. Ekrandaki işlem düğmesini kullanın.', 'action')
    reason = reason.strip()
    if action in ('return', 'reopen') and not reason:
        fail('İade veya yeniden açma gerekçesi eksik. Gerekçe yazıp yeniden deneyin.', 'reason')
    if action == 'approve':
        # Same revision boundary as require_independent_pp_approver; IC authorship
        # lives in its own typed stream, rather than the PP AuditLog scope.
        boundary = db.scalar(select(Event.revision).where(Event.batch_id == batch.id,
            Event.action.in_(['return', 'reopen'])).order_by(Event.revision.desc()).limit(1)) or 0
        if db.scalar(select(Event.id).where(Event.batch_id == batch.id, Event.revision > boundary,
            Event.actor_id == actor.id, Event.action.in_(['save', 'submit'])).limit(1)):
            fail(SOD_ERROR.format(record='İç Kontrol izleme paketi'), status=403)
    content = snapshot(db, batch) if action in ('submit', 'approve') else []
    return event(db, actor, batch, revision, action, status, destination, reason, content)


def cooperating_actions(db, actor, period):
    actor = require_access(db, actor)
    if actor.role != 'department':
        return []
    ids = select(ICActionParty.action_id).where(ICActionParty.role == 'cooperating',
        (ICActionParty.department_id == actor.department_id) | ICActionParty.all_departments.is_(True))
    return db.scalars(select(ICAction).where(ICAction.plan_id == period.plan_id, ICAction.id.in_(ids)).order_by(ICAction.sort_order)).all()


def add_note(db, actor, period_id, action_id, content):
    actor = require_access(db, actor)
    period = get_period(db, actor, period_id, lock=True, writable=True)
    actor = lock_actor(db, actor)
    if action_id not in {a.id for a in cooperating_actions(db, actor, period)}:
        fail('Bu eylemde işbirliği göreviniz yok. Kendi müdürlüğünüzün işbirliği listesini açın.', status=403)
    if today(db) > period.deadline:
        fail('Katkı notu giriş süresi doldu. Son giriş tarihini Strateji birimiyle kontrol edin.', status=409)
    content = content.strip()
    if not 1 <= len(content) <= 2000:
        fail('Katkı notu boş veya çok uzun. 1–2.000 karakter arasında not yazın.', 'content')
    note = Note(period_id=period.id, action_id=action_id, department_id=actor.department_id,
        actor_id=actor.id, actor_name=actor.full_name, content=content, created_at=auth.server_now(db))
    db.add(note)
    db.flush()
    return note


def visible_notes(db, actor, period):
    actor = require_access(db, actor)
    query = select(Note).where(Note.period_id == period.id)
    if actor.role == 'department':
        own_actions = select(Target.action_id).join(Batch).where(Batch.period_id == period.id,
            Batch.department_id == actor.department_id)
        query = query.where((Note.department_id == actor.department_id) | Note.action_id.in_(own_actions))
    return db.scalars(query.order_by(Note.id)).all()


def overview(db, actor, period):
    require_access(db, actor, strategy=True)
    batches = db.scalars(select(Batch).where(Batch.period_id == period.id).order_by(Batch.label)).all()
    result, counts = [], {}
    for batch in batches:
        status, revision = state(db, batch.id)
        details = rows(db, batch)
        missing = [r['action'].action_code_raw for r in details if not r['entry']]
        result.append(dict(batch=batch, status=status, revision=revision, missing=missing))
        for row in details:
            condition = db.get(ICCondition, row['action'].condition_id)
            key = (STANDARD_COMPONENTS[condition.standard_code], condition.standard_code)
            tally = counts.setdefault(key, {**{s: 0 for s in STATUSES}, 'missing': 0})
            tally[row['entry'].status if row['entry'] else 'missing'] += 1
    return result, counts
