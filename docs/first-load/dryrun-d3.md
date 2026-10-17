# 2027 PP ilk yükleme kuru denemesi

Dosya: `pp2027_print_d3.idml` (taslak; nihai kitapla tekrar çalıştırılmalı).

SHA256: `999a43b2c07074191a1e47622c544b9a53813f23d3bb6518e63b29979ca384cb`

## Çalıştırma ve kapsam

```sh
# Yerel PostgreSQL 16+ test URL adresini CIVENSA_TEST_POSTGRES_URL olarak ayarlayın.
python scripts/first_load_dryrun.py tests/fixtures/first_load/source/pp2027_print_d3.idml --out docs/first-load/dryrun-d3.md
```

Yalnızca CIVENSA_TEST_POSTGRES_URL okunur; yerel host ve sorgu parametresi kontrol edilir. Her çalıştırma ayrı bir veritabanı oluşturur, alembic upgrade head çalıştırır ve sonunda siler. Test kullanıcısının CREATE DATABASE yetkisi olmalıdır. Canlı veritabanı kullanılmaz.

Tek kurum, Strateji kullanıcısı, doğrulanmış şablonlu 2027 dönemi ve name_map.json hedef adları (ayrıca kitapta bulunan yerleşik ad eşlemeleri) ekilir. Kartların faaliyet üyeliği tablolarından resmî faaliyet kataloğu, tüm sorumlu müdürlükler ve yerel faaliyet bağlantıları ortak servislerle, denetim kaydı tutularak yüklenir. Kaynak tutarları düzeltilmez. Kitapta program/alt program kodu olmadığından bu kodlar boş kalır; kod uydurulmaz.

name_map.json içinde teyit bekleyen kitap adları: Gençlik ve Spor Hizmetleri Müdürlüğü; Sosyal Hizmetler Müdürlüğü; Basın Yayın ve Halkla İlişkiler Müdürlüğü; Harita ve Planlama Müdürlüğü; Araştırma ve Geliştirme Müdürlüğü.

## Genel sonuç

- Kitap müdürlükleri: 33; ekili/uygulama sonrası müdürlükler: 33.
- Kartlar: 64; göstergeler: 264; faaliyetler: 288; ekonomik tablolar: 34.
- import_validation_errors: 0; source_conflicts: 0; çözümlenemeyen ad: 0.
- Uygulama: başarılı; gönderime hazır: 5/33.
- Doğrulama: 553 hata, 22 uyarı.
- Ad taraması: 0 bulgu; çapraz toplam farkı: 63; eksik/belirsiz karşılaştırma: 7.

| 2027 bütçesi | Faaliyetler | Ekonomik kaynak toplamları |
| --- | ---: | ---: |
| Bütçe içi | Bilinmiyor (bilinen: 7.314.587.310,00; eksik: 2) | Bilinmiyor (bilinen: 7.999.475.000,00; eksik: 1) |
| Bütçe dışı | Bilinmiyor (bilinen: 0,00; eksik: 3) | Bilinmiyor (bilinen: 0,00; eksik: 1) |
| Toplam | 7.313.587.310,00 | Bilinmiyor (bilinen: 7.999.475.000,00; eksik: 1) |

## IDML dönüşümü ve kaynak üyelikleri

{"card": 64, "membership": 64, "cost": 33, "economic": 34}.

Eşlenmeyen kitap adları (aynen korunur; yerleşik içe aktarıcı eşlemesi ayrıca uygulanır): Gelirler Müdürlüğü (Bütçe İşletme Şefliği).

Basılı sayfaya bağlı olmayan tablolar (yükleme dışında): [{"id": "ubbb4ibbe3", "type": "cost"}, {"id": "ubbb4ibbcb", "type": "economic"}, {"id": "ubb2aibb60", "type": "card"}, {"id": "ubb2aibb40", "type": "membership"}].

Sayfa numaraları IDML metin çerçevesinin ilk basılı sayfasından alınır; çok sayfalı hikâyede başlangıç sayfasını gösterir. Üyelik kodu müdürlük içinde tekil eşleştirilir; maliyet ve üyelik başlıklarının yazım farkları değiştirilmez. Aynı faaliyet/alt program birden fazla müdürlükte varsa tek katalog kaydına bütün sorumlu müdürlükler eklenir.


## Kaynakta kalan üyelik sorunları

