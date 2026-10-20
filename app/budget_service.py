"""Controlled exception to D-34. Call mutators only after reading the entire body.

Money stays Decimal; signed preview binds actor, choices and a full scope snapshot.
All writers serialize on departments in ID order, then reread under row locks.
"""
import hashlib
import json
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP, localcontext
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select, exists
from sqlalchemy.orm import aliased

from . import authorization_service as auth
from . import structure_service as structure
from .config import session_secret
from .models import (Activity, ActivityCostValue, EconomicValue, Department, DepartmentCostValue,
    ReportingPeriod, User, Organization, Submission, SubmissionEvent, AuditLog,
    AuthorityDelegation, DirectorateMembership, DelegationRevocation, DirectoratePackage,
    WorkflowEvent, Notification, BudgetOperation, BudgetOperationLine, DepartmentScope)
from .numbers import format_number
from .program_service import ECONOMIC_CATEGORIES, PROGRAM_GROUPS, cost_columns

CENT = Decimal('.01')
ZERO = Decimal('0.00')
AUTHORITY = 'approved_data_correction'
REFERENCES = {'mayor_instruction': 'Başkanlık talimatı', 'council_decision': 'Meclis kararı',
              'executive_decision': 'Encümen kararı', 'mayor_approval': 'Başkan onayı'}
MODELS = {'economic_values': EconomicValue, 'activity_cost_values': ActivityCostValue}
CONFLICT = 'Aktarma önizlemesindeki müdürlük verileri değişti. İşlem uygulanmadı; sayfayı yenileyip yeni önizleme oluşturun.'


def fail(message, status=422):
    raise HTTPException(status, message)


def money(value):
    return format_number(value, money=True)


def decimal_input(value, label, *, cents=False):
    # JSON decimals must be strings, never binary floats. UI sends canonical strings.
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        fail(f'{label} geçersiz. Tutarı metin olarak, en fazla iki ondalıkla girin.')
    try:
        result = Decimal(value)
        if not result.is_finite() or result <= 0 or result >= Decimal('1e18'):
            raise ValueError()
        if cents and result != result.quantize(CENT):
            raise ValueError()
    except (InvalidOperation, ValueError):
        fail(f'{label} geçersiz. Pozitif ve geçerli büyüklükte bir sayı girin (TL için en fazla iki ondalık).')
    return result


