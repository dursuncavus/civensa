# CIV-183 kabul kanıtı

2026-11-05 tarihinde, yalnız geçici yerel PostgreSQL 17.11 verileriyle üretildi.
1920×1080 Chromium 151 ekran görüntüleri:

- `karne.png`: onaylı üç müdürlük kaynağı; 10/10 Hedefte, 8/10 Yakın, 6/10 Geride. Son müdürlüğün boş gerçekleşmesi paydaya girmez.
- `karne-acilim.png`: Yakın satırının iki eksik göstergesi; boş sapma nedeni `—`.
- `pdf-acilim.png`: aynı açılımın `#pdf` görünümünde ayrı sayfası.
- `butce-dagilimi.png`: ekonomik harcama payları 34,0 + 27,0 + 22,0 + 6,0 + 6,0 + 5,0 = 100,0 TL. Son kutu, %5 altındaki faiz ve sermaye transferini birleştirir.

`single-file-size.txt`, testin indirdiği tek HTML dosyasının bayt boyutudur.
Dosya tüm font, Reveal ve ECharts kaynaklarını içerir; tarayıcı ağsız çalıştırılır.
Kaynaklar sentetik test kayıtlarıdır; canlı veritabanı kullanılmaz.

Üretim testi:

```bash
CIVENSA_MECLIS_ARTIFACTS=tests/screenshots/civ-183 \
python -m pytest -q --require-postgres \
tests/test_sunum_meclis.py::test_popup_browser_keyboard_pdf_pages_and_screenshots
```

Önkoşul: `CIVENSA_TEST_POSTGRES_URL` yalnız geçici yerel PostgreSQL 16+ veritabanına ayarlanmalıdır. Yönetilen tarayıcı ortamında test ayrıca mevcut `CIVENSA_CHROMIUM_PATH` ve `CIVENSA_SUNUM_HTTP_FIXTURE` seçeneklerini kullanabilir.
