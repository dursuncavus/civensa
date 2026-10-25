# CIV-098 · Modüller ızgara ve simgeler

D-234 geri bildirimi doğrultusunda 033/034 ekranlarında içerik genişliği ≥ 960 px olduğunda üç eşit kart, altında tek sütun kullanılır. CSS container query eşiği içerik alanına bağlıdır. Ortak satırlar başlık, açıklama ve yardım metinlerinin üst kenarlarını hizalar; eylemler kart altında biter. Faaliyet Raporu’nun iki eylemi korunur ve son düğmesi diğer kartların düğmeleriyle hizalanır.

01/02/03 yerine 28 px, currentColor, 1.5 çizgi kalınlığında, aria-hidden SVG simgeleri kullanılır. Kaynak: [Lucide 0.468.0](https://github.com/lucide-icons/lucide/tree/0.468.0/icons), `target`, `file-text`, `shield-check`; yalnız boyut, çizgi kalınlığı ve sunum/erişilebilirlik öznitelikleri uyarlandı. [ISC lisansı](../../../../app/static/design/icons/LICENSE-lucide.txt) depoya eklendi. Yeni bağımlılık veya dış kaynak isteği yok.

Türkçe metinler, mevcut düğmeler, href değerleri ve rol koşulları korunur. Kartlar bağlantı değildir. D-224 gereği kenarlık/yüzey kullanılır; gölge, gradyan veya hareket eklenmedi.

## Görseller

Sentetik verili gerçek uygulama; Chromium 151.0.7922.173, DPR 1, 900 px viewport yüksekliği, tr-TR, Europe/Istanbul, tam sayfa PNG. Kesin tarayıcı sürümü ve ölçümler capture-summary.json içindedir.

| Ekran | 1440 px | 390 px |
| --- | --- | --- |
| 034 · Müdürlük | [PNG](034-modules-department-1440.png) | [PNG](034-modules-department-390.png) |
| 033 · Strateji | [PNG](033-modules-strategy-1440.png) | [PNG](033-modules-strategy-390.png) |

En büyük PNG 110.676 bayt (< 1.500.000). Görünüm için ürün sahibi onayı beklenir.

## Doğrulama

- `python -m pytest -q --require-postgres tests/test_design_shell.py tests/test_sidebar_ui.py tests/test_module_selection.py`: PostgreSQL 18 üzerinde **25 geçti**, 1 bağımlılık deprecation uyarısı.
- `python docs/design/rollout/civ-098/verify_rollout.py`: **8 yakalama, 0 kayıp/taşma/kırpılma/çakışma/hizalama/kontrast hatası**. 1440/390 yanında 1303/1304 viewport genişliklerinde içerik tam 959/960 px ölçülür; tek sütundan üç sütuna geçiş doğrulanır.
- Eski 033 için 20, 034 için 14 öğe/hedef, etiket/kimlik/alan adı/tür/hedef bazında yinelenenler dahil karşılaştırılır. CIV-096’nın envanter normalleştirmesi kullanılır. Toplam 136 öğe karşılaştırması, **0 kayıp**.
- Gerçek çizilen simge rengi `--accent` **#1e6b65**, kart yüzeyi `--surface` **#ffffff**: **6,28:1 ≥ 3:1**. SVG 28×28, stroke 1.5, aria-hidden ve focusable=false doğrulandı. Her kart düğmesinde görünür 2 px accent odak çizgisi doğrulandı.
- Kartlar masaüstünde eşit genişlik/yükseklikte; başlık/açıklama/yardım üst kenarları ve son düğme alt kenarları en fazla 1 px farkla hizalı.
- Yakalama öncesi/sonrası tüm model tablolarının özeti aynı. Yalnız geçici yerel veritabanı ve sentetik fixture kullanılır.

Tekrarlamak için requirements-dev.txt, yerel PostgreSQL 16+ ve Chromium kurulu olmalı. `CIVENSA_TEST_POSTGRES_URL` yerel test veritabanına, `CIVENSA_CHROMIUM_PATH` Chromium dosyasına ayarlanır. Ara PNG’ler `/tmp/civ098-captures/` altında kalır. [capture-summary.json](capture-summary.json) ve [screenshots.json](screenshots.json) ölçüm kanıtlarıdır.

Değişen uygulama dosyaları: `app/templates/modules.html`, yalnız Modüller kurallarıyla `app/static/design/shell.css`, `app/static/design/icons/LICENSE-lucide.txt`. Testlerde numara markup beklentisi bulunmadığı için test dosyası değişmedi. CIV-097 dosyalarına dokunulmadı. Varsayım: tek eylemli kartların düğmesi, iki eylemli kartın son düğmesiyle altta hizalanır.
