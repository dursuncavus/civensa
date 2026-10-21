"""Publication-bound annual actuals. All historical records are append-only."""
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func, update, inspect

from .models import (Indicator, Department, ReportingPeriod, Publication, IndicatorIdentity,
                     IndicatorDefinitionRevision, PublicationIndicatorBinding, ActivityReport,
                     ActivityReportRevision, ReportIndicator, ActualRevision, ActivityReportApproval, User,
                     ReportCandidate, ReportCandidateState, ReportRelease)
from .serialization import json_dumps

CURRENT_DEFINITION_CONTRACT = '3.0'


def publication_contract_version(payload):
    # Missing markers are the original v1 semantics, including legacy publications.
    version = payload.get('activity_contract_version', '1.0')
    if version not in {'1.0', '2.0', '3.0'} or payload.get('definition_contract_version', version) != version:
        raise HTTPException(409, 'Bu yayın veri sözleşmesinin desteklenmeyen bir sürümünü kullanıyor.')
    return version


def canonical(data):
    return json_dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def strategy(user):
    if user.role != 'strategy':
        raise HTTPException(403, 'Bu işlem için strateji birimi yetkisi gerekir.')


def authorize(user, department_id=None):
    if user.role == 'strategy':
        return
    if user.role != 'department' or not user.department_id:
        raise HTTPException(403, 'Müdürlük atamanız bulunmuyor. Strateji biriminden yetkinizi kontrol etmesini isteyin.')
    if department_id is not None and user.department_id != department_id:
        raise HTTPException(403, 'Bu gösterge yetkili olduğunuz müdürlüğe ait değil. Kendi müdürlüğünüzün göstergesini açın veya Stratejiden yetkinizi kontrol etmesini isteyin.')


def checked_publication(db, publication_id):
    pub = db.get(Publication, publication_id)
    if not pub:
        raise HTTPException(404, 'Seçilen Performans Programı yayını bulunamadı.')
    if digest(pub.snapshot_json) != pub.sha256:
        raise HTTPException(409, 'Program yayınının bütünlüğü doğrulanamadı. Strateji birimine başvurun.')
    try:
        payload = json.loads(pub.snapshot_json)
        period = db.get(ReportingPeriod, pub.period_id)
        if payload['period'] != period.year or not isinstance(payload['departments'], list):
            raise ValueError()
        publication_contract_version(payload)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(409, 'Program yayınının yıl veya içerik yapısı doğrulanamadı.') from None
    return pub, payload


def snapshot_rows(payload):
    result = {}
    try:
        for department in payload['departments']:
            cards = {card['id']: card for card in department.get('cards', [])}
            for row in department.get('indicators', []):
                sid = row['id']
                if sid in result or row['department_id'] != department['department_id']:
                    raise HTTPException(409, 'Yayın içindeki gösterge bağlantıları tutarsız.')
                result[sid] = dict(row, department=department['department'],
                                   _report_card=cards.get(row.get('card_id')))
    except (KeyError, TypeError, AttributeError):
        raise HTTPException(409, 'Yayın içindeki gösterge yapısı doğrulanamadı.') from None
    return result


def ensure_identity(db, row):
    if not row.persistent_indicator_id:
        dept = db.get(Department, row.department_id)
        identity = IndicatorIdentity(indicator_id=str(uuid4()), organization_id=dept.organization_id)
        db.add(identity); db.flush()
        row.persistent_indicator_id = identity.indicator_id
        db.flush()
    return row.persistent_indicator_id


def _definition_payload_v1(row, year):
    # Annual target is part of the immutable definition, not the global identity.
    fields = ('name', 'code', 'unit', 'explanation', 'calculation_method', 'data_source',
              'card_id', 'subprogram_id', 'department_id')
    data = {key: row.get(key) for key in fields}
    data['year'] = year
    # Do not expose the legacy period-row indicator_id as a global identity.
    data['targets'] = [{key: v.get(key) for key in ('year', 'value_kind', 'value', 'raw_text', 'state')}
                       for v in row.get('values', []) if v['year'] == year and v['value_kind'] == 'target']
    return data


