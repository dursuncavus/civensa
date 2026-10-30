"""CIV-160 Strateji-owned narratives using CIV-079 workflow semantics."""
import json
from sqlalchemy import select, or_, and_
from . import internal_control_monitoring_service as m
from .internal_control_models import ICCondition, COMPONENTS, STANDARD_COMPONENTS
from .internal_control_narrative_models import ICNarrativeEvent as Event

FIELDS = [('mission', 'Misyon', 2000), ('vision', 'Vizyon', 2000)]
TAIL_FIELDS = [('strengths', 'Güçlü yönler', 8000), ('improvements', 'Gelişim alanları', 8000),
               ('recommendations', 'Öneriler', 8000), ('band_label', 'Puan aralığı', 100),
               ('band_explanation', 'Puan aralığı açıklaması', 2000)]
ACTIONS = {'save': 'Kaydedildi', 'submit': 'Gönderildi', 'return': 'İade edildi',
           'approve': 'Onaylandı', 'reopen': 'Yeniden açıldı'}


def components(db, period):
    codes = {STANDARD_COMPONENTS[s] for s in db.scalars(select(ICCondition.standard_code).where(ICCondition.plan_id == period.plan_id))}
    return [(code, label) for code, label in COMPONENTS.items() if code in codes]


def fields(db, period):
    return FIELDS + [('component_' + code, label + ' — Bileşen değerlendirmesi', 8000)
                     for code, label in components(db, period)] + TAIL_FIELDS


def latest(db, period_id, *, approved=False):
    query = select(Event).where(Event.period_id == period_id)
    if approved:
        query = query.where(Event.action == 'approve')
    return db.scalar(query.order_by(Event.revision.desc()).limit(1))


def state(db, period_id):
    last = latest(db, period_id)
    return (last.to_status, last.revision) if last else ('draft', 0)


def content(db, period):
    last = latest(db, period.id)
    return json.loads(last.snapshot_json) if last else {key: '' for key, _, _ in fields(db, period)}


def writable(db, actor, period_id, expected_revision):
    m.require_access(db, actor, strategy=True)
    period = m.get_period(db, actor, period_id, lock=True, writable=True)
    actor = m.lock_actor(db, actor, strategy=True)
    status, revision = state(db, period_id)
    if m.number(expected_revision) != revision:
        m.conflict()
    return actor, period, status, revision


def append(db, actor, period, revision, action, origin, destination, snapshot, reason=''):
    record = Event(period_id=period.id, revision=revision+1, action=action, from_status=origin,
        to_status=destination, actor_id=actor.id, actor_name=actor.full_name, reason=reason,
        snapshot_json=m.auth.encode(snapshot), created_at=m.auth.server_now(db))
    db.add(record)
    db.flush()
    return record


def check_required(db, period, snapshot):
    missing = [label for key, label, _ in fields(db, period) if key != 'band_explanation' and not snapshot.get(key, '').strip()]
    if missing:
        m.fail('Rapor anlatı bölümlerinde boş alanlar: ' + ', '.join(missing) + '. Alanları tamamlayıp yeniden gönderin.')


def save(db, actor, period_id, expected_revision, data, *, submit=False):
    actor, period, status, revision = writable(db, actor, period_id, expected_revision)
    if status not in ('draft', 'returned'):
        m.fail('Rapor anlatı bölümleri incelemede veya onaylı. İade ya da gerekçeli yeniden açma işlemini tamamlayın.', status=409)
    snapshot = {}
    for key, label, limit in fields(db, period):
        value = str(data.get(key, '')).strip()
        if len(value) > limit:
            m.fail(f'{label} {m.format_number(limit)} karakter sınırını aşıyor. Metni kısaltıp yeniden kaydedin.', key)
        snapshot[key] = value
    if submit:
        check_required(db, period, snapshot)
    saved = append(db, actor, period, revision, 'save', status, status, snapshot)
    return transition(db, actor, period.id, 'submit', saved.revision) if submit else saved


def transition(db, actor, period_id, action, expected_revision, reason=''):
    actor, period, status, revision = writable(db, actor, period_id, expected_revision)
    snapshot = content(db, period)
    if action == 'submit':
        if status not in ('draft', 'returned'):
            m.conflict()
        check_required(db, period, snapshot)
        destination = 'submitted'
    elif action in ('return', 'approve', 'reopen'):
        m.require_strategy_director(actor)
        if status != ('approved' if action == 'reopen' else 'submitted'):
            m.conflict()
        destination = {'return': 'returned', 'approve': 'approved', 'reopen': 'draft'}[action]
    else:
        m.fail('Anlatı işlemi tanınmıyor. Ekrandaki işlem düğmesini kullanın.', 'action')
    reason = str(reason).strip()
    if action in ('return', 'reopen') and not reason:
        m.fail('İade veya yeniden açma gerekçesi eksik. Gerekçe yazıp yeniden deneyin.', 'reason')
    if action == 'approve':
        boundary = db.scalar(select(Event.revision).where(Event.period_id == period.id,
            Event.action == 'approve').order_by(Event.revision.desc()).limit(1)) or 0
        if db.scalar(select(Event.id).where(Event.period_id == period.id, Event.revision > boundary,
                Event.actor_id == actor.id, Event.action == 'save').limit(1)):
            m.fail(m.SOD_ERROR.format(record='İç Kontrol rapor anlatı bölümleri'), status=403)
    return append(db, actor, period, revision, action, status, destination, snapshot, reason)


def copy_previous(db, actor, period_id, expected_revision):
    actor, period, status, revision = writable(db, actor, period_id, expected_revision)
    if revision:
        m.fail('Bu dönemin anlatısı başlatılmış. Kopyalama yalnız ilk kayıttan önce yapılabilir; mevcut metni düzenleyin.', status=409)
    previous = db.scalar(select(m.Period).where(m.Period.plan_id == period.plan_id,
        or_(m.Period.year < period.year, and_(m.Period.year == period.year, m.Period.half < period.half)))
        .order_by(m.Period.year.desc(), m.Period.half.desc()).limit(1))
    source = latest(db, previous.id, approved=True) if previous else None
    if not source:
        m.fail('Önceki dönemde onaylı rapor anlatısı bulunamadı. Bu dönemin metinlerini girip kaydedin.')
    return save(db, actor, period.id, 0, json.loads(source.snapshot_json))


def approved_mission_vision(db, period_id):
    approved = latest(db, period_id, approved=True)
    if not approved:
        return None
    snapshot = json.loads(approved.snapshot_json)
    return {key: snapshot[key] for key in ('mission', 'vision')}
