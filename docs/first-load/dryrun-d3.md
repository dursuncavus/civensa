# 2027 PP ilk yükleme kuru denemesi

Dosya: `pp2027_print_d3.docx` (taslak; nihai kitapla tekrar çalıştırılmalı).

SHA256: `3bc2f955151113e6570b7ea10743ea5c7cfd15473528e445baa7553648e81763`

## Çalıştırma ve kapsam

```sh
# Yerel PostgreSQL 16+ test URL adresini CIVENSA_TEST_POSTGRES_URL olarak ayarlayın.
python scripts/first_load_dryrun.py tests/fixtures/first_load/pp2027_print_d3.docx --out docs/first-load/dryrun-d3.md
```

Yalnızca CIVENSA_TEST_POSTGRES_URL okunur; yerel host ve sorgu parametresi kontrol edilir. Her çalıştırma ayrı bir veritabanı oluşturur, alembic upgrade head çalıştırır ve sonunda siler. Test kullanıcısının CREATE DATABASE yetkisi olmalıdır. Canlı veritabanı kullanılmaz.

Tek kurum, Strateji kullanıcısı, doğrulanmış şablonlu 2027 dönemi ve name_map.json hedef adları (ayrıca kitapta bulunan yerleşik ad eşlemeleri) ekilir. Resmî faaliyet kataloğu, sorumluluklar ve elle veri düzeltmesi ekilmez; katalog bağlantısı eksikleri doğrulama sonucuna dahildir.

name_map.json içinde teyit bekleyen kitap adları: Gençlik ve Spor Hizmetleri Müdürlüğü; Sosyal Hizmetler Müdürlüğü; Basın Yayın ve Halkla İlişkiler Müdürlüğü; Harita ve Planlama Müdürlüğü; Araştırma ve Geliştirme Müdürlüğü.

## Genel sonuç

- Kitap müdürlükleri: 33; ekili/uygulama sonrası müdürlükler: 33.
- Kartlar: 64; göstergeler: 264; faaliyetler: 288; ekonomik tablolar: 34.
- import_validation_errors: 0; source_conflicts: 0; çözümlenemeyen ad: 0.
- Uygulama: başarılı; gönderime hazır: 0/33.
- Doğrulama: 1044 hata, 22 uyarı.
- Ad taraması: 0 bulgu; çapraz toplam farkı: 63; eksik/belirsiz karşılaştırma: 7.

| 2027 bütçesi | Faaliyetler | Ekonomik kaynak toplamları |
| --- | ---: | ---: |
| Bütçe içi | Bilinmiyor (bilinen: 7.314.587.310,00; eksik: 2) | Bilinmiyor (bilinen: 7.999.475.000,00; eksik: 1) |
| Bütçe dışı | Bilinmiyor (bilinen: 0,00; eksik: 3) | Bilinmiyor (bilinen: 0,00; eksik: 1) |
| Toplam | 7.313.587.310,00 | Bilinmiyor (bilinen: 7.999.475.000,00; eksik: 1) |

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

Uygulanan kayıtlar: 33 müdürlük, 64 kart, 264 gösterge, 288 faaliyet, 1336 ekonomik değer, 198 ortak personel değeri. Alt programa bağlanamayan faaliyet: 143.

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

Hatalar (44):

- 0001.Afet Risk Değerlendirme Toplantıları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Afet Risk Değerlendirme Toplantıları: kart bağlantısı eksik.
- 0002.Risk Azaltma Çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Risk Azaltma Çalışmaları: kart bağlantısı eksik.
- 0003.Afet ve Acil Durum Eylem Planı Hazırlık Çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Afet ve Acil Durum Eylem Planı Hazırlık Çalışmaları: kart bağlantısı eksik.
- 0004.İlçe Genelinde Haberleşme Sisteminin Kurulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.İlçe Genelinde Haberleşme Sisteminin Kurulması: kart bağlantısı eksik.
- 0005.Kurumlar Arası İş Birliği ve Koordinasyonun Güçlendirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Kurumlar Arası İş Birliği ve Koordinasyonun Güçlendirilmesi: kart bağlantısı eksik.
- 0006.Kapsamlı afet risk azaltma ve yönetim platformu projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Kapsamlı afet risk azaltma ve yönetim platformu projesi: kart bağlantısı eksik.
- 0007.İlçe Geneli Afet Müdahale ve Hasar Tespit Çalışma Grubu için Sektörleme Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.İlçe Geneli Afet Müdahale ve Hasar Tespit Çalışma Grubu için Sektörleme Projesi: kart bağlantısı eksik.
- 0008.Acil Durum Eylem Planı Geliştirme Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Acil Durum Eylem Planı Geliştirme Projesi: kart bağlantısı eksik.
- 0009.Bilgi Paylaşımı ve İş Birliği Platformu Oluşturma Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Bilgi Paylaşımı ve İş Birliği Platformu Oluşturma Projesi: kart bağlantısı eksik.
- 0010.Kırılgan Gruplara (Çocuk, Yaşlı, Engelli, Kadın, Genç vb.) Sosyal Sorumluluk Kapsamında Afet Bilinci Eğitimi Verme Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Kırılgan Gruplara (Çocuk, Yaşlı, Engelli, Kadın, Genç vb.) Sosyal Sorumluluk Kapsamında Afet Bilinci Eğitimi Verme Projesi: kart bağlantısı eksik.
- 0011.Afet tatbikatları düzenleme ve tatbikatlara katılma.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Afet tatbikatları düzenleme ve tatbikatlara katılma.: kart bağlantısı eksik.
- 0012.Afet yönetimiyle ilgili çalışmaların bilgi ve becerilerini geliştirmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Afet yönetimiyle ilgili çalışmaların bilgi ve becerilerini geliştirmek.: kart bağlantısı eksik.
- 0013.Kent sakinlerini afetler hakkında bilgilendirmek, afet öncesi, sırası ve sonrasında yapılması gerekenler konusunda bilinçlendirme: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Kent sakinlerini afetler hakkında bilgilendirmek, afet öncesi, sırası ve sonrasında yapılması gerekenler konusunda bilinçlendirme: kart bağlantısı eksik.
- 0014.Kapsamlı Afet Bilinçlendirme Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0014.Kapsamlı Afet Bilinçlendirme Projesi: kart bağlantısı eksik.
- 0015.Kurum Personelinin Afet Eğitim Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0015.Kurum Personelinin Afet Eğitim Projesi: kart bağlantısı eksik.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2029 Tahmin finansman bilgisi eksik.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2027 Bütçe finansman bilgisi eksik.
- 0015.Kurum Personelinin Afet Eğitim Projesi: 2028 Tahmin finansman bilgisi eksik.
- 0016.Okullar Başta Olmak Üzeri Diğer Kamu, Kurum Kuruluş ve İşletmelerde Afet Eğitimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0016.Okullar Başta Olmak Üzeri Diğer Kamu, Kurum Kuruluş ve İşletmelerde Afet Eğitimi: kart bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Araştırma ve Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (14):

