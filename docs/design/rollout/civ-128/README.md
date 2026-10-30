# CIV-128 — Mutabakat tablosunda kısa durum

Ekran görüntüleri sentetik verilerle `/program/{department_id}` sayfasından alınmıştır. Her iki genişlikte de kapalı durum ve bir satırın ayrıntıları açık durum gösterilir. PNG dosyalarının her biri 1.500.000 bayttan küçüktür.

- 1440 px: [kapalı](in-progress-1440-closed.png) · [açık](in-progress-1440-open.png)
- 390 px: [kapalı](in-progress-390-closed.png) · [açık](in-progress-390-open.png)

Yeniden üretmek için geçici PostgreSQL veritabanı ve Chromium ile şu odaklı test çalıştırılır:

```sh
CIVENSA_CIV128_SCREENSHOTS=docs/design/rollout/civ-128 \
CIVENSA_CHROMIUM_PATH=/usr/bin/chromium \
python -m pytest -q --require-postgres tests/test_pp_reconciliation_details.py
```
