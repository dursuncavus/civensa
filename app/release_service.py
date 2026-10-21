"""Evidence for PP release decisions; technical readiness alone is insufficient."""
import hashlib
from datetime import UTC

from fastapi import HTTPException
from sqlalchemy import select

from .models import AuditLog, Publication, ReleaseConfirmation, Submission, User
from .program_service import book_snapshot, publication_checks, record
from .serialization import json_dumps

TECHNICAL = {
    'database': ('Veritabanı bağlantısı', 'Teknik sorumlu bağlantıyı kontrol edip yeniden deneyin.'),
    'migration_head': ('Şema sürümü', 'Teknik sorumlu beklenen şema sürümünü doğrulasın.'),
    'period_active': ('Etkin dönem', 'Strateji seçilen dönemi doğrulayıp etkinleştirsin.'),
    'departments_present': ('Müdürlük kayıtları', 'Kurum Yapısı ekranında müdürlükleri tamamlayın.'),
    'indicators_present': ('Gösterge kayıtları', 'Seçilen dönemin göstergelerini tamamlayın.'),
    'activities_present': ('Faaliyet kayıtları', 'Seçilen dönemin faaliyetlerini tamamlayın.'),
    'activity_mappings_complete': ('Faaliyet eşleştirmeleri (PP-08)', 'Faaliyet Eşleştirme ekranında alt program, kart ve katalog eksiklerini tamamlayın.'),
    'no_orphan_activities': ('Faaliyet müdürlük bağlantıları', 'Teknik sorumlu müdürlük bağlantısı eksik faaliyetleri incelesin.'),
    'no_orphan_indicators': ('Gösterge müdürlük bağlantıları', 'Teknik sorumlu müdürlük bağlantısı eksik göstergeleri incelesin.'),
    'no_duplicate_active_department_accounts': ('Etkin Müdür hesaplarının tekilliği', 'Kullanıcılar ekranında mükerrer etkin Müdür hesaplarını inceleyin.'),
    'workflow_schema_present': ('Gönderim ve bildirim şeması', 'Teknik sorumlu gönderim ve bildirim tablolarını doğrulasın.'),
}

# These are acceptance decisions, never inferred from test names or record counts.
MANUAL = {
    'D1': ('Kurulum, içe aktarma ve elle giriş', 'Strateji veri sorumlusu',
           'Resmî kaynak tablo kapsamını, ilk dönem/elle giriş ve kopyalama sonuçlarını; kalan Word çeşitleri ve eşzamanlı yükleme bulgularını kanıtlayın.', 'tests/test_word_import.py; tests/test_pp_import_submit_ready.py; tests/test_master_data.py'),
    'D2': ('Müdürlük girişi ve düzeltmesi', 'Müdürlük Müdürü ve Strateji',
           'Dönem, boş/sıfır, taslak koruma ve onay sonrası hata düzeltme yolunu gerçek kullanıcıyla doğrulayın.', 'tests/test_indicator_update.py; tests/test_pp_period_context.py; tests/test_draft_removal.py'),
    'D3': ('İnceleme, iade ve yeniden onay', 'Strateji inceleme sorumlusu',
           'Gönderim, gerekçeli iade, yeniden gönderim ve bağımsız onayı; bütçe dışı onaylı hata düzeltmesi sınırını kabul kanıtıyla kaydedin.', 'tests/test_submission_workflow.py; tests/test_review_errors.py'),
    'D4': ('Değişmez ve hash içeren yayın', 'Teknik sorumlu ve Strateji',
           'Donmuş sürüm/hash ve başarısız yeniden yayın korumasını doğrulayın; PP-19 ayrıca teyit edilmelidir.', 'tests/test_publication_gates.py; tests/test_db_roles.py'),
    'D5': ('Kaynak karşılaştırması ve toplamlar', 'Mali hizmetler kontrol sorumlusu',
           'Kaynak konumları, çelişki kararları, genel toplamlar ve program/alt program/müdürlük ara toplamlarını yayımlanacak içerikle mutabık kılın.', 'tests/test_source_conflicts.py; tests/test_institution_summary_evidence.py'),
    'D6': ('Türkçe hata ve kurtarma akışları', 'Strateji kullanıcı kabul sorumlusu',
           'Ne/nerede/eylem mesajlarını, hatada form değerlerini ve yeniden denemeyi kullanıcı kabulüyle doğrulayın.', 'tests/test_pp_errors_forms.py'),
    'D7': ('Kitap, Word ve PDF', 'Strateji yayın sorumlusu',
           'Bölüm sırası, tablo kapsamı ve büyük Word/PDF çıktısını kontrol edin; resmî düzen/sayfalama PP-24 ile ayrıca onaylanır.', 'app/book_export.py; tests/test_program.py'),
    'D8': ('Teknik olmayan Strateji yönetimi', 'Strateji birim yöneticisi',
           'Kurum/dönem/hesap yönetimini, rol-müdürlük transfer politikasını, eşleştirmeyi ve hata kurtarmayı kullanıcıyla doğrulayın.', 'tests/test_master_data.py; tests/test_activity_mapping_gaps_ui.py; app/templates/operations.html'),
    'PP-19': ('Üretim veritabanı rol doğrulaması', 'Üretim yetkilisi ve teknik sorumlu',
              'Yetkili üretim sorumlusunun runtime/owner ayrımı, yetki ve geri dönüş kanıtını ekleyin. Yerel test canlı doğrulama değildir.', 'docs/operations/db-roles.md'),
    'PP-24': ('Resmî PP kitap ve Word kabulü', 'Strateji yayın sorumlusu ve iş sahibi',
              'Resmî PP referansını, büyük Word/PDF düzen-sayfalama kabulünü ve kabul eden kişiyi kanıta ekleyin.', 'docs/reports/civ-008-performance-programme-audit.md (PP-24)'),
    'operations': ('Güvenlik, yedek ve geri dönüş kabulü', 'Teknik sorumlu',
                   'Son commit CI kanıtını, giriş sınırı/oturum/menü kontrollerini ve yedekten geri dönüş provasını kaydedin.', '.github/workflows/performance-program.yml; docs/operations/db-roles.md'),
    'owner': ('İş sahibi yayın onayı', 'Strateji birim yöneticisi / iş sahibi',
              'Tüm kapıları ve açık PP bulgularını inceleyin; yayın kararının kapsamını ve iş sahibi onayını kaydedin.', 'docs/operations/release-checklist.md'),
}


