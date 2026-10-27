# CIV-126 · Faaliyet raporları

004 (strateji) / 005 (müdürlük), GET `/activity-reports`. Bütün örnekler sentetiktir.

| Senaryo | 1440 px | 390 px |
| --- | --- | --- |
| Strateji: revizyonlar ve oluşturma formu | [Görüntü](strategy-1440.png) | [Görüntü](strategy-390.png) |
| Müdürlük: revizyonlar | [Görüntü](department-1440.png) | [Görüntü](department-390.png) |
| Boş liste ve yayın bulunamadı | [Görüntü](empty-1440.png) | [Görüntü](empty-390.png) |
| Strateji: revizyonlar var, yayın yok | [Görüntü](no-publications-1440.png) | [Görüntü](no-publications-390.png) |

Görseller `tests/test_activity_reports_design.py` ile Chromium'da üretilir; her PNG
1.500.000 bayttan küçüktür. `CIVENSA_CIV126_SCREENSHOTS` bu dizini seçer.
Testler 1440, 1024, 620 ve 390 px'te yatay sayfa taşmasını; başlangıç şablonuyla
başlık geometrisi ve satır sarmayı; 44rem revizyon satırlarını; formun 1024 px'te
iki, 390 px'te tek sütun olmasını ve görünür metnin normal/hover/focus
kontrastının en az 4,5:1 olmasını doğrular. Uzun sentetik kurum adları ayrıca denenir.

Başlangıç şablonu `tests/fixtures/activity_contract_index_start.html` içinde bayt
bayt korunur (SHA-256: `ba26b6a53cb7000bb123174bdd35668c7b26d1f7a8c30e4fe605def1053305ab`).
Dört senaryoda bütün bağlantı adresleri, form yöntemi/adresi, gizli alanlar,
alan adları, seçenekler ve required/disabled özellikleri, revizyon rozetleri ve
gerekçeleri aynı bağlamla karşılaştırılır. Gerçek GET yanıtı da iki rolle denenir.

Görünür metin değişikliği yalnızca başlıktadır:
`Faaliyet Raporları` → `Faaliyet raporları`.
Özel adlar, boş durum cümleleri, açıklamalar ve form metinleri korunur.

Kabuk kuralları sayfa CSS'ine taşındı. Eski `.app:has(.activity-contract-content)`
seçicileri korunur; mevcut `.app-shell` başlığı ise başlangıç şablonuyla tarayıcıda
karşılaştırılır. Başka sayfalar yeni CSS'i yüklemez.

Doğrulama yalnızca yerel, geçici veritabanı ve Chromium ile yapılır; canlı veri
kullanılmaz. Diğer tarayıcı motorları bu çalışma kapsamında doğrulanmadı.
Tam paket, eski testlerin ürettiği dosyaları çalışma deposundaki
`tests/artifacts/**` dizinine yazmamak için geçici depo kopyasında çalıştırılır.
