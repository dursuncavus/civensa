"""Owned EK-1 text and resource facts; no dependency on finance or PP creation."""
import json
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException
from sqlalchemy import select
from .models import (ARSectionDefinition, ARDocument, ARSectionContent, ARResourceRow,
    ARDocumentFreeze, ARContentEvent, Department, DepartmentScope, Organization,
    ReportingPeriod, User, ActivityReport, ActivityReportRevision, ReportIndicator,
    ActualRevision, PublicationIndicatorBinding, IndicatorDefinitionRevision)
from .activity_contract_service import canonical, digest
from .structure_service import period_name
from .pp_errors import pp_error

STATUSES = {'empty':'Boş', 'draft':'Taslak', 'ready':'Hazır', 'not_applicable':'Uygulanamaz'}
CORE = 'III.B.2.i'
EMPLOYMENT = ['memur','sözleşmeli personel','işçi — kadrolu','işçi — geçici','şirket personeli/hizmet alımı','diğer']
# Column IDs are stable storage keys; labels are always Turkish.
TABLES = {
    'employment': ('I.C.4','İstihdam Türüne Göre Personel',[('category','İstihdam türü'),('count','Kişi sayısı')]),
    'education': ('I.C.4','Öğrenim Durumuna Göre Personel',[('category','Öğrenim düzeyi'),('count','Kişi sayısı')]),
    'gender': ('I.C.4','Cinsiyete Göre Personel',[('category','Cinsiyet'),('count','Kişi sayısı')]),
    'buildings': ('I.C.1','Binalar ve Hizmet Birimleri',[('name','Adı'),('category','Türü'),('address','Adres / mahalle'),('area','Alan (m²)'),('ownership','Mülkiyet')]),
    'vehicles': ('I.C.1','Taşıtlar',[('category','Türü'),('count','Adet'),('ownership','Mülkiyet')]),
    'hardware': ('I.C.3','Donanım',[('category','Türü'),('count','Adet')]),
    'software': ('I.C.3','Yazılım ve Sistemler',[('name','Adı'),('purpose','Kullanım amacı')]),
}
RESOURCE_FIELDS = ('name','category','address','purpose','ownership','count','area')


def fail(message, status=422):
    raise HTTPException(status, message)


def actor(user):
    if not user.is_active or user.role not in {'strategy','department'}:
        fail('Faaliyet raporu yetkiniz bulunmuyor. Müdürlük veya Strateji hesabınızla giriş yapın.',403)


def finance(db, user):
    dep = db.get(Department,user.department_id) if user.department_id else None
    return bool(dep and dep.name.strip().casefold() == 'Mali Hizmetler Müdürlüğü'.casefold())


def document(db, user, document_id):
    actor(user)
    doc = db.get(ARDocument, document_id)
    if not doc:
        fail('Faaliyet raporu bulunamadı. Rapor listesinden geçerli bir rapor seçin.',404)
    if user.role != 'strategy':
        dep = db.get(Department,user.department_id)
        if not dep or dep.organization_id != doc.organization_id or (doc.department_id and doc.department_id != dep.id):
            fail('Bu müdürlüğün faaliyet raporuna erişemezsiniz. Kendi birim raporunuzu açın.',403)
    return doc


def latest_release(db, doc, version=None):
    query=select(ARDocumentFreeze).where(ARDocumentFreeze.document_id==doc.id)
    if version is not None:query=query.where(ARDocumentFreeze.version==version)
    return db.scalar(query.order_by(ARDocumentFreeze.version.desc()).limit(1))


def release_reopen(db, doc, release):
    if doc.department_id or not release:return None
    for item in db.scalars(select(ARContentEvent).where(ARContentEvent.document_id==doc.id,
            ARContentEvent.action=='reopen').order_by(ARContentEvent.id.desc())):
        if json.loads(item.after_json).get('freeze_id')==release.id:return item
    return None


def frozen(db, doc):
    release=latest_release(db,doc)
    return None if release_reopen(db,doc,release) else release


