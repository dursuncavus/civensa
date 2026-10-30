# 2027 PP ilk yükleme — kaynak kontrol listesi

Kitap temiz mi: **Hayır**.

Kitap kontrol maddesi: **41**.

Yalnız program grubu dağılımı bekleyen müdürlük: **0**.

Gönderime hazır: **17/34** (yalnızca bu prova).

Kaynak: `2027-performans-programi_16102026_duzeltilmis 2.idml`; SHA256: `261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e`.

Mesaj sayımı: **145 kitap mesajı + 140 yalnız program grubu mesajı = 285**. Kitap mesajlarından 0 adedi ayrıca dağılım gerektirir; kitap nedenleri listede, dağılım hücreleri ayrı bölümde gösterilir ve mesaj ikinci kez sayılmaz.

Doğrulama: 285 SOURCE mesajı, 0 SYSTEM mesajı; 0 saklama aktarım sorunu; 23 engelleyici olmayan uyarı.

Aynı kök nedenden üreyen mesajlar müdürlük listesinde tek kontrol maddesinde toplanır. Hazır = gerçek paket uygulandı ve validate_department hata listesi boş. Çıkarılan tablo ve ek üyelik sorunu doğrulama mesajı sayısına eklenmez. Kitap maddeleri dağılım işlerini içermez. Fark = kitaptaki/kontrol edilen toplam − hesaplanan tutar. Koşullu 0,00 önerisi veri düzeltmesi değildir; kaynak yokluğunu Strateji teyit etmelidir.

## Çalıştırma

```sh
# CIVENSA_TEST_POSTGRES_URL: yerel, disposable PostgreSQL 16+; CREATE DATABASE yetkisi.
python scripts/first_load_dryrun.py 'tests/fixtures/first_load/source/2027-performans-programi_16102026_duzeltilmis 2.idml' --out docs/first-load/dryrun-printed.md
```

Yalnızca localhost test URL adresi okunur; her prova ayrı veritabanı oluşturur ve sonunda siler. Dışlama yalnızca prova betiğinde, geçici Word üzerinde yapılır; üretici ve canlı yükleyici tablo çıkarmaz. Kurum özetleri IDML kaynağından ayrıca okunur; dışlama bu denetimleri kaldırmaz.

Tek kurum, doğrulanmış dönem şablonu, ad eşlemesi ve denetimli/idempotent faaliyet kataloğu gerçek servislerle hazırlanır. Boş, çizgi ve sıfır ayrıdır. Kaynak sayıları değiştirilmedi; doğrulama kuralları gevşetilmedi. Sayfalar IDML hikâyesinin ilk basılı sayfasıdır. T numarası dışlamadan önce üretilen Word tablosunu; r/satır ve c/sütun 1 tabanlı hücreyi gösterir.

Uygulama: 34 müdürlük, 64 kart, 263 gösterge, 290 faaliyet, 1340 ekonomik değer; alt programa bağlanamayan faaliyet: 0. Katalog: 290 faaliyet, 290 sorumluluk, 290 yerel bağlantı.

İçe aktarma hatası: 0; kaynak çelişkisi: 0; çözümlenemeyen müdürlük: 1.

## Kurum özet tabloları

Kurum kontrolü: **1036 PASS / 184 FAIL**. Bu bulgular müdürlük SOURCE/SYSTEM mesajlarına ve kitap kontrol maddesi sayımına eklenmez.

FAIL sınıfları: **BOOK 53 / CHECK 104 / UNKNOWN 27**.

BOOK = aynı basılı tablonun kendi kapsamı içinde aritmetik yanlış; aşağıda toplanan hücreler gösterilir. CHECK = kapsam / program eşlemesi / tekil dağılım veya okuma sınırı; kitap hatası sayılmaz. UNKNOWN = farklı basılı kaynaklar uyuşmuyor veya hücre okunamıyor; kaynaktan hangi tarafın yanlış olduğu belirlenemedi. Sayısal fark tek başına BOOK kanıtı değildir.

Tablolar başlık metniyle bulunur; sayfa numarası yalnız kaynak kanıtıdır. Fark = basılı − hesaplanan. Boş, çizgi veya okunamayan tutar sıfır sayılmaz; eksik toplam ve hesaplanamayan karşılaştırma FAIL olur. Yedek Ödenekler yalnız kurum düzeyinde ayrı gösterilir. Ekonomik çapraz toplamlar ayrıştırılmış kaynak tutarlarını kullanır; kaynak inceleme durumunu veya yükleme engelini değiştirmez.

Okunan tablolar: s.244 / u40c3i5faa — Ekonomik kod / program grupları; s.246 / u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı; s.248 / u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı.

Sınırlar: IDML sayfası hikâyenin ilk basılı sayfasıdır; çok sayfalı tabloda hücrenin kesin devam sayfası çıkarılamaz. Program ayrıntısı, başlığında “Ekonomik Kod” yazmasına rağmen program / alt program / faaliyet hiyerarşisidir; ekonomik kategori dökümü içermez. Program çapraz toplamında kartlara bağlı üyelik tutarları kullanılır; ekonomik kategoriler program gruplarına tahminen dağıtılmaz. Yalnız genel “Program/Programı” soneki eşdeğer sayılır; farklı program adları eşlenmez ve ayrı FAIL olarak gösterilir. Döner Sermaye satırı satır toplamında denetlenir; kitapta bütçe içi + döner sermaye genel toplamı verilmediğinde böyle bir toplam üretilmez.

Yedek Ödenekler — yalnız kurum düzeyi; müdürlük farkına katılmaz. Aşağıdaki tutarlar basılı hücrelerdir; doğrulukları satır / sütun kontrollerinde ayrıca gösterilir.

| Kitap sayfası / tablo / satır | Yıl | Hizmet | Yönetim ve Destek | Program Dışı | Toplam |
| --- | --- | ---: | ---: | ---: | ---: |
| s.244 / u40c3i5faa / 11 | 2027 | 0,00 | 500.000,00 | 600.000.000,00 | 600.000.000,00 |
| s.244 / u40c3i5faa / 11 | 2028 | 0,00 | 610.000.000,00 | 610.000.000,00 | 610.000.000,00 |
| s.244 / u40c3i5faa / 11 | 2029 | 0,00 | 744.200.000,00 | 744.200.000,00 | 0,00 |