def definition_payload(row, year, contract_version='1.0'):
    # Keep the checkpoint's v1 builder unchanged; never reinterpret old snapshots.
    if contract_version == '1.0':
        return _definition_payload_v1(row, year)
    if contract_version not in {'2.0', '3.0'}:
        raise HTTPException(409, 'Gösterge tanım sözleşmesinin sürümü desteklenmiyor.')
    data = _definition_payload_v1(row, year)
    card = row.get('_report_card')
    if row.get('card_id') is not None:
        if not card or card['department_id'] != row['department_id'] or card['subprogram_id'] != row['subprogram_id']:
            raise HTTPException(409, 'Gösterge tanımı için yayın içindeki kart bağlantısı doğrulanamadı.')
    for field in (('calculation_method', 'data_source', 'explanation') if contract_version == '3.0' else ('calculation_method', 'data_source')):
        own = row.get(field)
        data[field] = own if own and own.strip() else (card or {}).get(field, '')
    data['definition_contract_version'] = contract_version
    return data


def make_definition(db, identity_id, period_id, row, year, user, contract_version='1.0'):
    # Identity lock serializes numbering across publications of different periods.
    identity = db.scalar(select(IndicatorIdentity).where(IndicatorIdentity.indicator_id == identity_id).with_for_update())
    if identity is None:
        raise HTTPException(422, 'Kalıcı gösterge kimliği bulunamadı.')
    text = canonical(definition_payload(row, year, contract_version))
    previous = db.scalar(select(IndicatorDefinitionRevision).where(
        IndicatorDefinitionRevision.indicator_id == identity_id,
        IndicatorDefinitionRevision.period_id == period_id,
        IndicatorDefinitionRevision.sha256 == digest(text)).order_by(IndicatorDefinitionRevision.revision.desc()))
    if previous:
        return previous
    number = (db.scalar(select(func.max(IndicatorDefinitionRevision.revision)).where(
        IndicatorDefinitionRevision.indicator_id == identity_id)) or 0) + 1
    definition = IndicatorDefinitionRevision(indicator_id=identity_id, revision=number,
        period_id=period_id, definition_json=text, sha256=digest(text), created_by=user.id)
    db.add(definition); db.flush()
    return definition


def freeze_program_payload(db, period_id, user):
    from .program_service import book_snapshot
    payload = book_snapshot(db, period_id)
    definitions = {}
    seen = set()
    for row in snapshot_rows(payload).values():
        live = db.get(Indicator, row['id'])
        identity_id = ensure_identity(db, live)
        if identity_id in seen:
            raise HTTPException(409, 'Aynı kalıcı gösterge kimliği bu dönemde birden fazla kayda bağlı.')
        seen.add(identity_id)
        definition = make_definition(db, identity_id, period_id, row, payload['period'], user, CURRENT_DEFINITION_CONTRACT)
        definitions[row['id']] = definition
    for department in payload['departments']:
        for row in department.get('indicators', []):
            definition = definitions[row['id']]
            row['indicator_id'] = definition.indicator_id
            row['persistent_indicator_id'] = definition.indicator_id
            row['definition_revision_id'] = definition.id
    payload['activity_contract_version'] = CURRENT_DEFINITION_CONTRACT
    payload['definition_contract_version'] = CURRENT_DEFINITION_CONTRACT
    return payload, definitions


def attach_publication_definitions(db, pub, definitions, user):
    for sid, definition in definitions.items():
        data = json.loads(definition.definition_json)
        db.add(PublicationIndicatorBinding(publication_id=pub.id, snapshot_indicator_id=sid,
            definition_revision_id=definition.id, department_id=data['department_id'],
            created_by=user.id, reason='Yayın sırasında açık dönem kaydı ilişkisi'))
    db.flush()


