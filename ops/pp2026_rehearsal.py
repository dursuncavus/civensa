"""CIV-168: doğrulanmış gerçek yedekte, yalnız yerel kopyada 2026 PP provası."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import timezone
import html
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from sqlalchemy import CheckConstraint, DateTime, String, and_, case, cast, func, literal, or_, select, text, tuple_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from ops.preprint_rehearsal import download_verified_run, identify_context, positive_id
from scripts import first_load_live as live
from scripts.first_load_dryrun import environment, local_test_url
from scripts.rehearse_clear_preprint_2027 import (
    empty_database, fresh_clone_backup, restore, snapshot, source_backup, state,
)

CONFIRMATION = '1aaa0bb81c3c'
EXPECTED = dict(departments=33, cards=105, indicators=226)
PHASES = {
    'guards': 'Başlangıç koruması geçmedi; sorumlu elle başlatma, kitap onayı ve yerel test hedefini kontrol etsin.',
    'target': 'Prova hedefi reddedildi; sorumlu CIVENSA_TEST_POSTGRES_URL alanını yalnız 127.0.0.1 üzerinde, sorgu parametresiz geçici PostgreSQL adresiyle düzeltsin.',
    'backup-id': 'Yedek çalışma numarası geçersiz; sorumlu backup_run_id alanına pozitif sayısal Actions çalışma numarasını girsin.',
    'done': 'Geçici kopya temizlenemedi; sorumlu Actions temizlik adımını ve yerel PostgreSQL bağlantılarını kontrol etsin.',
    'download': 'Yedek alınamadı; sorumlu varsayılan daldaki yeşil, 48 saatten yeni doğrulanmış yedeği ve Actions okuma/şifre çözme yetkisini kontrol etsin.',
    'restore': 'Yedek geri yükleme doğrulanamadı; sorumlu manifest, şema ve PostgreSQL 18 araçlarını kontrol etsin.',
    'inventory': '2026 envanteri okunamadı; sorumlu geri yüklenen yerel kopyanın şemasını kontrol etsin.',
    'context': 'Kurum/aktör seçilemedi; sorumlu tek kurum ve mevcut etkin Strateji/yönetici kimliklerini kontrol etsin.',
    'clear-plan': '2026 pilot temizleme planı reddedildi; sorumlu D-388 tablo sayımlarını ve dönem durumlarını yerel kopyada incelesin.',
    'clear-apply': '2026 pilot temizleme tamamlanamadı; sorumlu yeni yerel yedeği, arşiv ve koruma kontrollerini incelesin.',
    'load-backup': 'Temizleme sonrası yerel yedek doğrulanamadı; sorumlu PostgreSQL yedek/geri yükleme araçlarını kontrol etsin.',
    'plan': '2026 planı reddedildi; sorumlu dönem durumunu, mevcut PP sayımlarını ve tekil müdürlük eşleşmelerini kontrol etsin.',
    'apply': '2026 uygulaması tamamlanamadı; sorumlu başarısız müdürlükleri ve yükleyici korumalarını yerel kopyada incelesin.',
    'resume': 'Devam planı tamamlanamadı; sorumlu ilk yükleme izlerini yerel kopyada incelesin.',
    'protection': '2027 koruması doğrulanamadı; sorumlu hash ve önce/sonra sayımlarını incelesin.',
}


def check(record, condition, message):
    if not condition:
        record['message'] = message
        raise live.Refusal(message)


def service_url():
    try:
        url = local_test_url()
        if url.host != '127.0.0.1':
            raise ValueError
    except ValueError:
        raise live.Refusal('Prova yalnız 127.0.0.1 üzerinde sorgu parametresiz geçici PostgreSQL kullanabilir; sorumlu test hedefini düzeltsin.') from None
    return url


def period_counts(db, year):
    from app.models import (Activity, DepartmentCostValue, DepartmentScope, EconomicValue,
                            ImportBatch, Indicator, OfficialActivity, Program, ReportCard, ReportingPeriod)
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
    # Status fields are DB content too: expose only known enum labels.
    status = period.status if period and period.status in {'draft', 'active', 'closed', 'published', 'archived'} else 'diğer'
    template = period.template_status if period and period.template_status in {'verified', 'draft', 'pending', 'unverified'} else 'diğer'
    return dict(existed=period is not None, status=status if period else 'yok',
                template_status=template if period else 'yok', counts={
                    model.__tablename__: db.scalar(select(func.count()).select_from(model).where(
                        model.period_id == period.id)) if period else 0
                    for model in (Program, OfficialActivity, ImportBatch, Indicator, Activity, DepartmentScope,
                                  ReportCard, EconomicValue, DepartmentCostValue)})


def protected_state(engine):
    from app.first_load_service import period_rows_hash
    with Session(engine) as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        return dict(hash=period_rows_hash(db, year=2027), counts=period_counts(db, 2027)['counts'])


VALUE_TABLES = {'indicator_values', 'actual_revisions', 'activity_cost_values',
                'department_cost_values', 'economic_values'}
# String columns are not DB enums. These are application-defined labels only;
# an unrecognized label is grouped as "diğer" inside SQL, before it leaves DB.
APP_AUDIT_ACTIONS = {
    'indicator_update', 'activity_create', 'activity_update', 'activity_delete',
    'department_submit', 'submission_approved', 'submission_returned',
    'actual_revision_create', 'activity_report_revision', 'activity_report_approve',
    'activity_evidence_upload', 'activity_contract_bound', 'economic_programme_split',
    'activity_source_total_decision', 'release_manual_confirmation',
    'import_source_conflict_decision', 'program_create', 'program_update',
    'subprogram_create', 'subprogram_update', 'scope_save', 'structure_scope_save',
    'structure_profile', 'subprogram_responsibilities', 'indicator_remove', 'card_remove',
}
AUDIT_ACTIONS = APP_AUDIT_ACTIONS | {
    'data_import_preview', 'data_import_apply', 'data_import_revert',
    'first_load_department',
    'catalogue_create', 'catalogue_link', 'activity_mapping',
    'activity_mapping_csv', 'activity_mapping_csv_revert', 'activity_evidence_download',
    'template_upload', 'template_verify', 'period_activate',
}
IMPORT_AUDIT_ACTIONS = {'data_import_preview', 'data_import_apply', 'data_import_revert',
                      'first_load_department', 'activity_mapping_csv', 'activity_mapping_csv_revert'}


def period_inventory_tables(year):
    """Discover ownership from metadata, without following shared parents.

    Direct period ownership is authoritative. Children follow every FK path,
    including composite keys and both sides of links; IN avoids duplicate rows.
    Descend to a fixed point: ActualRevision is three hops below a period root.
    Self-history links do not confer ownership of another period's revisions.
    """
    from app.db import Base
    from app.models import ReportingPeriod
    tables = Base.metadata.tables
    periods = select(ReportingPeriod.id).where(ReportingPeriod.year == year)
    owned = {}
    for name, table in tables.items():
        # Other domains also call their own keys period_id (IC monitoring).
        # Column names alone must never join unrelated numeric identifiers.
        direct = [fk.parent.in_(periods) for fk in table.foreign_keys
                  if fk.column.table.name == 'reporting_periods']
        if direct:
            owned[name] = select(table).where(or_(*direct)).cte('inv_' + name)
    owned['reporting_periods'] = select(ReportingPeriod.__table__).where(
        ReportingPeriod.year == year).cte('inv_reporting_periods')
    pending = set(tables) - owned.keys()
    # Build a dependency DAG first, so a child includes all parent paths rather
    # than only the first parent discovered. There are no non-self FK cycles.
    visiting, unrelated = set(), set()

    def discover(name):
        if name in owned:
            return owned[name]
        if name in visiting or name in unrelated:
            return None
        visiting.add(name)
        table, paths = tables[name], []
        for fk in sorted(table.foreign_key_constraints, key=lambda fk: tuple(c.name for c in fk.columns)):
            parent_name = fk.referred_table.name
            if parent_name == name:
                continue
            parent = discover(parent_name)
            if parent is not None:
                local = [element.parent for element in fk.elements]
                remote = [parent.c[element.column.name] for element in fk.elements]
                left = local[0] if len(local) == 1 else tuple_(*local)
                paths.append(left.in_(select(*remote)))
        visiting.remove(name)
        if paths:
            owned[name] = select(table).where(or_(*paths)).cte('inv_' + name)
        else:
            unrelated.add(name)
        return owned.get(name)

    for name in sorted(pending):
        discover(name)
    return dict(sorted(owned.items()))


def inventory_allowed(table_name, column):
    from app.db import Base
    from app.program_service import ECONOMIC_CATEGORIES, PROGRAM_GROUPS
    from app.value_labels import VALUE_KIND_LABELS, FUNDING_LABELS
    allowed = {
        'value_kind': set(VALUE_KIND_LABELS), 'funding_type': set(FUNDING_LABELS),
        'state': {'verified', 'needs_review', 'missing', 'source_conflict'},
        'category': set(ECONOMIC_CATEGORIES) if table_name == 'economic_values' else {'personnel_sgk'},
        'program_group': set(PROGRAM_GROUPS),
    }
    specific = {
        ('reporting_periods', 'status'): {'draft', 'active', 'closed', 'published', 'archived'},
        ('indicators', 'status'): {'draft', 'verified'},
        ('submissions', 'status'): {'draft', 'submitted', 'approved', 'returned'},
        ('submission_events', 'event_type'): {'submitted', 'approved', 'returned', 'budget_reallocation'},
        ('import_batches', 'status'): {'preview', 'applied', 'reverted'},
        ('audit_log', 'action'): AUDIT_ACTIONS,
    }
    table = Base.metadata.tables[table_name]
    known = set(getattr(table.c[column].type, 'enums', ()))
    for constraint in table.constraints:
        if isinstance(constraint, CheckConstraint):
            match = re.search(r'\b' + re.escape(column) + r"\s+IN\s*\(([^)]+)\)", str(constraint.sqltext), re.I)
            if match:
                known.update(re.findall(r"'([^']*)'", match[1]))
    return known or specific.get((table_name, column), allowed.get(column, set()) if table_name in VALUE_TABLES else set())


def inventory_groups(db, name, table):
    """Return counts, safe dimensions, UTC hours and roles, never row content."""
    from app.models import User
    dimensions = []
    for column in ('year', 'value_kind', 'kind', 'state', 'value_type', 'funding_type',
                   'category', 'program_group', 'status', 'action', 'event_type'):
        if column not in table.c:
            continue
        field = table.c[column]
        if column == 'year':
            safe = case((field.between(1900, 2200), field.cast(String)), else_='diğer')
        else:
            safe = case((field.in_(sorted(inventory_allowed(name, column))), field), else_='diğer')
        dimensions.append(safe.label(column))
    actor = next((table.c[c] for c in ('created_by', 'actor_user_id', 'actor_id', 'user_id')
                  if c in table.c and any(fk.column.table.name == 'users'
                                         for fk in table.c[c].foreign_keys)), None)
    source = table
    if actor is not None:
        source = table.outerjoin(User.__table__, User.id == actor)
        role = case((User.role.in_(['strategy', 'department', 'admin']), User.role), else_='other')
    else:
        role = literal('other')
    dimensions.append(role.label('rol'))
    dates = [c for c in table.c if isinstance(c.type, DateTime) and c.name.endswith('_at')]
    aggregates = [func.count().label('sayı')]
    for c in dates:
        aggregates += [func.min(c).label(c.name + '_ilk'), func.max(c).label(c.name + '_son')]
    rows = db.execute(select(*dimensions, *aggregates).select_from(source).group_by(
        *dimensions).order_by(*dimensions)).mappings()
    groups = []
    for row in rows:
        public = dict(row)
        for c in dates:
            for suffix in ('_ilk', '_son'):
                key = c.name + suffix
                stamp = public[key]
                if stamp is not None:
                    stamp = stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp
                public[key] = stamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:00 UTC') if stamp else '—'
        groups.append(public)
    # ImportBatch.created_by records the importer, not application data entry.
    human = role.in_(['department', 'strategy']) if name not in {
        'import_batches', 'ar_financial_imports', 'ic_imports'} else literal(False)
    for column in ('import_batch_id', 'import_id'):
        if column in table.c:
            human = and_(human, table.c[column].is_(None))
    if 'source' in table.c:
        human = and_(human, table.c.source.in_(['manual', 'administrative', 'ex_officio']))
    if name == 'audit_log':
        # Actor attribution is independent of the display allowlist: a new or
        # unknown application action still proves user activity, while its text
        # is reported as "diğer". Exclude the existing importer audit paths.
        payload = cast(case((func.pg_input_is_valid(table.c.details, 'jsonb'), table.c.details),
                            else_='{}'), JSONB)
        manual_catalogue = and_(table.c.action.in_(['catalogue_create', 'catalogue_link']),
                                payload.has_key('source'), payload['source'].astext.is_(None))
        human = and_(human, table.c.action.not_in(sorted(IMPORT_AUDIT_ACTIONS)),
                     or_(table.c.action.not_in(['catalogue_create', 'catalogue_link']), manual_catalogue))
    has_human = bool(db.scalar(select(func.count()).select_from(source).where(human)))
    return groups, has_human


def period_audit_table(owned):
    """Polymorphic audit references for an already discovered ownership graph."""
    from app.db import Base
    audit = Base.metadata.tables['audit_log']
    entity_paths = []
    for name, table in owned.items():
        if 'id' not in table.c:
            continue
        # Both table names and model singular names are used by application logs.
        aliases = {name}
        for mapper in Base.registry.mappers:
            if mapper.local_table.name == name:
                singular = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', mapper.class_.__name__)
                aliases.add(re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', singular).lower())
        entity_paths.append(and_(audit.c.entity_type.in_(sorted(aliases)),
                                 audit.c.entity_id.in_(select(table.c.id))))
    return select(audit).where(or_(*entity_paths)).cte('inv_audit_log')


def period_inventory(engine, year=2026):
    owned = period_inventory_tables(year)
    owned['audit_log'] = period_audit_table(owned)
    inventory = dict(counts={}, groups={}, human=False)
    with Session(engine) as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        db.execute(text("SET LOCAL TIME ZONE 'UTC'"))
        for name, table in sorted(owned.items()):
            count = db.scalar(select(func.count()).select_from(table))
            inventory['counts'][name] = count
            # Include all discovered workflow/evidence tables with dimensions,
            # authors or timestamps, in addition to the five value tables.
            fields = {'status', 'action', 'event_type', 'created_by', 'actor_user_id',
                      'actor_id', 'user_id', 'created_at', 'updated_at', 'submitted_at'}
            if count and (name in VALUE_TABLES or fields.intersection(table.c.keys())):
                groups, human = inventory_groups(db, name, table)
                inventory['groups'][name] = groups
                inventory['human'] |= human
    return inventory


def inventory_lines(inventory):
    lines = ['', '### 2026 dönemi envanteri', '']
    if inventory is None:
        return lines + ['Envanter alınamadı; geri yükleme ve envanter aşamasını kontrol edin.']
    lines += ['| Kayıt | Sayı |', '| --- | ---: |']
    lines += [f'| {name} | {count} |' for name, count in inventory['counts'].items() if count]
    lines += ['', 'Sıfır satırlı tablolar: ' + ', '.join(
        name for name, count in inventory['counts'].items() if not count) + '.', '']
    for names, label in ((VALUE_TABLES, 'Değer kayıtları'),
                         (set(inventory['groups']) - VALUE_TABLES - {'audit_log'}, 'İş akışı kayıtları'),
                         ({'audit_log'}, 'Denetim kayıtları')):
        lines += [f'#### {label}', '']
        for name in sorted(names & inventory['groups'].keys()):
            for group in inventory['groups'][name]:
                lines.append('- ' + name + ': ' + '; '.join(f'{key}={value}' for key, value in group.items()))
        lines.append('')
    lines += ['', 'Kullanıcı girişi var mı: ' + ('EVET' if inventory['human'] else 'HAYIR'),
              'Kural: İçe aktarma dışındaki değer/iş akışı veya döneme bağlı denetim kayıtlarında department ya da strategy aktörü varsa EVET; aktörsüz kayıtlar, içe aktarma işlemleri ve kaynaklı katalog izleri tek başına kullanıcı girişi sayılmaz.']
    return lines


DETAIL = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,62}'
                    r'(, (SQLSTATE [0-9A-Z]{5}|(tablo|kısıt|sütun) [a-z_][a-z0-9_]{0,62}'
                    r'|konum (app|scripts|ops)/[A-Za-z0-9_/]{1,120}\.py:[0-9]{1,6}))*')


def public_detail(detail):
    """Publish a loader failure detail only if it matches failure_detail()'s grammar."""
    return detail if isinstance(detail, str) and DETAIL.fullmatch(detail) else 'ayrıntı gizlendi'


