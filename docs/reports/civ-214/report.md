# CIV-214 — 2027 düzeltilmiş kitapla değiştirme

Gerçek SONN ile değiştirme **ENGELLİ**: kural 3 kataloglar farklıysa reddetmeyi emrediyor. Bu nedenle kabul 1 için başarılı ONAYLI → SONN provası iddia edilmiyor. Katalog geçişi tasarlanmadı; canlı bağlantı, dağıtım ve birleştirme yapılmadı.

## Yerel gerçek kitap provası

Geçici PostgreSQL 18 / `c197a1b2c3d4`: boş veritabanı → mevcut yükleyiciyle ONAYLI → değiştirme planı ve uygulama denemesi. Plan çıktısı ve taze SONN içerik hash’leri [rehearsal.json](rehearsal.json) dosyasında.

```text
programs: 28 → 28
subprograms: 38 → 38
official_activities: 291 → 290
activity_responsibilities: 291 → 290
indicator_values: 1578 → 1578
indicators: 263 → 263
activity_cost_values: 5172 → 5220
activity_catalogue_links: 286 → 290
activities: 291 → 290
economic_values: 1340 → 1340
department_cost_values: 204 → 204
submission_events: 0 → 0
submissions: 34 → 34
subprogram_scopes: 0 → 0
department_scopes: 0 → 0
report_cards: 64 → 64
ENGEL: 2027 subprograms: ONAYLI ve düzeltilmiş kitap katalogları farklı; katalog geçişini sorumluya planlatın.
ENGEL: 2027 official_activities: ONAYLI ve düzeltilmiş kitap katalogları farklı; katalog geçişini sorumluya planlatın.
ENGEL: 2027 activity_responsibilities: ONAYLI ve düzeltilmiş kitap katalogları farklı; katalog geçişini sorumluya planlatın.
Reddedilen: 3; hedefe 0 satır yazıldı.
```

Bütün public tablo satır hash’leri ve sequence değerleri önce/sonra eşit; 2026 ve 2028 içerikleri korunuyor. Ayrı boş veritabanına taze SONN yüklemesi başarılı; bütün içerik tablolarının ID/zaman dışı imzaları kaynak planıyla eşit. Üç okunamayan Makine İkmal hücresi `NULL / needs_review` ve özgün metniyle korunuyor.

Katalog farkları: `subprograms` amaç/gerekçe metninde 110 → 119 ve metin değişiklikleri; `official_activities` / `activity_responsibilities` içinde Özel Kalem 0006 kaldırılması, Makine İkmal 0002–0005 yeniden kodlaması, İşletme 0011–0015 → 0001–0005. Son exportun SHA256 sabitlemesi yanında katalog için lider kararı/ayrı kapsam gerekir; mevcut koruma aşılmamalı.

## Doğrulama ve sınırlar

- `tests/test_replace_approved_2027.py`: gerçek SONN ret provası ve taze yükleme hash eşitliği; katalogları aynı kontrollü test verisinde atomik değiştirme, taze yüklemeyle içerik eşitliği, 2026/2028 hash koruması; üçüncü müdürlük yüklemesindeki hatada ONAYLI satırlarının bütünüyle geri gelmesi.
- Retler: gösterge/kart/faaliyet/maliyet/ekonomik/personel/bağlantı/kapsam değişimi, CSV ve elle eşleştirme geçmişi, normal/onaylı-kitap yayınları, taslak dışı teslim ve olay geçmişi, IC/FR, dönemler arası bağ, yabancı paket/eksik işaret, katalog farkı, eksik/eski yedek, yanlış cümle, terminal yokluğu, onay sırasında eskiyen yedek ve mevcut advisory kilit. Her ret için bütün satır hash’leri ve sequence değerleri eşit.
- Katalogları aynı test verisindeki başarı, gerçek SONN değiştirmenin yerine sayılmıyor. Eski paketler/denetimler korunur; içerik eşitliği karşılaştırması bu tarihçeyi yeni yükleme gibi silmez. Tamamlanmış değiştirmede köken/`--resume` okuması doğrulanmış tek değiştirme makbuzunu kullanır; bozuk makbuz reddedilir.
- Mevcut yükleme/temizlik/2026/yayın testleri Chromium ile yerel PostgreSQL üzerinde çalıştırıldı. Kesin sonuçlar PR açıklamasında; tüm suite sonucu PR’nin son SHA CI kontrollerindedir.
- Gerçek canlı verinin ONAYLI ile eşitliği ve sahibin BEYAN’ı doğrulanmadı; bunları araç uygulama anında mekanik korumalarla denetler. Gerçek üretim yedeği kullanılmadı; test manifestleri yerel sentetik koruma verisidir.

## Kapsam

Yeni komut `scripts/replace_approved_2027.py`; mevcut yükleme hizmeti ve parser aynen kullanılır. ONAYLI kaynak imzaları CIV-058 yaklaşımıyla salt okunur yeniden kurulur. Yazma tek transaction / mevcut advisory kilit altında; güncel yedek ve tam terminal cümlesi zorunlu. Katalog hash makbuzu her yükleme öncesinde ve sonunda doğrulanır. Runbook’a **2027 düzeltilmiş kitap ile değiştirme** bölümü eklendi.

`app/**` istisnası yalnız salt okunur yardımcılar içindir: `app/first_load_sources.py` kitap pinlerini tek yerde tutar; paketlenmiş uygulama `scripts/` taşımadığı için köken denetiminin ortak pini okuması gerekir. `approved_book_provenance` ve CLI, tarihî ONAYLI ile aktif SONN kökenini ve doğrulanmış değiştirme makbuzunu ortak okur; bilinen salt okunur denetimler yazma sayılmaz. Uygulama yazma yolları, legacy FR korumaları, `ACTIVITY_REFERENCE_SUCCESSORS`, migrasyonlar ve bağımlılıklar değiştirilmedi.
