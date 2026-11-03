"""CIV-168: doğrulanmış gerçek yedekte, yalnız yerel kopyada 2026 PP provası."""
from contextlib import redirect_stderr, redirect_stdout
import html
import os

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ops.preprint_rehearsal import download_verified_run, identify_context, positive_id
from scripts import first_load_live as live
from scripts.first_load_dryrun import environment, local_test_url
from scripts.rehearse_clear_preprint_2027 import (
    empty_database, restore, snapshot, source_backup, state,
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
    'context': 'Kurum/aktör seçilemedi; sorumlu tek kurum ve mevcut etkin Strateji/yönetici kimliklerini kontrol etsin.',
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
    from app.models import (Activity, DepartmentScope, ImportBatch, Indicator,
                            OfficialActivity, Program, ReportingPeriod)
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
    # Status fields are DB content too: expose only known enum labels.
    status = period.status if period and period.status in {'draft', 'active', 'closed', 'archived'} else 'diğer'
    template = period.template_status if period and period.template_status in {'verified', 'draft', 'pending', 'unverified'} else 'diğer'
    return dict(existed=period is not None, status=status if period else 'yok',
                template_status=template if period else 'yok', counts={
                    model.__tablename__: db.scalar(select(func.count()).select_from(model).where(
                        model.period_id == period.id)) if period else 0
                    for model in (Program, OfficialActivity, ImportBatch, Indicator, Activity, DepartmentScope)})


def protected_state(engine):
    from app.first_load_service import period_rows_hash
    with Session(engine) as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        return dict(hash=period_rows_hash(db, year=2027), counts=period_counts(db, 2027)['counts'])


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
        if step == 'plan' and any(record['source_2026']['counts'][key] for key in
                ('programs', 'official_activities', 'import_batches', 'indicators', 'activities')):
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
        failed_count=len(result['failed']), skipped=len(result['skipped']),
        departments=[dict(name=d['source_name'], action=d['action']) for d in result['departments']])
    for key in ('protected_2027_before', 'protected_2027_after'):
        if key in result:
            record[step][key] = result[key]
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
        with empty_database(url) as engine:
            restore(engine, backup)
            check(record, state(engine) == {k: saved[k] for k in ('public_table_row_counts', 'alembic_version')},
                  'Restore sayımları/şeması manifestle uyuşmuyor; sorumlu doğrulanmış kaynak yedeği kontrol etsin.')
            record['protected_before'] = protected_state(engine)
            with Session(engine) as db:
                db.execute(text('SET TRANSACTION READ ONLY'))
                record['source_2026'] = period_counts(db, 2026)
            plan = run_loader(engine, parsed, ids, record, 'plan')
            check(record, not plan['skipped'] and all(plan['counts'][k] == v for k, v in EXPECTED.items()),
                  'Plan 33 müdürlük / 105 kart / 226 gösterge değil veya müdürlük atlandı; sorumlu plan kararlarını incelesin.')
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
    lines = [f"## 2026 PP yedek provası: {record['status']}", '',
             '| Aşama | Müdürlük | Kart | Gösterge | Ret | Başarısız | Yazılan / atlanan |',
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
    if 'display_names_2026' in record:
        lines += ['', '### Yüklemenin atadığı 2026 kapsam adları', '']
        lines += ['- ' + html.escape(name) for name in record['display_names_2026']]
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