- Tablo 136, satır 8: Özel Kalem Müdürlüğü / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. (kitap s. 198)

## Korunan bilinen kitap sorunları ve CIV-041 sınırı

- s.128 Park ve Bahçeler 0007: kaynak toplamı 44.333.709,00 TL; Bütçe İçi 45.333.709,00 TL. Tutarlar değiştirilmedi; kaynak toplamı ve fark doğrulamada korunur.
- s.243: eski biçimli ekonomik tablo; 2025–2026 sütunları ve “2027 Tahmin”, 2027 Bütçe sütunu yok. Kaynak düzeltilmedi ve tablonun içeriği atılmadı.
- Bu rapor CIV-042 dalındaki ekonomik ayrıştırıcıyla üretilir. CIV-041 ayrı PR’dır; ekonomik ayrıştırma bu dalda değiştirilmedi. Mevcut ayrıştırıcı s.243 tablosunu son müdürlüğe (Makine İkmal) bağlıyor ve kod/ad düzenindeki kategorileri okuyamıyor. Bu müdürlükteki ilgili ekonomik hatalar gerçek kaynak eksikliği olarak yorumlanmamalı; CIV-041 sonrası rapor yeniden çalıştırılmalıdır. Diğer hatalar ve ham kaynaklar aşağıda korunur.


## Müdürlük bazında ayrıştırma