def run_loader(engine, parsed, ids, record, step, **options):
    record['phase'] = step
    before = snapshot(engine) if step != 'apply' else None
    try:
        # The loader prints progress and may carry private validation details in
        # its result. Neither child output nor arbitrary result fields escape.
        with open(os.devnull, 'w') as sink, redirect_stdout(sink), redirect_stderr(sink):
            result = live.execute(engine, parsed, year=2026, **ids, **options)
    except live.Refusal:
        record[step] = dict(refusals=1, failed=[], counts={}, departments=[])
        if step == 'plan' and 'clear-apply' not in record and any(value for key, value in record['source_2026']['counts'].items()
                                  if key != 'department_scopes'):
            check(record, snapshot(engine) == before,
                  'Reddedilen plan satır/sıra değiştirdi; sorumlu yükleyiciyi incelesin.')
            record['plan']['writes'] = 0
            check(record, False, '2026 dönemi dolu; 0 satır yazıldı. Sorumlu aşağıdaki 2026 PP sayımlarını incelesin; --resume ile korumayı aşmayın.')
        raise
    names = {d['name'] for d in parsed['departments']}
    check(record, all(d['source_name'] in names and d['action'] in {'match', 'create', 'skip'}
                      for d in result['departments']),
          'Müdürlük kararları kitapla uyuşmuyor; sorumlu yükleyici planını incelesin.')
    record[step] = dict(
        counts={key: int(value) for key, value in result['counts'].items()}, refusals=0,
        failed=[d['name'] for d in result['failed'] if d['name'] in names],
        # D-396: never the free-text reason (ValueError text may carry payload
        # or private values); only a detail matching the structured grammar.
        failed_details=[dict(name=d['name'], detail=public_detail(d.get('detail')))
                        for d in result['failed'] if d['name'] in names],
        failed_count=len(result['failed']), skipped=len(result['skipped']),
        departments=[dict(name=d['source_name'], action=d['action']) for d in result['departments']])
    for key in ('protected_2027_before', 'protected_2027_after'):
        if key in result:
            record[step][key] = result[key]
    if step == 'apply' and result['failed']:
        # Independent committed-state view: tells a real 2027 change apart from
        # a loader-session artefact when a failed run reports a different hash.
        try:
            record['protected_after'] = protected_state(engine)
        except Exception:
            record.pop('protected_after', None)
    if before is not None:
        check(record, snapshot(engine) == before,
              'Salt okunur plan satır/sıra değiştirdi; sorumlu yükleyiciyi incelesin.')
        record[step]['writes'] = 0
    check(record, not result['failed'],
          'Yükleyicide başarısız müdürlük var; sorumlu aşağıdaki müdürlük listesini yerel kopyada incelesin.')
    return result


