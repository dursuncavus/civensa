"""Sample content: the longest real values from the d3 print IDML, plus safety margins for numbers."""
import json, os

L = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'longest.json'), encoding='utf-8'))

MONEY_UNIT = '9.999.999.999,99'        # directorate-level maximum (real max 2.223.750.000,00)
MONEY_IDARE = '99.999.999.999,99'      # institution-level maximum (real max 11.904.930.191,00)
IND_MAX = '99.999.999'                 # indicator maximum (real max 12.050.000)

PROGRAM = L['kart_PROGRAM ADI']
BIRIM = 'Basın, Yayın ve Halkla İlişkiler Müdürlüğü'
ALT_PROGRAM = L['kart_ALT PROGRAM ADI']
GEREKCE = L['kart_GEREKÇE ve AÇIKLAMALAR']
HEDEF = L['kart_ALT PROGRAMIN HEDEFİ']
GOSTERGE = L['gosterge_adi']
BIRIM_OLCU = L['olcu_birimi']
G_ACIKLAMA = L['kart_Göstergeye İlişkin Açıklama']
HESAPLAMA = L['kart_Hesaplama Yöntemi']
KAYNAK = L['kart_Verinin Kaynağı']
SORUMLU = L['kart_Sorumlu İdare']
FAALIYET_KART = L['faaliyet_adi_kart']
FAALIYET_ORTAK = L['faaliyet_adi_ortak']
UZUN_METIN = L['ortak_tablo_uzun_metin']

INDICATORS = [
    (GOSTERGE, BIRIM_OLCU, [IND_MAX, IND_MAX, IND_MAX, IND_MAX, IND_MAX, IND_MAX]),
    ('SH09.PG05. Taşınmaz envanterinde güncellenen kayıtların toplam kayıtlara oranı', 'Yüzde (%)', ['100', '100', '100', '100', '100', '100']),
    ('SH09.PG06. Kiralama ihalelerinden elde edilen yıllık gelir', 'TL', ['1.234.567', '12.000.000', '12.000.000', '12.050.000', '12.170.000', '12.300.000']),
    ('SH09.PG07. Ortalama işlem süresi', 'Gün', ['12,5', '10,0', '9,5', '9,0', '8,5', '8,0']),
    ('SH09.PG08. Vatandaş memnuniyet oranı', 'Oran (%)', ['95', '95', '96', '97', '98', '99']),
    ('SH09.PG09. Dijital arşive aktarılan dosya sayısı (kümülatif)', 'Sayı (kümülatif Toplamı)', ['6.973', '7.500', '8.054', '8.600', '9.150', '9.700']),
]

# Activity cost rows: (name, six values)
ACTIVITIES_CARD = [
    (FAALIYET_KART, ['0,00', '0,00', '518.596,08', MONEY_UNIT, MONEY_UNIT, MONEY_UNIT]),
    ('0002.2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takibinin yapılması', ['0,00', '0,00', '0,00', '13.050.000,00', '16.250.000,00', '18.800.000,00']),
    ('0003.Semt pazarları tahsis işlemlerinin yapılması', ['-', '-', '-', '984.658,00', '1.168.323,00', '1.366.584,00']),
    ('0004.Kurum taşınmazlarının envanterinin güncel tutulması', ['0,00', '0,00', '0,00', '0,00', '0,00', '0,00']),
    ('0005.Diğer kamu kurum ve kuruluşları ile Belediyemiz arasında irtifak ve intifa hakkı tesisi, tahsis, kiralama ve devir işlemlerinin yürütülmesi', ['1.300.675,00', '650.337,50', '1.300.675,00', '52.000.000,00', '65.000.000,00', '78.000.000,00']),
]
TOTAL_CARD = ['1.300.675,00', '650.337,50', '1.819.271,08', MONEY_UNIT, MONEY_UNIT, MONEY_UNIT]