def release_history(db, doc):
    if doc.department_id:return {}
    releases=db.scalars(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id==doc.id)
        .order_by(ARDocumentFreeze.version)).all()
    reopens={json.loads(e.after_json)['freeze_id']:(e,json.loads(e.after_json)) for e in db.scalars(
        select(ARContentEvent).where(ARContentEvent.document_id==doc.id,ARContentEvent.action=='reopen')
        .order_by(ARContentEvent.id))}
    rows=[]
    for index,release in enumerate(releases):
        row={'version':release.version,'sha256':release.sha256,'created_at':release.created_at.isoformat(),
            'label':f'Önceki sürüm — Sürüm {releases[index+1].version} ile değiştirildi' if index+1<len(releases)
                else f'Sürüm {release.version} · Güncel sürüm'}
        if release.id in reopens:
            e,data=reopens[release.id]
            row['reopen']={'actor_id':e.actor_id,'actor_name':data['actor_name'],
                'created_at':e.created_at.isoformat(),'reason':data['reason']}
        rows.append(row)
    return {'releases':rows,'reopened':bool(releases and releases[-1].id in reopens)}


def reopen_document(db,user,document_id,expected_revision,reason):
    doc=document(db,user,document_id)
    lock_documents(db,doc)
    user=db.get(User,user.id,populate_existing=True)
    from .released_permissions import require_strategy_director
    require_strategy_director(user)
    dep=db.get(Department,user.department_id,populate_existing=True)
    if not dep or not dep.is_active or dep.organization_id!=doc.organization_id:
        raise pp_error(403,'Bu kurumun idare faaliyet raporunu açamazsınız. Kendi kurumunuzun etkin Strateji Geliştirme Müdürü hesabını kullanın.','document_id')
    if doc.department_id:
        raise pp_error(409,'Birim faaliyet raporu bu ekrandan açılamaz. Birim raporunun gerekçeli yeniden açma işlemini kullanın.','document_id')
    if not isinstance(reason,str) or not reason.strip() or len(reason)>10000:
        raise pp_error(422,'İdare faaliyet raporu açılamadı. Gerekçe alanına düzeltilecek noktaları en fazla 10.000 karakterle yazın.','reason')
    if doc.revision!=expected_revision:
        raise pp_error(409,'İdare faaliyet raporu başka bir işlemle güncellendi. Sayfayı yenileyip güncel sürüm üzerinden yeniden açın.','expected_revision')
    release=frozen(db,doc)
    if not release:
        raise pp_error(409,'İdare faaliyet raporu dondurulmuş durumda değil. Güncel raporu kontrol edip düzeltmeden sonra yeni sürüm oluşturun.','document_id')
    event(db,user,doc,'','reopen',{'sha256':release.sha256},
        {'freeze_id':release.id,'version':release.version,'reason':reason.strip(),'actor_name':user.full_name})
    # The database guard must see the appended reopen before the mutable revision.
    db.flush()
    doc.revision+=1
    db.flush()
    return doc


def definitions(db, doc):
    kind = 'birim' if doc.department_id else 'idare'
    return db.scalars(select(ARSectionDefinition).where(ARSectionDefinition.version==doc.definition_version,
        ARSectionDefinition.applies_to.in_(['both',kind])).order_by(ARSectionDefinition.position)).all()


def owner(definition, doc):
    if doc.department_id and definition.code in {'III.A.3','III.A.4'}:return 'directorate'
    return definition.birim_owner if doc.department_id else definition.idare_owner


def can_edit(db, user, doc, definition):
    if doc.department_id:
        from .ar_unit_workflow_service import state
        if state(db,doc) in {'submitted','approved'}:
            return False
    if definition.code == CORE:
        return False
    if user.role == 'strategy':
        return True
    if user.role != 'department':
        return False
    owning = owner(definition,doc)
    if owning == 'finance':
        return finance(db,user) and (doc.department_id is None or doc.department_id==user.department_id)
    return bool(doc.department_id==user.department_id and owning=='directorate')