- 0001.Ulusal ve uluslararası hibe ve fon programların düzenli olarak izlenmesi, analiz edilmesi ve belediyenin stratejik öcelikleri doğrultusunda uygun çağrıların belirlenmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Belirlenen çağrılar için proje fikirlerinin geliştirilmesi ve proje başvurularının hazırlanması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Proje başvuru koordinasyonu, başvuruların ilgili fon sağlayıcılara sunulması ve sonuçlarının takibi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Proje yazımı bütçeleme ve uygulama süreçlerine ilişkin kurum iç bilgilendirme ve kapasite geliştirme çalışmaların yürütülmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Hibe alınan projelerin yürütülmesi ve gerekli raporlamaların yapılarak sonuçlandırılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Yerel hizmetlere yönelik iş analizi, süreç analizi ve fizibilite çalışmalarının gerçekleştirilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Kente ilişkin mevcut veri kaynaklarının tespit edilmesi, sınıflandırılması ve analiz edilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Belediye karar alma süreçlerini desteklemek amacıyla sürdürülebilir, güncel ve standartlara uygun veri setlerinin oluşturulması ve güncellenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (4):

- SH45/PG01, Ulusal ve uluslararası hibe/fon programlarına yapılan proje başvuru sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG02, Kurulan ulusal ve uluslararası iş birliğine yönelik protokol, iş birliği ve proje ortaklığı sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG03, Belediye hizmetlerine yönelik tamamlanan iş analizi/ süreç analizi raporu sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.
- SH45/PG04, Veri temeli çalışmalar kapsamında ilgili birimlerle yapılan koordinasyon/toplantı sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Bilgi İşlem Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (11):

- 0001.Bilişim teknolojileri altyapısının modernizasyonu, donanım ve çevre birimlerinin yönetimi, bakım-onarım süreçlerinin yürütülmesi ve bilgi sistemlerinin mevzuat ile ulusal/uluslararası standartlara uygunluğunun sağlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Akıllı Şehirler ve Dijital Dönüşüm Kapsamında; Büyük Veri Analizi, Şehir Veri Platformu, Açık Veri Portalı, Dijital İkiz, Coğrafi Bilgi Sistemleri ile İHA Destekli 2D–3D Dijital Harita Altlıklarının Oluşturulması ve Entegrasyonunun Sağlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Kamu hizmetlerinin dijitalleşmesine yönelik olarak e-belediyecilik, e-devlet entegrasyonu, e-imar, e-ruhsat, e-iskân ve benzeri dijital süreçlerin geliştirilmesi ve vatandaşların hizmetlere web ve mobil platformlar üzerinden erişiminin artırılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Vatandaş odaklı mobil uygulamaların geliştirilmesi kapsamında; kültürel ve turistik tanıtım uygulamaları, sosyal tesis ve hizmet kartı projeleri, etkileşimli ilçe uygulamaları, saha denetim ve kurumsal hizmet mobil uygulamalarının hayata geçirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Siber güvenliğin sağlanması amacıyla siber saldırılara karşı koruma sistemlerinin kurulması ve geliştirilmesi ile ücretsiz Wi-Fi altyapısı başta olmak üzere dijital hizmetlerin güvenli, sürdürülebilir ve kesintisiz şekilde sunulmasına yönelik çalışmaların yürütülmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Çevre Koruma ve Kontrol Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (9):

- 0001.5 Haziran Dünya Çevre günü, 8 Haziran Marmara Denizi günü ve çevre koruma haftası gibi özel gün ve hafta etkinlikleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Yerel yönetimler, sivil toplum kuruluşları, üniversiteler ve özel sektör ile iş birliği yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Gürültü ve çevre denetimlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Destek Hizmetleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (17):

- 0001.Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılanacaktır.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılanacaktır.: kart bağlantısı eksik.
- 0002.Belediye binaları, bağlı birimler ve belirli kamu kurumlarının elektrik, su, doğalgaz ve iletişim gibi temel ihtiyaçları kesintisiz olarak sağlanacaktır.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Belediye binaları, bağlı birimler ve belirli kamu kurumlarının elektrik, su, doğalgaz ve iletişim gibi temel ihtiyaçları kesintisiz olarak sağlanacaktır.: kart bağlantısı eksik.
- 0003.Belediye hizmet binalarının mobilya, temizlik, bakım, onarım ve güvenlik ihtiyaçları karşılanacaktır.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Belediye hizmet binalarının mobilya, temizlik, bakım, onarım ve güvenlik ihtiyaçları karşılanacaktır.: kart bağlantısı eksik.
- 0004.Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin edilecektir.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin edilecektir.: kart bağlantısı eksik.
- 0005.İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması.: kart bağlantısı eksik.
- 0006.Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek.: kart bağlantısı eksik.
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: kart bağlantısı eksik.
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Bütçe finansman bilgisi eksik.
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0007.İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek: 2026 Haziran Sonu Harcama finansman bilgisi eksik.

Uyarılar (0):

Yok.

### Dış İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (19):

- 0001.Kardeş şehir protokollerinin güncellenmesi ve yeni kardeş şehir ilişkilerinin kurulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Yurt içi ve yurt dışındaki diplomatik misyonlara yönelik resmi ziyaretler: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Bütçe finansman bilgisi eksik.
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0007.Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Kültürel diplomasi odaklı etkinlik ve organizasyonlar: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Kardeş şehirler arası iyi uygulama ve deneyim paylaşımı faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Uluslararası ziyaret ve temasların raporlanması ve kurumsallaştırılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Emlak İstimlak Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (38):

- 0001.2942 sayılı yasa kapsamında kamulaştırma işlemlerinin yapılması ve fiili el atmalardan kaynaklı mahkeme kararlarının uygulanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.2942 sayılı yasa kapsamında kamulaştırma işlemlerinin yapılması ve fiili el atmalardan kaynaklı mahkeme kararlarının uygulanması: kart bağlantısı eksik.
- 0002.2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takiplerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takiplerinin yapılması: kart bağlantısı eksik.
- 0003.2886 sayılı yasa kapsamında satış işlemleri ve 3194 sayılı yasanın 17. Maddesine göre taşınmaz hisse satışı işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.2886 sayılı yasa kapsamında satış işlemleri ve 3194 sayılı yasanın 17. Maddesine göre taşınmaz hisse satışı işlemlerinin yapılması: kart bağlantısı eksik.
- 0004.2886 sayılı yasa kapsamında tüm ecrimisil işlemlerinin yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.2886 sayılı yasa kapsamında tüm ecrimisil işlemlerinin yapılması.: kart bağlantısı eksik.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: kart bağlantısı eksik.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2029 Tahmin finansman bilgisi eksik.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2027 Bütçe finansman bilgisi eksik.
- 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması: 2028 Tahmin finansman bilgisi eksik.
- 0006.Semt pazarları tahsis işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Semt pazarları tahsis işlemlerinin yapılması: kart bağlantısı eksik.
- 0007.Mimarsinan Yat Limanı tüm işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Mimarsinan Yat Limanı tüm işlemlerinin yapılması: kart bağlantısı eksik.
- 0008.775 sayılı yasa doğrultusunda taşınmaz tahsis sahiplerinin ve 4706 sayılı yasa kapsamında hak sahiplerinin işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.775 sayılı yasa doğrultusunda taşınmaz tahsis sahiplerinin ve 4706 sayılı yasa kapsamında hak sahiplerinin işlemlerinin yapılması: kart bağlantısı eksik.
- 0009.Kurum taşınmazlarının envanterinin güncel tutulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Kurum taşınmazlarının envanterinin güncel tutulması: kart bağlantısı eksik.
- 0010.Şartlı ve/veya şartsız taşınmaz bağış işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Şartlı ve/veya şartsız taşınmaz bağış işlemlerinin yapılması: kart bağlantısı eksik.
- 0011.Diğer kamu kurum ve kuruluşları ile Belediyemize arasında irtifak ve intifa hakkı tesisi, tahsis, kiralama ve devir işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Diğer kamu kurum ve kuruluşları ile Belediyemize arasında irtifak ve intifa hakkı tesisi, tahsis, kiralama ve devir işlemlerinin yapılması: kart bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Etüd Proje Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (25):

