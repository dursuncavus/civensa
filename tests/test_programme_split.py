"""CIV-045: atomic Strategy allocation, source scope, and real browser flow."""
import json
from decimal import Decimal

import pytest
from sqlalchemy import select, func

from app.models import EconomicValue, AuditLog, Submission, ReportCard, Program, SubProgram
from app.main import app, require_user
from app.program_service import validate_department
from test_sidebar_ui import browser
from test_word_import import import_context
from test_word_import_real_source import real_source, real_parsed

pytestmark = pytest.mark.postgres


@pytest.fixture
def split_rows(db, sample):
    """An otherwise complete compact-table directorate with mixed programme cards."""
    program = Program(period_id=sample['period'].id, name='Yönetim ve Destek Programı')
    db.add(program); db.flush()
    sp = SubProgram(period_id=sample['period'].id, program_id=program.id, name='Destek')
    db.add(sp); db.flush()
    card = ReportCard(period_id=sample['period'].id, department_id=sample['department'].id,
        subprogram_id=sp.id, source_title='2027/2', goal='Destek hedefi', rationale='Gerekçe',
        responsible='Test Belediyesi', source_page='42')
    db.add(card); db.flush()
    rows = db.scalars(select(EconomicValue).order_by(EconomicValue.id)).all()
    # Keep the Ministry compact category set, rather than fabricate six missing rows.
    for row in rows:
        if row.category not in {'personnel', 'sgk', 'goods_services'}:
            db.delete(row); continue
        row.program_group = 'unallocated'; row.state = 'needs_review'
        row.source_card_id = sample['card'].id; row.source_table_number = 7
        row.source_context_json = json.dumps({'categories':['personnel','sgk','goods_services'],
            'card_ids':[sample['card'].id, card.id], 'block_table_numbers':[1,2], 'totals':{}})
        row.raw_text = str(row.amount)
        row.issue = (f'Tablo 7, {row.year} ' + ('Bütçe' if row.value_kind=='budget' else 'Tahmin') +
            ': Program grubu dağılımı kaynakta ayrılmamış. Programlar: Test Programı; Yönetim ve Destek Programı. '
            'Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin.')
    db.commit()
    return db.scalars(select(EconomicValue).order_by(EconomicValue.id)).all()


def payload(rows):
    from app.economic_split_service import split_fingerprint
    data = {'period_id':rows[0].period_id, 'reason':'2027 program bütçesi, Mali Hizmetler tablosu',
            'cell_id':[str(r.id) for r in rows]}
    for row in rows:
        data[f'fingerprint_{row.id}'] = split_fingerprint(row)
        # Every positive cell splits two ways. Zero rows get a single explicit destination.
        service = (row.amount / 2).quantize(Decimal(".01"))
        data[f'share_{row.id}_service'] = str(service).replace('.', ',')
        data[f'share_{row.id}_management'] = str(row.amount-service).replace('.', ',')
        data[f'share_{row.id}_outside_program'] = ''
        data[f'zero_group_{row.id}'] = 'service'
    return data