def lock_documents(db, doc):
    # Lock the complete source set in stable order: a freeze and resource save
    # cannot observe half of a consolidation. All callers are synchronous.
    db.execute(select(Organization).where(Organization.id==doc.organization_id).with_for_update()).scalar_one()
    db.execute(select(ARDocument).where(ARDocument.organization_id==doc.organization_id,
        ARDocument.period_id==doc.period_id).order_by(ARDocument.id).with_for_update()
        .execution_options(populate_existing=True)).scalars().all()


def writable(db,user,doc,expected_revision,definition=None):
    lock_documents(db,doc)
    if frozen(db,doc):
        fail('Bu faaliyet raporunun içeriği onaylanıp donduruldu. Onaylı kopya değiştirilemez.',409)
    if doc.department_id:
        from .ar_unit_workflow_service import state
        if state(db,doc) in {'submitted','approved'}:
            raise pp_error(409,'Birim faaliyet raporu incelemede veya onaylı. Düzenlemek için Strateji biriminden gerekçeli iade ya da yeniden açma isteyin.','status')
    if definition and not can_edit(db,user,doc,definition):
        fail('Bu bölümde düzenleme yetkiniz yok. Bölüm sahibi veya Strateji ile iletişime geçin.',403)
    if doc.revision!=expected_revision:
        fail('Faaliyet raporu başka bir kullanıcı tarafından güncellendi. Son sürümü açıp değişikliklerinizi yeniden uygulayın.',409)


def event(db,user,doc,code,action,before,after):
    db.add(ARContentEvent(document_id=doc.id, section_code=code, action=action,
        before_json=numeric_canonical(before), after_json=numeric_canonical(after),actor_id=user.id))


def create_year(db,user,organization_id,period_id,copy_previous=False):
    actor(user)
    if user.role!='strategy':
        fail('Yıl raporlarını Strateji oluşturabilir. Strateji ile iletişime geçin.',403)
    org=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    period=db.get(ReportingPeriod,period_id)
    if not org or not period:
        fail('Kurum veya raporlama yılı bulunamadı. Listedeki kurum ve yılı seçin.',404)
    version=db.scalar(select(ARSectionDefinition.version).order_by(ARSectionDefinition.version.desc()).limit(1))
    if not version:
        fail('EK-1 bölüm tanımları yüklenmemiş. Sistem sorumlusundan veritabanı geçişini tamamlamasını isteyin.',409)
    deps=db.scalars(select(Department).join(DepartmentScope,DepartmentScope.department_id==Department.id).where(
        Department.organization_id==org.id,DepartmentScope.period_id==period.id,DepartmentScope.status!='excluded')
        .order_by(Department.id)).all()
    scopes=[None]+[d.id for d in deps]
    existing=db.scalars(select(ARDocument).where(ARDocument.organization_id==org.id,ARDocument.period_id==period.id)).all()
    existing_scopes={d.scope for d in existing}
    result=list(existing)
    previous_period=db.scalar(select(ReportingPeriod).where(ReportingPeriod.year==period.year-1))
    for dep_id in scopes:
        scope=f'birim:{dep_id}' if dep_id else 'idare'
        if scope in existing_scopes:
            continue
        doc=ARDocument(organization_id=org.id,period_id=period.id,department_id=dep_id,scope=scope,
            definition_version=version,created_by=user.id,revision=0)
        db.add(doc);db.flush()
        previous=None
        previous_approval=None
        if copy_previous and previous_period:
            previous=db.scalar(select(ARDocumentFreeze).join(ARDocument,ARDocument.id==ARDocumentFreeze.document_id).where(
                ARDocument.organization_id==org.id,ARDocument.period_id==previous_period.id,ARDocument.scope==scope)
                .order_by(ARDocumentFreeze.version.desc()).limit(1))
            if dep_id and not previous:
                from .ar_unit_workflow_service import latest
                prior_doc=db.scalar(select(ARDocument).where(ARDocument.organization_id==org.id,
                    ARDocument.period_id==previous_period.id,ARDocument.scope==scope))
                previous_approval=latest(db,prior_doc,'approve') if prior_doc else None
        prior={}
        if previous:
            if digest(previous.payload_json)!=previous.sha256:
                fail('Önceki yılın onaylı kopyası doğrulanamadı. Sistem sorumlusuyla iletişime geçin.',409)
            prior=json.loads(previous.payload_json,parse_float=Decimal)
        elif previous_approval:
            from .ar_unit_workflow_service import verified_payload
            prior=verified_payload(previous_approval)
        for definition in definitions(db,doc):
            old=next((s for s in prior.get('sections',[]) if s['code']==definition.code),None)
            copied=bool(old and definition.code!=CORE)
            db.add(ARSectionContent(document_id=doc.id,definition_id=definition.id,
                blocks_json=canonical(old['blocks']) if copied else '[]',status='draft' if copied else 'empty',
                reason=old['reason'] if copied else '',copied_from_id=previous.id if copied and previous else None,
                copied_from_approval_id=previous_approval.id if copied and previous_approval else None,
                copied_needs_review=copied,edited_by=user.id if copied else None,edited_at=datetime.now(UTC) if copied else None))
        from .activity_financial_service import seed_statements
        seed_statements(db,doc)
        if dep_id:
            for kind,table in prior.get('resources',{}).items():
                for i,row in enumerate(table['rows']):
                    db.add(ARResourceRow(document_id=doc.id,table_kind=kind,position=i,
                        **{k:row.get(k) for k in RESOURCE_FIELDS}))
        event(db,user,doc,'','create',None,{'copied_from_id':previous.id if previous else None,
            'copied_from_approval_id':previous_approval.id if previous_approval else None})
        result.append(doc)
    db.flush()
    return result