def rehearse(backup, record):
    """All entry paths validate the loopback URL before any database operation."""
    cleared = {key: None for key in os.environ if key.startswith('PG')}
    with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None,
                     CIVENSA_FIRST_LOAD_DATABASE_URL=None, **cleared):
        url = service_url()
        record['phase'] = 'restore'
        saved = source_backup(backup)
        parsed = live.verify_book(live.book_config(2026)[0], year=2026)
        # Reuse the existing private probe's exact organization/actor defaults.
        # It restores into its own disposable database and never mutates users.
        record['phase'] = 'context'
        org, actor = identify_context(url, backup, saved, {})
        ids = dict(organization_id=org, actor_id=actor)
        record['phase'] = 'restore'
        with empty_database(url) as engine, TemporaryDirectory(prefix='civ172_private_') as directory:
            restore(engine, backup)
            check(record, state(engine) == {k: saved[k] for k in ('public_table_row_counts', 'alembic_version')},
                  'Restore sayımları/şeması manifestle uyuşmuyor; sorumlu doğrulanmış kaynak yedeği kontrol etsin.')
            record['phase'] = 'inventory'
            record['inventory_2026'] = period_inventory(engine)
            record['protected_before'] = protected_state(engine)
            with Session(engine) as db:
                db.execute(text('SET TRANSACTION READ ONLY'))
                record['source_2026'] = period_counts(db, 2026)
            confirmation = os.environ.get('CIVENSA_REHEARSAL_CLEAR_CONFIRM', '')
            if confirmation:
                from scripts import clear_pilot_2026 as clear
                check(record, confirmation == clear.CONFIRMATION,
                      '2026 pilot temizleme onayı uyuşmuyor; sorumlu clear_confirmation alanına tam onay cümlesini girsin.')
                record['phase'] = 'clear-plan'
                before = snapshot(engine)
                clear_plan = clear.execute(engine, **ids)
                check(record, snapshot(engine) == before,
                      'Temizleme planı satır/sıra değiştirdi; sorumlu temizleme korumasını incelesin.')
                record['clear-plan'] = dict(counts=clear_plan['counts'], writes=0)
                record['phase'] = 'clear-apply'
                proof = fresh_clone_backup(engine, Path(directory), url)
                cleared = clear.execute(engine, **ids, apply=True, backup=proof, confirmation=confirmation)
                check(record, cleared['counts'] == clear_plan['counts']
                      and cleared['protected_2027_before'] == cleared['protected_2027_after']
                      == record['protected_before']['hash'],
                      '2026 temizleme sayımları/2027 hash kontrolü geçmedi; sorumlu temizleme planını incelesin.')
                record['clear-apply'] = dict(counts=cleared['removed_counts'], archive_sha256=cleared['archive_sha256'])
            plan = run_loader(engine, parsed, ids, record, 'plan')
            check(record, not plan['skipped'] and all(plan['counts'][k] == v for k, v in EXPECTED.items()),
                  'Plan 33 müdürlük / 105 kart / 226 gösterge değil veya müdürlük atlandı; sorumlu plan kararlarını incelesin.')
            if confirmation:
                record['phase'] = 'load-backup'
                proof = fresh_clone_backup(engine, Path(directory), url)
                live.verify_backup(proof)
            applied = run_loader(engine, parsed, ids, record, 'apply', apply=True)
            check(record, not applied['skipped'] and all(applied['counts'][k] == v for k, v in EXPECTED.items())
                  and applied['counts'] == plan['counts'],
                  'Uygulama 33/105/226 veya plan sayımlarıyla uyuşmuyor; sorumlu uygulama toplamlarını incelesin.')
            check(record, applied.get('protected_2027_before') == applied.get('protected_2027_after')
                  == record['protected_before']['hash'],
                  'Yükleyicinin 2027 koruma hash kontrolü geçmedi; sorumlu önce/sonra hash değerlerini incelesin.')
            from app.models import DepartmentScope, Indicator, ReportingPeriod
            with Session(engine) as db:
                db.execute(text('SET TRANSACTION READ ONLY'))
                pid = db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2026))
                record['persistent_indicator_id_assigned'] = db.scalar(select(func.count()).select_from(Indicator).where(
                    Indicator.period_id == pid, Indicator.persistent_indicator_id.is_not(None)))
                # Only names assigned by this book load may leave the database.
                dids = [d['department_id'] for d in applied['departments']]
                display_names = list(db.scalars(select(DepartmentScope.display_name).where(
                    DepartmentScope.period_id == pid, DepartmentScope.department_id.in_(dids)).order_by(DepartmentScope.department_id)))
                allowed = set(parsed['book_department_names'].values()) | {''}
                check(record, len(display_names) == 33 and all(name in allowed for name in display_names),
                      '2026 kapsam adları onaylı kitapla uyuşmuyor; sorumlu dönem kapsamlarını yerel kopyada incelesin.')
                record['display_names_2026'] = display_names
            check(record, record['persistent_indicator_id_assigned'] == 0,
                  'Yükleme kalıcı gösterge kimliği atadı; sorumlu 2026 gösterge kimliği korumasını incelesin.')
            resumed = run_loader(engine, parsed, ids, record, 'resume', resume=True)
            check(record, not any(resumed['counts'].values()) and len(resumed['skipped']) == 33
                  and len(resumed['departments']) == 33 and all(d['action'] == 'skip' for d in resumed['departments']),
                  'Devam planı sıfır yazma / 33 müdürlük atlama kontrolünü geçmedi; sorumlu yükleme izlerini incelesin.')
            record['phase'] = 'protection'
            record['protected_after'] = protected_state(engine)  # Fresh independent session after commit/resume.
            check(record, record['protected_before'] == record['protected_after'],
                  'Bağımsız 2027 hash/sayım kontrolü geçmedi; sorumlu korunan dönem farkını yerel kopyada incelesin.')
            record.update(status='PASS', phase='done')


