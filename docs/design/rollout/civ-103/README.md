# CIV-103 · EK-1 tamamlanma görünümü (009/010)

Başlangıç: `feature/authorization-workflow-phase5`, `7289c27` (CIV-102 / #132 sonrası). Yalnız sentetik kayıtlar ve bu görev için açılan geçici PostgreSQL 16 kullanıldı. Liste rapor başlıkları altında gruplanır; 390 px’de tablo satırları DOM sırasıyla kartlara dönüşür. Üç indirme bağlantısı rapor başına yerel **Dışa aktar** içinde; idare sürüm geçmişi aynı raporun altında kalır. 012’de yalnız kaynak tablosunun **Kaydet** başlığı tek satıra sabitlenir.

## Görseller

Chromium 151, DPR 1, `tr-TR`, `Europe/Istanbul`; viewport 1440×900 / 390×900. PNG’ler yalnız ilgili ekranın tam sayfa görünümüdür; 012 görselleri kaynak formunun yakın görünümüdür. Dolu/uyarı/dışa aktarma örnekleri mevcut `section=I.A` filtresini kullanır. Boş örnek ayrıca `status=not_applicable` kullanır. Her PNG ≤ 1.500.000 bayt. Başka ekranların toplu çekimi yapılmadı; çekim aracı ve JSON kaydedilmedi.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| 009 Strateji, dolu | [PNG](009-strategy-filled-1440.png) | [PNG](009-strategy-filled-390.png) |
| 010 Müdürlük, dolu | [PNG](010-department-filled-1440.png) | [PNG](010-department-filled-390.png) |
| Boş filtre sonucu | [PNG](009-empty-1440.png) | [PNG](009-empty-390.png) |
| Rapor hatası ve benzerlik uyarısı | [PNG](009-warning-1440.png) | [PNG](009-warning-390.png) |
| Dışa aktarma açık | [PNG](009-export-open-1440.png) | [PNG](009-export-open-390.png) |
| 012 kaynak tablosu başlığı | [PNG](012-resource-header-1440.png) | [PNG](012-resource-header-390.png) |

Uyarı görseli, geçerli yerel yanıt bağlamına eklenen sentetik hata/benzerlik mesajlarıyla üretilir; veritabanı bozulmaz. Onaylı kopya ve iki sürümlü idare yeniden açma zinciri gerçek oturum/CSRF üzerinden sözleşme testinde doğrulanır.

## Koruma ve doğrulama

- `tests/fixtures/section_index_009_010.html`: başlangıç şablonunun değiştirilmeden dondurulmuş kopyası. Gerçek route bağlamı aynı ortamda eski ve yeni şablona verilir; tüm form/link/alan/option öznitelikleri ve değerleri, seçili durumlar, alanların gerçek method/action bağı ve sırası, düğme/bağlantı/etiket metinleri karşılaştırılır. Yalnız sunum class/style ve CSRF’nin rastgele değeri envanterden çıkarılır; CSRF alanı ve gerçek oturum değeri ayrıca kontrol edilir.
- `tests/test_section_index_design.py`: Strateji/müdürlük × tüm/yıl/bölüm/durum/birleşik/boş filtre; iki idare sürümü, onaylı kopya, gerekçeyle açma ve eksik ad fallback’i; bölüm ve sürümlü indirme URL’leri, rol görünürlüğü, iki `role="status"` uyarısı; 1440/390 gruplama, Enter/Space/Tab, filtre yerleşimi, sayfa/kart taşması, metin kontrastı; 012’nin I.C.1/I.C.3/I.C.4 kaynak başlıkları.
- Mevcut `tests/test_section_editor_design.py` assertion’ları değiştirilmedi. Hedefli testler ve tam PostgreSQL suite sonuçları PR açıklamasında kaydedilir.

```sh
# CIVENSA_TEST_POSTGRES_URL yalnız geçici yerel PostgreSQL 16+ adresidir.
# Sistem Chromium’u kullanmak için CIVENSA_CHROMIUM_PATH=/usr/bin/chromium.
python -m pytest -q --require-postgres tests/test_section_index_design.py tests/test_section_editor_design.py
python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0
```

## Kontrast

Gerçek hesaplanmış metin/zemin çiftleri; normal/hover/odak, açık dışa aktarma, boş durum, uyarılar ve tüm bölüm/iş akışı rozet renkleri ölçüldü. Tüm renkler `tokens.css` içinden gelir. En düşük metin kontrastı **4,71:1** (Hazır/Onaylandı/Onaylı kopya); eşik 4,5:1.

| Metin | Zemin | Kontrast |
| --- | --- | --- |
| `--warning` | `--warning-bg` | 5.41:1 |
| `--accent-hover` | `--surface` | 8.58:1 |
| `--surface` | `--accent-hover` | 8.58:1 |
| `--surface` | `--accent` | 6.28:1 |
| `--accent` | `--accent-soft` | 5.37:1 |
| `--accent` | `--warning-bg` | 5.73:1 |
| `--accent` | `--surface` | 6.28:1 |
| `--success` | `--success-bg` | 4.71:1 |
| `--text` | `--surface-muted` | 13.50:1 |
| `--text` | `--surface` | 15.80:1 |
| `--text-secondary` | `--surface-muted` | 5.87:1 |
| `--text-secondary` | `--surface` | 6.87:1 |

## Görünür metin değişiklikleri ve sınırlar

- 012’den alınan **Dışa aktar** etiketi eklendi.
- `Gerekçeyle açıldı · {ad} (Kullanıcı {id}) · {tarih}` → `Gerekçeyle açıldı · {ad} · {tarih}`. Ad eksikse `Kullanıcı {id}` kullanılır.
- Tekrarlanan yıl/rapor değeri ve **Yıl / Rapor** sütun etiketi grup başlığına taşındı; dışa aktarmadaki rapor ile düğmeler arasındaki `·` ayıracı yerleşimle kaldırıldı. Mobilde mevcut dört sütun etiketi kart içinde tekrarlanır. Sözcükler, değerler ve mevcut büyük harf gösterimi korunur.

Canlı veri/ortam, farklı tarayıcılar ve ekran okuyucu yazılımıyla doğrulama yapılmadı. Bu çalışma tam WCAG uygunluğu beyanı değildir. Route, servis, şema, yazma yolu, ortak shell/token dosyaları ve eski `activity_sections.css` değişmez.
