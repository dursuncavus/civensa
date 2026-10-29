# CIV-151 — Nihai rapor tasarım sistemi

039 ve 040 ekranları, mevcut tasarım tokenlarıyla sayfaya özel panel, alan ızgarası,
açılır kayıt satırı ve metinli durum rozeti kullanır. Başlangıç şablonları
`7e4335be69171077c28947144167e74f35fc9621` tabanından byte-byte saklandı.
Kanıtların tamamı sentetik veridir; PostgreSQL 17 geçici yerel container kullanıldı.

## Önce / sonra görüntüleri

Chromium 151, `tr-TR`, 900 px pencere yüksekliği, tam sayfa PNG; her dosya 1,5 MB altında.
039 dolu durumda bir kitap bölümü açık, iki yayın ve güncelliğini yitiren müdürlük
uyarısı var. Hatalı kayıt durumunda gönderilen başlık, tür, konum ve çok satırlı
içerik korunuyor; 040'ta ekleme/koruma/çakışma metin ve tabloları açık.

| Durum | 1440 önce | 1440 sonra | 390 önce | 390 sonra |
| --- | --- | --- | --- | --- |
| 039 dolu | [PNG](before-039-populated-1440.png) | [PNG](after-039-populated-1440.png) | [PNG](before-039-populated-390.png) | [PNG](after-039-populated-390.png) |
| 039 hatalı kayıt | [PNG](before-039-failed-section-1440.png) | [PNG](after-039-failed-section-1440.png) | [PNG](before-039-failed-section-390.png) | [PNG](after-039-failed-section-390.png) |
| 040 önizleme | [PNG](before-040-apply-1440.png) | [PNG](after-040-apply-1440.png) | [PNG](before-040-apply-390.png) | [PNG](after-040-apply-390.png) |

## Metin değişiklikleri

- Mevcut erişilebilir bölge adı “Yayın sürümleri”, görünür başlık olarak da gösterilir.
- Müdürlük ve önizleme özetlerinde ad ile durum arasındaki “ · ” kaldırıldı; durum tek rozette yer alır.
- “Sürüm N · Güncel sürüm” → “Sürüm N Güncel sürüm”.
- “Sürüm N · Önceki sürüm — Sürüm M ile değiştirildi” → “Sürüm N Önceki sürüm · Sürüm M ile değiştirildi”.

Diğer görünür metinler, formlar, alan değerleri, seçili seçenekler, açık kayıtlar,
ID/data/aria/role nitelikleri ve bağlantılar dondurulmuş sözleşmeyle karşılaştırılır.
`test_publication_history.py` içindeki dört metin iddiası yeni ayraçlara birebir uyarlandı.

## Doğrulama

- Yeni sözleşme, tasarım ve tarayıcı testleri: **33 geçti**.
- Aynı şablonların önce/sonra sürümlerinden gerçek handler'lara beş form gönderimi:
  **4 geçti**; kapsam, bölüm, dönemden kopyalama, katalog kaydı ve 422 yayın engeli.
- Mevcut yayın geçmişi, form hata kurtarma, PP gösterim, yapı değişikliği ve mali
  mutabakat testleri: **151 geçti**.
- 1440/390: sayfa yatay taşması yok; tablolar kendi sarmalayıcılarında kayar;
  görünen metinlerde normal/hover/focus kontrastı en az **4,5:1**; uppercase dönüşümü yok;
  alanlar ve durum satırları en fazla 44rem, masaüstü alan ızgaraları iki sütun,
  metin alanları tam genişlik ve 039'da tek birincil eylem.
- `git diff --check` temiz. Tam paket ve PR CI sonuçları PR açıklamasında izlenir.

Görüntüleri üretmek için yeni test dosyasını `CIVENSA_CIV151_SCREENSHOTS` bu klasörü
gösterecek şekilde çalıştırın. Sistem Chromium yolu `CIVENSA_CHROMIUM_PATH` ile seçilebilir.
Playwright/TestClient köprüsü gerçek POST handler'larını kullanır; 303 yanıtlarının
hedefi yerel TestClient içinde çözülür. İçe aktarma API başarı/hata yanıtları tarayıcı
senaryolarında denetimlidir; kalıcılık ve indirme bütünlüğü mevcut testlerle doğrulanır.
Canlı veri, canlı yayın veya dağıtım denenmedi. Başka tarayıcı motorları ve ekran
okuyucu ile manuel kullanım doğrulanmadı.