def strategy(sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']


def test_strategy_split_route_exists(client, sample):
    strategy(sample)
    response = client.get('/program/1/economic-split?period_id=1')
    assert response.status_code == 200


def post_split(client, sample, data, **kwargs):
    strategy(sample)
    return client.post(f"/program/{sample['department'].id}/economic-split", data=data,
        follow_redirects=False, **kwargs)


def snapshot(db):
    from app.program_service import record
    return [record(r) for r in db.scalars(select(EconomicValue).order_by(EconomicValue.id))]


def test_split_two_groups_audit_provenance_and_compact_validation(client, db, sample, split_rows):
    before = {r['id']:r for r in snapshot(db)}
    assert any('program grubu doğrulanmalı' in e for e in validate_department(db,1,1)[0])
    response = post_split(client,sample,payload(split_rows))
    assert response.status_code == 303, response.text
    rows = db.scalars(select(EconomicValue)).all()
    assert all(r.program_group!='unallocated' for r in rows)
    audits = db.scalars(select(AuditLog).where(AuditLog.action=='economic_programme_split')).all()
    assert len(audits)==len(before)
    for audit in audits:
        details = json.loads(audit.details)
        original = before[audit.entity_id]
        assert details['original']==original
        assert details['reason']=='2027 program bütçesi, Mali Hizmetler tablosu'
        assert audit.user_id==sample['strategy'].id
        replacements = details['resulting']
        assert sum(Decimal(r['amount']) for r in replacements)==Decimal(original['amount'])
        assert len(replacements)==(2 if Decimal(original['amount'])>0 else 1)
        for replacement in replacements:
            assert replacement['state']=='verified' and replacement['issue']==''
            assert replacement['raw_text']==original['raw_text']
            assert replacement['source_card_id']==original['source_card_id']
            assert replacement['source_table_number']==7
            ctx=json.loads(replacement['source_context_json'])
            split=ctx.pop('split_from')
            assert ctx==json.loads(original['source_context_json'])
            assert split['original_id']==original['id']
            assert Decimal(split['amount'])==Decimal(original['amount'])
            assert split['raw_text']==original['raw_text']
            assert split['actor']==sample['strategy'].id and split['time']==details['time']
            assert split['reason']==details['reason'] and split['state']=='needs_review'
    # No full-category fabrication: imported scope and explicit zero shares suffice.
    assert {r.category for r in rows}=={'personnel','sgk','goods_services'}
    assert validate_department(db,1,1)[0]==[]
    from app.program_service import department_package_snapshot, validate_department_snapshot
    frozen=department_package_snapshot(db,1,1)
    assert validate_department_snapshot(frozen,1,1)[0]==[]
    assert db.scalar(select(AuditLog.id).where(AuditLog.action=='pp_data_change',AuditLog.user_id==sample['strategy'].id))
    from app.released_permissions import require_independent_pp_approver
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as caught:
        require_independent_pp_approver(db,sample['strategy'],db.scalar(select(Submission)))
    assert caught.value.status_code==403


def test_sum_mismatch_is_actionable_and_all_or_nothing(client, db, sample, split_rows):
    before=snapshot(db); data=payload(split_rows)
    row=next(r for r in split_rows if r.year==2027 and r.category=='goods_services' and r.funding_type=='inside')
    data[f'share_{row.id}_service']='100'; data[f'share_{row.id}_management']='20'
    response=post_split(client,sample,data,headers={'Accept':'application/json'})
    assert response.status_code==422
    assert response.json()['detail']=='2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: paylar toplamı 120,00, kaynak tutar 123,45 (fark -3,45). Payları düzeltin.'
    assert snapshot(db)==before
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action=='economic_programme_split'))


@pytest.mark.parametrize('raw,fragment',[('-1','negatif'),('0,001','ondalık'),('—','Çizgi'),('NaN','Sayı biçimi')])
def test_invalid_share_rejected(client,db,sample,split_rows,raw,fragment):
    before=snapshot(db); data=payload(split_rows)
    data[f'share_{split_rows[-1].id}_service']=raw
    response=post_split(client,sample,data)
    assert response.status_code==422 and fragment in response.text
    assert snapshot(db)==before


def test_department_user_gets_403(client,sample,split_rows):
    assert client.get('/program/1/economic-split?period_id=1').status_code==403
    assert client.post('/program/1/economic-split',data=payload(split_rows)).status_code==403
    assert 'Program Grubu Dağılımı' not in client.get('/program/1?period_id=1').text


@pytest.mark.parametrize('state',['submitted','approved','closed'])
def test_locked_package_or_period_rejected(client,db,sample,split_rows,state):
    if state=='closed':sample['period'].status=state
    else:db.scalar(select(Submission)).status=state
    db.commit(); before=snapshot(db)
    response=post_split(client,sample,payload(split_rows))
    assert response.status_code==409
    assert ('etkinleştirip' if state=='closed' else 'iade edilmesini') in response.text
    assert snapshot(db)==before


def test_existing_target_names_the_conflict(client,db,sample,split_rows):
    row=split_rows[-1]
    other=EconomicValue(period_id=row.period_id,department_id=row.department_id,year=row.year,
        value_kind=row.value_kind,category=row.category,program_group='service',funding_type=row.funding_type,amount=1)
    db.add(other); db.commit(); db.refresh(other); before=snapshot(db)
    response=post_split(client,sample,payload(split_rows))
    assert response.status_code==409
    assert f'kayıt {other.id}' in response.text and 'Hizmet Programları' in response.text
    assert snapshot(db)==before


