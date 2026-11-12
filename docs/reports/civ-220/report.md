# CIV-220 — Yeni birim tablolarıyla müdürlük provası ve EK-1 listesi hızı

**SENTETİK prova. Yalnız atılabilir yerel PostgreSQL; canlı veritabanına bağlanılmadı.**

## Ne yapıldı
- `scripts/fr_rehearsal.py` (CIV-187/188 provası) her müdürlükte rehber Tablo 1, 2, 7, 8'i gerçek formlarla doldurur ve bir faaliyet fotoğrafı yükler (Tablo 7'de son faaliyet gerekçeli "Uygulanmadı").
- Prova düzeneği 9 Kasım'dan beri çalışmıyordu; ürün hatası değil, düzenek eskimişti:
  1. Yükleyici sabiti (CIV-219 ile) migrasyon başına eşitlendi; düzenek yardımcı tabloları silip yeniden oluşturmayı bekliyordu, yükseltme boş geçtiği için `indicator_directions` eksik kalıyordu. Şema zaten güncelse artık silinmez.
  2. Müdürlük listesinde yıl öneki yalnız birden çok yıl varken gösteriliyor (CIV-199/201); başlık eşleşmesi buna uyarlandı.
  3. Rapor kartındaki ikinci başlık (CIV-201 penceresi) İdare kartı aramasını bozuyordu; ilk başlık okunur.

## Bulgu ve düzeltme: EK-1 rapor listesi yavaştı
33 müdürlüklü provada Strateji'nin **Rapor bölümleri ve beyanlar (EK-1)** listesi yıl raporları oluşturulduktan sonra **33 saniyede** açılıyordu (sayfa zaman aşımı). Liste her müdürlük için rapor verisini kurar; her seferinde onaylı kitabı (çok MB'lık JSON) veritabanından çekip doğruluyor, ayrıştırıyor ve 2026 errata görünümünü baştan derin kopyalıyordu (CIV-190'dan beri; CIV-219 birim tabloları için ikinci bir kez ekledi).

Düzeltme: yayın SHA-256 ile sabit olduğu için aynı istekte kitap bir kez doğrulanıp ayrıştırılır (`app/ar_unit_tables_service.py` `pinned_snapshot`, `app/activity_financial_service.py` `pp_references`); büyük sütun sonraki sorgularda yeniden çekilmez (`defer`). Döndürülen planlı satırlar kopyadır, bir müdürlüğün görünümü diğerine sızmaz. Doğrulama kodu uyuşmazlığı ilk okumada yine reddedilir.

Sonuç (aynı makine, yerel ölçüm; canlı kapasite ölçümü değildir): EK-1 yıl raporlarını oluştur + liste **33 sn → 2,9 sn**, İdare raporuna geçiş **10,7 sn → 2,8 sn**.

## Prova sonucu
347 adım: 342 OK, 4 SLOW, 1 BLOCKER (`steps.json`).
- Üç müdürlük (Fen İşleri, Afet İşleri ve Risk Yönetimi, Özel Kalem) Tablo 1, 2, 7 (5 / 9 / 4 faaliyet), 8 ve fotoğrafı kaydetti; gönderdi, Strateji iade etti, yeniden gönderildi ve onaylandı; Word/PDF indirildi.
- CIV-188'deki üç "faaliyet başına sonuç yok" (B2) engeli kalktı: Tablo 7 artık faaliyet başına çıktı ve maliyet alıyor.
- Tek BLOCKER beklenen kapsam engelidir: diğer 30 müdürlük onaylanmadığı için İdare raporu dondurulamaz.
- SLOW: kitap yayın hazırlığı ve yayınlama (3,8–7,2 sn; tek seferlik Strateji adımları).

## Test
`tests/test_civ220_listing_reuse.py`: 33 müdürlüğün rapor verisi aynı oturumda kurulurken errata görünümü 1 kez (düzeltmeden önce 33), büyük kitap JSON'u 2 kez ayrıştırılır; kopya değişikliği diğer görünüme sızmaz.