| Müdürlük | Kart | Gösterge | Gösterge değerleri / durum | Faaliyet | Faaliyet maliyet değerleri / durum | Personel değerleri / durum | Ekonomik tablo | Ekonomik değerler / durum |
| --- | ---: | ---: | --- | ---: | --- | --- | ---: | --- |
| Sağlık İşleri Müdürlüğü | 4 | 11 | verified: 66 | 10 | not_applicable: 90; verified: 90 | not_applicable: 3; verified: 3 | 1 | needs_review: 10; verified: 40 |
| Ruhsat ve Denetim Müdürlüğü | 1 | 5 | verified: 30 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | needs_review: 12; verified: 18 |
| Zabıta Müdürlüğü | 2 | 9 | verified: 54 | 9 | not_applicable: 81; verified: 81 | not_applicable: 3; verified: 3 | 1 | needs_review: 8; verified: 32 |
| Veteriner İşleri Müdürlüğü | 1 | 5 | verified: 30 | 6 | missing: 3; not_applicable: 54; verified: 51 | not_applicable: 3; verified: 3 | 1 | needs_review: 20; verified: 30 |
| Emlak İstimlak Müdürlüğü | 2 | 7 | verified: 42 | 11 | missing: 3; not_applicable: 99; verified: 96 | not_applicable: 3; verified: 3 | 1 | needs_review: 10; verified: 40 |
| Fen İşleri Müdürlüğü | 3 | 15 | verified: 90 | 9 | not_applicable: 81; verified: 81 | not_applicable: 3; verified: 3 | 1 | needs_review: 50 |
| İmar ve Şehircilik Müdürlüğü | 2 | 7 | verified: 42 | 13 | not_applicable: 117; verified: 117 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Park ve Bahçeler Müdürlüğü | 2 | 7 | needs_review: 15; verified: 27 | 13 | not_applicable: 117; verified: 117 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Etüd Proje Müdürlüğü | 2 | 6 | verified: 36 | 12 | missing: 1; not_applicable: 108; verified: 107 | not_applicable: 3; verified: 3 | 1 | verified: 30 |
| Plan Proje Müdürlüğü | 1 | 5 | needs_review: 1; verified: 29 | 1 | not_applicable: 9; verified: 9 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Kentsel Dönüşüm Müdürlüğü | 1 | 5 | verified: 30 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 2 | 10 | verified: 60 | 16 | missing: 3; not_applicable: 144; verified: 141 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Temizlik İşleri Müdürlüğü | 1 | 4 | verified: 24 | 8 | not_applicable: 72; verified: 72 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Çevre Koruma ve Kontrol Müdürlüğü | 1 | 3 | verified: 18 | 3 | not_applicable: 27; verified: 27 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Tarımsal Hizmetler Müdürlüğü | 2 | 9 | needs_review: 6; verified: 48 | 11 | missing: 6; not_applicable: 99; verified: 93 | not_applicable: 3; verified: 3 | 1 | needs_review: 8; verified: 32 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | 1 | 3 | verified: 18 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | verified: 30 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 5 | 24 | verified: 144 | 17 | missing: 47; not_applicable: 108; verified: 151 | not_applicable: 3; verified: 3 | 1 | verified: 30 |
| Gençlik ve Spor İşleri Müdürlüğü | 2 | 10 | verified: 60 | 10 | not_applicable: 90; verified: 90 | not_applicable: 3; verified: 3 | 1 | needs_review: 16; verified: 24 |
| Sosyal Destek Müdürlüğü | 4 | 20 | needs_review: 5; verified: 115 | 19 | not_applicable: 171; verified: 171 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Dış İlişkiler Müdürlüğü | 1 | 3 | verified: 18 | 10 | missing: 3; not_applicable: 87; verified: 90 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Halkla İlişkiler Müdürlüğü | 4 | 16 | verified: 96 | 10 | not_applicable: 90; verified: 90 | not_applicable: 3; verified: 3 | 1 | needs_review: 8; verified: 32 |
| Araştırma ve Geliştirme Müdürlüğü | 1 | 4 | verified: 24 | 8 | not_applicable: 72; verified: 72 | not_applicable: 3; verified: 3 | 1 | needs_review: 6; verified: 24 |
| Özel Kalem Müdürlüğü | 1 | 5 | verified: 30 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 2 | 6 | verified: 36 | 10 | not_applicable: 90; verified: 90 | not_applicable: 3; verified: 3 | 1 | needs_review: 40 |
| Bilgi İşlem Müdürlüğü | 1 | 5 | verified: 30 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 1 | 5 | verified: 30 | 3 | not_applicable: 27; verified: 27 | not_applicable: 3; verified: 3 | 1 | needs_review: 8; verified: 32 |
| Hukuk İşleri Müdürlüğü | 1 | 4 | verified: 24 | 3 | not_applicable: 27; verified: 27 | not_applicable: 3; verified: 3 | 1 | verified: 30 |
| Strateji Geliştirme Müdürlüğü | 1 | 5 | verified: 30 | 8 | not_applicable: 72; verified: 72 | not_applicable: 3; verified: 3 | 1 | verified: 30 |
| Destek Hizmetleri Müdürlüğü | 2 | 9 | verified: 54 | 7 | missing: 3; not_applicable: 60; verified: 63 | not_applicable: 3; verified: 3 | 1 | verified: 40 |
| Mali Hizmetler Müdürlüğü | 1 | 2 | verified: 12 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 1 | needs_review: 18; verified: 72 |
| Yazı İşleri Müdürlüğü | 4 | 20 | verified: 120 | 11 | missing: 18; not_applicable: 81; verified: 99 | not_applicable: 3; verified: 3 | 1 | needs_review: 50 |
| Gelirler Müdürlüğü | 4 | 10 | verified: 60 | 15 | missing: 3; not_applicable: 132; verified: 135 | not_applicable: 3; verified: 3 | 1 | needs_review: 16; verified: 24 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 1 | 5 | verified: 30 | 5 | not_applicable: 45; verified: 45 | not_applicable: 3; verified: 3 | 2 | needs_review: 36; verified: 40 |

Uygulanan kayıtlar: 33 müdürlük, 64 kart, 264 gösterge, 288 faaliyet, 1336 ekonomik değer, 198 ortak personel değeri. Alt programa bağlanamayan faaliyet: 0.

Katalog: 289 resmî faaliyet, 289 sorumluluk, 288 yerel faaliyet bağlantısı.

## İçe aktarma hataları ve kaynak çelişkileri

### import_validation_errors (0)

Yok.

### source_conflicts (0)

Yok.

## Sistem adına çözümlenemeyen kitap müdürlükleri

Yok; tüm kitap müdürlükleri ekili sistem adlarıyla eşleşti.

## 2027 bütçesi çapraz tablo kontrolü

Faaliyet maliyet hücrelerinin toplamı, ekonomik tablodaki açık Bütçe İçi / Bütçe Dışı / Faaliyet Maliyeti Toplamı kaynak satırlarıyla doğrudan karşılaştırılır. Ekonomik toplamlar ortak personel/SGK giderlerini de içerebilir; bu nedenle FARK tek başına içe aktarıcı hatası değildir. Bu karşılaştırma personeli düşmez, tutarları değiştirmez. Gönderime hazırlık için mevcut validate_department kuralları ayrıca uygulanır. Boş/belirsiz hücreler sıfır sayılmaz.