def bind_legacy_indicator(db, user, publication_id, snapshot_indicator_id, identity_id, reason):
    strategy(user)
    if not reason.strip():
        raise HTTPException(422, 'Kimlik eşlemesi için gerekçe girin.')
    pub, payload = checked_publication(db, publication_id)
    row = snapshot_rows(payload).get(snapshot_indicator_id)
    if not row:
        raise HTTPException(422, 'Gösterge seçilen yayın sürümünde bulunmuyor.')
    if row.get('definition_revision_id'):
        raise HTTPException(409, 'Bu yayının gösterge sürümü zaten sabitlenmiş.')
    if db.scalar(select(PublicationIndicatorBinding.id).where(
            PublicationIndicatorBinding.publication_id == pub.id,
            PublicationIndicatorBinding.snapshot_indicator_id == snapshot_indicator_id)):
        raise HTTPException(409, 'Yayın göstergesinin kimlik eşlemesi zaten sabitlenmiş.')
    department = db.get(Department, row['department_id'])
    if identity_id:
        identity = db.get(IndicatorIdentity, identity_id)
        if not identity or identity.organization_id != department.organization_id:
            raise HTTPException(422, 'Gösterge kimliği aynı kuruma ait olmalı.')
    else:
        identity = IndicatorIdentity(indicator_id=str(uuid4()), organization_id=department.organization_id)
        db.add(identity); db.flush()
    # No name/code matching, including for old snapshot IDs.
    existing = db.scalars(select(PublicationIndicatorBinding).where(PublicationIndicatorBinding.publication_id == pub.id)).all()
    if any(db.get(IndicatorDefinitionRevision, b.definition_revision_id).indicator_id == identity.indicator_id for b in existing):
        raise HTTPException(409, 'Bu kimlik yayında başka bir göstergeye bağlı.')
    definition = make_definition(db, identity.indicator_id, pub.period_id, row, payload['period'], user,
                                 publication_contract_version(payload))
    binding = PublicationIndicatorBinding(publication_id=pub.id, snapshot_indicator_id=snapshot_indicator_id,
        definition_revision_id=definition.id, department_id=row['department_id'], created_by=user.id, reason=reason)
    db.add(binding); db.flush()
    return binding


def link_period_identity(db, user, period_indicator_id, identity_id, reason):
    strategy(user)
    row = db.get(Indicator, period_indicator_id)
    identity = db.get(IndicatorIdentity, identity_id)
    if not row or not identity or not reason.strip():
        raise HTTPException(422, 'Dönem kaydı, kalıcı kimlik ve eşleme gerekçesi gerekir.')
    dept = db.get(Department, row.department_id)
    if identity.organization_id != dept.organization_id:
        raise HTTPException(422, 'Gösterge kimliği aynı kuruma ait olmalı.')
    if row.persistent_indicator_id and row.persistent_indicator_id != identity_id:
        raise HTTPException(409, 'Bu dönem kaydının kimliği zaten atanmış. Kimlik düzeltmesi ayrı inceleme gerektirir.')
    other = db.scalar(select(Indicator.id).where(Indicator.period_id == row.period_id,
        Indicator.persistent_indicator_id == identity_id, Indicator.id != row.id))
    if other:
        raise HTTPException(409, 'Aynı kimlik bu dönemde başka bir göstergeye bağlı.')
    row.persistent_indicator_id = identity_id
    db.flush()


def publication_bindings(db, pub, payload, organization_id):
    all_rows = snapshot_rows(payload)
    bindings = db.scalars(select(PublicationIndicatorBinding).where(PublicationIndicatorBinding.publication_id == pub.id)).all()
    by_sid = {b.snapshot_indicator_id: b for b in bindings}
    result = []
    for sid, row in all_rows.items():
        dept = db.get(Department, row['department_id'])
        if not dept or dept.organization_id != organization_id:
            continue
        binding = by_sid.get(sid)
        if not binding:
            raise HTTPException(409, f"{row['name']}: eski yayın için açık gösterge kimliği eşlemesi gerekir.")
        definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
        identity = db.get(IndicatorIdentity, definition.indicator_id)
        if (binding.department_id != row['department_id'] or definition.period_id != pub.period_id
                or identity.organization_id != organization_id
                or digest(definition.definition_json) != definition.sha256
                or canonical(definition_payload(row, payload['period'], publication_contract_version(payload))) != definition.definition_json
                or (row.get('definition_revision_id') and row['definition_revision_id'] != definition.id)
                or (row.get('indicator_id') and row['indicator_id'] != definition.indicator_id)):
            raise HTTPException(409, 'Yayın göstergesinin kimlik veya tanım sürümü doğrulanamadı.')
        result.append(binding)
    if not result:
        raise HTTPException(409, 'Seçilen yayında bu kurum için gösterge bulunmuyor.')
    return result