- 0001.İlçe sınırları dâhilinde, ihtiyaçlar kapsamında, hangi projenin hangi mahalle ve bölgede gerçekleştirileceğine ilişkin fizibilite, etüt çalışmasının yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.İlçe sınırları dâhilinde, ihtiyaçlar kapsamında, hangi projenin hangi mahalle ve bölgede gerçekleştirileceğine ilişkin fizibilite, etüt çalışmasının yapılması: kart bağlantısı eksik.
- 0002.Eğitim Tesisi Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Eğitim Tesisi Projeleri: kart bağlantısı eksik.
- 0003.Sosyal Tesis Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Sosyal Tesis Projeleri: kart bağlantısı eksik.
- 0004.Kültür-Sanat Tesisi Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Kültür-Sanat Tesisi Projeleri: kart bağlantısı eksik.
- 0005.Spor Tesisi Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Spor Tesisi Projeleri: kart bağlantısı eksik.
- 0006.Dini Tesis Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Dini Tesis Projeleri: kart bağlantısı eksik.
- 0007.Ulaşım Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Ulaşım Projeleri: kart bağlantısı eksik.
- 0008.Sağlık Tesisi Projeleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Sağlık Tesisi Projeleri: kart bağlantısı eksik.
- 0009.Diğer Projeler: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Diğer Projeler: kart bağlantısı eksik.
- 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet): kart bağlantısı eksik.
- 0010.Tüm bölgede, Sigara İçme Alanı talep ve başvurularının değerlendirilerek sonuçlandırılması (102 adet): 2028 Tahmin finansman bilgisi eksik.
- 0011.Tüm bölgede, Tabela talep ve başvurularının değerlendirilerek sonuçlandırılması (3225 adet): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Tüm bölgede, Tabela talep ve başvurularının değerlendirilerek sonuçlandırılması (3225 adet): kart bağlantısı eksik.
- 0012.Belirlenecek bölgelerde, Kent Meydanı, Köy Meydanı Tören Alanı, Prestij Caddesi, Trafik Sokağı, Bisiklet Aksı Projesi, Tarihi Sokak Silueti Projesi gibi Kentsel Tasarım ilintili düzenlemelerden yapımı uygun görülenlerin projelerinin hazırlanması (13 Adet): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Belirlenecek bölgelerde, Kent Meydanı, Köy Meydanı Tören Alanı, Prestij Caddesi, Trafik Sokağı, Bisiklet Aksı Projesi, Tarihi Sokak Silueti Projesi gibi Kentsel Tasarım ilintili düzenlemelerden yapımı uygun görülenlerin projelerinin hazırlanması (13 Adet): kart bağlantısı eksik.

Uyarılar (0):

Yok.

### Fen İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (72):

- 0001.Yeni bina projelerinin uygulanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Yeni bina projelerinin uygulanması: kart bağlantısı eksik.
- 0002.Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması: kart bağlantısı eksik.
- 0003.Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması: kart bağlantısı eksik.
- 0004.Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması.: kart bağlantısı eksik.
- 0005.Yeni sokak yapılması ve mevcut sokakların sağlamlaştırma çalışmalarının yürütülmesi (Bisiklet yolu, yaya yolu, bakım onarım, yapım vb.): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Yeni sokak yapılması ve mevcut sokakların sağlamlaştırma çalışmalarının yürütülmesi (Bisiklet yolu, yaya yolu, bakım onarım, yapım vb.): kart bağlantısı eksik.
- 0006.Yeni altyapı yapılması ve mevcut altyapı sağlamlaştırma çalışmalarının yürütülmesi (yağmur suyu kanalı bakım, onarım, yapım vb.): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Yeni altyapı yapılması ve mevcut altyapı sağlamlaştırma çalışmalarının yürütülmesi (yağmur suyu kanalı bakım, onarım, yapım vb.): kart bağlantısı eksik.
- 0007.Yeni sokak yapılması ve mevcut sokakların sağlamlaştırma çalışmalarında aydınlatma projelerinin uygulanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Yeni sokak yapılması ve mevcut sokakların sağlamlaştırma çalışmalarında aydınlatma projelerinin uygulanması: kart bağlantısı eksik.
- 0008.Yeni aydınlatma projelerinin uygulanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Yeni aydınlatma projelerinin uygulanması: kart bağlantısı eksik.
- 0009.Sorumluluğumuzda bulunan binaların elektrik bakım onarım çalışmalarının yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Sorumluluğumuzda bulunan binaların elektrik bakım onarım çalışmalarının yapılması: kart bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (1):

- SH12.PG04.Yeni Açılan ve Genişletilen Yol Sayısı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Gelirler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (55):

