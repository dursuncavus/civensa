"""Synthetic persisted-source fixture; no database access. Rebuild both merge samples."""
import copy
import hashlib
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from app.activity_sections_service import TABLES, RESOURCE_FIELDS, numeric_canonical
from app.activity_financial_service import ENTRY_FIELDS, DEFAULT_STATEMENTS
from app.ar_typeset_contract import export_bytes
from app.ar_typeset_csv import table_csv


def sample_source():
    spec = importlib.util.spec_from_file_location('civ086_sections', next((ROOT/'migrations/versions').glob('c037*.py')))
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    sections = [{'code': row['code'], 'title': row['title'], 'position': row['position'],
        'parent_id': row['parent_id'], 'depth': row['code'].count('.'), 'owner': row['idare_owner'],
        'content_kind': row['content_kind'], 'status': 'ready', 'reason': '', 'missing': [],
        'copied_from_id': None, 'copied_from_approval_id': None, 'copied_needs_review': False,
        'edited_by': 1, 'edited_at': '2026-10-24T09:00:00+00:00', 'editor_name': 'Sentetik Strateji',
        'blocks': [{'type':'paragraph','text':'Sentetik örnek: '+row['title']}]} for row in migration.SECTION_SEED]
    by_code = {row['code']:row for row in sections}
    by_code['I.A']['blocks'].append({'type':'table','rows':[['Hizmet','Sonuç'],['Örnek hizmet','5']]})
    by_code['II.A'].update(copied_from_id=7)
    resources = {kind:{'section_code':section,'title':title,'columns':columns,'rows':[],
        'totals':{},'source_documents':[]} for kind,(section,title,columns) in TABLES.items()}
    hardware = {key:None if key in {'count','area'} else '' for key in RESOURCE_FIELDS}
    hardware.update(category='Bilgisayar',count=0,department_id=2,department='Sentetik Birim')
    resources['hardware'].update(rows=[hardware],totals={'count':{'value':0,'missing':0}},
        groups=[{'category':'Bilgisayar','ownership':'','count':0,'missing':0}],
        source_documents=[{'id':2,'revision':4,'approval_id':9,'sha256':hashlib.sha256(b'synthetic-unit').hexdigest()}])
    budget = {'id':1,'row_key':'dep:2:03','department_id':2,'department':'Sentetik Birim','economic_code':'03',
        'program_id':None,'subprogram_id':None,'classification':'03 · Mal ve hizmet',
        'initial':Decimal('12500.23'),'added':Decimal('0.00'),'deducted':Decimal('0.00'),'entered_final':None,
        'actual':Decimal('12500.23'),'cancelled':Decimal('0.00'),'carried':Decimal('0.00'),
        'final':Decimal('12500.23'),'rate':Decimal('100.00'),'pp_budget':None,'pp_publication_id':1,
        'explanation':'Sentetik kaynak','birim_explanation':'','import_id':3}
    financial = {'source_document_id':1,'source_revision':5,'policy':{'lower_rate':None,'upper_rate':None},
        'tables':{kind:{'rows':[budget] if kind=='expenditure' else [],'totals':{},'by_department':[]}
                  for kind in ('expenditure','programme','revenue')},
        'entries':{kind:[] for kind in ENTRY_FIELDS},'checks':[],'missing':{},'imports':[],
        'statements':[{'id':1,'name':DEFAULT_STATEMENTS[0],'period':'2027','statement_date':'2027-12-31',
            'explanation':'Sentetik bilanço özeti','figures':[{'label':'Aktif toplamı','amount':Decimal('12500.23')}],
            'filename':'sentetik-bilanco.pdf','sha256':hashlib.sha256(b'synthetic-statement').hexdigest()}]}
    financial['entries'].update(assets=[{'label':'Varlık','amount':Decimal('12500.23'),'previous':Decimal('0.00'),
        'explanation':'Sentetik kayıt'}],aid_directorates=[],audit_directorates=[])
    source = {'id':1,'organization_id':1,'period_id':1,'year':2027,'organization':'Sentetik Belediyesi',
        'scope':'idare','department_id':None,'department':'İdare','definition_version':1,'revision':5,'frozen':False,
        'sections':sections,'resources':resources,'financial':financial,
        'core':{'status':'ready','total':1,'verified':1,'link':'/activity-reports','message':'Sentetik doğrulanmış gösterge.',
            'indicators':[{'name':'Hizmet sayısı','unit':'Adet','targets':[{'year':2027,'value':'12500.23','state':'verified'}],
                'data_source':'Sentetik kayıt','actual':Decimal('12500.230000'),'actual_state':'verified',
                'raw_text':'12.500,23','evidence':[{'title':'Sentetik kaynak','locator':'Sayfa 1','source_revision':'1'}],
                'explanation':'Sentetik açıklama','deviation':{'calculation_rule_version':'difference-v1',
                    'target_definition_revision_id':1,'delta':'0.000000','achievement_percent':None}}]}}
    source['_typeset'] = {'schema_version':'ar-source/1','complete':True,'generated_at':'2026-10-24T09:00:00+00:00',
        'sections':{row['code']:[] for row in sections},'resources':{kind:[] for kind in TABLES},
        'entries':{kind:[] for kind in financial['entries']},'figures':{'1':['10000000-0000-4000-8000-000000000031']},
        'indicators':[{'document_id':2,'department_id':2,'indicator_id':'10000000-0000-4000-8000-000000000041'}],
        'activities':[{'document_id':2,'department_id':2,'publication_id':1,'data':{'id':11,'name':'Sentetik hizmet',
            'official_ids':[77],'program':'Sentetik program','subprogram':'Sentetik alt program',
            'costs':[{'id':99,'activity_id':11,'year':2027,'value_kind':'budget','funding_type':'inside','amount':'12500.23'}]}}]}
    source['_typeset']['sections']['I.A'] = [{'position':1,'stable_key':'10000000-0000-4000-8000-000000000001',
        'rows':['10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000003']}]
    source['_typeset']['resources']['hardware'] = [{'document_id':2,'stable_key':'10000000-0000-4000-8000-000000000011'}]
    source['_typeset']['entries']['assets'] = [{'document_id':1,'stable_key':'10000000-0000-4000-8000-000000000021'}]
    return source


def generate():
    folder = Path(__file__).parent
    source = sample_source()
    raw = numeric_canonical(source)
    (folder/'synthetic-source.json').write_text(raw,encoding='utf-8')
    first = export_bytes(source,release_version=1,source_sha256=hashlib.sha256(raw.encode()).hexdigest())
    (folder/'release-1.typeset.json').write_bytes(first)
    updated = copy.deepcopy(source)
    updated['core']['indicators'][0]['actual'] += Decimal('1.000001')
    updated['core']['indicators'][0]['deviation']['delta'] = '1.000001'
    updated['_typeset']['generated_at'] = '2026-10-24T10:00:00+00:00'
    updated['revision'] += 1
    second = export_bytes(updated,release_version=2,source_sha256=hashlib.sha256(numeric_canonical(updated).encode()).hexdigest())
    (folder/'release-2-one-indicator.typeset.json').write_bytes(second)
    contract = json.loads(first)
    (folder/'hardware.csv').write_bytes(table_csv(contract,'ar:1:resource:hardware'))


if __name__ == '__main__':
    generate()