# A1-F2: a non-terminal candidate or any release makes the candidate/release
# workflow the only writer of the report (current_revision, actuals, freeze).
# A report whose candidates are all returned is no longer pre-workflow either:
# its rework must stay on the S3C-2 candidate lineage, so it is refused too.
LIVE_CANDIDATE_STATES = ('assembling', 'final_review', 'final_approved')


def workflow_owner(db, report):
    """Return (description, next step) of the workflow owning the report, or None."""
    # Older populated checkpoints predate candidates/releases: nothing can own the report.
    if not inspect(db.connection()).has_table('report_releases'):
        return None
    release = db.scalar(select(ReportRelease).where(ReportRelease.organization_id == report.organization_id,
        ReportRelease.resource_scope == 'activity_report', ReportRelease.report_key == str(report.id))
        .order_by(ReportRelease.major.desc(), ReportRelease.minor.desc(), ReportRelease.id.desc()))
    if release:
        return f'yayımlanmış {release.major}.{release.minor} sürümü', 'değişiklik için yayımlanmış sürüme düzeltme talebi açın'
    candidates = db.execute(select(ReportCandidate.id, ReportCandidateState.state).join(ReportCandidateState,
        ReportCandidateState.candidate_id == ReportCandidate.id).where(ReportCandidate.organization_id == report.organization_id,
        ReportCandidate.resource_scope == 'activity_report', ReportCandidate.report_key == str(report.id))
        .order_by(ReportCandidate.sequence.desc(), ReportCandidate.id.desc())).all()
    live = next((row for row in candidates if row[1] in LIVE_CANDIDATE_STATES), None)
    if live:
        return f'#{live[0]} numaralı rapor adayı ({live[1]})', 'değişiklik için aday nihai onaycı tarafından iade edilmeli ve Strateji yeni aday oluşturmalıdır'
    if candidates:
        return f'#{candidates[0][0]} numaralı iade edilmiş rapor adayı', 'yeniden çalışma yalnız aday iş akışıyla yapılır: Strateji ilgili müdürlük paketini gerekçeyle yeniden açar ve düzeltilen paketle yeni aday oluşturur'
    return None


def ensure_legacy_writable(db, report, revision=None):
    """Deterministic 409 before any legacy mutation of a workflow-managed report."""
    owner = workflow_owner(db, report)
    if owner:
        raise HTTPException(409, f'Bu Faaliyet Raporu artık aday/yayın iş akışı tarafından yönetiliyor ({owner[0]}). '
            f'Bu ekrandan yeni revizyon, gerçekleşme veya onay kaydı yapılamaz; {owner[1]}.')
    if revision is not None and inspect(db.connection()).has_table('report_candidates') and db.scalar(select(ReportCandidate.id).where(ReportCandidate.activity_revision_id == revision.id)):
        raise HTTPException(409, 'Bu rapor revizyonu bir nihai rapor adayına bağlı. Gerçekleşme eklenemez ve onayı yalnız görevli nihai onaycı verebilir; '
            'güncel rapor revizyonunu açın veya Stratejiyle aday durumunu kontrol edin.')


def returned_after_approval(db, revision):
    """A1-F1: a successor returned from final_approved keeps its freeze as history; never show it as approved."""
    if not inspect(db.connection()).has_table('report_candidates'):
        return False
    return bool(db.scalar(select(ReportCandidate.id).join(ReportCandidateState, ReportCandidateState.candidate_id == ReportCandidate.id)
        .where(ReportCandidate.activity_revision_id == revision.id, ReportCandidateState.state == 'returned_to_strategy')))