- 0001.Sahada tespiti yapılan emlak, ÇTV, ilan reklam, pay, ceza, işgaliye harcı için tutulan yoklama fişlerinin iş yeri ve konut bazında tasnif edilmesi,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Sahada tespiti yapılan emlak, ÇTV, ilan reklam, pay, ceza, işgaliye harcı için tutulan yoklama fişlerinin iş yeri ve konut bazında tasnif edilmesi,: kart bağlantısı eksik.
- 0002.Diğer müdürlüklerden tarafından tarh edilen gelirlerin tahakkuk, tahsil ve takip işlemlerinin süresinde yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Diğer müdürlüklerden tarafından tarh edilen gelirlerin tahakkuk, tahsil ve takip işlemlerinin süresinde yapılması: kart bağlantısı eksik.
- 0003.Yerinde yapılan tespitlere istinaden düzenlenen yoklama fişleri doğrultusunda mükellef kayıtlarının oluşturulması, güncellenmesi yapılarak ikmalen veya idarece tarhiyat oluşturulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Yerinde yapılan tespitlere istinaden düzenlenen yoklama fişleri doğrultusunda mükellef kayıtlarının oluşturulması, güncellenmesi yapılarak ikmalen veya idarece tarhiyat oluşturulması: kart bağlantısı eksik.
- 0004.Belediyeye emlak, ilan reklam, eğlence vergileri ile işgaliye harcı, beyan sureti için başvuran vatandaşların iş ve işlemlerinin yürütülmesi,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Belediyeye emlak, ilan reklam, eğlence vergileri ile işgaliye harcı, beyan sureti için başvuran vatandaşların iş ve işlemlerinin yürütülmesi,: kart bağlantısı eksik.
- 0005.Vadesinde ödenmeyen alacaklar hakkında 6183 sayılı kanun kapsamında ödeme emri düzenlenmesi ve tebliğ edilerek takip sürecinin başlatılması, Ödeme emri tebliğ edilmesine rağmen ödenmeyen alacaklar hakkında haciz varakası düzenleyerek haciz işlemleri yapılması,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Vadesinde ödenmeyen alacaklar hakkında 6183 sayılı kanun kapsamında ödeme emri düzenlenmesi ve tebliğ edilerek takip sürecinin başlatılması, Ödeme emri tebliğ edilmesine rağmen ödenmeyen alacaklar hakkında haciz varakası düzenleyerek haciz işlemleri yapılması,: kart bağlantısı eksik.
- 0006.Tesis edilen iş ve işlemlerle ilgili ihtilaf konusu olan hususlarda şahşi müracaat ve dava konusu edilenlerle ilgili izah ve savunma yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Tesis edilen iş ve işlemlerle ilgili ihtilaf konusu olan hususlarda şahşi müracaat ve dava konusu edilenlerle ilgili izah ve savunma yapılması.: kart bağlantısı eksik.
- 0007.Çeşitli ödeme kanalları üzerinde tahsilat yapılması,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Çeşitli ödeme kanalları üzerinde tahsilat yapılması,: kart bağlantısı eksik.
- 0008.Tarh edilen verginin ilgili mükellefiyete ihbarının oluşturulması ve düzenlenen ihbarnamelerin tebliğinin yapılması,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Tarh edilen verginin ilgili mükellefiyete ihbarının oluşturulması ve düzenlenen ihbarnamelerin tebliğinin yapılması,: kart bağlantısı eksik.
- 0009.Tebliğ edilen ihbarnamelere ilişkin mükellefin indirim için müracaatlarının alınması; Tebliğinden itibaren süresi dolan ihbarnamelerin tahakkuka bağlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Tebliğ edilen ihbarnamelere ilişkin mükellefin indirim için müracaatlarının alınması; Tebliğinden itibaren süresi dolan ihbarnamelerin tahakkuka bağlanması: kart bağlantısı eksik.
- 0010.Büyükçekmece İktisadi İşletmeye bağlı şubeleri (sosyal tesis, düğün salonu, otopark vb.) işletmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Büyükçekmece İktisadi İşletmeye bağlı şubeleri (sosyal tesis, düğün salonu, otopark vb.) işletmek: kart bağlantısı eksik.
- 0011.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek: kart bağlantısı eksik.
- 0012.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek,: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek,: kart bağlantısı eksik.
- 0013.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek.: kart bağlantısı eksik.
- 0014.Belediyeye bağlı iktisadi işletme şubelerinin (sosyal tesis, otopark, düğün salonu vb.) işletmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0014.Belediyeye bağlı iktisadi işletme şubelerinin (sosyal tesis, otopark, düğün salonu vb.) işletmek.: kart bağlantısı eksik.
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: kart bağlantısı eksik.
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Bütçe finansman bilgisi eksik.
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (1):

- Kadın kooperatifleri sayısının toplam tedarikçiye oranı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Gençlik ve Spor İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (40):

- 0001.Amatör spor kulüplerine maddi ve manevi destek sağlamak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Amatör spor kulüplerine maddi ve manevi destek sağlamak: kart bağlantısı eksik.
- 0002.Spor tesislerini engellilerin de kullanabileceği şekilde düzenleme çalışmalarına devam etmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Spor tesislerini engellilerin de kullanabileceği şekilde düzenleme çalışmalarına devam etmek: kart bağlantısı eksik.
- 0003.Mevcut spor tesislerini gençlerin ihtiyaçlarına uygun hale getirmek için modernize etmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Mevcut spor tesislerini gençlerin ihtiyaçlarına uygun hale getirmek için modernize etmek: kart bağlantısı eksik.
- 0004.Spor etkinliklerine sanat etkinlikleri ekleyerek gençlerin farklı alanlara olan ilgilerini birleştirmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Spor etkinliklerine sanat etkinlikleri ekleyerek gençlerin farklı alanlara olan ilgilerini birleştirmek: kart bağlantısı eksik.
- 0005.Spor etkinliklerini çevre bilinci ile yaparak gençlerde çevreye duyarlılık oluşturma konusunda çalışmalar yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Spor etkinliklerini çevre bilinci ile yaparak gençlerde çevreye duyarlılık oluşturma konusunda çalışmalar yapmak: kart bağlantısı eksik.
- 0006.Yenilikçi ve çeşitli spor branşları açmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Yenilikçi ve çeşitli spor branşları açmak: kart bağlantısı eksik.
- 0007.Toplumun her kesimine yönelik spor programları yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Toplumun her kesimine yönelik spor programları yapmak: kart bağlantısı eksik.
- 0008.Uluslararası spor turnuvalarını artırarak devam etmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Uluslararası spor turnuvalarını artırarak devam etmek: kart bağlantısı eksik.
- 0009.Sporun sağlık üzerindeki etkilerini vurgulayan kampanyalar düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Sporun sağlık üzerindeki etkilerini vurgulayan kampanyalar düzenlemek: kart bağlantısı eksik.
- 0010.Amatör spor kulüplerini desteklemeyi sürdürmek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Amatör spor kulüplerini desteklemeyi sürdürmek: kart bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Halkla İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (31):

- 0001.Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri: kart bağlantısı eksik.
- 0002.Basılı ve Görsel Tanıtım Metaryallerinin Üretimi ve Uygulanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Basılı ve Görsel Tanıtım Metaryallerinin Üretimi ve Uygulanması: kart bağlantısı eksik.
- 0003.Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri: kart bağlantısı eksik.
- 0004.Vatandaş Bilgilendirme ve Toplu iletişim Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Vatandaş Bilgilendirme ve Toplu iletişim Faaliyetleri: kart bağlantısı eksik.
- 0005.Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi: kart bağlantısı eksik.
- 0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri: kart bağlantısı eksik.
- 0007.Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri: kart bağlantısı eksik.
- 0008.Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri: kart bağlantısı eksik.
- 0009.Basın Takip, Medya İzleme ve Raporlama Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Basın Takip, Medya İzleme ve Raporlama Faaliyetleri: kart bağlantısı eksik.
- 0010.Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri: kart bağlantısı eksik.
- 0010.Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri: faaliyet açıklaması eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Hukuk İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (3):

- 0001.Birimlerin hazırladığı sözleşme ve yönetmeliklerin ön incelemeden geçirilerek dava açılma riskinin azaltılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Mevcut UYAP ve EBYS sistemleriyle entegre çalışan bir "Hukuk Otomasyon Sistemi"nin devreye alınması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Personelin uzmanlık alanlarına göre (İmar hukuku, Kamu İhale hukuku vb.) sertifikalı eğitim programlarına katılımının sağlanması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.

Uyarılar (0):

Yok.

### İklim Değişikliği ve Sıfır Atık Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (5):

- 0001.Sürdürülebilir Enerji ve İklim Eylem Planının takibi ve ihtiyaç halinde güncellenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.İklim değişikliği konusunda kurum içi, kurumlar arası ve vatandaşlara bilgilendirici eğitimler düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Yerel yönetimler, sivil toplum kuruluşları, üniversiteler ve özel sektör ile iş birliği yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Hava kalitesi eylem planı ve gürültü eylem planı hazırlanmasına destek vermek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Sıfır Atık uygulamaları ve atık yönetim, denetimler ve eğitim faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.

