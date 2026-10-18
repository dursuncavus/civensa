"""Deterministic fictional CIV-046 payload; no database or personal data required.

Run from the repository root: PYTHONPATH=. python tools/create_ar_docx_demo.py
"""
import importlib.util
from pathlib import Path
from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
from app.assurance_service import view, VERSION_ID, FILE_SHA256

ROOT = Path(__file__).resolve().parents[1]


def demo_payload():
    spec = importlib.util.spec_from_file_location('ek1_seed', next((ROOT / 'migrations/versions').glob('c037*.py')))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    sections = []
    for definition in migration.SECTION_SEED:
        if definition['applies_to'] == 'idare':
            continue
        code = definition['code']
        blocks = []
        if code == 'I.A':
            blocks = [{'type':'paragraph', 'text':'Örnek Belediyesi, kent yaşamını iyileştiren hizmetleri erişilebilir ve ölçülebilir biçimde sunar. Bu belge yalnızca kurgusal gösterim verileri içerir.'},
                      {'type':'bullets', 'items':['Mahallelerde düzenli bakım hizmeti sunmak.', 'Kaynak kullanımını ve hizmet sonuçlarını birlikte izlemek.']}]
        elif code == 'III.B.2.ii':
            blocks = []
        elif definition['parent_id']:
            blocks = [{'type':'paragraph', 'text':f"{definition['title']} kapsamında yıl içindeki çalışmalar değerlendirilmiştir. Ayrıntılar ilgili kayıt ve tablolarda sunulmaktadır."}]
        sections.append(dict(code=code, title=definition['title'], position=definition['position'], depth=code.count('.'),
            status='draft', reason='', blocks=blocks, missing=[]))
    by_code = {s['code']:s for s in sections}
    by_code['I.A']['missing'] = ['Bölüm içeriğini gözden geçirip Hazır veya gerekçeli Uygulanamaz seçin.']
    by_code['III.B.2.ii'].update(status='not_applicable', reason='Rapor yılında performans denetimi yapılmamıştır.')
    assurance = dict(code='EK-2', version_id=VERSION_ID, file_sha256=FILE_SHA256,
        variables=dict(place='Örnek İlçe', date='2028-02-15', reservations=[], signatories=[
            dict(person_ref='demo-1', name='Örnek İmzalayan', title='Örnek Birim Yetkilisi', start_date='2027-01-01', end_date='2027-12-31')]))
    assurance['rendered'] = view(assurance)
    by_code['EKLER']['assurances'] = [assurance]
    by_code['EKLER']['blocks'] = []
    budget = dict(department='Fen İşleri Müdürlüğü', classification='03 · Mal ve Hizmet Alım Giderleri',
        initial='12500.23', added=0, deducted=0, entered_final='12500.23', final='12500.23', actual='10000.00',
        cancelled=None, carried=0, rate='80.00', pp_budget='12500.23', explanation='Yılın son alımı sonraki döneme bırakıldı.',
        birim_explanation='Bakım hizmetleri tamamlandı; ekipman alımı ertelendi.')
    totals = {key:dict(value=budget[key], missing=int(budget[key] is None)) for key in
              ['initial','added','deducted','final','actual','cancelled','carried','rate']}
    return dict(year=2027, organization='Örnek Belediyesi', department='Fen İşleri Müdürlüğü', department_id=1,
        scope='birim:1', frozen=False, sections=sections,
        resources={'hardware':dict(section_code='I.C.3', title='Donanım', columns=[('category','Türü'),('count','Adet')],
            rows=[dict(category='Bilgisayar',count=12),dict(category='Yazıcı',count=None),dict(category='Sunucu',count=0)],
            totals={'count':dict(value=12,missing=1)})},
        financial=dict(tables={'expenditure':dict(rows=[budget],totals=totals)}, policy=dict(lower_rate=85,upper_rate=110),
            entries={'assets':[dict(label='Hizmet binası',amount='1500000.00',previous=None,explanation='Yıl sonu kayıt değeri')],
                     'audit':[dict(audit_type='İç denetim',auditor='Örnek Denetim Birimi',period='2027',report_date='2027-12-20',
                                   report_number='ÖRNEK-1',findings='Bakım kayıtları geliştirilmeli.',measures='Aylık kayıt takvimi oluşturuldu.',status='İzleniyor')],
                     'aid':[dict(name='Örnek Kuruluş',aid_type='Aynî',amount=0,basis='Örnek karar',explanation='Bu yıl yardım yapılmadı.')]}, statements=[]),
        core=dict(message='1 göstergenin 1 tanesinde doğrulanmış, kaynaklı gerçekleşme var.', indicators=[
            dict(name='Bakımı tamamlanan park sayısı',unit='Adet',targets=[dict(value=20,state='verified')],actual=22,
                 actual_state='verified',data_source='Örnek bakım kayıtları',evidence=[dict(title='Yıl sonu bakım özeti',locator='Tablo 1',source_revision='2027/12')],
                 explanation='İlave iki parkın bakımı tamamlandı.')]))


if __name__ == '__main__':
    destination = ROOT / 'docs/civ046/ornek-taslak.docx'
    destination.write_bytes(build_activity_report_docx(demo_payload(), TEMPLATE_PATH))
    print(destination.relative_to(ROOT))
