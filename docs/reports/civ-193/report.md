# CIV-193 — Faaliyet başına sonuç girişi yok (B2)

9.11.2026 Strateji kararı (D-446) doğrultusunda faaliyet sayfasını ziyaret eden prova adımı korundu; sonucu OK ve notu EK-1 bölüm metnine yönlendirme oldu. Son kontrol yalnız İdare dondurma kapsam engelini bekliyor; B2 veya başka bir engel, eksik ya da yinelenen kapsam engeli testi başarısız kılıyor.

Müdürlük kılavuzuna üç cümlelik faaliyet sonuçları bölümü ve Strateji Geliştirme Müdürlüğüne destek yönlendirmesi eklendi. Gösterge Excel toplu giriş yer tutucusu ve kılavuzun diğer içeriği korundu.

- Yerel, atılabilir PostgreSQL 18 üzerinde `python -m pytest -q --require-postgres tests/test_fr_rehearsal_harness.py tests/test_fr_guide_capture.py tests/test_ar_unit_workflow.py`: **27 geçti**. Kılavuz etiket kontrolü dahil; mevcut Starlette/httpx kullanımdan kaldırma uyarısı var.
- Chromium 151.0.7922.173 ile mevcut `guide_screenshots.main()` / `--fr-rehearsal` akışı çalıştırıldı; yalnız `fr_rehearsal.OUT` ve `SCREENS` geçici `/tmp/civ193-rehearsal/` altına yönlendirildi. Çıkış **0**; **329 adım: 323 OK, 5 SLOW, 1 BLOCKER**. B2: **0 BLOCKER**, üç Personel hesabında adım OK ve istenen karar notu mevcut. Tek BLOCKER, eksik diğer birimler nedeniyle beklenen İdare dondurma kapsam sınırı (HTTP 409).
- Fen İşleri, Afet İşleri ve Özel Kalem gönderim, iade, düzeltme, yeniden gönderim, bağımsız onay ve Word/PDF indirmelerini tamamladı. Hiçbir ekran gönderim öncesinde faaliyet başına ayrı sonuç istemedi; `app/` değişikliği gerekmedi. Sunucu/JavaScript/beklenmeyen ağ hatası: **0**. Adım sırası CIV-188 makine kanıtıyla aynı.
- `git diff --check`, değişen Python dosyalarının derlenmesi ve tek Alembic head kontrolü başarılı. Kılavuzda yalnız izin verilen iki değişiklik olduğu ayrıca karşılaştırıldı.

Sentetik veriler kullanıldı; canlı bağlantı, merge ve deploy yapılmadı. CIV-188 ekranları yenilenmedi. Tam 33 birim kapanışı ve canlı performans doğrulanmadı; beş SLOW kaydı yerel prova ölçümüdür. Kararın 2026 kapsamı esas alındı; yeni bağımlılık veya migrasyon eklenmedi. CI sonucu PR başında izlenir.
