# CIV-105 · İç Kontrol Eylemlerimiz

Başlangıç: `feature/authorization-workflow-phase5`, `264c04b`.
Yalnız iki müdürlük şablonu ve `.ic-our-actions-page` altında yeni CSS değişti.
Plan özeti, eylem kartları, tanım listeleri, dönem araç çubuğu, durum rozetleri,
salt okunur bildirimleri, alan hataları ve katkı notları D-224 tokenlarını kullanır.
Ortak makrolar import edilir; genel shell override’larını içeren eski style bloğu bu
sayfada include edilmez. Ortak dosyalar ve Strateji ekranları değiştirilmedi.

UI haritasında 029 paket ayrıntısı, 030 `/internal-control/our-actions` ekranıdır.
Bu görev aynı rotanın dönemli/dönemsiz durumlarını kapsar; PNG adları durum belirtir.

## Görseller

Chromium 151, 1440×900 ve 390×900 viewport, DPR 1. Yalnız sentetik kayıtlar,
geçici yerel PostgreSQL 18, gerçek şablonlar ve statik dosyalar kullanıldı.
Dönem durumları ve alan hatası render bağlamında çeşitlendirildi; hata mevcut
`pp_form` filtresinden üretildi. Uzun kesintisiz kod/metin örnekleri taşmayı sınar.
Ana görseller tam sayfa; katkı notu görselleri aynı sayfada forma kaydırılmış viewport’tur.
10 PNG’nin tamamı 1.500.000 bayttan küçüktür. Başka ekranların toplu çekimi,
çekim aracı veya JSON commit edilmedi.

| Durum | 1440 px | 390 px |
| --- | --- | --- |
| Dönem yok, eylemler var | [PNG](no-period-actions-1440.png) | [PNG](no-period-actions-390.png) |
| Dönem yok, boş | [PNG](no-period-empty-1440.png) | [PNG](no-period-empty-390.png) |
| Açık dönem, giriş ve alan hatası | [PNG](open-error-1440.png) | [PNG](open-error-390.png) |
| Kapalı dönem, salt okunur | [PNG](closed-1440.png) | [PNG](closed-390.png) |
| İşbirliği katkı notu formu | [PNG](cooperating-note-1440.png) | [PNG](cooperating-note-390.png) |

## Doğrulama

`tests/test_ic_our_actions_design.py`: 44 senaryo. Başlangıçtaki iki şablonun,
iki Strateji şablonunun ve iki ortak parçanın baytları SHA-256 ile donduruldu.
Aynı bağlamda form method/action, tüm kontrol öznitelikleri, CSRF/gizli alanlar,
maxlength, alan/form eşleşmeleri, bağlantılar/query, seçenekler/seçili durum,
alan değerleri ve görünür metinler karşılaştırılır. Rol, gönderim yetkisi,
taslak/iade/gönderilmiş/onaylı/kapalı/süresi dolmuş dönem, boş durumlar ve
sıfır/boş ayrımı kapsanır. Strateji izleme ve paket ekranları açık ve kapalı gerçek
dönemlerde başlangıç şablonlarıyla bayt düzeyinde aynı HTML’i üretir.

16 tarayıcı senaryosunda iki genişlikte taşma yok, büyük harf text-transform yok;
normal/hover/odak metin kontrastları ≥4,5:1. Dönem seçimi GET ile `period_id`
gönderir; katkı notu formunun POST adresi, `id`, `content` ve gerçek oturum CSRF
alanı mock üzerinde doğrulanır. Hata alan yanında, korunmuş değer ve erişilebilir
hata bağlantısıyla görünür. Mevcut test assertion’ları değiştirilmedi.

Hedefli komut: `python -m pytest -q --require-postgres tests/test_ic_our_actions_design.py tests/test_internal_control_monitoring.py`
→ **73 geçti**. Görsel üretiminde seçilen tarayıcı senaryoları → **8 geçti**.
Tam paket: `python -m pytest -q --require-postgres -n 4 --dist loadfile --max-worker-restart=0`.
Son tam paket ve CI sonuçları PR açıklamasındadır.