def summary(record):
    """Curated fields only; never dump loader results, exceptions or DB rows."""
    lines = [f"## 2026 PP yedek provası: {record['status']}"]
    lines += inventory_lines(record.get('inventory_2026'))
    if 'clear-plan' in record:
        lines += ['', '### 2026 pilot temizleme', '', 'Plan: 0 satır yazıldı.', '',
                  '| Kayıt | Plan | Silinen |', '| --- | ---: | ---: |']
        cleared = record.get('clear-apply', {})
        lines += [f"| {name} | {count} | {cleared.get('counts', {}).get(name, 0)} |"
                  for name, count in record['clear-plan']['counts'].items() if count]
        lines += ['', 'Arşiv SHA256: `' + cleared.get('archive_sha256', '—') + '`']
    lines += ['', '| Aşama | Müdürlük | Kart | Gösterge | Ret | Başarısız | Yazılan / atlanan |',
             '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for step, label in (('plan', 'Plan'), ('apply', 'Uygulama'), ('resume', 'Devam planı')):
        r = record.get(step, {})
        c = r.get('counts', {})
        tail = f"{r['writes']} yazma / {r.get('skipped', 0)} atlanan" if 'writes' in r else f"{r.get('skipped', '—')} atlanan"
        lines.append(f"| {label} | {c.get('departments', '—')} | {c.get('cards', '—')} | {c.get('indicators', '—')} | {r.get('refusals', '—')} | {r.get('failed_count', '—')} | {tail} |")
    if record.get('message'):
        lines += ['', record['message']]
    lines += ['', f"Kalıcı gösterge kimliği atanan: **{record.get('persistent_indicator_id_assigned', '—')}**."]
    source = record.get('source_2026')
    if source:
        lines += ['', '### Yedekteki 2026 dönemi', '',
                  f"Mevcut: {'evet' if source['existed'] else 'hayır'}; durum: {source['status']}; şablon: {source['template_status']}.", '',
                  '| Kayıt | Sayı |', '| --- | ---: |']
        lines += [f'| {key} | {value} |' for key, value in source['counts'].items()]
    lines += ['', '### 2027 koruması', '', '| Kayıt | Önce | Sonra |', '| --- | ---: | ---: |']
    before, after = record.get('protected_before', {}), record.get('protected_after', {})
    for key in ('indicators', 'activities', 'department_scopes'):
        lines.append(f"| {key} | {before.get('counts', {}).get(key, '—')} | {after.get('counts', {}).get(key, '—')} |")
    lines += ['', f"Restore sonrası hash: `{before.get('hash', '—')}`",
              f"Bağımsız son hash: `{after.get('hash', '—')}`"]
    for key in ('protected_2027_before', 'protected_2027_after'):
        lines.append(f"Yükleyici {key}: `{record.get('apply', {}).get(key, '—')}`")
    for step, label in (('plan', 'Plan'), ('apply', 'Uygulama'), ('resume', 'Devam planı')):
        if step in record:
            lines += ['', f'### {label}: müdürlük kararları ve toplamlar', '',
                      ', '.join(f'{k}: {v}' for k, v in record[step]['counts'].items()), '',
                      '| Müdürlük | Karar |', '| --- | --- |']
            actions = dict(match='eşleştir', create='oluştur', skip='atla')
            for d in record[step]['departments']:
                lines.append(f"| {html.escape(d['name'])} | {actions[d['action']]} |")
            lines += ['', 'Başarısız müdürlükler: ' + (', '.join(html.escape(n) for n in record[step]['failed']) or 'yok')]
            lines += [f"- {html.escape(d['name'])}: `{d['detail']}`"
                      for d in record[step].get('failed_details', [])]
    if 'display_names_2026' in record:
        lines += ['', '### Yüklemenin atadığı 2026 kapsam adları', '']
        lines += ['- ' + (html.escape(name) if name else '(boş)') for name in record['display_names_2026']]
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
        stream.write('\n'.join(lines) + '\n')


def main():
    record = dict(status='FAIL', phase='guards')
    previous_mask = os.umask(0o077)
    try:
        check(record, os.environ.get('GITHUB_ACTIONS') == 'true'
              and os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch', PHASES['guards'])
        check(record, os.environ.get('CIVENSA_REHEARSAL_BOOK_CONFIRM') == CONFIRMATION,
              'Kitap onayı uyuşmuyor; indirme başlamadı. Sorumlu book_confirmation alanına 1aaa0bb81c3c yazsın.')
        from scripts.clear_pilot_2026 import CONFIRMATION as CLEAR_CONFIRMATION
        check(record, os.environ.get('CIVENSA_REHEARSAL_CLEAR_CONFIRM', '') in {'', CLEAR_CONFIRMATION},
              '2026 pilot temizleme onayı uyuşmuyor; indirme başlamadı. Sorumlu clear_confirmation alanını boş bıraksın veya 2026 PILOT DONEMINI SIL yazsın.')
        record['phase'] = 'target'
        service_url()  # Refuse remote targets before even downloading a backup.
        record['phase'] = 'backup-id'
        run_id = positive_id(os.environ.get('CIVENSA_REHEARSAL_BACKUP_RUN'))
        record['phase'] = 'download'
        dump, _ = download_verified_run(run_id)
        os.environ.pop('GH_TOKEN', None)
        os.environ.pop('GITHUB_TOKEN', None)
        rehearse(dump, record)
    except Exception:
        record['status'] = 'FAIL'
        # Imported refusals and SQL/driver errors may include arbitrary content.
        record.setdefault('message', PHASES.get(record['phase'], PHASES['guards']))
    finally:
        try:
            summary(record)  # Sole reporting destination, including failures.
        finally:
            os.umask(previous_mask)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