def canonical(value):
    return json_dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def context_digest(db, period, technical, version, migration):
    # No secrets. Include approvals/accounts and frozen versions as well as book data.
    accounts = db.execute(select(User.id, User.full_name, User.role, User.department_id,
        User.position, User.is_active, User.can_submit, User.must_change_password).order_by(User.id)).mappings().all()
    context = dict(checklist='civ067-v1', period=record(period), version=version, migration=migration,
        technical=technical, book=book_snapshot(db, period.id), accounts=[dict(a) for a in accounts],
        submissions=[record(s) for s in db.scalars(select(Submission).where(
            Submission.period_id == period.id).order_by(Submission.id))],
        publications=[dict(id=p.id, version=p.version, sha256=p.sha256) for p in db.scalars(
            select(Publication).where(Publication.period_id == period.id).order_by(Publication.id))])
    return hashlib.sha256(canonical(context).encode()).hexdigest()


def confirmation_record(row):
    return dict(id=row.id, item_id=row.item_id, decision=row.decision, actor_id=row.actor_id,
        actor_name=row.actor_name, reason=row.reason, evidence=row.evidence,
        context_sha256=row.context_sha256, created_at=row.created_at.replace(tzinfo=UTC).isoformat())


def release_checklist(db, period, technical, version, migration, measurements):
    context = context_digest(db, period, technical, version, migration)
    automatic = [dict(id=name, label=TECHNICAL[name][0], status='Geçti' if ok else 'Engelli',
        owner='Teknik sorumlu / Strateji', source=f'main.release_readiness.checks.{name}',
        evidence=dict(result=ok, period_id=period.id, observed=measurements[name]),
        next_step='' if ok else TECHNICAL[name][1]) for name, ok in technical.items()]
    for check in publication_checks(db, period.id):
        automatic.append(dict(id='publication:' + check['id'], label=check['label'],
            status='Engelli' if check['errors'] else 'Geçti', owner='Strateji / ilgili Müdürlük Müdürü',
            source=check['source'], evidence=dict(period_id=period.id, observed=check['observed'], errors=check['errors']),
            next_step='İlgili müdürlük kayıtlarını, kapsamı ve Strateji onayını Nihai Rapor ekranında tamamlayın.' if check['errors'] else ''))
    history = db.scalars(select(ReleaseConfirmation).where(
        ReleaseConfirmation.period_id == period.id).order_by(ReleaseConfirmation.id)).all()
    latest = {}
    for row in history:
        if row.context_sha256 == context:
            latest[row.item_id] = row
    manual = []
    for key, (label, owner, step, source) in MANUAL.items():
        confirmation = latest.get(key)
        confirmed = confirmation is not None and confirmation.decision == 'confirmed'
        manual.append(dict(id=key, label=label, owner=owner, source=source,
            status='Geçti' if confirmed else ('Doğrulanmadı' if key == 'PP-19' else 'Elle onay bekliyor'),
            evidence=confirmation_record(confirmation) if confirmation else None,
            next_step='' if confirmed else step))
    blocked = any(item['status'] == 'Engelli' for item in automatic)
    pending = any(item['status'] != 'Geçti' for item in manual)
    return dict(status='Engelli' if blocked else ('Elle onay bekliyor' if pending else 'Hazır'),
        period_id=period.id, context_sha256=context, automatic=automatic, manual=manual,
        history=[confirmation_record(row) for row in history],
        live_role_verification=dict(status='Doğrulanmadı', observed_status='UNKNOWN',
            source='Canlı veritabanına bağlanılmadı; PP-19 yalnız yetkili kişinin manuel kanıtıyla teyit edilir.'))


def append_confirmation(db, user, period, data, context):
    if user.role != 'strategy':
        raise HTTPException(403, 'Yayın onayı için Strateji yetkisi gerekir. Strateji birimine başvurun.')
    key = data.get('item_id')
    if not isinstance(key, str) or key not in MANUAL or not isinstance(data.get('decision'), str) or data['decision'] not in {'confirmed', 'revoked'}:
        raise HTTPException(422, 'Yayın onay maddesi veya karar geçersiz. Kontrol listesinden madde ve karar seçin.')
    if data.get('context_sha256') != context:
        raise HTTPException(409, 'Dönem içeriği veya kontroller değişti. Sistem Durumu ekranını yenileyip kanıtı yeniden inceleyin.')
    values = {}
    for field, label in [('reason', 'Gerekçe'), ('evidence', 'Kanıt')]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 8000:
            raise HTTPException(422, f'{label} alanı eksik veya çok uzun. İlgili yayın maddesi için 1–8000 karakter girin.')
        values[field] = value.strip()
    row = ReleaseConfirmation(period_id=period.id, item_id=key, context_sha256=context,
        decision=data['decision'], actor_id=user.id, actor_name=user.full_name, **values)
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action='release_manual_confirmation', entity_type='release_confirmation',
        entity_id=row.id, details=canonical(dict(period_id=period.id, **confirmation_record(row)))))
    db.commit()
    return confirmation_record(row)
