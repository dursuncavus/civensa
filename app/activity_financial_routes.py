"""III-A APIs and forms; all body/file reads finish before acquiring row locks."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel, Field, StrictInt, StrictFloat, StrictStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db
from .structure_service import period_name
from .models import Department, Program, SubProgram, ARFinancialStatement
from . import activity_financial_service as service
from . import activity_sections_service as sections
from .activity_sections_routes import transact, TurkishValidationRoute


class Rows(BaseModel):
    expected_revision: StrictInt = Field(ge=0)
    rows: list[dict]


class Policy(BaseModel):
    expected_revision: StrictInt = Field(ge=0)
    lower_rate: StrictInt | StrictFloat | StrictStr | None = None
    upper_rate: StrictInt | StrictFloat | StrictStr | None = None


class Revision(BaseModel):
    expected_revision: StrictInt = Field(ge=0)


def financial_context(db,user,doc,report):
    departments=db.scalars(select(Department).where(Department.organization_id==doc.organization_id).order_by(Department.name)).all()
    return {'financial_department_names':{dep.id:period_name(db,doc.period_id,dep) for dep in departments},'financial':report.get('financial',{}),'budget_kinds':{'expenditure':'Gider — Ekonomik Kod','programme':'Gider — Program / Alt Program','revenue':'Gelir'},
        'budget_columns':{k:service.budget_columns(k) for k in ('expenditure','programme','revenue')},
        'entry_columns':service.ENTRY_FIELDS,'entry_titles':{'assets':'Varlıklar ve Yükümlülükler','aid':'Yardım Yapılan Birlik ve Kuruluşlar','audit':'Malî Denetim Sonuçları','explanations':'Birim Sapma Açıklamaları'},
        'financial_slots':service.SLOTS,
        'financial_central':not report['frozen'] and not doc.department_id and (user.role=='strategy' or sections.finance(db,user)),
        'financial_own':not report['frozen'] and bool(doc.department_id and (user.role=='strategy' or doc.department_id==user.department_id)),
        'financial_departments':departments,
        'financial_programs':db.scalars(select(Program).where(Program.period_id==doc.period_id)).all(),
        'financial_subprograms':db.scalars(select(SubProgram).where(SubProgram.period_id==doc.period_id)).all(),
        'expense_codes':service.EXPENSE_CODES,'revenue_codes':service.REVENUE_CODES}


def register(app):
    from .main import require_user,templates
    router=APIRouter(route_class=TurkishValidationRoute)
    prefix='/api/activity-sections/reports/{document_id}/financial'
    form_prefix='/activity-sections/reports/{document_id}/financial'

    @router.get(prefix)
    def read(document_id:int,db:Session=Depends(get_db),user=Depends(require_user)):
        return sections.report_data(db,user,document_id).get('financial',{})

    @router.post(prefix+'/budget/{kind}')
    def budget(document_id:int,kind:str,data:Rows,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.save_budget(db,user,document_id,kind,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post(prefix+'/entries/{kind}')
    def entry(document_id:int,kind:str,data:Rows,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.save_entries(db,user,document_id,kind,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post(prefix+'/policy')
    def policy(document_id:int,data:Policy,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.save_policy(db,user,document_id,**data.model_dump()))
        return {'revision':doc.revision}

    @router.get(prefix+'/template/{kind}')
    def template(document_id:int,kind:str,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=sections.document(db,user,document_id);service.authorize(db,user,doc,kind)
        return Response(service.template(kind),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition':f'attachment; filename="mali-{kind}.xlsx"'})

    @router.post(prefix+'/imports/{kind}/preview')
    async def preview(document_id:int,kind:str,file:UploadFile=File(...),expected_revision:int=Form(...),db:Session=Depends(get_db),user=Depends(require_user)):
        data=await file.read(service.MAX_FILE+1)
        return transact(db,lambda:service.preview_import(db,user,document_id,kind,data,expected_revision))

    @router.get(prefix+'/imports/{import_id}')
    def preview_get(document_id:int,import_id:int,db:Session=Depends(get_db),user=Depends(require_user)):
        return service.import_preview(db,user,document_id,import_id)[1]

    @router.post(prefix+'/imports/{import_id}/apply')
    def apply(document_id:int,import_id:int,data:Revision,db:Session=Depends(get_db),user=Depends(require_user)):
        doc=transact(db,lambda:service.apply_import(db,user,document_id,import_id,**data.model_dump()))
        return {'revision':doc.revision}

    @router.post(prefix+'/statements')
    async def statement(document_id:int,metadata:str=Form(...),expected_revision:int=Form(...),file:UploadFile|None=File(None),db:Session=Depends(get_db),user=Depends(require_user)):
        data=await file.read(service.MAX_FILE+1) if file and file.filename else None
        values=parse_metadata(metadata)
        doc=transact(db,lambda:service.save_statement(db,user,document_id,values,expected_revision,data,file.filename if file else ''))
        return {'revision':doc.revision}

    @router.get(prefix+'/statements/{statement_id}/file')
    def download(document_id:int,statement_id:int,db:Session=Depends(get_db),user=Depends(require_user)):
        report=sections.report_data(db,user,document_id)
        row=db.get(ARFinancialStatement,statement_id)
        meta=next((s for s in report.get('financial',{}).get('statements',[]) if s['id']==statement_id),None)
        if not row or row.document_id!=document_id or not meta or not row.file_data:sections.fail('Malî tablo dosyası bulunamadı. Mali Hizmetler ile dosyayı tamamlayın.',404)
        if service.hashlib.sha256(row.file_data).hexdigest()!=meta['sha256']:sections.fail('Malî tablo dosyasının doğrulama kodu uyuşmuyor. Sistem sorumlusuyla iletişime geçin.',409)
        return Response(row.file_data,media_type='application/pdf' if row.filename.lower().endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition':'attachment; filename="mali-tablo'+('.pdf' if row.filename.lower().endswith('.pdf') else '.xlsx')+'"','X-Content-Type-Options':'nosniff'})

    def parse_metadata(raw):
        try:
            value=json.loads(raw)
            if not isinstance(value,dict):raise ValueError()
            return value
        except (ValueError,TypeError):sections.fail('Tablo bilgileri okunamadı. Formdaki alanları kontrol ederek yeniden kaydedin.')

    def revision(form):return service.integer(form.get('expected_revision'),'Rapor sürümü')

    def redirect(document_id,kind):return RedirectResponse(f'/activity-sections/reports/{document_id}?code={service.SLOTS[kind]}',303)

    def error(request,user,exc,document_id,kind=None):
        return templates.TemplateResponse(request,'activity_contract_error.html',{'user':user,'message':exc.detail,'blockers':[],
            'back':f'/activity-sections/reports/{document_id}?code={service.SLOTS.get(kind,"III.A.1")}'},status_code=exc.status_code)

    def rows_from_form(form,columns):
        result=[]
        for i in range(5000):
            if form.get(f'include_{i}')=='on':result.append({key:str(form.get(f'{key}_{i}','')) for key,_ in columns})
        return result

    @router.post(form_prefix+'/budget/{kind}')
    async def budget_form(document_id:int,kind:str,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000)
        try:
            transact(db,lambda:service.save_budget(db,user,document_id,kind,rows_from_form(form,service.budget_columns(kind)),revision(form)))
            return redirect(document_id,kind)
        except HTTPException as exc:return retained_error(request,user,exc,db,document_id,kind,form)

    @router.post(form_prefix+'/entries/{kind}')
    async def entries_form(document_id:int,kind:str,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000)
        try:
            if kind not in service.ENTRY_FIELDS:sections.fail('Kayıt tablosu bulunamadı. Geçerli tabloyu seçin.',404)
            transact(db,lambda:service.save_entries(db,user,document_id,kind,rows_from_form(form,service.ENTRY_FIELDS[kind]),revision(form)))
            return redirect(document_id,kind)
        except HTTPException as exc:return retained_error(request,user,exc,db,document_id,kind,form)

    @router.post(form_prefix+'/policy')
    async def policy_form(document_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000)
        try:
            transact(db,lambda:service.save_policy(db,user,document_id,form.get('lower_rate'),form.get('upper_rate'),revision(form)))
            return redirect(document_id,'policy')
        except HTTPException as exc:return retained_error(request,user,exc,db,document_id,'policy',form)

    def retained_error(request,user,exc,db,document_id,kind,form):
        if exc.status_code in {422,409}:
            # Read after transact rolled back; failed values survive in the form.
            report=sections.report_data(db,user,document_id)
            doc=sections.document(db,user,document_id)
            code=service.SLOTS.get(kind,'III.A.1')
            section=next(s for s in report['sections'] if s['code']==code)
            context={**financial_context(db,user,doc,report),'user':user,'report':report,'section':section,'statuses':sections.STATUSES,
                'editable':False,'tables':{},'events':[],'owners':{'directorate':'Müdürlük','strategy':'Strateji','finance':'Mali Hizmetler'},
                'form_error':exc.detail,'financial_attempt':dict(form),'financial_attempt_kind':kind,
                'financial_attempt_count':min(5000,max([int(k.rsplit('_',1)[1])+1 for k in form if k.startswith('include_') and k.rsplit('_',1)[1].isdigit()]+[3]))}
            return templates.TemplateResponse(request,'activity_sections_editor.html',context,status_code=exc.status_code)
        return error(request,user,exc,document_id,kind=kind)

    @router.post(form_prefix+'/imports/{kind}/preview')
    async def preview_form(document_id:int,kind:str,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000);file=form.get('file')
        data=await file.read(service.MAX_FILE+1) if hasattr(file,'read') else b''
        try:
            preview=transact(db,lambda:service.preview_import(db,user,document_id,kind,data,revision(form)))
            return RedirectResponse(f'/activity-sections/reports/{document_id}/financial/imports/{preview["id"]}',303)
        except HTTPException as exc:return error(request,user,exc,document_id,kind=kind)

    @router.get(form_prefix+'/imports/{import_id}')
    def preview_page(document_id:int,import_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        record,preview=service.import_preview(db,user,document_id,import_id)
        report=sections.report_data(db,user,document_id)
        return templates.TemplateResponse(request,'activity_financial_import.html',{'user':user,'report':report,'preview':preview,
            'columns':service.budget_columns(record.kind),'stale':record.revision!=report['revision']})

    @router.post(form_prefix+'/imports/{import_id}/apply')
    async def apply_form(document_id:int,import_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000)
        try:
            record,_=service.import_preview(db,user,document_id,import_id)
            transact(db,lambda:service.apply_import(db,user,document_id,import_id,revision(form)))
            return redirect(document_id,record.kind)
        except HTTPException as exc:return error(request,user,exc,document_id)

    @router.post(form_prefix+'/statements')
    async def statement_form(document_id:int,request:Request,db:Session=Depends(get_db),user=Depends(require_user)):
        form=await request.form(max_fields=100000);file=form.get('file')
        data=await file.read(service.MAX_FILE+1) if hasattr(file,'read') and file.filename else None
        values={k:str(form.get(k,'')) for k in ('name','period','statement_date','explanation')}
        figures=[]
        for i in range(100):
            if form.get(f'figure_label_{i}'):figures.append({'label':str(form.get(f'figure_label_{i}')),'amount':str(form.get(f'figure_amount_{i}',''))})
        values['figures']=figures
        try:
            transact(db,lambda:service.save_statement(db,user,document_id,values,revision(form),data,file.filename if hasattr(file,'filename') else ''))
            return redirect(document_id,'statements')
        except HTTPException as exc:return retained_error(request,user,exc,db,document_id,'statements',form)

    app.include_router(router)
