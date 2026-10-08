# Açık issue: dolu PostgreSQL migration testinin ikinci çalıştırılması

Durum: açık; C1 sonrası veri sözleşmesi uygulamasından ayrı tutuldu.

Kullanıcının önceki oturumdan aktardığı bulgu: `tests/test_migration.py::test_populated_v4_migration[postgres]`, dolu test DB'sinde ikinci çalıştırmada çakışıyor.

Mevcut test aynı `CIVENSA_TEST_POSTGRES_URL` üzerinde eski migration seviyesini hazırlayıp id=1 kaynak satırları ekliyor; test sonunda oluşturduğu public şema verilerini kaldırmıyor. Bu, tekrar kullanılabilir migration test altyapısı için açık borçtur. Önceki oturumun kesin exception çıktısı bu checkout'ta doğrulanmadığından burada tahmin edilmez.

Bu işte eski testin davranışı değiştirilmedi ve dolu DB temizlenmedi. Tam test koşusu yeni boş, geçici bir PostgreSQL veritabanında çalıştırılır. Yeni sözleşme migration testi ayrıca kendine ait geçici şema kullanır; eski verilerin/indexlerin korunmasını, `upgrade head` tekrarının no-op olmasını ve snapshot UPDATE/DELETE korumasını SQLite/PostgreSQL üzerinde sınar.

Sonraki küçük görev: eski migration testine ait fixture/veritabanı yaşam döngüsünü izole etmek ve aynı suite'i aynı disposable DB'de iki kez başarıyla çalıştırmak. Kurum veya üretim veritabanında temizlik yapılmamalı.

Git remote bulunmadığı için GitHub issue oluşturulmadı; kayıt yerel issue olarak saklandı.