Uyarılar (0):

Yok.

### İmar ve Şehircilik Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (32):

- 0001.İmar Planlama ve Uygulama Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.İmar Planlama ve Uygulama Faaliyetleri: kart bağlantısı eksik.
- 0002.Yapı Ruhsatlandırma ve İskân İşlemleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Yapı Ruhsatlandırma ve İskân İşlemleri: kart bağlantısı eksik.
- 0003.İmar Mevzuatı Denetim ve Kontrol Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.İmar Mevzuatı Denetim ve Kontrol Faaliyetleri: kart bağlantısı eksik.
- 0004.Vatandaş ve Paydaş Hizmetleri Yönetimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Vatandaş ve Paydaş Hizmetleri Yönetimi: kart bağlantısı eksik.
- 0005.Kurumsal Yazışma ve Süreç Koordinasyonu: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Kurumsal Yazışma ve Süreç Koordinasyonu: kart bağlantısı eksik.
- 0006.Yapı süreci denetimleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Yapı süreci denetimleri: kart bağlantısı eksik.
- 0007.Kaçak ve ruhsata aykırı yapılaşmayla mücadele: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Kaçak ve ruhsata aykırı yapılaşmayla mücadele: kart bağlantısı eksik.
- 0008.Yapı kullanma izin belgesi işlemleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Yapı kullanma izin belgesi işlemleri: kart bağlantısı eksik.
- 0009.Şikâyet ve başvuruların değerlendirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Şikâyet ve başvuruların değerlendirilmesi: kart bağlantısı eksik.
- 0010.Yıkım işlemleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Yıkım işlemleri: kart bağlantısı eksik.
- 0011.Yapı denetim kuruluşlarıyla koordinasyon: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Yapı denetim kuruluşlarıyla koordinasyon: kart bağlantısı eksik.
- 0012.Mahkeme ve hukuki süreçlere ilişkin işlemler: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Mahkeme ve hukuki süreçlere ilişkin işlemler: kart bağlantısı eksik.
- 0013.Arşiv ve kayıt işlemleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Arşiv ve kayıt işlemleri: kart bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### İnsan Kaynakları ve Eğitim Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (62):

- 0001.Eğitimci eğitimi programları düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Eğitimci eğitimi programları düzenlemek: kart bağlantısı eksik.
- 0002.Farklı konularda sertifika programları düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Farklı konularda sertifika programları düzenlemek: kart bağlantısı eksik.
- 0003.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak: kart bağlantısı eksik.
- 0004.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek: kart bağlantısı eksik.
- 0005.Moral, motivasyon, Kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyetler düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Moral, motivasyon, Kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyetler düzenlemek: kart bağlantısı eksik.
- 0006.Eğitimci eğitimi programları düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Eğitimci eğitimi programları düzenlemek: kart bağlantısı eksik.
- 0007.Farklı konularda sertifika programları düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Farklı konularda sertifika programları düzenlemek: kart bağlantısı eksik.
- 0008.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak: kart bağlantısı eksik.
- 0009.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek: kart bağlantısı eksik.
- 0010.Moral, motivasyon, Kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyetler düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Moral, motivasyon, Kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyetler düzenlemek: kart bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Kentsel Dönüşüm Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (11):

- 0001.Vatandaş bilgilendirme toplantıları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Çalışan personel için eğitim programları düzenleme: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Planlama ve strateji geliştirme: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Kentsel Dönüşüm Kapsamında yapılacak maddi yardımlar hususunda (kira yardımı, tahliye desteği, yarısı bizden yapım yardımı vb.) hak sahiplerine bilgilendirme yapılması, talep doğrultusunda sistem girişlerinin sağlanması ve takibinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Kültür, Sanat ve Sosyal İşler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (89):

- 0001.Bilgilendirme Çalışmaları: Seminerler, atölye çalışmaları, konferanslar ve sosyal medya kampanyaları aracılığıyla halkı kütüphaneler ile ilgili gelişmeler konusunda bilgilendirmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Bilgilendirme Çalışmaları: Seminerler, atölye çalışmaları, konferanslar ve sosyal medya kampanyaları aracılığıyla halkı kütüphaneler ile ilgili gelişmeler konusunda bilgilendirmek.: kart bağlantısı eksik.
- 0002.Okuma Etkinlikleri: Kitap kulüpleri, yazar söyleşileri, okuma yarışmaları gibi etkinliklerle kitap okumayı teşvik etmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Okuma Etkinlikleri: Kitap kulüpleri, yazar söyleşileri, okuma yarışmaları gibi etkinliklerle kitap okumayı teşvik etmek.: kart bağlantısı eksik.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: kart bağlantısı eksik.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2029 toplamı bütçe içi + dışı ile eşit değil.
- 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak.: 2028 toplamı bütçe içi + dışı ile eşit değil.
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: kart bağlantısı eksik.
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Bütçe finansman bilgisi eksik.
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: kart bağlantısı eksik.
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Bütçe finansman bilgisi eksik.
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): kart bağlantısı eksik.
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik.
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: kart bağlantısı eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2029 Tahmin finansman bilgisi eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Bütçe finansman bilgisi eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2028 Tahmin finansman bilgisi eksik.
- 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: kart bağlantısı eksik.
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Bütçe finansman bilgisi eksik.
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): kart bağlantısı eksik.
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Bütçe finansman bilgisi eksik.
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili): 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: kart bağlantısı eksik.
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Bütçe finansman bilgisi eksik.
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: kart bağlantısı eksik.
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Bütçe finansman bilgisi eksik.
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: kart bağlantısı eksik.
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Bütçe finansman bilgisi eksik.
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: kart bağlantısı eksik.
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik.
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: kart bağlantısı eksik.
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik.
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: kart bağlantısı eksik.
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Bütçe finansman bilgisi eksik.
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: kart bağlantısı eksik.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2029 toplamı bütçe içi + dışı ile eşit değil.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Bütçe finansman bilgisi eksik.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2028 toplamı bütçe içi + dışı ile eşit değil.
- 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: kart bağlantısı eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: faaliyet açıklaması eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Bütçe finansman bilgisi eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.

Uyarılar (0):

Yok.

### Makine İkmal Bakım ve Onarım Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (69):

- 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Birimlerden gelen araç taleplerinin karşılanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2025 Yıl Sonu Tahmini / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- Ekonomik tablo boyut/tutar bilgisi geçersiz.
- 2027 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027: Program Grubu Belirlenmeli / Bütçe İçi: 9 ekonomik gider hücresi eksik (yoksa 0 girin).
- 2027: Program Grubu Belirlenmeli / Bütçe Dışı: 9 ekonomik gider hücresi eksik (yoksa 0 girin).
- 2029: Program Grubu Belirlenmeli / Bütçe İçi: 9 ekonomik gider hücresi eksik (yoksa 0 girin).
- 2029: Program Grubu Belirlenmeli / Bütçe Dışı: 9 ekonomik gider hücresi eksik (yoksa 0 girin).

Uyarılar (0):