ACTIVITIES_ORTAK = [
    (FAALIYET_ORTAK, [MONEY_UNIT, MONEY_UNIT, MONEY_UNIT, MONEY_UNIT, MONEY_UNIT, MONEY_UNIT], ['0,00'] * 6),
    ('0002.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait sosyal destek programlarının yürütülmesi', ['-', '-', '-', '25.010.974,00', '29.431.122,00', '34.665.674,00'], ['-', '-', '-', '0,00', '0,00', '0,00']),
    ('0003.Yerel Eşitlik Eylem Planının hayata geçirilmesi', ['-', '-', '-', '18.000.000,00', '20.000.000,00', '22.000.000,00'], ['-', '-', '-', '1.500.000,00', '1.750.000,00', '2.000.000,00']),
]

ECON_CATEGORIES = [
    ('01', 'Personel Giderleri'), ('02', 'Sosyal Güvenlik Kurumlarına Devlet Primi Giderleri'),
    ('03', 'Mal ve Hizmet Alım Giderleri'), ('04', 'Faiz Giderleri'), ('05', 'Cari Transferler'),
    ('06', 'Sermaye Giderleri'), ('07', 'Sermaye Transferleri'), ('08', 'Borç Verme'), ('09', 'Yedek Ödenekler'),
]
ECON_TOTALS = ['TOPLAM', 'BÜTÇE İÇİ TOPLAM KAYNAK', 'Diğer Bütçe Dışı Kaynak', 'BÜTÇE DIŞI TOPLAM KAYNAK', 'FAALİYET MALİYETİ TOPLAMI']

DIRECTORATES = [
    'Sağlık İşleri Müdürlüğü', 'Ruhsat ve Denetim Müdürlüğü', 'Zabıta Müdürlüğü', 'Veteriner İşleri Müdürlüğü',
    'Emlak ve İstimlak Müdürlüğü', 'Fen İşleri Müdürlüğü', 'İmar ve Şehircilik Müdürlüğü', 'Park ve Bahçeler Müdürlüğü',
    'Etüd Proje Müdürlüğü', 'Harita ve Planlama Müdürlüğü', 'Kentsel Dönüşüm Müdürlüğü',
    'Afet İşleri ve Risk Yönetimi Müdürlüğü', 'Temizlik İşleri Müdürlüğü', 'Çevre Koruma ve Kontrol Müdürlüğü',
    'Tarımsal Hizmetler Müdürlüğü', 'İklim Değişikliği ve Sıfır Atık Müdürlüğü', 'Kültür, Sanat ve Sosyal İşler Müdürlüğü',
    'Gençlik ve Spor Hizmetleri Müdürlüğü', 'Sosyal Hizmetler Müdürlüğü', 'Dış İlişkiler Müdürlüğü',
    'Basın, Yayın ve Halkla İlişkiler Müdürlüğü', 'Araştırma ve Geliştirme Müdürlüğü', 'Özel Kalem Müdürlüğü',
    'İnsan Kaynakları ve Eğitim Müdürlüğü', 'Bilgi İşlem Müdürlüğü', 'Rehberlik ve Teftiş Kurulu Müdürlüğü',
    'Hukuk İşleri Müdürlüğü', 'Strateji Geliştirme Müdürlüğü', 'Destek Hizmetleri Müdürlüğü', 'Mali Hizmetler Müdürlüğü',
    'Yazı İşleri Müdürlüğü', 'Gelirler Müdürlüğü', 'Makine İkmal Bakım ve Onarım Müdürlüğü',
]


def tr_money(value):
    s = f'{value:,.2f}'
    return s.replace(',', '_').replace('.', ',').replace('_', '.')


def directorate_budget():
    """Deterministic sample amounts; the largest row uses the maximum width."""
    import random
    rng = random.Random(2027)
    values = [rng.uniform(5_000_000, 900_000_000) for _ in DIRECTORATES]
    values[5] = 9_999_999_999.99
    total = sum(values)
    return [(d, tr_money(v), tr_money(v / total * 100)) for d, v in zip(DIRECTORATES, values)], tr_money(total)