def validate_blocks(blocks):
    if not isinstance(blocks,list) or len(blocks)>500 or len(canonical(blocks))>200000:
        fail('Bölüm metni çok uzun veya biçimi geçersiz. En fazla 500 paragraf, liste ya da tablo kullanın.')
    for block in blocks:
        if not isinstance(block,dict):
            fail('Bölüm içeriği okunamadı. Paragraf, liste veya tablo seçerek yeniden kaydedin.')
        kind=block.get('type')
        if kind=='paragraph' and set(block)=={'type','text'} and isinstance(block['text'],str):
            continue
        if kind=='bullets' and set(block)=={'type','items'} and isinstance(block['items'],list) and all(isinstance(x,str) for x in block['items']):
            continue
        if kind=='table' and set(block)=={'type','rows'} and isinstance(block['rows'],list) and block['rows']:
            rows=block['rows']
            if all(isinstance(row,list) and 0<len(row)==len(rows[0])<=30 and all(isinstance(x,str) for x in row) for row in rows):
                continue
        fail('Bölüm içeriğinin biçimi geçersiz. Paragraf, madde listesi veya eşit sütunlu basit tablo kullanın.')
    return blocks


def section_pair(db,doc,code):
    for definition in definitions(db,doc):
        if definition.code==code:
            content=db.scalar(select(ARSectionContent).where(ARSectionContent.document_id==doc.id,ARSectionContent.definition_id==definition.id))
            return definition,content
    fail('Bölüm bu raporda bulunamadı. EK-1 listesinden geçerli bir bölüm seçin.',404)


def content_data(content):
    return {'blocks':json.loads(content.blocks_json),'status':content.status,'reason':content.reason,
        'copied_from_id':content.copied_from_id,'copied_from_approval_id':content.copied_from_approval_id,
        'copied_needs_review':content.copied_needs_review,
        'edited_by':content.edited_by,'edited_at':content.edited_at.isoformat() if content.edited_at else None}