@pytest.mark.parametrize('mutation',['reason','stale','missing','duplicate','foreign','null','zero_group'])
def test_missing_reason_or_stale_source_fails_closed(client,db,sample,split_rows,mutation):
    data=payload(split_rows); row=split_rows[0]
    if mutation=='reason':data['reason']='  '
    if mutation=='stale':row.raw_text='Düzeltilmiş kaynak'; db.commit()
    if mutation=='missing':data['cell_id']=data['cell_id'][1:]
    if mutation=='duplicate':data['cell_id'].append(data['cell_id'][0])
    if mutation=='foreign':data['cell_id'][0]='999999'
    if mutation=='null':row.amount=None; db.commit(); data=payload_nonnull(split_rows,row)
    if mutation=='zero_group':
        row=next(r for r in split_rows if r.amount==0)
        data[f'zero_group_{row.id}']=''
    before=snapshot(db)
    response=post_split(client,sample,data)
    assert response.status_code in {409,422},response.text
    assert snapshot(db)==before


def payload_nonnull(rows, null_row):
    # Construct a valid-looking form for an unresolved amount without treating it as zero.
    from app.economic_split_service import split_fingerprint
    data=payload([r for r in rows if r!=null_row]); data['cell_id'].append(str(null_row.id))
    data[f'fingerprint_{null_row.id}']=split_fingerprint(null_row)
    return data


def test_blank_shares_zero_only_for_existing_source(client,db,sample,split_rows):
    data=payload(split_rows)
    for row in split_rows:
        data[f'share_{row.id}_service']=str(row.amount).replace('.',',')
        data[f'share_{row.id}_management']=''
        data[f'share_{row.id}_outside_program']=''
        if row.amount==0:data[f'share_{row.id}_service']=''
    response=post_split(client,sample,data)
    assert response.status_code==303,response.text
    rows=db.scalars(select(EconomicValue)).all()
    assert len(rows)==len(split_rows) and all(r.program_group=='service' for r in rows)
    assert validate_department(db,1,1)[0]==[]
    assert post_split(client,sample,data).status_code==409  # replay cannot create phantom zero rows


def test_other_review_causes_survive_allocation(client,db,sample,split_rows):
    row=split_rows[0]; row.issue+=' Tablo toplamı uyuşmuyor. Kaynak tabloyu kontrol edin.'; db.commit()
    response=post_split(client,sample,payload(split_rows))
    assert response.status_code==303,response.text
    replacements=db.scalars(select(EconomicValue).where(EconomicValue.year==row.year,
        EconomicValue.category==row.category,EconomicValue.funding_type==row.funding_type)).all()
    assert all(r.state=='needs_review' and r.issue=='Tablo toplamı uyuşmuyor. Kaynak tabloyu kontrol edin.' for r in replacements)
    assert any('kaynak tutarı ve program grubu doğrulanmalı' in e for e in validate_department(db,1,1)[0])


def test_audit_insert_failure_rolls_back_every_replacement(client,db,sample,split_rows):
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError
    before=snapshot(db)
    def fail_audit(mapper, connection, row):
        if row.action=='economic_programme_split':
            raise IntegrityError('synthetic audit failure',{},Exception('test only'))
    event.listen(AuditLog,'before_insert',fail_audit)
    try:
        response=post_split(client,sample,payload(split_rows))
        assert response.status_code==409
    finally:
        event.remove(AuditLog,'before_insert',fail_audit)
    assert snapshot(db)==before
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action=='economic_programme_split'))


def test_two_simultaneous_splits_have_one_audited_winner(db,sample,split_rows):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from fastapi import HTTPException
    from app.economic_split_service import split_economic_cells, split_fingerprint
    from app.models import User
    cells=[{'id':r.id,'fingerprint':split_fingerprint(r),
            'shares':{'service':str(r.amount).replace('.',',')},'zero_group':'service'} for r in split_rows]
    barrier=Barrier(2); actor_id=sample['strategy'].id
    def run(_):
        with Session(db.get_bind()) as session:
            actor=session.get(User,actor_id); barrier.wait(timeout=5)
            try:
                split_economic_cells(session,actor,1,1,cells,'Eşzamanlı dağılım testi')
                session.commit(); return 200
            except HTTPException as exc:
                session.rollback(); return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run,range(2)))==[200,409]
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action=='economic_programme_split'))==len(split_rows)