def lock_report(db, report):
    version = report.lock_version
    changed = db.execute(update(ActivityReport).where(ActivityReport.id == report.id,
        ActivityReport.lock_version == version).values(lock_version=version + 1),
        execution_options={'synchronize_session': False}).rowcount
    if changed != 1:
        raise HTTPException(409, 'Rapor başka bir kullanıcı tarafından güncellendi. Son sürümü açın.')
    db.refresh(report)


def report_revision(db, user, revision_id):
    authorize(user)
    revision = db.get(ActivityReportRevision, revision_id)
    if not revision:
        raise HTTPException(404, 'Faaliyet Raporu revizyonu bulunamadı.')
    report = db.get(ActivityReport, revision.report_id)
    if user.role == 'department' and db.get(Department, user.department_id).organization_id != report.organization_id:
        raise HTTPException(403, 'Bu rapor kurumunuza ait değil.')
    pub, payload = checked_publication(db, revision.publication_id)
    if (pub.sha256 != revision.publication_sha256 or pub.period_id != report.period_id
            or revision.contract_version != publication_contract_version(payload)):
        raise HTTPException(409, 'Raporun sabit baz yayını doğrulanamadı.')
    return report, revision, pub, payload


def revision_definitions(db, revision):
    result = {}
    for item in db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision.id)):
        binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
        definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
        result[definition.indicator_id] = dict(json.loads(definition.definition_json),
            definition_revision_id=definition.id)
    return result


def create_report_revision(db, user, publication_id, organization_id, report_id=None, expected_revision=0,
                           revision_reason=''):
    strategy(user)
    if not isinstance(revision_reason, str) or len(revision_reason) > 10000:
        raise HTTPException(422, 'Revizyon gerekçesi en fazla 10.000 karakterlik metin olmalı.')
    pub, payload = checked_publication(db, publication_id)
    # Serialize creation within a period without modifying the published snapshot.
    # NO KEY UPDATE: still serializes creation, but lets a concurrent candidate insert take its
    # foreign-key share lock on the period (A1-P1 REL-1: no legacy/assembly deadlock).
    db.scalar(select(ReportingPeriod).where(ReportingPeriod.id == pub.period_id).with_for_update(key_share=True))
    previous = None
    if report_id:
        report = db.scalar(select(ActivityReport).where(ActivityReport.id == report_id).with_for_update())
        if not report or report.organization_id != organization_id or report.period_id != pub.period_id:
            raise HTTPException(422, 'Yeni yayın mevcut raporla aynı yıl ve kuruma ait olmalı.')
        lock_report(db, report)
        ensure_legacy_writable(db, report)
        if report.current_revision != expected_revision:
            raise HTTPException(409, 'Rapor revizyonu değişti. Son sürümü açıp tekrar kontrol edin.')
        previous = db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id == report.id,
            ActivityReportRevision.revision == report.current_revision))
        predecessor_approved = bool(db.scalar(select(ActivityReportApproval.id).where(
            ActivityReportApproval.report_revision_id == previous.id)))
        if predecessor_approved and not revision_reason.strip():
            raise HTTPException(422, 'Onaylı rapor için yeni revizyon oluştururken düzeltme gerekçesi girin.')
        if previous.publication_id == pub.id:
            # Same-base correction of an approved report is valid, too.
            if not predecessor_approved:
                raise HTTPException(409, 'Rapor zaten bu yayın sürümüne bağlı; taslakta gerçekleşmeleri düzenleyebilirsiniz.')
    else:
        if db.scalar(select(ActivityReport.id).where(ActivityReport.organization_id == organization_id, ActivityReport.period_id == pub.period_id)):
            raise HTTPException(409, 'Bu kurum ve yıl için Faaliyet Raporu zaten var. Rapor listesinden mevcut raporu açıp yeni revizyon oluşturun.')
        report = ActivityReport(organization_id=organization_id, period_id=pub.period_id, current_revision=0, lock_version=0)
        db.add(report); db.flush()
    bindings = publication_bindings(db, pub, payload, organization_id)
    before = revision_definitions(db, previous) if previous else {}
    after = {db.get(IndicatorDefinitionRevision, b.definition_revision_id).indicator_id:
        dict(json.loads(db.get(IndicatorDefinitionRevision, b.definition_revision_id).definition_json),
             definition_revision_id=b.definition_revision_id) for b in bindings}
    changes = []
    for identity_id in sorted(before.keys() | after.keys()):
        if before.get(identity_id) != after.get(identity_id):
            changes.append({'indicator_id': identity_id, 'before': before.get(identity_id), 'after': after.get(identity_id)})
    revision = ActivityReportRevision(report_id=report.id, revision=report.current_revision + 1,
        publication_id=pub.id, publication_sha256=pub.sha256, previous_revision_id=previous.id if previous else None,
        diff_json=canonical(changes), created_by=user.id,
        contract_version=publication_contract_version(payload), revision_reason=revision_reason.strip())
    db.add(revision); db.flush()
    for binding in bindings:
        db.add(ReportIndicator(report_revision_id=revision.id, publication_binding_id=binding.id))
    report.current_revision = revision.revision
    db.flush()
    return revision


