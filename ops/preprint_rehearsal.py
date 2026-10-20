"""CIV-058: mevcut yeşil yedek artifact'ini yalnız Actions yerel kopyasında prova et."""
import html
import json
import os
from unittest.mock import patch

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ops.release_rehearsal import BACKUP_DIR, github_json, require_fresh_backup, run_private
from scripts.first_load_dryrun import environment, local_test_url
from scripts import first_load_live as live
from scripts import clear_preprint_2027 as clear
from scripts.rehearse_clear_preprint_2027 import empty_database, restore, source_backup, state, rehearse


def positive_id(value):
    if not value or not str(value).isascii() or not str(value).isdigit() or int(value) <= 0:
        raise live.Refusal('Prova numarası geçersiz; yalnız pozitif sayısal kimlik girin.')
    return int(value)


def download_verified_run(run_id):
    repo = os.environ['GITHUB_REPOSITORY']
    run = github_json(f'repos/{repo}/actions/runs/{run_id}')
    if (run['name'] != 'Daily verified database backup' or run['head_branch'] != 'main'
            or run['status'] != 'completed' or run['conclusion'] != 'success'):
        raise live.Refusal('Kaynak yalnız main dalındaki yeşil Daily verified database backup çalışması olabilir.')
    require_fresh_backup(run['created_at'])
    artifacts = github_json(f'repos/{repo}/actions/runs/{run_id}/artifacts')['artifacts']
    artifacts = [a for a in artifacts if not a['expired'] and a['name'].startswith('civensa-db-backup-')]
    if len(artifacts) != 1:
        raise live.Refusal('Yeşil yedekte tek, süresi dolmamış yedek artifact bulunamadı.')
    BACKUP_DIR.mkdir(mode=0o700)
    run_private(['gh', 'run', 'download', str(run_id), '--repo', repo, '--name',
                 artifacts[0]['name'], '--dir', str(BACKUP_DIR)], 'Yedek artifact indirilemedi.')
    dumps = list(BACKUP_DIR.glob('*.dump'))
    if len(dumps) != 1:
        raise live.Refusal('Artifact içinde tek .dump ve eşleşen manifest bulunmalıdır.')
    return dumps[0], dict(backup_run_id=run_id, artifact_id=artifacts[0]['id'])


def payload_shape(db, period_id):
    """Only counts/known field coverage; never source text, values or user names."""
    from app.models import ImportBatch, AuditLog
    result = {}
    batches = db.scalars(select(ImportBatch).where(ImportBatch.period_id == period_id)).all()
    applied = [b for b in batches if b.status == 'applied' and b.applied_at]
    for batch in batches:
        try:
            payload, snapshot = json.loads(batch.payload_json), json.loads(batch.snapshot_json)
            departments = payload.get('departments', [])
            indicators = [i for d in departments for b in d.get('blocks', []) for i in b.get('indicators', [])]
            values = [v for i in indicators for v in i.get('values', [])]
            costs = [v for d in departments for a in d.get('activities', []) for v in a.get('costs', [])]
            result[str(batch.id)] = dict(
                departments=len(departments), indicators=len(indicators), indicator_values=len(values),
                indicator_values_missing_state=sum('state' not in v for v in values),
                indicator_values_missing_raw_text=sum('raw_text' not in v for v in values),
                activity_costs=len(costs), activity_costs_missing_state=sum('state' not in v for v in costs),
                snapshot_departments=len(snapshot.get('departments', [])),
                snapshot_created_departments=len(snapshot.get('created_department_ids', [])))
        except (TypeError, ValueError, KeyError):
            result[str(batch.id)] = {'shape_readable': False}
    if applied:
        terminal = max(applied, key=lambda b: (b.applied_at, b.id))
        own = db.scalars(select(AuditLog).where(AuditLog.action == 'data_import_apply',
            AuditLog.entity_type == 'import_batch', AuditLog.entity_id == terminal.id)).all()
        result['terminal_apply_audit'] = dict(count=len(own),
            seconds_after_apply=[(a.created_at - terminal.applied_at).total_seconds() for a in own])
    return result


