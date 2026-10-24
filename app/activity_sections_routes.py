"""EK-1 HTML and API actions use the same authorization and transactions."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request
import re
import unicodedata
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, StrictInt, StrictBool, StrictStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from .db import get_db
from .models import ARDocument, ARSectionDefinition, ARContentEvent, Organization, ReportingPeriod
from . import activity_sections_service as service
from . import ar_similarity
from .numbers import parse_number, format_number
from .time_display import turkey_time


class NewYear(BaseModel):
    organization_id: StrictInt
    period_id: StrictInt
    copy_previous: StrictBool = False


class SectionSave(BaseModel):
    expected_revision: StrictInt = Field(ge=0)
    blocks: list[dict]
    status: StrictStr
    reason: StrictStr = ''
    table_keys: list[dict] | None = None


class ResourceSave(BaseModel):
    expected_revision: StrictInt = Field(ge=0)
    rows: list[dict]


class Freeze(BaseModel):
    expected_revision: StrictInt = Field(ge=0)


class Reopen(Freeze):
    reason: StrictStr = ''


def transact(db, operation):
    try:
        result=operation();db.commit();return result
    except HTTPException:
        db.rollback();raise
    except (IntegrityError,OperationalError):
        db.rollback()
        raise HTTPException(409,'Faaliyet raporu kaydedilemedi; eşzamanlı kayıt veya bağlantı sorunu oluştu. Sayfayı yenileyip son sürümü kontrol edin.') from None


def form_blocks(text):
    blocks=[];paragraph=[];bullets=[];rows=[]
    def flush():
        if paragraph:blocks.append({'type':'paragraph','text':'\n'.join(paragraph)});paragraph.clear()
        if bullets:blocks.append({'type':'bullets','items':list(bullets)});bullets.clear()
        if rows:blocks.append({'type':'table','rows':list(rows)});rows.clear()
    for line in text.splitlines():
        if not line.strip():flush()
        elif line.startswith('- '):
            if paragraph or rows:flush()
            bullets.append(line[2:])
        elif line.startswith('|') and line.endswith('|'):
            if paragraph or bullets:flush()
            rows.append([cell.strip() for cell in line[1:-1].split('|')])
        else:
            if rows or bullets:flush()
            paragraph.append(line)
    flush();return blocks


def blocks_text(blocks):
    return '\n\n'.join(b['text'] if b['type']=='paragraph' else '\n'.join('- '+s for s in b['items']) if b['type']=='bullets' else
        '\n'.join('| '+' | '.join(row)+' |' for row in b['rows']) for b in blocks)


class TurkishValidationRoute(APIRoute):
    def get_route_handler(self):
        original=super().get_route_handler()
        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError as error:
                labels={'expected_revision':'Rapor sürümü','organization_id':'Kurum','period_id':'Raporlama yılı',
                    'blocks':'Bölüm içeriği','status':'Durum','reason':'Gerekçe','rows':'Kaynak satırları',
                    'copy_previous':'Önceki yıldan kopyalama','document_id':'Faaliyet raporu',
                    'lower_rate':'Alt gerçekleşme oranı','upper_rate':'Üst gerçekleşme oranı',
                    'metadata':'Malî tablo bilgileri','file':'Dosya','import_id':'İçe aktarma önizlemesi',
                    'statement_id':'Malî tablo','kind':'Tablo türü','version':'Yayın sürümü',
                    'approval_id':'Birim onayı','table_keys':'Tablo ve satır anahtarları'}
                fields=[]
                for issue in error.errors():
                    location=issue.get('loc',())
                    fields.append(' / '.join(labels.get(str(part),str(part)) for part in location if part not in {'body','query','path'}))
                return JSONResponse({'detail':'Faaliyet raporu kaydedilemedi. '+', '.join(fields)+
                    ': Alan biçimini kontrol edin; yıl ve sürüm için tam sayı, içerik için metin veya tablo kullanın.'},status_code=422)
        return handler


def register(app):
    router=APIRouter(route_class=TurkishValidationRoute)
    from .main import require_user, templates
    templates.env.filters['ar_number']=format_number
    templates.env.filters['ar_time']=turkey_time
    templates.env.filters['ar_text']=blocks_text

    @router.post('/api/activity-sections/years')
    def create(data:NewYear,db:Session=Depends(get_db),user=Depends(require_user)):
        docs=transact(db,lambda:service.create_year(db,user,**data.model_dump()))
        return {'documents':[d.id for d in docs]}

    @router.get('/api/activity-sections/reports/{document_id}')
    def data(document_id:int,version:int|None=None,db:Session=Depends(get_db),user=Depends(require_user)):
        return service.report_data(db,user,document_id,version=version)

    @router.get('/api/activity-sections/reports/{document_id}/typeset-keys')
    def data_keys(document_id:int,db:Session=Depends(get_db),user=Depends(require_user)):
        from .ar_typeset_source import require_keys
        payload=service.report_data(db,user,document_id,include_typeset=True)
        require_keys(payload)
        return {key:payload['_typeset'][key] for key in ('sections','resources','entries','figures')}

    def export_document(document_id,db,user):
        doc=service.document(db,user,document_id)
        if user.role!='strategy' and (doc.department_id is None or doc.department_id!=user.department_id):
            service.fail('Bu faaliyet raporunu indiremezsiniz. Kendi birim raporunuzu açın; idare raporu için Strateji ile iletişime geçin.',403)
        return doc

    def export_payload(document_id,db,user,version=None):
        doc=export_document(document_id,db,user)
        payload=service.report_data(db,user,doc.id,version=version)
        slug='idare'
        if payload['department_id']:
            name=payload['department'].translate(str.maketrans('ıİşŞğĞüÜöÖçÇ','iIsSgGuUoOcC'))
            name=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()
            slug=re.sub(r'[^a-z0-9]+','-',name).strip('-') or 'birim'
        state='onayli' if payload['frozen'] else 'taslak'
        filename=f"{payload['year']}-faaliyet-raporu-{slug}-{state}"
        return payload,filename

    @router.get('/activity-sections/reports/{document_id}/export.docx')
    def export_docx(document_id:int,version:int|None=None,db:Session=Depends(get_db),user=Depends(require_user)):
        from .ar_export import build_activity_report_docx, TEMPLATE_PATH
        from docx.opc.exceptions import PackageNotFoundError
        payload,filename=export_payload(document_id,db,user,version)
        try:
            content=build_activity_report_docx(payload,TEMPLATE_PATH)
        except (FileNotFoundError,PackageNotFoundError):
            service.fail('Faaliyet raporu Word şablonu açılamadı. Sistem sorumlusundan faaliyet_raporu.docx dosyasını kontrol etmesini isteyin.',503)
        except ValueError as error:
            service.fail(str(error),503)
        return Response(content,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition':f'attachment; filename="{filename}.docx"',
                     'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.get('/activity-sections/reports/{document_id}/export.pdf')
    def export_pdf(document_id:int,version:int|None=None,db:Session=Depends(get_db),user=Depends(require_user)):
        from .ar_pdf_export import build_activity_report_pdf
        from reportlab.pdfbase.ttfonts import TTFError
        payload,filename=export_payload(document_id,db,user,version)
        try:
            content=build_activity_report_pdf(payload)
        except (OSError,TTFError):
            service.fail('Faaliyet raporu PDF yazı tipleri açılamadı. Sistem sorumlusundan app/fonts dosyalarını kontrol etmesini isteyin.',503)
        return Response(content,media_type='application/pdf',
            headers={'Content-Disposition':f'attachment; filename="{filename}.pdf"',
                     'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.get('/activity-sections/reports/{document_id}/export.json')
    def export_json(document_id:int,version:int|None=None,db:Session=Depends(get_db),user=Depends(require_user)):
        payload,filename=export_payload(document_id,db,user,version)
        doc=service.document(db,user,document_id)
        release=service.latest_release(db,doc,version) if version is not None else service.frozen(db,doc)
        content=release.payload_json if release else service.numeric_canonical(payload)
        return Response(content,media_type='application/json',headers={
            'Content-Disposition':f'attachment; filename="{filename}.json"',
            'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.get('/activity-sections/reports/{document_id}/typeset.json')
    def export_typeset(document_id:int,version:int|None=None,approval_id:int|None=None,db:Session=Depends(get_db),user=Depends(require_user)):
        from .ar_typeset_download import download
        doc=export_document(document_id,db,user)
        content=download(db,user,doc,version,approval_id)
        return Response(content,media_type='application/json',headers={
            'Content-Disposition':f'attachment; filename="faaliyet-raporu-{doc.id}-dizgi.json"',
            'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.get('/activity-sections/reports/{document_id}/approvals/{approval_id}.json')
    def approved_copy(document_id:int,approval_id:int,db:Session=Depends(get_db),user=Depends(require_user)):
        from .models import ARUnitWorkflowEvent
        from .ar_unit_workflow_service import verified_payload
        doc=export_document(document_id,db,user)
        approval=db.get(ARUnitWorkflowEvent,approval_id)
        if not doc.department_id or not approval or approval.document_id!=doc.id or approval.action!='approve':
            service.fail('Birim raporu onayı bulunamadı. Kendi raporunuzun sürüm geçmişini kullanın.',404)
        verified_payload(approval)
        return Response(approval.payload_json,media_type='application/json',headers={
            'Content-Disposition':f'attachment; filename="birim-raporu-{doc.id}-onay-{approval.revision}.json"',
            'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/api/activity-sections/reports/{document_id}/reopen')
    def reopen(document_id:int,data:Reopen,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.reopen_document(db,user,document_id,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post('/api/activity-sections/reports/{document_id}/sections/{code}')
    def save(document_id:int,code:str,data:SectionSave,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.save_section(db,user,document_id,code,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post('/api/activity-sections/reports/{document_id}/resources/{kind}')
    def resource(document_id:int,kind:str,data:ResourceSave,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.save_resources(db,user,document_id,kind,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post('/api/activity-sections/reports/{document_id}/freeze')
    def freeze(document_id:int,data:Freeze,db:Session=Depends(get_db),user=Depends(require_user)):
        result=transact(db,lambda:service.freeze_document(db,user,document_id,**data.model_dump()))
        return {'freeze_id':result.id,'sha256':result.sha256}

    def listing(db,user,period_id=None,section='',status=''):
        service.actor(user)
        query=select(ARDocument).order_by(ARDocument.period_id,ARDocument.id)
        if period_id:query=query.where(ARDocument.period_id==period_id)
        reports=[];report_errors=[];baseline_cache={}
        for doc in db.scalars(query):
            if user.role!='strategy' and doc.department_id not in {None,user.department_id}:continue
            try:report=service.report_data(db,user,doc.id)
            except HTTPException as error:
                if error.status_code==403:continue
                if error.status_code==409:
                    report_errors.append({'year':db.get(ReportingPeriod,doc.period_id).year,
                        'document_id':doc.id,'message':error.detail})
                    continue
                raise
            matches=[s for s in report['sections'] if (not section or s['code']==section) and (not status or s['status']==status)]
            if matches:reports.append({'report':report,'matches':matches,'similarities':ar_similarity.for_report(
                db,user,report,visible_sections=matches,baseline_cache=baseline_cache)})
        return reports,report_errors

    @router.get('/activity-sections')
    def index(request:Request,period_id:str='',section:str='',status:str='',db:Session=Depends(get_db),user=Depends(require_user)):
        period_id=integer(period_id) if period_id else None
        reports,report_errors=listing(db,user,period_id,section,status)
        return templates.TemplateResponse(request,'activity_sections_index.html',{'user':user,
            'reports':reports,'report_errors':report_errors,'statuses':service.STATUSES,
            'owners':{'directorate':'Müdürlük','strategy':'Strateji','finance':'Mali Hizmetler'},
            'definitions':db.scalars(select(ARSectionDefinition).order_by(ARSectionDefinition.version.desc(),ARSectionDefinition.position)).all(),
            'organizations':db.scalars(select(Organization).order_by(Organization.name)).all(),
            'periods':db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all(),
            'selected_period':period_id,'selected_section':section,'selected_status':status})

    def error_page(request,user,error,back):
        return templates.TemplateResponse(request,'activity_contract_error.html',{'user':user,
            'message':error.detail,'blockers':[],'back':back},status_code=error.status_code)

    def integer(raw):
        try:return int(raw)
        except (ValueError,TypeError):service.fail('Yıl veya sürüm numarası geçersiz. Sayfayı yenileyip listedeki kaydı seçin.')

    @router.post('/activity-sections/years')
    async def create_form(request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form()
        try:
            transact(db,lambda:service.create_year(db,user,integer(form.get('organization_id')),integer(form.get('period_id')),form.get('copy_previous')=='on'))
            return RedirectResponse('/activity-sections',303)
        except HTTPException as error:return error_page(request,user,error,'/activity-sections')

    def editor_context(db,user,document_id,code):
        doc=service.document(db,user,document_id)
        report=service.report_data(db,user,doc.id)
        section=next((s for s in report['sections'] if s['code']==code),None)
        if not section:service.fail('Bu raporda bölüm bulunamadı. Soldaki EK-1 listesinden bir bölüm seçin.',404)
        definition=None
        if not report['frozen']:
            definition,_=service.section_pair(db,doc,code)
        from .activity_financial_routes import financial_context
        from .released_permissions import require_strategy_director
        reopen_allowed=False
        if not doc.department_id and report['frozen']:
            try:
                require_strategy_director(user)
                from .models import Department
                dep=db.get(Department,user.department_id)
                reopen_allowed=bool(dep and dep.is_active and dep.organization_id==doc.organization_id)
            except HTTPException:pass
        from .ar_typeset_keys import section_keys
        from .models import ARResourceRow, ARSectionContent, ARUnitWorkflowEvent
        keys=[];resource_keys={}
        if not report['frozen']:
            _,content=service.section_pair(db,doc,code)
            keys=section_keys(db,content)
            for kind in service.TABLES:
                resource_keys[kind]=list(db.scalars(select(ARResourceRow.stable_key).where(
                    ARResourceRow.document_id==doc.id,ARResourceRow.table_kind==kind).order_by(ARResourceRow.position,ARResourceRow.id)))
        approvals=list(db.scalars(select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id==doc.id,
            ARUnitWorkflowEvent.action=='approve').order_by(ARUnitWorkflowEvent.revision))) if doc.department_id else []
        return {**financial_context(db,user,doc,report), 'section_table_keys_json':json.dumps(keys),
            'resource_key_map':resource_keys, 'typeset_approvals':approvals, 'user':user,'report':report,'section':section,'statuses':service.STATUSES,
            'reopen_allowed':reopen_allowed,'similarities':ar_similarity.for_report(db,user,report),
            'editable':not report['frozen'] and service.can_edit(db,user,doc,definition),
            'tables':{k:{**report['resources'][k],'kind':k} for k,v in service.TABLES.items() if v[0]==code},
            'employment':service.EMPLOYMENT,'owners':{'directorate':'Müdürlük','strategy':'Strateji','finance':'Mali Hizmetler'},
            'events':db.scalars(select(ARContentEvent).where(ARContentEvent.document_id==doc.id,ARContentEvent.section_code==code).order_by(ARContentEvent.id.desc())).all()}

    @router.get('/activity-sections/reports/{document_id}')
    def editor(document_id:int,request:Request,code:str='I.A',db:Session=Depends(get_db),user=Depends(require_user)):
        try:return templates.TemplateResponse(request,'activity_sections_editor.html',editor_context(db,user,document_id,code))
        except HTTPException as error:return error_page(request,user,error,'/activity-sections')

    def form_section_keys(db,user,document_id,code,form):
        from .ar_typeset_forms import align_section_keys
        doc=service.document(db,user,document_id)
        _,content=service.section_pair(db,doc,code)
        return align_section_keys(content.blocks_json,form_blocks(str(form.get('text',''))),str(form.get('table_keys','[]')))

    @router.post('/activity-sections/reports/{document_id}/sections/{code}')
    async def section_form(document_id:int,code:str,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form()
        try:
            transact(db,lambda:service.save_section(db,user,document_id,code,form_blocks(str(form.get('text',''))),
                str(form.get('status','draft')),str(form.get('reason','')),integer(form.get('expected_revision')),
                form_section_keys(db,user,document_id,code,form)))
            return RedirectResponse(f'/activity-sections/reports/{document_id}?code={code}',303)
        except HTTPException as error:
            if error.status_code in {422,409}:
                context=editor_context(db,user,document_id,code);context.update(form_error=error.detail,attempted=dict(form))
                return templates.TemplateResponse(request,'activity_sections_editor.html',context,status_code=error.status_code)
            return error_page(request,user,error,'/activity-sections')

    @router.post('/activity-sections/reports/{document_id}/resources/{kind}')
    async def resource_form(document_id:int,kind:str,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form()
        code=service.TABLES[kind][0] if kind in service.TABLES else 'I.C'
        try:
            if kind not in service.TABLES:service.fail('Kaynak tablosu bulunamadı. Bölüm listesini kullanın.',404)
            rows=[]
            for i in range(2000):
                if form.get(f'include_{i}')!='on':continue
                row={key:str(form.get(f'{key}_{i}','')) for key,_ in service.TABLES[kind][2]}
                if f'stable_key_{i}' in form:row['stable_key']=str(form.get(f'stable_key_{i}',''))
                for key in ('count','area'):
                    if key in row:
                        try:row[key]=parse_number(row[key])
                        except ValueError:service.fail(f'{service.TABLES[kind][1]}, {i+1}. satır: Sayı okunamadı. Örneğin 12.500 veya 12.500,23 girin.')
                rows.append(row)
            transact(db,lambda:service.save_resources(db,user,document_id,kind,rows,integer(form.get('expected_revision'))))
            return RedirectResponse(f'/activity-sections/reports/{document_id}?code={code}',303)
        except HTTPException as error:
            if error.status_code in {422,409}:
                context=editor_context(db,user,document_id,code)
                context.update(form_error=error.detail,resource_attempt=dict(form),resource_kind=kind,
                    resource_count=min(2000,max([int(k.rsplit('_',1)[1])+1 for k in form if k.startswith('include_') and k.rsplit('_',1)[1].isdigit()]+[3])))
                return templates.TemplateResponse(request,'activity_sections_editor.html',context,status_code=error.status_code)
            return error_page(request,user,error,'/activity-sections')

    @router.post('/activity-sections/reports/{document_id}/freeze')
    async def freeze_form(document_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form()
        try:
            transact(db,lambda:service.freeze_document(db,user,document_id,integer(form.get('expected_revision'))))
            return RedirectResponse(f'/activity-sections/reports/{document_id}',303)
        except HTTPException as error:return error_page(request,user,error,f'/activity-sections/reports/{document_id}')

    @router.post('/activity-sections/reports/{document_id}/reopen')
    async def reopen_form(document_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form()
        try:
            transact(db,lambda:service.reopen_document(db,user,document_id,
                integer(form.get('expected_revision')),str(form.get('reason',''))))
            return RedirectResponse(f'/activity-sections/reports/{document_id}',303)
        except HTTPException as error:
            context=editor_context(db,user,document_id,'I.A')
            context.update(reopen_error=error.detail,reopen_reason=str(form.get('reason','')))
            return templates.TemplateResponse(request,'activity_sections_editor.html',context,status_code=error.status_code)

    app.include_router(router)