def parse_actual(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise HTTPException(422, 'Gerçekleşme değerini ondalık metin olarak gönderin.')
    try:
        if not re.fullmatch(r'[+-]?\d+(?:\.\d{1,6})?', value):
            raise ValueError()
        number = Decimal(value)
        if not number.is_finite() or abs(number) >= Decimal('1e20'):
            raise ValueError()
        return number
    except (InvalidOperation, ValueError):
        raise HTTPException(422, 'Sonlu bir sayı ve en fazla 6 ondalık basamak girin.') from None


def save_actual(db, user, report_indicator_id, expected_revision, value, state, evidence, explanation, deviation, uploads=None):
    item = db.get(ReportIndicator, report_indicator_id)
    if not item:
        raise HTTPException(404, 'Rapor göstergesi bulunamadı.')
    binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
    authorize(user, binding.department_id)
    report, revision, pub, payload = report_revision(db, user, item.report_revision_id)
    lock_report(db, report)
    ensure_legacy_writable(db, report, revision)
    if revision.revision != report.current_revision:
        raise HTTPException(409, 'Geçmiş rapor revizyonuna yazılamaz. Güncel revizyonu açın.')
    if db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id == revision.id)):
        raise HTTPException(409, 'Onaylı rapor değiştirilemez. Yeni rapor revizyonu oluşturun.')
    previous = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision.desc()))
    if expected_revision != (previous.revision if previous else 0):
        raise HTTPException(409, 'Bu gerçekleşme başka bir kullanıcı tarafından güncellendi. Son sürümü açın.')
    uploads = uploads or {}
    if uploads and (user.role != 'department' or user.department_id != binding.department_id):
        raise HTTPException(403, 'Kanıt dosyasını yalnız göstergenin müdürlüğü ekleyebilir. Kendi müdürlüğünüzün kullanıcısıyla giriş yapın; Strateji dosyaları okuyabilir.')
    try:
        number = parse_actual(value)
    except HTTPException as error:
        raise HTTPException(error.status_code, {'message': error.detail, 'field': 'value'}) from None
    if state not in {'verified', 'needs_review', 'missing'} or (state == 'verified' and number is None) or (state == 'missing' and number is not None):
        raise HTTPException(422, 'Gerçekleşme ve veri durumu uyumsuz. Doğrulanmış için sayı girin; veri yoksa Eksik seçip alanı boş bırakın. Boş değer sıfır değildir.')
    if not isinstance(evidence, list) or len(evidence) > 30:
        raise HTTPException(422, 'Kanıtlar en fazla 30 kaynak kaydı içermeli.')
    for index, source in enumerate(evidence):
        if not isinstance(source, dict):
            raise HTTPException(422, 'Kanıt satırı geçersiz. Kaynak alanlarını yeniden doldurun.')
        missing = next((key for key in ('title', 'locator', 'source_revision')
                        if not isinstance(source.get(key), str) or not source[key].strip()), None)
        if missing:
            field = {'title': 'source_title', 'locator': 'source_locator', 'source_revision': 'source_revision'}[missing]
            raise HTTPException(422, {'message': f'Eksik kaynak kaydı ({index + 1}. satır): kaynak adı, konumu ve sabit kaynak sürümünü doldurun.',
                                      'field': field, 'source_index': index})
    if state == 'verified' and not evidence:
        raise HTTPException(422, 'Doğrulanmış gerçekleşme için kaynak bulunmuyor. En az bir tam kaynak ekleyin veya veri durumunu İncelenmeli seçin.')
    if not isinstance(explanation, str) or not isinstance(deviation, dict):
        raise HTTPException(422, 'Açıklama metin, sapma kaydı bir nesne olmalı.')
    for content, field, limit, label in ((canonical(evidence), 'source_title', 50000, 'Kanıt kaynakları'),
            (explanation, 'explanation', 10000, 'Açıklama'), (canonical(deviation), 'corrective_action', 10000, 'Sapma / düzeltici işlem')):
        if len(content) > limit:
            raise HTTPException(422, {'message': f'{label} çok uzun. Alanı kısaltıp yeniden kaydedin.', 'field': field})
    from . import activity_evidence_service as attachments
    evidence, pending = attachments.prepare(db, item, previous, evidence, uploads)
    definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
    target = json.loads(definition.definition_json)['targets']
    target_value = None
    if len(target) == 1 and target[0].get('state') == 'verified' and target[0].get('value') is not None:
        target_value = Decimal(str(target[0]['value']))
    # Direction/achievement percentage is deliberately not inferred from name or unit.
    calculated = dict(deviation, calculation_rule_version='difference-v1', target_definition_revision_id=definition.id,
        delta=str(number - target_value) if state == 'verified' and target_value is not None else None,
        achievement_percent=None)
    actual = ActualRevision(report_indicator_id=item.id, revision=(previous.revision if previous else 0) + 1,
        supersedes_id=previous.id if previous else None, value=number, raw_text=value or '', state=state,
        evidence_json=canonical(evidence), explanation=explanation, deviation_json=canonical(calculated), created_by=user.id)
    db.add(actual)
    attachments.persist(db, user, actual, evidence, pending)
    return actual