def test_compact_split_scope_does_not_hide_a_missing_positive_share(client,db,sample,split_rows):
    assert post_split(client,sample,payload(split_rows)).status_code==303
    row=db.scalar(select(EconomicValue).where(EconomicValue.program_group=='management',
        EconomicValue.year==2027,EconomicValue.category=='goods_services',EconomicValue.funding_type=='inside'))
    db.delete(row); db.commit()
    errors=validate_department(db,1,1)[0]
    assert any('Yönetim ve Destek Programı / Bütçe İçi' in e and 'hücresi eksik' in e for e in errors)


def test_strategy_browser_walkthrough(browser,client,db,sample,split_rows,tmp_path):
    import os
    from pathlib import Path
    from playwright.sync_api import expect
    from app.security import hash_password
    app.dependency_overrides.pop(require_user,None)
    sample['strategy'].password_hash=hash_password('split-browser-test-only'); db.commit()
    assert client.post('/login',data={'email':sample['strategy'].email,
        'password':'split-browser-test-only'},follow_redirects=False).status_code==303
    with browser.new_context(viewport={'width':1600,'height':1000}) as context:
        requests=[]
        def serve(route):
            req=route.request
            response=client.request(req.method,req.url,content=req.post_data_buffer,
                headers={'content-type':req.headers.get('content-type',''),
                    'X-CSRF-Token':req.headers.get('x-csrf-token',''),
                    'Accept':req.headers.get('accept','')},
                follow_redirects=req.resource_type in {'fetch','xhr'})
            requests.append((req.method,response.status_code))
            headers=dict(response.headers); headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page(); errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://testserver/program/1?period_id=1')
        page.get_by_role('link',name='Program Grubu Dağılımı',exact=True).click()
        expect(page.get_by_role('heading',name='Test Müdürlüğü — Program Grubu Dağılımı')).to_be_visible()
        expect(page.get_by_text('Referans: Müdürlüğün Program Kartları')).to_be_visible()
        data=payload(split_rows)
        for key,value in data.items():
            if key.startswith(('share_','zero_group_')):
                field=page.locator(f'[name="{key}"]')
                if key.startswith('zero_group_'):
                    if field.count():field.select_option(value)
                else:field.fill(value)
        page.locator('[name="reason"]').fill(data['reason'])
        expect(page.locator('[data-split-remaining]').filter(has_text='0,00')).to_have_count(len(split_rows))
        # Store a reviewable screenshot only when explicitly requested by the local run.
        screenshot_dir=Path(os.getenv('CIVENSA_SPLIT_SCREENSHOT_DIR',str(tmp_path)))
        screenshot_dir.mkdir(parents=True,exist_ok=True)
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(screenshot_dir/'strategy-programme-split.png'))
        # A mismatch must preserve the entire filled form and show the server's cell error.
        row=next(r for r in split_rows if r.year==2027 and r.category=='goods_services' and r.funding_type=='inside')
        field=page.locator(f'[name="share_{row.id}_service"]')
        original=field.input_value(); field.fill('100')
        expect(page.locator(f'[data-split-cell="{row.id}"] [data-split-remaining]')).to_have_text('-38,28')
        page.get_by_role('button',name='Müdürlüğün Tüm Dağılımını Kaydet').click()
        expect(page.locator('#economicSplitErrors')).to_contain_text('Payları düzeltin.')
        expect(field).to_have_value('100')
        assert not db.scalar(select(AuditLog.id).where(AuditLog.action=='economic_programme_split'))
        field.fill(original)
        page.get_by_role('button',name='Müdürlüğün Tüm Dağılımını Kaydet').click()
        expect(page.locator('p[role="status"]')).to_contain_text('denetim kaydıyla birlikte kaydedildi')
        expect(page.get_by_text('Bu müdürlük ve dönemde program grubu belirlenmemiş ekonomik hücre yok.')).to_be_visible()
        assert validate_department(db,1,1)[0]==[]
        assert ('POST',422) in requests and ('POST',200) in requests
        assert errors==[]


