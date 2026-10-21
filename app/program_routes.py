import json
import hashlib
import base64
import io
from PIL import Image
from decimal import Decimal
from fastapi import Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, Response
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from .db import get_db
from .models import *
from .numbers import parse_number
from .serialization import json_dumps
from .program_service import *
from .pp_errors import pp_error, recover_form, payload

CARD_FIELDS = ['source_title','administration','responsible','rationale','goal','explanation',
               'calculation_method','data_source','footnote','source_page','service_area','strategic_link']


def integer(value, label='Kimlik'):
    try: return int(value)
    except (ValueError, TypeError): raise pp_error(422, f'{label} geçersiz. Tam sayı girip yeniden kaydedin.', {'Sıra':'position', 'Alt program':'subprogram_id', 'Kart':'card_id', 'Kayıt':'record_id'}.get(label, 'id')) from None


def register(app):
    from .main import require_user, require_strategy, ensure_department_editable, templates, session_period, pp_period, check_pp_access, require_pp_period, log

    def form_screen(request, db, user, department_id, data):
        # The write dependency already validated the explicit period before the endpoint.
        period = session_period(request, db, data, require=True)
        if department_id is None:
            return builder(request=request, db=db, user=user, period_id=period.id)
        group = data.get('program_group', 'service')
        fund = data.get('funding_type', 'inside')
        return workbench(department_id=department_id, request=request, period_id=period.id,
            group=group if group in PROGRAM_GROUPS else 'service',
            fund=fund if fund in {'inside', 'outside'} else 'inside', db=db, user=user)

    def context(db, user, did, pid, edit=False):
        if not db.get(Department,did) or not db.get(ReportingPeriod,pid): raise pp_error(404)
        check_pp_access(db,user,did,db.get(ReportingPeriod,pid))
        if edit: ensure_department_editable(db,user,did,pid)

    def remove_record(department_id, record_id, model, request, data, db, user):
        from .draft_removal_service import remove_draft
        pid = session_period(request, db, data, require=True).id
        try:
            remove_draft(db, user, department_id, pid, model, record_id)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Kayıt bağlantıları değiştiği için kaldırılamadı. Sayfayı yenileyip bağlı kayıtları kontrol edin.') from None
        redirect = f'/program/{department_id}?period_id={pid}'
        if data.get('return_to') == 'department':
            redirect = f'/department/{department_id}?period_id={pid}'
        if 'application/json' in request.headers.get('accept', ''):
            return {'ok': True, 'redirect_url': redirect}
        return RedirectResponse(redirect, 303)

    @app.post('/program/{department_id}/indicator/{indicator_id}/remove', dependencies=[Depends(require_pp_period)])
    async def remove_indicator(department_id:int, indicator_id:int, request:Request,
            db:Session=Depends(get_db), user:User=Depends(require_user)):
        data = await request.form()
        return await run_in_threadpool(remove_record, department_id, indicator_id, Indicator, request, data, db, user)

    @app.post('/program/{department_id}/cards/{card_id}/remove', dependencies=[Depends(require_pp_period)])
    async def remove_card(department_id:int, card_id:int, request:Request,
            db:Session=Depends(get_db), user:User=Depends(require_user)):
        data = await request.form()
        return await run_in_threadpool(remove_record, department_id, card_id, ReportCard, request, data, db, user)

    @app.get('/program/{department_id}')
    def workbench(department_id:int, request:Request, period_id:int|None=None, group:str='service', fund:str='inside', db:Session=Depends(get_db), user:User=Depends(require_user)):
        period = pp_period(request,db,user,department_id, {"period_id": period_id} if period_id else None)
        if not period: raise pp_error(404)
        context(db,user,department_id,period.id)
        sub = db.scalar(select(Submission).where(Submission.department_id==department_id,Submission.period_id==period.id))
        errors,warnings = validate_department(db,period.id,department_id)
        snapshot=department_snapshot(db,period.id,department_id)
        if group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:raise pp_error(422, 'Program grubu veya bütçe kaynağı geçersiz. Geçerli bir program grubu ve bütçe kaynağı seçin.', 'program_group')
        economic_map={f"{v['category']}:{v['year']}:{v['value_kind']}":v['amount'] for v in snapshot['economics'] if v['program_group']==group and v['funding_type']==fund}
        from .draft_removal_service import removal_available
        return templates.TemplateResponse(request,'program.html',dict(user=user,department=db.get(Department,department_id),period=period,
            snapshot=snapshot,reconciliation=[r for r in cost_reconciliation(db,period.id) if r['department_id']==department_id],cards=rows(db,ReportCard,period.id,department_id),subprograms=rows(db,SubProgram,period.id),
            economic_map=economic_map,selected_group=group,selected_fund=fund,catalogue=rows(db,OfficialActivity,period.id), fields=CARD_FIELDS,errors=errors,warnings=warnings,
            editable=user.role=='department' and period.status!='closed' and (not sub or sub.status in {'draft','returned'}),
            removable=removal_available(db,user,department_id,period),
            categories=ECONOMIC_CATEGORIES,groups=PROGRAM_GROUPS,columns=economic_columns(period.year),cost_columns=cost_columns(period.year)))

    def split_screen(request, db, user, department_id, period_id, data=None, error=None, status=200, saved=0):
        from .economic_split_service import unallocated_cells, split_fingerprint, SPLIT_GROUPS
        context(db,user,department_id,period_id)
        cells = unallocated_cells(db,period_id,department_id)
        cards = rows(db,ReportCard,period_id,department_id)
        period = db.get(ReportingPeriod,period_id)
        sub = db.scalar(select(Submission).where(Submission.department_id==department_id,Submission.period_id==period_id))
        blocked = period.status=='closed' or bool(sub and sub.status in {'submitted','approved'})
        card_pages = {card.id:card.source_page for card in cards}
        pages = {}
        for cell in cells:
            try:
                source_ids = json.loads(cell.source_context_json).get('card_ids', [])
            except (ValueError, TypeError, AttributeError):
                source_ids = []
            source_ids = source_ids if isinstance(source_ids,list) else []
            source_pages = [card_pages.get(cid) for cid in source_ids if isinstance(cid,int)]
            source_pages.append(card_pages.get(cell.source_card_id))
            pages[cell.id] = ', '.join(dict.fromkeys(page for page in source_pages if page))
        return templates.TemplateResponse(request,'economic_split.html',dict(user=user,
            department=db.get(Department,department_id),period=period,cells=cells,cards=cards,pages=pages,
            groups=SPLIT_GROUPS,categories=ECONOMIC_CATEGORIES,fingerprint=split_fingerprint,
            data=data or {},error=error,blocked=blocked,saved=saved),status_code=status)

    @app.get('/program/{department_id}/economic-split')
    def economic_split_page(department_id:int, request:Request, period_id:int|None=None,
            saved:int=0, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        period=pp_period(request,db,user,department_id)
        return split_screen(request,db,user,department_id,period.id,saved=saved)

    def apply_economic_split(department_id, request, data, db, user):
        from .economic_split_service import split_economic_cells, SPLIT_GROUPS
        pid=session_period(request,db,data).id
        context(db,user,department_id,pid)
        cells=[{'id':integer(cell_id,'Kaynak hücre'), 'fingerprint':data.get(f'fingerprint_{cell_id}'),
            'shares':{g:data.get(f'share_{cell_id}_{g}','') for g in SPLIT_GROUPS},
            'zero_group':data.get(f'zero_group_{cell_id}')} for cell_id in data.getlist('cell_id')]
        try:
            count=split_economic_cells(db,user,pid,department_id,cells,data.get('reason'))
            db.commit()
        except (HTTPException,IntegrityError) as exc:
            db.rollback()
            status=exc.status_code if isinstance(exc,HTTPException) else 409
            if isinstance(exc,HTTPException):
                message=exc.detail
            elif getattr(getattr(exc.orig,'diag',None),'constraint_name',None)=='uq_economic_cell':
                message='Hedef ekonomik hücre eşzamanlı olarak oluşturuldu. Sayfayı yenileyip çakışan kaynakları karşılaştırın.'
            else:
                message='Dağılımın tutarlılık veya denetim kaydı kontrolü başarısız; hiçbir hücre değiştirilmedi. Sayfayı yenileyip tekrar deneyin; sorun sürerse sistem yöneticisine başvurun.'
            if 'application/json' in request.headers.get('accept',''):
                from fastapi.responses import JSONResponse
                return JSONResponse(payload(pp_error(status, str(message), 'shares')),status_code=status)
            return split_screen(request,db,user,department_id,pid,data,error=message,status=status)
        redirect=f'/program/{department_id}/economic-split?period_id={pid}&saved={count}'
        if 'application/json' in request.headers.get('accept',''):
            return {'ok':True,'redirect_url':redirect}
        return RedirectResponse(redirect,303)

    @app.post('/program/{department_id}/economic-split', dependencies=[Depends(require_pp_period)])
    async def economic_split_save(department_id:int, request:Request, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        data=await request.form()  # All awaits finish before the transaction takes row locks.
        return await run_in_threadpool(apply_economic_split,department_id,request,data,db,user)

    @app.post('/program/{department_id}/cards', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def save_card(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data['id'])) if data.get('id') else None
        if data.get('id') and not card: raise pp_error(404)
        if card and (card.department_id!=department_id or card.period_id!=pid): raise pp_error(403)
        sp=db.get(SubProgram,integer(data.get('subprogram_id'), 'Alt program'))
        if not sp or sp.period_id!=pid: raise pp_error(422, 'Alt program seçilen döneme ait değil. Bu dönemin alt programını seçin.', 'subprogram_id')
        if not card:
            card=ReportCard(period_id=pid,department_id=department_id,subprogram_id=sp.id);db.add(card)
        elif card.subprogram_id!=sp.id and (db.scalar(select(Indicator.id).where(Indicator.card_id==card.id).limit(1)) or db.scalar(select(Activity.id).where(Activity.card_id==card.id).limit(1))):
            raise HTTPException(409,'Kayıtları bağlı kartın alt programını değiştirmeden önce atamaları düzenleyin.')
        card.subprogram_id=sp.id;card.position=integer(data.get('position',0),'Sıra')
        for f in CARD_FIELDS:setattr(card,f,str(data.get(f,'')).strip())
        db.commit();log(db,user,'card_save','report_card',card.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/assign', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def assign(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data.get('card_id'), 'Kart'))
        if not card or card.department_id!=department_id or card.period_id!=pid:raise pp_error(422, 'Performans kartı bu müdürlük ve döneme ait değil. Ekrandaki kartlardan birini seçin.', 'card_id')
        model=Indicator if data.get('kind')=='indicator' else Activity if data.get('kind')=='activity' else None
        if not model:raise pp_error(422, 'Atanacak kayıt türü geçersiz. Gösterge veya faaliyet satırından yeniden kaydedin.', 'kind')
        obj=db.get(model,integer(data.get('record_id'), 'Kayıt'))
        if not obj or obj.department_id!=department_id or obj.period_id!=pid:raise pp_error(403)
        obj.card_id=card.id;obj.subprogram_id=card.subprogram_id
        obj.code=str(data.get('code',obj.code)).strip();obj.position=integer(data.get('position',obj.position or 0), 'Sıra')
        db.commit();log(db,user,'card_assign',model.__tablename__,obj.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/indicator', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def add_indicator(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data.get('card_id'), 'Kart'))
        if not card or card.department_id!=department_id or card.period_id!=pid:raise pp_error(422, 'Gösterge kartı bu müdürlük ve döneme ait değil. Ekrandaki kartlardan birini seçin.', 'card_id')
        name=str(data.get('name','')).strip();unit=str(data.get('unit','')).strip()
        if not name or len(name)>300:raise pp_error(422, 'Gösterge adı boş veya çok uzun. En fazla 300 karakterlik ad girin.', 'name')
        if not unit or len(unit)>50:raise pp_error(422, 'Ölçü birimi boş veya çok uzun. En fazla 50 karakterlik birim girin.', 'unit')
        obj=Indicator(period_id=pid,department_id=department_id,card_id=card.id,subprogram_id=card.subprogram_id,name=name,unit=unit)
        db.add(obj);db.commit();log(db,user,'indicator_create','indicator',obj.id)
        return RedirectResponse(f'/department/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/finance/{activity_id}', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def finance(department_id:int,activity_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        act=db.scalar(select(Activity).where(Activity.id==activity_id).with_for_update())
        if not act or act.department_id!=department_id or act.period_id!=pid:raise pp_error(403)
        save_activity_costs(db,act,db.get(ReportingPeriod,pid).year,data,actor=user)
        db.commit();log(db,user,'finance_save','activity',act.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/economic', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def economic(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        year=integer(data.get('year'));kind=data.get('value_kind');cat=data.get('category');group=data.get('program_group');fund=data.get('funding_type')
        if (year,kind) not in economic_columns(db.get(ReportingPeriod,pid).year) or cat not in ECONOMIC_CATEGORIES or group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:
            raise pp_error(422, 'Ekonomik tutarın yıl, tür, gider veya kaynak seçimi geçersiz. Döneme uygun seçenekleri seçin.', 'year')
        try:amount=parse_number(data.get('amount'),money=True)
        except ValueError as exc:raise pp_error(422, 'Tutar geçersiz. Türkçe sayı biçiminde girin (ör. 1.250,50).', 'amount') from None
        obj=db.scalar(select(EconomicValue).where(EconomicValue.period_id==pid,EconomicValue.department_id==department_id,EconomicValue.year==year,EconomicValue.value_kind==kind,EconomicValue.category==cat,EconomicValue.program_group==group,EconomicValue.funding_type==fund))
        if amount is None:
            if obj:db.delete(obj)
        elif obj:obj.amount=amount
        else:db.add(EconomicValue(period_id=pid,department_id=department_id,year=year,value_kind=kind,category=cat,program_group=group,funding_type=fund,amount=amount))
        db.commit();log(db,user,'economic_save','department',department_id,f'{year}/{kind}/{cat}/{group}/{fund}')
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/economic-grid', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def economic_grid(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        group=data.get('program_group');fund=data.get('funding_type')
        if group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:raise pp_error(422, 'Program grubu veya bütçe kaynağı geçersiz. Geçerli bir program grubu ve bütçe kaynağı seçin.', 'program_group')
        values={}
        for cat in ECONOMIC_CATEGORIES:
            for year,kind in economic_columns(db.get(ReportingPeriod,pid).year):
                key=f'{cat}:{year}:{kind}'
                if key not in data:continue
                try:values[cat,year,kind]=parse_number(data[key],money=True)
                except ValueError as exc:raise pp_error(422, f'{ECONOMIC_CATEGORIES[cat]} / {year}: {exc} Tutarı Türkçe sayı biçiminde girin (ör. 1.250,50).', key) from None
        existing={(v.category,v.year,v.value_kind):v for v in rows(db,EconomicValue,pid,department_id) if v.program_group==group and v.funding_type==fund}
        for (cat,year,kind),amount in values.items():
            obj=existing.get((cat,year,kind))
            if amount is None:
                if obj:db.delete(obj)
            elif obj:obj.amount=amount
            else:db.add(EconomicValue(period_id=pid,department_id=department_id,year=year,value_kind=kind,category=cat,program_group=group,funding_type=fund,amount=amount))
        db.commit();log(db,user,'economic_grid_save','department',department_id,f'{pid}/{group}/{fund}')
        redirect_url=f'/program/{department_id}?period_id={pid}&group={group}&fund={fund}'
        if 'application/json' in request.headers.get('accept',''):
            return {'ok':True,'redirect_url':redirect_url}
        return RedirectResponse(redirect_url,303)

    @app.post('/program/{department_id}/verify-value/{value_id}', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def verify_value(department_id:int,value_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();v=db.get(IndicatorValue,value_id)
        if not v:raise pp_error(404)
        period=pp_period(request,db,user,department_id,data,v.indicator.period_id)
        context(db,user,department_id,period.id,True)
        if v.indicator.department_id!=department_id:raise pp_error(403)
        kind=str(data.get('value_kind',v.value_kind));period=db.get(ReportingPeriod,v.indicator.period_id)
        from .main import indicator_columns
        if (v.year,kind) not in {(c['year'],c['kind']) for c in indicator_columns(period.year)}:raise pp_error(422, 'Gösterge yılı ve değer türü uygun değil. Döneme uygun değer türünü seçin.', 'value_kind')
        duplicate=db.scalar(select(IndicatorValue.id).where(IndicatorValue.indicator_id==v.indicator_id,IndicatorValue.year==v.year,IndicatorValue.value_kind==kind,IndicatorValue.id!=v.id))
        if duplicate:raise HTTPException(409,'Aynı yıl/türde başka değer var; kaynakları karşılaştırın.')
        try:value=parse_number(data.get('value'))
        except ValueError as exc:raise pp_error(422, 'Gösterge değeri geçersiz. Türkçe sayı biçiminde girin (ör. 1.250,50).', 'value') from None
        if value is None:raise pp_error(422, 'Gösterge değeri boş. Kaynakla doğruladığınız sayıyı girin.', 'value')
        v.value=value;v.value_kind=kind;v.state='verified'
        # Original source spelling survives an explicit correction.
        db.commit();log(db,user,'source_value_verified','indicator_value',v.id)
        return RedirectResponse(f'/program/{department_id}?period_id={period.id}',303)

    @app.post('/program/{department_id}/verify-money/{kind}/{value_id}', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def verify_money(department_id:int,kind:str,value_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form()
        model={'activity':ActivityCostValue,'personnel':DepartmentCostValue,'economic':EconomicValue}.get(kind)
        if not model:raise pp_error(404)
        value=db.get(model,value_id)
        if not value:raise pp_error(404)
        owner=value.activity if kind=='activity' else value
        period=pp_period(request,db,user,department_id,data,owner.period_id)
        context(db,user,department_id,period.id,True)
        if owner.department_id!=department_id:raise pp_error(403)
        try:amount=parse_number(data.get('amount'),money=True)
        except ValueError as exc:raise pp_error(422, 'Tutar geçersiz. Türkçe sayı biçiminde girin (ör. 1.250,50).', 'amount') from None
        if amount is None:raise pp_error(422, 'Doğrulanmış tutar boş. Kaynakla doğruladığınız tutarı girin.', 'amount')
        if kind=='activity' and value.funding_type=='total' and value.source_amount is not None and value.source_resolution_json=='{}':
            disagreement=activity_source_disagreements(owner).get(f'{value.year}:{value.value_kind}')
            if disagreement or amount!=value.source_amount:
                raise pp_error(422,source_total_message(owner,value.year,value.value_kind,value.source_amount,
                    disagreement['computed_total'] if disagreement else value.amount), 'amount')
        if kind == 'economic':
            group = str(data.get('program_group', value.program_group))
            if group not in PROGRAM_GROUPS or group == 'unallocated':
                raise pp_error(422, 'Ekonomik giderin program grubu belirsiz. Geçerli program grubunu seçin.', 'program_group')
            conflict = db.scalar(select(EconomicValue.id).where(EconomicValue.period_id==value.period_id,
                EconomicValue.department_id==department_id, EconomicValue.year==value.year,
                EconomicValue.value_kind==value.value_kind, EconomicValue.category==value.category,
                EconomicValue.funding_type==value.funding_type, EconomicValue.program_group==group,
                EconomicValue.id!=value.id))
            if conflict:
                raise HTTPException(409, 'Bu program grubunda ekonomik hücre zaten var; kayıtları karşılaştırın.')
            value.program_group = group
            value.issue = ''
        value.amount=amount;value.state='verified'
        db.commit();log(db,user,'source_money_verified',model.__tablename__,value.id)
        return RedirectResponse(f'/program/{department_id}?period_id={owner.period_id}',303)

    @app.get('/report-builder')
    def builder(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy),period_id:int|None=None):
        period=session_period(request,db,{"period_id":period_id} if period_id else None)
        if not period:raise pp_error(404)
        from .structure_service import period_name
        scopes={r.department_id:r for r in rows(db,DepartmentScope,period.id)}
        section_copy_audit = db.scalar(select(AuditLog).where(AuditLog.action == 'section_period_copy',
            AuditLog.entity_id == period.id).order_by(AuditLog.id.desc()))
        return templates.TemplateResponse(request,'report_builder.html',dict(user=user,period=period,
            source_periods=db.scalars(select(ReportingPeriod).where(ReportingPeriod.id != period.id).order_by(ReportingPeriod.year.desc())).all(),
            section_copy_result=getattr(request.state, 'section_copy_result', None) or (json.loads(section_copy_audit.details)['new'] if section_copy_audit else None),
            departments=period_departments(db,period.id),scopes=scopes,reconciliation=cost_reconciliation(db,period.id),
            department_names={d.id:period_name(db,period.id,d) for d in period_departments(db,period.id)},
            sections=rows(db,ReportSection,period.id),catalogue=rows(db,OfficialActivity,period.id),responsibilities={i.id:[r.department_id for r in db.scalars(select(ActivityResponsibility).where(ActivityResponsibility.official_activity_id==i.id)).all()] for i in rows(db,OfficialActivity,period.id)},publications=rows(db,Publication,period.id)))

    @app.get('/report-builder/sections.js', include_in_schema=False)
    def section_script(user:User=Depends(require_strategy)):
        # Same-origin external script preserves the app's strict CSP. Keep this
        # task's UI asset with its templates; no shared static bundle is changed.
        return Response(templates.env.get_template('pp_sections.js').render(), media_type='application/javascript')

    @app.get('/report-builder/manifest')
    def manifest(request:Request, period_id:int|None=None, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        from .pp_manifest import completion_manifest
        period = session_period(request, db, {'period_id': period_id} if period_id else None)
        if not period: raise pp_error(404)
        return templates.TemplateResponse(request, 'pp_manifest.html', dict(user=user, period=period,
            manifest=completion_manifest(db, period.id), periods=db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all()))

    @app.get('/report-builder/manifest.json')
    def manifest_json(request:Request, period_id:int|None=None, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        from .pp_manifest import completion_manifest
        period = session_period(request, db, {'period_id': period_id} if period_id else None)
        if not period: raise pp_error(404)
        return completion_manifest(db, period.id)

    @app.get('/report-builder/import/{batch_id}')
    def section_import_preview(batch_id:int, request:Request, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        from .main import import_batch_detail
        batch = db.get(ImportBatch, batch_id)
        if not batch: raise pp_error(404)
        period = session_period(request, db, require=True)
        if period.id != batch.period_id: raise pp_error(403)
        return templates.TemplateResponse(request, 'pp_section_import.html', dict(user=user, period=period,
            batch=batch, preview=import_batch_detail(batch_id, db, user)))

    @app.post('/report-builder/copy-sections', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def copy_sections(request:Request, db:Session=Depends(get_db), user:User=Depends(require_strategy)):
        from .structure_service import copy_general_sections
        data = await request.form()
        period = session_period(request, db, data, require=True)
        base = db.get(ReportingPeriod, integer(data.get('base_period_id'), 'Kaynak dönem'))
        if not base: raise pp_error(404)
        request.state.section_copy_result = await run_in_threadpool(copy_general_sections, db, user, base, period)
        db.commit()
        return builder(request=request, db=db, user=user, period_id=period.id)

    @app.post('/report-builder/scope', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def scope(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=session_period(request,db,data).id;did=integer(data.get('department_id'))
        from .master_data_service import active_department, audit_change, period_record
        period_record(db,pid)  # Share the lock used by master-data responsibilities.
        context(db,user,did,pid)
        status=data.get('status');reason=str(data.get('reason','')).strip()
        if status not in {'required','zero','excluded'} or (status!='required' and not reason):raise pp_error(422, 'Müdürlük kapsamı veya gerekçesi geçersiz. Kapsamı seçin; sıfır bütçe veya kapsam dışı için gerekçe yazın.', 'reason')
        obj=db.scalar(select(DepartmentScope).where(DepartmentScope.period_id==pid,DepartmentScope.department_id==did))
        fields=('position','status','reason','display_name')
        old={f:getattr(obj,f) for f in fields} if obj else None
        if not obj:
            active_department(db,did)
            obj=DepartmentScope(period_id=pid,department_id=did);db.add(obj)
        if status!='required' and obj.id and db.scalar(select(SubProgramScope.subprogram_id).where(SubProgramScope.scope_id==obj.id).limit(1)):
            raise pp_error(422,'Müdürlüğün alt program sorumluluğu var. Kurum Yapısı ekranında bu sorumluluğu kaldırıp kapsamı yeniden kaydedin.', 'status')
        obj.position=integer(data.get('position',0), 'Sıra');obj.status=status;obj.reason=reason;obj.display_name=str(data.get('display_name','')).strip()
        audit_change(db,user,'scope_save',obj,old,{f:getattr(obj,f) for f in fields})
        db.commit()
        return RedirectResponse(f'/report-builder?period_id={pid}',303)

    @app.post('/report-builder/section', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def section(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=session_period(request,db,data).id
        if not db.get(ReportingPeriod,pid):raise pp_error(404)
        from .structure_service import lock_organization
        from .master_data_service import period_record
        for oid in db.scalars(select(Organization.id).order_by(Organization.id)):
            lock_organization(db, oid)
        period_record(db, pid)
        obj=db.get(ReportSection,integer(data['id']),populate_existing=True) if data.get('id') else None
        if data.get('id') and not obj:raise pp_error(404)
        if obj and obj.period_id!=pid:raise pp_error(403)
        title=str(data.get('title','')).strip();kind=data.get('kind','text');content=str(data.get('content',''))
        if not title or len(title)>300 or kind not in {'text','table','image'}:raise pp_error(422, 'Bölüm başlığı veya türü geçersiz. En fazla 300 karakterlik başlık girip metin, tablo veya görsel seçin.', 'title')
        if kind=='text' and not content.strip():raise pp_error(422, 'Bölüm içeriği boş. Bölüm metnini girip yeniden kaydedin.', 'content')
        if len(content)>500000:raise pp_error(422, 'Bölüm içeriği çok uzun. İçeriği 500.000 karakterin altına indirin.', 'content')
        payload={'text':content} if kind=='text' else {'rows':[line.split('\t') for line in content.splitlines()]}
        if kind=='table' and (not payload['rows'] or any(len(r)!=len(payload['rows'][0]) for r in payload['rows'])):raise pp_error(422, 'Bölüm tablosunun sütunları uyuşmuyor. Her satırda aynı sayıda sütun olacak şekilde düzeltin.', 'content')
        if kind=='image':
            upload=data.get('image')
            if upload and getattr(upload,'filename',''):
                raw=await upload.read(5*1024*1024+1)
                if len(raw)>5*1024*1024:raise pp_error(422, 'Bölüm görseli çok büyük. En fazla 5 MB PNG/JPEG dosyasını yeniden seçin.', 'image')
                try:
                    with Image.open(io.BytesIO(raw)) as im:
                        if im.format not in {'PNG','JPEG'} or im.width*im.height>16000000:raise ValueError()
                        im.verify()
                except Exception:raise pp_error(422, 'Bölüm görseli okunamadı. Geçerli PNG/JPEG dosyasını yeniden seçin (en fazla 16 megapiksel).', 'image') from None
                payload={'data':base64.b64encode(raw).decode(),'caption':content}
            elif obj and obj.kind=='image':
                payload=json.loads(obj.content_json);payload['caption']=content
            else:raise pp_error(422, 'Bölüm görseli eksik. PNG/JPEG dosyasını yeniden seçip kaydedin.', 'image')
        placement=str(data.get('placement','before'))
        if placement not in {'before','after'}:raise pp_error(422, 'Bölüm konumu geçersiz. Müdürlüklerden önce veya mali özetlerden sonra seçeneğini seçin.', 'placement')
        payload['placement']=placement
        if not obj:obj=ReportSection(period_id=pid);db.add(obj)
        obj.title=title;obj.kind=kind;obj.position=integer(data.get('position',0), 'Sıra');obj.content_json=json_dumps(payload,ensure_ascii=False)
        db.commit();log(db,user,'section_save','report_section',obj.id)
        return RedirectResponse(f'/report-builder?period_id={pid}',303)

    @app.post('/report-builder/catalogue', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def catalogue(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=session_period(request,db,data).id
        if not db.get(ReportingPeriod,pid):raise pp_error(404)
        fields=['program_code','program_name','subprogram_code','subprogram_name','code','name'];values={f:str(data.get(f,'')).strip() for f in fields}
        if any(not v for v in values.values()):raise pp_error(422, 'Katalog kod veya adı eksik. Program, alt program ve faaliyet kod/ad alanlarını doldurun.', next(f for f in fields if not values[f]))
        ids={integer(v) for v in data.getlist('department_ids')}
        if not ids or any(not db.get(Department,d) for d in ids):raise pp_error(422, 'Katalog sorumlu birimi geçersiz. Listeden en az bir müdürlük seçin.', 'department_ids')
        obj=db.get(OfficialActivity,integer(data['id'])) if data.get('id') else None
        if data.get('id') and not obj:raise pp_error(404)
        save_catalogue_entry(db,pid,values,ids,user,obj=obj)
        db.commit()
        return RedirectResponse(f'/report-builder?period_id={pid}',303)

    @app.post('/program/{department_id}/catalogue-link', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def catalogue_link(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=session_period(request,db,data).id;context(db,user,department_id,pid,True)
        activity=db.get(Activity,integer(data.get('activity_id')))
        if not activity or activity.department_id!=department_id or activity.period_id!=pid:raise pp_error(403)
        ids={integer(v) for v in data.getlist('official_ids')}
        save_activity_catalogue_links(db,activity,ids,user)
        db.commit()
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/report-builder/publish', dependencies=[Depends(require_pp_period)])
    @recover_form(form_screen)
    async def publish(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=session_period(request,db,data).id;period=db.scalar(select(ReportingPeriod).where(ReportingPeriod.id==pid).with_for_update())
        if not period:raise pp_error(404)
        errors=[error for check in publication_checks(db,pid) for error in check['errors']]
        if errors:raise pp_error(422, 'Nihai yayın oluşturulamadı: ' + ' '.join(errors) + ' İlgili müdürlük kayıtlarını, kapsamı ve onayları tamamlayıp yeniden deneyin.', 'publish')
        from .activity_contract_service import freeze_program_payload, attach_publication_definitions
        payload, definitions = freeze_program_payload(db, pid, user)
        raw=json_dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        version=(db.scalar(select(func.max(Publication.version)).where(Publication.period_id==pid)) or 0)+1
        obj=Publication(period_id=pid,version=version,snapshot_json=raw,sha256=hashlib.sha256(raw.encode()).hexdigest(),created_by=user.id)
        db.add(obj);db.flush()
        attach_publication_definitions(db, obj, definitions, user)
        db.commit();log(db,user,'publication_freeze','publication',obj.id)
        return RedirectResponse(f'/report-builder?period_id={pid}',303)

    @app.get('/publications/{publication_id}.{format}')
    def publication_export(publication_id:int,format:str,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        obj=db.get(Publication,publication_id)
        if not obj:raise pp_error(404)
        if hashlib.sha256(obj.snapshot_json.encode()).hexdigest()!=obj.sha256:raise HTTPException(409,'Yayın içeriğinin bütünlük kontrolü başarısız.')
        from .book_export import export_book
        payload=json.loads(obj.snapshot_json)
        if format=='json':content=obj.snapshot_json.encode();mime='application/json'
        elif format in {'docx','pdf'}:content,mime=export_book(payload,format)
        else:raise pp_error(404)
        return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="civensa-{payload["period"]}-v{obj.version}.{format}"'})

    @app.get('/report-builder/preview.{format}')
    def preview(format:str,request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        from .book_export import export_book
        if format not in {'docx','pdf'}:raise pp_error(404)
        period=session_period(request,db);payload=book_snapshot(db,period.id);payload['draft']=True
        content,mime=export_book(payload,format)
        return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="civensa-taslak.{format}"'})