def approve_report(db, user, revision_id):
    from .released_permissions import require_strategy_director, SOD_ERROR
    strategy(user)
    report, revision, pub, payload = report_revision(db, user, revision_id)
    lock_report(db, report)
    ensure_legacy_writable(db, report, revision)
    require_strategy_director(user)
    if revision.revision != report.current_revision:
        raise HTTPException(409, 'Yalnız güncel rapor revizyonu onaylanabilir.')
    if db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id == revision.id)):
        raise HTTPException(409, 'Bu rapor revizyonu zaten onaylı.')
    authored_actual = db.scalar(select(ActualRevision.id).join(ReportIndicator).where(
        ReportIndicator.report_revision_id == revision.id, ActualRevision.created_by == user.id).limit(1))
    if revision.created_by == user.id or authored_actual:
        raise HTTPException(403, SOD_ERROR.format(record="Faaliyet Raporu revizyonu"))
    blockers = []
    for item in db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision.id).order_by(ReportIndicator.id)):
        actual = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision.desc()))
        binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
        name = snapshot_rows(payload)[binding.snapshot_indicator_id]['name']
        if not actual or actual.state != 'verified' or not json.loads(actual.evidence_json):
            blockers.append({'indicator': name, 'report_indicator_id': item.id, 'message': 'Doğrulanmış gerçekleşme ve tam dayanak kaynağı girin.'})
            if not actual:
                continue
        delta = json.loads(actual.deviation_json)['delta']
        if delta is not None and Decimal(delta) != 0 and not actual.explanation.strip():
            blockers.append({'indicator': name, 'report_indicator_id': item.id, 'message': 'Hedef ile gerçekleşme farkı için açıklama girin.'})
    if blockers:
        raise HTTPException(409, {'message': 'Rapor onaylanmadı. Aşağıdaki göstergelerde belirtilen eksikleri giderip yeniden onaylayın.', 'blockers': blockers})
    approval = ActivityReportApproval(report_revision_id=revision.id, created_by=user.id)
    db.add(approval); db.flush()
    from .activity_evidence_service import freeze
    freeze(db, revision.id)
    return approval