Yok.

### Mali Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (25):

- 0001.Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Raporlardaki tespitlerin ayrıntılı analizi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Uygunsuzlukların giderilmesi için somut adımların belirlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Büyükçekmece Belediyesi Mali Veri Analitiği Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Faiz Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Faiz Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Transferleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Transferleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Borç Verme / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Borç Verme / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Yedek Ödenekler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Yedek Ödenekler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Özel Kalem Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (5):

- 0001.Üst Yönetim Program ve Randevu Yönetimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Protokol ve Resmi Organizasyon Yönetimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Paydaş Talep ve İlişki Yönetimi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler: sorumlu harcama birimleri kataloğu bağlantısı eksik.

Uyarılar (0):

Yok.

### Park ve Bahçeler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (46):

- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (17,840).
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Planlanan: kaynak değeri doğrulanmalı (50,000).
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (50,000).
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2027 Hedef: kaynak değeri doğrulanmalı (50,000).
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2028 Tahmin: kaynak değeri doğrulanmalı (60,000).
- SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı: 2029 Tahmin: kaynak değeri doğrulanmalı (60,000).
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2025 Gerçekleşme: kaynak değeri doğrulanmalı (132,915).
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Planlanan: kaynak değeri doğrulanmalı (250,000).
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (250,000).
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2027 Hedef: kaynak değeri doğrulanmalı (200,000).
- SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı: 2029 Tahmin: kaynak değeri doğrulanmalı (300,000).
- SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (650,000).
- 0001.Su israfını önlemek ve su kullanım verimliliğini artırmak için Akıllı Otomatik sulama sistemlerinin kurulumu, bakım ve onarımı.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Su israfını önlemek ve su kullanım verimliliğini artırmak için Akıllı Otomatik sulama sistemlerinin kurulumu, bakım ve onarımı.: kart bağlantısı eksik.
- 0002.İmar planında park ve yeşil alan olarak ayrılan alanların projelendirilerek kente kazandırılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.İmar planında park ve yeşil alan olarak ayrılan alanların projelendirilerek kente kazandırılması: kart bağlantısı eksik.
- 0003.Ekonomik ömrünü tamamlamış park ve peyzaj alanlarının revize edilmesi, bakımı ve onarımı: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Ekonomik ömrünü tamamlamış park ve peyzaj alanlarının revize edilmesi, bakımı ve onarımı: kart bağlantısı eksik.
- 0004.Bitkilendirme, budama, gübreleme ve çim biçimi gibi rutin peyzaj bakımlarının yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Bitkilendirme, budama, gübreleme ve çim biçimi gibi rutin peyzaj bakımlarının yapılması.: kart bağlantısı eksik.
- 0005.Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi.: kart bağlantısı eksik.
- 0006.İş hacmi doğrultusunda gerekli malzeme, araç ve gereçlerin temini ve yönetimi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.İş hacmi doğrultusunda gerekli malzeme, araç ve gereçlerin temini ve yönetimi.: kart bağlantısı eksik.
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: kart bağlantısı eksik.
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0007.Kırılgan grupların da rahatlıkla kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı.: 2027 toplamı bütçe içi + dışı ile eşit değil.
- 0008.Kent genelinde ağaçlandırma çalışmaları yaparak kişi başına düşen yeşil alan miktarını artırmak ve biyolojik çeşitliliği korumak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Kent genelinde ağaçlandırma çalışmaları yaparak kişi başına düşen yeşil alan miktarını artırmak ve biyolojik çeşitliliği korumak: kart bağlantısı eksik.
- 0009.Ekonomik ömrünü tamamlamış parkların donatılarının yenilenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Ekonomik ömrünü tamamlamış parkların donatılarının yenilenmesi: kart bağlantısı eksik.
- 0010.Çocukların fiziksel ve zihinsel gelişimini destekleyen, uluslararası güvenlik sertifikalı modern oyun alanlarının kurulumu.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Çocukların fiziksel ve zihinsel gelişimini destekleyen, uluslararası güvenlik sertifikalı modern oyun alanlarının kurulumu.: kart bağlantısı eksik.
- 0011.Engelli bireylerin kullanımına uygun kent donatılarının park ve meydanlara yerleştirilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Engelli bireylerin kullanımına uygun kent donatılarının park ve meydanlara yerleştirilmesi.: kart bağlantısı eksik.
- 0012.Vatandaşların ücretsiz spor yapabileceği modern dış mekân spor ekipmanlarının temini ve montajı: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Vatandaşların ücretsiz spor yapabileceği modern dış mekân spor ekipmanlarının temini ve montajı: kart bağlantısı eksik.
- 0013.Kentin kimliğini yansıtan heykel, anıt, saat kulesi gibi sanatsal donatılar ile meydan zeminlerinin estetik tasarımı: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Kentin kimliğini yansıtan heykel, anıt, saat kulesi gibi sanatsal donatılar ile meydan zeminlerinin estetik tasarımı: kart bağlantısı eksik.
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (3):

- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH17/PG02. Kullanıma sunulan ve bakım onarımı yapılan kent donatısı hakkında vatandaş memnuniyeti: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Plan Proje Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (7):

- 0001.1/5000 ölçekli nazım imar planları ve kentsel gelişme doğrultusunda etaplar halinde uygulama imar planı ve plan değişikliği çalışmalarını yapmak ve uygulamak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (1):

- SH20.PG05. Vatandaşların memnuniyet: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Rehberlik ve Teftiş Kurulu Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (13):

- 0001.Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Belediye kaynaklarının mevzuata uygun, etkili ve verimli kullanılmasını sağlamak amacıyla; risk odaklı denetim faaliyetlerini gerçekleştirmek, kurumsal süreçlerdeki hata ve usulsüzlükleri önleyici rehberlik hizmetleri sunmak ve soruşturma süreçlerini yasal süreleri içerisinde %100 oranında tamamlamaktır.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe dışı faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Ruhsat ve Denetim Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (17):

- 0001.Ruhsatlandırma faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Denetim faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Eğitim ve bilgilendirme faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Yıl içerisinde vatandaşlardan gelen şikâyetlerin takibi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Denetim ve ruhsat verilerinin toplanması ve analiz edilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Sağlık İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (32):

