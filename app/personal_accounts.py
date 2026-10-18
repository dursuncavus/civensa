"""Personal account CSV validation and the shared single/bulk appointment rules."""
import csv
import io
import re

from fastapi import HTTPException
from sqlalchemy import select

from . import released_permissions
from .csv_safety import csv_cell_matches
from .master_data_service import active_department
from .models import Department, Organization, User

ACCOUNT_CSV_HEADERS = ['Müdürlük ID', 'Müdürlük', 'Ad Soyad', 'E-posta', 'Görev']
POSITIONS = {'Müdür': 'director', 'Personel': 'staff'}


def prepare_user_creation(db, actor, target):
    """Exactly the appointment/permission path used by single-user creation."""
    released_permissions.validate_position(target.position)
    reason = None
    if target.position == 'director':
        actor, target = released_permissions.lock_user_administration(db, actor, target)
        reason = released_permissions.require_strategy_user_management(db, actor, target, appointment=True)
    if target.department_id:
        active_department(db, target.department_id)
    if target.position == 'director':
        released_permissions.check_director_available(db, target)
    return actor, reason


def csv_error(line, field, problem, remedy):
    return f'Satır {line}: {field}: {problem} — {remedy}'


def validate_account_csv(data: bytes, db, actor):
    def error(line, field, problem, remedy):
        return [], [csv_error(line, field, problem, remedy)]
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return error(1, 'Dosya', 'UTF-8 kodlaması okunamadı', 'Dosyayı UTF-8 CSV olarak kaydedin.')
    if '\x00' in text:
        return error(1, 'Dosya', 'Geçersiz karakter bulundu', 'İndirilen şablonu yeniden doldurun.')
    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        headers = reader.fieldnames or []
        if any(re.search(r'parola|şifre|sifre|password|pwd|passphrase', h.casefold().replace('\u0307', '')) for h in headers):
            return error(1, 'Sütunlar', 'Parola sütunu kabul edilmez',
                         'Parola sütununu kaldırın; geçici parolalar hesap oluşturulurken otomatik üretilecektir.')
        if headers != ACCOUNT_CSV_HEADERS:
            return error(1, 'Sütunlar', 'Başlıklar şablonla eşleşmiyor',
                         'Müdürlük ID, Müdürlük, Ad Soyad, E-posta, Görev başlıklarını kullanın.')
        source_rows = []
        for source in reader:
            source_rows.append((reader.line_num, source))
            if len(source_rows) > 200:
                return error(reader.line_num, 'Dosya', '200 hesap satırı sınırı aşıldı', 'Dosyayı en fazla 200 satırlık dosyalara ayırın.')
    except csv.Error:
        return error(1, 'Dosya', 'CSV okunamadı', 'Tırnak ve ayraçları kontrol edip UTF-8 CSV olarak kaydedin.')

    # Same lock order as account administration: organizations, departments, users.
    # Acquire the whole batch scope first so director checks cannot deadlock when
    # two files list directorates in different orders. Recheck under these locks.
    ids = set()
    for _, source in source_rows:
        try:
            did = int(source.get('Müdürlük ID', ''))
            if 0 < did <= 2147483647:
                ids.add(did)
        except (ValueError, TypeError):
            pass
    if actor.department_id:
        ids.add(actor.department_id)
    org_ids = set(db.scalars(select(Department.organization_id).where(Department.id.in_(ids))))
    for oid in sorted(org_ids):
        db.scalar(select(Organization).where(Organization.id == oid).with_for_update())
    for did in sorted(ids):
        db.scalar(select(Department).where(Department.id == did).with_for_update().execution_options(populate_existing=True))
    departments = {d.id: d for d in db.scalars(select(Department))}
    directors = {u.department_id: u for u in db.scalars(select(User).where(
        User.position == 'director', User.is_active.is_(True)))}
    existing_emails = {email.lower() for email in db.scalars(select(User.email))}
    seen_directors, seen_emails, rows, errors = set(), set(), [], []
    for line, source in source_rows:
        if None in source or any(value is None for value in source.values()):
            errors.append(csv_error(line, 'Sütunlar', 'Satırdaki sütun sayısı şablonla eşleşmiyor', 'Her satırda beş sütun kullanın.'))
            continue
        full_name = source['Ad Soyad'].strip()
        email = source['E-posta'].strip().lower()
        duty = source['Görev'].strip()
        # Empty template rows are suggestions, not incomplete accounts.
        if not full_name and not email and not duty:
            continue
        start_errors = len(errors)
        def fail(field, problem, remedy):
            errors.append(csv_error(line, field, problem, remedy))
        try:
            did = int(source['Müdürlük ID'].strip())
            if not 0 < did <= 2147483647:
                raise ValueError
        except ValueError:
            fail('Müdürlük ID', 'Sayısal kimlik gerekli', 'Kimliği indirilen şablondan kopyalayın.')
            continue
        department = departments.get(did)
        if not department:
            fail('Müdürlük ID', 'Müdürlük bulunamadı', 'Etkin bir müdürlüğün kimliğini şablondan kopyalayın.')
            continue
        if not department.is_active:
            fail('Müdürlük', 'Müdürlük pasif', 'Kurum Yapısı ekranında müdürlüğü kontrol edin; etkin bir müdürlük seçin.')
        if not csv_cell_matches(source['Müdürlük'], department.name):
            fail('Müdürlük', 'Müdürlük adı şablonla eşleşmiyor', 'Müdürlük adını indirilen şablondan değiştirmeden kopyalayın.')
        if not full_name or len(full_name) > 200:
            fail('Ad Soyad', 'Ad soyad boş veya 200 karakterden uzun', 'Kişinin adını ve soyadını en fazla 200 karakterle yazın.')
        if len(email) > 255 or not re.fullmatch(r'[^\s@,;]+@[^\s@,;]+', email):
            fail('E-posta', 'Geçerli e-posta gerekli', 'Kişiye ait e-posta adresini kontrol edin.')
        elif email in existing_emails:
            fail('E-posta', 'Adres zaten kayıtlı', 'Başka bir kişisel adres kullanın; mevcut hesabın parolası için Kullanıcılar ekranında Parola sıfırla seçin.')
        elif email in seen_emails:
            fail('E-posta', 'Adres dosyada tekrarlanıyor', 'Her kişi için farklı bir e-posta adresi yazın.')
        seen_emails.add(email)
        position = POSITIONS.get(duty)
        if not position:
            fail('Görev', 'Görev geçersiz', 'Yalnızca Müdür veya Personel yazın.')
        elif position == 'director':
            if did in seen_directors:
                fail('Görev', 'Aynı müdürlük için birden fazla Müdür var', 'Bu müdürlük için yalnızca bir Müdür satırı bırakın.')
            seen_directors.add(did)
            if did in directors:
                existing = directors[did]
                fail('Görev', f'Etkin Müdür zaten var: {existing.full_name} ({existing.email})',
                     'Kullanıcılar ekranında mevcut Müdürü Personel yapın veya gerekçeyle pasifleştirin; sonra yeni Müdürü oluşturun.')
        if len(errors) == start_errors:
            target = User(email=email, full_name=full_name, role='department', department_id=did,
                          position=position, can_submit=False, is_active=True)
            try:
                prepare_user_creation(db, actor, target)
            except HTTPException as exc:
                fail('Görev', str(exc.detail), 'Kullanıcılar ekranındaki Müdür atamasını Strateji Geliştirme Müdürüne kontrol ettirin.')
                continue
            rows.append(dict(department_id=did, department_name=department.name,
                             full_name=full_name, email=email, position=position, duty=duty))
    if not rows and not errors:
        errors.append(csv_error(2, 'Hesap', 'Doldurulmuş hesap satırı yok', 'En az bir kişinin adını, e-posta adresini ve görevini doldurun.'))
    return rows, errors