def save_section(db,user,document_id,code,blocks,status,reason,expected_revision):
    doc=document(db,user,document_id)
    if code == 'EKLER':
        from .assurance_service import LOCK_ERROR
        fail(LOCK_ERROR)
    definition,content=section_pair(db,doc,code)
    writable(db,user,doc,expected_revision,definition)
    validate_blocks(blocks)
    reason=reason.strip()
    if status not in STATUSES or (status=='not_applicable' and not reason):
        fail(f'{definition.title}: Uygulanamaz durumu için gerekçe yazın ve geçerli bir durum seçin.')
    if len(reason)>10000:
        fail(f'{definition.title}: Gerekçe çok uzun. En fazla 10.000 karakter kullanın.')
    if status=='empty' and blocks:
        fail(f'{definition.title}: İçerik var. Taslak veya Hazır durumunu seçin.')
    if status=='ready' and not has_text(blocks) and not has_resources(db,doc,code):
        fail(f'{definition.title}: Hazır işaretlemek için metin veya kaynak tablosu girin; uygulanmıyorsa gerekçe yazın.')
    before=content_data(content)
    content.blocks_json=canonical(blocks);content.status=status;content.reason=reason
    content.copied_needs_review=bool((content.copied_from_id or content.copied_from_approval_id) and status not in {'ready','not_applicable'})
    content.edited_by=user.id;content.edited_at=datetime.now(UTC)
    doc.revision+=1
    event(db,user,doc,code,'section_save',before,content_data(content))
    db.flush()
    return doc


def has_text(blocks):
    return any(b.get('text','').strip() or any(x.strip() for x in b.get('items',[])) or
        any(x.strip() for row in b.get('rows',[]) for x in row) for b in blocks)


def row_data(row):
    return {k:getattr(row,k) for k in RESOURCE_FIELDS}


def resources(db,doc):
    docs=[doc] if doc.department_id else []
    result={k:{'section_code':v[0],'title':v[1],'columns':v[2],'rows':[],'totals':{},'source_documents':[]} for k,v in TABLES.items()}
    if not doc.department_id:
        from .ar_unit_workflow_service import approved_sources
        approved,_=approved_sources(db,doc)
        for approval,payload in approved:
            for kind,table in result.items():
                table['rows'].extend(payload['resources'][kind]['rows'])
                table['source_documents'].append({'id':approval.document_id,'revision':payload['revision'],
                    'approval_id':approval.id,'sha256':approval.sha256})
        docs=[]
    for source in docs:
        rows=db.scalars(select(ARResourceRow).where(ARResourceRow.document_id==source.id).order_by(ARResourceRow.table_kind,ARResourceRow.position,ARResourceRow.id)).all()
        for row in rows:
            result[row.table_kind]['rows'].append({**row_data(row),'department_id':source.department_id,
                'department':period_name(db,doc.period_id,db.get(Department,source.department_id))})
        for table in result.values():
            table['source_documents'].append({'id':source.id,'revision':source.revision})
    for kind,table in result.items():
        for field in ('count','area'):
            if field in dict(TABLES[kind][2]):
                values=[r[field] for r in table['rows']]
                known=[v for v in values if v is not None]
                table['totals'][field]={'value':sum(known) if known else None,'missing':sum(v is None for v in values)}
        # Keep categories and ownership distinct when consolidating, and disclose
        # missing observations instead of silently converting them to zero.
        if 'count' in table['totals']:
            groups={}
            for row in table['rows']:
                key=(row['category'],row['ownership'])
                groups.setdefault(key,[]).append(row['count'])
            table['groups']=[{'category':key[0],'ownership':key[1],
                'count':sum(v for v in values if v is not None) if any(v is not None for v in values) else None,
                'missing':sum(v is None for v in values)} for key,values in groups.items()]
    return result


def has_resources(db,doc,code):
    return any(table['rows'] for kind,table in resources(db,doc).items() if TABLES[kind][0]==code)


