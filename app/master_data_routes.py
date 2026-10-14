"""HTML forms for Strategy; attempted values survive all validation failures."""
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Department, DepartmentScope, Organization, Program, ReportingPeriod, SubProgram, SubProgramScope, User
from .master_data_service import (active_department, audit_change, check_department_name,
                                department_duplicates, name_value, normalized_name, period_record)


def integer(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(422, f'{label} geçersiz. {label} alanından mevcut bir kayıt seçin.') from None


def register(app):
    from .main import require_strategy, templates, session_period

    def render(request, db, user, period_id=None, attempted=None, action='', error='', status=200):
        periods = db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all()
        period = (db.get(ReportingPeriod, period_id) if period_id else None) or session_period(request, db)
        departments = db.scalars(select(Department).order_by(Department.name, Department.id)).all()
        programs = db.scalars(select(Program).where(Program.period_id == period.id).order_by(Program.name)).all() if period else []
        subs = db.scalars(select(SubProgram).where(SubProgram.period_id == period.id).order_by(SubProgram.name)).all() if period else []
        scopes = db.scalars(select(DepartmentScope).where(DepartmentScope.period_id == period.id)).all() if period else []
        scope_by_id = {s.id: s for s in scopes}
        assigned = {sp.id: [] for sp in subs}
        for link in db.scalars(select(SubProgramScope).where(SubProgramScope.subprogram_id.in_(assigned))):
            if link.scope_id in scope_by_id:
                assigned[link.subprogram_id].append(scope_by_id[link.scope_id].department_id)
        return templates.TemplateResponse(request, 'structure.html', dict(user=user, period=period, periods=periods,
            organizations=db.scalars(select(Organization).order_by(Organization.name)).all(), departments=departments,
            duplicates=department_duplicates(departments), programs=programs, subprograms=subs,
            scopes={s.department_id: s for s in scopes}, assigned=assigned, attempted=attempted or {},
            attempted_action=action, error=error), status_code=status)

    @app.get('/structure')
    def screen(request: Request, period_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        try:
            pid = integer(period_id, 'Dönem') if period_id else None
            if pid: period_record(db, pid)
            return render(request, db, user, pid)
        except HTTPException as exc:
            return render(request, db, user, error=exc.detail, status=exc.status_code)

    async def change(request, db, user, operation):
        form = await request.form()
        try:
            pid = operation(form)
            db.commit()
            return RedirectResponse('/structure' + (f'?period_id={pid}' if pid else ''), 303)
        except (HTTPException, IntegrityError) as exc:
            db.rollback()
            try: pid = int(form.get('period_id', ''))
            except (ValueError, TypeError): pid = None
            message = exc.detail if isinstance(exc, HTTPException) else 'Bu ad veya kapsam başka bir işlemde kaydedildi. İlgili kaydı kontrol edip farklı bir adla tekrar deneyin.'
            status = exc.status_code if isinstance(exc, HTTPException) else 409
            values = dict(form)
            values['department_ids'] = form.getlist('department_ids')
            return render(request, db, user, pid, values, request.url.path, message, status)

    @app.post('/structure/departments')
    async def create_department(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        def operation(form):
            oid = integer(form.get('organization_id'), 'Kurum')
            name = name_value(form.get('name'), 'Müdürlük adı', 200)
            check_department_name(db, oid, name)
            obj = Department(organization_id=oid, name=name, is_active=True)
            db.add(obj)
            audit_change(db, user, 'department_create', obj, None, {'name': name, 'organization_id': oid, 'is_active': True})
        return await change(request, db, user, operation)

    @app.post('/structure/departments/{department_id}/rename')
    async def rename_department(department_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        def operation(form):
            obj = db.get(Department, integer(department_id, 'Müdürlük'))
            if not obj: raise HTTPException(404, 'Müdürlük bulunamadı. Kurum Yapısı listesini yenileyip kayıt seçin.')
            name = name_value(form.get('name'), 'Müdürlük adı', 200)
            check_department_name(db, obj.organization_id, name, obj.id)
            db.refresh(obj)
            old = {'name': obj.name}
            obj.name = name
            audit_change(db, user, 'department_rename', obj, old, {'name': name})
        return await change(request, db, user, operation)

    def set_department_active(form, db, user, department_id):
        # The async wrapper reads the complete form before calling this synchronous
        # mutation. No await can occur while the department row lock is held.
        obj = db.scalar(select(Department).where(Department.id == integer(department_id, 'Müdürlük')).with_for_update().execution_options(populate_existing=True))
        if not obj: raise HTTPException(404, 'Müdürlük bulunamadı. Kurum Yapısı listesini yenileyip kayıt seçin.')
        if form.get('active') not in {'0', '1'}: raise HTTPException(422, 'Müdürlük durumu geçersiz. Etkinleştir veya Pasifleştir düğmesini kullanın.')
        old = {'is_active': obj.is_active}
        obj.is_active = form['active'] == '1'
        audit_change(db, user, 'department_active', obj, old, {'is_active': obj.is_active})

    @app.post('/structure/departments/{department_id}/active')
    async def department_active(department_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        return await change(request, db, user, lambda form: set_department_active(form, db, user, department_id))

    async def save_hierarchy(request, db, user, model, record_id=None):
        def operation(form):
            pid = integer(form.get('period_id'), 'Dönem')
            period_record(db, pid)
            rid = integer(record_id, 'Program kaydı') if record_id is not None else None
            obj = db.get(model, rid) if rid else None
            if record_id and (not obj or obj.period_id != pid):
                raise HTTPException(422, 'Program kaydı seçilen döneme ait değil. Dönem ve program seçimini kontrol edin.')
            label = 'Program adı' if model is Program else 'Alt program adı'
            name = name_value(form.get('name'), label, 250)
            query = select(model).where(model.period_id == pid)
            fields = {'name': name}
            if model is SubProgram:
                program_id = obj.program_id if obj else integer(form.get('program_id'), 'Program')
                parent = db.get(Program, program_id)
                if not parent or parent.period_id != pid: raise HTTPException(422, 'Üst program seçilen döneme ait değil. Program alanından bu dönemin programını seçin.')
                query = query.where(SubProgram.program_id == program_id)
                fields.update(program_id=program_id, rationale=str(form.get('rationale', '')).strip(), goal=str(form.get('goal', '')).strip())
            for existing in db.scalars(query):
                if existing.id != rid and normalized_name(existing.name) == normalized_name(name):
                    raise HTTPException(409, f'{label} “{existing.name}” kaydıyla aynı. {label} alanına farklı bir ad girin veya mevcut kaydı düzenleyin.')
            old = {key: getattr(obj, key) for key in fields} if obj else None
            if not obj:
                obj = model(period_id=pid, **fields)
                db.add(obj)
            else:
                for key, value in fields.items(): setattr(obj, key, value)
            audit_change(db, user, ('program' if model is Program else 'subprogram') + ('_update' if record_id else '_create'), obj, old, dict(period_id=pid, **fields))
            return pid
        return await change(request, db, user, operation)

    @app.post('/structure/programs')
    async def create_program(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        return await save_hierarchy(request, db, user, Program)

    @app.post('/structure/programs/{program_id}')
    async def update_program(program_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        return await save_hierarchy(request, db, user, Program, program_id)

    @app.post('/structure/subprograms')
    async def create_subprogram(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        return await save_hierarchy(request, db, user, SubProgram)

    @app.post('/structure/subprograms/{subprogram_id}')
    async def update_subprogram(subprogram_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        return await save_hierarchy(request, db, user, SubProgram, subprogram_id)

    @app.post('/structure/scopes')
    async def save_scope(request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        def operation(form):
            pid = integer(form.get('period_id'), 'Dönem'); period_record(db, pid)
            did = integer(form.get('department_id'), 'Müdürlük')
            obj = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == pid, DepartmentScope.department_id == did))
            if not obj: active_department(db, did)
            fields = {'status': form.get('status'), 'reason': str(form.get('reason', '')).strip()}
            if fields['status'] not in {'required', 'zero', 'excluded'} or (fields['status'] != 'required' and not fields['reason']):
                raise HTTPException(422, 'Dönem kapsamı geçersiz veya gerekçesi eksik. Kapsam alanını seçin; sıfır veya kapsam dışı için gerekçe yazın.')
            if fields['status'] != 'required' and obj and db.scalar(select(SubProgramScope.subprogram_id).where(SubProgramScope.scope_id == obj.id).limit(1)):
                raise HTTPException(422, 'Müdürlüğün alt program sorumluluğu var. Önce bu dönemdeki alt program sorumluluğunu kaldırın, sonra kapsamı değiştirin.')
            old = {k: getattr(obj, k) for k in fields} if obj else None
            if not obj:
                obj = DepartmentScope(period_id=pid, department_id=did, **fields); db.add(obj)
            else:
                for key, value in fields.items(): setattr(obj, key, value)
            audit_change(db, user, 'structure_scope_save', obj, old, dict(period_id=pid, department_id=did, **fields))
            return pid
        return await change(request, db, user, operation)

    @app.post('/structure/subprograms/{subprogram_id}/responsibilities')
    async def responsibilities(subprogram_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_strategy)):
        def operation(form):
            pid = integer(form.get('period_id'), 'Dönem'); period_record(db, pid)
            sp = db.get(SubProgram, integer(subprogram_id, 'Alt program'))
            if not sp or sp.period_id != pid: raise HTTPException(422, 'Alt program seçilen döneme ait değil. Dönem ve alt program seçimini kontrol edin.')
            links = db.scalars(select(SubProgramScope).where(SubProgramScope.subprogram_id == sp.id)).all()
            old = {db.get(DepartmentScope, link.scope_id).department_id for link in links}
            selected = {integer(v, 'Sorumlu müdürlük') for v in form.getlist('department_ids')}
            for did in sorted(selected):
                if did not in old: active_department(db, did)
                scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == pid, DepartmentScope.department_id == did))
                if scope and scope.status != 'required':
                    raise HTTPException(422, f'Sorumlu müdürlük #{did} bu dönemde sıfır veya kapsam dışı. Önce Dönem Kapsamı alanından “Veri girecek” seçin.')
                if not scope:
                    scope = DepartmentScope(period_id=pid, department_id=did, status='required'); db.add(scope)
                    audit_change(db, user, 'structure_scope_save', scope, None, {'period_id': pid, 'department_id': did, 'status': 'required'})
                if did not in old: db.add(SubProgramScope(subprogram_id=sp.id, scope_id=scope.id))
            for link in links:
                if db.get(DepartmentScope, link.scope_id).department_id not in selected: db.delete(link)
            audit_change(db, user, 'subprogram_responsibilities', sp, {'department_ids': sorted(old)}, {'department_ids': sorted(selected), 'period_id': pid})
            return pid
        return await change(request, db, user, operation)
