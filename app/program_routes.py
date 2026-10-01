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
from .db import get_db
from .models import *
from .numbers import parse_number
from .serialization import json_dumps
from .program_service import *

CARD_FIELDS = ['source_title','administration','responsible','rationale','goal','explanation',
               'calculation_method','data_source','footnote','source_page','service_area','strategic_link']


def integer(value, label='Kimlik'):
    try: return int(value)
    except (ValueError, TypeError): raise HTTPException(422, f'{label} geçersiz.') from None


def register(app):
    from .main import require_user, require_strategy, ensure_department_editable, templates, session_period, log

    def context(db, user, did, pid, edit=False):
        if not db.get(Department,did) or not db.get(ReportingPeriod,pid): raise HTTPException(404)
        if user.role == 'department' and user.department_id != did: raise HTTPException(403)
        if edit: ensure_department_editable(db,user,did,pid)

    @app.get('/program/{department_id}')
    def workbench(department_id:int, request:Request, period_id:int|None=None, group:str='service', fund:str='inside', db:Session=Depends(get_db), user:User=Depends(require_user)):
        period = db.get(ReportingPeriod,period_id) if period_id else session_period(request,db)
        if not period: raise HTTPException(404)
        context(db,user,department_id,period.id)
        sub = db.scalar(select(Submission).where(Submission.department_id==department_id,Submission.period_id==period.id))
        errors,warnings = validate_department(db,period.id,department_id)
        snapshot=department_snapshot(db,period.id,department_id)
        if group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:raise HTTPException(422)
        economic_map={f"{v['category']}:{v['year']}:{v['value_kind']}":v['amount'] for v in snapshot['economics'] if v['program_group']==group and v['funding_type']==fund}
        return templates.TemplateResponse(request,'program.html',dict(user=user,department=db.get(Department,department_id),period=period,
            snapshot=snapshot,cards=rows(db,ReportCard,period.id,department_id),subprograms=rows(db,SubProgram,period.id),
            economic_map=economic_map,selected_group=group,selected_fund=fund,catalogue=rows(db,OfficialActivity,period.id), fields=CARD_FIELDS,errors=errors,warnings=warnings,
            editable=user.role=='department' and (not sub or sub.status in {'draft','returned'}),
            categories=ECONOMIC_CATEGORIES,groups=PROGRAM_GROUPS,columns=economic_columns(period.year),cost_columns=cost_columns(period.year)))

    @app.post('/program/{department_id}/cards')
    async def save_card(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data['id'])) if data.get('id') else None
        if data.get('id') and not card: raise HTTPException(404)
        if card and (card.department_id!=department_id or card.period_id!=pid): raise HTTPException(403)
        sp=db.get(SubProgram,integer(data.get('subprogram_id')))
        if not sp or sp.period_id!=pid: raise HTTPException(422,'Alt program dönemle uyuşmuyor.')
        if not card:
            card=ReportCard(period_id=pid,department_id=department_id,subprogram_id=sp.id);db.add(card)
        elif card.subprogram_id!=sp.id and (db.scalar(select(Indicator.id).where(Indicator.card_id==card.id).limit(1)) or db.scalar(select(Activity.id).where(Activity.card_id==card.id).limit(1))):
            raise HTTPException(409,'Kayıtları bağlı kartın alt programını değiştirmeden önce atamaları düzenleyin.')
        card.subprogram_id=sp.id;card.position=integer(data.get('position',0),'Sıra')
        for f in CARD_FIELDS:setattr(card,f,str(data.get(f,'')).strip())
        db.commit();log(db,user,'card_save','report_card',card.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/assign')
    async def assign(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data.get('card_id')))
        if not card or card.department_id!=department_id or card.period_id!=pid:raise HTTPException(422,'Kart bu müdürlük/döneme ait değil.')
        model=Indicator if data.get('kind')=='indicator' else Activity if data.get('kind')=='activity' else None
        if not model:raise HTTPException(422,'Kayıt türü geçersiz.')
        obj=db.get(model,integer(data.get('record_id')))
        if not obj or obj.department_id!=department_id or obj.period_id!=pid:raise HTTPException(403)
        obj.card_id=card.id;obj.subprogram_id=card.subprogram_id
        obj.code=str(data.get('code',obj.code)).strip();obj.position=integer(data.get('position',obj.position or 0))
        db.commit();log(db,user,'card_assign',model.__tablename__,obj.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/indicator')
    async def add_indicator(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        card=db.get(ReportCard,integer(data.get('card_id')))
        if not card or card.department_id!=department_id or card.period_id!=pid:raise HTTPException(422,'Kart kapsamı geçersiz.')
        name=str(data.get('name','')).strip();unit=str(data.get('unit','')).strip()
        if not name or not unit or len(name)>300 or len(unit)>50:raise HTTPException(422,'Gösterge adı ve birimini kontrol edin.')
        obj=Indicator(period_id=pid,department_id=department_id,card_id=card.id,subprogram_id=card.subprogram_id,name=name,unit=unit)
        db.add(obj);db.commit();log(db,user,'indicator_create','indicator',obj.id)
        return RedirectResponse(f'/department/{department_id}',303)

    @app.post('/program/{department_id}/finance/{activity_id}')
    async def finance(department_id:int,activity_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        act=db.get(Activity,activity_id)
        if not act or act.department_id!=department_id or act.period_id!=pid:raise HTTPException(403)
        save_activity_costs(db,act,db.get(ReportingPeriod,pid).year,data)
        db.commit();log(db,user,'finance_save','activity',act.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/economic')
    async def economic(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        year=integer(data.get('year'));kind=data.get('value_kind');cat=data.get('category');group=data.get('program_group');fund=data.get('funding_type')
        if (year,kind) not in economic_columns(db.get(ReportingPeriod,pid).year) or cat not in ECONOMIC_CATEGORIES or group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:
            raise HTTPException(422,'Ekonomik tablo boyutları geçersiz.')
        try:amount=parse_number(data.get('amount'),money=True)
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        obj=db.scalar(select(EconomicValue).where(EconomicValue.period_id==pid,EconomicValue.department_id==department_id,EconomicValue.year==year,EconomicValue.value_kind==kind,EconomicValue.category==cat,EconomicValue.program_group==group,EconomicValue.funding_type==fund))
        if amount is None:
            if obj:db.delete(obj)
        elif obj:obj.amount=amount
        else:db.add(EconomicValue(period_id=pid,department_id=department_id,year=year,value_kind=kind,category=cat,program_group=group,funding_type=fund,amount=amount))
        db.commit();log(db,user,'economic_save','department',department_id,f'{year}/{kind}/{cat}/{group}/{fund}')
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/program/{department_id}/economic-grid')
    async def economic_grid(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        group=data.get('program_group');fund=data.get('funding_type')
        if group not in PROGRAM_GROUPS or fund not in {'inside','outside'}:raise HTTPException(422)
        values={}
        for cat in ECONOMIC_CATEGORIES:
            for year,kind in economic_columns(db.get(ReportingPeriod,pid).year):
                key=f'{cat}:{year}:{kind}'
                if key not in data:continue
                try:values[cat,year,kind]=parse_number(data[key],money=True)
                except ValueError as exc:raise HTTPException(422,f'{ECONOMIC_CATEGORIES[cat]} / {year}: {exc}') from None
        existing={(v.category,v.year,v.value_kind):v for v in rows(db,EconomicValue,pid,department_id) if v.program_group==group and v.funding_type==fund}
        for (cat,year,kind),amount in values.items():
            obj=existing.get((cat,year,kind))
            if amount is None:
                if obj:db.delete(obj)
            elif obj:obj.amount=amount
            else:db.add(EconomicValue(period_id=pid,department_id=department_id,year=year,value_kind=kind,category=cat,program_group=group,funding_type=fund,amount=amount))
        db.commit();log(db,user,'economic_grid_save','department',department_id,f'{pid}/{group}/{fund}')
        return RedirectResponse(f'/program/{department_id}?period_id={pid}&group={group}&fund={fund}',303)

    @app.post('/program/{department_id}/verify-value/{value_id}')
    async def verify_value(department_id:int,value_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();v=db.get(IndicatorValue,value_id)
        if not v:raise HTTPException(404)
        context(db,user,department_id,v.indicator.period_id,True)
        if v.indicator.department_id!=department_id:raise HTTPException(403)
        kind=str(data.get('value_kind',v.value_kind));period=db.get(ReportingPeriod,v.indicator.period_id)
        from .main import indicator_columns
        if (v.year,kind) not in {(c['year'],c['kind']) for c in indicator_columns(period.year)}:raise HTTPException(422,'Yıl/değer türü uygun değil.')
        duplicate=db.scalar(select(IndicatorValue.id).where(IndicatorValue.indicator_id==v.indicator_id,IndicatorValue.year==v.year,IndicatorValue.value_kind==kind,IndicatorValue.id!=v.id))
        if duplicate:raise HTTPException(409,'Aynı yıl/türde başka değer var; kaynakları karşılaştırın.')
        try:value=parse_number(data.get('value'))
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        if value is None:raise HTTPException(422,'Doğrulanmış değeri girin.')
        v.value=value;v.value_kind=kind;v.state='verified'
        # Original source spelling survives an explicit correction.
        db.commit();log(db,user,'source_value_verified','indicator_value',v.id)
        return RedirectResponse(f'/program/{department_id}?period_id={period.id}',303)

    @app.post('/program/{department_id}/verify-money/{kind}/{value_id}')
    async def verify_money(department_id:int,kind:str,value_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        model=ActivityCostValue if kind=='activity' else DepartmentCostValue if kind=='personnel' else None
        if not model:raise HTTPException(404)
        value=db.get(model,value_id)
        if not value:raise HTTPException(404)
        owner=value.activity if kind=='activity' else value
        context(db,user,department_id,owner.period_id,True)
        if owner.department_id!=department_id:raise HTTPException(403)
        data=await request.form()
        try:amount=parse_number(data.get('amount'),money=True)
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        if amount is None:raise HTTPException(422,'Kaynakla doğruladığınız tutarı girin.')
        value.amount=amount;value.state='verified'
        db.commit();log(db,user,'source_money_verified',model.__tablename__,value.id)
        return RedirectResponse(f'/program/{department_id}?period_id={owner.period_id}',303)

    @app.get('/report-builder')
    def builder(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        period=session_period(request,db)
        if not period:raise HTTPException(404)
        scopes={r.department_id:r for r in rows(db,DepartmentScope,period.id)}
        return templates.TemplateResponse(request,'report_builder.html',dict(user=user,period=period,
            departments=db.scalars(select(Department).order_by(Department.name)).all(),scopes=scopes,
            sections=rows(db,ReportSection,period.id),catalogue=rows(db,OfficialActivity,period.id),responsibilities={i.id:[r.department_id for r in db.scalars(select(ActivityResponsibility).where(ActivityResponsibility.official_activity_id==i.id)).all()] for i in rows(db,OfficialActivity,period.id)},publications=rows(db,Publication,period.id)))

    @app.post('/report-builder/scope')
    async def scope(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=integer(data.get('period_id'));did=integer(data.get('department_id'));context(db,user,did,pid)
        status=data.get('status');reason=str(data.get('reason','')).strip()
        if status not in {'required','zero','excluded'} or (status!='required' and not reason):raise HTTPException(422,'Kapsam ve gerekçeyi kontrol edin.')
        obj=db.scalar(select(DepartmentScope).where(DepartmentScope.period_id==pid,DepartmentScope.department_id==did))
        if not obj:obj=DepartmentScope(period_id=pid,department_id=did);db.add(obj)
        obj.position=integer(data.get('position',0));obj.status=status;obj.reason=reason;obj.display_name=str(data.get('display_name','')).strip()
        db.commit();log(db,user,'scope_save','department',did)
        return RedirectResponse('/report-builder',303)

    @app.post('/report-builder/section')
    async def section(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=integer(data.get('period_id'))
        if not db.get(ReportingPeriod,pid):raise HTTPException(404)
        obj=db.get(ReportSection,integer(data['id'])) if data.get('id') else None
        if data.get('id') and not obj:raise HTTPException(404)
        if obj and obj.period_id!=pid:raise HTTPException(403)
        title=str(data.get('title','')).strip();kind=data.get('kind','text');content=str(data.get('content',''))
        if not title or len(title)>300 or kind not in {'text','table','image'}:raise HTTPException(422,'Bölüm başlığı/türü geçersiz.')
        if kind=='text' and not content.strip():raise HTTPException(422,'Bölüm içeriği boş olamaz.')
        if len(content)>500000:raise HTTPException(422,'Bölüm içeriği çok uzun.')
        payload={'text':content} if kind=='text' else {'rows':[line.split('\t') for line in content.splitlines()]}
        if kind=='table' and (not payload['rows'] or any(len(r)!=len(payload['rows'][0]) for r in payload['rows'])):raise HTTPException(422,'Tablonun her satırında aynı sayıda sütun bulunmalı.')
        if kind=='image':
            upload=data.get('image')
            if upload and getattr(upload,'filename',''):
                raw=await upload.read(5*1024*1024+1)
                if len(raw)>5*1024*1024:raise HTTPException(422,'Görsel en fazla 5 MB olabilir.')
                try:
                    with Image.open(io.BytesIO(raw)) as im:
                        if im.format not in {'PNG','JPEG'} or im.width*im.height>16000000:raise ValueError()
                        im.verify()
                except Exception:raise HTTPException(422,'Geçerli PNG/JPEG görseli yükleyin (en fazla 16 megapiksel).') from None
                payload={'data':base64.b64encode(raw).decode(),'caption':content}
            elif obj and obj.kind=='image':
                payload=json.loads(obj.content_json);payload['caption']=content
            else:raise HTTPException(422,'Görsel dosyası gerekli.')
        placement=str(data.get('placement','before'))
        if placement not in {'before','after'}:raise HTTPException(422,'Bölüm konumu geçersiz.')
        payload['placement']=placement
        if not obj:obj=ReportSection(period_id=pid);db.add(obj)
        obj.title=title;obj.kind=kind;obj.position=integer(data.get('position',0));obj.content_json=json_dumps(payload,ensure_ascii=False)
        db.commit();log(db,user,'section_save','report_section',obj.id)
        return RedirectResponse('/report-builder',303)

    @app.post('/report-builder/catalogue')
    async def catalogue(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=integer(data.get('period_id'))
        if not db.get(ReportingPeriod,pid):raise HTTPException(404)
        fields=['program_code','program_name','subprogram_code','subprogram_name','code','name'];values={f:str(data.get(f,'')).strip() for f in fields}
        if any(not v for v in values.values()):raise HTTPException(422,'Katalog kod/ad alanları zorunlu.')
        ids={integer(v) for v in data.getlist('department_ids')}
        if not ids or any(not db.get(Department,d) for d in ids):raise HTTPException(422,'Geçerli sorumlu birimleri seçin.')
        obj=db.get(OfficialActivity,integer(data['id'])) if data.get('id') else None
        if data.get('id') and not obj:raise HTTPException(404)
        if obj and obj.period_id!=pid:raise HTTPException(403)
        if obj:
            linked_departments=set(db.scalars(select(Activity.department_id).join(ActivityCatalogueLink,ActivityCatalogueLink.activity_id==Activity.id).where(ActivityCatalogueLink.official_activity_id==obj.id)).all())
            if not linked_departments.issubset(ids):raise HTTPException(409,'Bağlı yerel faaliyetlerin sorumlu birimini kaldırmadan önce bağlantıyı düzenleyin.')
            for f,v in values.items():setattr(obj,f,v)
            db.execute(delete(ActivityResponsibility).where(ActivityResponsibility.official_activity_id==obj.id))
        else:obj=OfficialActivity(period_id=pid,**values);db.add(obj);db.flush()
        for did in ids:db.add(ActivityResponsibility(official_activity_id=obj.id,department_id=did))
        db.commit();log(db,user,'catalogue_create','official_activity',obj.id)
        return RedirectResponse('/report-builder',303)

    @app.post('/program/{department_id}/catalogue-link')
    async def catalogue_link(department_id:int,request:Request,db:Session=Depends(get_db),user:User=Depends(require_user)):
        data=await request.form();pid=integer(data.get('period_id'));context(db,user,department_id,pid,True)
        activity=db.get(Activity,integer(data.get('activity_id')))
        if not activity or activity.department_id!=department_id or activity.period_id!=pid:raise HTTPException(403)
        ids={integer(v) for v in data.getlist('official_ids')}
        for oid in ids:
            official=db.get(OfficialActivity,oid)
            responsible=db.scalar(select(ActivityResponsibility.id).where(ActivityResponsibility.official_activity_id==oid,ActivityResponsibility.department_id==department_id))
            if not official or official.period_id!=pid or not responsible:raise HTTPException(422,'Katalog faaliyeti bu dönem ve sorumlu birime ait olmalı.')
        db.execute(delete(ActivityCatalogueLink).where(ActivityCatalogueLink.activity_id==activity.id))
        for oid in ids:db.add(ActivityCatalogueLink(activity_id=activity.id,official_activity_id=oid))
        db.commit();log(db,user,'catalogue_link','activity',activity.id)
        return RedirectResponse(f'/program/{department_id}?period_id={pid}',303)

    @app.post('/report-builder/publish')
    async def publish(request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        data=await request.form();pid=integer(data.get('period_id'));period=db.scalar(select(ReportingPeriod).where(ReportingPeriod.id==pid).with_for_update())
        if not period:raise HTTPException(404)
        errors=[]
        for dept in db.scalars(select(Department)).all():
            scope=db.scalar(select(DepartmentScope).where(DepartmentScope.department_id==dept.id,DepartmentScope.period_id==pid))
            if not scope:errors.append(f'{dept.name}: dönem kapsamı belirtilmeli.');continue
            issues,_=validate_department(db,pid,dept.id);errors.extend(f'{dept.name}: {e}' for e in issues)
            if scope.status=='required':
                sub=db.scalar(select(Submission).where(Submission.department_id==dept.id,Submission.period_id==pid))
                if not sub or sub.status!='approved':errors.append(f'{dept.name}: onay eksik.')
        if not rows(db,ReportSection,pid):errors.append('Kitabın genel bilgi bölümleri hazırlanmalı.')
        if not rows(db,OfficialActivity,pid):errors.append('Sorumlu harcama birimleri kataloğu hazırlanmalı.')
        if errors:raise HTTPException(409,errors)
        raw=json_dumps(book_snapshot(db,pid),ensure_ascii=False,sort_keys=True,separators=(',',':'))
        version=(db.scalar(select(func.max(Publication.version)).where(Publication.period_id==pid)) or 0)+1
        obj=Publication(period_id=pid,version=version,snapshot_json=raw,sha256=hashlib.sha256(raw.encode()).hexdigest(),created_by=user.id)
        db.add(obj);db.commit();log(db,user,'publication_freeze','publication',obj.id)
        return RedirectResponse('/report-builder',303)

    @app.get('/publications/{publication_id}.{format}')
    def publication_export(publication_id:int,format:str,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        obj=db.get(Publication,publication_id)
        if not obj:raise HTTPException(404)
        if hashlib.sha256(obj.snapshot_json.encode()).hexdigest()!=obj.sha256:raise HTTPException(409,'Yayın içeriğinin bütünlük kontrolü başarısız.')
        from .book_export import export_book
        payload=json.loads(obj.snapshot_json)
        if format=='json':content=obj.snapshot_json.encode();mime='application/json'
        elif format in {'docx','pdf'}:content,mime=export_book(payload,format)
        else:raise HTTPException(404)
        return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="civensa-{payload["period"]}-v{obj.version}.{format}"'})

    @app.get('/report-builder/preview.{format}')
    def preview(format:str,request:Request,db:Session=Depends(get_db),user:User=Depends(require_strategy)):
        from .book_export import export_book
        if format not in {'docx','pdf'}:raise HTTPException(404)
        period=session_period(request,db);payload=book_snapshot(db,period.id);payload['draft']=True
        content,mime=export_book(payload,format)
        return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="civensa-taslak.{format}"'})