def normalize_rows(kind,rows):
    if kind not in TABLES or not isinstance(rows,list) or len(rows)>2000:
        fail('Kaynak tablosu geçersiz veya çok uzun. Geçerli bir tablo ve en fazla 2.000 satır kullanın.')
    allowed=dict(TABLES[kind][2])
    result=[]
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict) or set(row)-set(allowed):
            fail(f'{TABLES[kind][1]}, {i}. satır: Sütunlar geçersiz. Tablodaki alanları kullanın.')
        item={key:None if key in {'count','area'} else '' for key in RESOURCE_FIELDS}
        for key,label in allowed.items():
            value=row.get(key)
            if key in {'count','area'}:
                if value is None:
                    item[key]=None;continue
                if isinstance(value,bool) or not isinstance(value,(int,float,Decimal)):
                    fail(f'{TABLES[kind][1]}, {i}. satır, {label}: Sayı girin veya alanı boş bırakın.')
                try:
                    number=Decimal(str(value))
                    if not number.is_finite() or number<0 or number>=(Decimal('2147483648') if key=='count' else Decimal('1e15')) or number!=number.quantize(Decimal('1') if key=='count' else Decimal('.01')):
                        raise ValueError()
                except (InvalidOperation,ValueError):
                    fail(f'{TABLES[kind][1]}, {i}. satır, {label}: Negatif olmayan geçerli bir sayı girin.')
                item[key]=int(number) if key=='count' else number
            else:
                if not isinstance(value,str) or len(value)>2000:
                    fail(f'{TABLES[kind][1]}, {i}. satır, {label}: En fazla 2.000 karakter metin girin.')
                item[key]=value.strip()
        if kind=='employment' and item['category'] not in EMPLOYMENT:
            fail(f'İstihdam tablosu, {i}. satır: Listeden geçerli bir istihdam türü seçin.')
        if kind in {'buildings','vehicles'} and item['ownership'] not in (['mülk','kira','tahsis'] if kind=='buildings' else ['mülk','kira']):
            fail(f'{TABLES[kind][1]}, {i}. satır: Geçerli mülkiyet türünü seçin.')
        if not (item['category'] or item['name']):
            fail(f'{TABLES[kind][1]}, {i}. satır: Ad veya tür alanını doldurun.')
        result.append(item)
    return result


def save_resources(db,user,document_id,kind,rows,expected_revision):
    doc=document(db,user,document_id)
    if not doc.department_id:
        fail('İdare kaynakları müdürlüklerden hesaplanır. İlgili birim raporundaki kaynak tablosunu düzenleyin.',403)
    if kind not in TABLES:
        fail('Kaynak tablosu bulunamadı. Bölüm listesinden geçerli bir tablo seçin.',404)
    code=TABLES[kind][0]
    definition,content=section_pair(db,doc,code)
    writable(db,user,doc,expected_revision,definition)
    normalized=normalize_rows(kind,rows)
    existing=db.scalars(select(ARResourceRow).where(ARResourceRow.document_id==doc.id,ARResourceRow.table_kind==kind)).all()
    before=[row_data(r) for r in existing]
    for row in existing:
        db.delete(row)
    for i,row in enumerate(normalized):
        db.add(ARResourceRow(document_id=doc.id,table_kind=kind,position=i,**row))
    content.status='draft';content.edited_by=user.id;content.edited_at=datetime.now(UTC)
    doc.revision+=1
    event(db,user,doc,code,'resource_save',{'table':kind,'rows':before},{'table':kind,'rows':normalized})
    db.flush()
    return doc