def identify_context(url, dump, saved, record):
    from app.models import Organization, User, ImportBatch, ReportingPeriod
    with empty_database(url) as probe:
        restore(probe, dump)
        if state(probe) != {k: saved[k] for k in ('public_table_row_counts', 'alembic_version')}:
            raise live.Refusal('Kaynak restore sayımları/şeması manifest ile uyuşmuyor.')
        with Session(probe) as db:
            db.execute(text('SET TRANSACTION READ ONLY'))
            orgs = db.scalars(select(Organization.id)).all()
            if len(orgs) != 1:
                raise live.Refusal('Prova yedeğinde tek kurum bulunmalıdır.')
            org = positive_id(os.environ['CIVENSA_REHEARSAL_ORG_ID']) if os.getenv('CIVENSA_REHEARSAL_ORG_ID') else orgs[0]
            if org != orgs[0]:
                raise live.Refusal('Prova kurum numarası yedekteki tek kurumla uyuşmuyor.')
            if os.getenv('CIVENSA_REHEARSAL_ACTOR_ID'):
                actor = db.get(User, positive_id(os.environ['CIVENSA_REHEARSAL_ACTOR_ID']))
            else:
                # Private rehearsal only: use an existing active account, never
                # create/enable a user. Live CLI still requires an explicit ID.
                terminal = db.get(ImportBatch, 10)
                actor = db.get(User, terminal.created_by) if terminal and terminal.created_by else None
                if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
                    actor = db.scalar(select(User).where(User.is_active.is_(True), User.role == 'strategy').order_by(User.id))
                if actor is None:
                    actor = db.scalar(select(User).where(User.is_active.is_(True), User.role == 'admin').order_by(User.id))
            if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
                raise live.Refusal('Yedekte etkin Strateji/yönetici prova aktörü bulunamadı; kullanıcı değiştirilmedi.')
            record['organization_id'], record['actor_id'] = org, actor.id
            period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
            if period:
                from sqlalchemy import func
                from app.models import DepartmentCostValue, Indicator, Activity, Submission, ReportCard, EconomicValue, Publication
                record['source_shape_counts'] = payload_shape(db, period.id)
                record['source_2027_counts'] = {
                    model.__tablename__: db.scalar(select(func.count()).select_from(model).where(model.period_id == period.id))
                    for model in (Indicator, Activity, Submission, ReportCard, EconomicValue, DepartmentCostValue, Publication)}
                record['source_2027_department_cost_counts'] = [
                    dict(department_id=did, rows=count) for did, count in db.execute(
                        select(DepartmentCostValue.department_id, func.count()).where(
                            DepartmentCostValue.period_id == period.id).group_by(DepartmentCostValue.department_id)
                        .order_by(DepartmentCostValue.department_id))]
                record['source_2027_department_cost_year_counts'] = [
                    dict(year=year, rows=count) for year, count in db.execute(
                        select(DepartmentCostValue.year, func.count()).where(
                            DepartmentCostValue.period_id == period.id).group_by(DepartmentCostValue.year)
                        .order_by(DepartmentCostValue.year))]
            return org, actor.id


def main():
    record = dict(status='FAIL', steps=[])
    previous_mask = os.umask(0o077)
    try:
        if os.environ.get('GITHUB_ACTIONS') != 'true':
            raise live.Refusal('Bu çalıştırıcı yalnız Actions içinde kullanılır; yerel prova betiğini kullanın.')
        if (os.environ.get('CIVENSA_REHEARSAL_CONFIRM') != clear.CONFIRMATION
                or os.environ.get('CIVENSA_REHEARSAL_BOOK_CONFIRM') != live.BOOK_SHA256[:12]):
            raise live.Refusal('Geçici kopya için iki yazılı prova onayı gerekli.')
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None,
                         CIVENSA_FIRST_LOAD_DATABASE_URL=None, **cleared):
            url = local_test_url()
            record['phase'] = 'backup-download'
            dump, metadata = download_verified_run(positive_id(os.environ.get('CIVENSA_REHEARSAL_BACKUP_RUN')))
            record.update(metadata)
            os.environ.pop('GH_TOKEN', None)
            os.environ.pop('GITHUB_TOKEN', None)
            record['phase'] = 'source-verification'
            saved = source_backup(dump)
            record.update(source_sha256=saved['sha256'], source_utc_timestamp=saved['utc_timestamp'])
            record['phase'] = 'restore-and-context'
            org, actor = identify_context(url, dump, saved, record)
            # Values came from the manual dispatch/PR request and were validated
            # above. Only local disposable engines are accepted by rehearse().
            responses = iter([os.environ['CIVENSA_REHEARSAL_CONFIRM'], os.environ['CIVENSA_REHEARSAL_BOOK_CONFIRM']])
            with patch('builtins.input', lambda _: next(responses)):
                record['phase'] = 'clear-and-first-load'
                rehearse(dump, org, actor, record)
            record['status'] = 'PASS'
            record['phase'] = 'done'
    except live.Refusal as exc:
        print('DURDU: ' + str(exc))
    except Exception as exc:
        record['failure_kind'] = type(exc).__name__
        print('DURDU: Yedek provası tamamlanamadı; dosya, bağlantı ve satır ayrıntıları gizlendi.')
    finally:
        try:
            print('CIV058_RESULT_JSON=' + json.dumps(record, ensure_ascii=True, sort_keys=True))
            safe = html.escape(json.dumps(record, ensure_ascii=False, indent=2))
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
                stream.write(f"<h2>CIV-058 yedek provası: {record['status']}</h2><pre>{safe}</pre>\n")
        finally:
            os.umask(previous_mask)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
