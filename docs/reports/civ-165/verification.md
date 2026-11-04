# CIV-165 — prova ve kullanım notları

Taban: `feature/authorization-workflow-phase5`, `a0f91a6`. Migrasyon eklenmedi; tek Alembic head `c162a1b2c3d4`. Canlı veritabanına bağlanılmadı, merge/deploy yapılmadı.

## Yerel prova

`CIVENSA_TEST_POSTGRES_URL`, CREATE DATABASE yetkili, disposable, yalnız loopback PostgreSQL 16+ hedefini göstermelidir. Uygulamanın DATABASE_URL / MIGRATION_DATABASE_URL değerleri prova girdisi değildir.

```sh
python scripts/first_load_dryrun.py --year 2026 --out docs/reports/civ-165/dryrun_2026.md
```

Komut önce aynı geçici veritabanına onaylı 2027 kitabını yükler, sonra 2026 yazımını gerçek ilk yükleme servisleriyle uygular. Her kaynak faaliyet satırı, importer snapshot'ındaki kayıt kimliği üzerinden denetlenir; aynı adlı faaliyetler ilk ada bakılarak karşılaştırılmaz. Veritabanı sonunda kaldırılır. Sayımlar ve önce/sonra 2027 hash'i `dryrun_summary.json` içindedir; tüm bağlanmayan faaliyetler `dryrun_2026.md` içinde listelenir.

2027 varsayılan raporu, taban commit'indeki komutla aynı kaynak ve aynı çıktı yolu kullanılarak karşılaştırıldı. `cmp` başarılı; rapor SHA256 `c3a1236edd1242cf2ebb2b5eded734f3c21f97767eae0a973a61d07963bb9be4`. Yeni komutun bayraksız ve açık `--year 2027` çıktıları da aynı baytları verdi.

## Sahibin sonraki uygulaması

Bu görev canlı yüklemeyi çalıştırmaz. Mevcut [ilk yükleme runbook'u](../../first-load/live-runbook.md) ve [doğrulanmış yedek adımları](../../operations/db-backup.md) geçerlidir. Bağlantı yalnız mevcut gizli ortam değişkeni üzerinden alınır; CLI argümanına yazılmaz.

- Plan: `python scripts/first_load_live.py --year 2026 --organization-id N --actor-id N`. Varsayılan salt okunurdur, 0 satır yazar.
- Uygulama: aynı komuta `--apply --backup /YOL/dogrulanmis.dump` eklenir. Şema pini, bir saatten yeni doğrulanmış yedek ve 2026 kitap SHA256 önekinin yazılması zorunludur. Ön baskı temizliği 2026 için reddedilir.
- `--resume`, aynı yıl ve SHA256 ile yazılmış tamamlanma makbuzu bulunan müdürlükleri atlar; sonradan yapılan kullanıcı düzeltmelerini korur. Başka yüklemeye ait 2026 PP verisi varsa durur. 2026 tüm çalışma tek işlemde tamamlandığından beklenmedik hata veya 2027 hash farkında yeni çalışmanın tüm yazımları geri alınır. İptal edilen çalışmadan sonra önce yeniden plan alınmalıdır.

## Açık varsayımlar ve sınırlar

- Açıklama tablolarındaki “ETÜT VE PROJE MÜDÜRLÜĞÜ” → “Etüd Proje Müdürlüğü” ve “Afet İşleri ve Risk Yönetim Müdürlüğü” → “Afet İşleri ve Risk Yönetimi Müdürlüğü” ek eşlemeleri proje sahibi tarafından bu görev sırasında açıkça onaylandı. 2026 görünüm adı kartın kanonik “Sorumlu İdare” satırından gelir.
- 2026 ekonomik tablolarının sorumluluğu, sayfadaki fiziksel okuma sırasında en son açık müdürlük başlığı taşıyan açıklama tablosundan alınır. Sonrasında tablo ilgili müdürlük kartlarının arkasına taşınır. IDML export kimliği veya maliyet benzerliği eşleme amacıyla kullanılmaz.
- Katalogda her farklı program / alt program / faaliyet adı / açıklama dörtlüsü bir kayıttır. Mevcut OfficialActivity şemasında açıklama alanı bulunmadığı için açıklama, katalog denetim kaydının kaynak verisinde korunur. Zorunlu ve 80 karakterle sınırlı kod alanındaki `name:` SHA256 değeri teknik kimliktir; resmî faaliyet kodu değildir. Müdürlük içindeki normalleştirilmiş faaliyet adı ve katalog adının ikisi de tekil olmadıkça bağlantı kurulmaz.
- Kitabın boş hedefleri, çizgileri ve aritmetik/kapsam sorunları düzeltilmez. Doğrulama hataları gönderime hazır olunduğunu göstermez; 0 yükleme reddi ile karıştırılmamalıdır. Mevcut ekonomik kolon sözleşmesi önceki yıl sonu harcama sütununu saklamaz; bu 2027 davranışıdır. Üretilen Word bu sütunu korur.
- PDF ayrıca doğrulanmadı; IDML-PDF eşitliği görevdeki D-371 teyididir. InDesign dizgisi çalıştırılmadı. 14 Ekim 2026 varyantı depoda yok; yanlış dosya koruması 2027 kitabı ve onaysız içerik ile sınanır.
- Gösterge aday raporu tüm 226 göstergeyi, eşleşmeyenler dahil, gösterir. Aynı müdürlükte SH/PG öneki çıkarılmış tam ad eşitliğine göre 37 göstergenin toplam 48 adayı vardır. Birim ve 2026 hedef/planlanan değerleri ayrı karşılaştırılır. Kalıcı kimlik bağlantısı yapılmaz; bu daha sonra gerekçeli Strateji işlemidir.