- 0001.Engelli ve özel gereksinimli bireylere yönelik eğitim, rehabilitasyon ve sosyal gelişim faaliyetlerinin artması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Engelli ve özel gereksinimli bireylere yönelik eğitim, rehabilitasyon ve sosyal gelişim faaliyetlerinin artması: kart bağlantısı eksik.
- 0002.Ailelere yönelik bilgilendirme ve destek programlarının düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Ailelere yönelik bilgilendirme ve destek programlarının düzenlenmesi: kart bağlantısı eksik.
- 0003.Kurumlar arası iş birliği ile erişilebilir hizmet modellerinin geliştirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Kurumlar arası iş birliği ile erişilebilir hizmet modellerinin geliştirilmesi: kart bağlantısı eksik.
- 0004.Larva ve Erişkin Vektörle Mücadele Çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Larva ve Erişkin Vektörle Mücadele Çalışmaları: kart bağlantısı eksik.
- 0005.Dezenfeksiyon ve İlaçlama Faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Dezenfeksiyon ve İlaçlama Faaliyetleri: kart bağlantısı eksik.
- 0006.Vatandaş Bilgilendirme ve Farkındalık Çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Vatandaş Bilgilendirme ve Farkındalık Çalışmaları: kart bağlantısı eksik.
- 0007.Sağlık Nesiller Güçlü Yarınlar Koruyucu Tarama ve Eğitim Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Sağlık Nesiller Güçlü Yarınlar Koruyucu Tarama ve Eğitim Projesi: kart bağlantısı eksik.
- 0008.Dijital Sağlık Takip Sistemi Kurumsal Veri Entegrasyon Projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Dijital Sağlık Takip Sistemi Kurumsal Veri Entegrasyon Projesi: kart bağlantısı eksik.
- 0009.Hasta Nakil Hizmetlerinin Kapasitesinin Artırılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Hasta Nakil Hizmetlerinin Kapasitesinin Artırılması: kart bağlantısı eksik.
- 0010.Vatandaş Memnuniyetini artırmaya yönelik hizmet iyileştirme çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Vatandaş Memnuniyetini artırmaya yönelik hizmet iyileştirme çalışmaları: kart bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (1):

- SH03/PG01 Sunulan Hasta Nakil Hizmet Sayısı Sağlık Hizmetlerinden yararlanan vatandaşların memnuniyet oranı: sayı/oran birimi müdürlükçe kontrol edilmeli.

### Sosyal Destek Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (38):

- 0001.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: kart bağlantısı eksik.
- 0002.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: kart bağlantısı eksik.
- 0003.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: kart bağlantısı eksik.
- 0004.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: kart bağlantısı eksik.
- 0005.Yerel Eşitlik Eylem planının hayata geçirilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Yerel Eşitlik Eylem planının hayata geçirilmesi.: kart bağlantısı eksik.
- 0006.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: kart bağlantısı eksik.
- 0007.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: kart bağlantısı eksik.
- 0008.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: kart bağlantısı eksik.
- 0009.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: kart bağlantısı eksik.
- 0010.Yerel Eşitlik Eylem planının hayata geçirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Yerel Eşitlik Eylem planının hayata geçirilmesi: kart bağlantısı eksik.
- 0011.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Dar gelirli ve ihtiyaç sahibi hemşehrilerimiz destekleyici ve/veya güçlendirici çalışmaların yapılması: kart bağlantısı eksik.
- 0012.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0012.Kırılgan gruplara (kadın, çocuk, genç, yaşlı, hasta, engelli) ait bireyleri güçlendirici, her türlü bilgilendirici, ayni ve nakdi destek vb. destekleyici faaliyetlerde bulunulması: kart bağlantısı eksik.
- 0013.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0013.Toplumun her kesimini bilinçlendirmeye ve/veya bilgilendirmeye katkı sağlayacak çeşitli etkinlikler düzenlenmesi: kart bağlantısı eksik.
- 0014.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0014.Diğer kurum ve kuruluşlarla iş birliği halinde çeşitli etkinlikleri yapılması.: kart bağlantısı eksik.
- 0015.Yerel Eşitlik Eylem planının hayata geçirilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0015.Yerel Eşitlik Eylem planının hayata geçirilmesi.: kart bağlantısı eksik.
- 0016.Sosyal İnceleme ve Vaka Takibi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0016.Sosyal İnceleme ve Vaka Takibi: kart bağlantısı eksik.
- 0017.Çocuk Rehberlik ve Danışmanlık Destek Programı: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0017.Çocuk Rehberlik ve Danışmanlık Destek Programı: kart bağlantısı eksik.
- 0018.Eğitim ve Farkındalık Etkinlikleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0018.Eğitim ve Farkındalık Etkinlikleri: kart bağlantısı eksik.
- 0019.Aile Destek ve Bilgilendirme Çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0019.Aile Destek ve Bilgilendirme Çalışmaları: kart bağlantısı eksik.

Uyarılar (5):

- SH39/PG01. Sosyal incelemesi yapılan çocuk sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG02. Rehberlik ve Danışmanlık desteği verilen çocuk sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG03. Dezavantajlı Çocukların güçlendirilmesine yönelik eğitim ve farkındalık çalışma sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG04. Ailelere yönelik rehberlik çalışması: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH39/PG05. Gerçekleştirilen görüşmelerden duyulan memnuniyet oranı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Strateji Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (10):

- 0001.Stratejik planlama ve bütçeleme faaliyetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.İç Kontrol Eylem Planı Uyum ve Kalite Yönetim Süreçleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Performans göstergelerinin takibi ve raporlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Katılımcı bütçe çalışmaları: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Performans programı ve bütçenin hazırlanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Ulusal ve uluslararası projelere katılım: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.2050 Büyükçekmece vizyonu takibi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Ulusal ve uluslararası kongre ve toplantılara katılım: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Tarımsal Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (42):

- 0001.Yeni üretim alanlarının tespiti, tahsisi, tesisi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Yeni üretim alanlarının tespiti, tahsisi, tesisi: kart bağlantısı eksik.
- 0002.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: kart bağlantısı eksik.
- 0003.Üretimin zehirsiz gıda ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Üretimin zehirsiz gıda ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: kart bağlantısı eksik.
- 0004.Önemli günlerde toplantı, seminer düzenlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Önemli günlerde toplantı, seminer düzenlenmesi: kart bağlantısı eksik.
- 0005.Tıbbi aromatik bitkilerin yetiştirilmesinin yaygınlaştırılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Tıbbi aromatik bitkilerin yetiştirilmesinin yaygınlaştırılması: kart bağlantısı eksik.
- 0006.Çiftçilere ve hayvan üreticilerine tohum, fide ve tarımsal girdi desteği: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Çiftçilere ve hayvan üreticilerine tohum, fide ve tarımsal girdi desteği: kart bağlantısı eksik.
- 0007.Yenilikçi ve sürdürülebilir tarımsal faaliyetler: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Yenilikçi ve sürdürülebilir tarımsal faaliyetler: kart bağlantısı eksik.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: kart bağlantısı eksik.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2029 Tahmin finansman bilgisi eksik.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2027 Bütçe finansman bilgisi eksik.
- 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini: 2028 Tahmin finansman bilgisi eksik.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: kart bağlantısı eksik.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2029 Tahmin finansman bilgisi eksik.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2027 Bütçe finansman bilgisi eksik.
- 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi: 2028 Tahmin finansman bilgisi eksik.
- 0010.Bitkisel ve hayvansal üretim yapan üreticilerin eğitim ve bilgilendirme çalışmalarının yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Bitkisel ve hayvansal üretim yapan üreticilerin eğitim ve bilgilendirme çalışmalarının yapılması: kart bağlantısı eksik.
- 0011.Yerel ürünlerin satış ve pazarlamasına yönelik etkinlik yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Yerel ürünlerin satış ve pazarlamasına yönelik etkinlik yapılması: kart bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (6):

- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG03. Dikey ve topraksız tarım yöntemleriyle yapılan çalışma sayısı: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2025 Gerçekleşme kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2026 Planlanan kaynakta çizgi; müdürlükçe kontrol edilmeli.
- SH27/PG04. Desteklenen çiftçi sayısı: 2026 Yıl Sonu Tahmini kaynakta çizgi; müdürlükçe kontrol edilmeli.