def core_summary(db,doc):
    report=db.scalar(select(ActivityReport).where(ActivityReport.organization_id==doc.organization_id,ActivityReport.period_id==doc.period_id))
    if not report:
        return {'status':'empty','total':0,'verified':0,'link':'/activity-reports','message':'Gösterge raporu henüz oluşturulmadı. Gerçekleşme ekranında raporu oluşturun.'}
    revision=db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id==report.id,ActivityReportRevision.revision==report.current_revision))
    if not revision:
        return {'status':'empty','total':0,'verified':0,'link':'/activity-reports','message':'Güncel gösterge revizyonu bulunamadı. Gerçekleşme raporunu kontrol edin.'}
    query=select(ReportIndicator).join(PublicationIndicatorBinding,PublicationIndicatorBinding.id==ReportIndicator.publication_binding_id).where(ReportIndicator.report_revision_id==revision.id)
    if doc.department_id:
        query=query.where(PublicationIndicatorBinding.department_id==doc.department_id)
    items=db.scalars(query.order_by(ReportIndicator.id)).all();verified=0;indicators=[]
    for item in items:
        latest=db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id==item.id).order_by(ActualRevision.revision.desc()).limit(1))
        verified+=bool(latest and latest.state=='verified' and json.loads(latest.evidence_json))
        binding=db.get(PublicationIndicatorBinding,item.publication_binding_id)
        definition=db.get(IndicatorDefinitionRevision,binding.definition_revision_id)
        if digest(definition.definition_json)!=definition.sha256:
            fail('Gösterge tanımı doğrulanamadı. Strateji ile gösterge raporunu kontrol edin.',409)
        data=json.loads(definition.definition_json)
        indicators.append({'name':data['name'],'unit':data.get('unit'),'targets':data.get('targets',[]),
            'data_source':data.get('data_source',''), 'actual':latest.value if latest else None,
            'actual_state':latest.state if latest else 'missing','raw_text':latest.raw_text if latest else '',
            'evidence':json.loads(latest.evidence_json) if latest else [],
            'explanation':latest.explanation if latest else '',
            'deviation':json.loads(latest.deviation_json) if latest else {}})
    return {'revision_id':revision.id,'status':'ready' if items and verified==len(items) else 'draft',
        'total':len(items),'verified':verified,'indicators':indicators,'link':f'/activity-reports/revisions/{revision.id}',
        'message':f'{len(items)} göstergenin {verified} tanesinde doğrulanmış, kaynaklı gerçekleşme var.'}


def report_data(db,user,document_id,use_freeze=True,version=None):
    doc=document(db,user,document_id)
    freeze=latest_release(db,doc,version) if version is not None else frozen(db,doc)
    if version is not None and not freeze:
        raise pp_error(404,'Faaliyet raporu sürümü bulunamadı. Sürüm geçmişinden mevcut bir sürüm seçin.','version')
    if freeze and use_freeze:
        if digest(freeze.payload_json)!=freeze.sha256:
            fail('Onaylı faaliyet raporu kopyası doğrulanamadı. Sistem sorumlusuyla iletişime geçin.',409)
        result=json.loads(freeze.payload_json,parse_float=Decimal)
        result.update(frozen=True,sha256=freeze.sha256)
        # Presentation metadata for pre-CIV-046 freezes; never replace stored facts.
        for kind, table in result.get('resources',{}).items():
            if kind in TABLES:table.setdefault('section_code',TABLES[kind][0])
        from .assurance_service import slot
        for row in result['sections']:
            if row['code'] == 'EKLER': slot(db,doc,row,frozen=True)
        result.update(release_history(db,doc),release_version=freeze.version,revision=doc.revision)
        return result
    if doc.department_id and use_freeze:
        from .ar_unit_workflow_service import latest, verified_payload, view
        current=latest(db,doc)
        if current and current.to_status in {'submitted','approved'}:
            result=verified_payload(current)
            result.update(revision=doc.revision,workflow=view(db,doc),frozen=current.to_status=='approved')
            if current.to_status=='approved':result['sha256']=current.sha256
            return result
    core=core_summary(db,doc) if doc.department_id else {}
    result={'id':doc.id,'organization_id':doc.organization_id,'period_id':doc.period_id,
        'year':db.get(ReportingPeriod,doc.period_id).year,'organization':db.get(Organization,doc.organization_id).name,
        'scope':doc.scope,'department_id':doc.department_id,
        'department':period_name(db,doc.period_id,db.get(Department,doc.department_id)) if doc.department_id else 'İdare',
        'definition_version':doc.definition_version,'revision':doc.revision,'frozen':False,
        'sections':[],'resources':resources(db,doc),'core':core}
    if doc.department_id:
        from .ar_unit_workflow_service import view
        result['workflow']=view(db,doc)
    else:
        from .ar_unit_workflow_service import approved_sources
        approved,missing_units=approved_sources(db,doc)
        result['unit_manifest']=[{'document_id':a.document_id,'approval_id':a.id,'sha256':a.sha256,
            'revision':p['revision'],'department_id':p['department_id'],'department':p['department']} for a,p in approved]
        result['missing_units']=missing_units
        indicators=[i for _,p in approved for i in p['core'].get('indicators',[])]
        core={'status':'ready' if approved and not missing_units and all(p['core']['status']=='ready' for _,p in approved) else 'empty',
            'total':sum(p['core']['total'] for _,p in approved),'verified':sum(p['core']['verified'] for _,p in approved),
            'indicators':indicators,'link':'/activity-reports',
            'message':'Gösterge sonuçları onaylı birim sürümlerinden alınır. Eksik birimlerin onayını tamamlayın.'}
        result['core']=core
    from .activity_financial_service import financial_data, has_slot_data
    result['financial']=financial_data(db,doc)
    contents={c.definition_id:c for c in db.scalars(select(ARSectionContent).where(ARSectionContent.document_id==doc.id))}
    for definition in definitions(db,doc):
        content=contents[definition.id]
        row={'code':definition.code,'title':definition.title,'position':definition.position,
            'parent_id':definition.parent_id,'depth':definition.code.count('.'),
            'owner':owner(definition,doc),'content_kind':definition.content_kind,**content_data(content)}
        missing=[]
        if definition.code==CORE:
            row['status']=core['status']
            if core['status']!='ready':missing.append(core['message'])
        else:
            if content.status in {'empty','draft'}:missing.append('Bölüm içeriğini gözden geçirip Hazır veya gerekçeli Uygulanamaz seçin.')
            if content.copied_needs_review:missing.append('Geçen yıldan kopyalandı — gözden geçirin')
        if content.status!='not_applicable' or has_slot_data(result['financial'],definition.code):
            missing+=result['financial']['missing'].get(definition.code,[])
        row['missing']=missing
        row['editor_name']=db.get(User,content.edited_by).full_name if content.edited_by else '—'
        if definition.code == 'EKLER':
            from .assurance_service import slot
            slot(db,doc,row)
        result['sections'].append(row)
    if use_freeze:result.update(release_history(db,doc))
    return result