def actual_data(actual):
    return {'id': actual.id, 'revision': actual.revision, 'supersedes_id': actual.supersedes_id,
        'value': format(actual.value, 'f') if actual.value is not None else None,
        'raw_text': actual.raw_text, 'state': actual.state, 'evidence': json.loads(actual.evidence_json),
        'explanation': actual.explanation, 'deviation': json.loads(actual.deviation_json),
        'created_by': actual.created_by, 'created_at': actual.created_at.isoformat()}


def report_data(db, user, revision_id):
    report, revision, pub, payload = report_revision(db, user, revision_id)
    rows = snapshot_rows(payload)
    result = []
    for item in db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision.id).order_by(ReportIndicator.id)):
        binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
        if user.role == 'department' and binding.department_id != user.department_id:
            continue
        definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
        if (digest(definition.definition_json) != definition.sha256
                or canonical(definition_payload(rows[binding.snapshot_indicator_id], payload['period'],
                    publication_contract_version(payload))) != definition.definition_json):
            raise HTTPException(409, 'Gösterge tanımının bütünlüğü doğrulanamadı.')
        actuals = db.scalars(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id).order_by(ActualRevision.revision)).all()
        result.append({'report_indicator_id': item.id, 'snapshot_indicator_id': binding.snapshot_indicator_id,
            'indicator_id': definition.indicator_id, 'definition_revision_id': definition.id,
            'definition': json.loads(definition.definition_json), 'department': rows[binding.snapshot_indicator_id]['department'],
            'actuals': [dict(actual_data(a), entered_by_name=(db.get(User, a.created_by).full_name)) for a in actuals]})
    latest = db.scalar(select(func.max(Publication.version)).where(Publication.period_id == pub.period_id))
    differences = json.loads(revision.diff_json)
    if user.role == 'department':
        differences = [d for d in differences if any((d.get(side) or {}).get('department_id') == user.department_id for side in ('before', 'after'))]
        # A transfer must not disclose the other department's definition.
        differences = [dict(d, **{side: d.get(side) if (d.get(side) or {}).get('department_id') == user.department_id else None for side in ('before', 'after')}) for d in differences]
    approval = db.scalar(select(ActivityReportApproval).where(ActivityReportApproval.report_revision_id == revision.id))
    from .structure_service import closure_notes
    from .models import ActivityEvidenceFreeze
    frozen_manifest = None
    if inspect(db.connection()).has_table('activity_evidence_freezes', schema=db.connection().get_execution_options().get('schema_translate_map', {}).get(None)):
        frozen = db.scalar(select(ActivityEvidenceFreeze).where(ActivityEvidenceFreeze.report_revision_id == revision.id))
        if frozen:
            if digest(frozen.manifest_json) != frozen.sha256:
                raise HTTPException(409, 'Dondurulmuş kanıt listesi doğrulanamadı. Sistem sorumlusuyla iletişime geçin.')
            permitted = {row['report_indicator_id'] for row in result}
            frozen_manifest = [entry for entry in json.loads(frozen.manifest_json) if entry['report_indicator_id'] in permitted]
    return {'closure_notes': closure_notes(db, report.period_id, user, report.organization_id), 'approval': {'created_by': approval.created_by, 'name': db.get(User, approval.created_by).full_name, 'created_at': approval.created_at.isoformat()} if approval else None, 'report_id': report.id, 'organization_id': report.organization_id, 'revision_id': revision.id,
        'revision': revision.revision, 'current_revision': report.current_revision, 'year': payload['period'],
        'publication_id': pub.id, 'publication_version': pub.version, 'publication_sha256': revision.publication_sha256,
        'newer_publication_available': latest > pub.version, 'previous_revision_id': revision.previous_revision_id,
        'revision_reason': revision.revision_reason, 'contract_version': revision.contract_version,
        'approved': bool(db.scalar(select(ActivityReportApproval.id).where(ActivityReportApproval.report_revision_id == revision.id))),
        'returned_after_approval': returned_after_approval(db, revision) if approval else False,
        'differences': differences, 'indicators': result, 'evidence_manifest': frozen_manifest}