| Durum | Sınıf | Kontrol | Kitap sayfası | Tablo | Satır | Sütun | Basılı değer | Hesaplanan değer | Fark | Açıklama |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 5 | 647.804.357,00 | 647.804.357,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 9 | 790.321.316,00 | 790.321.316,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 13 | 964.192.006,00 | 964.192.006,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 5 | 59.488.454,00 | 59.488.454,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 9 | 72.575.914,00 | 72.575.914,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 13 | 88.542.615,00 | 88.542.615,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 5 | 5.054.079.860,00 | 5.079.079.860,00 | -25.000.000,00 | 2027: bileşen sütunları 2, 3, 4 Kanıt: s.244 / u40c3i5faa / r5c2 = «1.793.766.517,00»; s.244 / u40c3i5faa / r5c3 = «3.285.313.343,00»; s.244 / u40c3i5faa / r5c4 = «0,00» |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 9 | 6.318.477.429,00 | 6.318.477.429,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 13 | 7.708.542.463,00 | 7.708.542.463,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 5 | 30.000.000,00 | 30.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 9 | 36.600.000,00 | 36.600.000,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 13 | 44.652.000,00 | 44.652.000,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 5 | 132.012.604,00 | 132.012.604,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 9 | 161.055.377,00 | 161.055.377,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 13 | 196.487.560,00 | 196.487.560,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 5 | 1.401.176.848,00 | 1.401.176.848,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 9 | 1.709.435.755,00 | 1.709.435.755,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 13 | 2.085.511.621,00 | 2.085.511.621,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 5 | 48.912.877,00 | 48.912.877,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 9 | 59.673.710,00 | 59.673.710,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 13 | 72.801.926,00 | 72.801.926,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 5 | 0,00 | 0,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 9 | 0,00 | 0,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 13 | 0,00 | 0,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 11 — Yedek Ödenekler | 5 | 600.000.000,00 | 600.500.000,00 | -500.000,00 | 2027: bileşen sütunları 2, 3, 4 Kanıt: s.244 / u40c3i5faa / r11c2 = «0,00»; s.244 / u40c3i5faa / r11c3 = «500.000,00»; s.244 / u40c3i5faa / r11c4 = «600.000.000,00» |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 11 — Yedek Ödenekler | 9 | 610.000.000,00 | 1.220.000.000,00 | -610.000.000,00 | 2028: bileşen sütunları 6, 7, 8 Kanıt: s.244 / u40c3i5faa / r11c6 = «0,00»; s.244 / u40c3i5faa / r11c7 = «610.000.000,00»; s.244 / u40c3i5faa / r11c8 = «610.000.000,00» |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 11 — Yedek Ödenekler | 13 | 0,00 | 1.488.400.000,00 | -1.488.400.000,00 | 2029: bileşen sütunları 10, 11, 12 Kanıt: s.244 / u40c3i5faa / r11c10 = «0,00»; s.244 / u40c3i5faa / r11c11 = «744.200.000,00»; s.244 / u40c3i5faa / r11c12 = «744.200.000,00» |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 5 | 7.998.475.000,00 | 8.497.975.000,00 | -499.500.000,00 | 2027: bileşen sütunları 2, 3, 4 Kanıt: s.244 / u40c3i5faa / r12c2 = «3.634.800.237,00»; s.244 / u40c3i5faa / r12c3 = «4.263.174.763,00»; s.244 / u40c3i5faa / r12c4 = «600.000.000,00» |
| FAIL | BOOK | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 9 | 9.758.139.501,00 | 9.758.094.501,00 | 45.000,00 | 2028: bileşen sütunları 6, 7, 8 Kanıt: s.244 / u40c3i5faa / r12c6 = «4.434.456.289,00»; s.244 / u40c3i5faa / r12c7 = «4.713.638.212,00»; s.244 / u40c3i5faa / r12c8 = «610.000.000,00» |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 13 | 11.904.930.191,00 | 11.904.930.191,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 13 — Döner Sermaye | 5 | 0,00 | 0,00 | 0,00 | 2027: bileşen sütunları 2, 3, 4 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 13 — Döner Sermaye | 9 | 0,00 | 0,00 | 0,00 | 2028: bileşen sütunları 6, 7, 8 |
| PASS | — | Satır toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 13 — Döner Sermaye | 13 | 0,00 | 0,00 | 0,00 | 2029: bileşen sütunları 10, 11, 12 |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 2 | 3.634.800.237,00 | 3.634.800.237,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| FAIL | BOOK | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 3 | 4.263.174.763,00 | 3.764.174.763,00 | 499.000.000,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 Kanıt: s.244 / u40c3i5faa / r3c3 = «240.061.908,00»; s.244 / u40c3i5faa / r4c3 = «28.396.534,00»; s.244 / u40c3i5faa / r5c3 = «3.285.313.343,00»; s.244 / u40c3i5faa / r6c3 = «30.000.000,00»; s.244 / u40c3i5faa / r7c3 = «56.011.000,00»; s.244 / u40c3i5faa / r8c3 = «79.476.848,00»; s.244 / u40c3i5faa / r9c3 = «44.415.130,00»; s.244 / u40c3i5faa / r10c3 = «0,00»; s.244 / u40c3i5faa / r11c3 = «500.000,00» |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 4 | 600.000.000,00 | 600.000.000,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| FAIL | BOOK | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 5 | 7.998.475.000,00 | 7.973.475.000,00 | 25.000.000,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 Kanıt: s.244 / u40c3i5faa / r3c5 = «647.804.357,00»; s.244 / u40c3i5faa / r4c5 = «59.488.454,00»; s.244 / u40c3i5faa / r5c5 = «5.054.079.860,00»; s.244 / u40c3i5faa / r6c5 = «30.000.000,00»; s.244 / u40c3i5faa / r7c5 = «132.012.604,00»; s.244 / u40c3i5faa / r8c5 = «1.401.176.848,00»; s.244 / u40c3i5faa / r9c5 = «48.912.877,00»; s.244 / u40c3i5faa / r10c5 = «0,00»; s.244 / u40c3i5faa / r11c5 = «600.000.000,00» |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 6 | 4.434.456.289,00 | 4.434.456.289,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| FAIL | BOOK | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 7 | 4.713.638.212,00 | 5.323.683.212,00 | -610.045.000,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 Kanıt: s.244 / u40c3i5faa / r3c7 = «292.875.528,00»; s.244 / u40c3i5faa / r4c7 = «34.643.772,00»; s.244 / u40c3i5faa / r5c7 = «4.130.082.278,00»; s.244 / u40c3i5faa / r6c7 = «36.600.000,00»; s.244 / u40c3i5faa / r7c7 = «68.333.420,00»; s.244 / u40c3i5faa / r8c7 = «96.961.755,00»; s.244 / u40c3i5faa / r9c7 = «54.186.459,00»; s.244 / u40c3i5faa / r10c7 = «0,00»; s.244 / u40c3i5faa / r11c7 = «610.000.000,00» |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 8 | 610.000.000,00 | 610.000.000,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 9 | 9.758.139.501,00 | 9.758.139.501,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 10 | 5.410.036.673,00 | 5.410.036.673,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| FAIL | BOOK | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 11 | 5.750.693.518,00 | 6.494.893.518,00 | -744.200.000,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 Kanıt: s.244 / u40c3i5faa / r3c11 = «357.308.145,00»; s.244 / u40c3i5faa / r4c11 = «42.265.401,00»; s.244 / u40c3i5faa / r5c11 = «5.038.700.379,00»; s.244 / u40c3i5faa / r6c11 = «44.652.000,00»; s.244 / u40c3i5faa / r7c11 = «83.366.773,00»; s.244 / u40c3i5faa / r8c11 = «118.293.341,00»; s.244 / u40c3i5faa / r9c11 = «66.107.479,00»; s.244 / u40c3i5faa / r10c11 = «0,00»; s.244 / u40c3i5faa / r11c11 = «744.200.000,00» |
| PASS | — | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 12 | 744.200.000,00 | 744.200.000,00 | 0,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| FAIL | BOOK | Sütun toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 12 — BÜTÇE İÇİ TOPLAM KAYNAK | 13 | 11.904.930.191,00 | 11.160.730.191,00 | 744.200.000,00 | Kapsanan satırlar: 3, 4, 5, 6, 7, 8, 9, 10, 11 Kanıt: s.244 / u40c3i5faa / r3c13 = «964.192.006,00»; s.244 / u40c3i5faa / r4c13 = «88.542.615,00»; s.244 / u40c3i5faa / r5c13 = «7.708.542.463,00»; s.244 / u40c3i5faa / r6c13 = «44.652.000,00»; s.244 / u40c3i5faa / r7c13 = «196.487.560,00»; s.244 / u40c3i5faa / r8c13 = «2.085.511.621,00»; s.244 / u40c3i5faa / r9c13 = «72.801.926,00»; s.244 / u40c3i5faa / r10c13 = «0,00»; s.244 / u40c3i5faa / r11c13 = «0,00» |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 5 | 647.804.357,00 | 647.022.357,00 | 782.000,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Personel Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 2 | 407.742.449,00 | Bilinmiyor | Bilinmiyor | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 3 | 240.061.908,00 | Bilinmiyor | Bilinmiyor | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 4 | 0,00 | Bilinmiyor | Bilinmiyor | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 9 | 790.321.316,00 | 805.947.447,00 | -15.626.131,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Personel Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 6 | 497.445.788,00 | Bilinmiyor | Bilinmiyor | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 7 | 292.875.528,00 | Bilinmiyor | Bilinmiyor | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 8 | 0,00 | Bilinmiyor | Bilinmiyor | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 13 | 964.192.006,00 | 1.003.187.216,00 | -38.995.210,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Personel Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 10 | 606.883.861,00 | Bilinmiyor | Bilinmiyor | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 11 | 357.308.145,00 | Bilinmiyor | Bilinmiyor | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 3 — Personel Giderleri | 12 | 0,00 | Bilinmiyor | Bilinmiyor | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 5 | 59.488.454,00 | 53.703.454,00 | 5.785.000,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sosyal Güvenlik Kurumuna Devlet Primi Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 2 | 31.091.920,00 | Bilinmiyor | Bilinmiyor | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 3 | 28.396.534,00 | Bilinmiyor | Bilinmiyor | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 4 | 0,00 | Bilinmiyor | Bilinmiyor | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 9 | 72.575.914,00 | 66.880.070,00 | 5.695.844,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sosyal Güvenlik Kurumuna Devlet Primi Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 6 | 37.932.142,00 | Bilinmiyor | Bilinmiyor | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 7 | 34.643.772,00 | Bilinmiyor | Bilinmiyor | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 8 | 0,00 | Bilinmiyor | Bilinmiyor | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 13 | 88.542.615,00 | 83.283.041,00 | 5.259.574,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sosyal Güvenlik Kurumuna Devlet Primi Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 10 | 46.277.214,00 | Bilinmiyor | Bilinmiyor | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 11 | 42.265.401,00 | Bilinmiyor | Bilinmiyor | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 4 — Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | 12 | 0,00 | Bilinmiyor | Bilinmiyor | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 5 | 5.054.079.860,00 | 5.160.080.485,00 | -106.000.625,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Mal ve Hizmet Alım Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 2 | 1.793.766.517,00 | Bilinmiyor | Bilinmiyor | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 3 | 3.285.313.343,00 | Bilinmiyor | Bilinmiyor | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 4 | 0,00 | Bilinmiyor | Bilinmiyor | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 9 | 6.318.477.429,00 | 7.491.284.414,00 | -1.172.806.985,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Mal ve Hizmet Alım Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 6 | 2.188.395.151,00 | Bilinmiyor | Bilinmiyor | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 7 | 4.130.082.278,00 | Bilinmiyor | Bilinmiyor | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 8 | 0,00 | Bilinmiyor | Bilinmiyor | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 13 | 7.708.542.463,00 | 9.464.585.675,00 | -1.756.043.212,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Mal ve Hizmet Alım Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 10 | 2.669.842.084,00 | Bilinmiyor | Bilinmiyor | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 11 | 5.038.700.379,00 | Bilinmiyor | Bilinmiyor | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 5 — Mal ve Hizmet Alım Giderleri | 12 | 0,00 | Bilinmiyor | Bilinmiyor | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 5 | 30.000.000,00 | 30.000.000,00 | 0,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Faiz Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 2 | 0,00 | 0,00 | 0,00 | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 3 | 30.000.000,00 | 30.000.000,00 | 0,00 | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 4 | 0,00 | 0,00 | 0,00 | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 9 | 36.600.000,00 | 36.000.000,00 | 600.000,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Faiz Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 6 | 0,00 | 0,00 | 0,00 | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 7 | 36.600.000,00 | 36.000.000,00 | 600.000,00 | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 8 | 0,00 | 0,00 | 0,00 | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 13 | 44.652.000,00 | 43.200.000,00 | 1.452.000,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Faiz Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 10 | 0,00 | 0,00 | 0,00 | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 11 | 44.652.000,00 | 43.200.000,00 | 1.452.000,00 | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 6 — Faiz Giderleri | 12 | 0,00 | 0,00 | 0,00 | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 5 | 132.012.604,00 | 132.012.604,00 | 0,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Cari Transferler. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 2 | 76.001.604,00 | Bilinmiyor | Bilinmiyor | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 3 | 56.011.000,00 | Bilinmiyor | Bilinmiyor | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 4 | 0,00 | Bilinmiyor | Bilinmiyor | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 9 | 161.055.377,00 | 157.562.736,00 | 3.492.641,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Cari Transferler. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 6 | 92.721.957,00 | Bilinmiyor | Bilinmiyor | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 7 | 68.333.420,00 | Bilinmiyor | Bilinmiyor | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 8 | 0,00 | Bilinmiyor | Bilinmiyor | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 13 | 196.487.560,00 | 184.253.158,00 | 12.234.402,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Cari Transferler. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 10 | 113.120.787,00 | Bilinmiyor | Bilinmiyor | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 11 | 83.366.773,00 | Bilinmiyor | Bilinmiyor | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 7 — Cari Transferler | 12 | 0,00 | Bilinmiyor | Bilinmiyor | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 5 | 1.401.176.848,00 | 1.435.089.725,00 | -33.912.877,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 2 | 1.321.700.000,00 | Bilinmiyor | Bilinmiyor | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 3 | 79.476.848,00 | Bilinmiyor | Bilinmiyor | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 4 | 0,00 | Bilinmiyor | Bilinmiyor | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 9 | 1.709.435.755,00 | 2.398.885.303,00 | -689.449.548,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 6 | 1.612.474.000,00 | Bilinmiyor | Bilinmiyor | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 7 | 96.961.755,00 | Bilinmiyor | Bilinmiyor | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 8 | 0,00 | Bilinmiyor | Bilinmiyor | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 13 | 2.085.511.621,00 | 2.852.656.593,00 | -767.144.972,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Giderleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 10 | 1.967.218.280,00 | Bilinmiyor | Bilinmiyor | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 11 | 118.293.341,00 | Bilinmiyor | Bilinmiyor | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | CHECK | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 8 — Sermaye Giderleri | 12 | 0,00 | Bilinmiyor | Bilinmiyor | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 5 | 48.912.877,00 | 40.000.000,00 | 8.912.877,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Transferleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 2 | 4.497.747,00 | 0,00 | 4.497.747,00 | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 3 | 44.415.130,00 | 40.000.000,00 | 4.415.130,00 | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 4 | 0,00 | 0,00 | 0,00 | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 9 | 59.673.710,00 | 48.000.000,00 | 11.673.710,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Transferleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 6 | 5.487.251,00 | 0,00 | 5.487.251,00 | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 7 | 54.186.459,00 | 48.000.000,00 | 6.186.459,00 | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 8 | 0,00 | 0,00 | 0,00 | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 13 | 72.801.926,00 | 57.600.000,00 | 15.201.926,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Sermaye Transferleri. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 10 | 6.694.447,00 | 0,00 | 6.694.447,00 | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| FAIL | UNKNOWN | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 11 | 66.107.479,00 | 57.600.000,00 | 8.507.479,00 | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 9 — Sermaye Transferleri | 12 | 0,00 | 0,00 | 0,00 | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 5 | 0,00 | 0,00 | 0,00 | 2027: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Borç Verme. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 2 | 0,00 | 0,00 | 0,00 | 2027: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 3 | 0,00 | 0,00 | 0,00 | 2027: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 4 | 0,00 | 0,00 | 0,00 | 2027: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 9 | 0,00 | 0,00 | 0,00 | 2028: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Borç Verme. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 6 | 0,00 | 0,00 | 0,00 | 2028: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 7 | 0,00 | 0,00 | 0,00 | 2028: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 8 | 0,00 | 0,00 | 0,00 | 2028: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük ekonomik çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 13 | 0,00 | 0,00 | 0,00 | 2029: tüm müdürlük ekonomik tablolarının bütçe içi tutarları; kategori=Borç Verme. Kaynak inceleme durumları değiştirilmez; verilmeyen kategori satırları kapsama alınmaz. Kaynak hücresi / ayrıştırılmış değer eşleşmiyorsa hesap doğrulanamaz (CHECK). Sayısal fark varsa hangi basılı tutarın yanlış olduğu veya ileri yıl dağılım yöntemi kaynaktan belirlenemez (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 10 | 0,00 | 0,00 | 0,00 | 2029: HİZMET PROGRAMLARI TOPLAM. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 11 | 0,00 | 0,00 | 0,00 | 2029: YÖNETİM VE DESTEK PROGRAMI. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Müdürlük program grubu çapraz toplamı | 244 | u40c3i5faa — Ekonomik kod / program grupları | 10 — Borç Verme | 12 | 0,00 | 0,00 | 0,00 | 2029: PROGRAM DIŞI GİDERLER. Birden çok program grubunu içeren müdürlüklerde kategori dağılımı kitapta yoksa hesaplanamaz (CHECK); paylaştırma yapılmadı. Sayısal fark tek başına kitap hatası kanıtı değildir (UNKNOWN). |
| PASS | — | Sütun toplamı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 38 — TOPLAM | 2 | 7.998.475.000,00 | 7.998.475.000,00 | 0,00 | Kapsanan satırlar: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37 |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 2 — ÖZEL KALEM MÜDÜRLÜĞÜ | 3 | 0,72 | 0,722638 | -0,002638 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 3 — REHBERLİK VE TEFTİŞ KURULU MÜDÜRLÜĞÜ | 3 | 0,02 | 0,022496 | -0,002496 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 4 — HUKUK İŞLERİ MÜDÜRLÜĞÜ | 3 | 0,62 | 0,618646 | 0,001354 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 5 — YAZI İŞLERİ MÜDÜRLÜĞÜ | 3 | 0,51 | 0,512924 | -0,002924 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 6 — MALİ HİZMETLER MÜDÜRLÜĞÜ | 3 | 11,1 | 11,10492 | -0,00492 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 7 — İNSAN KAYNAKLARI VE EĞİTİM MÜDÜRLÜĞÜ | 3 | 0,39 | 0,39265 | -0,00265 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 8 — DESTEK HİZMETLERİ MÜDÜRLÜĞÜ | 3 | 32,93 | 32,93312 | -0,00312 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 9 — BİLGİ İŞLEM MÜDÜRLÜĞÜ | 3 | 3,54 | 3,535835 | 0,004165 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 10 — ZABITA MÜDÜRLÜĞÜ | 3 | 1,47 | 1,472608 | -0,002608 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 11 — İMAR VE ŞEHİRCİLİK MÜDÜRLÜĞÜ | 3 | 0,69 | 0,692096 | -0,002096 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 12 — FEN İŞLERİ MÜDÜRLÜĞÜ | 3 | 15,46 | 15,458433 | 0,001567 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 13 — İKLİM DEĞİŞİKLİĞİ VE SIFIR ATIK MÜDÜRLÜĞÜ | 3 | 0,03 | 0,028143 | 0,001857 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 14 — AFET İŞLERİ VE RİSK YÖNETİMİ MÜDÜRLÜĞÜ | 3 | 0,38 | 0,383876 | -0,003876 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 15 — VETERİNER İŞLERİ MÜDÜRLÜĞÜ | 3 | 0,98 | 0,979984 | 0,000016 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 16 — ÇEVRE KORUMA VE KONTROL MÜDÜRLÜĞÜ | 3 | 0,15 | 0,148959 | 0,001041 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 17 — STRATEJİ GELİŞTİRME MÜDÜRLÜĞÜ | 3 | 0,07 | 0,073309 | -0,003309 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 18 — BASIN, YAYIN VE HALKLA İLİŞKİLER MÜDÜRLÜĞÜ | 3 | 0,82 | 0,82351 | -0,00351 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 19 — DIŞ İLİŞKİLER MÜDÜRLÜĞÜ | 3 | 0,08 | 0,081447 | -0,001447 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 20 — EMLAK VE İSTİMLAK MÜDÜRLÜĞÜ | 3 | 3,31 | 3,310563 | -0,000563 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 21 — ETÜT VE PROJE MÜDÜRLÜĞÜ | 3 | 0,15 | 0,148753 | 0,001247 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 22 — SOSYAL HİZMETLER MÜDÜRLÜĞÜ | 3 | 0,9 | 0,904928 | -0,004928 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 23 — SAĞLIK İŞLERİ MÜDÜRLÜĞÜ | 3 | 0,43 | 0,433001 | -0,003001 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 24 — KÜLTÜR, SANAT VE SOSYAL İŞLER MÜDÜRLÜĞÜ | 3 | 1,19 | 1,189391 | 0,000609 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 25 — MAKİNE İKMAL, BAKIM VE ONARIM MÜDÜRLÜĞÜ | 3 | 2,61 | 2,610379 | -0,000379 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 26 — GENÇLİK VE SPOR HİZMETLERİ MÜDÜRLÜĞÜ | 3 | 0,77 | 0,765141 | 0,004859 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 27 — PARK VE BAHÇELER MÜDÜRLÜĞÜ | 3 | 6,89 | 6,892564 | -0,002564 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 28 — TARIMSAL HİZMETLER MÜDÜRLÜĞÜ | 3 | 0,19 | 0,191127 | -0,001127 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 29 — KENTSEL DÖNÜŞÜM MÜDÜRLÜĞÜ | 3 | 0,22 | 0,220739 | -0,000739 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 30 — KADIN VE AİLE HİZMETLERİ MÜDÜRLÜĞÜ | 3 | 0 | 0 | 0 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 31 — KENTSEL TASARIM MÜDÜRLÜĞÜ | 3 | 0 | 0 | 0 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 32 — TEMİZLİK İŞLERİ MÜDÜRLÜĞÜ | 3 | 10,66 | 10,656256 | 0,003744 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 33 — RUHSAT VE DENETİM MÜDÜRLÜĞÜ | 3 | 0,18 | 0,181892 | -0,001892 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 34 — GELİRLER MÜDÜRLÜĞÜ | 3 | 0,84 | 0,837266 | 0,002734 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 35 — HARİTA VE PLANLAMA MÜDÜRLÜĞÜ | 3 | 0,41 | 0,411553 | -0,001553 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 36 — AR-GE MÜDÜRLÜĞÜ | 3 | 0,07 | 0,068701 | 0,001299 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 37 — İŞLETME İŞTİRAKLER MÜDÜRLÜĞÜ | 3 | 1,19 | 1,192152 | -0,002152 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzde oranı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 38 — TOPLAM | 3 | 100 | 100 | 0 | Tutar / basılı genel toplam × 100; basılı ondalık basamağa yuvarlanır. |
| PASS | — | Yüzdeler toplamı | 246 | u4336i5f94 — Müdürlük bütçeleri ve toplam bütçeye oranı | 38 — TOPLAM | 3 | 100 | 99,97 | 0,03 | Yuvarlama toleransı: 0,18; hesaplanan = satır yüzdeleri toplamı. |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 4 | 1.132.975.122,00 | 1.132.975.122,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 7 | 1.464.002.665,00 | 1.464.002.665,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 10 | 1.767.927.554,00 | 1.767.927.554,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 4 | 1.089.920.835,00 | 1.089.920.835,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 7 | 1.398.412.510,00 | 1.398.412.510,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 10 | 1.690.925.768,00 | 1.690.925.768,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 5 — Yeni bina projelerinin uygulanması | 4 | 85.152.000,00 | 85.152.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 5 — Yeni bina projelerinin uygulanması | 7 | 133.500.000,00 | 133.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 5 — Yeni bina projelerinin uygulanması | 10 | 160.515.475,00 | 160.515.475,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 6 — Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 4 | 105.192.000,00 | 105.192.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 6 — Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 7 | 168.700.000,00 | 168.700.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 6 — Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 10 | 202.756.389,00 | 202.756.389,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 7 — Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 4 | 30.048.000,00 | 30.048.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 7 — Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 7 | 42.200.000,00 | 42.200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 7 — Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 10 | 50.689.097,00 | 50.689.097,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 8 — Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 4 | 5.008.000,00 | 5.008.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 8 — Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 7 | 7.645.208,00 | 7.645.208,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 8 — Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 10 | 9.124.037,00 | 9.124.037,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 9 — Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 4 | 232.904.967,00 | 232.904.967,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 9 — Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 7 | 215.198.462,00 | 215.198.462,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 9 — Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 10 | 260.974.404,00 | 260.974.404,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 10 — Raporlardaki tespitlerin ayrıntılı analizi | 4 | 232.904.967,00 | 232.904.967,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 10 — Raporlardaki tespitlerin ayrıntılı analizi | 7 | 215.198.460,00 | 215.198.460,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 10 — Raporlardaki tespitlerin ayrıntılı analizi | 10 | 260.974.402,00 | 260.974.402,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 11 — Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 4 | 132.904.967,00 | 132.904.967,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 11 — Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 7 | 215.198.460,00 | 215.198.460,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 11 — Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 10 | 260.974.402,00 | 260.974.402,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 12 — Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 4 | 132.904.967,00 | 132.904.967,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 12 — Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 7 | 215.198.460,00 | 215.198.460,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 12 — Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 10 | 260.974.402,00 | 260.974.402,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 13 — Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 4 | 132.904.967,00 | 132.904.967,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 13 — Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 7 | 215.198.460,00 | 215.198.460,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 13 — Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 10 | 260.974.402,00 | 260.974.402,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 4 | 39.039.548,00 | 39.039.548,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 7 | 59.320.481,00 | 59.320.481,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 10 | 69.683.393,00 | 69.683.393,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 15 — Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 4 | 1.489.548,00 | 1.489.548,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 15 — Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 7 | 1.589.548,00 | 1.589.548,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 15 — Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 10 | 1.624.067,00 | 1.624.067,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 16 — Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 4 | 400.000,00 | 400.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 16 — Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 7 | 530.933,00 | 530.933,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 16 — Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 10 | 530.933,00 | 530.933,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 17 — Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 4 | 700.000,00 | 700.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 17 — Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 7 | 800.000,00 | 800.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 17 — Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 10 | 800.000,00 | 800.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 18 — Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 4 | 1.450.000,00 | 1.450.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 18 — Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 7 | 1.650.000,00 | 1.650.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 18 — Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 10 | 1.650.000,00 | 1.650.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 19 — Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 4 | 15.000.000,00 | 15.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 19 — Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 7 | 21.875.000,00 | 21.875.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 19 — Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 10 | 25.630.000,00 | 25.630.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 20 — Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 4 | 2.500.000,00 | 2.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 20 — Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 7 | 3.125.000,00 | 3.125.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 20 — Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 10 | 3.630.000,00 | 3.630.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 21 — Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 4 | 5.000.000,00 | 5.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 21 — Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 7 | 9.375.000,00 | 9.375.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 21 — Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 10 | 10.930.000,00 | 10.930.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 22 — Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 4 | 2.500.000,00 | 2.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 22 — Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 7 | 3.125.000,00 | 3.125.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 22 — Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 10 | 3.630.000,00 | 3.630.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 23 — Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 4 | 1.500.000,00 | 1.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 23 — Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 7 | 3.125.000,00 | 3.125.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 23 — Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 10 | 3.630.000,00 | 3.630.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 24 — Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 4 | 1.500.000,00 | 1.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 24 — Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 7 | 3.125.000,00 | 3.125.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 24 — Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 10 | 3.630.000,00 | 3.630.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 25 — Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 25 — Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 7 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 25 — Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 10 | 4.425.000,00 | 4.425.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 26 — Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 4 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 26 — Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 7 | 6.250.000,00 | 6.250.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 26 — Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 10 | 7.260.000,00 | 7.260.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 4 | 4.015.739,00 | 4.015.739,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 7 | 6.269.674,00 | 6.269.674,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 10 | 7.318.393,00 | 7.318.393,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 28 — Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 28 — Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 7 | 3.750.000,00 | 3.750.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 28 — Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 10 | 4.368.393,00 | 4.368.393,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 29 — Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 4 | 2.015.739,00 | 2.015.739,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 29 — Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 7 | 2.519.674,00 | 2.519.674,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 29 — Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 10 | 2.950.000,00 | 2.950.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 4 | 3.400.000,00 | 3.400.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 7 | 3.650.000,00 | 3.650.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 10 | 3.527.500,00 | 3.527.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 4 | 3.400.000,00 | 3.400.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 7 | 3.650.000,00 | 3.650.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 10 | 3.527.500,00 | 3.527.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 32 — Belirlenen çağrılar için proje fikirlerinin geliştirilmesi ve proje başvurularının hazırlanması | 4 | 984.000,00 | 984.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 32 — Belirlenen çağrılar için proje fikirlerinin geliştirilmesi ve proje başvurularının hazırlanması | 7 | 936.000,00 | 936.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 32 — Belirlenen çağrılar için proje fikirlerinin geliştirilmesi ve proje başvurularının hazırlanması | 10 | 897.500,00 | 897.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 33 — Proje yazımı, bütçeleme ve uygulama süreçlerine ilişkin kurum içi bilgilendirme ve kapasite geliştirme | 4 | 1.456.000,00 | 1.456.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 33 — Proje yazımı, bütçeleme ve uygulama süreçlerine ilişkin kurum içi bilgilendirme ve kapasite geliştirme | 7 | 1.794.000,00 | 1.794.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 33 — Proje yazımı, bütçeleme ve uygulama süreçlerine ilişkin kurum içi bilgilendirme ve kapasite geliştirme | 10 | 1.430.000,00 | 1.430.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 34 — Yerel hizmetlere yönelik iş analizi, süreç analizi ve fizibilite çalışmalarının gerçekleştirilmesi | 4 | 960.000,00 | 960.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 34 — Yerel hizmetlere yönelik iş analizi, süreç analizi ve fizibilite çalışmalarının gerçekleştirilmesi | 7 | 920.000,00 | 920.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 34 — Yerel hizmetlere yönelik iş analizi, süreç analizi ve fizibilite çalışmalarının gerçekleştirilmesi | 10 | 1.200.000,00 | 1.200.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 4 | 810.844.764,00 | 810.844.764,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 7 | 1.182.029.090,50 | 1.182.029.090,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 10 | 1.411.393.421,00 | 1.411.393.421,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 4 | 785.740.921,00 | 785.740.921,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 7 | 1.155.046.041,50 | 1.155.046.041,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 10 | 1.385.040.627,00 | 1.385.040.627,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 37 — Kamulaştırma işlemleri ve fiili el atmalardan kaynaklı mahkeme kararlarının uygulanması (2942 s.k.) | 4 | 179.000.000,00 | 179.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 37 — Kamulaştırma işlemleri ve fiili el atmalardan kaynaklı mahkeme kararlarının uygulanması (2942 s.k.) | 7 | 236.250.000,00 | 236.250.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 37 — Kamulaştırma işlemleri ve fiili el atmalardan kaynaklı mahkeme kararlarının uygulanması (2942 s.k.) | 10 | 283.500.000,00 | 283.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 38 — 2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takiplerinin yapılması | 4 | 13.050.000,00 | 13.050.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 38 — 2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takiplerinin yapılması | 7 | 16.250.000,00 | 16.250.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 38 — 2886 sayılı yasa kapsamında kiralama işlemleri ile tahakkuk borç takiplerinin yapılması | 10 | 18.800.000,00 | 18.800.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 39 — 4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması | 4 | 5.500.000,00 | 5.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 39 — 4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması | 7 | 7.000.000,00 | 7.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 39 — 4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması | 10 | 8.300.000,00 | 8.300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 40 — Semt pazarları tahsis işlemlerinin yapılması | 4 | 984.658,00 | 984.658,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 40 — Semt pazarları tahsis işlemlerinin yapılması | 7 | 1.168.323,00 | 1.168.323,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 40 — Semt pazarları tahsis işlemlerinin yapılması | 10 | 1.366.584,00 | 1.366.584,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 41 — Diğer kamu kurum ve kuruluşları ile belediyemiz arasında irtifak/intifa, tahsis, kira ve devir işlemleri | 4 | 52.000.000,00 | 52.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 41 — Diğer kamu kurum ve kuruluşları ile belediyemiz arasında irtifak/intifa, tahsis, kira ve devir işlemleri | 7 | 65.000.000,00 | 65.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 41 — Diğer kamu kurum ve kuruluşları ile belediyemiz arasında irtifak/intifa, tahsis, kira ve devir işlemleri | 10 | 78.000.000,00 | 78.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 42 — 1/5000 nazım planlar doğrultusunda etaplar halinde uygulama imar planı ve değişiklikleri yapılması | 4 | 4.134.625,00 | 4.134.625,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 42 — 1/5000 nazım planlar doğrultusunda etaplar halinde uygulama imar planı ve değişiklikleri yapılması | 7 | 5.972.384,00 | 5.972.384,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 42 — 1/5000 nazım planlar doğrultusunda etaplar halinde uygulama imar planı ve değişiklikleri yapılması | 10 | 3.395.323,00 | 3.395.323,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 43 — Akıllı otomatik sulama sistemlerinin kurulumu, bakım ve onarımı | 4 | 60.133.709,00 | 60.133.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 43 — Akıllı otomatik sulama sistemlerinin kurulumu, bakım ve onarımı | 7 | 150.000.000,00 | 150.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 43 — Akıllı otomatik sulama sistemlerinin kurulumu, bakım ve onarımı | 10 | 150.000.000,00 | 150.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 44 — İmar planında park ve yeşil alan olarak ayrılan alanların projelendirilerek kente kazandırılması | 4 | 60.133.709,00 | 60.133.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 44 — İmar planında park ve yeşil alan olarak ayrılan alanların projelendirilerek kente kazandırılması | 7 | 150.000.000,00 | 150.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 44 — İmar planında park ve yeşil alan olarak ayrılan alanların projelendirilerek kente kazandırılması | 10 | 150.000.000,00 | 150.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 45 — Ekonomik ömrünü tamamlamış park ve peyzaj alanlarının revize edilmesi, bakımı ve onarımı | 4 | 70.133.709,00 | 70.133.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 45 — Ekonomik ömrünü tamamlamış park ve peyzaj alanlarının revize edilmesi, bakımı ve onarımı | 7 | 201.091.978,00 | 201.091.978,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 45 — Ekonomik ömrünü tamamlamış park ve peyzaj alanlarının revize edilmesi, bakımı ve onarımı | 10 | 150.000.000,00 | 150.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 46 — Bitkilendirme, budama, gübreleme ve çim biçimi gibi rutin peyzaj bakımlarının yapılması | 4 | 70.133.709,00 | 70.133.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 46 — Bitkilendirme, budama, gübreleme ve çim biçimi gibi rutin peyzaj bakımlarının yapılması | 7 | 37.653.411,00 | 37.653.411,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 46 — Bitkilendirme, budama, gübreleme ve çim biçimi gibi rutin peyzaj bakımlarının yapılması | 10 | 47.066.763,00 | 47.066.763,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 47 — Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi | 4 | 235.172,00 | 235.172,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 47 — Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi | 7 | 1.022.667,00 | 1.022.667,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 47 — Ruhsat ve iskân aşamasındaki yapıların peyzaj projelerinin incelenmesi, onaylanması ve denetimi | 10 | 2.019.444,00 | 2.019.444,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 48 — Malzeme, araç ve gereçlerin temini ve yönetimi (Park ve Bahçeler) | 4 | 45.333.709,00 | 45.333.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 48 — Malzeme, araç ve gereçlerin temini ve yönetimi (Park ve Bahçeler) | 7 | 166.398.994,00 | 166.398.994,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 48 — Malzeme, araç ve gereçlerin temini ve yönetimi (Park ve Bahçeler) | 10 | 160.000.000,00 | 160.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 49 — Kırılgan grupların kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı | 4 | 45.333.709,00 | 45.333.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 49 — Kırılgan grupların kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı | 7 | 100.586.604,00 | 100.586.604,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 49 — Kırılgan grupların kullanabileceği ortak alanların oluşturulması, bakımı ve onarımı | 10 | 100.000.000,00 | 100.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 50 — Ağaçlandırma çalışmaları ve biyolojik çeşitliliğin korunması | 4 | 70.133.709,00 | 70.133.709,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 50 — Ağaçlandırma çalışmaları ve biyolojik çeşitliliğin korunması | 7 | 100.586.605,00 | 100.586.605,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 50 — Ağaçlandırma çalışmaları ve biyolojik çeşitliliğin korunması | 10 | 100.000.000,00 | 100.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 51 — Ekonomik ömrünü tamamlamış park donatılarının yenilenmesi | 4 | 71.532.023,00 | 71.532.023,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 51 — Ekonomik ömrünü tamamlamış park donatılarının yenilenmesi | 7 | 82.220.822,00 | 82.220.822,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 51 — Ekonomik ömrünü tamamlamış park donatılarının yenilenmesi | 10 | 90.000.000,00 | 90.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 52 — Yeni nesil çocuk oyun alanlarının kurulumu | 4 | 9.305.773,00 | 9.305.773,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 52 — Yeni nesil çocuk oyun alanlarının kurulumu | 7 | 9.770.824,00 | 9.770.824,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 52 — Yeni nesil çocuk oyun alanlarının kurulumu | 10 | 10.000.000,00 | 10.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 53 — Engelsiz kent mobilyaları ve erişilebilirlik uygulamaları | 4 | 7.055.773,00 | 7.055.773,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 53 — Engelsiz kent mobilyaları ve erişilebilirlik uygulamaları | 7 | 5.240.769,00 | 5.240.769,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 53 — Engelsiz kent mobilyaları ve erişilebilirlik uygulamaları | 10 | 6.776.029,00 | 6.776.029,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 54 — Açık hava spor ve fitness alanları kurulumu | 4 | 9.005.773,00 | 9.005.773,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 54 — Açık hava spor ve fitness alanları kurulumu | 7 | 6.970.824,00 | 6.970.824,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 54 — Açık hava spor ve fitness alanları kurulumu | 10 | 7.000.000,00 | 7.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 55 — Meydan düzenleme ve kentsel sanat uygulamaları | 4 | 8.805.773,00 | 8.805.773,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 55 — Meydan düzenleme ve kentsel sanat uygulamaları | 7 | 11.170.824,00 | 11.170.824,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 55 — Meydan düzenleme ve kentsel sanat uygulamaları | 10 | 12.099.694,00 | 12.099.694,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 56 — Sigara içme alanı talep ve müracaatlarının değerlendirilmesi | 4 | 200.000,00 | 200.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 56 — Sigara içme alanı talep ve müracaatlarının değerlendirilmesi | 7 | 0,00 | 0,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 56 — Sigara içme alanı talep ve müracaatlarının değerlendirilmesi | 10 | 0,00 | 0,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 57 — Tabela talep ve müracaatlarının değerlendirilmesi | 4 | 200.000,00 | 200.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 57 — Tabela talep ve müracaatlarının değerlendirilmesi | 7 | 0,00 | 0,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 57 — Tabela talep ve müracaatlarının değerlendirilmesi | 10 | 0,00 | 0,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 58 — Kentsel tasarım ilintili meydan, cadde, sokak projelerinin hazırlanması | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 58 — Kentsel tasarım ilintili meydan, cadde, sokak projelerinin hazırlanması | 7 | 625.000,00 | 625.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 58 — Kentsel tasarım ilintili meydan, cadde, sokak projelerinin hazırlanması | 10 | 781.250,00 | 781.250,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 59 — Kentsel dönüşüm vatandaş bilgilendirme toplantıları | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 59 — Kentsel dönüşüm vatandaş bilgilendirme toplantıları | 7 | 750.000,00 | 750.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 59 — Kentsel dönüşüm vatandaş bilgilendirme toplantıları | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 60 — Kentsel dönüşümde riskli yapılara ilişkin iş ve işlemlerin gerçekleştirilmesi | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 60 — Kentsel dönüşümde riskli yapılara ilişkin iş ve işlemlerin gerçekleştirilmesi | 7 | 3.500.000,00 | 3.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 60 — Kentsel dönüşümde riskli yapılara ilişkin iş ve işlemlerin gerçekleştirilmesi | 10 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 61 — Kentsel dönüşüm personeli için eğitim programları düzenleme | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 61 — Kentsel dönüşüm personeli için eğitim programları düzenleme | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 61 — Kentsel dönüşüm personeli için eğitim programları düzenleme | 10 | 1.812.500,00 | 1.812.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 62 — Kentsel dönüşüm planlama ve strateji geliştirme | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 62 — Kentsel dönüşüm planlama ve strateji geliştirme | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 62 — Kentsel dönüşüm planlama ve strateji geliştirme | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 4 | 4.400.000,00 | 4.400.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 7 | 5.500.000,00 | 5.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 10 | 6.575.000,00 | 6.575.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 64 — İmar planlama ve uygulama faaliyetleri | 4 | 240.000,00 | 240.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 64 — İmar planlama ve uygulama faaliyetleri | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 64 — İmar planlama ve uygulama faaliyetleri | 10 | 345.000,00 | 345.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 65 — Yapı ruhsatlandırma ve iskân işlemleri | 4 | 240.000,00 | 240.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 65 — Yapı ruhsatlandırma ve iskân işlemleri | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 65 — Yapı ruhsatlandırma ve iskân işlemleri | 10 | 345.000,00 | 345.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 66 — İmar mevzuatı denetim ve kontrol faaliyetleri | 4 | 240.000,00 | 240.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 66 — İmar mevzuatı denetim ve kontrol faaliyetleri | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 66 — İmar mevzuatı denetim ve kontrol faaliyetleri | 10 | 345.000,00 | 345.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 67 — Vatandaş ve paydaş hizmetleri yönetimi (İmar) | 4 | 240.000,00 | 240.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 67 — Vatandaş ve paydaş hizmetleri yönetimi (İmar) | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 67 — Vatandaş ve paydaş hizmetleri yönetimi (İmar) | 10 | 345.000,00 | 345.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 68 — Kurumsal yazışma ve süreç koordinasyonu (İmar) | 4 | 240.000,00 | 240.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 68 — Kurumsal yazışma ve süreç koordinasyonu (İmar) | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 68 — Kurumsal yazışma ve süreç koordinasyonu (İmar) | 10 | 345.000,00 | 345.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 69 — Yapı süreci denetimleri | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 69 — Yapı süreci denetimleri | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 69 — Yapı süreci denetimleri | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 70 — Kaçak ve ruhsata aykırı yapılaşmayla mücadele | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 70 — Kaçak ve ruhsata aykırı yapılaşmayla mücadele | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 70 — Kaçak ve ruhsata aykırı yapılaşmayla mücadele | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 71 — Yapı kullanma izin belgesi işlemleri | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 71 — Yapı kullanma izin belgesi işlemleri | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 71 — Yapı kullanma izin belgesi işlemleri | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 72 — Şikâyet ve başvuruların değerlendirilmesi (İmar/Yapı Kontrol) | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 72 — Şikâyet ve başvuruların değerlendirilmesi (İmar/Yapı Kontrol) | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 72 — Şikâyet ve başvuruların değerlendirilmesi (İmar/Yapı Kontrol) | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 73 — Yıkım işlemleri | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 73 — Yıkım işlemleri | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 73 — Yıkım işlemleri | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 74 — Yapı denetim kuruluşlarıyla koordinasyon | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 74 — Yapı denetim kuruluşlarıyla koordinasyon | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 74 — Yapı denetim kuruluşlarıyla koordinasyon | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 75 — Mahkeme ve hukuki süreçlere ilişkin işlemler (İmar) | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 75 — Mahkeme ve hukuki süreçlere ilişkin işlemler (İmar) | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 75 — Mahkeme ve hukuki süreçlere ilişkin işlemler (İmar) | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 76 — Arşiv ve kayıt işlemleri (İmar) | 4 | 150.000,00 | 150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 76 — Arşiv ve kayıt işlemleri (İmar) | 7 | 187.500,00 | 187.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 76 — Arşiv ve kayıt işlemleri (İmar) | 10 | 215.625,00 | 215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 77 — Mahalle bazlı fizibilite ve etüt çalışmaları | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 77 — Mahalle bazlı fizibilite ve etüt çalışmaları | 7 | 1.250.000,00 | 1.250.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 77 — Mahalle bazlı fizibilite ve etüt çalışmaları | 10 | 1.562.500,00 | 1.562.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 78 — Eğitim tesisi projeleri etüt ve tasarımı | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 78 — Eğitim tesisi projeleri etüt ve tasarımı | 7 | 625.000,00 | 625.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 78 — Eğitim tesisi projeleri etüt ve tasarımı | 10 | 781.250,00 | 781.250,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 79 — Sosyal tesis projeleri etüt ve tasarımı | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 79 — Sosyal tesis projeleri etüt ve tasarımı | 7 | 625.000,00 | 625.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 79 — Sosyal tesis projeleri etüt ve tasarımı | 10 | 781.250,00 | 781.250,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 4 | 20.703.843,00 | 20.703.843,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 7 | 21.483.049,00 | 21.483.049,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 10 | 19.777.794,00 | 19.777.794,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 81 — Afet risk değerlendirme toplantıları | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 81 — Afet risk değerlendirme toplantıları | 7 | 500.000,00 | 500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 81 — Afet risk değerlendirme toplantıları | 10 | 500.000,00 | 500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 82 — Risk azaltma çalışmaları | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 82 — Risk azaltma çalışmaları | 7 | 500.000,00 | 500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 82 — Risk azaltma çalışmaları | 10 | 500.000,00 | 500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 83 — Afet ve acil durum eylem planı hazırlık çalışmaları | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 83 — Afet ve acil durum eylem planı hazırlık çalışmaları | 7 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 83 — Afet ve acil durum eylem planı hazırlık çalışmaları | 10 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 84 — İlçe genelinde afet haberleşme sisteminin kurulması | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 84 — İlçe genelinde afet haberleşme sisteminin kurulması | 7 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 84 — İlçe genelinde afet haberleşme sisteminin kurulması | 10 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 85 — Kurumlar arası iş birliği ve koordinasyonun güçlendirilmesi | 4 | 134.614,00 | 134.614,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 85 — Kurumlar arası iş birliği ve koordinasyonun güçlendirilmesi | 7 | 816.524,50 | 816.524,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 85 — Kurumlar arası iş birliği ve koordinasyonun güçlendirilmesi | 10 | 326.397,00 | 326.397,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 86 — Afet müdahale ve hasar tespit çalışma grubu için sektörleme | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 86 — Afet müdahale ve hasar tespit çalışma grubu için sektörleme | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 86 — Afet müdahale ve hasar tespit çalışma grubu için sektörleme | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 87 — Acil durum eylem planı geliştirme projesi | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 87 — Acil durum eylem planı geliştirme projesi | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 87 — Acil durum eylem planı geliştirme projesi | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 88 — Kırılgan gruplara afet bilinci eğitimi verme projesi | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 88 — Kırılgan gruplara afet bilinci eğitimi verme projesi | 7 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 88 — Kırılgan gruplara afet bilinci eğitimi verme projesi | 10 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 89 — Afet tatbikatları düzenleme ve tatbikatlara katılma | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 89 — Afet tatbikatları düzenleme ve tatbikatlara katılma | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 89 — Afet tatbikatları düzenleme ve tatbikatlara katılma | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 90 — Afet yönetimiyle ilgili çalışanların bilgi ve becerilerini geliştirmek | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 90 — Afet yönetimiyle ilgili çalışanların bilgi ve becerilerini geliştirmek | 7 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 90 — Afet yönetimiyle ilgili çalışanların bilgi ve becerilerini geliştirmek | 10 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 91 — Kent sakinlerini afetler hakkında bilgilendirme ve bilinçlendirme | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 91 — Kent sakinlerini afetler hakkında bilgilendirme ve bilinçlendirme | 7 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 91 — Kent sakinlerini afetler hakkında bilgilendirme ve bilinçlendirme | 10 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 92 — Kapsamlı afet bilinçlendirme projesi | 4 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 92 — Kapsamlı afet bilinçlendirme projesi | 7 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 92 — Kapsamlı afet bilinçlendirme projesi | 10 | 4.000.000,00 | 4.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 93 — Kurum personelinin afet eğitimi projesi | 4 | 134.615,00 | 134.615,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 93 — Kurum personelinin afet eğitimi projesi | 7 | 816.524,50 | 816.524,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 93 — Kurum personelinin afet eğitimi projesi | 10 | 326.397,00 | 326.397,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 94 — Okullarda, kamu kurumlarında ve işletmelerde afet eğitimi | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 94 — Okullarda, kamu kurumlarında ve işletmelerde afet eğitimi | 7 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 94 — Okullarda, kamu kurumlarında ve işletmelerde afet eğitimi | 10 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 4 | 828.638.909,00 | 828.638.909,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 7 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 10 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 4 | 828.638.909,00 | 828.638.909,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 7 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 10 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 97 — Yeni sokak yapılması ve mevcut sokakların sağlamlaştırılması (bisiklet/yaya yolu, asfalt vb.) | 4 | 758.571.936,00 | 758.571.936,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 97 — Yeni sokak yapılması ve mevcut sokakların sağlamlaştırılması (bisiklet/yaya yolu, asfalt vb.) | 7 | 1.516.492.252,00 | 1.516.492.252,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 97 — Yeni sokak yapılması ve mevcut sokakların sağlamlaştırılması (bisiklet/yaya yolu, asfalt vb.) | 10 | 1.819.419.408,00 | 1.819.419.408,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 98 — Yeni altyapı yapılması ve mevcut altyapının sağlamlaştırılması (yağmur suyu vb.) | 4 | 70.066.973,00 | 70.066.973,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 98 — Yeni altyapı yapılması ve mevcut altyapının sağlamlaştırılması (yağmur suyu vb.) | 7 | 98.415.194,00 | 98.415.194,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 98 — Yeni altyapı yapılması ve mevcut altyapının sağlamlaştırılması (yağmur suyu vb.) | 10 | 118.074.137,00 | 118.074.137,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 4 | 144.100.000,00 | 144.100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 7 | 213.658.966,00 | 213.658.966,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 10 | 256.580.170,00 | 256.580.170,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 4 | 136.100.000,00 | 136.100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 7 | 203.658.966,00 | 203.658.966,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 10 | 244.080.170,00 | 244.080.170,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 101 — Larva ve erişkin vektör mücadelesi çalışmaları | 4 | 6.000.000,00 | 6.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 101 — Larva ve erişkin vektör mücadelesi çalışmaları | 7 | 6.828.579,00 | 6.828.579,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 101 — Larva ve erişkin vektör mücadelesi çalışmaları | 10 | 7.000.000,00 | 7.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 102 — Sokak sağlamlaştırmada aydınlatma projelerinin uygulanması | 4 | 60.050.000,00 | 60.050.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 102 — Sokak sağlamlaştırmada aydınlatma projelerinin uygulanması | 7 | 98.415.194,00 | 98.415.194,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 102 — Sokak sağlamlaştırmada aydınlatma projelerinin uygulanması | 10 | 116.080.085,00 | 116.080.085,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 103 — Yeni aydınlatma projelerinin uygulanması | 4 | 60.243.000,00 | 60.243.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 103 — Yeni aydınlatma projelerinin uygulanması | 7 | 84.355.880,00 | 84.355.880,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 103 — Yeni aydınlatma projelerinin uygulanması | 10 | 99.417.216,00 | 99.417.216,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 104 — Kamu binalarının elektrik bakım ve onarım çalışmaları | 4 | 9.807.000,00 | 9.807.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 104 — Kamu binalarının elektrik bakım ve onarım çalışmaları | 7 | 14.059.313,00 | 14.059.313,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 104 — Kamu binalarının elektrik bakım ve onarım çalışmaları | 10 | 21.582.869,00 | 21.582.869,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 4 | 8.000.000,00 | 8.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 7 | 10.000.000,00 | 10.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 10 | 12.500.000,00 | 12.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 106 — Ruhsatsız faaliyet gösteren işletmelerin tespiti ve ruhsatlandırma denetimleri | 4 | 8.000.000,00 | 8.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 106 — Ruhsatsız faaliyet gösteren işletmelerin tespiti ve ruhsatlandırma denetimleri | 7 | 10.000.000,00 | 10.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 106 — Ruhsatsız faaliyet gösteren işletmelerin tespiti ve ruhsatlandırma denetimleri | 10 | 12.500.000,00 | 12.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 4 | 14.587.500,00 | 14.587.500,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 7 | 16.970.110,00 | 16.970.110,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 10 | 18.102.713,00 | 18.102.713,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 7 | 3.828.577,00 | 3.828.577,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 10 | 4.500.000,00 | 4.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 109 — Engelli ve özel gereksinimli bireylere yönelik eğitim, rehabilitasyon ve sosyal gelişim faaliyetleri | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 109 — Engelli ve özel gereksinimli bireylere yönelik eğitim, rehabilitasyon ve sosyal gelişim faaliyetleri | 7 | 3.828.577,00 | 3.828.577,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 109 — Engelli ve özel gereksinimli bireylere yönelik eğitim, rehabilitasyon ve sosyal gelişim faaliyetleri | 10 | 4.500.000,00 | 4.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 4 | 6.087.500,00 | 6.087.500,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 7 | 6.937.954,00 | 6.937.954,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 10 | 7.020.359,00 | 7.020.359,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 111 — Sağlıklı Nesiller Güçlü Yarınlar Koruyucu Tarama ve Eğitim Projesi | 4 | 6.087.500,00 | 6.087.500,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 111 — Sağlıklı Nesiller Güçlü Yarınlar Koruyucu Tarama ve Eğitim Projesi | 7 | 6.937.954,00 | 6.937.954,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 111 — Sağlıklı Nesiller Güçlü Yarınlar Koruyucu Tarama ve Eğitim Projesi | 10 | 7.020.359,00 | 7.020.359,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 4 | 5.500.000,00 | 5.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 7 | 6.203.579,00 | 6.203.579,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 10 | 6.582.354,00 | 6.582.354,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 113 — Hasta nakil hizmetlerinin kapasitesinin artırılması | 4 | 5.500.000,00 | 5.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 113 — Hasta nakil hizmetlerinin kapasitesinin artırılması | 7 | 6.203.579,00 | 6.203.579,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 113 — Hasta nakil hizmetlerinin kapasitesinin artırılması | 10 | 6.582.354,00 | 6.582.354,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 4 | 2.343.147,00 | 2.343.147,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 7 | 1.534.074,00 | 1.534.074,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 10 | 1.687.482,00 | 1.687.482,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 4 | 2.343.147,00 | 2.343.147,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 7 | 1.534.074,00 | 1.534.074,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 10 | 1.687.482,00 | 1.687.482,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 116 — İşyeri ruhsatlandırma faaliyetleri | 4 | 2.343.147,00 | 2.343.147,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 116 — İşyeri ruhsatlandırma faaliyetleri | 7 | 1.534.074,00 | 1.534.074,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 116 — İşyeri ruhsatlandırma faaliyetleri | 10 | 1.687.482,00 | 1.687.482,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 4 | 72.675.000,00 | 72.675.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 7 | 99.545.813,00 | 99.545.813,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 10 | 124.625.000,00 | 124.625.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 4 | 72.675.000,00 | 72.675.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 7 | 99.545.813,00 | 99.545.813,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 10 | 124.625.000,00 | 124.625.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 119 — Sahipsiz hayvanlara yönelik rehabilitasyon hizmetleri | 4 | 5.000.000,00 | 5.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 119 — Sahipsiz hayvanlara yönelik rehabilitasyon hizmetleri | 7 | 10.000.000,00 | 10.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 119 — Sahipsiz hayvanlara yönelik rehabilitasyon hizmetleri | 10 | 15.000.000,00 | 15.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 120 — İlaç, tıbbi sarf malzemesi ve mama alımı ile cerrahi müdahaleler | 4 | 23.675.000,00 | 23.675.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 120 — İlaç, tıbbi sarf malzemesi ve mama alımı ile cerrahi müdahaleler | 7 | 33.045.813,00 | 33.045.813,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 120 — İlaç, tıbbi sarf malzemesi ve mama alımı ile cerrahi müdahaleler | 10 | 43.000.000,00 | 43.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 121 — Sokak hayvanlarına yönelik periyodik besleme faaliyetleri | 4 | 34.000.000,00 | 34.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 121 — Sokak hayvanlarına yönelik periyodik besleme faaliyetleri | 7 | 44.000.000,00 | 44.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 121 — Sokak hayvanlarına yönelik periyodik besleme faaliyetleri | 10 | 51.000.000,00 | 51.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 122 — Mevcut barınak kapasitesinin artırılması ve teknik altyapı iyileştirmesi | 4 | 10.000.000,00 | 10.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 122 — Mevcut barınak kapasitesinin artırılması ve teknik altyapı iyileştirmesi | 7 | 12.500.000,00 | 12.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 122 — Mevcut barınak kapasitesinin artırılması ve teknik altyapı iyileştirmesi | 10 | 15.625.000,00 | 15.625.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 4 | 838.307.912,00 | 838.307.912,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 7 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 10 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 4 | 838.307.912,00 | 838.307.912,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 7 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 10 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 125 — Evsel atıkların düzenli toplanması ve katı atık aktarma istasyonuna nakli | 4 | 225.610.000,00 | 225.610.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 125 — Evsel atıkların düzenli toplanması ve katı atık aktarma istasyonuna nakli | 7 | 293.565.000,00 | 293.565.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 125 — Evsel atıkların düzenli toplanması ve katı atık aktarma istasyonuna nakli | 10 | 366.710.000,00 | 366.710.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 126 — Kamusal alanların (cadde, sokak, meydan vb.) süpürülmesi, yıkanması ve temizlenmesi | 4 | 347.250.000,00 | 347.250.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 126 — Kamusal alanların (cadde, sokak, meydan vb.) süpürülmesi, yıkanması ve temizlenmesi | 7 | 583.250.000,00 | 583.250.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 126 — Kamusal alanların (cadde, sokak, meydan vb.) süpürülmesi, yıkanması ve temizlenmesi | 10 | 728.500.000,00 | 728.500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 127 — İnşaat-moloz, bahçe atıkları ve atıl eşyaların toplanması | 4 | 63.360.000,00 | 63.360.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 127 — İnşaat-moloz, bahçe atıkları ve atıl eşyaların toplanması | 7 | 82.440.000,00 | 82.440.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 127 — İnşaat-moloz, bahçe atıkları ve atıl eşyaların toplanması | 10 | 102.960.000,00 | 102.960.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 128 — Atık konteynerlerinin bakım, onarım, yıkama ve dezenfeksiyonu | 4 | 37.770.000,00 | 37.770.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 128 — Atık konteynerlerinin bakım, onarım, yıkama ve dezenfeksiyonu | 7 | 49.455.000,00 | 49.455.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 128 — Atık konteynerlerinin bakım, onarım, yıkama ve dezenfeksiyonu | 10 | 62.095.000,00 | 62.095.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 129 — İbadethane temizliklerinin yapılması | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 129 — İbadethane temizliklerinin yapılması | 7 | 5.000.000,00 | 5.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 129 — İbadethane temizliklerinin yapılması | 10 | 7.000.000,00 | 7.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 130 — Kordon boyu sahil şeridinin yıkanması, çöp kutularının boşaltılması ve temizlenmesi | 4 | 133.760.000,00 | 133.760.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 130 — Kordon boyu sahil şeridinin yıkanması, çöp kutularının boşaltılması ve temizlenmesi | 7 | 174.040.000,00 | 174.040.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 130 — Kordon boyu sahil şeridinin yıkanması, çöp kutularının boşaltılması ve temizlenmesi | 10 | 217.360.000,00 | 217.360.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 131 — Şehir merkezine modern ve estetik çöp konteynerlerinin yerleştirilmesi | 4 | 25.750.000,00 | 25.750.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 131 — Şehir merkezine modern ve estetik çöp konteynerlerinin yerleştirilmesi | 7 | 32.920.000,00 | 32.920.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 131 — Şehir merkezine modern ve estetik çöp konteynerlerinin yerleştirilmesi | 10 | 41.212.743,00 | 41.212.743,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 132 — Dünya Çevre Günü, Marmara Denizi Günü ve çevre koruma haftası etkinlikleri | 4 | 1.000.000,00 | 1.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 132 — Dünya Çevre Günü, Marmara Denizi Günü ve çevre koruma haftası etkinlikleri | 7 | 1.500.000,00 | 1.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 132 — Dünya Çevre Günü, Marmara Denizi Günü ve çevre koruma haftası etkinlikleri | 10 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 133 — Yerel yönetimler, STK, üniversiteler ile çevre iş birlikleri | 4 | 403.956,00 | 403.956,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 133 — Yerel yönetimler, STK, üniversiteler ile çevre iş birlikleri | 7 | 600.000,00 | 600.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 133 — Yerel yönetimler, STK, üniversiteler ile çevre iş birlikleri | 10 | 700.000,00 | 700.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 134 — Gürültü ve çevre denetimlerinin yapılması | 4 | 403.956,00 | 403.956,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 134 — Gürültü ve çevre denetimlerinin yapılması | 7 | 600.000,00 | 600.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 134 — Gürültü ve çevre denetimlerinin yapılması | 10 | 700.000,00 | 700.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 4 | 9.171.747,00 | 9.171.747,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 7 | 9.476.838,00 | 9.476.838,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 10 | 8.417.000,00 | 8.417.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 4 | 8.571.747,00 | 8.571.747,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 7 | 8.776.838,00 | 8.776.838,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 10 | 7.697.000,00 | 7.697.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 137 — Yeni tarımsal üretim alanlarının tespiti, tahsisi ve tesisi | 4 | 4.150.000,00 | 4.150.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 137 — Yeni tarımsal üretim alanlarının tespiti, tahsisi ve tesisi | 7 | 4.200.000,00 | 4.200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 137 — Yeni tarımsal üretim alanlarının tespiti, tahsisi ve tesisi | 10 | 2.900.000,00 | 2.900.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 138 — Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini | 4 | 2.521.747,00 | 2.521.747,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 138 — Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini | 7 | 2.676.838,00 | 2.676.838,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 138 — Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini | 10 | 2.897.000,00 | 2.897.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 139 — Zehirsiz gıda ve çevre korunma esaslı tasarruflu sürdürülebilir üretim | 4 | 500.000,00 | 500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 139 — Zehirsiz gıda ve çevre korunma esaslı tasarruflu sürdürülebilir üretim | 7 | 500.000,00 | 500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 139 — Zehirsiz gıda ve çevre korunma esaslı tasarruflu sürdürülebilir üretim | 10 | 500.000,00 | 500.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 140 — Tıbbi ve aromatik bitkilerin yetiştirilmesinin yaygınlaştırılması | 4 | 800.000,00 | 800.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 140 — Tıbbi ve aromatik bitkilerin yetiştirilmesinin yaygınlaştırılması | 7 | 800.000,00 | 800.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 140 — Tıbbi ve aromatik bitkilerin yetiştirilmesinin yaygınlaştırılması | 10 | 800.000,00 | 800.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 141 — Çiftçilere tohum, fide ve tarımsal girdi desteği | 4 | 600.000,00 | 600.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 141 — Çiftçilere tohum, fide ve tarımsal girdi desteği | 7 | 600.000,00 | 600.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 141 — Çiftçilere tohum, fide ve tarımsal girdi desteği | 10 | 600.000,00 | 600.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 4 | 600.000,00 | 600.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 7 | 700.000,00 | 700.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 10 | 720.000,00 | 720.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 143 — Yenilikçi ve sürdürülebilir tarımsal AR-GE faaliyetleri | 4 | 200.000,00 | 200.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 143 — Yenilikçi ve sürdürülebilir tarımsal AR-GE faaliyetleri | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 143 — Yenilikçi ve sürdürülebilir tarımsal AR-GE faaliyetleri | 10 | 220.000,00 | 220.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 144 — Bitkisel ve hayvansal üretim yapan üreticilerin eğitim ve bilgilendirilmesi | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 144 — Bitkisel ve hayvansal üretim yapan üreticilerin eğitim ve bilgilendirilmesi | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 144 — Bitkisel ve hayvansal üretim yapan üreticilerin eğitim ve bilgilendirilmesi | 10 | 200.000,00 | 200.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 145 — Yerel ürünlerin satış ve pazarlamasına yönelik etkinlik yapılması | 4 | 300.000,00 | 300.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 145 — Yerel ürünlerin satış ve pazarlamasına yönelik etkinlik yapılması | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 145 — Yerel ürünlerin satış ve pazarlamasına yönelik etkinlik yapılması | 10 | 300.000,00 | 300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 4 | 590.000,00 | 590.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 7 | 1.100.000,00 | 1.100.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 10 | 1.600.000,00 | 1.600.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 4 | 590.000,00 | 590.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 7 | 1.100.000,00 | 1.100.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 10 | 1.600.000,00 | 1.600.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 148 — Sürdürülebilir Enerji ve İklim Eylem Planının (SECAP) takibi ve güncellenmesi | 4 | 190.000,00 | 190.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 148 — Sürdürülebilir Enerji ve İklim Eylem Planının (SECAP) takibi ve güncellenmesi | 7 | 300.000,00 | 300.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 148 — Sürdürülebilir Enerji ve İklim Eylem Planının (SECAP) takibi ve güncellenmesi | 10 | 400.000,00 | 400.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 149 — İklim değişikliği konusunda kurum içi ve vatandaşa yönelik eğitimler | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 149 — İklim değişikliği konusunda kurum içi ve vatandaşa yönelik eğitimler | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 149 — İklim değişikliği konusunda kurum içi ve vatandaşa yönelik eğitimler | 10 | 300.000,00 | 300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 150 — Yerel yönetimler, STK, üniversite ve özel sektör iş birlikleri (İklim) | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 150 — Yerel yönetimler, STK, üniversite ve özel sektör iş birlikleri (İklim) | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 150 — Yerel yönetimler, STK, üniversite ve özel sektör iş birlikleri (İklim) | 10 | 300.000,00 | 300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 151 — Hava kalitesi eylem planı ve gürültü eylem planı hazırlanmasına destek | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 151 — Hava kalitesi eylem planı ve gürültü eylem planı hazırlanmasına destek | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 151 — Hava kalitesi eylem planı ve gürültü eylem planı hazırlanmasına destek | 10 | 300.000,00 | 300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 152 — Sıfır Atık uygulamaları, atık yönetimi denetimleri ve eğitim faaliyetleri | 4 | 100.000,00 | 100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 152 — Sıfır Atık uygulamaları, atık yönetimi denetimleri ve eğitim faaliyetleri | 7 | 200.000,00 | 200.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 152 — Sıfır Atık uygulamaları, atık yönetimi denetimleri ve eğitim faaliyetleri | 10 | 300.000,00 | 300.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 4 | 80.000.000,00 | 80.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 7 | 141.635.659,00 | 141.635.659,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 10 | 191.746.000,00 | 191.746.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 4 | 8.050.000,00 | 8.050.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 7 | 16.882.450,00 | 16.882.450,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 10 | 21.103.050,00 | 21.103.050,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 155 — Kütüphane hizmetleri bilgilendirme ve farkındalık çalışmaları | 4 | 3.500.000,00 | 3.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 155 — Kütüphane hizmetleri bilgilendirme ve farkındalık çalışmaları | 7 | 7.093.750,00 | 7.093.750,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 155 — Kütüphane hizmetleri bilgilendirme ve farkındalık çalışmaları | 10 | 8.735.925,00 | 8.735.925,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 156 — Kitap kulüpleri, yazar söyleşileri ve okuma etkinlikleri | 4 | 2.300.000,00 | 2.300.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 156 — Kitap kulüpleri, yazar söyleşileri ve okuma etkinlikleri | 7 | 4.876.200,00 | 4.876.200,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 156 — Kitap kulüpleri, yazar söyleşileri ve okuma etkinlikleri | 10 | 6.151.500,00 | 6.151.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 157 — Kütüphanecilikte eğitim kurumları ve STK iş birlikleri | 4 | 2.250.000,00 | 2.250.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 157 — Kütüphanecilikte eğitim kurumları ve STK iş birlikleri | 7 | 4.912.500,00 | 4.912.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 157 — Kütüphanecilikte eğitim kurumları ve STK iş birlikleri | 10 | 6.215.625,00 | 6.215.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 4 | 40.935.750,00 | 40.935.750,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 7 | 78.490.930,00 | 78.490.930,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 10 | 106.877.340,00 | 106.877.340,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 159 — Uluslararası İstanbul Büyükçekmece Kültür ve Sanat Festivali ve organizasyonlar | 4 | 9.050.000,00 | 9.050.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 159 — Uluslararası İstanbul Büyükçekmece Kültür ve Sanat Festivali ve organizasyonlar | 7 | 16.332.550,00 | 16.332.550,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 159 — Uluslararası İstanbul Büyükçekmece Kültür ve Sanat Festivali ve organizasyonlar | 10 | 21.138.594,00 | 21.138.594,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 160 — Sahne sanatları ve güzel sanatlar eğitim ve atölyeleri | 4 | 3.600.000,00 | 3.600.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 160 — Sahne sanatları ve güzel sanatlar eğitim ve atölyeleri | 7 | 6.861.510,00 | 6.861.510,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 160 — Sahne sanatları ve güzel sanatlar eğitim ve atölyeleri | 10 | 8.728.806,00 | 8.728.806,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 161 — Kültürel ve sanatsal etkinlikler (Göl, Kültürpark, Sahil) | 4 | 450.000,00 | 450.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 161 — Kültürel ve sanatsal etkinlikler (Göl, Kültürpark, Sahil) | 7 | 585.000,00 | 585.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 161 — Kültürel ve sanatsal etkinlikler (Göl, Kültürpark, Sahil) | 10 | 693.250,00 | 693.250,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 162 — Uluslararası fotoğraf yarışması platformu | 4 | 650.000,00 | 650.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 162 — Uluslararası fotoğraf yarışması platformu | 7 | 910.000,00 | 910.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 162 — Uluslararası fotoğraf yarışması platformu | 10 | 1.300.675,00 | 1.300.675,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 163 — Milli/dini bayramlar ve özel günlerde toplumsal etkinlikler | 4 | 3.250.000,00 | 3.250.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 163 — Milli/dini bayramlar ve özel günlerde toplumsal etkinlikler | 7 | 5.906.250,00 | 5.906.250,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 163 — Milli/dini bayramlar ve özel günlerde toplumsal etkinlikler | 10 | 6.994.343,00 | 6.994.343,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 164 — Marmara Denizi kıyısında açık hava kültürel ve sanatsal organizasyonları | 4 | 21.675.750,00 | 21.675.750,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 164 — Marmara Denizi kıyısında açık hava kültürel ve sanatsal organizasyonları | 7 | 40.018.120,00 | 40.018.120,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 164 — Marmara Denizi kıyısında açık hava kültürel ve sanatsal organizasyonları | 10 | 57.348.617,00 | 57.348.617,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 165 — Okullara yönelik rehberli müze turları | 4 | 810.000,00 | 810.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 165 — Okullara yönelik rehberli müze turları | 7 | 1.105.000,00 | 1.105.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 165 — Okullara yönelik rehberli müze turları | 10 | 2.295.000,00 | 2.295.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 166 — Çocuk, genç ve yetişkinlere yönelik tematik müze atölyeleri | 4 | 1.450.000,00 | 1.450.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 166 — Çocuk, genç ve yetişkinlere yönelik tematik müze atölyeleri | 7 | 6.772.500,00 | 6.772.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 166 — Çocuk, genç ve yetişkinlere yönelik tematik müze atölyeleri | 10 | 8.378.055,00 | 8.378.055,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 4 | 31.014.250,00 | 31.014.250,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 7 | 46.262.279,00 | 46.262.279,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 10 | 63.765.610,00 | 63.765.610,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 168 — Meslek kursları düzenleme (dil, bilişim, mutfak vb.) | 4 | 3.373.750,00 | 3.373.750,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 168 — Meslek kursları düzenleme (dil, bilişim, mutfak vb.) | 7 | 5.325.000,00 | 5.325.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 168 — Meslek kursları düzenleme (dil, bilişim, mutfak vb.) | 10 | 6.840.000,00 | 6.840.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 169 — Sahne sanatları kursları (halk oyunları, dans, tiyatro, enstrüman) | 4 | 2.845.000,00 | 2.845.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 169 — Sahne sanatları kursları (halk oyunları, dans, tiyatro, enstrüman) | 7 | 4.692.500,00 | 4.692.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 169 — Sahne sanatları kursları (halk oyunları, dans, tiyatro, enstrüman) | 10 | 6.045.625,00 | 6.045.625,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 170 — Örgün eğitime destek ve merkezi sınavlara hazırlık kursları | 4 | 20.400.000,00 | 20.400.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 170 — Örgün eğitime destek ve merkezi sınavlara hazırlık kursları | 7 | 32.373.570,00 | 32.373.570,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 170 — Örgün eğitime destek ve merkezi sınavlara hazırlık kursları | 10 | 46.275.725,00 | 46.275.725,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 171 — Teknoloji eğitimleri (yapay zeka, kodlama, web tasarım vb.) | 4 | 1.100.000,00 | 1.100.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 171 — Teknoloji eğitimleri (yapay zeka, kodlama, web tasarım vb.) | 7 | 1.775.000,00 | 1.775.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 171 — Teknoloji eğitimleri (yapay zeka, kodlama, web tasarım vb.) | 10 | 1.976.250,00 | 1.976.250,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 172 — Sanatsal eğitimler ve yaz okulları düzenleme | 4 | 1.295.500,00 | 1.295.500,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 172 — Sanatsal eğitimler ve yaz okulları düzenleme | 7 | 2.127.500,00 | 2.127.500,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 172 — Sanatsal eğitimler ve yaz okulları düzenleme | 10 | 2.729.375,00 | 2.729.375,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 4 | 54.270.630,00 | 54.270.630,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 7 | 81.146.442,00 | 81.146.442,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 10 | 92.146.534,00 | 92.146.534,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 4 | 54.270.630,00 | 54.270.630,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 7 | 81.146.442,00 | 81.146.442,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 10 | 92.146.534,00 | 92.146.534,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 175 — Amatör spor kulüplerine ayni, nakdi ve lojistik destek sağlanması | 4 | 14.505.630,00 | 14.505.630,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 175 — Amatör spor kulüplerine ayni, nakdi ve lojistik destek sağlanması | 7 | 22.206.756,00 | 22.206.756,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 175 — Amatör spor kulüplerine ayni, nakdi ve lojistik destek sağlanması | 10 | 25.537.769,00 | 25.537.769,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 176 — Spor tesislerinin engelli erişimine uygun hale getirilmesi | 4 | 4.520.000,00 | 4.520.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 176 — Spor tesislerinin engelli erişimine uygun hale getirilmesi | 7 | 5.424.000,00 | 5.424.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 176 — Spor tesislerinin engelli erişimine uygun hale getirilmesi | 10 | 6.237.600,00 | 6.237.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 177 — Mevcut spor tesislerinin modernizasyonu ve ekipman temini | 4 | 6.270.334,00 | 6.270.334,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 177 — Mevcut spor tesislerinin modernizasyonu ve ekipman temini | 7 | 11.124.000,00 | 11.124.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 177 — Mevcut spor tesislerinin modernizasyonu ve ekipman temini | 10 | 12.792.600,00 | 12.792.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 178 — Spor etkinliklerine kültür ve sanatın entegre edilmesi | 4 | 903.333,00 | 903.333,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 178 — Spor etkinliklerine kültür ve sanatın entegre edilmesi | 7 | 1.084.000,00 | 1.084.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 178 — Spor etkinliklerine kültür ve sanatın entegre edilmesi | 10 | 1.246.600,00 | 1.246.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 179 — Çevre bilinci odaklı spor etkinlikleri yapılması | 4 | 2.403.333,00 | 2.403.333,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 179 — Çevre bilinci odaklı spor etkinlikleri yapılması | 7 | 2.884.000,00 | 2.884.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 179 — Çevre bilinci odaklı spor etkinlikleri yapılması | 10 | 3.316.600,00 | 3.316.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 180 — Yenilikçi ve çeşitli alternatif spor branşları açılması | 4 | 10.520.000,00 | 10.520.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 180 — Yenilikçi ve çeşitli alternatif spor branşları açılması | 7 | 16.224.000,00 | 16.224.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 180 — Yenilikçi ve çeşitli alternatif spor branşları açılması | 10 | 18.657.600,00 | 18.657.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 181 — Toplumun her kesimine yönelik kapsayıcı spor programları | 4 | 10.120.000,00 | 10.120.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 181 — Toplumun her kesimine yönelik kapsayıcı spor programları | 7 | 16.944.000,00 | 16.944.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 181 — Toplumun her kesimine yönelik kapsayıcı spor programları | 10 | 19.485.600,00 | 19.485.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 182 — Uluslararası spor organizasyonları ve turnuvaları | 4 | 2.625.000,00 | 2.625.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 182 — Uluslararası spor organizasyonları ve turnuvaları | 7 | 3.150.000,00 | 3.150.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 182 — Uluslararası spor organizasyonları ve turnuvaları | 10 | 3.622.500,00 | 3.622.500,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 183 — Sporun sağlık üzerindeki etkilerini vurgulayan farkındalık kampanyaları | 4 | 2.403.000,00 | 2.403.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 183 — Sporun sağlık üzerindeki etkilerini vurgulayan farkındalık kampanyaları | 7 | 2.884.000,80 | 2.884.000,80 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 183 — Sporun sağlık üzerindeki etkilerini vurgulayan farkındalık kampanyaları | 10 | 3.316.600,00 | 3.316.600,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 4 | 43.010.974,00 | 43.010.974,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 7 | 49.431.122,00 | 49.431.122,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 10 | 56.665.674,00 | 56.665.674,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 4 | 43.010.974,00 | 43.010.974,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 7 | 49.431.122,00 | 49.431.122,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 10 | 56.665.674,00 | 56.665.674,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 186 — Dar gelirli ve ihtiyaç sahibi vatandaşlara ayni destek (gıda, giyim, yakacak vb.) | 4 | 25.010.974,00 | 25.010.974,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 186 — Dar gelirli ve ihtiyaç sahibi vatandaşlara ayni destek (gıda, giyim, yakacak vb.) | 7 | 29.431.122,00 | 29.431.122,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 186 — Dar gelirli ve ihtiyaç sahibi vatandaşlara ayni destek (gıda, giyim, yakacak vb.) | 10 | 34.665.674,00 | 34.665.674,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 187 — Dar gelirli ve muhtaç hanelere nakdi yardım ve sosyal destekler | 4 | 18.000.000,00 | 18.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 187 — Dar gelirli ve muhtaç hanelere nakdi yardım ve sosyal destekler | 7 | 20.000.000,00 | 20.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 187 — Dar gelirli ve muhtaç hanelere nakdi yardım ve sosyal destekler | 10 | 22.000.000,00 | 22.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 4 | 18.500.000,00 | 18.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 7 | 23.500.000,00 | 23.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 10 | 25.000.000,00 | 25.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 4 | 16.500.000,00 | 16.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 7 | 21.000.000,00 | 21.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 10 | 22.000.000,00 | 22.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 190 — İhtiyaç sahibi öğrencilere kırtasiye ve düzenli beslenme desteği | 4 | 16.500.000,00 | 16.500.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 190 — İhtiyaç sahibi öğrencilere kırtasiye ve düzenli beslenme desteği | 7 | 21.000.000,00 | 21.000.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 190 — İhtiyaç sahibi öğrencilere kırtasiye ve düzenli beslenme desteği | 10 | 22.000.000,00 | 22.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 7 | 2.500.000,00 | 2.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 10 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 192 — Sosyal risk altındaki çocukların güçlendirilmesi, eğitim ve farkındalık faaliyetleri | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 192 — Sosyal risk altındaki çocukların güçlendirilmesi, eğitim ve farkındalık faaliyetleri | 7 | 2.500.000,00 | 2.500.000,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 192 — Sosyal risk altındaki çocukların güçlendirilmesi, eğitim ve farkındalık faaliyetleri | 10 | 3.000.000,00 | 3.000.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 4 | 3.189.780.044,00 | 3.189.780.044,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 7 | 5.026.960.693,50 | 5.026.960.693,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 10 | 6.064.309.830,00 | 6.064.309.830,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 4 | 4.808.694.956,00 | 4.808.694.956,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 7 | 4.160.006.066,50 | 4.160.006.066,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 10 | 4.523.165.170,00 | 4.523.165.170,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 195 — Harcamacı Birimler Personel ve SGK Giderleri Toplamı (Tüm Müdürlükler) | 4 | 383.032.506,00 | 383.032.506,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 195 — Harcamacı Birimler Personel ve SGK Giderleri Toplamı (Tüm Müdürlükler) | 7 | 478.790.632,00 | 478.790.632,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 195 — Harcamacı Birimler Personel ve SGK Giderleri Toplamı (Tüm Müdürlükler) | 10 | 598.488.294,00 | 598.488.294,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 196 — Diğer Destek, Denetim ve Hizmet Birimleri Bütçe Tahsisi (Hukuk, Teftiş, Özel Kalem, Yazı İşleri vb.) | 4 | 4.425.662.450,00 | 4.425.662.450,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 196 — Diğer Destek, Denetim ve Hizmet Birimleri Bütçe Tahsisi (Hukuk, Teftiş, Özel Kalem, Yazı İşleri vb.) | 7 | 3.681.215.434,50 | 3.681.215.434,50 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 196 — Diğer Destek, Denetim ve Hizmet Birimleri Bütçe Tahsisi (Hukuk, Teftiş, Özel Kalem, Yazı İşleri vb.) | 10 | 3.924.676.876,00 | 3.924.676.876,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 4 | 7.998.475.000,00 | 7.998.475.000,00 | 0,00 | 2027: bileşen sütunları 2, 3 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 7 | 9.186.966.760,00 | 9.186.966.760,00 | 0,00 | 2028: bileşen sütunları 5, 6 |
| PASS | — | Satır toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 10 | 10.587.475.000,00 | 10.587.475.000,00 | 0,00 | 2029: bileşen sütunları 8, 9 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 2 | 1.132.975.122,00 | 1.132.976.122,00 | -1.000,00 | Kapsanan satırlar: 4, 14, 27 Kanıt: s.248 / u444di4775 / r4c2 = «1.089.920.835,00»; s.248 / u444di4775 / r14c2 = «39.039.548,00»; s.248 / u444di4775 / r27c2 = «4.015.739,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 4 | 1.132.975.122,00 | 1.132.976.122,00 | -1.000,00 | Kapsanan satırlar: 4, 14, 27 Kanıt: s.248 / u444di4775 / r4c4 = «1.089.920.835,00»; s.248 / u444di4775 / r14c4 = «39.039.548,00»; s.248 / u444di4775 / r27c4 = «4.015.739,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 5 | 1.464.002.665,00 | 1.464.002.665,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 7 | 1.464.002.665,00 | 1.464.002.665,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 8 | 1.767.927.554,00 | 1.767.927.554,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 10 | 1.767.927.554,00 | 1.767.927.554,00 | 0,00 | Kapsanan satırlar: 4, 14, 27 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 2 | 1.089.920.835,00 | 1.089.924.835,00 | -4.000,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c2 = «85.152.000,00»; s.248 / u444di4775 / r6c2 = «105.192.000,00»; s.248 / u444di4775 / r7c2 = «30.048.000,00»; s.248 / u444di4775 / r8c2 = «5.008.000,00»; s.248 / u444di4775 / r9c2 = «232.904.967,00»; s.248 / u444di4775 / r10c2 = «232.904.967,00»; s.248 / u444di4775 / r11c2 = «132.904.967,00»; s.248 / u444di4775 / r12c2 = «132.904.967,00»; s.248 / u444di4775 / r13c2 = «132.904.967,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 4 | 1.089.920.835,00 | 1.089.924.835,00 | -4.000,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c4 = «85.152.000,00»; s.248 / u444di4775 / r6c4 = «105.192.000,00»; s.248 / u444di4775 / r7c4 = «30.048.000,00»; s.248 / u444di4775 / r8c4 = «5.008.000,00»; s.248 / u444di4775 / r9c4 = «232.904.967,00»; s.248 / u444di4775 / r10c4 = «232.904.967,00»; s.248 / u444di4775 / r11c4 = «132.904.967,00»; s.248 / u444di4775 / r12c4 = «132.904.967,00»; s.248 / u444di4775 / r13c4 = «132.904.967,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 5 | 1.398.412.510,00 | 1.428.037.510,00 | -29.625.000,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c5 = «133.500.000,00»; s.248 / u444di4775 / r6c5 = «168.700.000,00»; s.248 / u444di4775 / r7c5 = «42.200.000,00»; s.248 / u444di4775 / r8c5 = «7.645.208,00»; s.248 / u444di4775 / r9c5 = «215.198.462,00»; s.248 / u444di4775 / r10c5 = «215.198.460,00»; s.248 / u444di4775 / r11c5 = «215.198.460,00»; s.248 / u444di4775 / r12c5 = «215.198.460,00»; s.248 / u444di4775 / r13c5 = «215.198.460,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 7 | 1.398.412.510,00 | 1.428.037.510,00 | -29.625.000,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c7 = «133.500.000,00»; s.248 / u444di4775 / r6c7 = «168.700.000,00»; s.248 / u444di4775 / r7c7 = «42.200.000,00»; s.248 / u444di4775 / r8c7 = «7.645.208,00»; s.248 / u444di4775 / r9c7 = «215.198.462,00»; s.248 / u444di4775 / r10c7 = «215.198.460,00»; s.248 / u444di4775 / r11c7 = «215.198.460,00»; s.248 / u444di4775 / r12c7 = «215.198.460,00»; s.248 / u444di4775 / r13c7 = «215.198.460,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 8 | 1.690.925.768,00 | 1.727.957.010,00 | -37.031.242,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c8 = «160.515.475,00»; s.248 / u444di4775 / r6c8 = «202.756.389,00»; s.248 / u444di4775 / r7c8 = «50.689.097,00»; s.248 / u444di4775 / r8c8 = «9.124.037,00»; s.248 / u444di4775 / r9c8 = «260.974.404,00»; s.248 / u444di4775 / r10c8 = «260.974.402,00»; s.248 / u444di4775 / r11c8 = «260.974.402,00»; s.248 / u444di4775 / r12c8 = «260.974.402,00»; s.248 / u444di4775 / r13c8 = «260.974.402,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 4 — (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 10 | 1.690.925.768,00 | 1.727.957.010,00 | -37.031.242,00 | Kapsanan satırlar: 5, 6, 7, 8, 9, 10, 11, 12, 13 Kanıt: s.248 / u444di4775 / r5c10 = «160.515.475,00»; s.248 / u444di4775 / r6c10 = «202.756.389,00»; s.248 / u444di4775 / r7c10 = «50.689.097,00»; s.248 / u444di4775 / r8c10 = «9.124.037,00»; s.248 / u444di4775 / r9c10 = «260.974.404,00»; s.248 / u444di4775 / r10c10 = «260.974.402,00»; s.248 / u444di4775 / r11c10 = «260.974.402,00»; s.248 / u444di4775 / r12c10 = «260.974.402,00»; s.248 / u444di4775 / r13c10 = «260.974.402,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 2 | 39.039.548,00 | 38.039.548,00 | 1.000.000,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c2 = «1.489.548,00»; s.248 / u444di4775 / r16c2 = «400.000,00»; s.248 / u444di4775 / r17c2 = «700.000,00»; s.248 / u444di4775 / r18c2 = «1.450.000,00»; s.248 / u444di4775 / r19c2 = «15.000.000,00»; s.248 / u444di4775 / r20c2 = «2.500.000,00»; s.248 / u444di4775 / r21c2 = «5.000.000,00»; s.248 / u444di4775 / r22c2 = «2.500.000,00»; s.248 / u444di4775 / r23c2 = «1.500.000,00»; s.248 / u444di4775 / r24c2 = «1.500.000,00»; s.248 / u444di4775 / r25c2 = «2.000.000,00»; s.248 / u444di4775 / r26c2 = «4.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 4 | 39.039.548,00 | 38.039.548,00 | 1.000.000,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c4 = «1.489.548,00»; s.248 / u444di4775 / r16c4 = «400.000,00»; s.248 / u444di4775 / r17c4 = «700.000,00»; s.248 / u444di4775 / r18c4 = «1.450.000,00»; s.248 / u444di4775 / r19c4 = «15.000.000,00»; s.248 / u444di4775 / r20c4 = «2.500.000,00»; s.248 / u444di4775 / r21c4 = «5.000.000,00»; s.248 / u444di4775 / r22c4 = «2.500.000,00»; s.248 / u444di4775 / r23c4 = «1.500.000,00»; s.248 / u444di4775 / r24c4 = «1.500.000,00»; s.248 / u444di4775 / r25c4 = «2.000.000,00»; s.248 / u444di4775 / r26c4 = «4.000.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 5 | 59.320.481,00 | 58.570.481,00 | 750.000,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c5 = «1.589.548,00»; s.248 / u444di4775 / r16c5 = «530.933,00»; s.248 / u444di4775 / r17c5 = «800.000,00»; s.248 / u444di4775 / r18c5 = «1.650.000,00»; s.248 / u444di4775 / r19c5 = «21.875.000,00»; s.248 / u444di4775 / r20c5 = «3.125.000,00»; s.248 / u444di4775 / r21c5 = «9.375.000,00»; s.248 / u444di4775 / r22c5 = «3.125.000,00»; s.248 / u444di4775 / r23c5 = «3.125.000,00»; s.248 / u444di4775 / r24c5 = «3.125.000,00»; s.248 / u444di4775 / r25c5 = «4.000.000,00»; s.248 / u444di4775 / r26c5 = «6.250.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 7 | 59.320.481,00 | 58.570.481,00 | 750.000,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c7 = «1.589.548,00»; s.248 / u444di4775 / r16c7 = «530.933,00»; s.248 / u444di4775 / r17c7 = «800.000,00»; s.248 / u444di4775 / r18c7 = «1.650.000,00»; s.248 / u444di4775 / r19c7 = «21.875.000,00»; s.248 / u444di4775 / r20c7 = «3.125.000,00»; s.248 / u444di4775 / r21c7 = «9.375.000,00»; s.248 / u444di4775 / r22c7 = «3.125.000,00»; s.248 / u444di4775 / r23c7 = «3.125.000,00»; s.248 / u444di4775 / r24c7 = «3.125.000,00»; s.248 / u444di4775 / r25c7 = «4.000.000,00»; s.248 / u444di4775 / r26c7 = «6.250.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 8 | 69.683.393,00 | 67.370.000,00 | 2.313.393,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c8 = «1.624.067,00»; s.248 / u444di4775 / r16c8 = «530.933,00»; s.248 / u444di4775 / r17c8 = «800.000,00»; s.248 / u444di4775 / r18c8 = «1.650.000,00»; s.248 / u444di4775 / r19c8 = «25.630.000,00»; s.248 / u444di4775 / r20c8 = «3.630.000,00»; s.248 / u444di4775 / r21c8 = «10.930.000,00»; s.248 / u444di4775 / r22c8 = «3.630.000,00»; s.248 / u444di4775 / r23c8 = «3.630.000,00»; s.248 / u444di4775 / r24c8 = «3.630.000,00»; s.248 / u444di4775 / r25c8 = «4.425.000,00»; s.248 / u444di4775 / r26c8 = «7.260.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 14 — (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 10 | 69.683.393,00 | 67.370.000,00 | 2.313.393,00 | Kapsanan satırlar: 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 Kanıt: s.248 / u444di4775 / r15c10 = «1.624.067,00»; s.248 / u444di4775 / r16c10 = «530.933,00»; s.248 / u444di4775 / r17c10 = «800.000,00»; s.248 / u444di4775 / r18c10 = «1.650.000,00»; s.248 / u444di4775 / r19c10 = «25.630.000,00»; s.248 / u444di4775 / r20c10 = «3.630.000,00»; s.248 / u444di4775 / r21c10 = «10.930.000,00»; s.248 / u444di4775 / r22c10 = «3.630.000,00»; s.248 / u444di4775 / r23c10 = «3.630.000,00»; s.248 / u444di4775 / r24c10 = «3.630.000,00»; s.248 / u444di4775 / r25c10 = «4.425.000,00»; s.248 / u444di4775 / r26c10 = «7.260.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 2 | 4.015.739,00 | 4.015.739,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 4 | 4.015.739,00 | 4.015.739,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 5 | 6.269.674,00 | 6.269.674,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 7 | 6.269.674,00 | 6.269.674,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 8 | 7.318.393,00 | 7.318.393,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 27 — (1.3) Vatandaşlık ve Sivil Toplum | 10 | 7.318.393,00 | 7.318.393,00 | 0,00 | Kapsanan satırlar: 28, 29 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 2 | 3.400.000,00 | 3.400.000,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 4 | 3.400.000,00 | 3.400.000,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 5 | 3.650.000,00 | 3.650.000,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 7 | 3.650.000,00 | 3.650.000,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 8 | 3.527.500,00 | 3.527.500,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 10 | 3.527.500,00 | 3.527.500,00 | 0,00 | Kapsanan satırlar: 31 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 2 | 3.400.000,00 | 3.400.000,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 4 | 3.400.000,00 | 3.400.000,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 5 | 3.650.000,00 | 3.650.000,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 7 | 3.650.000,00 | 3.650.000,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 8 | 3.527.500,00 | 3.527.500,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 31 — (2.1) Deneysel Geliştirme | 10 | 3.527.500,00 | 3.527.500,00 | 0,00 | Kapsanan satırlar: 32, 33, 34 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 2 | 810.844.764,00 | 810.844.764,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 4 | 810.844.764,00 | 810.844.764,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 5 | 1.182.029.090,50 | 1.182.029.090,50 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 7 | 1.182.029.090,50 | 1.182.029.090,50 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 8 | 1.411.393.421,00 | 1.411.393.421,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 10 | 1.411.393.421,00 | 1.411.393.421,00 | 0,00 | Kapsanan satırlar: 36, 63, 80 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 2 | 785.740.921,00 | 787.445.533,00 | -1.704.612,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c2 = «179.000.000,00»; s.248 / u444di4775 / r38c2 = «13.050.000,00»; s.248 / u444di4775 / r39c2 = «5.500.000,00»; s.248 / u444di4775 / r40c2 = «984.658,00»; s.248 / u444di4775 / r41c2 = «52.000.000,00»; s.248 / u444di4775 / r42c2 = «4.134.625,00»; s.248 / u444di4775 / r43c2 = «60.133.709,00»; s.248 / u444di4775 / r44c2 = «60.133.709,00»; s.248 / u444di4775 / r45c2 = «70.133.709,00»; s.248 / u444di4775 / r46c2 = «70.133.709,00»; s.248 / u444di4775 / r47c2 = «235.172,00»; s.248 / u444di4775 / r48c2 = «45.333.709,00»; s.248 / u444di4775 / r49c2 = «45.333.709,00»; s.248 / u444di4775 / r50c2 = «70.133.709,00»; s.248 / u444di4775 / r51c2 = «71.532.023,00»; s.248 / u444di4775 / r52c2 = «9.305.773,00»; s.248 / u444di4775 / r53c2 = «7.055.773,00»; s.248 / u444di4775 / r54c2 = «9.005.773,00»; s.248 / u444di4775 / r55c2 = «8.805.773,00»; s.248 / u444di4775 / r56c2 = «200.000,00»; s.248 / u444di4775 / r57c2 = «200.000,00»; s.248 / u444di4775 / r58c2 = «100.000,00»; s.248 / u444di4775 / r59c2 = «500.000,00»; s.248 / u444di4775 / r60c2 = «3.000.000,00»; s.248 / u444di4775 / r61c2 = «500.000,00»; s.248 / u444di4775 / r62c2 = «1.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 4 | 785.740.921,00 | 787.445.533,00 | -1.704.612,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c4 = «179.000.000,00»; s.248 / u444di4775 / r38c4 = «13.050.000,00»; s.248 / u444di4775 / r39c4 = «5.500.000,00»; s.248 / u444di4775 / r40c4 = «984.658,00»; s.248 / u444di4775 / r41c4 = «52.000.000,00»; s.248 / u444di4775 / r42c4 = «4.134.625,00»; s.248 / u444di4775 / r43c4 = «60.133.709,00»; s.248 / u444di4775 / r44c4 = «60.133.709,00»; s.248 / u444di4775 / r45c4 = «70.133.709,00»; s.248 / u444di4775 / r46c4 = «70.133.709,00»; s.248 / u444di4775 / r47c4 = «235.172,00»; s.248 / u444di4775 / r48c4 = «45.333.709,00»; s.248 / u444di4775 / r49c4 = «45.333.709,00»; s.248 / u444di4775 / r50c4 = «70.133.709,00»; s.248 / u444di4775 / r51c4 = «71.532.023,00»; s.248 / u444di4775 / r52c4 = «9.305.773,00»; s.248 / u444di4775 / r53c4 = «7.055.773,00»; s.248 / u444di4775 / r54c4 = «9.005.773,00»; s.248 / u444di4775 / r55c4 = «8.805.773,00»; s.248 / u444di4775 / r56c4 = «200.000,00»; s.248 / u444di4775 / r57c4 = «200.000,00»; s.248 / u444di4775 / r58c4 = «100.000,00»; s.248 / u444di4775 / r59c4 = «500.000,00»; s.248 / u444di4775 / r60c4 = «3.000.000,00»; s.248 / u444di4775 / r61c4 = «500.000,00»; s.248 / u444di4775 / r62c4 = «1.000.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 5 | 1.155.046.041,50 | 1.361.230.029,00 | -206.183.987,50 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c5 = «236.250.000,00»; s.248 / u444di4775 / r38c5 = «16.250.000,00»; s.248 / u444di4775 / r39c5 = «7.000.000,00»; s.248 / u444di4775 / r40c5 = «1.168.323,00»; s.248 / u444di4775 / r41c5 = «65.000.000,00»; s.248 / u444di4775 / r42c5 = «5.972.384,00»; s.248 / u444di4775 / r43c5 = «150.000.000,00»; s.248 / u444di4775 / r44c5 = «150.000.000,00»; s.248 / u444di4775 / r45c5 = «201.091.978,00»; s.248 / u444di4775 / r46c5 = «37.653.411,00»; s.248 / u444di4775 / r47c5 = «1.022.667,00»; s.248 / u444di4775 / r48c5 = «166.398.994,00»; s.248 / u444di4775 / r49c5 = «100.586.604,00»; s.248 / u444di4775 / r50c5 = «100.586.605,00»; s.248 / u444di4775 / r51c5 = «82.220.822,00»; s.248 / u444di4775 / r52c5 = «9.770.824,00»; s.248 / u444di4775 / r53c5 = «5.240.769,00»; s.248 / u444di4775 / r54c5 = «6.970.824,00»; s.248 / u444di4775 / r55c5 = «11.170.824,00»; s.248 / u444di4775 / r56c5 = «0,00»; s.248 / u444di4775 / r57c5 = «0,00»; s.248 / u444di4775 / r58c5 = «625.000,00»; s.248 / u444di4775 / r59c5 = «750.000,00»; s.248 / u444di4775 / r60c5 = «3.500.000,00»; s.248 / u444di4775 / r61c5 = «1.000.000,00»; s.248 / u444di4775 / r62c5 = «1.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 7 | 1.155.046.041,50 | 1.361.230.029,00 | -206.183.987,50 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c7 = «236.250.000,00»; s.248 / u444di4775 / r38c7 = «16.250.000,00»; s.248 / u444di4775 / r39c7 = «7.000.000,00»; s.248 / u444di4775 / r40c7 = «1.168.323,00»; s.248 / u444di4775 / r41c7 = «65.000.000,00»; s.248 / u444di4775 / r42c7 = «5.972.384,00»; s.248 / u444di4775 / r43c7 = «150.000.000,00»; s.248 / u444di4775 / r44c7 = «150.000.000,00»; s.248 / u444di4775 / r45c7 = «201.091.978,00»; s.248 / u444di4775 / r46c7 = «37.653.411,00»; s.248 / u444di4775 / r47c7 = «1.022.667,00»; s.248 / u444di4775 / r48c7 = «166.398.994,00»; s.248 / u444di4775 / r49c7 = «100.586.604,00»; s.248 / u444di4775 / r50c7 = «100.586.605,00»; s.248 / u444di4775 / r51c7 = «82.220.822,00»; s.248 / u444di4775 / r52c7 = «9.770.824,00»; s.248 / u444di4775 / r53c7 = «5.240.769,00»; s.248 / u444di4775 / r54c7 = «6.970.824,00»; s.248 / u444di4775 / r55c7 = «11.170.824,00»; s.248 / u444di4775 / r56c7 = «0,00»; s.248 / u444di4775 / r57c7 = «0,00»; s.248 / u444di4775 / r58c7 = «625.000,00»; s.248 / u444di4775 / r59c7 = «750.000,00»; s.248 / u444di4775 / r60c7 = «3.500.000,00»; s.248 / u444di4775 / r61c7 = «1.000.000,00»; s.248 / u444di4775 / r62c7 = «1.000.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 8 | 1.385.040.627,00 | 1.386.917.587,00 | -1.876.960,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c8 = «283.500.000,00»; s.248 / u444di4775 / r38c8 = «18.800.000,00»; s.248 / u444di4775 / r39c8 = «8.300.000,00»; s.248 / u444di4775 / r40c8 = «1.366.584,00»; s.248 / u444di4775 / r41c8 = «78.000.000,00»; s.248 / u444di4775 / r42c8 = «3.395.323,00»; s.248 / u444di4775 / r43c8 = «150.000.000,00»; s.248 / u444di4775 / r44c8 = «150.000.000,00»; s.248 / u444di4775 / r45c8 = «150.000.000,00»; s.248 / u444di4775 / r46c8 = «47.066.763,00»; s.248 / u444di4775 / r47c8 = «2.019.444,00»; s.248 / u444di4775 / r48c8 = «160.000.000,00»; s.248 / u444di4775 / r49c8 = «100.000.000,00»; s.248 / u444di4775 / r50c8 = «100.000.000,00»; s.248 / u444di4775 / r51c8 = «90.000.000,00»; s.248 / u444di4775 / r52c8 = «10.000.000,00»; s.248 / u444di4775 / r53c8 = «6.776.029,00»; s.248 / u444di4775 / r54c8 = «7.000.000,00»; s.248 / u444di4775 / r55c8 = «12.099.694,00»; s.248 / u444di4775 / r56c8 = «0,00»; s.248 / u444di4775 / r57c8 = «0,00»; s.248 / u444di4775 / r58c8 = «781.250,00»; s.248 / u444di4775 / r59c8 = «1.000.000,00»; s.248 / u444di4775 / r60c8 = «4.000.000,00»; s.248 / u444di4775 / r61c8 = «1.812.500,00»; s.248 / u444di4775 / r62c8 = «1.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 36 — (3.1) Mekânsal Planlama ve Kentsel Dönüşüm | 10 | 1.385.040.627,00 | 1.386.917.587,00 | -1.876.960,00 | Kapsanan satırlar: 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62 Kanıt: s.248 / u444di4775 / r37c10 = «283.500.000,00»; s.248 / u444di4775 / r38c10 = «18.800.000,00»; s.248 / u444di4775 / r39c10 = «8.300.000,00»; s.248 / u444di4775 / r40c10 = «1.366.584,00»; s.248 / u444di4775 / r41c10 = «78.000.000,00»; s.248 / u444di4775 / r42c10 = «3.395.323,00»; s.248 / u444di4775 / r43c10 = «150.000.000,00»; s.248 / u444di4775 / r44c10 = «150.000.000,00»; s.248 / u444di4775 / r45c10 = «150.000.000,00»; s.248 / u444di4775 / r46c10 = «47.066.763,00»; s.248 / u444di4775 / r47c10 = «2.019.444,00»; s.248 / u444di4775 / r48c10 = «160.000.000,00»; s.248 / u444di4775 / r49c10 = «100.000.000,00»; s.248 / u444di4775 / r50c10 = «100.000.000,00»; s.248 / u444di4775 / r51c10 = «90.000.000,00»; s.248 / u444di4775 / r52c10 = «10.000.000,00»; s.248 / u444di4775 / r53c10 = «6.776.029,00»; s.248 / u444di4775 / r54c10 = «7.000.000,00»; s.248 / u444di4775 / r55c10 = «12.099.694,00»; s.248 / u444di4775 / r56c10 = «0,00»; s.248 / u444di4775 / r57c10 = «0,00»; s.248 / u444di4775 / r58c10 = «781.250,00»; s.248 / u444di4775 / r59c10 = «1.000.000,00»; s.248 / u444di4775 / r60c10 = «4.000.000,00»; s.248 / u444di4775 / r61c10 = «1.812.500,00»; s.248 / u444di4775 / r62c10 = «1.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 2 | 4.400.000,00 | 4.400.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 4 | 4.400.000,00 | 4.400.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 5 | 5.500.000,00 | 5.500.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 7 | 5.500.000,00 | 5.500.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 8 | 6.575.000,00 | 6.575.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 63 — (3.2) Çevreye Duyarlı ve Güvenli Yapılaşma | 10 | 6.575.000,00 | 6.575.000,00 | 0,00 | Kapsanan satırlar: 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 2 | 20.703.843,00 | 20.269.229,00 | 434.614,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c2 = «500.000,00»; s.248 / u444di4775 / r82c2 = «500.000,00»; s.248 / u444di4775 / r83c2 = «2.000.000,00»; s.248 / u444di4775 / r84c2 = «2.000.000,00»; s.248 / u444di4775 / r85c2 = «134.614,00»; s.248 / u444di4775 / r86c2 = «1.000.000,00»; s.248 / u444di4775 / r87c2 = «1.000.000,00»; s.248 / u444di4775 / r88c2 = «3.000.000,00»; s.248 / u444di4775 / r89c2 = «1.000.000,00»; s.248 / u444di4775 / r90c2 = «1.000.000,00»; s.248 / u444di4775 / r91c2 = «2.000.000,00»; s.248 / u444di4775 / r92c2 = «4.000.000,00»; s.248 / u444di4775 / r93c2 = «134.615,00»; s.248 / u444di4775 / r94c2 = «2.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 4 | 20.703.843,00 | 20.269.229,00 | 434.614,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c4 = «500.000,00»; s.248 / u444di4775 / r82c4 = «500.000,00»; s.248 / u444di4775 / r83c4 = «2.000.000,00»; s.248 / u444di4775 / r84c4 = «2.000.000,00»; s.248 / u444di4775 / r85c4 = «134.614,00»; s.248 / u444di4775 / r86c4 = «1.000.000,00»; s.248 / u444di4775 / r87c4 = «1.000.000,00»; s.248 / u444di4775 / r88c4 = «3.000.000,00»; s.248 / u444di4775 / r89c4 = «1.000.000,00»; s.248 / u444di4775 / r90c4 = «1.000.000,00»; s.248 / u444di4775 / r91c4 = «2.000.000,00»; s.248 / u444di4775 / r92c4 = «4.000.000,00»; s.248 / u444di4775 / r93c4 = «134.615,00»; s.248 / u444di4775 / r94c4 = «2.000.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 5 | 21.483.049,00 | 21.633.049,00 | -150.000,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c5 = «500.000,00»; s.248 / u444di4775 / r82c5 = «500.000,00»; s.248 / u444di4775 / r83c5 = «2.000.000,00»; s.248 / u444di4775 / r84c5 = «2.000.000,00»; s.248 / u444di4775 / r85c5 = «816.524,50»; s.248 / u444di4775 / r86c5 = «1.000.000,00»; s.248 / u444di4775 / r87c5 = «1.000.000,00»; s.248 / u444di4775 / r88c5 = «3.000.000,00»; s.248 / u444di4775 / r89c5 = «1.000.000,00»; s.248 / u444di4775 / r90c5 = «1.000.000,00»; s.248 / u444di4775 / r91c5 = «2.000.000,00»; s.248 / u444di4775 / r92c5 = «4.000.000,00»; s.248 / u444di4775 / r93c5 = «816.524,50»; s.248 / u444di4775 / r94c5 = «2.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 7 | 21.483.049,00 | 21.633.049,00 | -150.000,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c7 = «500.000,00»; s.248 / u444di4775 / r82c7 = «500.000,00»; s.248 / u444di4775 / r83c7 = «2.000.000,00»; s.248 / u444di4775 / r84c7 = «2.000.000,00»; s.248 / u444di4775 / r85c7 = «816.524,50»; s.248 / u444di4775 / r86c7 = «1.000.000,00»; s.248 / u444di4775 / r87c7 = «1.000.000,00»; s.248 / u444di4775 / r88c7 = «3.000.000,00»; s.248 / u444di4775 / r89c7 = «1.000.000,00»; s.248 / u444di4775 / r90c7 = «1.000.000,00»; s.248 / u444di4775 / r91c7 = «2.000.000,00»; s.248 / u444di4775 / r92c7 = «4.000.000,00»; s.248 / u444di4775 / r93c7 = «816.524,50»; s.248 / u444di4775 / r94c7 = «2.000.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 8 | 19.777.794,00 | 20.652.794,00 | -875.000,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c8 = «500.000,00»; s.248 / u444di4775 / r82c8 = «500.000,00»; s.248 / u444di4775 / r83c8 = «2.000.000,00»; s.248 / u444di4775 / r84c8 = «2.000.000,00»; s.248 / u444di4775 / r85c8 = «326.397,00»; s.248 / u444di4775 / r86c8 = «1.000.000,00»; s.248 / u444di4775 / r87c8 = «1.000.000,00»; s.248 / u444di4775 / r88c8 = «3.000.000,00»; s.248 / u444di4775 / r89c8 = «1.000.000,00»; s.248 / u444di4775 / r90c8 = «1.000.000,00»; s.248 / u444di4775 / r91c8 = «2.000.000,00»; s.248 / u444di4775 / r92c8 = «4.000.000,00»; s.248 / u444di4775 / r93c8 = «326.397,00»; s.248 / u444di4775 / r94c8 = «2.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 80 — (3.3) Afetlere Yönelik Risk Azaltma, Hazırlık ve İyileştirme | 10 | 19.777.794,00 | 20.652.794,00 | -875.000,00 | Kapsanan satırlar: 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 Kanıt: s.248 / u444di4775 / r81c10 = «500.000,00»; s.248 / u444di4775 / r82c10 = «500.000,00»; s.248 / u444di4775 / r83c10 = «2.000.000,00»; s.248 / u444di4775 / r84c10 = «2.000.000,00»; s.248 / u444di4775 / r85c10 = «326.397,00»; s.248 / u444di4775 / r86c10 = «1.000.000,00»; s.248 / u444di4775 / r87c10 = «1.000.000,00»; s.248 / u444di4775 / r88c10 = «3.000.000,00»; s.248 / u444di4775 / r89c10 = «1.000.000,00»; s.248 / u444di4775 / r90c10 = «1.000.000,00»; s.248 / u444di4775 / r91c10 = «2.000.000,00»; s.248 / u444di4775 / r92c10 = «4.000.000,00»; s.248 / u444di4775 / r93c10 = «326.397,00»; s.248 / u444di4775 / r94c10 = «2.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 2 | 828.638.909,00 | 828.638.909,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 4 | 828.638.909,00 | 828.638.909,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 5 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 7 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 8 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 10 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | Kapsanan satırlar: 96 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 2 | 828.638.909,00 | 828.638.909,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 4 | 828.638.909,00 | 828.638.909,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 5 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 7 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 8 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 96 — (4.1) Karayolu Altyapısı ve Hizmetleri | 10 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | Kapsanan satırlar: 97, 98 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 2 | 144.100.000,00 | 144.100.000,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 4 | 144.100.000,00 | 144.100.000,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 5 | 213.658.966,00 | 213.658.966,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 7 | 213.658.966,00 | 213.658.966,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 8 | 256.580.170,00 | 256.580.170,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 10 | 256.580.170,00 | 256.580.170,00 | 0,00 | Kapsanan satırlar: 100, 105 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 2 | 136.100.000,00 | 136.100.000,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 4 | 136.100.000,00 | 136.100.000,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 5 | 203.658.966,00 | 203.658.966,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 7 | 203.658.966,00 | 203.658.966,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 8 | 244.080.170,00 | 244.080.170,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 100 — (5.1) Çevre ve Halk Sağlığının Korunması (Aydınlatma / Vektör) | 10 | 244.080.170,00 | 244.080.170,00 | 0,00 | Kapsanan satırlar: 101, 102, 103, 104 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 2 | 8.000.000,00 | 8.000.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 4 | 8.000.000,00 | 8.000.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 5 | 10.000.000,00 | 10.000.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 7 | 10.000.000,00 | 10.000.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 8 | 12.500.000,00 | 12.500.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 105 — (5.2) Zabıta Hizmetleri ve Kentsel Denetim | 10 | 12.500.000,00 | 12.500.000,00 | 0,00 | Kapsanan satırlar: 106 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 2 | 14.587.500,00 | 14.587.500,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 4 | 14.587.500,00 | 14.587.500,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 5 | 16.970.110,00 | 16.970.110,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 7 | 16.970.110,00 | 16.970.110,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 8 | 18.102.713,00 | 18.102.713,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 10 | 18.102.713,00 | 18.102.713,00 | 0,00 | Kapsanan satırlar: 108, 110, 112 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 2 | 3.000.000,00 | 3.000.000,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 4 | 3.000.000,00 | 3.000.000,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 5 | 3.828.577,00 | 3.828.577,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 7 | 3.828.577,00 | 3.828.577,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 8 | 4.500.000,00 | 4.500.000,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 108 — (6.1) Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 10 | 4.500.000,00 | 4.500.000,00 | 0,00 | Kapsanan satırlar: 109 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 2 | 6.087.500,00 | 6.087.500,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 4 | 6.087.500,00 | 6.087.500,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 5 | 6.937.954,00 | 6.937.954,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 7 | 6.937.954,00 | 6.937.954,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 8 | 7.020.359,00 | 7.020.359,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 110 — (6.2) Koruyucu Sağlık / Halk Sağlığının Korunması | 10 | 7.020.359,00 | 7.020.359,00 | 0,00 | Kapsanan satırlar: 111 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 2 | 5.500.000,00 | 5.500.000,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 4 | 5.500.000,00 | 5.500.000,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 5 | 6.203.579,00 | 6.203.579,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 7 | 6.203.579,00 | 6.203.579,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 8 | 6.582.354,00 | 6.582.354,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 112 — (6.3) Tedavi Edici Sağlık / Tedavi Hizmetleri | 10 | 6.582.354,00 | 6.582.354,00 | 0,00 | Kapsanan satırlar: 113 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 2 | 2.343.147,00 | 2.343.147,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 4 | 2.343.147,00 | 2.343.147,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 5 | 1.534.074,00 | 1.534.074,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 7 | 1.534.074,00 | 1.534.074,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 8 | 1.687.482,00 | 1.687.482,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 10 | 1.687.482,00 | 1.687.482,00 | 0,00 | Kapsanan satırlar: 115 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 2 | 2.343.147,00 | 2.343.147,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 4 | 2.343.147,00 | 2.343.147,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 5 | 1.534.074,00 | 1.534.074,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 7 | 1.534.074,00 | 1.534.074,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 8 | 1.687.482,00 | 1.687.482,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 115 — (7.1) Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | 10 | 1.687.482,00 | 1.687.482,00 | 0,00 | Kapsanan satırlar: 116 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 2 | 72.675.000,00 | 72.675.000,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 4 | 72.675.000,00 | 72.675.000,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 5 | 99.545.813,00 | 99.545.813,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 7 | 99.545.813,00 | 99.545.813,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 8 | 124.625.000,00 | 124.625.000,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 10 | 124.625.000,00 | 124.625.000,00 | 0,00 | Kapsanan satırlar: 118 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 2 | 72.675.000,00 | 72.675.000,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 4 | 72.675.000,00 | 72.675.000,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 5 | 99.545.813,00 | 99.545.813,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 7 | 99.545.813,00 | 99.545.813,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 8 | 124.625.000,00 | 124.625.000,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 118 — (8.1) Doğa Koruma ve Milli Parklar (Veterinerlik) | 10 | 124.625.000,00 | 124.625.000,00 | 0,00 | Kapsanan satırlar: 119, 120, 121, 122 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 2 | 838.307.912,00 | 838.307.912,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 4 | 838.307.912,00 | 838.307.912,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 5 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 7 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 8 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 10 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | Kapsanan satırlar: 124 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 2 | 838.307.912,00 | 838.307.912,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 4 | 838.307.912,00 | 838.307.912,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 5 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 7 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 8 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 124 — (9.1) Çevre Kirliliğinin Önlenmesi ve Koruma | 10 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | Kapsanan satırlar: 125, 126, 127, 128, 129, 130, 131, 132, 133, 134 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 2 | 9.171.747,00 | 9.171.747,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 4 | 9.171.747,00 | 9.171.747,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 5 | 9.476.838,00 | 9.476.838,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 7 | 9.476.838,00 | 9.476.838,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 8 | 8.417.000,00 | 8.417.000,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 10 | 8.417.000,00 | 8.417.000,00 | 0,00 | Kapsanan satırlar: 136, 142 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 2 | 8.571.747,00 | 8.571.747,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 4 | 8.571.747,00 | 8.571.747,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 5 | 8.776.838,00 | 8.776.838,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 7 | 8.776.838,00 | 8.776.838,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 8 | 7.697.000,00 | 7.697.000,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 136 — (10.1) Bitkisel Ürünlerde Arz Güvenliği | 10 | 7.697.000,00 | 7.697.000,00 | 0,00 | Kapsanan satırlar: 137, 138, 139, 140, 141 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 2 | 600.000,00 | 600.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 4 | 600.000,00 | 600.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 5 | 700.000,00 | 700.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 7 | 700.000,00 | 700.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 8 | 720.000,00 | 720.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 142 — (10.2) Tarımsal Araştırma ve Geliştirme | 10 | 720.000,00 | 720.000,00 | 0,00 | Kapsanan satırlar: 143, 144, 145 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 2 | 590.000,00 | 590.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 4 | 590.000,00 | 590.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 5 | 1.100.000,00 | 1.100.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 7 | 1.100.000,00 | 1.100.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 8 | 1.600.000,00 | 1.600.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 10 | 1.600.000,00 | 1.600.000,00 | 0,00 | Kapsanan satırlar: 147 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 2 | 590.000,00 | 590.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 4 | 590.000,00 | 590.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 5 | 1.100.000,00 | 1.100.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 7 | 1.100.000,00 | 1.100.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 8 | 1.600.000,00 | 1.600.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 147 — (11.1) Enerji Verimliliği ve İklim Eylemi | 10 | 1.600.000,00 | 1.600.000,00 | 0,00 | Kapsanan satırlar: 148, 149, 150, 151, 152 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 2 | 80.000.000,00 | 80.000.000,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 4 | 80.000.000,00 | 80.000.000,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 5 | 141.635.659,00 | 141.635.659,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 7 | 141.635.659,00 | 141.635.659,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 8 | 191.746.000,00 | 191.746.000,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 10 | 191.746.000,00 | 191.746.000,00 | 0,00 | Kapsanan satırlar: 154, 158, 167 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 2 | 8.050.000,00 | 8.050.000,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 4 | 8.050.000,00 | 8.050.000,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 5 | 16.882.450,00 | 16.882.450,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 7 | 16.882.450,00 | 16.882.450,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 8 | 21.103.050,00 | 21.103.050,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 154 — (12.1) Bilgi Kaynaklarına Erişim ile Türk Dili ve Kültürünün Güçlendirilmesi | 10 | 21.103.050,00 | 21.103.050,00 | 0,00 | Kapsanan satırlar: 155, 156, 157 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 2 | 40.935.750,00 | 40.935.750,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 4 | 40.935.750,00 | 40.935.750,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 5 | 78.490.930,00 | 78.490.930,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 7 | 78.490.930,00 | 78.490.930,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 8 | 106.877.340,00 | 106.877.340,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 158 — (12.2) Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisi | 10 | 106.877.340,00 | 106.877.340,00 | 0,00 | Kapsanan satırlar: 159, 160, 161, 162, 163, 164, 165, 166 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 2 | 31.014.250,00 | 29.014.250,00 | 2.000.000,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c2 = «3.373.750,00»; s.248 / u444di4775 / r169c2 = «2.845.000,00»; s.248 / u444di4775 / r170c2 = «20.400.000,00»; s.248 / u444di4775 / r171c2 = «1.100.000,00»; s.248 / u444di4775 / r172c2 = «1.295.500,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 4 | 31.014.250,00 | 29.014.250,00 | 2.000.000,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c4 = «3.373.750,00»; s.248 / u444di4775 / r169c4 = «2.845.000,00»; s.248 / u444di4775 / r170c4 = «20.400.000,00»; s.248 / u444di4775 / r171c4 = «1.100.000,00»; s.248 / u444di4775 / r172c4 = «1.295.500,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 5 | 46.262.279,00 | 46.293.570,00 | -31.291,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c5 = «5.325.000,00»; s.248 / u444di4775 / r169c5 = «4.692.500,00»; s.248 / u444di4775 / r170c5 = «32.373.570,00»; s.248 / u444di4775 / r171c5 = «1.775.000,00»; s.248 / u444di4775 / r172c5 = «2.127.500,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 7 | 46.262.279,00 | 46.293.570,00 | -31.291,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c7 = «5.325.000,00»; s.248 / u444di4775 / r169c7 = «4.692.500,00»; s.248 / u444di4775 / r170c7 = «32.373.570,00»; s.248 / u444di4775 / r171c7 = «1.775.000,00»; s.248 / u444di4775 / r172c7 = «2.127.500,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 8 | 63.765.610,00 | 63.866.975,00 | -101.365,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c8 = «6.840.000,00»; s.248 / u444di4775 / r169c8 = «6.045.625,00»; s.248 / u444di4775 / r170c8 = «46.275.725,00»; s.248 / u444di4775 / r171c8 = «1.976.250,00»; s.248 / u444di4775 / r172c8 = «2.729.375,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 167 — (12.3) Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | 10 | 63.765.610,00 | 63.866.975,00 | -101.365,00 | Kapsanan satırlar: 168, 169, 170, 171, 172 Kanıt: s.248 / u444di4775 / r168c10 = «6.840.000,00»; s.248 / u444di4775 / r169c10 = «6.045.625,00»; s.248 / u444di4775 / r170c10 = «46.275.725,00»; s.248 / u444di4775 / r171c10 = «1.976.250,00»; s.248 / u444di4775 / r172c10 = «2.729.375,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 2 | 54.270.630,00 | 54.270.630,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 4 | 54.270.630,00 | 54.270.630,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 5 | 81.146.442,00 | 81.146.442,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 7 | 81.146.442,00 | 81.146.442,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 8 | 92.146.534,00 | 92.146.534,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 10 | 92.146.534,00 | 92.146.534,00 | 0,00 | Kapsanan satırlar: 174 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 2 | 54.270.630,00 | 54.270.630,00 | 0,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 4 | 54.270.630,00 | 54.270.630,00 | 0,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 5 | 81.146.442,00 | 81.924.756,80 | -778.314,80 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 Kanıt: s.248 / u444di4775 / r175c5 = «22.206.756,00»; s.248 / u444di4775 / r176c5 = «5.424.000,00»; s.248 / u444di4775 / r177c5 = «11.124.000,00»; s.248 / u444di4775 / r178c5 = «1.084.000,00»; s.248 / u444di4775 / r179c5 = «2.884.000,00»; s.248 / u444di4775 / r180c5 = «16.224.000,00»; s.248 / u444di4775 / r181c5 = «16.944.000,00»; s.248 / u444di4775 / r182c5 = «3.150.000,00»; s.248 / u444di4775 / r183c5 = «2.884.000,80» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 7 | 81.146.442,00 | 81.924.756,80 | -778.314,80 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 Kanıt: s.248 / u444di4775 / r175c7 = «22.206.756,00»; s.248 / u444di4775 / r176c7 = «5.424.000,00»; s.248 / u444di4775 / r177c7 = «11.124.000,00»; s.248 / u444di4775 / r178c7 = «1.084.000,00»; s.248 / u444di4775 / r179c7 = «2.884.000,00»; s.248 / u444di4775 / r180c7 = «16.224.000,00»; s.248 / u444di4775 / r181c7 = «16.944.000,00»; s.248 / u444di4775 / r182c7 = «3.150.000,00»; s.248 / u444di4775 / r183c7 = «2.884.000,80» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 8 | 92.146.534,00 | 94.213.469,00 | -2.066.935,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 Kanıt: s.248 / u444di4775 / r175c8 = «25.537.769,00»; s.248 / u444di4775 / r176c8 = «6.237.600,00»; s.248 / u444di4775 / r177c8 = «12.792.600,00»; s.248 / u444di4775 / r178c8 = «1.246.600,00»; s.248 / u444di4775 / r179c8 = «3.316.600,00»; s.248 / u444di4775 / r180c8 = «18.657.600,00»; s.248 / u444di4775 / r181c8 = «19.485.600,00»; s.248 / u444di4775 / r182c8 = «3.622.500,00»; s.248 / u444di4775 / r183c8 = «3.316.600,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 174 — (13.1) Sporun ve Sporcuların Desteklenmesi | 10 | 92.146.534,00 | 94.213.469,00 | -2.066.935,00 | Kapsanan satırlar: 175, 176, 177, 178, 179, 180, 181, 182, 183 Kanıt: s.248 / u444di4775 / r175c10 = «25.537.769,00»; s.248 / u444di4775 / r176c10 = «6.237.600,00»; s.248 / u444di4775 / r177c10 = «12.792.600,00»; s.248 / u444di4775 / r178c10 = «1.246.600,00»; s.248 / u444di4775 / r179c10 = «3.316.600,00»; s.248 / u444di4775 / r180c10 = «18.657.600,00»; s.248 / u444di4775 / r181c10 = «19.485.600,00»; s.248 / u444di4775 / r182c10 = «3.622.500,00»; s.248 / u444di4775 / r183c10 = «3.316.600,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 2 | 43.010.974,00 | 43.010.974,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 4 | 43.010.974,00 | 43.010.974,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 5 | 49.431.122,00 | 49.431.122,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 7 | 49.431.122,00 | 49.431.122,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 8 | 56.665.674,00 | 56.665.674,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 10 | 56.665.674,00 | 56.665.674,00 | 0,00 | Kapsanan satırlar: 185 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 2 | 43.010.974,00 | 43.010.974,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 4 | 43.010.974,00 | 43.010.974,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 5 | 49.431.122,00 | 49.431.122,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 7 | 49.431.122,00 | 49.431.122,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 8 | 56.665.674,00 | 56.665.674,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 185 — (14.1) Yoksullukla Mücadele (Ayni ve Nakdi Yardımlar) | 10 | 56.665.674,00 | 56.665.674,00 | 0,00 | Kapsanan satırlar: 186, 187 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 2 | 18.500.000,00 | 18.500.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 4 | 18.500.000,00 | 18.500.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 5 | 23.500.000,00 | 23.500.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 7 | 23.500.000,00 | 23.500.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 8 | 25.000.000,00 | 25.000.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 10 | 25.000.000,00 | 25.000.000,00 | 0,00 | Kapsanan satırlar: 189, 191 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 2 | 16.500.000,00 | 16.500.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 4 | 16.500.000,00 | 16.500.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 5 | 21.000.000,00 | 21.000.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 7 | 21.000.000,00 | 21.000.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 8 | 22.000.000,00 | 22.000.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 189 — (15.1) Temel Eğitim ve Dezavantajlı Çocuklara Destek | 10 | 22.000.000,00 | 22.000.000,00 | 0,00 | Kapsanan satırlar: 190 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 2 | 2.000.000,00 | 2.000.000,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 4 | 2.000.000,00 | 2.000.000,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 5 | 2.500.000,00 | 2.500.000,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 7 | 2.500.000,00 | 2.500.000,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 8 | 3.000.000,00 | 3.000.000,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 192 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 191 — (15.2) Çocuklara Yönelik Koruyucu ve Önleyici Sosyal Hizmetler | 10 | 3.000.000,00 | 3.000.000,00 | 0,00 | Kapsanan satırlar: 192 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 2 | 3.189.780.044,00 | 4.053.415.705,00 | -863.635.661,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c2 = «1.132.975.122,00»; s.248 / u444di4775 / r30c2 = «3.400.000,00»; s.248 / u444di4775 / r35c2 = «810.844.764,00»; s.248 / u444di4775 / r95c2 = «828.638.909,00»; s.248 / u444di4775 / r99c2 = «144.100.000,00»; s.248 / u444di4775 / r107c2 = «14.587.500,00»; s.248 / u444di4775 / r114c2 = «2.343.147,00»; s.248 / u444di4775 / r117c2 = «72.675.000,00»; s.248 / u444di4775 / r123c2 = «838.307.912,00»; s.248 / u444di4775 / r135c2 = «9.171.747,00»; s.248 / u444di4775 / r146c2 = «590.000,00»; s.248 / u444di4775 / r153c2 = «80.000.000,00»; s.248 / u444di4775 / r173c2 = «54.270.630,00»; s.248 / u444di4775 / r184c2 = «43.010.974,00»; s.248 / u444di4775 / r188c2 = «18.500.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 4 | 3.189.780.044,00 | 4.053.415.705,00 | -863.635.661,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c4 = «1.132.975.122,00»; s.248 / u444di4775 / r30c4 = «3.400.000,00»; s.248 / u444di4775 / r35c4 = «810.844.764,00»; s.248 / u444di4775 / r95c4 = «828.638.909,00»; s.248 / u444di4775 / r99c4 = «144.100.000,00»; s.248 / u444di4775 / r107c4 = «14.587.500,00»; s.248 / u444di4775 / r114c4 = «2.343.147,00»; s.248 / u444di4775 / r117c4 = «72.675.000,00»; s.248 / u444di4775 / r123c4 = «838.307.912,00»; s.248 / u444di4775 / r135c4 = «9.171.747,00»; s.248 / u444di4775 / r146c4 = «590.000,00»; s.248 / u444di4775 / r153c4 = «80.000.000,00»; s.248 / u444di4775 / r173c4 = «54.270.630,00»; s.248 / u444di4775 / r184c4 = «43.010.974,00»; s.248 / u444di4775 / r188c4 = «18.500.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 5 | 5.026.960.693,50 | 6.125.958.225,50 | -1.098.997.532,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c5 = «1.464.002.665,00»; s.248 / u444di4775 / r30c5 = «3.650.000,00»; s.248 / u444di4775 / r35c5 = «1.182.029.090,50»; s.248 / u444di4775 / r95c5 = «1.614.907.446,00»; s.248 / u444di4775 / r99c5 = «213.658.966,00»; s.248 / u444di4775 / r107c5 = «16.970.110,00»; s.248 / u444di4775 / r114c5 = «1.534.074,00»; s.248 / u444di4775 / r117c5 = «99.545.813,00»; s.248 / u444di4775 / r123c5 = «1.223.370.000,00»; s.248 / u444di4775 / r135c5 = «9.476.838,00»; s.248 / u444di4775 / r146c5 = «1.100.000,00»; s.248 / u444di4775 / r153c5 = «141.635.659,00»; s.248 / u444di4775 / r173c5 = «81.146.442,00»; s.248 / u444di4775 / r184c5 = «49.431.122,00»; s.248 / u444di4775 / r188c5 = «23.500.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 7 | 5.026.960.693,50 | 6.125.958.225,50 | -1.098.997.532,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c7 = «1.464.002.665,00»; s.248 / u444di4775 / r30c7 = «3.650.000,00»; s.248 / u444di4775 / r35c7 = «1.182.029.090,50»; s.248 / u444di4775 / r95c7 = «1.614.907.446,00»; s.248 / u444di4775 / r99c7 = «213.658.966,00»; s.248 / u444di4775 / r107c7 = «16.970.110,00»; s.248 / u444di4775 / r114c7 = «1.534.074,00»; s.248 / u444di4775 / r117c7 = «99.545.813,00»; s.248 / u444di4775 / r123c7 = «1.223.370.000,00»; s.248 / u444di4775 / r135c7 = «9.476.838,00»; s.248 / u444di4775 / r146c7 = «1.100.000,00»; s.248 / u444di4775 / r153c7 = «141.635.659,00»; s.248 / u444di4775 / r173c7 = «81.146.442,00»; s.248 / u444di4775 / r184c7 = «49.431.122,00»; s.248 / u444di4775 / r188c7 = «23.500.000,00» |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 8 | 6.064.309.830,00 | 7.426.150.336,00 | -1.361.840.506,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c8 = «1.767.927.554,00»; s.248 / u444di4775 / r30c8 = «3.527.500,00»; s.248 / u444di4775 / r35c8 = «1.411.393.421,00»; s.248 / u444di4775 / r95c8 = «1.937.493.545,00»; s.248 / u444di4775 / r99c8 = «256.580.170,00»; s.248 / u444di4775 / r107c8 = «18.102.713,00»; s.248 / u444di4775 / r114c8 = «1.687.482,00»; s.248 / u444di4775 / r117c8 = «124.625.000,00»; s.248 / u444di4775 / r123c8 = «1.529.237.743,00»; s.248 / u444di4775 / r135c8 = «8.417.000,00»; s.248 / u444di4775 / r146c8 = «1.600.000,00»; s.248 / u444di4775 / r153c8 = «191.746.000,00»; s.248 / u444di4775 / r173c8 = «92.146.534,00»; s.248 / u444di4775 / r184c8 = «56.665.674,00»; s.248 / u444di4775 / r188c8 = «25.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 |
| FAIL | BOOK | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 193 — FAALİYET MALİYETLERİ ARA TOPLAMI | 10 | 6.064.309.830,00 | 7.426.150.336,00 | -1.361.840.506,00 | Kapsanan satırlar: 3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188 Kanıt: s.248 / u444di4775 / r3c10 = «1.767.927.554,00»; s.248 / u444di4775 / r30c10 = «3.527.500,00»; s.248 / u444di4775 / r35c10 = «1.411.393.421,00»; s.248 / u444di4775 / r95c10 = «1.937.493.545,00»; s.248 / u444di4775 / r99c10 = «256.580.170,00»; s.248 / u444di4775 / r107c10 = «18.102.713,00»; s.248 / u444di4775 / r114c10 = «1.687.482,00»; s.248 / u444di4775 / r117c10 = «124.625.000,00»; s.248 / u444di4775 / r123c10 = «1.529.237.743,00»; s.248 / u444di4775 / r135c10 = «8.417.000,00»; s.248 / u444di4775 / r146c10 = «1.600.000,00»; s.248 / u444di4775 / r153c10 = «191.746.000,00»; s.248 / u444di4775 / r173c10 = «92.146.534,00»; s.248 / u444di4775 / r184c10 = «56.665.674,00»; s.248 / u444di4775 / r188c10 = «25.000.000,00» |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 2 | 4.808.694.956,00 | 4.808.694.956,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 4 | 4.808.694.956,00 | 4.808.694.956,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 5 | 4.160.006.066,50 | 4.160.006.066,50 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 7 | 4.160.006.066,50 | 4.160.006.066,50 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 8 | 4.523.165.170,00 | 4.523.165.170,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 194 — KURUMSAL GENEL YÖNETİM GİDERLERİ (Personel, SGK ve Diğer Birimler) | 10 | 4.523.165.170,00 | 4.523.165.170,00 | 0,00 | Kapsanan satırlar: 195, 196 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 2 | 7.998.475.000,00 | 7.998.475.000,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 3 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 4 | 7.998.475.000,00 | 7.998.475.000,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 5 | 9.186.966.760,00 | 9.186.966.760,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 6 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 7 | 9.186.966.760,00 | 9.186.966.760,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 8 | 10.587.475.000,00 | 10.587.475.000,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 9 | 0,00 | 0,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| PASS | — | Sütun toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 197 — GENEL TOPLAM | 10 | 10.587.475.000,00 | 10.587.475.000,00 | 0,00 | Kapsanan satırlar: 193, 194 |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 4 | 1.132.975.122,00 | 4.277.347.655,00 | -3.144.372.533,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 77. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 7 | 1.464.002.665,00 | 5.953.827.451,00 | -4.489.824.786,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 77. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 3 — (1) YÖNETİM VE DESTEK PROGRAMI | 10 | 1.767.927.554,00 | 7.562.101.098,00 | -5.794.173.544,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 77. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 4 | 3.400.000,00 | 8.400.000,00 | -5.000.000,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 13. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 7 | 3.650.000,00 | 9.938.610,00 | -6.288.610,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 13. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 30 — (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 10 | 3.527.500,00 | 9.418.420,00 | -5.890.920,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 13. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 4 | 810.844.764,00 | 828.821.869,00 | -17.977.105,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 71. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 7 | 1.182.029.090,50 | 1.212.368.756,00 | -30.339.665,50 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 71. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 35 — (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 10 | 1.411.393.421,00 | 1.445.247.450,00 | -33.854.029,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 71. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 4 | 828.638.909,00 | 828.638.909,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 2. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 7 | 1.614.907.446,00 | 1.614.907.446,00 | 0,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 2. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 95 — (4) KENT İÇİ ULAŞIM | 10 | 1.937.493.545,00 | 1.937.493.545,00 | 0,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 2. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 4 | 144.100.000,00 | Bilinmiyor | Bilinmiyor | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 7 | 213.658.966,00 | Bilinmiyor | Bilinmiyor | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 99 — (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 10 | 256.580.170,00 | Bilinmiyor | Bilinmiyor | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 4 | 14.587.500,00 | Bilinmiyor | Bilinmiyor | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 7 | 16.970.110,00 | Bilinmiyor | Bilinmiyor | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 107 — (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 10 | 18.102.713,00 | Bilinmiyor | Bilinmiyor | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 4 | 2.343.147,00 | Bilinmiyor | Bilinmiyor | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 7 | 1.534.074,00 | Bilinmiyor | Bilinmiyor | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 114 — (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 10 | 1.687.482,00 | Bilinmiyor | Bilinmiyor | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 4 | 72.675.000,00 | Bilinmiyor | Bilinmiyor | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 7 | 99.545.813,00 | Bilinmiyor | Bilinmiyor | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 117 — (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 10 | 124.625.000,00 | Bilinmiyor | Bilinmiyor | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 0. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 4 | 838.307.912,00 | 838.307.912,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 7 | 1.223.370.000,00 | 1.223.370.000,00 | 0,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 123 — (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 10 | 1.529.237.743,00 | 1.529.237.743,00 | 0,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 4 | 9.171.747,00 | 9.171.747,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 7 | 9.476.838,00 | 9.576.838,00 | -100.000,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 135 — (10) TARIM PROGRAMI | 10 | 8.417.000,00 | 8.517.000,00 | -100.000,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 11. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 4 | 590.000,00 | 590.000,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 5. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 7 | 1.100.000,00 | 1.100.000,00 | 0,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 5. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 146 — (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 10 | 1.600.000,00 | 1.600.000,00 | 0,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 5. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 4 | 80.000.000,00 | 80.000.000,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 17. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 7 | 141.635.659,00 | 140.927.750,00 | 707.909,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 17. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 153 — (12) MİLLİ KÜLTÜR | 10 | 191.746.000,00 | 191.746.000,00 | 0,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 17. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 4 | 54.270.630,00 | 54.270.630,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 7 | 81.146.442,00 | 77.148.000,00 | 3.998.442,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 173 — (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 10 | 92.146.534,00 | 88.367.100,00 | 3.779.434,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 4 | 43.010.974,00 | 43.010.974,00 | 0,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 7 | 49.431.122,00 | 49.431.122,00 | 0,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 184 — (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 10 | 56.665.674,00 | 56.665.674,00 | 0,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 10. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 4 | 18.500.000,00 | 2.000.000,00 | 16.500.000,00 | 2027: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 4. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 7 | 23.500.000,00 | 2.500.000,00 | 21.000.000,00 | 2028: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 4. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Müdürlük program çapraz toplamı | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | 188 — (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 10 | 25.000.000,00 | 3.000.000,00 | 22.000.000,00 | 2029: kartlara bağlı üyelik tablolarındaki program tutarları; ekonomik kategoriler programlara paylaştırılmadı. Katkı hücresi: 4. Faaliyet kapsamları eşleşmiyor veya tekil dağılım yok (CHECK); hesaplanan tutar tanısal aday toplamdır, basılı toplamın düzeltmesi değildir. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Çocukların Korunması ve Gelişiminin Sağlanması | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Kamu Gelirleri Yönetimi | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Kent Güvenliği ve Esenliği | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — KENT GÜVENLİĞİ VE ESTETİĞİ | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Kent Güvenliği ve Sağlığı | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Koruyucu Sağlık | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Ormanların ve Doğanın Korunması İle Sürdürülebilir Yönetimi | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Tedavi Edici Sağlık | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Temel Eğitim | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Ticaretin Düzenlenmesi, Geliştirilmesi ve Kolaylaştırılması | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Tüketicinin korunması, ürün ve hizmetlerin güvenliği ve standardizasyonu | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Vatandaşlık ve Sivil Toplum Programı | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |
| FAIL | CHECK | Program adı eşlemesi | 248 | u444di4775 — Ekonomik kod / program ve faaliyet ayrıntısı | — — Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı | 1 | «BOŞ» | Bilinmiyor | Bilinmiyor | Müdürlük program adı kurum ayrıntısındaki program adıyla eşleşmiyor; taksonomi eşlemesini Strateji teyit etmelidir. Tutarlardan program eşlemesi üretilmedi. |

### Büyük farklar — katkı ve kapsam kanıtı

Aşağıdaki hesaplar kaynak hücrelerine kadar izlenir. CHECK satırındaki hesaplanan tutar tanısal aday toplamdır; farklı faaliyet kapsamlarını eşit kabul etmez ve basılı tutarın düzeltmesi değildir. UNKNOWN, iki basılı kaynak arasındaki farkın hangi taraftan geldiğinin belirlenemediğini gösterir. Kart listesi kaynak bağlamıdır; aynı ekonomik hücre kart sayısı ile çarpılmaz. Tüm kaynak hücreleri fiziksel tablo / satır / sütun kimliğine göre bir kez sayılır.

#### Kanıt 1 — s.244 / u40c3i5faa / r5c9

Sınıf: **UNKNOWN**; basılı: **6.318.477.429,00**; hesaplanan: **7.491.284.414,00**; Fark: **-1.172.806.985,00**.

Kurum hücresi aynı kategorinin basılı program-grubu sütunlarını kapsar. Müdürlük hesabı her ekonomik kaynak hücresini bir kez içerir; kart sayısı ile çarpılmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.244 / u40c3i5faa / r5c6 | Mal ve Hizmet Alım Giderleri | 2.188.395.151,00 |
| s.244 / u40c3i5faa / r5c7 | Mal ve Hizmet Alım Giderleri | 4.130.082.278,00 |
| s.244 / u40c3i5faa / r5c8 | Mal ve Hizmet Alım Giderleri | 0,00 |

Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Sağlık İşleri Müdürlüğü | s.94 / u2e07i5fc9 r2c2 / r4c2; Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim / Engelli Bakımı; s.95 / u2e1di5ddf r2c2 / r4c2; Kent Güvenliği ve Esenliği / Çevre Ve Halk Sağlığının Korunması; s.96 / u2e3ci5db8 r2c2 / r4c2; Koruyucu Sağlık / Halk Sağlığının Korunması; s.97 / u2e52i5d96 r2c2 / r4c2; Tedavi Edici Sağlık / Tedavi Hizmetleri | s.98 / u2e71i602c / r4c5 | Mal ve Hizmet Alım Giderleri | 17.595.110,00 | 17.595.110,00 |
| Ruhsat ve Denetim Müdürlüğü | s.100 / u2ebdi5d69 r2c2 / r4c2; Tüketicinin korunması, ürün ve hizmetlerin güvenliği ve standardizasyonu / Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | s.101 / u2ea7i5e29 / r4c5 | Mal ve Hizmet Alım Giderleri | 1.534.074,00 | 1.534.074,00 |
| Zabıta Müdürlüğü | s.102 / u2edci5d3e r2c2 / r4c2; KENT GÜVENLİĞİ VE ESTETİĞİ / ZABITA HİZMETLERİ (Zabıta Denetim ve Kontrol Faaliyetleri); s.103 / u2ef2i5d11 r2c2 / r4c2; KENT GÜVENLİĞİ VE ESTETİĞİ / ZABITA HİZMETLERİ (Diğer Zabıta Hizmetleri) | s.104 / u2f11i5d01 / r4c5 | Mal ve Hizmet Alım Giderleri | 8.750.000,00 | 8.750.000,00 |
| Veteriner İşleri Müdürlüğü | s.106 / u2f47i5c95 r2c2 / r4c2; Ormanların ve Doğanın Korunması İle Sürdürülebilir Yönetimi / Doğa Koruma ve Milli Parklar | s.107 / u2f5di5c86 / r4c5 | Mal ve Hizmet Alım Giderleri | 84.045.813,00 | 84.045.813,00 |
| Emlak İstimlak Müdürlüğü | s.110 / u2ff7i5c39 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.111 / u300di5c04 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.112 / u3043i5bf4 / r4c5 | Mal ve Hizmet Alım Giderleri | 114.418.323,00 | 114.418.323,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.116 / u30b0i5b0f r2c2 / r4c2; Kent İçi Ulaşım / Karayolu Altyapısı ve Hizmetleri; s.117 / u30c6i5ae5 r2c2 / r4c2; Kent Güvenliği ve Sağlığı / Çevre ve Halk Sağlığının Korunması | s.118 / u30e5i5ad5 / r4c5 | Mal ve Hizmet Alım Giderleri | 302.948.429,00 | 302.948.429,00 |
| İmar ve Şehircilik Müdürlüğü | s.120 / u313fi5a73 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma; s.121 / u3155i5a42 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma | s.122 / u3174i59fa / r4c5 | Mal ve Hizmet Alım Giderleri | 3.000.000,00 | 3.000.000,00 |
| Park ve Bahçeler Müdürlüğü | s.125 / u31c1i58f6 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.127 / u3227i58cf r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.128 / u3254i5862 / r4c5 | Mal ve Hizmet Alım Giderleri | 623.050.000,00 | 623.050.000,00 |
| Etüd Proje Müdürlüğü | s.131 / u32a1i57e2 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma; s.132 / u32c0i57bb r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.133 / u32d6i57ac / r4c5 | Mal ve Hizmet Alım Giderleri | 3.125.000,00 | 3.125.000,00 |
| Plan Proje Müdürlüğü | s.135 / u330ci573a r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.136 / u332bi572b / r4c5 | Mal ve Hizmet Alım Giderleri | 5.972.384,00 | 5.972.384,00 |
| Kentsel Dönüşüm Müdürlüğü | s.138 / u33a5i56ec r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.139 / u33bbi56dd / r4c5 | Mal ve Hizmet Alım Giderleri | 6.250.000,00 | 6.250.000,00 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | s.141 / u33f1i5682 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Afet İyileştirme Çalışmaları; s.143 / u3434i5614 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Afet İyileştirme Çalışmaları | s.144 / u345fi5604 / r4c5 | Mal ve Hizmet Alım Giderleri | 21.633.049,00 | 21.633.049,00 |
| Temizlik İşleri Müdürlüğü | s.148 / u3510i5571 r2c2 / r4c2; Sürdürülebilir Çevre ve İklim Değişikliği / Çevre Kirliliğinin Önlenmesi ve Koruma | s.150 / u3550i5562 / r4c5 | Mal ve Hizmet Alım Giderleri | 1.200.670.000,00 | 1.200.670.000,00 |
| Çevre Koruma ve Kontrol Müdürlüğü | s.152 / u3596i5506 r2c2 / r4c2; Sürdürülebilir Çevre ve İklim Değişikliği / Çevre Kirliliğinin Önlenmesi ve Koruma | s.153 / u35aci54f7 / r4c5 | Mal ve Hizmet Alım Giderleri | 2.700.000,00 | 2.700.000,00 |
| Tarımsal Hizmetler Müdürlüğü | s.154 / u35cbi54ac r2c2 / r4c2; Tarım Programı / Bitkisel Ürünlerde Arz Güvenliği; s.155 / u35e1i5480 r2c2 / r4c2; Tarım Programı / Tarımsal Araştırma ve Geliştirme | s.156 / u3600i546f / r4c5 | Mal ve Hizmet Alım Giderleri | 4.900.000,00 | 4.900.000,00 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | s.158 / u3636i5402 r2c2 / r4c2; Enerji Arz Güvenliği, Verimliliği ve Enerji Piyasası / Enerji Verimliliği | s.159 / u364ci53f3 / r4c5 | Mal ve Hizmet Alım Giderleri | 1.100.000,00 | 1.100.000,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | s.162 / u36dfi53a3 r2c2 / r4c2; Milli Kültür / Bilgi Kaynaklarına Erişim İle Türk Dili, Edebiyatı ve Kültürünün Güçlendirilmesi; s.163 / u36f5i5379 r2c2 / r4c2; Milli Kültür / Milli Kültür/Bilgi Kaynaklarına Erişim İle Türk Dili, Edebiyatı ve Kültürünün Güçlendirilmesi; s.164 / u3714i534f r2c2 / r4c2; Milli Kültür / Sanat ve Kültür Ekonomisi/Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisinin Geliştirilmesi; s.165 / u372ai5327 r2c2 / r4c2; Milli Kültür / Sanat ve Kültür Ekonomisi/Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisinin Geliştirilmesi; s.166 / u3749i52fa r2c2 / r4c2; Milli Kültür / Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | s.167 / u375fi52ea / r4c5 | Mal ve Hizmet Alım Giderleri | 141.635.659,00 | 141.635.659,00 |
| Gençlik ve Spor İşleri Müdürlüğü | s.170 / u37cci5256 r2c2 / r4c2; SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ / Sporun ve Sporcuların Desteklenmesi; s.172 / u3811i5229 r2c2 / r4c2; Sporun Geliştirilmesi Ve Desteklenmesi / Sporun ve Sporcuların Desteklenmesi | s.173 / u3827i5219 / r4c5 | Mal ve Hizmet Alım Giderleri | 76.387.666,00 | 76.387.666,00 |
| Sosyal Destek Müdürlüğü | s.175 / u385di51ac r2c2 / r4c2; Yoksullukla Mücadele Ve Yardımlaşma / Yoksullukla Mücadele; s.176 / u387ci517f r2c2 / r4c2; Yoksullukla Mücadele Ve Yardımlaşma / Yoksullukla Mücadele; s.177 / u3892i5152 r2c2 / r4c2; Temel Eğitim / Eğitime Erişim Ve Fırsat Eşitliği; s.178 / u38b1i5126 r2c2 / r4c2; Sosyal Koruma Ve Sosyal Hizmetler Programı / Çocuklara Yönelik Koruyucu Ve Önleyici Sosyal Hizmetler | s.179 / u38dei5117 / r4c5 | Mal ve Hizmet Alım Giderleri | 3.250.000,00 | 3.250.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.186 / u39ffi5064 / r4c5 | Mal ve Hizmet Alım Giderleri | 5.470.481,00 | 5.470.481,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum; s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.192 / u3a9fi4f77 / r4c5 | Mal ve Hizmet Alım Giderleri | 58.769.674,00 | 58.769.674,00 |
| Araştırma ve Geliştirme Müdürlüğü | s.194 / u3ad5i4f05 r2c2 / r4c2; Araştırma, Geliştirme Ve Yenilik / Deneysel Geliştirme | s.195 / u3aebi4ef6 / r4c5 | Mal ve Hizmet Alım Giderleri | 3.650.000,00 | 3.650.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.199 / u3b9bi4e82 / r4c5 | Mal ve Hizmet Alım Giderleri | 25.062.500,00 | 25.062.500,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.201 / u3bd1i4e33 r2c2 / r4c2; Araştırma, Geliştirme ve Yenilik / Bilim, Teknoloji ve Yenilik Kültürü İle İnsan Kaynağının Geliştirilmesi; s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.203 / u3c11i4df7 / r4c5 | Mal ve Hizmet Alım Giderleri | 10.877.216,00 | 10.877.216,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.207 / u3c7di4d7b / r4c5 | Mal ve Hizmet Alım Giderleri | 409.500.000,00 | 409.500.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.210 / u3cd2i4d1b / r4c5 | Mal ve Hizmet Alım Giderleri | 187.000,00 | 187.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.212 / u3d07i4cc3 / r4c5 | Mal ve Hizmet Alım Giderleri | 38.595.240,00 | 38.595.240,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.215 / u3d6ai4c57 / r4c5 | Mal ve Hizmet Alım Giderleri | 2.275.528,00 | 2.275.528,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.219 / u3dd5i4bc0 / r4c5 | Mal ve Hizmet Alım Giderleri | 3.612.925.804,00 | 3.612.925.804,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.222 / u3e2ai4b54 / r4c5 | Mal ve Hizmet Alım Giderleri | 320.792.302,00 | 320.792.302,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.226 / u3ea0i4aba r2c2 / r4c2; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı / Sosyal Yardımlaşma; s.227 / u3eb6i4a8a r2c2 / r4c2; Vatandaşlık ve Sivil Toplum Programı / Nüfus ve Vatandaşlık Hizmetleri | s.228 / u3ed5i4a7a / r4c5 | Mal ve Hizmet Alım Giderleri | 14.073.382,00 | 14.073.382,00 |
| Gelirler Müdürlüğü | s.230 / u3f0bi4a04 r2c2 / r4c2; Kamu Gelirleri Yönetimi / Kamu Gelirlerinin Toplanması | s.232 / u3f4fi49f4 / r4c5 | Mal ve Hizmet Alım Giderleri | 2.567.600,00 | 2.567.600,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.236 / u3fc8i497d / r4c5 | Mal ve Hizmet Alım Giderleri | 259.909.180,00 | 259.909.180,00 |
| İşletme ve İştirakler Müdürlüğü | s.238 / u400ai4705 r2c2 / r4c2; Çocukların Korunması ve Gelişiminin Sağlanması / Çocukların Gelişimi; s.239 / u4020i46e2 r2c2 / r4c2; Ticaretin Düzenlenmesi, Geliştirilmesi ve Kolaylaştırılması / İç Ticaretin Düzenlenmesi ve Geliştirilmesi; s.240 / u403fi46c0 r2c2 / r4c2; Kamu Gelirleri Yönetimi / Kamu Gelirlerinin Toplanması | s.241 / u4055i46b1 / r4c5 | Mal ve Hizmet Alım Giderleri | 103.663.000,00 | 103.663.000,00 |

Tekil kaynak hücresi: 34; katkılar toplamı: 7.491.284.414,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.

#### Kanıt 2 — s.244 / u40c3i5faa / r5c13

Sınıf: **UNKNOWN**; basılı: **7.708.542.463,00**; hesaplanan: **9.464.585.675,00**; Fark: **-1.756.043.212,00**.

Kurum hücresi aynı kategorinin basılı program-grubu sütunlarını kapsar. Müdürlük hesabı her ekonomik kaynak hücresini bir kez içerir; kart sayısı ile çarpılmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.244 / u40c3i5faa / r5c10 | Mal ve Hizmet Alım Giderleri | 2.669.842.084,00 |
| s.244 / u40c3i5faa / r5c11 | Mal ve Hizmet Alım Giderleri | 5.038.700.379,00 |
| s.244 / u40c3i5faa / r5c12 | Mal ve Hizmet Alım Giderleri | 0,00 |

Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Sağlık İşleri Müdürlüğü | s.94 / u2e07i5fc9 r2c2 / r4c2; Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim / Engelli Bakımı; s.95 / u2e1di5ddf r2c2 / r4c2; Kent Güvenliği ve Esenliği / Çevre Ve Halk Sağlığının Korunması; s.96 / u2e3ci5db8 r2c2 / r4c2; Koruyucu Sağlık / Halk Sağlığının Korunması; s.97 / u2e52i5d96 r2c2 / r4c2; Tedavi Edici Sağlık / Tedavi Hizmetleri | s.98 / u2e71i602c / r4c6 | Mal ve Hizmet Alım Giderleri | 18.520.359,00 | 18.520.359,00 |
| Ruhsat ve Denetim Müdürlüğü | s.100 / u2ebdi5d69 r2c2 / r4c2; Tüketicinin korunması, ürün ve hizmetlerin güvenliği ve standardizasyonu / Gıda Güvenilirliğini Sağlamaya Yönelik Faaliyetler | s.101 / u2ea7i5e29 / r4c6 | Mal ve Hizmet Alım Giderleri | 1.687.482,00 | 1.687.482,00 |
| Zabıta Müdürlüğü | s.102 / u2edci5d3e r2c2 / r4c2; KENT GÜVENLİĞİ VE ESTETİĞİ / ZABITA HİZMETLERİ (Zabıta Denetim ve Kontrol Faaliyetleri); s.103 / u2ef2i5d11 r2c2 / r4c2; KENT GÜVENLİĞİ VE ESTETİĞİ / ZABITA HİZMETLERİ (Diğer Zabıta Hizmetleri) | s.104 / u2f11i5d01 / r4c6 | Mal ve Hizmet Alım Giderleri | 10.937.500,00 | 10.937.500,00 |
| Veteriner İşleri Müdürlüğü | s.106 / u2f47i5c95 r2c2 / r4c2; Ormanların ve Doğanın Korunması İle Sürdürülebilir Yönetimi / Doğa Koruma ve Milli Parklar | s.107 / u2f5di5c86 / r4c6 | Mal ve Hizmet Alım Giderleri | 105.500.000,00 | 105.500.000,00 |
| Emlak İstimlak Müdürlüğü | s.110 / u2ff7i5c39 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.111 / u300di5c04 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.112 / u3043i5bf4 / r4c6 | Mal ve Hizmet Alım Giderleri | 136.466.584,00 | 136.466.584,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.116 / u30b0i5b0f r2c2 / r4c2; Kent İçi Ulaşım / Karayolu Altyapısı ve Hizmetleri; s.117 / u30c6i5ae5 r2c2 / r4c2; Kent Güvenliği ve Sağlığı / Çevre ve Halk Sağlığının Korunması | s.118 / u30e5i5ad5 / r4c6 | Mal ve Hizmet Alım Giderleri | 367.084.546,00 | 367.084.546,00 |
| İmar ve Şehircilik Müdürlüğü | s.120 / u313fi5a73 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma; s.121 / u3155i5a42 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma | s.122 / u3174i59fa / r4c6 | Mal ve Hizmet Alım Giderleri | 3.450.000,00 | 3.450.000,00 |
| Park ve Bahçeler Müdürlüğü | s.125 / u31c1i58f6 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.127 / u3227i58cf r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.128 / u3254i5862 / r4c6 | Mal ve Hizmet Alım Giderleri | 774.300.000,00 | 774.300.000,00 |
| Etüd Proje Müdürlüğü | s.131 / u32a1i57e2 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Çevreye Duyarlı ve Güvenli Yapılaşma; s.132 / u32c0i57bb r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.133 / u32d6i57ac / r4c6 | Mal ve Hizmet Alım Giderleri | 3.906.250,00 | 3.906.250,00 |
| Plan Proje Müdürlüğü | s.135 / u330ci573a r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.136 / u332bi572b / r4c6 | Mal ve Hizmet Alım Giderleri | 3.395.323,00 | 3.395.323,00 |
| Kentsel Dönüşüm Müdürlüğü | s.138 / u33a5i56ec r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.139 / u33bbi56dd / r4c6 | Mal ve Hizmet Alım Giderleri | 7.812.500,00 | 7.812.500,00 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | s.141 / u33f1i5682 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Afet İyileştirme Çalışmaları; s.143 / u3434i5614 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Afet İyileştirme Çalışmaları | s.144 / u345fi5604 / r4c6 | Mal ve Hizmet Alım Giderleri | 20.652.794,00 | 20.652.794,00 |
| Temizlik İşleri Müdürlüğü | s.148 / u3510i5571 r2c2 / r4c2; Sürdürülebilir Çevre ve İklim Değişikliği / Çevre Kirliliğinin Önlenmesi ve Koruma | s.150 / u3550i5562 / r4c6 | Mal ve Hizmet Alım Giderleri | 1.500.837.743,00 | 1.500.837.743,00 |
| Çevre Koruma ve Kontrol Müdürlüğü | s.152 / u3596i5506 r2c2 / r4c2; Sürdürülebilir Çevre ve İklim Değişikliği / Çevre Kirliliğinin Önlenmesi ve Koruma | s.153 / u35aci54f7 / r4c6 | Mal ve Hizmet Alım Giderleri | 3.400.000,00 | 3.400.000,00 |
| Tarımsal Hizmetler Müdürlüğü | s.154 / u35cbi54ac r2c2 / r4c2; Tarım Programı / Bitkisel Ürünlerde Arz Güvenliği; s.155 / u35e1i5480 r2c2 / r4c2; Tarım Programı / Tarımsal Araştırma ve Geliştirme | s.156 / u3600i546f / r4c6 | Mal ve Hizmet Alım Giderleri | 5.347.000,00 | 5.347.000,00 |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | s.158 / u3636i5402 r2c2 / r4c2; Enerji Arz Güvenliği, Verimliliği ve Enerji Piyasası / Enerji Verimliliği | s.159 / u364ci53f3 / r4c6 | Mal ve Hizmet Alım Giderleri | 1.600.000,00 | 1.600.000,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | s.162 / u36dfi53a3 r2c2 / r4c2; Milli Kültür / Bilgi Kaynaklarına Erişim İle Türk Dili, Edebiyatı ve Kültürünün Güçlendirilmesi; s.163 / u36f5i5379 r2c2 / r4c2; Milli Kültür / Milli Kültür/Bilgi Kaynaklarına Erişim İle Türk Dili, Edebiyatı ve Kültürünün Güçlendirilmesi; s.164 / u3714i534f r2c2 / r4c2; Milli Kültür / Sanat ve Kültür Ekonomisi/Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisinin Geliştirilmesi; s.165 / u372ai5327 r2c2 / r4c2; Milli Kültür / Sanat ve Kültür Ekonomisi/Sanatın Desteklenmesi, Sahnelenmesi ve Kültür Ekonomisinin Geliştirilmesi; s.166 / u3749i52fa r2c2 / r4c2; Milli Kültür / Hayat Boyu Öğrenme - Eğitime Erişim ve Fırsat Eşitliği | s.167 / u375fi52ea / r4c6 | Mal ve Hizmet Alım Giderleri | 191.746.000,00 | 191.746.000,00 |
| Gençlik ve Spor İşleri Müdürlüğü | s.170 / u37cci5256 r2c2 / r4c2; SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ / Sporun ve Sporcuların Desteklenmesi; s.172 / u3811i5229 r2c2 / r4c2; Sporun Geliştirilmesi Ve Desteklenmesi / Sporun ve Sporcuların Desteklenmesi | s.173 / u3827i5219 / r4c6 | Mal ve Hizmet Alım Giderleri | 85.673.965,00 | 85.673.965,00 |
| Sosyal Destek Müdürlüğü | s.175 / u385di51ac r2c2 / r4c2; Yoksullukla Mücadele Ve Yardımlaşma / Yoksullukla Mücadele; s.176 / u387ci517f r2c2 / r4c2; Yoksullukla Mücadele Ve Yardımlaşma / Yoksullukla Mücadele; s.177 / u3892i5152 r2c2 / r4c2; Temel Eğitim / Eğitime Erişim Ve Fırsat Eşitliği; s.178 / u38b1i5126 r2c2 / r4c2; Sosyal Koruma Ve Sosyal Hizmetler Programı / Çocuklara Yönelik Koruyucu Ve Önleyici Sosyal Hizmetler | s.179 / u38dei5117 / r4c6 | Mal ve Hizmet Alım Giderleri | 3.900.000,00 | 3.900.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.186 / u39ffi5064 / r4c6 | Mal ve Hizmet Alım Giderleri | 5.605.000,00 | 5.605.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum; s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.192 / u3a9fi4f77 / r4c6 | Mal ve Hizmet Alım Giderleri | 68.608.393 | 68.608.393,00 |
| Araştırma ve Geliştirme Müdürlüğü | s.194 / u3ad5i4f05 r2c2 / r4c2; Araştırma, Geliştirme Ve Yenilik / Deneysel Geliştirme | s.195 / u3aebi4ef6 / r4c6 | Mal ve Hizmet Alım Giderleri | 3.527.500,00 | 3.527.500,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.199 / u3b9bi4e82 / r4c6 | Mal ve Hizmet Alım Giderleri | 24.203.125,00 | 24.203.125,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.201 / u3bd1i4e33 r2c2 / r4c2; Araştırma, Geliştirme ve Yenilik / Bilim, Teknoloji ve Yenilik Kültürü İle İnsan Kaynağının Geliştirilmesi; s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.203 / u3c11i4df7 / r4c6 | Mal ve Hizmet Alım Giderleri | 9.981.840,00 | 9.981.840,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.207 / u3c7di4d7b / r4c6 | Mal ve Hizmet Alım Giderleri | 705.000.000,00 | 705.000.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.210 / u3cd2i4d1b / r4c6 | Mal ve Hizmet Alım Giderleri | 233.750,00 | 233.750,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.212 / u3d07i4cc3 / r4c6 | Mal ve Hizmet Alım Giderleri | 42.097.624,00 | 42.097.624,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.215 / u3d6ai4c57 / r4c6 | Mal ve Hizmet Alım Giderleri | 1.881.614,00 | 1.881.614,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.219 / u3dd5i4bc0 / r4c6 | Mal ve Hizmet Alım Giderleri | 4.526.157.255,00 | 4.526.157.255,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.222 / u3e2ai4b54 / r4c6 | Mal ve Hizmet Alım Giderleri | 349.400.762,00 | 349.400.762,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.226 / u3ea0i4aba r2c2 / r4c2; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı / Sosyal Yardımlaşma; s.227 / u3eb6i4a8a r2c2 / r4c2; Vatandaşlık ve Sivil Toplum Programı / Nüfus ve Vatandaşlık Hizmetleri | s.228 / u3ed5i4a7a / r4c6 | Mal ve Hizmet Alım Giderleri | 13.592.495,00 | 13.592.495,00 |
| Gelirler Müdürlüğü | s.230 / u3f0bi4a04 r2c2 / r4c2; Kamu Gelirleri Yönetimi / Kamu Gelirlerinin Toplanması | s.232 / u3f4fi49f4 / r4c6 | Mal ve Hizmet Alım Giderleri | 3.200.016,00 | 3.200.016,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.236 / u3fc8i497d / r4c6 | Mal ve Hizmet Alım Giderleri | 353.442.255,00 | 353.442.255,00 |
| İşletme ve İştirakler Müdürlüğü | s.238 / u400ai4705 r2c2 / r4c2; Çocukların Korunması ve Gelişiminin Sağlanması / Çocukların Gelişimi; s.239 / u4020i46e2 r2c2 / r4c2; Ticaretin Düzenlenmesi, Geliştirilmesi ve Kolaylaştırılması / İç Ticaretin Düzenlenmesi ve Geliştirilmesi; s.240 / u403fi46c0 r2c2 / r4c2; Kamu Gelirleri Yönetimi / Kamu Gelirlerinin Toplanması | s.241 / u4055i46b1 / r4c6 | Mal ve Hizmet Alım Giderleri | 111.436.000,00 | 111.436.000,00 |

Tekil kaynak hücresi: 34; katkılar toplamı: 9.464.585.675,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.

#### Kanıt 3 — s.244 / u40c3i5faa / r8c9

Sınıf: **UNKNOWN**; basılı: **1.709.435.755,00**; hesaplanan: **2.398.885.303,00**; Fark: **-689.449.548,00**.

Kurum hücresi aynı kategorinin basılı program-grubu sütunlarını kapsar. Müdürlük hesabı her ekonomik kaynak hücresini bir kez içerir; kart sayısı ile çarpılmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.244 / u40c3i5faa / r8c6 | Sermaye Giderleri | 1.612.474.000,00 |
| s.244 / u40c3i5faa / r8c7 | Sermaye Giderleri | 96.961.755,00 |
| s.244 / u40c3i5faa / r8c8 | Sermaye Giderleri | 0,00 |

Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Sağlık İşleri Müdürlüğü | s.94 / u2e07i5fc9 r2c2 / r4c2; Engellilerin Toplumsal Hayata Katılımı ve Özel Eğitim / Engelli Bakımı; s.95 / u2e1di5ddf r2c2 / r4c2; Kent Güvenliği ve Esenliği / Çevre Ve Halk Sağlığının Korunması; s.96 / u2e3ci5db8 r2c2 / r4c2; Koruyucu Sağlık / Halk Sağlığının Korunması; s.97 / u2e52i5d96 r2c2 / r4c2; Tedavi Edici Sağlık / Tedavi Hizmetleri | s.98 / u2e71i602c / r6c5 | Sermaye Giderleri | 6.203.579,00 | 6.203.579,00 |
| Veteriner İşleri Müdürlüğü | s.106 / u2f47i5c95 r2c2 / r4c2; Ormanların ve Doğanın Korunması İle Sürdürülebilir Yönetimi / Doğa Koruma ve Milli Parklar | s.107 / u2f5di5c86 / r6c5 | Sermaye Giderleri | 2.000.000,00 | 2.000.000,00 |
| Emlak İstimlak Müdürlüğü | s.110 / u2ff7i5c39 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.111 / u300di5c04 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.112 / u3043i5bf4 / r6c5 | Sermaye Giderleri | 211.250.000,00 | 211.250.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.116 / u30b0i5b0f r2c2 / r4c2; Kent İçi Ulaşım / Karayolu Altyapısı ve Hizmetleri; s.117 / u30c6i5ae5 r2c2 / r4c2; Kent Güvenliği ve Sağlığı / Çevre ve Halk Sağlığının Korunması | s.118 / u30e5i5ad5 / r6c5 | Sermaye Giderleri | 1.859.300.000,00 | 1.859.300.000,00 |
| Park ve Bahçeler Müdürlüğü | s.125 / u31c1i58f6 r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm; s.127 / u3227i58cf r2c2 / r4c2; Şehircilik ve Risk Odaklı Bütünleşik Afet Yönetimi / Mekânsal Planlama ve Kentsel Dönüşüm | s.128 / u3254i5862 / r5c5 | Sermaye Giderleri | 198.572.344,00 | 198.572.344,00 |
| Temizlik İşleri Müdürlüğü | s.148 / u3510i5571 r2c2 / r4c2; Sürdürülebilir Çevre ve İklim Değişikliği / Çevre Kirliliğinin Önlenmesi ve Koruma | s.150 / u3550i5562 / r5c5 | Sermaye Giderleri | 20.000.000,00 | 20.000.000,00 |
| Tarımsal Hizmetler Müdürlüğü | s.154 / u35cbi54ac r2c2 / r4c2; Tarım Programı / Bitkisel Ürünlerde Arz Güvenliği; s.155 / u35e1i5480 r2c2 / r4c2; Tarım Programı / Tarımsal Araştırma ve Geliştirme | s.156 / u3600i546f / r5c5 | Sermaye Giderleri | 4.576.838,00 | 4.576.838,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum; s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri; s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.192 / u3a9fi4f77 / r5c5 | Sermaye Giderleri | 1.250.000,00 | 1.250.000,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.207 / u3c7di4d7b / r5c5 | Sermaye Giderleri | 44.655.142,00 | 44.655.142,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.219 / u3dd5i4bc0 / r5c5 | Sermaye Giderleri | 40.000.000,00 | 40.000.000,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.222 / u3e2ai4b54 / r7c5 | Sermaye Giderleri | 0,00 | 0,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler; s.226 / u3ea0i4aba r2c2 / r4c2; Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı / Sosyal Yardımlaşma; s.227 / u3eb6i4a8a r2c2 / r4c2; Vatandaşlık ve Sivil Toplum Programı / Nüfus ve Vatandaşlık Hizmetleri | s.228 / u3ed5i4a7a / r6c5 | Sermaye Giderleri | 5.077.400,00 | 5.077.400,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.236 / u3fc8i497d / r5c5 | Sermaye Giderleri | 6.000.000,00 | 6.000.000,00 |

Tekil kaynak hücresi: 13; katkılar toplamı: 2.398.885.303,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.

#### Kanıt 4 — s.248 / u444di4775 / r193c2

Sınıf: **BOOK**; basılı: **3.189.780.044,00**; hesaplanan: **4.053.415.705,00**; Fark: **-863.635.661,00**.

Ara toplamdan önceki kapalı program bloğunun birinci düzey (n) satırları birer kez toplanır. İkinci düzey (n.m) satırları ve faaliyetler bunların içinde olduğundan ayrıca eklenmez. Sonraki Kurumsal Genel Yönetim Giderleri ve Genel Toplam bu ara toplamın dışında tutulur.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r3c2 | (1) YÖNETİM VE DESTEK PROGRAMI | 1.132.975.122,00 |
| s.248 / u444di4775 / r30c2 | (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 3.400.000,00 |
| s.248 / u444di4775 / r35c2 | (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 810.844.764,00 |
| s.248 / u444di4775 / r95c2 | (4) KENT İÇİ ULAŞIM | 828.638.909,00 |
| s.248 / u444di4775 / r99c2 | (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 144.100.000,00 |
| s.248 / u444di4775 / r107c2 | (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 14.587.500,00 |
| s.248 / u444di4775 / r114c2 | (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 2.343.147,00 |
| s.248 / u444di4775 / r117c2 | (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 72.675.000,00 |
| s.248 / u444di4775 / r123c2 | (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 838.307.912,00 |
| s.248 / u444di4775 / r135c2 | (10) TARIM PROGRAMI | 9.171.747,00 |
| s.248 / u444di4775 / r146c2 | (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 590.000,00 |
| s.248 / u444di4775 / r153c2 | (12) MİLLİ KÜLTÜR | 80.000.000,00 |
| s.248 / u444di4775 / r173c2 | (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 54.270.630,00 |
| s.248 / u444di4775 / r184c2 | (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 43.010.974,00 |
| s.248 / u444di4775 / r188c2 | (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 18.500.000,00 |

Hesaplanan tutar yukarıda gösterilen doğrudan basılı satırların toplamıdır. Alt programlar ve faaliyetler ayrıca eklenmedi; sonraki kurumsal giderler dışarıda bırakıldı.

#### Kanıt 5 — s.248 / u444di4775 / r193c5

Sınıf: **BOOK**; basılı: **5.026.960.693,50**; hesaplanan: **6.125.958.225,50**; Fark: **-1.098.997.532,00**.

Ara toplamdan önceki kapalı program bloğunun birinci düzey (n) satırları birer kez toplanır. İkinci düzey (n.m) satırları ve faaliyetler bunların içinde olduğundan ayrıca eklenmez. Sonraki Kurumsal Genel Yönetim Giderleri ve Genel Toplam bu ara toplamın dışında tutulur.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r3c5 | (1) YÖNETİM VE DESTEK PROGRAMI | 1.464.002.665,00 |
| s.248 / u444di4775 / r30c5 | (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 3.650.000,00 |
| s.248 / u444di4775 / r35c5 | (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 1.182.029.090,50 |
| s.248 / u444di4775 / r95c5 | (4) KENT İÇİ ULAŞIM | 1.614.907.446,00 |
| s.248 / u444di4775 / r99c5 | (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 213.658.966,00 |
| s.248 / u444di4775 / r107c5 | (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 16.970.110,00 |
| s.248 / u444di4775 / r114c5 | (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 1.534.074,00 |
| s.248 / u444di4775 / r117c5 | (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 99.545.813,00 |
| s.248 / u444di4775 / r123c5 | (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 1.223.370.000,00 |
| s.248 / u444di4775 / r135c5 | (10) TARIM PROGRAMI | 9.476.838,00 |
| s.248 / u444di4775 / r146c5 | (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 1.100.000,00 |
| s.248 / u444di4775 / r153c5 | (12) MİLLİ KÜLTÜR | 141.635.659,00 |
| s.248 / u444di4775 / r173c5 | (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 81.146.442,00 |
| s.248 / u444di4775 / r184c5 | (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 49.431.122,00 |
| s.248 / u444di4775 / r188c5 | (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 23.500.000,00 |

Hesaplanan tutar yukarıda gösterilen doğrudan basılı satırların toplamıdır. Alt programlar ve faaliyetler ayrıca eklenmedi; sonraki kurumsal giderler dışarıda bırakıldı.

#### Kanıt 6 — s.248 / u444di4775 / r193c8

Sınıf: **BOOK**; basılı: **6.064.309.830,00**; hesaplanan: **7.426.150.336,00**; Fark: **-1.361.840.506,00**.

Ara toplamdan önceki kapalı program bloğunun birinci düzey (n) satırları birer kez toplanır. İkinci düzey (n.m) satırları ve faaliyetler bunların içinde olduğundan ayrıca eklenmez. Sonraki Kurumsal Genel Yönetim Giderleri ve Genel Toplam bu ara toplamın dışında tutulur.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r3c8 | (1) YÖNETİM VE DESTEK PROGRAMI | 1.767.927.554,00 |
| s.248 / u444di4775 / r30c8 | (2) ARAŞTIRMA, GELİŞTİRME VE YENİLİK | 3.527.500,00 |
| s.248 / u444di4775 / r35c8 | (3) ŞEHİRCİLİK VE RİSK ODAKLI BÜTÜNLEŞİK AFET YÖNETİMİ | 1.411.393.421,00 |
| s.248 / u444di4775 / r95c8 | (4) KENT İÇİ ULAŞIM | 1.937.493.545,00 |
| s.248 / u444di4775 / r99c8 | (5) KENT GÜVENLİĞİ, SAĞLIĞI VE ESTETİĞİ | 256.580.170,00 |
| s.248 / u444di4775 / r107c8 | (6) SAĞLIK HİZMETLERİ VE ENGELLİ DESTEĞİ | 18.102.713,00 |
| s.248 / u444di4775 / r114c8 | (7) TÜKETİCİNİN KORUNMASI, ÜRÜN VE HİZMET GÜVENLİĞİ | 1.687.482,00 |
| s.248 / u444di4775 / r117c8 | (8) ORMANLARIN VE DOĞANIN KORUNMASI (DOĞA KORUMA) | 124.625.000,00 |
| s.248 / u444di4775 / r123c8 | (9) SÜRDÜRÜLEBİLİR ÇEVRE VE İKLİM DEĞİŞİKLİĞİ | 1.529.237.743,00 |
| s.248 / u444di4775 / r135c8 | (10) TARIM PROGRAMI | 8.417.000,00 |
| s.248 / u444di4775 / r146c8 | (11) ENERJİ ARZ GÜVENLİĞİ, VERİMLİLİĞİ VE ENERJİ PİYASASI | 1.600.000,00 |
| s.248 / u444di4775 / r153c8 | (12) MİLLİ KÜLTÜR | 191.746.000,00 |
| s.248 / u444di4775 / r173c8 | (13) SPORUN GELİŞTİRİLMESİ VE DESTEKLENMESİ | 92.146.534,00 |
| s.248 / u444di4775 / r184c8 | (14) YOKSULLUKLA MÜCADELE VE YARDIMLAŞMA | 56.665.674,00 |
| s.248 / u444di4775 / r188c8 | (15) SOSYAL KORUMA VE SOSYAL HİZMETLER | 25.000.000,00 |

Hesaplanan tutar yukarıda gösterilen doğrudan basılı satırların toplamıdır. Alt programlar ve faaliyetler ayrıca eklenmedi; sonraki kurumsal giderler dışarıda bırakıldı.

#### Kanıt 7 — s.248 / u444di4775 / r3c4

Sınıf: **CHECK**; basılı: **1.132.975.122,00**; hesaplanan: **4.277.347.655,00**; Fark: **-3.144.372.533,00**.

Basılı program toplamı kodlu alt programlarını; alt programlar kendi faaliyet satırlarını kapsar. Müdürlük hesabı ise aynı program adıyla etiketlenmiş üyelik hücrelerini kapsar. Bu iki faaliyet kümesi tekil ve aynı olmadıkça eşitlik doğrulanmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r4c4 | (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 1.089.920.835,00 |
| s.248 / u444di4775 / r14c4 | (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 39.039.548,00 |
| s.248 / u444di4775 / r27c4 | (1.3) Vatandaşlık ve Sivil Toplum | 4.015.739,00 |

Bu alt programların kapsadığı faaliyet satırları (alt toplamlarla birlikte tekrar toplanmaz):

| Kaynak hücresi | Faaliyet | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r5c4 | Yeni bina projelerinin uygulanması | 85.152.000,00 |
| s.248 / u444di4775 / r6c4 | Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 105.192.000,00 |
| s.248 / u444di4775 / r7c4 | Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 30.048.000,00 |
| s.248 / u444di4775 / r8c4 | Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 5.008.000,00 |
| s.248 / u444di4775 / r9c4 | Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 232.904.967,00 |
| s.248 / u444di4775 / r10c4 | Raporlardaki tespitlerin ayrıntılı analizi | 232.904.967,00 |
| s.248 / u444di4775 / r11c4 | Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 132.904.967,00 |
| s.248 / u444di4775 / r12c4 | Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 132.904.967,00 |
| s.248 / u444di4775 / r13c4 | Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 132.904.967,00 |
| s.248 / u444di4775 / r15c4 | Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.489.548,00 |
| s.248 / u444di4775 / r16c4 | Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 400.000,00 |
| s.248 / u444di4775 / r17c4 | Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 700.000,00 |
| s.248 / u444di4775 / r18c4 | Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.450.000,00 |
| s.248 / u444di4775 / r19c4 | Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 15.000.000,00 |
| s.248 / u444di4775 / r20c4 | Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 2.500.000,00 |
| s.248 / u444di4775 / r21c4 | Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 5.000.000,00 |
| s.248 / u444di4775 / r22c4 | Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 2.500.000,00 |
| s.248 / u444di4775 / r23c4 | Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 1.500.000,00 |
| s.248 / u444di4775 / r24c4 | Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 1.500.000,00 |
| s.248 / u444di4775 / r25c4 | Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 2.000.000,00 |
| s.248 / u444di4775 / r26c4 | Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 4.000.000,00 |
| s.248 / u444di4775 / r28c4 | Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 2.000.000,00 |
| s.248 / u444di4775 / r29c4 | Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 2.015.739,00 |

Kapsam karşılaştırması: **Eşleşmiyor / tekil değil**. Yalnız kurumda: 10; yalnız müdürlüklerde: 64. Bu sayılar tutar dağılımı veya yeni program eşlemesi üretmez.

Kurum tablosundaki sonraki Kurumsal Genel Yönetim Giderleri / Diğer Destek, Denetim ve Hizmet Birimleri satırları, program başlığının bütün müdürlük kartlarıyla aynı kapsam olduğunu kanıtlamaz; bu satırlardan programa tutar taşınmadı.


Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r3c5 | 0001.Yeni bina projelerinin uygulanması | 85.652.000,00 | 85.652.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r4c5 | 0002.Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 108.192.000,00 | 108.192.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r5c5 | 0003.Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 27.048.000,00 | 27.048.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r6c5 | 0004.Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması. | 4.508.000,00 | 4.508.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r3c5 | 0001.Kardeş şehir protokollerinin güncellenmesi ve yeni kardeş şehir ilişkilerinin kurulması | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r4c5 | 0002.Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.489.548,00 | 1.489.548,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r5c5 | 0003.Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 400.000,00 | 400.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r6c5 | 0004.Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 700.000,00 | 700.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r7c5 | 0005.Yurt içi ve yurt dışındaki diplomatik misyonlara yönelik resmi ziyaretler | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r8c5 | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi | 1.000.000,00 | 1.000.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r9c5 | 0007.Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.450.000,00 | 1.450.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r10c5 | 0008.Kültürel diplomasi odaklı etkinlik ve organizasyonlar | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r11c5 | 0009.Kardeş şehirler arası iyi uygulama ve deneyim paylaşımı faaliyetleri | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r12c5 | 0010.Uluslararası ziyaret ve temasların raporlanması ve kurumsallaştırılması | 0,00 | 0,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r3c5 | 0001. Belediye projelerinin billboard, raket ve megalight gibi mecralarda etkin duyurularının yapılması. | 15.000.000,00 | 15.000.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r4c5 | 0002. Hizmetlerin tanıtımı için bilgilendirme materyallerinin tasarımı, basımı ve halka ulaştırılması. | 2.500.000,00 | 2.500.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r5c5 | 0003. Defin süreçlerinin koordinasyonu, dini hizmetlerin sunulması ve ailelere yönelik manevi destek ziyaretlerinin gerçekleştirilmesi | 5.000.000,00 | 5.000.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r6c5 | 0004. Vatandaşların belediye faaliyetleri hakkında SMS yoluyla düzenli ve hızlı şekilde bilgilendirilmesi | 2.500.000,00 | 2.500.000,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r3c5 | 0005. ULAKBEL ve çağrı yönetim yazılımının güncellenmesi, daha modüler yapıya kavuşturulması | 2.000.000,00 | 2.000.000,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r4c5 | 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler | 2.015.739,00 | 2.015.739,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r3c5 | 0007. Belediyenin proje, hizmet ve etkinliklerinin sosyal medya, web sitesi ve diğer dijital kanallar aracılığıyla sade, anlaşılır ve erişilebilir biçimde vatandaşlara aktarılması | 1.500.000,00 | 1.500.000,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r4c5 | 0008. Video, görsel, kısa film, röportaj ve bilgilendirici multimedya içeriklerinin hazırlanması ve çoklu platformlarda yayınlanması | 1.500.000,00 | 1.500.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r3c5 | 0009. Medya takip ve analiz çalışmaları yapmak. | 2.000.000,00 | 2.000.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r4c5 | 0010. Ulusal ve uluslararası fuarlarda Büyükçekmece’nin tanıtım filmlerini yapmak | 4.000.000,00 | 4.000.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r3c5 | 0001.Üst Yönetim Program ve Randevu Yönetimi | 6.300.000,00 | 6.300.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r4c5 | 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | 6.800.000,00 | 6.800.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r5c5 | 0003.Protokol ve Resmi Organizasyon Yönetimi | 8.050.000,00 | 8.050.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r6c5 | 0004.Paydaş Talep ve İlişki Yönetimi | 2.300.000,00 | 2.300.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r7c5 | 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | 300.000,00 | 300.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r3c5 | 0006. Eğitici eğitimi programları düzenlemek | 1.000.000,00 | 1.000.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r4c5 | 0007.Farklı konularda sertifika programları düzenlemek | 1.000.000,00 | 1.000.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r5c5 | 0008.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak | 1.000.000,00 | 1.000.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r6c5 | 0009.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek | 1.000.000,00 | 1.000.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r7c5 | 0010.Moral, motivasyon, kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyet düzenlemek | 1.000.000,00 | 1.000.000,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r3c5 | 0001.Bilişim teknolojileri altyapısının modernizasyonu, donanım ve çevre birimlerinin yönetimi, bakım-onarım süreçlerinin yürütülmesi ve bilgi sistemlerinin mevzuat ile ulusal/uluslararası standartlara uygunluğunun sağlanması | 53.495.369,00 | 53.495.369,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r4c5 | 0002.Akıllı Şehirler ve Dijital Dönüşüm Kapsamında; Büyük Veri Analizi, Şehir Veri Platformu, Açık Veri Portalı, Dijital İkiz, Coğrafi Bilgi Sistemleri ile İHA Destekli 2D–3D Dijital Harita Altlıklarının Oluşturulması ve Entegrasyonunun Sağlanması | 53.594.369,00 | 53.594.369,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r5c5 | 0003.Kamu hizmetlerinin dijitalleşmesine yönelik olarak e-belediyecilik, e-devlet entegrasyonu, e-imar, e-ruhsat, e-iskân ve benzeri dijital süreçlerin geliştirilmesi ve vatandaşların hizmetlere web ve mobil platformlar üzerinden erişiminin artırılması | 53.495.369,00 | 53.495.369,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r6c5 | 0004.Vatandaş odaklı mobil uygulamaların geliştirilmesi kapsamında; kültürel ve turistik tanıtım uygulamaları, sosyal tesis ve hizmet kartı projeleri, etkileşimli ilçe uygulamaları, saha denetim ve kurumsal hizmet mobil uygulamalarının hayata geçirilmesi | 53.495.369,00 | 53.495.369,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r7c5 | 0005.Siber güvenliğin sağlanması amacıyla siber saldırılara karşı koruma sistemlerinin kurulması ve geliştirilmesi ile ücretsiz Wi-Fi altyapısı başta olmak üzere dijital hizmetlerin güvenli, sürdürülebilir ve kesintisiz şekilde sunulmasına yönelik çalışmaların yürütülmesi | 53.495.369,00 | 53.495.369,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r3c5 | 0001.Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak | 49.343,00 | 49.343,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r4c5 | 0002.Belediyenin tüm birimlerinde belirli aralıklarla denetimler yapmak | 50.000,00 | 50.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r5c5 | 0003.Belirli bir konu veya şikâyet üzerine özel denetimler yapmak | 50.000,00 | 50.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r3c5 | 0001.Dava, icra ve hukuki süreçlerin etkin ve mevzuata uygun yürütülmesi için kurumsal kapasite artırılacaktır. | 10.975.000,00 | 10.975.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r4c5 | 0002.Birimler arası koordinasyon güçlendirilerek standart uygulamalar oluşturulacaktır | 10.975.000,00 | 10.975.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r5c5 | 0003.Hukuki risklerin erken tespiti için önleyici hukuk ve risk yönetimi geliştirilecektir. | 10.975.000,00 | 10.975.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r6c5 | 0004.Hukuk hizmetlerinde dijitalleşme sağlanarak dosya ve dava takibi güçlendirilecektir | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r7c5 | 0005.Personelin mesleki bilgi ve yetkinliği hizmet içi eğitimlerle artırılacaktır | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r8c5 | 0006.Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r3c5 | 0001.Stratejik planlama ve bütçeleme faaliyetleri | 1.167.350,00 | 1.167.350,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r4c5 | 0002.İç Kontrol Eylem Planı Uyum ve Kalite Yönetim Süreçleri | 1.100.000,00 | 1.100.000,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r5c5 | 0003.Performans göstergelerinin takibi ve raporlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r6c5 | 0004.Katılımcı bütçe çalışmaları | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r7c5 | 0005.Performans programı ve bütçenin hazırlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r8c5 | 0006.Ulusal ve uluslararası projelere katılım | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r9c5 | 0007.2050 Büyükçekmece vizyonu takibi | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r10c5 | 0008.Ulusal ve uluslararası kongre ve toplantılara katılım | 0,00 | 0,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r3c5 | 0001.Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılanacaktır. | 630.000.000,00 | 630.000.000,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r4c5 | 0002.Belediye binaları, bağlı birimler ve belirli kamu kurumlarının elektrik, su, doğalgaz ve iletişim gibi temel ihtiyaçları kesintisiz olarak sağlanacaktır. | 129.750.000,00 | 129.750.000,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r5c5 | 0003. Belediye hizmet binalarının mobilya, temizlik, bakım, onarım ve güvenlik ihtiyaçları karşılanacaktır. | 35.250.000,00 | 35.250.000,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r6c5 | 0004. Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin edilecektir. | 20.000.000,00 | 20.000.000,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r3c5 | 0005. İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması. | 1.660.000.000,00 | 1.660.000.000,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r4c5 | 0006. Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek. | 25.000.000,00 | 25.000.000,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r5c5 | 0007. İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek | 108.868.429,00 | 108.868.429,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r3c5 | 0001.Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 232.904.967,00 | 232.904.967,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r4c5 | 0002.Raporlardaki tespitlerin ayrıntılı analizi | 232.904.967,00 | 232.904.967,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r5c5 | 0003.Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 132.904.967,00 | 132.904.967,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r6c5 | 0004.Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 132.904.967,00 | 132.904.967,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r7c5 | 0005.Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 132.904.967,00 | 132.904.967,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r3c5 | 0001.Encümen ve Belediye Meclisi İşlemlerinin takibi ve alınan kararların yazılması | 6.550.555,00 | 6.550.555,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r4c5 | 0002. Alınan Kararların İlgili Birimlere İletilmesi | 1.765.130,00 | 1.765.130,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r3c5 | 0003. Gelen evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 499.685,00 | 499.685,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r4c5 | 0004.Giden evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 499.685,00 | 499.685,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r3c5 | 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | 64.838.837,00 | 64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r4c5 | 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | 64.838.837,00 | 64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r5c5 | 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | 64.838.837,00 | 64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r6c5 | 0004.Birimlerden gelen araç taleplerinin karşılanması | 0,00 | 0,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r7c5 | 0005.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | 0,00 | 0,00 |

Tekil kaynak hücresi: 77; katkılar toplamı: 4.277.347.655,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.

#### Kanıt 8 — s.248 / u444di4775 / r3c7

Sınıf: **CHECK**; basılı: **1.464.002.665,00**; hesaplanan: **5.953.827.451,00**; Fark: **-4.489.824.786,00**.

Basılı program toplamı kodlu alt programlarını; alt programlar kendi faaliyet satırlarını kapsar. Müdürlük hesabı ise aynı program adıyla etiketlenmiş üyelik hücrelerini kapsar. Bu iki faaliyet kümesi tekil ve aynı olmadıkça eşitlik doğrulanmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r4c7 | (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 1.398.412.510,00 |
| s.248 / u444di4775 / r14c7 | (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 59.320.481,00 |
| s.248 / u444di4775 / r27c7 | (1.3) Vatandaşlık ve Sivil Toplum | 6.269.674,00 |

Bu alt programların kapsadığı faaliyet satırları (alt toplamlarla birlikte tekrar toplanmaz):

| Kaynak hücresi | Faaliyet | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r5c7 | Yeni bina projelerinin uygulanması | 133.500.000,00 |
| s.248 / u444di4775 / r6c7 | Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 168.700.000,00 |
| s.248 / u444di4775 / r7c7 | Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 42.200.000,00 |
| s.248 / u444di4775 / r8c7 | Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 7.645.208,00 |
| s.248 / u444di4775 / r9c7 | Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 215.198.462,00 |
| s.248 / u444di4775 / r10c7 | Raporlardaki tespitlerin ayrıntılı analizi | 215.198.460,00 |
| s.248 / u444di4775 / r11c7 | Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 215.198.460,00 |
| s.248 / u444di4775 / r12c7 | Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 215.198.460,00 |
| s.248 / u444di4775 / r13c7 | Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 215.198.460,00 |
| s.248 / u444di4775 / r15c7 | Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.589.548,00 |
| s.248 / u444di4775 / r16c7 | Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 530.933,00 |
| s.248 / u444di4775 / r17c7 | Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 800.000,00 |
| s.248 / u444di4775 / r18c7 | Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.650.000,00 |
| s.248 / u444di4775 / r19c7 | Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 21.875.000,00 |
| s.248 / u444di4775 / r20c7 | Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 3.125.000,00 |
| s.248 / u444di4775 / r21c7 | Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 9.375.000,00 |
| s.248 / u444di4775 / r22c7 | Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 3.125.000,00 |
| s.248 / u444di4775 / r23c7 | Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 3.125.000,00 |
| s.248 / u444di4775 / r24c7 | Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 3.125.000,00 |
| s.248 / u444di4775 / r25c7 | Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 4.000.000,00 |
| s.248 / u444di4775 / r26c7 | Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 6.250.000,00 |
| s.248 / u444di4775 / r28c7 | Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 3.750.000,00 |
| s.248 / u444di4775 / r29c7 | Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 2.519.674,00 |

Kapsam karşılaştırması: **Eşleşmiyor / tekil değil**. Yalnız kurumda: 10; yalnız müdürlüklerde: 64. Bu sayılar tutar dağılımı veya yeni program eşlemesi üretmez.

Kurum tablosundaki sonraki Kurumsal Genel Yönetim Giderleri / Diğer Destek, Denetim ve Hizmet Birimleri satırları, program başlığının bütün müdürlük kartlarıyla aynı kapsam olduğunu kanıtlamaz; bu satırlardan programa tutar taşınmadı.


Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r3c6 | 0001.Yeni bina projelerinin uygulanması | 133.500.000,00 | 133.500.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r4c6 | 0002.Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 168.700.000,00 | 168.700.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r5c6 | 0003.Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 42.200.000,00 | 42.200.000,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r6c6 | 0004.Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması. | 7.645.208,00 | 7.645.208,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r3c6 | 0001.Kardeş şehir protokollerinin güncellenmesi ve yeni kardeş şehir ilişkilerinin kurulması | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r4c6 | 0002.Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.589.548,00 | 1.589.548,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r5c6 | 0003.Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 530.933,00 | 530.933,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r6c6 | 0004.Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 800.000,00 | 800.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r7c6 | 0005.Yurt içi ve yurt dışındaki diplomatik misyonlara yönelik resmi ziyaretler | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r8c6 | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r9c6 | 0007.Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.650.000,00 | 1.650.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r10c6 | 0008.Kültürel diplomasi odaklı etkinlik ve organizasyonlar | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r11c6 | 0009.Kardeş şehirler arası iyi uygulama ve deneyim paylaşımı faaliyetleri | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r12c6 | 0010.Uluslararası ziyaret ve temasların raporlanması ve kurumsallaştırılması | 0,00 | 0,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r3c6 | 0001. Belediye projelerinin billboard, raket ve megalight gibi mecralarda etkin duyurularının yapılması. | 21.875.000,00 | 21.875.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r4c6 | 0002. Hizmetlerin tanıtımı için bilgilendirme materyallerinin tasarımı, basımı ve halka ulaştırılması. | 3.125.000,00 | 3.125.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r5c6 | 0003. Defin süreçlerinin koordinasyonu, dini hizmetlerin sunulması ve ailelere yönelik manevi destek ziyaretlerinin gerçekleştirilmesi | 9.375.000,00 | 9.375.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r6c6 | 0004. Vatandaşların belediye faaliyetleri hakkında SMS yoluyla düzenli ve hızlı şekilde bilgilendirilmesi | 3.125.000,00 | 3.125.000,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r3c6 | 0005. ULAKBEL ve çağrı yönetim yazılımının güncellenmesi, daha modüler yapıya kavuşturulması | 3.750.000,00 | 3.750.000,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r4c6 | 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler | 2.519.674,00 | 2.519.674,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r3c6 | 0007. Belediyenin proje, hizmet ve etkinliklerinin sosyal medya, web sitesi ve diğer dijital kanallar aracılığıyla sade, anlaşılır ve erişilebilir biçimde vatandaşlara aktarılması | 3.125.000,00 | 3.125.000,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r4c6 | 0008. Video, görsel, kısa film, röportaj ve bilgilendirici multimedya içeriklerinin hazırlanması ve çoklu platformlarda yayınlanması | 3.125.000,00 | 3.125.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r3c6 | 0009. Medya takip ve analiz çalışmaları yapmak. | 4.000.000,00 | 4.000.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r4c6 | 0010. Ulusal ve uluslararası fuarlarda Büyükçekmece’nin tanıtım filmlerini yapmak | 6.250.000,00 | 6.250.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r3c6 | 0001.Üst Yönetim Program ve Randevu Yönetimi | 7.600.000,00 | 7.600.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r4c6 | 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | 7.600.000,00 | 7.600.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r5c6 | 0003.Protokol ve Resmi Organizasyon Yönetimi | 9.162.500,00 | 9.162.500,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r6c6 | 0004.Paydaş Talep ve İlişki Yönetimi | 3.100.000,00 | 3.100.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r7c6 | 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | 300.000,00 | 300.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r3c6 | 0006. Eğitici eğitimi programları düzenlemek | 1.257.722,00 | 1.257.722,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r4c6 | 0007.Farklı konularda sertifika programları düzenlemek | 1.257.722,00 | 1.257.722,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r5c6 | 0008.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak | 1.257.722,00 | 1.257.722,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r6c6 | 0009.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek | 1.257.722,00 | 1.257.722,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r7c6 | 0010.Moral, motivasyon, kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyet düzenlemek | 1.257.722,00 | 1.257.722,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r3c6 | 0001.Bilişim teknolojileri altyapısının modernizasyonu, donanım ve çevre birimlerinin yönetimi, bakım-onarım süreçlerinin yürütülmesi ve bilgi sistemlerinin mevzuat ile ulusal/uluslararası standartlara uygunluğunun sağlanması | 90.831.028,00 | 90.831.028,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r4c6 | 0002.Akıllı Şehirler ve Dijital Dönüşüm Kapsamında; Büyük Veri Analizi, Şehir Veri Platformu, Açık Veri Portalı, Dijital İkiz, Coğrafi Bilgi Sistemleri ile İHA Destekli 2D–3D Dijital Harita Altlıklarının Oluşturulması ve Entegrasyonunun Sağlanması | 90.831.028,00 | 90.831.028,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r5c6 | 0003.Kamu hizmetlerinin dijitalleşmesine yönelik olarak e-belediyecilik, e-devlet entegrasyonu, e-imar, e-ruhsat, e-iskân ve benzeri dijital süreçlerin geliştirilmesi ve vatandaşların hizmetlere web ve mobil platformlar üzerinden erişiminin artırılması | 90.831.028,00 | 90.831.028,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r6c6 | 0004.Vatandaş odaklı mobil uygulamaların geliştirilmesi kapsamında; kültürel ve turistik tanıtım uygulamaları, sosyal tesis ve hizmet kartı projeleri, etkileşimli ilçe uygulamaları, saha denetim ve kurumsal hizmet mobil uygulamalarının hayata geçirilmesi | 90.831.028,00 | 90.831.028,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r7c6 | 0005.Siber güvenliğin sağlanması amacıyla siber saldırılara karşı koruma sistemlerinin kurulması ve geliştirilmesi ile ücretsiz Wi-Fi altyapısı başta olmak üzere dijital hizmetlerin güvenli, sürdürülebilir ve kesintisiz şekilde sunulmasına yönelik çalışmaların yürütülmesi | 90.831.028,00 | 90.831.028,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r3c6 | 0001.Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak | 87.000,00 | 87.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r4c6 | 0002.Belediyenin tüm birimlerinde belirli aralıklarla denetimler yapmak | 50.000,00 | 50.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r5c6 | 0003.Belirli bir konu veya şikâyet üzerine özel denetimler yapmak | 50.000,00 | 50.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r3c6 | 0001.Dava, icra ve hukuki süreçlerin etkin ve mevzuata uygun yürütülmesi için kurumsal kapasite artırılacaktır. | 12.865.080,00 | 12.865.080,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r4c6 | 0002.Birimler arası koordinasyon güçlendirilerek standart uygulamalar oluşturulacaktır | 12.865.080,00 | 12.865.080,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r5c6 | 0003.Hukuki risklerin erken tespiti için önleyici hukuk ve risk yönetimi geliştirilecektir. | 12.865.080,00 | 12.865.080,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r6c6 | 0004.Hukuk hizmetlerinde dijitalleşme sağlanarak dosya ve dava takibi güçlendirilecektir | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r7c6 | 0005.Personelin mesleki bilgi ve yetkinliği hizmet içi eğitimlerle artırılacaktır | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r8c6 | 0006.Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r3c6 | 0001.Stratejik planlama ve bütçeleme faaliyetleri | 1.075.528,00 | 1.075.528,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r4c6 | 0002.İç Kontrol Eylem Planı Uyum ve Kalite Yönetim Süreçleri | 1.250.000,00 | 1.250.000,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r5c6 | 0003.Performans göstergelerinin takibi ve raporlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r6c6 | 0004.Katılımcı bütçe çalışmaları | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r7c6 | 0005.Performans programı ve bütçenin hazırlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r8c6 | 0006.Ulusal ve uluslararası projelere katılım | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r9c6 | 0007.2050 Büyükçekmece vizyonu takibi | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r10c6 | 0008.Ulusal ve uluslararası kongre ve toplantılara katılım | 0,00 | 0,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r3c6 | 0001.Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılanacaktır. | 800.000.000,00 | 800.000.000,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r4c6 | 0002.Belediye binaları, bağlı birimler ve belirli kamu kurumlarının elektrik, su, doğalgaz ve iletişim gibi temel ihtiyaçları kesintisiz olarak sağlanacaktır. | 461.679.197,00 | 461.679.197,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r5c6 | 0003. Belediye hizmet binalarının mobilya, temizlik, bakım, onarım ve güvenlik ihtiyaçları karşılanacaktır. | 455.176.673,00 | 455.176.673,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r6c6 | 0004. Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin edilecektir. | 19.507.571,00 | 19.507.571,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r3c6 | 0005. İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması. | 1.820.496.118,00 | 1.820.496.118,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r4c6 | 0006. Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek. | 19.507.571,00 | 19.507.571,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r5c6 | 0007. İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek | 76.558.674,00 | 76.558.674,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r3c6 | 0001.Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 215.198.462,00 | 215.198.462,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r4c6 | 0002.Raporlardaki tespitlerin ayrıntılı analizi | 215.198.460,00 | 215.198.460,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r5c6 | 0003.Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 215.198.460,00 | 215.198.460,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r6c6 | 0004.Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 215.198.460,00 | 215.198.460,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r7c6 | 0005.Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 215.198.460,00 | 215.198.460,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r3c6 | 0001.Encümen ve Belediye Meclisi İşlemlerinin takibi ve alınan kararların yazılması | 11.743.432,00 | 11.743.432,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r4c6 | 0002. Alınan Kararların İlgili Birimlere İletilmesi | 0,00 | 0,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r3c6 | 0003. Gelen evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 422.540,00 | 422.540,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r4c6 | 0004.Giden evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 634.810,00 | 634.810,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r3c6 | 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | 88.636.394,00 | 88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r4c6 | 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | 88.636.394,00 | 88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r5c6 | 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | 88.636.394,00 | 88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r6c6 | 0004.Birimlerden gelen araç taleplerinin karşılanması | 0,00 | 0,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r7c6 | 0005.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | 0,00 | 0,00 |

Tekil kaynak hücresi: 77; katkılar toplamı: 5.953.827.451,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.

#### Kanıt 9 — s.248 / u444di4775 / r3c10

Sınıf: **CHECK**; basılı: **1.767.927.554,00**; hesaplanan: **7.562.101.098,00**; Fark: **-5.794.173.544,00**.

Basılı program toplamı kodlu alt programlarını; alt programlar kendi faaliyet satırlarını kapsar. Müdürlük hesabı ise aynı program adıyla etiketlenmiş üyelik hücrelerini kapsar. Bu iki faaliyet kümesi tekil ve aynı olmadıkça eşitlik doğrulanmaz.

Basılı toplamın doğrudan kapsadığı satır / bileşenler:

| Kaynak hücresi | Basılı satır | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r4c10 | (1.1) Üst Yönetim, İdari ve Mali Hizmetler | 1.690.925.768,00 |
| s.248 / u444di4775 / r14c10 | (1.2) Teftiş, Denetim, Danışmanlık ve Kurumsal İletişim Hizmetleri | 69.683.393,00 |
| s.248 / u444di4775 / r27c10 | (1.3) Vatandaşlık ve Sivil Toplum | 7.318.393,00 |

Bu alt programların kapsadığı faaliyet satırları (alt toplamlarla birlikte tekrar toplanmaz):

| Kaynak hücresi | Faaliyet | Basılı değer |
| --- | --- | ---: |
| s.248 / u444di4775 / r5c10 | Yeni bina projelerinin uygulanması | 160.515.475,00 |
| s.248 / u444di4775 / r6c10 | Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 202.756.389,00 |
| s.248 / u444di4775 / r7c10 | Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 50.689.097,00 |
| s.248 / u444di4775 / r8c10 | Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması | 9.124.037,00 |
| s.248 / u444di4775 / r9c10 | Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 260.974.404,00 |
| s.248 / u444di4775 / r10c10 | Raporlardaki tespitlerin ayrıntılı analizi | 260.974.402,00 |
| s.248 / u444di4775 / r11c10 | Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 260.974.402,00 |
| s.248 / u444di4775 / r12c10 | Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 260.974.402,00 |
| s.248 / u444di4775 / r13c10 | Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 260.974.402,00 |
| s.248 / u444di4775 / r15c10 | Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.624.067,00 |
| s.248 / u444di4775 / r16c10 | Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 530.933,00 |
| s.248 / u444di4775 / r17c10 | Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 800.000,00 |
| s.248 / u444di4775 / r18c10 | Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.650.000,00 |
| s.248 / u444di4775 / r19c10 | Kurumsal Tanıtım, Duyuru ve Dış Mecra Faaliyetleri (Billboard, Megalight vb.) | 25.630.000,00 |
| s.248 / u444di4775 / r20c10 | Basılı ve Görsel Tanıtım Materyallerinin Üretimi ve Uygulanması | 3.630.000,00 |
| s.248 / u444di4775 / r21c10 | Kurumsal Organizasyon, Tanıtım ve Ağırlama Faaliyetleri | 10.930.000,00 |
| s.248 / u444di4775 / r22c10 | Vatandaş Bilgilendirme ve Toplu İletişim Faaliyetleri (SMS vb.) | 3.630.000,00 |
| s.248 / u444di4775 / r23c10 | Dijital İletişim ve Sosyal Medya Yönetimi Faaliyetleri | 3.630.000,00 |
| s.248 / u444di4775 / r24c10 | Dijital İçerik Üretimi ve Tanıtım Yayın Faaliyetleri | 3.630.000,00 |
| s.248 / u444di4775 / r25c10 | Basın Takip, Medya İzleme ve Raporlama Faaliyetleri | 4.425.000,00 |
| s.248 / u444di4775 / r26c10 | Basın ve Medya İletişimi ile Haber Duyuru Faaliyetleri | 7.260.000,00 |
| s.248 / u444di4775 / r28c10 | Çözüm Masası ve Vatandaş İletişim Hizmetlerinin Yürütülmesi (ULAKBEL) | 4.368.393,00 |
| s.248 / u444di4775 / r29c10 | Personel Eğitim ve Yetkinlik Geliştirme Faaliyetleri (Çözüm Masası) | 2.950.000,00 |

Kapsam karşılaştırması: **Eşleşmiyor / tekil değil**. Yalnız kurumda: 10; yalnız müdürlüklerde: 64. Bu sayılar tutar dağılımı veya yeni program eşlemesi üretmez.

Kurum tablosundaki sonraki Kurumsal Genel Yönetim Giderleri / Diğer Destek, Denetim ve Hizmet Birimleri satırları, program başlığının bütün müdürlük kartlarıyla aynı kapsam olduğunu kanıtlamaz; bu satırlardan programa tutar taşınmadı.


Hesaplamaya giren kaynak hücreleri:

| Müdürlük | Bağlı kartlar (sayfa / tablo; program / alt program) | Kaynak hücresi | Kaynak satır | Ham değer | Katkı |
| --- | --- | --- | --- | --- | ---: |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r3c7 | 0001.Yeni bina projelerinin uygulanması | 160.515.475,00 | 160.515.475,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r4c7 | 0002.Sorumluluğumuzda bulunan binaların bakım onarım tadilat tamirat çalışmalarının yapılması | 202.756.389,00 | 202.756.389,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r5c7 | 0003.Bina, yol ve bakım işleri için araç, malzeme ve ekipman alımının yapılması | 50.689.097,00 | 50.689.097,00 |
| Fen İşleri Müdürlüğü | s.115 / u3091i5b37 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.115 / u3091i5b52 / r6c7 | 0004.Belediyemizin çeşitli organizasyonları için açık/kapalı mekânlar için tasarlanan projeleri faaliyete geçirme çalışmalarının yapılması. | 9.124.037,00 | 9.124.037,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r3c7 | 0001.Kardeş şehir protokollerinin güncellenmesi ve yeni kardeş şehir ilişkilerinin kurulması | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r4c7 | 0002.Kardeş şehirler arasında karşılıklı resmi ziyaretlerin gerçekleştirilmesi | 1.624.067,00 | 1.624.067,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r5c7 | 0003.Konsolosluklar ve büyükelçilik temsilcilerinin Büyükçekmece’de ağırlanması | 530.933,00 | 530.933,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r6c7 | 0004.Uluslararası günler ve özel tarihler kapsamında diplomatik etkinlikler düzenlenmesi | 800.000,00 | 800.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r7c7 | 0005.Yurt içi ve yurt dışındaki diplomatik misyonlara yönelik resmi ziyaretler | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r8c7 | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r9c7 | 0007.Şehir tanıtımına yönelik uluslararası temsil ve protokol faaliyetleri | 1.650.000,00 | 1.650.000,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r10c7 | 0008.Kültürel diplomasi odaklı etkinlik ve organizasyonlar | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r11c7 | 0009.Kardeş şehirler arası iyi uygulama ve deneyim paylaşımı faaliyetleri | 0,00 | 0,00 |
| Dış İlişkiler Müdürlüğü | s.184 / u39bei5074 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.184 / u39bei508a / r12c7 | 0010.Uluslararası ziyaret ve temasların raporlanması ve kurumsallaştırılması | 0,00 | 0,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r3c7 | 0001. Belediye projelerinin billboard, raket ve megalight gibi mecralarda etkin duyurularının yapılması. | 25.630.000,00 | 25.630.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r4c7 | 0002. Hizmetlerin tanıtımı için bilgilendirme materyallerinin tasarımı, basımı ve halka ulaştırılması. | 3.630.000,00 | 3.630.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r5c7 | 0003. Defin süreçlerinin koordinasyonu, dini hizmetlerin sunulması ve ailelere yönelik manevi destek ziyaretlerinin gerçekleştirilmesi | 10.930.000,00 | 10.930.000,00 |
| Halkla İlişkiler Müdürlüğü | s.188 / u3a35i4ffa r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.188 / u3a35i5014 / r6c7 | 0004. Vatandaşların belediye faaliyetleri hakkında SMS yoluyla düzenli ve hızlı şekilde bilgilendirilmesi | 3.630.000,00 | 3.630.000,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r3c7 | 0005. ULAKBEL ve çağrı yönetim yazılımının güncellenmesi, daha modüler yapıya kavuşturulması | 4.368.393,00 | 4.368.393,00 |
| Halkla İlişkiler Müdürlüğü | s.189 / u3a4bi4fd3 r2c2 / r4c2; Yönetim ve Destek Programı / Vatandaşlık ve Sivil Toplum | s.189 / u3a4bi4fed / r4c7 | 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler | 2.950.000,00 | 2.950.000,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r3c7 | 0007. Belediyenin proje, hizmet ve etkinliklerinin sosyal medya, web sitesi ve diğer dijital kanallar aracılığıyla sade, anlaşılır ve erişilebilir biçimde vatandaşlara aktarılması | 3.630.000,00 | 3.630.000,00 |
| Halkla İlişkiler Müdürlüğü | s.190 / u3a6ai4fb0 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.190 / u3a6ai4fc6 / r4c7 | 0008. Video, görsel, kısa film, röportaj ve bilgilendirici multimedya içeriklerinin hazırlanması ve çoklu platformlarda yayınlanması | 3.630.000,00 | 3.630.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r3c7 | 0009. Medya takip ve analiz çalışmaları yapmak. | 4.425.000,00 | 4.425.000,00 |
| Halkla İlişkiler Müdürlüğü | s.191 / u3a80i4f88 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.191 / u3a80i4fa3 / r4c7 | 0010. Ulusal ve uluslararası fuarlarda Büyükçekmece’nin tanıtım filmlerini yapmak | 7.260.000,00 | 7.260.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r3c7 | 0001.Üst Yönetim Program ve Randevu Yönetimi | 7.350.000,00 | 7.350.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r4c7 | 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | 7.350.000,00 | 7.350.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r5c7 | 0003.Protokol ve Resmi Organizasyon Yönetimi | 8.803.125,00 | 8.803.125,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r6c7 | 0004.Paydaş Talep ve İlişki Yönetimi | 3.100.000,00 | 3.100.000,00 |
| Özel Kalem Müdürlüğü | s.198 / u3b85i4e91 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.198 / u3b85i4eac / r7c7 | 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | 300.000,00 | 300.000,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r3c7 | 0006. Eğitici eğitimi programları düzenlemek | 1.178.184,00 | 1.178.184,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r4c7 | 0007.Farklı konularda sertifika programları düzenlemek | 1.178.184,00 | 1.178.184,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r5c7 | 0008.Personel ve eğitim ihtiyacı analizi yapılarak uzaktan eğitim programları düzenlemek ve personelin bu programlara katılımını sağlamak | 1.178.184,00 | 1.178.184,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r6c7 | 0009.Eğitim ihtiyacı analizi yapılarak hizmet içi eğitim semineri düzenlemek | 1.178.184,00 | 1.178.184,00 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | s.202 / u3bfbi4e07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.202 / u3bfbi4e21 / r7c7 | 0010.Moral, motivasyon, kurum aidiyet duygusu, personel kaynaşmasını artırıcı faaliyet düzenlemek | 1.178.184,00 | 1.178.184,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r3c7 | 0001.Bilişim teknolojileri altyapısının modernizasyonu, donanım ve çevre birimlerinin yönetimi, bakım-onarım süreçlerinin yürütülmesi ve bilgi sistemlerinin mevzuat ile ulusal/uluslararası standartlara uygunluğunun sağlanması | 155.460.553,00 | 155.460.553,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r4c7 | 0002.Akıllı Şehirler ve Dijital Dönüşüm Kapsamında; Büyük Veri Analizi, Şehir Veri Platformu, Açık Veri Portalı, Dijital İkiz, Coğrafi Bilgi Sistemleri ile İHA Destekli 2D–3D Dijital Harita Altlıklarının Oluşturulması ve Entegrasyonunun Sağlanması | 155.460.553,00 | 155.460.553,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r5c7 | 0003.Kamu hizmetlerinin dijitalleşmesine yönelik olarak e-belediyecilik, e-devlet entegrasyonu, e-imar, e-ruhsat, e-iskân ve benzeri dijital süreçlerin geliştirilmesi ve vatandaşların hizmetlere web ve mobil platformlar üzerinden erişiminin artırılması | 155.460.553,00 | 155.460.553,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r6c7 | 0004.Vatandaş odaklı mobil uygulamaların geliştirilmesi kapsamında; kültürel ve turistik tanıtım uygulamaları, sosyal tesis ve hizmet kartı projeleri, etkileşimli ilçe uygulamaları, saha denetim ve kurumsal hizmet mobil uygulamalarının hayata geçirilmesi | 155.460.553,00 | 155.460.553,00 |
| Bilgi İşlem Müdürlüğü | s.205 / u3c47i4d8a r2c2 / r4c2; Yönetim Ve Destek Program / Üst Yönetim, İdari ve Mali Hizmetler | s.205 / u3c47i4da5 / r7c7 | 0005.Siber güvenliğin sağlanması amacıyla siber saldırılara karşı koruma sistemlerinin kurulması ve geliştirilmesi ile ücretsiz Wi-Fi altyapısı başta olmak üzere dijital hizmetlerin güvenli, sürdürülebilir ve kesintisiz şekilde sunulmasına yönelik çalışmaların yürütülmesi | 155.460.553,00 | 155.460.553,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r3c7 | 0001.Devlet Memurlarına yönelik ön inceleme, araştırma raporu, disiplin soruşturması işlemleri yapmak | 33.750,00 | 33.750,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r4c7 | 0002.Belediyenin tüm birimlerinde belirli aralıklarla denetimler yapmak | 100.000,00 | 100.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | s.209 / u3cb3i4d2b r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.209 / u3cb3i4d46 / r5c7 | 0003.Belirli bir konu veya şikâyet üzerine özel denetimler yapmak | 200.000,00 | 200.000,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r3c7 | 0001.Dava, icra ve hukuki süreçlerin etkin ve mevzuata uygun yürütülmesi için kurumsal kapasite artırılacaktır. | 14.032.542,00 | 14.032.542,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r4c7 | 0002.Birimler arası koordinasyon güçlendirilerek standart uygulamalar oluşturulacaktır | 14.032.542,00 | 14.032.542,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r5c7 | 0003.Hukuki risklerin erken tespiti için önleyici hukuk ve risk yönetimi geliştirilecektir. | 14.032.542,00 | 14.032.542,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r6c7 | 0004.Hukuk hizmetlerinde dijitalleşme sağlanarak dosya ve dava takibi güçlendirilecektir | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r7c7 | 0005.Personelin mesleki bilgi ve yetkinliği hizmet içi eğitimlerle artırılacaktır | 0,00 | 0,00 |
| Hukuk İşleri Müdürlüğü | s.211 / u3ce8i4cd2 r2c2 / r4c2; Yönetim ve Destek Programı / Teftiş, Denetim ve Danışmanlık Hizmetleri | s.211 / u3ce8i4cec / r8c7 | 0006.Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r3c7 | 0001.Stratejik planlama ve bütçeleme faaliyetleri | 1.000.000,00 | 1.000.000,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r4c7 | 0002.İç Kontrol Eylem Planı Uyum ve Kalite Yönetim Süreçleri | 881.614,00 | 881.614,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r5c7 | 0003.Performans göstergelerinin takibi ve raporlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r6c7 | 0004.Katılımcı bütçe çalışmaları | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r7c7 | 0005.Performans programı ve bütçenin hazırlanması | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r8c7 | 0006.Ulusal ve uluslararası projelere katılım | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r9c7 | 0007.2050 Büyükçekmece vizyonu takibi | 0,00 | 0,00 |
| Strateji Geliştirme Müdürlüğü | s.214 / u3d3di4c66 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.214 / u3d3di4c81 / r10c7 | 0008.Ulusal ve uluslararası kongre ve toplantılara katılım | 0,00 | 0,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r3c7 | 0001.Hizmetlerinin aksamadan sürdürülebilmesi için, araç, iş makinesi ve akaryakıt ihtiyaçları yasal çerçeveye uygun olarak ve maliyet etkinliği gözetilerek karşılanacaktır. | 1.178.608.749,00 | 1.178.608.749,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r4c7 | 0002.Belediye binaları, bağlı birimler ve belirli kamu kurumlarının elektrik, su, doğalgaz ve iletişim gibi temel ihtiyaçları kesintisiz olarak sağlanacaktır. | 577.098.996,00 | 577.098.996,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r5c7 | 0003. Belediye hizmet binalarının mobilya, temizlik, bakım, onarım ve güvenlik ihtiyaçları karşılanacaktır. | 568.970.841,00 | 568.970.841,00 |
| Destek Hizmetleri Müdürlüğü | s.217 / u3da0i4bf6 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.217 / u3da0i4c11 / r6c7 | 0004. Belediye birimlerinin gereksinim duyduğu malzeme, ekipman ve hizmet alımları, mevzuata uygun, şeffaf ve rekabetçi yöntemlerle temin edilecektir. | 24.384.464,00 | 24.384.464,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r3c7 | 0005. İhtiyaç duyulan destek hizmetleri yönetiminin sağlanması. | 2.097.011.373,00 | 2.097.011.373,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r4c7 | 0006. Kurumun tanıtımı için yapılacak olan faaliyetlerde kullanılacak tüm görsel tasarımlar için malzeme temin etmek. | 24.384.464,00 | 24.384.464,00 |
| Destek Hizmetleri Müdürlüğü | s.218 / u3dbfi4bcf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.218 / u3dbfi4be9 / r5c7 | 0007. İhtiyaç duyulan malzeme, ekipman ve hizmet alımlarının yasalara uygun, şeffaf ve rekabetçi bir şekilde gerçekleştirmek | 95.698.368,00 | 95.698.368,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r3c7 | 0001.Mali denetim raporlarının değerlendirilmesi ve aksiyon planı hazırlanması | 253.568.154,00 | 253.568.154,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r4c7 | 0002.Raporlardaki tespitlerin ayrıntılı analizi | 253.568.152,00 | 253.568.152,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r5c7 | 0003.Uygunsuzlukların giderilmesi için somut adımların belirlenmesi | 253.568.152,00 | 253.568.152,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r6c7 | 0004.Büyükçekmece Belediyesi Mali Veri Analitiği Projesi | 253.568.152,00 | 253.568.152,00 |
| Mali Hizmetler Müdürlüğü | s.221 / u3e0bi4b69 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.221 / u3e0bi4b7f / r7c7 | 0005.Belediyenin mali verilerinin analiz edilerek karar verme süreçlerine destek sağlanması | 253.568.152,00 | 253.568.152,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r3c7 | 0001.Encümen ve Belediye Meclisi İşlemlerinin takibi ve alınan kararların yazılması | 12.474.890,00 | 12.474.890,00 |
| Yazı İşleri Müdürlüğü | s.224 / u3e6bi4b07 r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.224 / u3e6bi4b22 / r4c7 | 0002. Alınan Kararların İlgili Birimlere İletilmesi | 0,00 | 0,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r3c7 | 0003. Gelen evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 401.098,00 | 401.098,00 |
| Yazı İşleri Müdürlüğü | s.225 / u3e81i4adf r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | s.225 / u3e81i4afa / r4c7 | 0004.Giden evrakların kayıt altına alınması ve ilgili birime gönderilmesi | 601.647,00 | 601.647,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r3c7 | 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | 120.814.085,00 | 120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r4c7 | 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | 120.814.085,00 | 120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r5c7 | 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | 120.814.085,00 | 120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r6c7 | 0004.Birimlerden gelen araç taleplerinin karşılanması | 0,00 | 0,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | s.235 / u3fa9i498c r2c2 / r4c2; Yönetim ve Destek Programı / Üst Yönetim ve İdari Mali Hizmetler | s.235 / u3fa9i49a7 / r7c7 | 0005.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | 0,00 | 0,00 |

Tekil kaynak hücresi: 77; katkılar toplamı: 7.562.101.098,00. Bu bilinen ara toplamdır; eksik hücre varsa genel hesap Bilinmiyor kalır.


## Yapılan SYSTEM düzeltmeleri

- Para ayrıştırıcısı baştaki ₺ işaretini tanır; ham metin korunur. Veteriner s.107 ekonomik toplamı «₺10.424.938,95» artık 10424938.95 olarak okunur; rastgele ek metin kabul edilmez.
- Kodlu faaliyet açıklamaları sıra yerine faaliyet kodu ve tekil başlık ile eşlenir. Halkla İlişkiler s.192’de 0006 başlığındaki “Faaliyet Adı:” eksikliği sonraki dört açıklamayı kaydırmaz. Kültür s.167’deki yanlış 0008/0009 sağlık başlıkları 0015/0016’ya taşınmaz; kaynakta uygun açıklama olmayan 0015–0017 aşağıda SOURCE olarak kalır.
- CIV-041 ile s.243 ekonomik tablosunun son müdürlüğe yanlış bağlanması önlendi; ret listesi ile üyelik/sayfa kökeni birlikte korunur.

## Bütün hata gruplarının sınıflandırması

| Grup | Sınıf | Doğrulama mesajı |
| --- | --- | ---: |
| Çapraz maliyet/toplam farkı | SOURCE | 53 |
| Ekonomik kaynak/grup doğrulama | SOURCE | 88 |
| Faaliyet açıklaması | SOURCE | 1 |
| Gösterge kaynak değeri | SOURCE | 2 |
| Personel/SGK toplam farkı | SOURCE | 1 |
| Program Grubu Belirlenmeli | SOURCE | 140 |

SYSTEM = üretilen Word, ayrıştırıcı, eşleme/ekim, saklama veya doğrulama kaynaklı hata. SOURCE = kitap hücresi/dağılımının kendisi. Tanınmayan hata veya kitap–Word/saklama farkı otomatik SOURCE sayılmaz; SYSTEM olarak raporlanır. Program Grubu Belirlenmeli kitap düzeltme listesine girmez; kategori × program grubu dağılımı yükleme sonrası ayrı Strateji işidir. Paylaştırma oranı veya varsayılan grup uydurulmadı.

## Her gruptan kitap → Word → saklanan değer kanıtı

### Gösterge kaynak değeri — SOURCE

İşletme ve İştirakler Müdürlüğü

- Kitap hücreleri: s.239 T191 r10c6 = «1 100»
- Üretilen Word hücreleri: s.239 T191 r10c6 = «1 100»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2026, "value_kind": "year_end_estimate", "value": null, "raw_text": "1 100", "state": "needs_review"}]
- Neden: SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı: 2026 Yıl Sonu Tahmini: kaynak değeri doğrulanmalı (1 100).

### Faaliyet açıklaması — SOURCE

Halkla İlişkiler Müdürlüğü

- Kitap hücreleri: s.192 T129 r17c1 = «0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler»; s.192 T129 r48c1 = «0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimleri»; s.192 T129 r37c1 = «Faaliyetlere İlişkin Açıklamalar»; s.192 T129 r57c1 = «Büyükçekmece’nin tarihi, kültürel, turistik ve sosyal değerlerinin ulusal ve uluslararası platformlarda tanıtılması amacıyla tanıtım filmleri hazırlanması ve yayınlanmasına yönelik çalışmalar yürütülmektedir. Bu kapsamda, ilçemizin doğal güzelliklerini, kültürel mirasını, turizm potansiyelini ve belediyemizin faaliyetlerini ön plana çıkaran görsel içerikler üretilerek fuar, organizasyon ve tanıtım etkinliklerinde gösterimi sağlanmaktadır. Gerçekleştirilen çalışmalarla ilçemizin ulusal ve uluslararası alanda bilinirliğinin artırılması ve kurumsal tanıtım faaliyetlerinin güçlendirilmesi amaçlanmaktadır.»
- Üretilen Word hücreleri: s.192 T129 r17c1 = «0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler»; s.192 T129 r48c1 = «0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimleri»; s.192 T129 r37c1 = «Faaliyetlere İlişkin Açıklamalar»; s.192 T129 r57c1 = «Büyükçekmece’nin tarihi, kültürel, turistik ve sosyal değerlerinin ulusal ve uluslararası platformlarda tanıtılması amacıyla tanıtım filmleri hazırlanması ve yayınlanmasına yönelik çalışmalar yürütülmektedir. Bu kapsamda, ilçemizin doğal güzelliklerini, kültürel mirasını, turizm potansiyelini ve belediyemizin faaliyetlerini ön plana çıkaran görsel içerikler üretilerek fuar, organizasyon ve tanıtım etkinliklerinde gösterimi sağlanmaktadır. Gerçekleştirilen çalışmalarla ilçemizin ulusal ve uluslararası alanda bilinirliğinin artırılması ve kurumsal tanıtım faaliyetlerinin güçlendirilmesi amaçlanmaktadır.»
- Saklanan değerler (ondalık depolama gösterimi): [{"activity": "0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler", "explanation": ""}]
- Neden: 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler: faaliyet açıklaması eksik. Bu kod için tekil ve uygun açıklama başlığı/metni kaynakta yok; başka faaliyetin metni taşınmadı.

### Ekonomik kaynak/grup doğrulama — SOURCE

Dış İlişkiler Müdürlüğü

- Kitap hücreleri: s.186 T120 r2c5 = «1.756.250,00»; s.186 T120 r3c5 = «87.500,00»; s.186 T120 r4c5 = «5.470.481,00»; s.186 T120 r5c5 = «100.000,00»; s.186 T120 r6c5 = «7.414.231,00»; s.186 T120 r7c5 = «0,00»; s.186 T120 r8c5 = «6.414.231,00»
- Üretilen Word hücreleri: s.186 T120 r2c5 = «1.756.250,00»; s.186 T120 r3c5 = «87.500,00»; s.186 T120 r4c5 = «5.470.481,00»; s.186 T120 r5c5 = «100.000,00»; s.186 T120 r6c5 = «7.414.231,00»; s.186 T120 r7c5 = «0,00»; s.186 T120 r8c5 = «6.414.231,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2028, "value_kind": "forecast", "category": "current_transfers", "funding_type": "outside", "amount": "0.00", "raw_text": "0,00", "state": "needs_review", "program_group": "management"}]
- Neden: Tablo 120, 2028 Tahmin: Faaliyet Maliyeti Toplamı 6.414.231,00 TL, Bütçe İçi Toplam 7.414.231,00 TL + Bütçe Dışı Toplam 0,00 TL = 7.414.231,00 TL; fark -1.000.000,00 TL. Kaynak tabloyu kontrol edin.

### Program Grubu Belirlenmeli — SOURCE

Fen İşleri Müdürlüğü

- Kitap hücreleri: s.118 T38 r2c2 = «46.388.000,00»; s.118 T38 r3c2 = «2.300.000,00»; s.118 T38 r4c2 = «442.490.000,00»; s.118 T38 r5c2 = «4.600.000,00»; s.118 T38 r6c2 = «453.562.000,00»; s.118 T38 r7c2 = «949.340.000,00»; s.118 T38 r8c2 = «0,00»; s.118 T38 r9c2 = «949.340.000,00»; s.115 T31 r2c2 = «Yönetim ve Destek Programı»; s.116 T33 r2c2 = «Kent İçi Ulaşım»; s.117 T35 r2c2 = «Kent Güvenliği ve Sağlığı»
- Üretilen Word hücreleri: s.118 T38 r2c2 = «46.388.000,00»; s.118 T38 r3c2 = «2.300.000,00»; s.118 T38 r4c2 = «442.490.000,00»; s.118 T38 r5c2 = «4.600.000,00»; s.118 T38 r6c2 = «453.562.000,00»; s.118 T38 r7c2 = «949.340.000,00»; s.118 T38 r8c2 = «0,00»; s.118 T38 r9c2 = «949.340.000,00»; s.115 T31 r2c2 = «Yönetim ve Destek Programı»; s.116 T33 r2c2 = «Kent İçi Ulaşım»; s.117 T35 r2c2 = «Kent Güvenliği ve Sağlığı»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2026, "value_kind": "budget", "category": "current_transfers", "funding_type": "outside", "amount": "0.00", "raw_text": "0,00", "state": "needs_review", "program_group": "unallocated"}]
- Neden: Tablo 38, 2026 Bütçe: Program grubu dağılımı kaynakta ayrılmamış. Programlar: Yönetim ve Destek Programı; Kent İçi Ulaşım; Kent Güvenliği ve Sağlığı. Tutarları program gruplarına göre doğrulayın. Kaynak tabloyu kontrol edin.

### Çapraz maliyet/toplam farkı — SOURCE

Bilgi İşlem Müdürlüğü

- Kitap hücreleri: s.207 T147 r20c6 = «26.670.000,00»; s.207 T148 r2c5 = «25.432.500,00»; s.207 T148 r3c5 = «1.237.500,00»; s.207 T148 r4c5 = «409.500.000,00»; s.207 T148 r5c5 = «44.655.142,00»; s.207 T148 r6c5 = «480.825.142,00»; s.207 T148 r7c5 = «0,00»; s.207 T148 r8c5 = «480.825.142,00»; s.207 T147 r2c6 = «90.831.028,00»; s.207 T147 r3c6 = «90.831.028,00»; s.207 T147 r4c6 = «0,00»; s.207 T147 r5c6 = «90.831.028,00»; s.207 T147 r6c6 = «90.831.028,00»; s.207 T147 r7c6 = «0,00»; s.207 T147 r8c6 = «90.831.028,00»; s.207 T147 r9c6 = «90.831.028,00»; s.207 T147 r10c6 = «0,00»; s.207 T147 r11c6 = «90.831.028,00»; s.207 T147 r12c6 = «90.831.028,00»; s.207 T147 r13c6 = «0,00»; s.207 T147 r14c6 = «90.831.028,00»; s.207 T147 r15c6 = «90.831.028,00»; s.207 T147 r16c6 = «0,00»
- Üretilen Word hücreleri: s.207 T147 r20c6 = «26.670.000,00»; s.207 T148 r2c5 = «25.432.500,00»; s.207 T148 r3c5 = «1.237.500,00»; s.207 T148 r4c5 = «409.500.000,00»; s.207 T148 r5c5 = «44.655.142,00»; s.207 T148 r6c5 = «480.825.142,00»; s.207 T148 r7c5 = «0,00»; s.207 T148 r8c5 = «480.825.142,00»; s.207 T147 r2c6 = «90.831.028,00»; s.207 T147 r3c6 = «90.831.028,00»; s.207 T147 r4c6 = «0,00»; s.207 T147 r5c6 = «90.831.028,00»; s.207 T147 r6c6 = «90.831.028,00»; s.207 T147 r7c6 = «0,00»; s.207 T147 r8c6 = «90.831.028,00»; s.207 T147 r9c6 = «90.831.028,00»; s.207 T147 r10c6 = «0,00»; s.207 T147 r11c6 = «90.831.028,00»; s.207 T147 r12c6 = «90.831.028,00»; s.207 T147 r13c6 = «0,00»; s.207 T147 r14c6 = «90.831.028,00»; s.207 T147 r15c6 = «90.831.028,00»; s.207 T147 r16c6 = «0,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2028, "activity_total": "454155140.00", "personnel": "26670000.00", "economic_total": "480825142.00", "economic_personnel": "26670000.00", "activity_inside": "454155140.00", "economic_inside": "454155142.00", "activity_outside": "0.00", "economic_outside": "0.00"}]
- Neden: 2028: bütçe içi faaliyet ve ekonomik toplamları uyuşmuyor. Faaliyet toplamı 454.155.140,00; ortak personel/SGK 26.670.000,00; ekonomik kategori toplamı 480.825.142,00; ekonomik personel/SGK 26.670.000,00 TL.

### Personel/SGK toplam farkı — SOURCE

İşletme ve İştirakler Müdürlüğü

- Kitap hücreleri: s.241 T195 r20c7 = «15.809.760,00»; s.241 T196 r2c6 = «14.160.960,00»; s.241 T196 r3c6 = «1.648.000,00»; s.241 T196 r4c6 = «111.436.000,00»; s.241 T196 r5c6 = «0,00»; s.241 T196 r6c6 = «127.245.760,00»; s.241 T196 r7c6 = «0,00»; s.241 T196 r8c6 = «127.245.760,00»
- Üretilen Word hücreleri: s.241 T195 r20c7 = «15.809.760,00»; s.241 T196 r2c6 = «14.160.960,00»; s.241 T196 r3c6 = «1.648.000,00»; s.241 T196 r4c6 = «111.436.000,00»; s.241 T196 r5c6 = «0,00»; s.241 T196 r6c6 = «127.245.760,00»; s.241 T196 r7c6 = «0,00»; s.241 T196 r8c6 = «127.245.760,00»
- Saklanan değerler (ondalık depolama gösterimi): [{"year": 2029, "activity_total": "111436000.00", "personnel": "15809760.00", "economic_total": "127244960.00", "economic_personnel": "15808960.00", "activity_inside": "111436000.00", "economic_inside": "111436000.00", "activity_outside": "0.00", "economic_outside": "0.00"}]
- Neden: 2029: ekonomik personel/SGK satırları ortak tablodan farklı. Faaliyet toplamı 111.436.000,00; ortak personel/SGK 15.809.760,00; ekonomik kategori toplamı 127.244.960,00; ekonomik personel/SGK 15.808.960,00 TL.

### SYSTEM düzeltmesinin saklama kanıtı

## Kitapta düzeltilmez — yükleme sonrası Strateji girer (program grubu dağılımı)

Bu bölüm kitap kontrol maddesi sayısına dahil değildir. Her kaynak kategori hücresi için Hizmet + Yönetim ve Destek tutarları kaynak tutarını korumalıdır. Bütçe dışı 0,00 değerleri kitabın Bütçe Dışı Toplam satırından gelir; kategori hücresindeki bütçe içi tutarla karıştırılmamalı. Mevcut uygulamada Strateji için iki gruba atomik bölme akışı bulunmuyor; bu bölüm yapılacak yükleme sonrası işi tanımlar (PR açıklamasında route/validator incelemesi vardır).

### Fen İşleri Müdürlüğü

50 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/2 | Kent İçi Ulaşım / Karayolu Altyapısı ve Hizmetleri | Hizmet |
| 2027/3 | Kent Güvenliği ve Sağlığı / Çevre ve Halk Sağlığının Korunması | Hizmet |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Sermaye Giderleri | Bütçe İçi | 453.562.000,00 | s.118 / T38 / sütun 2 / satır 6 |
| 2026 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 6,8 |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 4.600.000,00 | s.118 / T38 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 5,8 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 442.490.000,00 | s.118 / T38 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 4,8 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 46.388.000,00 | s.118 / T38 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 2,8 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.300.000,00 | s.118 / T38 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 2 / satır 3,8 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe İçi | 537.600,00 | s.118 / T38 / sütun 3 / satır 6 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 6,8 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 0,00 | s.118 / T38 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 5,8 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 33.097.435,87 | s.118 / T38 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 4,8 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 17.824.074,35 | s.118 / T38 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 2,8 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.261.101,27 | s.118 / T38 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 3 / satır 3,8 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe İçi | 1.071.850.000,00 | s.118 / T38 / sütun 4 / satır 6 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 6,8 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.200.000,00 | s.118 / T38 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 5,8 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 116.088.909,00 | s.118 / T38 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 4,8 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 44.000.000,00 | s.118 / T38 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 2,8 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.300.000,00 | s.118 / T38 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 4 / satır 3,8 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe İçi | 1.859.300.000,00 | s.118 / T38 / sütun 5 / satır 6 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 6,8 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 1.675.208,00 | s.118 / T38 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 5,8 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 302.948.429,00 | s.118 / T38 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 4,8 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 55.000.000,00 | s.118 / T38 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 2,8 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 4.125.000,00 | s.118 / T38 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 5 / satır 3,8 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe İçi | 2.223.750.000,00 | s.118 / T38 / sütun 6 / satır 6 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 6,8 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 2.070.000,00 | s.118 / T38 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 5,8 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 367.084.546,00 | s.118 / T38 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 4,8 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 68.750.000,00 | s.118 / T38 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 2,8 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 5.156.250,00 | s.118 / T38 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.118 / T38 / sütun 6 / satır 3,8 |

### Yazı İşleri Müdürlüğü

50 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/2 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |
| 2027/3 | Yoksullukla Mücadele Ve Sosyal Yardımlaşma Programı / Sosyal Yardımlaşma | Hizmet |
| 2027/4 | Vatandaşlık ve Sivil Toplum Programı / Nüfus ve Vatandaşlık Hizmetleri | Hizmet |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Sermaye Giderleri | Bütçe İçi | 3.057.600,00 | s.228 / T180 / sütun 2 / satır 6 |
| 2026 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 2 / satır 6,8 |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 1.528.800,00 | s.228 / T180 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 2 / satır 5,8 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.434.060,00 | s.228 / T180 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 2 / satır 4,8 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 16.976.137,00 | s.228 / T180 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 2 / satır 2,8 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.940.000,00 | s.228 / T180 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 2 / satır 3,8 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe İçi | 3.532.103,48 | s.228 / T180 / sütun 3 / satır 6 |
| 2026 Haziran Sonu Harcama | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 3 / satır 6,8 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 81.805,31 | s.228 / T180 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 3 / satır 5,8 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 5.312.554,37 | s.228 / T180 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 3 / satır 4,8 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 8.836.228,24 | s.228 / T180 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 3 / satır 2,8 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.039.203,47 | s.228 / T180 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 3 / satır 3,8 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe İçi | 4.415.130,00 | s.228 / T180 / sütun 4 / satır 6 |
| 2027 Bütçe | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 4 / satır 6,8 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.911.000,00 | s.228 / T180 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 4 / satır 5,8 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.000.000,00 | s.228 / T180 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 4 / satır 4,8 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 21.700.000,00 | s.228 / T180 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 4 / satır 2,8 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.000.000,00 | s.228 / T180 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 4 / satır 3,8 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe İçi | 5.077.400,00 | s.228 / T180 / sütun 5 / satır 6 |
| 2028 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 5 / satır 6,8 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 2.197.650,00 | s.228 / T180 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 5 / satır 5,8 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 14.073.382,00 | s.228 / T180 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 5 / satır 4,8 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 27.125.000,00 | s.228 / T180 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 5 / satır 2,8 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.757.000,00 | s.228 / T180 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 5 / satır 3,8 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe İçi | 5.585.140,00 | s.228 / T180 / sütun 6 / satır 6 |
| 2029 Tahmin | Sermaye Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 6 / satır 6,8 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 2.417.415,00 | s.228 / T180 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 6 / satır 5,8 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 13.592.495,00 | s.228 / T180 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 6 / satır 4,8 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 33.906.250,00 | s.228 / T180 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 6 / satır 2,8 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 4.687.500,00 | s.228 / T180 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.228 / T180 / sütun 6 / satır 3,8 |

### İnsan Kaynakları ve Eğitim Müdürlüğü

40 doğrulama mesajında dağılım gereksinimi var; başka kitap nedeni de taşıyan mesajlar kitap sayımında bir kez sayılmıştır.

| Kart | Program / alt program | Grup |
| --- | --- | --- |
| 2027/1 | Araştırma, Geliştirme ve Yenilik / Bilim, Teknoloji ve Yenilik Kültürü İle İnsan Kaynağının Geliştirilmesi | Hizmet |
| 2027/2 | Yönetim ve Destek Programı / Üst Yönetim, İdari ve Mali Hizmetler | Yönetim ve Destek |

| Yıl / sütun | Kategori | Finansman | Dağıtılacak tutar | Kaynak hücresi |
| --- | --- | --- | ---: | --- |
| 2026 Bütçe | Cari Transferler | Bütçe İçi | 1.500.000,00 | s.203 / T144 / sütun 2 / satır 5 |
| 2026 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 5,7 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 7.600.000,00 | s.203 / T144 / sütun 2 / satır 4 |
| 2026 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 4,7 |
| 2026 Bütçe | Personel Giderleri | Bütçe İçi | 15.364.541,00 | s.203 / T144 / sütun 2 / satır 2 |
| 2026 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 2,7 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 1.800.000,00 | s.203 / T144 / sütun 2 / satır 3 |
| 2026 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 2 / satır 3,7 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe İçi | 2.228.000,00 | s.203 / T144 / sütun 3 / satır 5 |
| 2026 Haziran Sonu Harcama | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 5,7 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 2.435.619,92 | s.203 / T144 / sütun 3 / satır 4 |
| 2026 Haziran Sonu Harcama | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 4,7 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe İçi | 13.287.541,43 | s.203 / T144 / sütun 3 / satır 2 |
| 2026 Haziran Sonu Harcama | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 2,7 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 859.945,87 | s.203 / T144 / sütun 3 / satır 3 |
| 2026 Haziran Sonu Harcama | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 3 / satır 3,7 |
| 2027 Bütçe | Cari Transferler | Bütçe İçi | 1.600.000,00 | s.203 / T144 / sütun 4 / satır 5 |
| 2027 Bütçe | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 5,7 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 8.400.000,00 | s.203 / T144 / sütun 4 / satır 4 |
| 2027 Bütçe | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 4,7 |
| 2027 Bütçe | Personel Giderleri | Bütçe İçi | 19.306.000,00 | s.203 / T144 / sütun 4 / satır 2 |
| 2027 Bütçe | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 2,7 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.100.000,00 | s.203 / T144 / sütun 4 / satır 3 |
| 2027 Bütçe | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 4 / satır 3,7 |
| 2028 Tahmin | Cari Transferler | Bütçe İçi | 1.700.000,00 | s.203 / T144 / sütun 5 / satır 5 |
| 2028 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 5,7 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 10.877.216,00 | s.203 / T144 / sütun 5 / satır 4 |
| 2028 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 4,7 |
| 2028 Tahmin | Personel Giderleri | Bütçe İçi | 24.132.500,00 | s.203 / T144 / sütun 5 / satır 2 |
| 2028 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 2,7 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 2.625.000,00 | s.203 / T144 / sütun 5 / satır 3 |
| 2028 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 5 / satır 3,7 |
| 2029 Tahmin | Cari Transferler | Bütçe İçi | 1.800.000,00 | s.203 / T144 / sütun 6 / satır 5 |
| 2029 Tahmin | Cari Transferler | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 5,7 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe İçi | 9.981.840,00 | s.203 / T144 / sütun 6 / satır 4 |
| 2029 Tahmin | Mal ve Hizmet Alım Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 4,7 |
| 2029 Tahmin | Personel Giderleri | Bütçe İçi | 30.165.625,00 | s.203 / T144 / sütun 6 / satır 2 |
| 2029 Tahmin | Personel Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 2,7 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe İçi | 3.281.250,00 | s.203 / T144 / sütun 6 / satır 3 |
| 2029 Tahmin | Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | Bütçe Dışı | 0,00 | s.203 / T144 / sütun 6 / satır 3,7 |

## Pazartesi — müdürlük bazında yalnız kitap düzeltme listesi

### Afet İşleri ve Risk Yönetimi Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Araştırma ve Geliştirme Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Bilgi İşlem Müdürlüğü

Gönderime hazır: **Hayır**; 4 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.207 / T147 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 454.155.140,00 + ortak personel/SGK 26.670.000,00 = 480.825.140,00 olmalı; ekonomik tablo toplamı 480.825.142,00 (fark 2,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 454.155.140,00, ekonomik personel/SGK hariç toplam 454.155.142,00 (fark 2,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.207 / T147 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 777.302.765,00 + ortak personel/SGK 33.337.500,00 = 810.640.265,00 olmalı; ekonomik tablo toplamı 810.640.269,00 (fark 4,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 777.302.765,00, ekonomik personel/SGK hariç toplam 777.302.769,00 (fark 4,00). İki tabloda bu finansman tutarları eşit olmalı.


### Destek Hizmetleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Dış İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 12 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.186 / T119 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 4.570.481,00 + ortak personel/SGK 1.843.750,00 = 6.414.231,00 olmalı; ekonomik tablo toplamı 7.414.231,00 (fark 1.000.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 4.570.481,00, ekonomik personel/SGK hariç toplam 5.570.481,00 (fark 1.000.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.186 / T119 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 4.605.000,00 + ortak personel/SGK 2.304.688,00 = 6.909.688,00 olmalı; ekonomik tablo toplamı 8.009.688,00 (fark 1.100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 4.605.000,00, ekonomik personel/SGK hariç toplam 5.705.000,00 (fark 1.100.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2028 Tahmin

  **Hücreler:** s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Toplam = Bütçe İçi + Bütçe Dışı olmalı: 7.414.231,00 + 0,00 = 7.414.231,00, kitapta 6.414.231,00 yazıyor (fark -1.000.000,00). Yanlış hücreyi düzeltin.


### Emlak İstimlak Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Etüd Proje Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Fen İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 4 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.118 / T37 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 2.163.783.041,00 + ortak personel/SGK 59.125.000,00 = 2.222.908.041,00 olmalı; ekonomik tablo toplamı 2.223.048.637,00 (fark 140.596,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.163.783.041,00, ekonomik personel/SGK hariç toplam 2.163.923.637,00 (fark 140.596,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.118 / T37 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 2.592.658.713,00 + ortak personel/SGK 73.906.250,00 = 2.666.564.963,00 olmalı; ekonomik tablo toplamı 2.666.810.796,00 (fark 245.833,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.592.658.713,00, ekonomik personel/SGK hariç toplam 2.592.904.546,00 (fark 245.833,00). İki tabloda bu finansman tutarları eşit olmalı.


### Gelirler Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Gençlik ve Spor İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 12 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.173 / T105 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 77.148.000,00 + ortak personel/SGK 8.661.250,00 = 85.809.250,00 olmalı; ekonomik tablo toplamı 89.807.672,00 (fark 3.998.422,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 77.148.000,00, ekonomik personel/SGK hariç toplam 81.146.422,00 (fark 3.998.422,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.173 / T105 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 88.367.100,00 + ortak personel/SGK 10.826.563,00 = 99.193.663,00 olmalı; ekonomik tablo toplamı 102.973.097,00 (fark 3.779.434,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 88.367.100,00, ekonomik personel/SGK hariç toplam 92.146.534,00 (fark 3.779.434,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2029 Tahmin

  **Hücreler:** s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 102.973.097,00, Bütçe İçi Toplam 99.193.663,00 (fark -3.779.434,00). Yanlış satırı veya toplamı düzeltin.


### Halkla İlişkiler Müdürlüğü

Gönderime hazır: **Hayır**; 3 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.192 / T129 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.192 / T130 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 60.269.674,00 + ortak personel/SGK 34.815.579,00 = 95.085.253,00 olmalı; ekonomik tablo toplamı 94.835.253,00 (fark -250.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 60.269.674,00, ekonomik personel/SGK hariç toplam 60.019.674,00 (fark -250.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler

  **Hücreler:** s.192 / T129 / sütun 1 / satır 17,37,48,57

  Yapılacak: Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin.


### Hukuk İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Kentsel Dönüşüm Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Kültür, Sanat ve Sosyal İşler Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.167 / T99 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 4 / satır 2,3,4,5,6,7

  Yapılacak: Faaliyet maliyetleri toplamı 98.050.750,00 + ortak personel/SGK 15.133.171,00 = 113.183.921,00 olmalı; ekonomik tablo toplamı 95.133.171,00 (fark -18.050.750,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 98.050.750,00, ekonomik personel/SGK hariç toplam 80.000.000,00 (fark -18.050.750,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.167 / T99 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 5 / satır 2,3,4,5,6,7

  Yapılacak: Faaliyet maliyetleri toplamı 141.808.665,00 + ortak personel/SGK 18.916.464,00 = 160.725.129,00 olmalı; ekonomik tablo toplamı 160.552.123,00 (fark -173.006,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 141.808.665,00, ekonomik personel/SGK hariç toplam 141.635.659,00 (fark -173.006,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.167 / T99 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 6 / satır 2,3,4,5,6,7

  Yapılacak: Faaliyet maliyetleri toplamı 194.212.180,00 + ortak personel/SGK 23.645.580,00 = 217.857.760,00 olmalı; ekonomik tablo toplamı 215.391.580,00 (fark -2.466.180,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 194.212.180,00, ekonomik personel/SGK hariç toplam 191.746.000,00 (fark -2.466.180,00). İki tabloda bu finansman tutarları eşit olmalı.


### Makine İkmal Bakım ve Onarım Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.236 / T187 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 265.909.182,00 + ortak personel/SGK 17.842.500,00 = 283.751.682,00 olmalı; ekonomik tablo toplamı 283.751.680,00 (fark -2,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 265.909.182,00, ekonomik personel/SGK hariç toplam 265.909.180,00 (fark -2,00). İki tabloda bu finansman tutarları eşit olmalı.


### Mali Hizmetler Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Park ve Bahçeler Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.128 / T49 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 543.583.357,00 + ortak personel/SGK 23.223.750,00 = 566.807.107,00 olmalı; ekonomik tablo toplamı 551.300.000,00 (fark -15.507.107,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 543.583.357,00, ekonomik personel/SGK hariç toplam 528.076.250,00 (fark -15.507.107,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.128 / T49 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 846.720.000,00 + ortak personel/SGK 29.029.688,00 = 875.749.688,00 olmalı; ekonomik tablo toplamı 850.652.032,00 (fark -25.097.656,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 846.720.000,00, ekonomik personel/SGK hariç toplam 821.622.344,00 (fark -25.097.656,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.128 / T49 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 1.016.063.999,00 + ortak personel/SGK 36.287.110,00 = 1.052.351.109,00 olmalı; ekonomik tablo toplamı 1.020.978.440,00 (fark -31.372.669,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 1.016.063.999,00, ekonomik personel/SGK hariç toplam 984.691.330,00 (fark -31.372.669,00). İki tabloda bu finansman tutarları eşit olmalı.


### Plan Proje Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Rehberlik ve Teftiş Kurulu Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.210 / T151 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,14; s.210 / T152 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 333.750,00 + ortak personel/SGK 2.578.125,00 = 2.911.875,00 olmalı; ekonomik tablo toplamı 2.811.875,00 (fark -100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 333.750,00, ekonomik personel/SGK hariç toplam 233.750,00 (fark -100.000,00). İki tabloda bu finansman tutarları eşit olmalı.


### Ruhsat ve Denetim Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.101 / T14 / sütun 2 / satır 2,3,4,5,6,7

  Yapılacak: Kategori satırlarının toplamı 11.386.500,16, Bütçe İçi Toplam 11.623.833,00 (fark 237.332,84). Yanlış satırı veya toplamı düzeltin.


### Sağlık İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 52 kitap mesajı / 6 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.98 / T9 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 24.931.292,00 + ortak personel/SGK 21.946.875,00 = 46.878.167,00 olmalı; ekonomik tablo toplamı 47.049.588,00 (fark 171.421,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 24.931.292,00, ekonomik personel/SGK hariç toplam 25.102.713,00 (fark 171.421,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Ekonomik tablo · 2026 Bütçe

  **Hücreler:** s.98 / T10 / sütun 2 / satır 2,3,4,5,6,7,8,9

  Yapılacak: s.98, tablo 10, satır 2, sütun 2; s.98, tablo 10, satır 3, sütun 2; s.98, tablo 10, satır 4, sütun 2; s.98, tablo 10, satır 5, sütun 2; s.98, tablo 10, satır 6, sütun 2; s.98, tablo 10, satır 7, sütun 2; s.98, tablo 10, satır 8, sütun 2; s.98, tablo 10, satır 9, sütun 2: Bütçe İçi Toplam = «BOŞ». Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.

- [ ] Ekonomik tablo · 2026 Haziran Sonu Harcama

  **Hücreler:** s.98 / T10 / sütun 3 / satır 2,3,4,5,6,7,8,9

  Yapılacak: s.98, tablo 10, satır 2, sütun 3; s.98, tablo 10, satır 3, sütun 3; s.98, tablo 10, satır 4, sütun 3; s.98, tablo 10, satır 5, sütun 3; s.98, tablo 10, satır 6, sütun 3; s.98, tablo 10, satır 7, sütun 3; s.98, tablo 10, satır 8, sütun 3; s.98, tablo 10, satır 9, sütun 3: Bütçe İçi Toplam = «BOŞ». Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.

- [ ] Ekonomik tablo · 2027 Bütçe

  **Hücreler:** s.98 / T10 / sütun 4 / satır 2,3,4,5,6,7,8,9

  Yapılacak: s.98, tablo 10, satır 2, sütun 4; s.98, tablo 10, satır 3, sütun 4; s.98, tablo 10, satır 4, sütun 4; s.98, tablo 10, satır 5, sütun 4; s.98, tablo 10, satır 6, sütun 4; s.98, tablo 10, satır 7, sütun 4; s.98, tablo 10, satır 8, sütun 4; s.98, tablo 10, satır 9, sütun 4: Bütçe İçi Toplam = «BOŞ». Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.

- [ ] Ekonomik tablo · 2028 Tahmin

  **Hücreler:** s.98 / T10 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: s.98, tablo 10, satır 2, sütun 5; s.98, tablo 10, satır 3, sütun 5; s.98, tablo 10, satır 4, sütun 5; s.98, tablo 10, satır 5, sütun 5; s.98, tablo 10, satır 6, sütun 5; s.98, tablo 10, satır 7, sütun 5; s.98, tablo 10, satır 8, sütun 5; s.98, tablo 10, satır 9, sütun 5: Bütçe İçi Toplam = «BOŞ». Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.

- [ ] Ekonomik tablo · 2029 Tahmin

  **Hücreler:** s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9

  Yapılacak: s.98, tablo 10, satır 2, sütun 6; s.98, tablo 10, satır 3, sütun 6; s.98, tablo 10, satır 4, sütun 6; s.98, tablo 10, satır 5, sütun 6; s.98, tablo 10, satır 6, sütun 6; s.98, tablo 10, satır 7, sütun 6; s.98, tablo 10, satır 8, sütun 6; s.98, tablo 10, satır 9, sütun 6: Bütçe İçi Toplam = «BOŞ». Kaynak kayda göre açık bir sayısal tutar yazın; boş hücreyi sıfır varsaymayın.


### Sosyal Destek Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Strateji Geliştirme Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.215 / T159 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29; s.215 / T160 / sütun 5 / satır 2,3,4,5,6,7

  Yapılacak: Faaliyet maliyetleri toplamı 2.325.528,00 + ortak personel/SGK 4.495.313,00 = 6.820.841,00 olmalı; ekonomik tablo toplamı 6.770.841,00 (fark -50.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 2.325.528,00, ekonomik personel/SGK hariç toplam 2.275.528,00 (fark -50.000,00). İki tabloda bu finansman tutarları eşit olmalı.


### Tarımsal Hizmetler Müdürlüğü

Gönderime hazır: **Hayır**; 6 kitap mesajı / 3 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2027

  **Hücreler:** s.156 / T83 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 9.221.747,00 + ortak personel/SGK 6.115.460,00 = 15.337.207,00 olmalı; ekonomik tablo toplamı 15.287.207,00 (fark -50.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 9.221.747,00, ekonomik personel/SGK hariç toplam 9.171.747,00 (fark -50.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.156 / T83 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 9.576.838,00 + ortak personel/SGK 7.644.325,00 = 17.221.163,00 olmalı; ekonomik tablo toplamı 17.121.163,00 (fark -100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 9.576.838,00, ekonomik personel/SGK hariç toplam 9.476.838,00 (fark -100.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.156 / T83 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 8.517.000,00 + ortak personel/SGK 9.555.406,00 = 18.072.406,00 olmalı; ekonomik tablo toplamı 17.972.406,00 (fark -100.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 8.517.000,00, ekonomik personel/SGK hariç toplam 8.417.000,00 (fark -100.000,00). İki tabloda bu finansman tutarları eşit olmalı.


### Temizlik İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Veteriner İşleri Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Yazı İşleri Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.228 / T179 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9

  Yapılacak: Faaliyet maliyetleri toplamı 21.348.440,00 + ortak personel/SGK 30.882.000,00 = 52.230.440,00 olmalı; ekonomik tablo toplamı 52.230.432,00 (fark -8,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 21.348.440,00, ekonomik personel/SGK hariç toplam 21.348.432,00 (fark -8,00). İki tabloda bu finansman tutarları eşit olmalı.


### Zabıta Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Çevre Koruma ve Kontrol Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### Özel Kalem Müdürlüğü

Gönderime hazır: **Hayır**; 4 kitap mesajı / 2 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.199 / T137 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 27.762.500,00 + ortak personel/SGK 42.562.500,00 = 70.325.000,00 olmalı; ekonomik tablo toplamı 69.125.000,00 (fark -1.200.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 27.762.500,00, ekonomik personel/SGK hariç toplam 26.562.500,00 (fark -1.200.000,00). İki tabloda bu finansman tutarları eşit olmalı.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.199 / T137 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 26.903.125,00 + ortak personel/SGK 53.203.125,00 = 80.106.250,00 olmalı; ekonomik tablo toplamı 78.906.250,00 (fark -1.200.000,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 26.903.125,00, ekonomik personel/SGK hariç toplam 25.703.125,00 (fark -1.200.000,00). İki tabloda bu finansman tutarları eşit olmalı.


### İklim Değişikliği ve Sıfır Atık Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### İmar ve Şehircilik Müdürlüğü

Gönderime hazır: **Evet**; 0 kitap mesajı / 0 kitap kontrol maddesi.

Kitap düzeltmesi yok.

### İnsan Kaynakları ve Eğitim Müdürlüğü

Gönderime hazır: **Hayır**; 2 kitap mesajı / 1 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2028

  **Hücreler:** s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 12.577.220,00 + ortak personel/SGK 26.757.500,00 = 39.334.720,00 olmalı; ekonomik tablo toplamı 39.334.716,00 (fark -4,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin. Bütçe İçi faaliyet toplamı 12.577.220,00, ekonomik personel/SGK hariç toplam 12.577.216,00 (fark -4,00). İki tabloda bu finansman tutarları eşit olmalı.


### İşletme ve İştirakler Müdürlüğü

Gönderime hazır: **Hayır**; 20 kitap mesajı / 6 kitap kontrol maddesi.

- [ ] Çapraz maliyet/toplam farkı · 2029

  **Hücreler:** s.241 / T195 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Faaliyet maliyetleri toplamı 111.436.000,00 + ortak personel/SGK 15.809.760,00 = 127.245.760,00 olmalı; ekonomik tablo toplamı 127.244.960,00 (fark -800,00). Hangi tablonun yanlış olduğunu Strateji ile belirleyin.

- [ ] Ekonomik tablo · 2027 Bütçe

  **Hücreler:** s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8

  Yapılacak: Kategori satırlarının toplamı 94.787.000,00, Bütçe İçi Toplam 95.354.000,00 (fark 567.000,00). Yanlış satırı veya toplamı düzeltin.

- [ ] Ekonomik tablo · 2029 Tahmin

  **Hücreler:** s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 7 / satır 20

  Yapılacak: Kategori satırlarının toplamı 127.244.960,00, Bütçe İçi Toplam 127.245.760,00 (fark 800,00). Yanlış satırı veya toplamı düzeltin. Ekonomik personel/SGK 15.808.960,00, ortak personel/SGK 15.809.760,00 (fark -800,00). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.

- [ ] SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2026 Yıl Sonu Tahmini

  **Hücreler:** s.239 / T191 / sütun 6 / satır 10

  Yapılacak: s.239, tablo 191, satır 10, sütun 6: Gösterge kaynak değeri alanını kaynak kayda göre tamamlayın. Beklenen kural: açık sayısal değer, eksiksiz açıklama ve kaynak toplamlarıyla tutarlılık.

- [ ] SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2027 Hedef

  **Hücreler:** s.239 / T191 / sütun 7 / satır 10

  Yapılacak: s.239, tablo 191, satır 10, sütun 7: Gösterge kaynak değeri alanını kaynak kayda göre tamamlayın. Beklenen kural: açık sayısal değer, eksiksiz açıklama ve kaynak toplamlarıyla tutarlılık.

- [ ] Personel/SGK toplam farkı · 2029

  **Hücreler:** s.241 / T195 / sütun 7 / satır 20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8

  Yapılacak: Ekonomik personel/SGK 15.808.960,00, ortak personel/SGK 15.809.760,00 (fark -800,00). İki kaynakta aynı tutar olmalı; yanlış hücreyi düzeltin.


## Dönüşüm ve varsayımlar

Eşlenmeyen ad (ham metin korundu, yerleşik müdürlük eşlemesi uygulandı): İşletme ve İştirakler Müdürlüğü.

Basılı sayfaya bağlı olmayan tablolar (dışlama seçeneğinden bağımsız; yüklemeye alınmaz): [{"id": "u2cfi5928", "type": "cost"}, {"id": "u2cfi5968", "type": "economic"}, {"id": "u2b9i5978", "type": "card"}, {"id": "u2b9i5993", "type": "membership"}].

Teyit bekleyen ad eşlemeleri: Yok (D-94, 19 Ekim 2026 proje sahibi teyidi). Program/alt program kodları kitapta yoktur ve boş bırakılır. Tekil müdürlük içi faaliyet kodu üyeliği belirler. Resmî katalog 0006 Özel Kalem gibi maliyet karşılığı bulunmayan üyelikleri korur; yeni maliyet üretilmez. Nihai kitap dışlamasız yeniden denenmelidir.