| Müdürlük | Finansman | Faaliyet toplamı | Ekonomik kaynak toplamı | Sonuç |
| --- | --- | ---: | ---: | --- |
| Sağlık İşleri Müdürlüğü | Bütçe içi | 20.587.500,00 | 34.633.500,00 | FARK |
| Sağlık İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Sağlık İşleri Müdürlüğü | Toplam | 20.587.500,00 | 34.633.500,00 | FARK |
| Ruhsat ve Denetim Müdürlüğü | Bütçe içi | 2.343.147,00 | 14.548.599,00 | FARK |
| Ruhsat ve Denetim Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Ruhsat ve Denetim Müdürlüğü | Toplam | 2.343.147,00 | 14.548.599,00 | FARK |
| Zabıta Müdürlüğü | Bütçe içi | 8.000.000,00 | 117.786.161,00 | FARK |
| Zabıta Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Zabıta Müdürlüğü | Toplam | 8.000.000,00 | 117.786.161,00 | FARK |
| Veteriner İşleri Müdürlüğü | Bütçe içi | 72.675.000,00 | 78.383.750,00 | FARK |
| Veteriner İşleri Müdürlüğü | Bütçe dışı | Bilinmiyor (bilinen: 0,00; eksik: 1) | 0,00 | Eksik/belirsiz |
| Veteriner İşleri Müdürlüğü | Toplam | 72.675.000,00 | 78.383.750,00 | FARK |
| Emlak İstimlak Müdürlüğü | Bütçe içi | 250.534.658,00 | 264.794.573,00 | FARK |
| Emlak İstimlak Müdürlüğü | Bütçe dışı | Bilinmiyor (bilinen: 0,00; eksik: 1) | 0,00 | Eksik/belirsiz |
| Emlak İstimlak Müdürlüğü | Toplam | 250.534.658,00 | 264.794.573,00 | FARK |
| Fen İşleri Müdürlüğü | Bütçe içi | 1.189.138.909,00 | 1.236.438.909,00 | FARK |
| Fen İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Fen İşleri Müdürlüğü | Toplam | 1.189.138.909,00 | 1.236.438.909,00 | FARK |
| İmar ve Şehircilik Müdürlüğü | Bütçe içi | 2.400.000,00 | 55.357.116,00 | FARK |
| İmar ve Şehircilik Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| İmar ve Şehircilik Müdürlüğü | Toplam | 2.400.000,00 | 55.357.116,00 | FARK |
| Park ve Bahçeler Müdürlüğü | Bütçe içi | 543.389.649,00 | 551.300.000,00 | FARK |
| Park ve Bahçeler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Park ve Bahçeler Müdürlüğü | Toplam | 542.389.649,00 | 551.300.000,00 | FARK |
| Etüd Proje Müdürlüğü | Bütçe içi | 2.500.000,00 | 11.898.000,00 | FARK |
| Etüd Proje Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Etüd Proje Müdürlüğü | Toplam | 2.500.000,00 | 11.898.000,00 | FARK |
| Plan Proje Müdürlüğü | Bütçe içi | 4.134.625,00 | 32.917.972,00 | FARK |
| Plan Proje Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Plan Proje Müdürlüğü | Toplam | 4.134.625,00 | 32.917.972,00 | FARK |
| Kentsel Dönüşüm Müdürlüğü | Bütçe içi | 5.000.000,00 | 17.655.784,00 | FARK |
| Kentsel Dönüşüm Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Kentsel Dönüşüm Müdürlüğü | Toplam | 5.000.000,00 | 17.655.784,00 | FARK |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Bütçe içi | 20.269.229,00 | 30.704.229,00 | FARK |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Bütçe dışı | Bilinmiyor (bilinen: 0,00; eksik: 1) | 0,00 | Eksik/belirsiz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | Toplam | 20.269.229,00 | 30.704.229,00 | FARK |
| Temizlik İşleri Müdürlüğü | Bütçe içi | 836.500.000,00 | 852.338.000,00 | FARK |
| Temizlik İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Temizlik İşleri Müdürlüğü | Toplam | 836.500.000,00 | 852.338.000,00 | FARK |
| Çevre Koruma ve Kontrol Müdürlüğü | Bütçe içi | 1.807.912,00 | 11.914.412,00 | FARK |
| Çevre Koruma ve Kontrol Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Çevre Koruma ve Kontrol Müdürlüğü | Toplam | 1.807.912,00 | 11.914.412,00 | FARK |
| Tarımsal Hizmetler Müdürlüğü | Bütçe içi | Bilinmiyor (bilinen: 9.171.747,00; eksik: 2) | 15.287.207,00 | Eksik/belirsiz |
| Tarımsal Hizmetler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Tarımsal Hizmetler Müdürlüğü | Toplam | 9.171.747,00 | 15.287.207,00 | FARK |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Bütçe içi | 590.000,00 | 2.251.000,00 | FARK |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | Toplam | 590.000,00 | 2.251.000,00 | FARK |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Bütçe içi | 80.000.000,00 | 95.133.171,00 | FARK |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | Toplam | 80.000.000,00 | 95.133.171,00 | FARK |
| Gençlik ve Spor İşleri Müdürlüğü | Bütçe içi | 54.270.630,00 | 61.199.630,00 | FARK |
| Gençlik ve Spor İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Gençlik ve Spor İşleri Müdürlüğü | Toplam | 54.270.630,00 | 61.199.630,00 | FARK |
| Sosyal Destek Müdürlüğü | Bütçe içi | 61.510.974,00 | 72.380.474,00 | FARK |
| Sosyal Destek Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Sosyal Destek Müdürlüğü | Toplam | 61.510.974,00 | 72.380.474,00 | FARK |
| Dış İlişkiler Müdürlüğü | Bütçe içi | 4.039.548,00 | 6.514.548,00 | FARK |
| Dış İlişkiler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Dış İlişkiler Müdürlüğü | Toplam | 4.039.548,00 | 6.514.548,00 | FARK |
| Halkla İlişkiler Müdürlüğü | Bütçe içi | 38.015.739,00 | 65.868.202,00 | FARK |
| Halkla İlişkiler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Halkla İlişkiler Müdürlüğü | Toplam | 38.015.739,00 | 65.868.202,00 | FARK |
| Araştırma ve Geliştirme Müdürlüğü | Bütçe içi | 3.400.000,00 | 5.495.000,00 | FARK |
| Araştırma ve Geliştirme Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Araştırma ve Geliştirme Müdürlüğü | Toplam | 3.400.000,00 | 5.495.000,00 | FARK |
| Özel Kalem Müdürlüğü | Bütçe içi | 23.750.000,00 | 57.800.000,00 | FARK |
| Özel Kalem Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Özel Kalem Müdürlüğü | Toplam | 23.750.000,00 | 57.800.000,00 | FARK |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Bütçe içi | 10.000.000,00 | 31.406.000,00 | FARK |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| İnsan Kaynakları ve Eğitim Müdürlüğü | Toplam | 10.000.000,00 | 31.406.000,00 | FARK |
| Bilgi İşlem Müdürlüğü | Bütçe içi | 267.575.845,00 | 283.812.848,00 | FARK |
| Bilgi İşlem Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Bilgi İşlem Müdürlüğü | Toplam | 267.575.845,00 | 283.812.848,00 | FARK |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Bütçe içi | 149.343,00 | 1.799.343,00 | FARK |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | Toplam | 149.343,00 | 1.799.343,00 | FARK |
| Hukuk İşleri Müdürlüğü | Bütçe içi | 32.925.000,00 | 49.482.284,00 | FARK |
| Hukuk İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Hukuk İşleri Müdürlüğü | Toplam | 32.925.000,00 | 49.482.284,00 | FARK |
| Strateji Geliştirme Müdürlüğü | Bütçe içi | 2.267.350,00 | 5.863.600,00 | FARK |
| Strateji Geliştirme Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Strateji Geliştirme Müdürlüğü | Toplam | 2.267.350,00 | 5.863.600,00 | FARK |
| Destek Hizmetleri Müdürlüğü | Bütçe içi | 2.608.868.429,00 | 2.634.147.337,00 | FARK |
| Destek Hizmetleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Destek Hizmetleri Müdürlüğü | Toplam | 2.608.868.429,00 | 2.634.147.337,00 | FARK |
| Mali Hizmetler Müdürlüğü | Bütçe içi | 864.524.835,00 | 888.224.210,00 | FARK |
| Mali Hizmetler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Mali Hizmetler Müdürlüğü | Toplam | 864.524.835,00 | 888.224.210,00 | FARK |
| Yazı İşleri Müdürlüğü | Bütçe içi | 16.330.730,00 | 41.026.130,00 | FARK |
| Yazı İşleri Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Yazı İşleri Müdürlüğü | Toplam | 16.330.730,00 | 41.026.130,00 | FARK |
| Gelirler Müdürlüğü | Bütçe içi | 83.400.000,00 | 162.322.500,00 | FARK |
| Gelirler Müdürlüğü | Bütçe dışı | 0,00 | 0,00 | Eşit |
| Gelirler Müdürlüğü | Toplam | 83.400.000,00 | 162.322.500,00 | FARK |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Bütçe içi | 194.516.511,00 | Bilinmiyor (bilinen: 208.790.511,00; eksik: 1) | Eksik/belirsiz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Bütçe dışı | 0,00 | Bilinmiyor (bilinen: 0,00; eksik: 1) | Eksik/belirsiz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | Toplam | 194.516.511,00 | Bilinmiyor (bilinen: 208.790.511,00; eksik: 1) | Eksik/belirsiz |