def test_actual_imported_rows_preserve_compact_scope_and_review_causes(db,import_context,real_parsed):
    from app.models import ImportBatch, Department
    from app.import_service import apply_import_batch
    from app.economic_split_service import split_economic_cells, split_fingerprint
    batch=ImportBatch(period_id=import_context.period.id,filename='local-fixture.docx',
        payload_json=json.dumps(real_parsed),created_by=import_context.user.id)
    db.add(batch); db.commit(); apply_import_batch(db,batch); db.commit()
    department=db.scalar(select(Department).where(Department.name.contains('İnsan Kaynakları')))
    sources=db.scalars(select(EconomicValue).where(EconomicValue.department_id==department.id,
        EconomicValue.program_group=='unallocated').order_by(EconomicValue.id)).all()
    assert len(sources)==40 and all(r.amount is not None for r in sources)
    source_values={(t['table_number'],v['year'],v['kind'],v['category'],v['funding_type']):v
        for d in real_parsed['departments'] for t in d.get('economic_tables',[]) for v in t['values']}
    expected={}
    for row in sources:
        original=source_values[row.source_table_number,row.year,row.value_kind,row.category,row.funding_type]
        unresolved=[c['message'] for c in original['review_causes'] if c['cause']!='program_group_unallocated']
        expected[row.id]=(json.loads(row.source_context_json),
            ('needs_review' if unresolved else 'verified',' '.join(unresolved)))
    assert any(state=='verified' for _,(state,_) in expected.values())
    assert any(state=='needs_review' for _,(state,_) in expected.values())
    cells=[]
    for row in sources:
        half=(row.amount/2).quantize(Decimal('.01'))
        cells.append({'id':row.id,'fingerprint':split_fingerprint(row),
            'shares':{'service':str(half).replace('.',','),
                'management':str(row.amount-half).replace('.',',')},'zero_group':'service'})
    assert split_economic_cells(db,import_context.user,batch.period_id,department.id,cells,
        'Yerel 2027 Word kaynağı, program grubu dağılımı')==40
    db.commit()
    targets=db.scalars(select(EconomicValue).where(EconomicValue.department_id==department.id)).all()
    assert all(r.program_group!='unallocated' for r in targets)
    for row in targets:
        context=json.loads(row.source_context_json); split=context.pop('split_from')
        source_context,(state,issue)=expected[split['original_id']]
        assert context==source_context and (row.state,row.issue)==(state,issue)
    errors,_=validate_department(db,batch.period_id,department.id)
    assert not any('ekonomik gider hücresi eksik' in e or 'ekonomik kaynak kapsamı' in e for e in errors),errors


def test_zero_source_uses_one_explicit_group_and_turkish_thousands_parse(client,db,sample,split_rows):
    row=next(r for r in split_rows if r.amount>0)
    row.amount=Decimal('12500.23'); db.commit()
    data=payload(split_rows)
    data[f'share_{row.id}_service']='12.000,00'
    data[f'share_{row.id}_management']='500,23'
    zero=next(r for r in split_rows if r.amount==0)
    data[f'zero_group_{zero.id}']='outside_program'
    assert post_split(client,sample,data).status_code==303
    zeros=db.scalars(select(EconomicValue).where(EconomicValue.year==zero.year,
        EconomicValue.value_kind==zero.value_kind,EconomicValue.category==zero.category,
        EconomicValue.funding_type==zero.funding_type)).all()
    assert len(zeros)==1 and zeros[0].program_group=='outside_program' and zeros[0].amount==0
    positive=db.scalars(select(EconomicValue).where(EconomicValue.year==row.year,
        EconomicValue.value_kind==row.value_kind,EconomicValue.category==row.category,
        EconomicValue.funding_type==row.funding_type)).all()
    assert {r.program_group:r.amount for r in positive}=={'service':Decimal('12000'),'management':Decimal('500.23')}


def test_allocation_only_directorate_submits_but_splitter_cannot_approve(client,db,sample,split_rows):
    assert post_split(client,sample,payload(split_rows)).status_code==303
    app.dependency_overrides[require_user]=lambda:sample['user']
    submitted=client.post('/api/departments/1/submit')
    assert submitted.status_code==200,submitted.text
    strategy(sample)
    rejected=client.post('/api/submissions/1/decision',json={'decision':'approve'})
    assert rejected.status_code==403 and 'Görevler ayrılığı' in rejected.json()['detail']
    assert db.scalar(select(Submission)).status=='submitted'