### Temizlik İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (8):

- 0001.Evsel atıkların düzenli olarak toplanması ve nakli: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Kamuya ait alanların (cadde, sokak, meydan, okul bahçesi, durak, semt pazarı vb.) süpürülmesi, yıkanması ve temizlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.İnşaat-moloz, bahçe atıklarının ve atıl eşyaların toplanması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Atık konteynerlerinin bakım, onarım, yıkama ve dezenfeksiyon işlemlerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.İbadethane temizliklerinin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Marmara Denizi kıyısında bulunan Büyükçekmece Kordon boyu sahil şeridinin yıkanması, çöp kutularının boşaltılması ve temizlenmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Kirleten öder projesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Şehir merkezinde modern ve estetik çöp konteynerlerinin yerleştirilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.

Uyarılar (0):

Yok.

### Veteriner İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (32):

- 0001.Mevzuat kapsamında sahipsiz hayvanlara yönelik rehabilitasyon hizmetlerini gerçekleştirmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.İlaç, tıbbi sarf malzemesi ve mama alımı ile cerrahi müdahalelerin yürütülmesini sağlamak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Sokak hayvanlarına yönelik besleme faaliyetlerini, periyodik aralıklarla ve insan sağlığı ile çevre sağlığı gözetilerek gerçekleştirmek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe / Toplam kaynak tutarı doğrulanmalı.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin / Toplam kaynak tutarı doğrulanmalı.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2029 Tahmin finansman bilgisi eksik.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2027 Bütçe finansman bilgisi eksik.
- 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak.: 2028 Tahmin finansman bilgisi eksik.
- 0005.4 Ekim Dünya Hayvanları Koruma Günü ve 4 Nisan Sokak Hayvanları Günü başta olmak üzere, hayvanlara yönelik özel gün ve haftalarda etkinlikler yapmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.İlçemizdeki okullarda; sahiplendirme ve “Satın Alma, Sahiplen” kampanyaları kapsamında sahipsiz hayvanlar, hayvan sevgisi ve zoonotik hastalıklar konularında eğitimler vermek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.

### Yazı İşleri Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (97):

- 0001.Encümen ve Belediye Meclisi İşlemlerinin takibi ve alınan kararların yazılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.Encümen ve Belediye Meclisi İşlemlerinin takibi ve alınan kararların yazılması: kart bağlantısı eksik.
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: kart bağlantısı eksik.
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Bütçe finansman bilgisi eksik.
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0002.Alınan Kararların İlgili Birimlere İletilmesi: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0003.Gelen evrakların kayıt altına alınması ve ilgili birime gönderilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Gelen evrakların kayıt altına alınması ve ilgili birime gönderilmesi: kart bağlantısı eksik.
- 0004.Giden evrakların kayıt altına alınması ve ilgili birime gönderilmesi: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Giden evrakların kayıt altına alınması ve ilgili birime gönderilmesi: kart bağlantısı eksik.
- 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması: kart bağlantısı eksik.
- 0006.Müracaat eden çiftlerin nikah işlemlerinin yapılması, kayıtlarının ve istatistiklerin tutulması: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.Müracaat eden çiftlerin nikah işlemlerinin yapılması, kayıtlarının ve istatistiklerin tutulması: kart bağlantısı eksik.
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: kart bağlantısı eksik.
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Bütçe finansman bilgisi eksik.
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0007.Dijital Nikah Yönetim Sisteminin Kurulması ve İşletilmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: kart bağlantısı eksik.
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Bütçe finansman bilgisi eksik.
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0008.Nikah Akdi ve Tescil İşlemlerinin Yürütülmesi.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: kart bağlantısı eksik.
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Bütçe finansman bilgisi eksik.
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0009.Nikah Salonlarının Teknolojik ve Fiziksel Modernizasyonu.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: kart bağlantısı eksik.
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Bütçe finansman bilgisi eksik.
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0010.Saha Hizmetleri İçin Mobil Altyapı Desteği.: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: kart bağlantısı eksik.
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Bütçe finansman bilgisi eksik.
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Yıl Sonu Tahmini finansman bilgisi eksik.
- 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri: 2026 Haziran Sonu Harcama finansman bilgisi eksik.
- 2026 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027 Bütçe / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2028 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sermaye Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2029 Tahmin / Sermaye Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2027: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2027: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2028: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2028: ekonomik personel/SGK satırları ortak tablodan farklı.
- 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.
- 2029: ortak maliyet ve ekonomik tablo toplamları uyuşmuyor.
- 2029: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor.

Uyarılar (0):

Yok.

### Zabıta Müdürlüğü

Gönderime hazır: **Hayır**.

Hatalar (26):

- 0001.İşyeri Açma ve Çalışma Ruhsatı olmadan ticari faaliyete başlayan işletmelerin tespitini yaparak ruhsatlandırmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0001.İşyeri Açma ve Çalışma Ruhsatı olmadan ticari faaliyete başlayan işletmelerin tespitini yaparak ruhsatlandırmak.: kart bağlantısı eksik.
- 0002.Hijyen yönünden denetimleri sıklaştırmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0002.Hijyen yönünden denetimleri sıklaştırmak.: kart bağlantısı eksik.
- 0003.Gıda tüketimine uygun olmayan müesseseleri mühürlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0003.Gıda tüketimine uygun olmayan müesseseleri mühürlemek.: kart bağlantısı eksik.
- 0004.Çalışacak zabıta personellerine denetim konusunda eğitim düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0004.Çalışacak zabıta personellerine denetim konusunda eğitim düzenlemek.: kart bağlantısı eksik.
- 0005.Hijyen Yönünden denetimleri sıklaştırmak: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0005.Hijyen Yönünden denetimleri sıklaştırmak: kart bağlantısı eksik.
- 0006.İş yeri Açma ve Çalışma ruhsatı olmadan ticari faaliyete başlayan işletmelerin tespitini yaparak ruhsatlandırmak.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0006.İş yeri Açma ve Çalışma ruhsatı olmadan ticari faaliyete başlayan işletmelerin tespitini yaparak ruhsatlandırmak.: kart bağlantısı eksik.
- 0007.Gıda tüketimine uygun olmayan müesseseleri mühürlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0007.Gıda tüketimine uygun olmayan müesseseleri mühürlemek.: kart bağlantısı eksik.
- 0008.Çalışacak zabıta personellerine denetim konusunda eğitim düzenlemek.: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0008.Çalışacak zabıta personellerine denetim konusunda eğitim düzenlemek.: kart bağlantısı eksik.
- 0009.Hukuki koruma ve mevzuat eğitimi düzenlemek: sorumlu harcama birimleri kataloğu bağlantısı eksik.
- 0009.Hukuki koruma ve mevzuat eğitimi düzenlemek: kart bağlantısı eksik.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Personel Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Mal ve Hizmet Alım Giderleri / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe İçi: ekonomik kaynak tutarı ve program grubu doğrulanmalı.
- 2026 Haziran Sonu Harcama / Cari Transferler / Bütçe Dışı: ekonomik kaynak tutarı ve program grubu doğrulanmalı.

Uyarılar (0):

Yok.