## Ad düzeyinde tarama

Tarama ayrıştırılmış kaynak kayıtlarını inceler; ayrıştırıcının atladığı boş satırları yeni kayıt saymaz. Kod tekrarı müdürlük içinde taranır, kayıtlar birleştirilmez.

### Tablo başlığı adlı gösterge (0)

Yok.

### Yıl biçimli gösterge (0)

Yok.

### Boş gösterge adı (0)

Yok.

### Boş faaliyet adı (0)

Yok.

### Tekrarlanan faaliyet kodu (0)

Yok.

## Uygulama sonrası gönderime hazırlık

Hazır = paket uygulandı ve validate_department hata listesi boş. Uyarılar engelleyici değildir. Aşağıdaki hata ve uyarı metinleri doğrulayıcıdan aynen alınmıştır.

### Afet İşleri ve Risk Yönetimi Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 141, 143, 144.

Hatalar (12):

- 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 144)
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 144)
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 144)
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin finansman bilgisi eksik. (kitap s. 144)
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin finansman bilgisi eksik. (kitap s. 144)
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe finansman bilgisi eksik. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 144)

Uyarılar (0):

Yok.

### Araştırma ve Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 194, 195.

Hatalar (6):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 195)

Uyarılar (4):

- SH45/PG01, Ulusal ve uluslararası hibe/fon programlarına yapılan proje başvuru sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG02, Kurulan ulusal ve uluslararası iş birliğine yönelik protokol, iş birliği ve proje ortaklığı sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG03, Belediye hizmetlerine yönelik tamamlanan iş analizi/ süreç analizi raporu sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG04, Veri temeli çalışmalar kapsamında ilgili birimlerle yapılan koordinasyon/toplantı sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Bilgi İşlem Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 205, 207.