## Kontrast

Tarayıcı gerçek hesaplanmış metin/zemin renklerini kontrol eder.

| Token metin / zemin | Oran |
| --- | --- |
| `--text` / `--surface` | 15,80:1 |
| `--text` / `--bg` | 14,49:1 |
| `--text` / `--accent-soft` | 13,51:1 |
| `--text-secondary` / `--surface` | 6,87:1 |
| `--text-secondary` / `--surface-muted` | 5,87:1 |
| `--accent` / `--surface` (tersi de aynı) | 6,28:1 |
| `--accent` / `--bg` | 5,76:1 |
| `--accent` / `--accent-soft` | 5,37:1 |
| `--accent-hover` / `--surface` (tersi de aynı) | 8,58:1 |
| `--danger` / `--surface` | 6,57:1 |
| `--danger` / `--danger-bg` | 5,75:1 |
| `--warning` / `--warning-bg` | 5,41:1 |
| `--success` / `--success-bg` | 4,71:1 |

## Metinler ve sınırlar

- `Çıktı / Sonuç:` → `Çıktı / sonuç:`.
- `Başlama: {değer} · Tamamlanma: {değer}` → aynı etiket/değerler ayrı tanım
  satırlarında; aradaki `·` kaldırıldı.
- Eski CSS’nin büyük harf gösterimi kaldırıldı (kaynak metinler aynı):

| Önce (görünüm) | Sonra |
| --- | --- |
| İZLEME DÖNEMİ | İzleme dönemi |
| DURUM | Durum |
| GERÇEKLEŞME ORANI % (0–100) | Gerçekleşme oranı % (0–100) |
| AÇIKLAMA (UYGUN GÖRÜLMEYEN EYLEMDE ZORUNLU) | Açıklama (uygun görülmeyen eylemde zorunlu) |
| TAMAMLANMAMA NEDENİ | Tamamlanmama nedeni |
| KANIT REFERANSI | Kanıt referansı |
| KATKI NOTU | Katkı notu |
| BAŞLANMADI VEYA EYLEM UYGUN GÖRÜLMEMİŞTİR DURUMUNDA BOŞ BIRAKILABİLİR. KISMEN TAMAMLANDI İÇİN 1–99 ZORUNLUDUR. BOŞ DEĞER SIFIR DEĞİLDİR. | Başlanmadı veya Eylem uygun görülmemiştir durumunda boş bırakılabilir. Kısmen tamamlandı için 1–99 zorunludur. Boş değer sıfır değildir. |
| SÜRESİ GEÇEN TAMAMLANMAMIŞ EYLEMLERDE VE GECİKMEDE DURUMUNDA ZORUNLUDUR. | Süresi geçen tamamlanmamış eylemlerde ve Gecikmede durumunda zorunludur. |
| EBYS EVRAK SAYISI/TARİHİ VEYA BAĞLANTI YAZIN. | EBYS evrak sayısı/tarihi veya bağlantı yazın. |

`İç Kontrol Eylemlerimiz` başlığı mevcut `tests/test_internal_control_monitoring.py`
ve `scripts/guide_screenshots.py` tarafından eşleştirildiği için korundu.
Diğer sabit metinler ve bağlantı etiketleri aynı kaldı.

Gönderilmiş/onaylı pakette eylem girişi salt okunur; dönem açıksa katkı notu
başlangıçtaki gibi eklenebilir. Süresi dolmuş dönemde giriş/not düzenleme kapalıdır;
ortak makronun yetkili kullanıcıya gösterdiği mevcut gönderim düğmesi de korundu.
Canlı ortam, diğer tarayıcılar ve ekran okuyucu yazılımıyla doğrulama yapılmadı.