def identifier(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        fail(f'{label} seçimi geçersiz. Listeden yeniden seçin.')
    return value


def authorize(db, user):
    user = db.get(User, user.id, populate_existing=True)
    dep = db.get(Department, user.department_id) if user and user.department_id else None
    if not user or not user.is_active or not dep or not dep.is_active:
        fail('Bütçe aktarma yetkisi bulunamadı. Etkin Strateji Geliştirme Müdürüne başvurun.', 403)
    if user.role == 'strategy' and user.position == 'director':
        return dep.organization_id, None
    director = aliased(DirectorateMembership)
    delegate = aliased(DirectorateMembership)
    grantor = aliased(User)
    now = auth.server_now(db)
    grant = db.scalar(select(AuthorityDelegation).join(director, director.id == AuthorityDelegation.director_membership_id)
        .join(delegate, delegate.id == AuthorityDelegation.delegate_membership_id).join(grantor, grantor.id == director.user_id)
        .where(AuthorityDelegation.authority_kind == AUTHORITY, AuthorityDelegation.active.is_(True),
            AuthorityDelegation.organization_id == dep.organization_id, AuthorityDelegation.department_id == dep.id,
            AuthorityDelegation.start_at <= now, AuthorityDelegation.end_at > now,
            director.active.is_(True), director.role_code == 'department_director', director.department_id == dep.id,
            director.organization_id == dep.organization_id, delegate.active.is_(True),
            delegate.role_code == 'department_editor', delegate.user_id == user.id, delegate.department_id == dep.id,
            delegate.organization_id == dep.organization_id, grantor.is_active.is_(True),
            grantor.role == 'strategy', grantor.position == 'director', grantor.department_id == dep.id,
            ~exists().where(DelegationRevocation.delegation_id == AuthorityDelegation.id)))
    if not grant:
        fail('Bütçe aktarma yalnızca Strateji Geliştirme Müdürü veya onaylı veri düzeltme yetkisi devredilen kullanıcı tarafından yapılabilir. Müdürünüzden geçerli yetki devri isteyin.', 403)
    return dep.organization_id, grant.id


def protected(category):
    return category in {'personnel', 'sgk'} or category.split('.')[0] in {'01', '02'}


def distribute(amount, rows):
    """Exact-cent largest remainder, stable ties by persistent value ID."""
    total = sum((r.amount for r in rows), ZERO)
    if total <= 0:
        fail('Seçilen kayıtların dağıtılabilir toplamı sıfır. Pozitif tutarı olan ekonomik hücre ve faaliyet seçin.')
    with localcontext() as ctx:
        ctx.prec = 60
        exact = {r.id: abs(amount) * r.amount / total for r in rows}
        base = {key: value.quantize(CENT, rounding=ROUND_DOWN) for key, value in exact.items()}
        count = int((abs(amount) - sum(base.values(), ZERO)) / CENT)
        for key in sorted(base, key=lambda key: (-(exact[key] - base[key]), key))[:count]:
            base[key] += CENT
    sign = Decimal(-1) if amount < 0 else Decimal(1)
    return {key: value * sign for key, value in base.items()}


def state(row):
    result = {'amount': str(row.amount) if row.amount is not None else None,
              'raw_text': row.raw_text, 'state': row.state}
    if isinstance(row, ActivityCostValue):
        result.update(source_amount=str(row.source_amount) if row.source_amount is not None else None,
                      source_raw_text=row.source_raw_text, source_resolution_json=row.source_resolution_json)
    else:
        result.update(issue=row.issue, source_context_json=row.source_context_json,
                      source_card_id=row.source_card_id, source_table_number=row.source_table_number)
    return result


def canonical(data):
    return auth.encode(data)


def normalized(db, data):
    if not isinstance(data, dict):
        fail('Aktarma bilgileri okunamadı. Formu yeniden doldurun.')
    period = db.get(ReportingPeriod, identifier(data.get('period_id'), 'Dönem'))
    if not period:
        fail('Dönem bulunamadı. Dönem listesini yenileyin.')
    year = data.get('year', period.year)
    kind = data.get('value_kind', 'budget')
    if type(year) is not int or not isinstance(kind, str) or (year, kind) not in cost_columns(period.year):
        fail('Yıl / değer türü bu PP dönemine ait değil. Dönemin bütçe veya tahmin sütununu seçin.')
    legs = data.get('legs')
    if not isinstance(legs, list) or not 1 <= len(legs) <= 100:
        fail('En az bir, en fazla 100 aktarma satırı girin.')
    for leg in legs:
        if not isinstance(leg, dict):
            fail('Aktarma satırı geçersiz. Müdürlük ve tutarı yeniden girin.')
        identifier(leg.get('department_id'), 'Müdürlük')
        if not isinstance(leg.get('direction'), str) or leg['direction'] not in {'increase', 'decrease'}:
            fail('Aktarma yönü geçersiz. Artır veya Azalt seçin.')
        if ('amount' in leg) == ('ratio' in leg):
            fail('Her satır için yalnızca TL tutarı veya yüzde girin.')
        decimal_input(leg.get('amount', leg.get('ratio')), 'Aktarma tutarı / oranı', cents='amount' in leg)
        for key in ('excluded_categories', 'excluded_activities'):
            if key in leg and (not isinstance(leg[key], list) or len(leg[key]) > 10000):
                fail('Uygun kayıt seçimi geçersiz. Önizlemeyi yenileyin.')
        if any(not isinstance(x, str) for x in leg.get('excluded_categories', [])) or any(type(x) is not int for x in leg.get('excluded_activities', [])):
            fail('Uygun kayıt seçimi geçersiz. Önizlemeyi yenileyin.')
    for key in ('change_total', 'change_outside'):
        if key in data and not isinstance(data[key], bool):
            fail('Bütçe seçenekleri geçersiz. Kutucukları yeniden seçin.')
    return period, year, kind, legs


def operation_date(db):
    return auth.server_now(db).astimezone(ZoneInfo('Europe/Istanbul')).date()


def check_increases(db, ctx, legs):
    """The period profile's closing date is inclusive; reductions remain available."""
    today = operation_date(db)
    for leg in legs:
        profile = ctx['profiles'].get(leg['department_id'])
        if leg['direction'] != 'increase' or not profile or not profile.active_to or profile.active_to >= today:
            continue
        receivers = set()
        for change in structure.live_changes(db):
            if change.change_type not in {'CLOSED', 'MERGED', 'SPLIT'} or change.effective_date != profile.active_to:
                continue
            for link in structure.links_for(db, change.id):
                if link.from_department_id == leg['department_id'] and link.to_department_id:
                    receiver = db.get(Department, link.to_department_id)
                    if receiver:
                        receivers.add(structure.period_name(db, ctx['period'].id, receiver))
        receiving = ', '.join(sorted(receivers)) if receivers else 'yapı kararında devralan müdürlük belirtilmemiş'
        fail(f'{ctx["names"][leg["department_id"]]}: müdürlük {profile.active_to.strftime("%d.%m.%Y")} tarihinde kapandı/birleşti; bütçe artışı yapılamaz. '
             f'Yapı kararındaki devralan müdürlükler: {receiving}. Artış için devralan müdürlük seçin; gerekirse Kurum Yapısı kararını kontrol edin.')


def scope(db, user, data, *, lock=False, require_approved=True):
    period, year, kind, legs = normalized(db, data)
    org_id, delegation_id = authorize(db, user)
    dids = sorted({leg['department_id'] for leg in legs})
    if lock:
        # Same order as user administration; delegation revocations lock their department.
        db.scalar(select(Organization).where(Organization.id == org_id).with_for_update())
        for did in sorted(set(dids + [user.department_id])):
            db.scalar(select(Department).where(Department.id == did).with_for_update())
        org_id, delegation_id = authorize(db, user)
    deps = db.scalars(select(Department).where(Department.id.in_(dids), Department.organization_id == org_id)
        .execution_options(populate_existing=True)).all()
    if len(deps) != len(dids):
        fail('Aktarma müdürlüğü kurumunuza ait değil. Müdürlük listesini kontrol edin.', 403)
    def read(query):
        if lock:
            query = query.with_for_update()
        return db.scalars(query.execution_options(populate_existing=True)).all()
    profiles = {profile.department_id: profile for profile in read(select(DepartmentScope).where(
        DepartmentScope.period_id == period.id, DepartmentScope.department_id.in_(dids)).order_by(DepartmentScope.id))}
    names = {dep.id: structure.period_name(db, period.id, dep) for dep in deps}
    for dep in deps:
        if not dep.is_active and not (dep.id in profiles and profiles[dep.id].active_to):
            fail(f'{names[dep.id]}: müdürlük etkin değil ve bu dönemde kayıtlı kapanış tarihi yok. Müdürlük listesini ve dönem profilini kontrol edin.', 403)
    submissions = read(select(Submission).where(Submission.period_id == period.id, Submission.department_id.in_(dids)).order_by(Submission.id))
    packages = read(select(DirectoratePackage).where(DirectoratePackage.period_id == period.id,
        DirectoratePackage.department_id.in_(dids), DirectoratePackage.resource_scope == 'performance_program').order_by(DirectoratePackage.id))
    for dep in deps:
        sub = next((s for s in submissions if s.department_id == dep.id), None)
        pp = [p for p in packages if p.department_id == dep.id]
        if require_approved and (not sub or sub.status != 'approved' or any(p.state != 'strategy_approved' for p in pp)):
            fail(f'{names[dep.id]}: PP paketi onaylı değil. Aktarmadan önce onay sürecini tamamlayın.')
    activities = read(select(Activity).where(Activity.period_id == period.id, Activity.department_id.in_(dids)).order_by(Activity.id))
    economic = read(select(EconomicValue).where(EconomicValue.period_id == period.id, EconomicValue.department_id.in_(dids),
        EconomicValue.year == year, EconomicValue.value_kind == kind).order_by(EconomicValue.id))
    costs = read(select(ActivityCostValue).where(ActivityCostValue.activity_id.in_([a.id for a in activities]),
        ActivityCostValue.year == year, ActivityCostValue.value_kind == kind).order_by(ActivityCostValue.id))
    # Include non-activity costs and every relevant flag/value in stale detection.
    personnel = read(select(DepartmentCostValue).where(DepartmentCostValue.period_id == period.id,
        DepartmentCostValue.department_id.in_(dids), DepartmentCostValue.year == year, DepartmentCostValue.value_kind == kind).order_by(DepartmentCostValue.id))
    snapshot = {'period': [period.id, period.status],
        'department_profiles': [[dep.id, names[dep.id], dep.is_active, structure.profile_data(profiles[dep.id]) if dep.id in profiles else None] for dep in deps],
        'activities': [[a.id, a.department_id, a.name, a.contract_bound] for a in activities],
        'economic': [[r.id, r.department_id, r.category, r.program_group, r.funding_type, state(r)] for r in economic],
        'costs': [[r.id, r.activity_id, r.funding_type, state(r)] for r in costs],
        'personnel': [[r.id, str(r.amount), r.state] for r in personnel],
        'submissions': [[s.id, s.status, s.revision] for s in submissions],
        'packages': [[p.id, p.state, p.version] for p in packages],
        # Detect an apply+reversal cycle even if values return to their old amounts.
        'last_lines': list(db.execute(select(BudgetOperationLine.id).where(BudgetOperationLine.department_id.in_(dids)).order_by(BudgetOperationLine.id)).scalars())}
    return dict(period=period, year=year, kind=kind, legs=legs, org_id=org_id, delegation_id=delegation_id,
                deps=deps, profiles=profiles, names=names, activities=activities, economic=economic, costs=costs, submissions=submissions,
                packages=packages, snapshot=hashlib.sha256(canonical(snapshot).encode()).hexdigest())


def plan(db, user, data, *, lock=False, ctx=None):
    ctx = ctx or scope(db, user, data, lock=lock)
    check_increases(db, ctx, ctx['legs'])
    activities = {a.id: a for a in ctx['activities']}
    rows_by_key = {(r.__tablename__, r.id): r for r in ctx['economic'] + ctx['costs']}
    changes, used, summaries, choices = {}, set(), [], []
    net = ZERO
    for index, leg in enumerate(ctx['legs']):
        did = leg['department_id']
        dep = next(d for d in ctx['deps'] if d.id == did)
        name = ctx['names'][did]
        erows = [r for r in ctx['economic'] if r.department_id == did]
        arows = [r for r in ctx['costs'] if activities[r.activity_id].department_id == did]
        available_categories = sorted({r.category for r in erows if not protected(r.category)})
        available_activities = [a for a in ctx['activities'] if a.department_id == did and not a.contract_bound]
        if set(leg.get('excluded_categories', [])) - set(available_categories) or set(leg.get('excluded_activities', [])) - {a.id for a in available_activities}:
            fail(f'{name}: seçilen kayıtlar değişti. Uygun kayıt önizlemesini yenileyin.')
        eligible_e = [r for r in erows if not protected(r.category) and r.category not in leg.get('excluded_categories', [])]
        eligible_a = [r for r in arows if not activities[r.activity_id].contract_bound and r.activity_id not in leg.get('excluded_activities', [])]
        for r in erows + arows:
            if r.funding_type == 'inside' and (r.amount is None or not r.amount.is_finite() or r.amount < 0):
                fail(f'{name}: {r.id} numaralı bütçe içi kaydı eksik veya negatif. Kaynak veriyi doğrulayıp yeniden önizleyin.')
        baseline = sum((r.amount for r in erows if r.funding_type == 'inside'), ZERO)
        if baseline <= 0:
            fail(f'{name}: bütçe içi toplam sıfır. Dağıtım için pozitif kaynak tutarı girin.')
        with localcontext() as precision:
            precision.prec = 60
            amount = decimal_input(leg['amount'], 'Tutar', cents=True) if 'amount' in leg else (baseline * decimal_input(leg['ratio'], 'Oran') / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        if amount >= Decimal('1e18'):
            fail(f'{name}: hesaplanan tutar çok büyük. Oranı veya tutarı azaltın.')
        if amount == 0:
            fail(f'{name}: oran bir kuruşun altında kaldı. Daha büyük tutar veya oran girin.')
        delta = -amount if leg['direction'] == 'decrease' else amount
        ratio = delta / baseline
        outside_delta = ZERO
        if data.get('change_outside', False):
            outside = [r for r in eligible_e if r.funding_type == 'outside']
            if any(r.amount is None or r.amount < 0 for r in outside):
                fail(f'{name}: bütçe dışı ekonomik tutar eksik. Kaynak veriyi doğrulayın.')
            outside_delta = (sum((r.amount for r in outside), ZERO) * ratio).quantize(CENT, rounding=ROUND_HALF_UP)
        for table_label, table_rows in (('ekonomik tablo', eligible_e), ('faaliyetler', eligible_a)):
            for fund, target in [('inside', delta), ('outside', outside_delta)]:
                if fund == 'outside' and not data.get('change_outside', False):
                    continue
                selected = [r for r in table_rows if r.funding_type == fund]
                if any(r.amount is None or r.amount < 0 for r in selected):
                    fail(f'{name}: {"bütçe içi" if fund == "inside" else "bütçe dışı"} dağıtımında eksik / negatif kayıt var. Kaynak veriyi doğrulayın.')
                total = sum((r.amount for r in selected), ZERO)
                if target < 0 and -target > total:
                    fail(f'{name} / {table_label} / {"bütçe içi" if fund == "inside" else "bütçe dışı"}: uygun toplam {money(total)} TL, istenen azalış {money(-target)} TL. Tutarı azaltın veya uygun kayıt seçimini genişletin.')
                if target == 0:
                    continue
                if total <= 0:
                    fail(f'{name} / {table_label}: seçilen dağıtılabilir toplam sıfır. Pozitif tutarı olan kayıtları seçin.')
                allocation = distribute(target, selected)
                for r in selected:
                    key = (r.__tablename__, r.id)
                    if key in used:
                        fail(f'{name}: aynı kayıt iki aktarma satırında seçilmiş. Aynı müdürlükteki satırlar için birbirinden ayrı ekonomik kategori ve faaliyetler seçin.')
                    used.add(key)
                    changes[key] = r.amount + allocation[r.id]
        econ_before = sum((r.amount for r in erows if r.funding_type == 'inside'), ZERO)
        activity_before = sum((r.amount for r in arows if r.funding_type == 'inside'), ZERO)
        summaries.append(dict(department_id=did, name=ctx['names'][dep.id], amount=str(amount), change=str(delta),
            percent=str((ratio * 100).quantize(Decimal('.0001'))), before=str(baseline), after=str(baseline + delta),
            outside_change=str(outside_delta), source_difference=str(econ_before - activity_before)))
        choices.append(dict(index=index, name=ctx['names'][dep.id],
            categories=[{'id': c, 'name': ECONOMIC_CATEGORIES.get(c, c)} for c in available_categories],
            activities=[{'id': a.id, 'name': a.name} for a in available_activities]))
        net += delta
    if net != 0 and not data.get('change_total', False):
        fail('Azalış ve artış toplamları eşit değil. Tutarları eşitleyin veya “Toplam bütçe değişiyor” seçeneğini işaretleyin.')
    # Recompute existing totals only for changed cells. Never invent a missing/blank split.
    groups = {}
    for key, r in rows_by_key.items():
        group = (r.__tablename__, r.activity_id) if isinstance(r, ActivityCostValue) else (r.__tablename__, r.department_id, r.category, r.program_group)
        groups.setdefault(group, {})[r.funding_type] = r
    for parts in groups.values():
        if not any((r.__tablename__, r.id) in changes for r in parts.values()):
            continue
        if 'total' not in parts:
            continue
        if any(f not in parts or parts[f].amount is None for f in ('inside', 'outside', 'total')):
            fail('Toplamı tutulan kaydın iç/dış tutarı eksik. Eksik kaydı doğrulayıp önizlemeyi yeniden oluşturun.')
        total = parts['total']
        computed_before = parts['inside'].amount + parts['outside'].amount
        if total.amount != computed_before:
            fail(f'{total.id} numaralı toplam iç/dış dağılımıyla uyuşmuyor. Kaynak farkını doğrulayıp yeniden önizleyin; aktarma bu farkı sessizce düzeltemez.')
        changes[(total.__tablename__, total.id)] = sum((changes.get((parts[f].__tablename__, parts[f].id), parts[f].amount) for f in ('inside', 'outside')), ZERO)
    lines, warnings = [], []
    for key, row in rows_by_key.items():
        before = state(row)
        after = dict(before)
        after_amount = changes.get(key, row.amount)
        if after_amount is not None and (after_amount < 0 or after_amount >= Decimal('1e20')):
            fail(f'{row.id} numaralı kayıt sınır dışında kalıyor. Aktarma tutarını azaltın.')
        after['amount'] = str(after_amount) if after_amount is not None else None
        changed = row.amount != after_amount
        if changed:
            after['raw_text'] = str(after_amount)
        if isinstance(row, ActivityCostValue):
            act = activities[row.activity_id]
            label, did = act.name, act.department_id
            if row.funding_type == 'total' and row.source_amount is not None:
                resolution = json.loads(row.source_resolution_json or '{}')
                adjustment = Decimal(resolution.get('budget_reallocation_delta', '0'))
                if not {k: v for k, v in resolution.items() if k != 'budget_reallocation_delta'} and row.source_amount != row.amount - adjustment:
                    warnings.append(f'{label}: kaynak toplam farkı {money(row.source_amount - (row.amount - adjustment))} TL korunuyor.')
                if changed:
                    resolution['budget_reallocation_delta'] = str(adjustment + after_amount - row.amount)
                    after['source_resolution_json'] = canonical(resolution)
        else:
            label = f'{ECONOMIC_CATEGORIES.get(row.category, row.category)} / {PROGRAM_GROUPS.get(row.program_group, row.program_group)}'
            did = row.department_id
        lines.append(dict(value_table=key[0], value_id=key[1], department_id=did, label=label,
            funding_type=row.funding_type, before=before['amount'], after=after['amount'],
            change=str(after_amount - row.amount) if after_amount is not None and row.amount is not None else None,
            changed=changed, before_state=before, after_state=after))
    department_results = []
    for dep in ctx['deps']:
        items = [s for s in summaries if s['department_id'] == dep.id]
        before = Decimal(items[0]['before'])
        delta = sum((Decimal(s['change']) for s in items), ZERO)
        department_results.append(dict(department_id=dep.id, name=ctx['names'][dep.id], before=str(before), after=str(before + delta),
            change=str(delta), percent=str((delta / before * 100).quantize(Decimal('.0001')))))
    result = dict(summaries=summaries, department_results=department_results, lines=lines, choices=choices, warnings=warnings, snapshot=ctx['snapshot'])
    return ctx, result


def signer():
    return URLSafeTimedSerializer(session_secret(), salt='civ031-budget-preview-v1')


def preview(db, user, data):
    _, result = plan(db, user, data)
    result['token'] = signer().dumps({'actor': user.id, 'request': data, 'snapshot': result['snapshot']})
    return result


def reference(data, legs):
    phase = data.get('phase')
    if not isinstance(phase, str) or phase not in {'before_adoption', 'after_adoption'}:
        fail('Bütçenin meclis kabul aşaması seçilmedi. Kabul öncesi veya sonrası seçin.')
    if phase == 'before_adoption':
        expected = 'mayor_instruction'
    elif len({leg['department_id'] for leg in legs}) > 1:
        expected = 'council_decision'
    else:
        scope_name = data.get('transfer_scope')
        if not isinstance(scope_name, str) or scope_name not in {'functional_classes', 'other'}:
            fail('Müdürlük içi aktarma sınıfını belirtin: ikinci düzey fonksiyonel sınıflar arası veya diğer.')
        expected = 'executive_decision' if scope_name == 'functional_classes' else 'mayor_approval'
    if data.get('reference_type') != expected:
        fail(f'Bu aşama ve aktarma kapsamı için {REFERENCES[expected]} zorunlu. Dayanak türünü düzeltin.')
    try:
        ref_date = date.fromisoformat(data.get('reference_date', ''))
        if ref_date > date.today():
            raise ValueError()
    except (ValueError, TypeError):
        fail('Dayanak tarihi geçersiz. Gelecekte olmayan geçerli bir tarih girin.')
    number = auth.required(data.get('reference_number'), 'Dayanak sayısı')
    reason = auth.required(data.get('reason'), 'Aktarma gerekçesi')
    if len(number) > 100 or len(reason) > 10000:
        fail('Dayanak sayısı veya gerekçe çok uzun. Sayıyı 100, gerekçeyi 10.000 karakterle sınırlandırın.')
    return dict(phase=phase, reference_type=expected, reference_date=ref_date.isoformat(), reference_number=number, reason=reason)


@contextmanager
def controlled_write(db):
    # Bypass only the ordinary PP edit hook in this synchronous transaction.
    # Authority, approved scope, signed freshness and immutable lines were checked first.
    old = db.info.pop('released_actor_id', None)
    try:
        yield
        db.flush()
    finally:
        if old is not None:
            db.info['released_actor_id'] = old


def persist(db, user, data, ctx, result, ref, *, reverses_id=None):
    with controlled_write(db):
        operation = BudgetOperation(organization_id=ctx['org_id'], period_id=ctx['period'].id, actor_id=user.id,
            delegation_id=ctx['delegation_id'], year=ctx['year'], value_kind=ctx['kind'], reverses_id=reverses_id,
            request_json=canonical(data), preview_json=canonical(result), **ref)
        db.add(operation)
        db.flush()
        for line in result['lines']:
            if not line['changed']:
                continue
            row = db.get(MODELS[line['value_table']], line['value_id'])
            for key, value in line['after_state'].items():
                setattr(row, key, Decimal(value) if key in {'amount', 'source_amount'} and value is not None else value)
            db.add(BudgetOperationLine(operation_id=operation.id, department_id=line['department_id'],
                value_table=line['value_table'], value_id=line['value_id'], label=line['label'], funding_type=line['funding_type'],
                before=Decimal(line['before']), after=Decimal(line['after']),
                before_json=canonical(line['before_state']), after_json=canonical(line['after_state'])))
        label = REFERENCES[ref['reference_type']] + ' ile aktarma' + (' — geri alma' if reverses_id else '')
        note = f'{label} #{operation.id}; {ref["reference_date"]} / {ref["reference_number"]}: {ref["reason"]}'
        for sub in ctx['submissions']:
            department_note = f'{ctx["names"][sub.department_id]}: {note}'
            sub.revision += 1
            db.add(SubmissionEvent(submission_id=sub.id, department_id=sub.department_id, period_id=sub.period_id,
                actor_user_id=user.id, event_type='budget_reallocation', revision=sub.revision, note=department_note,
                snapshot_json=canonical({'budget_operation_id': operation.id, 'reverses_id': reverses_id})))
        for package in ctx['packages']:
            db.add(WorkflowEvent(actor_user_id=user.id, actor_snapshot_json=auth.actor_snapshot(db, user, ctx['org_id']),
                organization_id=ctx['org_id'], department_id=package.department_id, event_type='budget_reallocation',
                resource_type='directorate_package', resource_id=str(package.id), context_json=canonical({'budget_operation_id': operation.id}),
                reason=f'{ctx["names"][package.department_id]}: {note}', source='administrative', correlation_id=str(uuid4())))
        for dep in ctx['deps']:
            delta = sum((Decimal(s['change']) for s in result['summaries'] if s['department_id'] == dep.id), ZERO)
            db.add(Notification(role='department', department_id=dep.id, event_type='budget_reallocation',
                message=f'{ctx["names"][dep.id]}: {money(delta)} TL bütçe aktarması. {REFERENCES[ref["reference_type"]]} {ref["reference_date"]} / {ref["reference_number"]}'[:500],
                link=f'/department/{dep.id}?period_id={operation.period_id}'))
        db.add(AuditLog(user_id=user.id, action='budget_reallocation', entity_type='budget_operation', entity_id=operation.id, details=f'{", ".join(ctx["names"].values())}: {note}'))
    return operation


def apply(db, user, data):
    if not isinstance(data, dict):
        fail('Aktarma isteği geçersiz. Önizlemeyi yeniden oluşturun.')
    try:
        signed = signer().loads(data.get('token', ''), max_age=1800)
    except (BadSignature, SignatureExpired, TypeError):
        fail('Aktarma önizlemesi geçersiz veya süresi dolmuş. Yeni önizleme oluşturun.', 409)
    if signed.get('actor') != user.id:
        fail('Önizleme başka kullanıcıya ait. Kendi hesabınızla önizleme oluşturun.', 403)
    request = signed['request']
    ref = reference(data, request['legs'])
    ctx = scope(db, user, request, lock=True, require_approved=False)
    check_increases(db, ctx, ctx['legs'])
    if ctx['snapshot'] != signed['snapshot']:
        fail(CONFLICT, 409)
    ctx, result = plan(db, user, request, ctx=ctx)
    return persist(db, user, request, ctx, result, ref)


def reverse(db, user, operation_id, data):
    original = db.get(BudgetOperation, operation_id)
    org_id, _ = authorize(db, user)
    if not original or original.organization_id != org_id:
        fail('Aktarma kaydı bulunamadı. İşlem listesini yenileyin.', 404)
    request = json.loads(original.request_json)
    ref = reference(data, request['legs'])
    ctx = scope(db, user, request, lock=True)
    if db.scalar(select(BudgetOperation.id).where(BudgetOperation.reverses_id == original.id)):
        fail('Bu aktarma daha önce geri alındı. Bağlı geri alma kaydını inceleyin.', 409)
    originals = db.scalars(select(BudgetOperationLine).where(BudgetOperationLine.operation_id == original.id).order_by(BudgetOperationLine.id)).all()
    lines = []
    for item in originals:
        row = db.get(MODELS[item.value_table], item.value_id, populate_existing=True)
        later = db.scalar(select(BudgetOperationLine.id).where(BudgetOperationLine.value_table == item.value_table,
            BudgetOperationLine.value_id == item.value_id, BudgetOperationLine.id > item.id).limit(1))
        if not row or canonical(state(row)) != item.after_json or later:
            fail(f'{ctx["names"][item.department_id]} / {item.label}: aktarmadan sonra değer değişti. Geri alma uygulanmadı; güncel kaydı inceleyip yeni aktarma hazırlayın.', 409)
        lines.append(dict(value_table=item.value_table, value_id=item.value_id, department_id=item.department_id,
            label=item.label, funding_type=item.funding_type, before=str(item.after), after=str(item.before),
            change=str(item.before-item.after), changed=True, before_state=json.loads(item.after_json), after_state=json.loads(item.before_json)))
    old_preview = json.loads(original.preview_json)
    summaries = [dict(s, name=ctx['names'][s['department_id']], change=str(-Decimal(s['change'])), outside_change=str(-Decimal(s['outside_change'])),
        percent=str((-Decimal(s['change']) / Decimal(s['after']) * 100).quantize(Decimal('.0001'))) if Decimal(s['after']) else '—',
        before=s['after'], after=s['before']) for s in old_preview['summaries']]
    compensating_request = json.loads(original.request_json)
    for leg, summary in zip(compensating_request['legs'], summaries):
        leg['direction'] = 'increase' if leg['direction'] == 'decrease' else 'decrease'
        leg.pop('ratio', None)
        leg['amount'] = summary['amount']
    check_increases(db, ctx, compensating_request['legs'])
    result = dict(lines=lines, summaries=summaries, warnings=old_preview.get('warnings', []))
    return persist(db, user, compensating_request, ctx, result, ref, reverses_id=original.id)


def set_contract_bound(db, user, activity_id, value):
    if not isinstance(value, bool):
        fail('Sözleşme işareti geçersiz. İşaretli veya işaretsiz seçin.')
    activity = db.get(Activity, activity_id)
    if not activity:
        fail('Faaliyet bulunamadı. Veri giriş listesini yenileyin.', 404)
    own = db.get(Department, user.department_id) if user.department_id else None
    dep = db.get(Department, activity.department_id)
    if not own or own.organization_id != dep.organization_id or not user.is_active or not (
        user.role == 'strategy' or (user.role == 'department' and user.department_id == activity.department_id)):
        fail('Bu faaliyetin sözleşme işaretini değiştiremezsiniz. İlgili müdürlük veya Strateji birimine başvurun.', 403)
    # Activity update routes lock the activity first. Match their ordering.
    db.scalar(select(Activity).where(Activity.id == activity_id).with_for_update())
    db.refresh(activity)
    old = activity.contract_bound
    with controlled_write(db):
        activity.contract_bound = value
        if old != value:
            db.add(AuditLog(user_id=user.id, action='activity_contract_bound', entity_type='activity', entity_id=activity.id,
                details=canonical({'before': old, 'after': value, 'period_id': activity.period_id, 'department_id': activity.department_id})))
    return activity