Hatalar (6):

- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 207)
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 207)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 207)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 207)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 207)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 207)

Uyarılar (0):

Yok.

### Çevre Koruma ve Kontrol Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 152, 153.

Hatalar (6):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 153)

Uyarılar (0):

Yok.

### Destek Hizmetleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 216, 217, 218.

Hatalar (3):

- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 218)
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 218)
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Bütçe finansman bilgisi eksik. (kitap s. 218)

Uyarılar (0):

Yok.

### Dış İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 184, 186.

Hatalar (9):

- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 186)
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 186)
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Bütçe finansman bilgisi eksik. (kitap s. 186)
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 186)
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 186)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 186)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 186)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 186)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 186)

Uyarılar (0):

Yok.

### Emlak İstimlak Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 110, 111, 112.

Hatalar (16):

- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 112)
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 112)
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 112)
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin finansman bilgisi eksik. (kitap s. 112)
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin finansman bilgisi eksik. (kitap s. 112)
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe finansman bilgisi eksik. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 112)

Uyarılar (0):

Yok.

### Etüd Proje Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 131, 132, 133.

Hatalar (1):

- 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet): 2028 Tahmin finansman bilgisi eksik. (kitap s. 133)

Uyarılar (0):

Yok.

### Fen İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 115, 116, 117, 118.