def freeze_document(db,user,document_id,expected_revision):
    doc=document(db,user,document_id)
    if doc.department_id:
        from .ar_unit_workflow_service import transition
        return transition(db,user,document_id,'approve',expected_revision)
    if user.role!='strategy':
        fail('Faaliyet raporu içeriğini Strateji onaylayabilir. Strateji ile iletişime geçin.',403)
    writable(db,user,doc,expected_revision)
    previous=latest_release(db,doc)
    payload=report_data(db,user,doc.id,use_freeze=False)
    if payload['missing_units']:
        raise pp_error(409,'İdare faaliyet raporu dondurulamadı. Onaylı birim sürümü eksik: '+
            '; '.join(u['department'] for u in payload['missing_units'])+'. Birim raporlarını gönderip bağımsız onayını tamamlayın.','unit_versions')
    from .ar_unit_workflow_service import completeness
    missing=completeness(payload)
    if missing:
        raise pp_error(409,'İçerik onaylanmadı. Şu bölümleri tamamlayın: '+'; '.join(missing),'sections')
    if previous:
        # Advance the edit token so a waiting stale reopen cannot open N+1.
        doc.revision+=1
        payload['revision']=doc.revision
        db.flush()
    text=numeric_canonical(payload)
    freeze=ARDocumentFreeze(document_id=doc.id,version=previous.version+1 if previous else 1,
        payload_json=text,sha256=digest(text),created_by=user.id)
    db.add(freeze)
    event(db,user,doc,'','freeze',None,{'sha256':freeze.sha256})
    db.flush()
    return freeze


def numeric_canonical(value):
    # Resource quantities remain JSON numbers in the frozen, renderable payload.
    # Decimal area is bounded to 2 places / < 1e15, so a decimal token is exact.
    if isinstance(value,Decimal):return format(value,'f')
    if isinstance(value,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+numeric_canonical(value[k]) for k in sorted(value))+'}'
    if isinstance(value,(list,tuple)):return '['+','.join(numeric_canonical(v) for v in value)+']'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)
