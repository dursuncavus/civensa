"""Owned EK-1 text and resource facts; no dependency on finance or PP creation."""
import json
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException
from sqlalchemy import select
from .models import (ARSectionDefinition, ARDocument, ARSectionContent, ARResourceRow,
    ARDocumentFreeze, ARContentEvent, Department, DepartmentScope, Organization,
    ReportingPeriod, User, ActivityReport, ActivityReportRevision, ReportIndicator,
    ActualRevision, PublicationIndicatorBinding)
from .activity_contract_service import canonical, digest

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


def frozen(db, doc):
    return db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id==doc.id))


def definitions(db, doc):
    kind = 'birim' if doc.department_id else 'idare'
    return db.scalars(select(ARSectionDefinition).where(ARSectionDefinition.version==doc.definition_version,
        ARSectionDefinition.applies_to.in_(['both',kind])).order_by(ARSectionDefinition.position)).all()


def owner(definition, doc):
    return definition.birim_owner if doc.department_id else definition.idare_owner


def can_edit(db, user, doc, definition):
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
    if definition and not can_edit(db,user,doc,definition):
        fail('Bu bölümde düzenleme yetkiniz yok. Bölüm sahibi veya Strateji ile iletişime geçin.',403)
    lock_documents(db,doc)
    if frozen(db,doc):
        fail('Bu faaliyet raporunun içeriği onaylanıp donduruldu. Onaylı kopya değiştirilemez.',409)
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
        if copy_previous and previous_period:
            previous=db.scalar(select(ARDocumentFreeze).join(ARDocument,ARDocument.id==ARDocumentFreeze.document_id).where(
                ARDocument.organization_id==org.id,ARDocument.period_id==previous_period.id,ARDocument.scope==scope))
        prior={}
        if previous:
            if digest(previous.payload_json)!=previous.sha256:
                fail('Önceki yılın onaylı kopyası doğrulanamadı. Sistem sorumlusuyla iletişime geçin.',409)
            prior=json.loads(previous.payload_json,parse_float=Decimal)
        for definition in definitions(db,doc):
            old=next((s for s in prior.get('sections',[]) if s['code']==definition.code),None)
            copied=bool(old and definition.code!=CORE)
            db.add(ARSectionContent(document_id=doc.id,definition_id=definition.id,
                blocks_json=canonical(old['blocks']) if copied else '[]',status='draft' if copied else 'empty',
                reason=old['reason'] if copied else '',copied_from_id=previous.id if copied else None,
                copied_needs_review=copied,edited_by=user.id if copied else None,edited_at=datetime.now(UTC) if copied else None))
        if dep_id:
            for kind,table in prior.get('resources',{}).items():
                for i,row in enumerate(table['rows']):
                    db.add(ARResourceRow(document_id=doc.id,table_kind=kind,position=i,
                        **{k:row.get(k) for k in RESOURCE_FIELDS}))
        event(db,user,doc,'','create',None,{'copied_from_id':previous.id if previous else None})
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
        'copied_from_id':content.copied_from_id,'copied_needs_review':content.copied_needs_review,
        'edited_by':content.edited_by,'edited_at':content.edited_at.isoformat() if content.edited_at else None}


def save_section(db,user,document_id,code,blocks,status,reason,expected_revision):
    doc=document(db,user,document_id)
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
    content.copied_needs_review=bool(content.copied_from_id and status not in {'ready','not_applicable'})
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
    docs=[doc] if doc.department_id else db.scalars(select(ARDocument).where(
        ARDocument.organization_id==doc.organization_id,ARDocument.period_id==doc.period_id,ARDocument.department_id.is_not(None)).order_by(ARDocument.id)).all()
    result={k:{'title':v[1],'columns':v[2],'rows':[],'totals':{},'source_documents':[]} for k,v in TABLES.items()}
    for source in docs:
        rows=db.scalars(select(ARResourceRow).where(ARResourceRow.document_id==source.id).order_by(ARResourceRow.table_kind,ARResourceRow.position,ARResourceRow.id)).all()
        for row in rows:
            result[row.table_kind]['rows'].append({**row_data(row),'department_id':source.department_id,
                'department':db.get(Department,source.department_id).name})
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
    items=db.scalars(query).all();verified=0
    for item in items:
        latest=db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id==item.id).order_by(ActualRevision.revision.desc()).limit(1))
        verified+=bool(latest and latest.state=='verified' and json.loads(latest.evidence_json))
    return {'revision_id':revision.id,'status':'ready' if items and verified==len(items) else 'draft',
        'total':len(items),'verified':verified,'link':f'/activity-reports/revisions/{revision.id}',
        'message':f'{len(items)} göstergenin {verified} tanesinde doğrulanmış, kaynaklı gerçekleşme var.'}


def report_data(db,user,document_id,use_freeze=True):
    doc=document(db,user,document_id)
    freeze=frozen(db,doc)
    if freeze and use_freeze:
        if digest(freeze.payload_json)!=freeze.sha256:
            fail('Onaylı faaliyet raporu kopyası doğrulanamadı. Sistem sorumlusuyla iletişime geçin.',409)
        result=json.loads(freeze.payload_json,parse_float=Decimal)
        result.update(frozen=True,sha256=freeze.sha256)
        return result
    core=core_summary(db,doc)
    result={'id':doc.id,'organization_id':doc.organization_id,'period_id':doc.period_id,
        'year':db.get(ReportingPeriod,doc.period_id).year,'scope':doc.scope,'department_id':doc.department_id,
        'department':db.get(Department,doc.department_id).name if doc.department_id else 'İdare',
        'definition_version':doc.definition_version,'revision':doc.revision,'frozen':False,
        'sections':[],'resources':resources(db,doc),'core':core}
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
        row['missing']=missing
        row['editor_name']=db.get(User,content.edited_by).full_name if content.edited_by else '—'
        result['sections'].append(row)
    return result


def freeze_document(db,user,document_id,expected_revision):
    doc=document(db,user,document_id)
    if user.role!='strategy':
        fail('Faaliyet raporu içeriğini Strateji onaylayabilir. Strateji ile iletişime geçin.',403)
    writable(db,user,doc,expected_revision)
    payload=report_data(db,user,doc.id,use_freeze=False)
    missing=[s['title'] for s in payload['sections'] if s['code']!=CORE and s['missing']]
    if missing:
        fail('İçerik onaylanmadı. Şu bölümleri tamamlayın: '+'; '.join(missing),409)
    text=numeric_canonical(payload)
    freeze=ARDocumentFreeze(document_id=doc.id,payload_json=text,sha256=digest(text),created_by=user.id)
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