Hatalar (54):

- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2029 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 118)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 118)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 118)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 118)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 118)

Uyarılar (1):

- SH12.PG04.Yeni Açılan ve Genişletilen Yol Sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Gelirler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 229, 231, 232, 233, 234.

Hatalar (25):

- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 234)
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 234)
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 234)
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 234)
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 234)
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 234)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 234)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 234)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 234)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 234)

Uyarılar (1):

- Kadın kooperatifleri sayısının toplam tedarikçiye oranı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Gençlik ve Spor İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 170, 172, 173.

Hatalar (20):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 173)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 173)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 173)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 173)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 173)

Uyarılar (0):

Yok.

### Halkla İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 188, 189, 190, 191, 192.

Hatalar (11):

- 0010.Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri: faaliyet açıklaması eksik. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 192)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 192)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 192)

Uyarılar (0):

Yok.

### Hukuk İşleri Müdürlüğü

Gönderime hazır: **Evet**.

Kitap sayfaları: 211, 212.

Hatalar (0):

Yok.

Uyarılar (0):

Yok.

### İklim Değişikliği ve Sıfır Atık Müdürlüğü

Gönderime hazır: **Evet**.

Kitap sayfaları: 158, 159.

Hatalar (0):

Yok.

Uyarılar (0):

Yok.

### İmar ve Şehircilik Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 120, 121, 122.

Hatalar (6):

- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 122)

Uyarılar (0):

Yok.

### İnsan Kaynakları ve Eğitim Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 201, 202, 203.

Hatalar (42):

- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 203)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 203)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 203)

Uyarılar (0):

Yok.

### Kentsel Dönüşüm Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 138, 139.

Hatalar (6):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 139)

Uyarılar (0):

Yok.

### Kültür, Sanat ve Sosyal İşler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 162, 163, 164, 165, 166, 167.

Hatalar (55):

- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 toplamı bütçe içi + dışı ile eşit değil. (kitap s. 167)
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 toplamı bütçe içi + dışı ile eşit değil. (kitap s. 167)
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin finansman bilgisi eksik. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin finansman bilgisi eksik. (kitap s. 167)
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 toplamı bütçe içi + dışı ile eşit değil. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 toplamı bütçe içi + dışı ile eşit değil. (kitap s. 167)
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: faaliyet açıklaması eksik. (kitap s. 167)
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 167)
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 167)
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 167)

Uyarılar (0):

Yok.

### Makine İkmal Bakım ve Onarım Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 238, 239, 243.

Hatalar (64):

- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2025 Yıl Sonu Tahmini / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- Ekonomik tablo boyut/tutar bilgisi geçersiz. (kitap s. 238, 239, 243)
- 2027 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 239, 243)
- 2027: Program Grubu Belirlenmeli / Bütçe İçi: 9 ekonomik gider hücresi eksik (yoksa 0 girin). (kitap s. 239, 243)
- 2027: Program Grubu Belirlenmeli / Bütçe Dışı: 9 ekonomik gider hücresi eksik (yoksa 0 girin). (kitap s. 239, 243)
- 2029: Program Grubu Belirlenmeli / Bütçe İçi: 9 ekonomik gider hücresi eksik (yoksa 0 girin). (kitap s. 239, 243)
- 2029: Program Grubu Belirlenmeli / Bütçe Dışı: 9 ekonomik gider hücresi eksik (yoksa 0 girin). (kitap s. 239, 243)

Uyarılar (0):

Yok.

### Mali Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 220, 221.

Hatalar (20):

- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Faiz Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Faiz Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sermaye Transferleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Sermaye Transferleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Borç Verme / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Borç Verme / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Yedek Ödenekler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2027 Bütçe / Yedek Ödenekler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 221)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 221)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 221)

Uyarılar (0):

Yok.

### Özel Kalem Müdürlüğü

Gönderime hazır: **Evet**.

Kitap sayfaları: 198, 199.

Hatalar (0):

Yok.

Ek kaynak sorunu (validate_department dışında; maliyet kaydı üretilmedi):

- Tablo 136, satır 8: Özel Kalem Müdürlüğü / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin.

Uyarılar (0):

Yok.

### Park ve Bahçeler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 125, 127, 128.

Hatalar (20):

- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (17,840). (kitap s. 125)
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Planlanan: kaynak değeri doğrulanmalı (50,000). (kitap s. 125)
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (50,000). (kitap s. 125)
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2027 Hedef: kaynak değeri doğrulanmalı (50,000). (kitap s. 125)
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2028 Tahmin: kaynak değeri doğrulanmalı (60,000). (kitap s. 125)
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2029 Tahmin: kaynak değeri doğrulanmalı (60,000). (kitap s. 125)
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (132,915). (kitap s. 125)
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Planlanan: kaynak değeri doğrulanmalı (250,000). (kitap s. 125)
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (250,000). (kitap s. 125)
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2027 Hedef: kaynak değeri doğrulanmalı (200,000). (kitap s. 125)
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2029 Tahmin: kaynak değeri doğrulanmalı (300,000). (kitap s. 125)
- SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (650,000). (kitap s. 125)
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 128)
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 toplamı bütçe içi + dışı ile eşit değil. (kitap s. 128)
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 128)
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 128)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 128)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 128)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 128)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 128)

Uyarılar (3):

- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Plan Proje Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 135, 136.

Hatalar (6):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 136)

Uyarılar (1):

- SH20.PG05. Vatandaşların memnuniyet: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Rehberlik ve Teftiş Kurulu Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 209, 210.

Hatalar (10):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 210)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 210)
- 2029: bütçe dışı faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 210)

Uyarılar (0):

Yok.

### Ruhsat ve Denetim Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 100, 101.

Hatalar (12):

- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 101)

Uyarılar (0):

Yok.

### Sağlık İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 94, 95, 96, 97, 98.

Hatalar (12):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 98)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 98)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 98)

Uyarılar (1):

- SH03/PG01 Sunulan Hasta Nakil Hizmet Sayısı Sağlık Hizmetlerinden yararlanan vatandaşların memnuniyet oranı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Sosyal Destek Müdürlüğü

Gönderime hazır: **Evet**.

Kitap sayfaları: 175, 176, 177, 178, 179.

Hatalar (0):

Yok.

Uyarılar (5):

- SH39/PG01. Sosyal incelemesi yapılan çocuk sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG02. Rehberlik ve Danışmanlık desteği verilen çocuk sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG03. Dezavantajlı Çocukların güçlendirilmesine yönelik eğitim ve farkındalık çalışma sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG04. Ailelere yönelik rehberlik çalışması: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG05. Gerçekleştirilen görüşmelerden duyulan memnuniyet oranı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Strateji Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 213, 214.

Hatalar (2):

- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 214)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 214)

Uyarılar (0):

Yok.

### Tarımsal Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 154, 155, 156.

Hatalar (20):

- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin finansman bilgisi eksik. (kitap s. 156)
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin finansman bilgisi eksik. (kitap s. 156)
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe finansman bilgisi eksik. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin finansman bilgisi eksik. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin finansman bilgisi eksik. (kitap s. 156)
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe finansman bilgisi eksik. (kitap s. 156)
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 156)

Uyarılar (6):

- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Temizlik İşleri Müdürlüğü

Gönderime hazır: **Evet**.

Kitap sayfaları: 148, 150.

Hatalar (0):

Yok.

Uyarılar (0):

Yok.

### Veteriner İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 106, 107.

Hatalar (26):

- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı. (kitap s. 107)
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 107)
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı. (kitap s. 107)
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin finansman bilgisi eksik. (kitap s. 107)
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin finansman bilgisi eksik. (kitap s. 107)
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe finansman bilgisi eksik. (kitap s. 107)
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 107)

Uyarılar (0):

Yok.

### Yazı İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 223, 224, 225, 226, 227.

Hatalar (75):

- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Haziran Sonu Harcama finansman bilgisi eksik. (kitap s. 227)
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik. (kitap s. 227)
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Bütçe finansman bilgisi eksik. (kitap s. 227)
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2028 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2029 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 227)
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 227)
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 227)
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 227)
- 2028: ekonomik personel/SGK satırları ortak tablodan farklı. (kitap s. 227)
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 227)
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor. (kitap s. 227)
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. (kitap s. 227)

Uyarılar (0):

Yok.

### Zabıta Müdürlüğü

Gönderime hazır: **Hayır**.

Kitap sayfaları: 102, 103, 104.

Hatalar (8):

- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı. (kitap s. 104)

Uyarılar (0):

Yok.
