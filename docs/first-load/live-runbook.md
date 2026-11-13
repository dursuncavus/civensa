# Onaylı 2027 Performans Programı — canlı ilk yükleme

Bu kılavuz sahibi ve sorumlunun ayrı yetkili operasyonu içindir. CIV-158 yalnız
tek kullanımlık yerel PostgreSQL üzerinde hazırlanır ve kanıtlanır. Canlı ilk
yükleme burada otomatik başlatılmaz.

Hedef uygulama **main 7ef5a20 veya daha yeni**, hedef ve yedek şeması yalnız
**c086a1b2c3d4** olmalıdır. Uygulama sürümünü sahibi dağıtım kaydından doğrular.
Farklı Alembic sürümünde durun; bu işlem sırasında migrasyon çalıştırmayın.
CIV-157 basılı tablo seçimini ve CIV-158 yükleyici değişikliklerini içeren,
sorumlunun onayladığı commit kullanılmalıdır.

Kaynak `tests/fixtures/first_load/source/2027-performans-programi_ONAYLI.idml`;
SHA256 **cbbf9018302d0a1d33d1dde0c4a64a2418d12b55cc29d046205371018673bd71**;
yazılı yükleme onayı **cbbf9018302d**.

Beklenen sonuç **34 müdürlük / 64 kart / 263 gösterge / 291 faaliyet /
1.340 ekonomik değer**. İşletme ve İştirakler Müdürlüğü dahildir; hiçbir
müdürlük Meclis verisi bekleniyor gerekçesiyle atlanmaz.

**D-324: Onaylı kitap kesindir; kitap kontrol maddeleri yüklemeyi durdurmaz, doğrulama listesinde görünür.**
CIV-157 dry-run'ında 153 kitap kontrol maddesi ve 5/34 hazır müdürlük vardır.
Bu hazırlık sayısı yükleme şartı değildir; CLI `validation` listesi farklı
ayrıntı düzeyinde olabilir. İşletme'nin beş faaliyet kodu uyuşmazlığı raporlanır,
ad benzerliğiyle otomatik eşlenmez. Kaynak sayıları, boş/çizgi/sıfır ve inceleme
durumları korunur; doğrulama hatalı paketler taslak olarak kaydolur.

Her komut bloğu zsh dahil bir terminale **tek başına** yapıştırılabilir; kendi
Bash oturumunu açar. Bağlantıları komut satırına, sohbet/PR'a veya dosyaya
kopyalamayın; yalnız `/dev/tty` gizli istemine girin. Blok sonunda bağlantı
ortam değişkeni kaldırılır. Doğrudan havuzsuz hedefi sahibi kontrol eder;
uzak hedefte `sslmode=require` veya `verify-ca`/`verify-full`, isteğe bağlı
`channel_binding=require` kabul edilir; başka bağlantı parametresi kabul edilmez.
Kurum tek olmalı; aktör etkin Strateji/yönetici olmalıdır.

## 1. Kaynağı ve araç sürümünü kontrol edin

Bu blok veritabanına bağlanmaz. Depoda tam bir Alembic başı bulunmalı ve
operatör aracının sabitiyle eşleşmelidir. Yeni migration varsa önce sorumluya
bildirin; sabiti elle değiştirerek devam etmeyin.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
python - <<'PY'
from alembic.config import Config
from alembic.script import ScriptDirectory
from scripts.first_load_live import BOOK, BOOK_SHA256, HEAD, verify_book
assert ScriptDirectory.from_config(Config('alembic.ini')).get_heads() == [HEAD] == ['c086a1b2c3d4']
verify_book(BOOK)
print('Şema:', HEAD)
print('Kitap:', BOOK.name)
print('SHA256:', BOOK_SHA256)
PY
BASH
```

## 2. Önce taze doğrulanmış yedekle Actions provası

Actions → **CIV-058 verified backup rehearsal** → Run workflow; yukarıdaki
onaylı değişiklikleri içeren dalı seçin. Kaynak olarak varsayılan daldaki
(feature/authorization-workflow-phase5) yeşil
**Daily verified database backup** çalışmasının numarasını girin. Kaynak yedek
48 saatten yeni olmalıdır; daha eskiyse sahibi [yedek prosedürüyle](../operations/db-backup.md)
yeni doğrulanmış yedek alır. İki onay alanına **2027 ON BASKI TASLAGINI SIL**
ve **cbbf9018302d** yazın. Kurum ve aktör alanları boşken prova yalnız kopyadan
tek kurum ve mevcut etkin Strateji/yönetici seçer; kullanıcı oluşturmaz veya
etkinleştirmez. Kullanılan sayısal kimlikler Summary'de görünür. Canlı komutlarda
kimlikleri sahibi ayrıca açıkça girer.

Workflow mevcut doğrulanmış şifreli artifact'i indirir, yalnız geçici yerel
PostgreSQL 18'e geri yükler; canlı veritabanı bağlantısı almaz ve migrasyon
çalıştırmaz. Her uygulamadan önce geçici hedefin gerçek yedeği alınır ve başka
boş yerel veritabanında satır/sıra/sayım/şema karşılaştırması yapılır. Bu hedef
yedekleri 60 dakikadan yeni olmalıdır. Kaynak artifact tarihi değiştirilmez.

Summary'de **PASS**, bütün aşama sayımları, temizleme planında **93 personel/SGK
maliyet satırı**, yüklemede **34/64/263/291/1340**, hiçbir başarısız/atlanan
müdürlük ve son planda bütün sayımların 0 olduğunu kontrol edin. Doğrulama
bulguları sayım özetinde kalır. Eksik aşama veya FAIL varsa canlı adıma geçmeyin.
PR açıklaması üzerinden prova başlatma yolu yoktur; yalnız elle Actions çalıştırılır.
Yedek/kopyalar iş sonunda silinir; veri satırları veya bağlantılar rapora alınmaz.

Sorumlu aynı provayı gerekirse kendi bilgisayarında da yalnız yerel PostgreSQL
18 ve `pg_dump`/`pg_restore` 18 ile çalıştırabilir. Girdi `.dump` ve yanındaki
manifesttir; şifreli artifact'i önce [yedek kılavuzuna](../operations/db-backup.md)
göre erişimi kısıtlı klasörde çözün. Bu ek yerel prova Actions PASS kaydının yerini almaz.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Doğrulanmış kaynak yedeğin tam yolu: ' CIV158_DUMP </dev/tty
read -r -p 'Yedekteki kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Yedekteki etkin Strateji/yönetici numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Yalnız yerel PostgreSQL 18 test bağlantısı (gizli): ' CIVENSA_TEST_POSTGRES_URL </dev/tty
printf '\n'
export CIVENSA_TEST_POSTGRES_URL
trap 'unset CIVENSA_TEST_POSTGRES_URL' EXIT
python scripts/rehearse_clear_preprint_2027.py --backup "$CIV158_DUMP" \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" </dev/tty
BASH
```

İstemlere sırasıyla temizleme cümlesi ve kitap öneki yazılır. Son satır
`CIV-058 yerel prova: PASS`, sayım dosyası `civ058-rehearsal-counts.json`
olmalıdır. Bu rapor sayım/hash/zaman içerir; operasyon kaydına alınır.

## 3. Veri girişini durdurun ve yeni doğrulanmış yedek alın

Önce 2. adımın PASS kanıtını kaydedin. Sahibi kullanıcıların veri girişini
kapattığı pencereyi belirlesin; danışma kilidi normal kullanıcı oturumlarını
kapatmaz. İşlem tamamlanana kadar girişleri açmayın.

[db-backup.md](../operations/db-backup.md) uyarınca **Daily verified database backup**
→ Run workflow → main üzerinden **yeni** yedek alın. Yeşil çalışmanın doğru
canlı hedefe ait olduğunu sahibi doğrular; şifreli artifact'i erişimi kısıtlı,
depo dışındaki klasöre indirip kılavuzdaki şekilde çözün. Düz `.dump` ve aynı
adlı `.manifest.json` yan yana kalmalıdır. Üretim yedek sırrını yükleyiciye vermeyin.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Yeni doğrulanmış .dump tam yolu: ' CIV158_DUMP </dev/tty
python - "$CIV158_DUMP" <<'PY'
from pathlib import Path
import sys
from scripts.first_load_live import verify_backup
try:
    verify_backup(Path(sys.argv[1]))
except Exception:
    print('DURDU: Yedek doğrulanamadı; yeni yeşil yedeği kontrol edin.')
    raise SystemExit(1)
print('Yedek dosya/manifest/şema/SHA256 ve 60 dakika kontrolü geçti.')
PY
BASH
```

Dosya biçimi, boyut, SHA256, şema ve manifestteki gerçek yedek zamanı denetlenir;
indirme zamanı yetmez. Kaynak hedefin doğruluğu sahibin sorumluluğundadır.

## 4. Ön baskı temizleme planı

D-131/D-135 yalnız 21 Eylül ön baskı envanterindeki **3–10** paketlerini kapsar.
Aşağıdaki plan 0 satır yazar; sıra sayaçlarını da değiştirmez.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" --clear-preprint
BASH
```

Her `Temizle` satırının müdürlük/paket kimliğini ve gösterge/değer/faaliyet/
maliyet/taslak teslim sayımını Actions PASS ile karşılaştırın. Özellikle
personel/SGK toplamı **93** ve müdürlük dağılımı birebir aynı olmalıdır.
Sentetik test sayımlarını gerçek yedek sayımları yerine kullanmayın.

Koruma koşulları değişmemiştir. Rapor kartı, ekonomik değer, yayın, taslak dışı
teslim, ilk yükleme işareti, paket/tarih envanteri farkı, kökeni kanıtlanamayan
2027 satırı veya paket sonrası içerik/müdürlük/personel düzenlemesi varsa araç
0 satır yazarak reddeder. Personel maliyetleri yalnız `personnel_sgk` olabilir;
yıl/tür/kategori/tutar/ham metin/durum çoklu kümesi arşiv planıyla tam eşleşmelidir.
Eski arşivin belgeli sayısal dönüşümleri salt okunur hesaplanır; migrasyon
çalıştırılmaz. Kapsam, bağlantı ve teslim olayında oluşturulma kökeni zorunludur;
eski paketlerde bu köken yoksa varlıkları reddedilir. Ret durumunda kaydı silip
korumayı aşmayın; sorumluya bildirin.

## 5. Ön baskı temizliğini uygulayın

Plan ve yedek doğrulandıktan sonra, girişler kapalıyken çalıştırın.
Yedek süresi dolduysa 3. adımdan yeni doğrulanmış yedek alın.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p '60 dakikadan yeni doğrulanmış .dump tam yolu: ' CIV158_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" --clear-preprint --apply --backup "$CIV158_DUMP" </dev/tty
BASH
```

İsteme **2027 ON BASKI TASLAGINI SIL** yazın. Yedek onaydan sonra ve ilk
silmeden hemen önce tekrar kontrol edilir. Tablo kilidi beklemesi 10 saniye
ile sınırlıdır. Bütün temizlik tek işlemde yapılır; hata olursa geri alınır.

Yalnız kökeni kanıtlanmış 2027 göstergeleri/değerleri, faaliyetleri/maliyetleri,
93 personel/SGK maliyeti ve taslak teslimleri temizlenir. Müdürlükler,
kullanıcılar, dönemler, 2026 verisi, program/alt program kataloğu, bütün denetim
ve paket satırları korunur. 3–10 paketlerinin yalnız durumu `superseded` olur;
içerik/snapshot/hash/tarih alanları korunur. Sürüm 2 / D-135
`preprint_2027_cleared` makbuzu silinen sayımları ve korunan hash'leri kaydeder.
Bu seçenek onaylı yüklemeyi geri almak için kullanılamaz.

## 6. Onaylı kitap yükleme planı

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR"
BASH
```

Beklenen `PLAN: Hedefe 0 satır yazıldı.` ve **34/64/263/291/1340**;
`skipped` ve `failed` boş olmalıdır. `created_departments` mevcut müdürlüklere
göre değişir. Her Eşleştir/Oluştur adını ve kimliğini sahibi doğrular.
İşletme ve İştirakler dahildir. Beklenmeyen eşleme/atlama veya sayımda durun.
Temizleme öncesinde alınan normal planın “2027 PP verisi zaten var” diye
reddedilmesi beklenir; temizleme sonrasında bu ret beklenmez.

## 7. Onaylı kitabı yükleyin

6. adımın planı onaylı ve girişler kapalı kalmalıdır. Aynı temizleme öncesi
yedek hâlâ 60 dakikadan yeniyse kullanılabilir; değilse yeni yedek alın.
Temizleme sonrası yedek seçilirse geri dönüş noktası artık temiz başlangıçtır.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p '60 dakikadan yeni doğrulanmış .dump tam yolu: ' CIV158_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" --apply --backup "$CIV158_DUMP" </dev/tty
BASH
```

İsteme **cbbf9018302d** yazın; tam SHA256 veya eski önek kabul edilmez.
Her müdürlük ayrı işlemde kaydolur; başarısız müdürlük işlemi geri alınır.
`UYGULAMA SONUCU` sayımları **34/64/263/291/1340**, `failed` ve `skipped` boş
olmalıdır. Kitap kontrol hataları `validation` içinde görünür ve yüklemeyi
durdurmaz; paketler taslak kalır. `needs_review` hücreleri korunur.

## 8. Son sıfır yazan plan ve sonuç kontrolü

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" --resume
BASH
```

Beklenen bütün `counts` alanları **0**, `skipped` **34**, bütün kararlar `skip`;
hiçbir satır veya sıra sayacı değişmez. Strateji ekranında 2027 kart/faaliyet/
ekonomik tabloyu, taslak durumlarını ve denetim geçmişini kontrol edin.
Boşlar sıfıra dönüşmemelidir. İlerleme ilk gerçek müdürlük düzenlemesine kadar
Başlamadı görünebilir; araç sahte düzenleme geçmişi üretmez.

Onaylı commit'i, yedek çalışmasını/artifact'ini, Actions PASS kaydını ve her
aşamanın sayımlarını operasyon kaydına alın. Beklenmeyen sonuçta girişleri
açmayın; doğru sonucu sahibi ve sorumlu doğruladıktan sonra girişleri açın.

## 9. Kesintiden sonra devam

Normal tekrar yükleme mevcut veri nedeniyle reddedilir. Önce 8. adımın
`--resume` planını alın: yalnız aynı kitap SHA256'sının uygulanmış paket ve
`first_load_department` izi olan müdürlükler, kullanıcı düzeltmeleri korunarak
atlanır. Kısmi yüklemede yalnız eksikler sayılır. Yabancı kayıt varsa durun.
Sahibi eksikleri onayladıktan ve **yeni** doğrulanmış yedek aldıktan sonra:

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV158_REPO </dev/tty
cd "$CIV158_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV158_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV158_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p '60 dakikadan yeni doğrulanmış .dump tam yolu: ' CIV158_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV158_ORG" --actor-id "$CIV158_ACTOR" --resume --apply --backup "$CIV158_DUMP" </dev/tty
BASH
```

Kitap onayı yine **cbbf9018302d**. Sonra 8. adımı tekrarlayın. Tam yüklemede
bu uygulama da 0 satır yazar. Kurtarma için temizleme seçeneğini kullanmayın.

## 10. Geri dönüş ve kanıtın sınırı

Temizleme işlemi başarısızsa bütünü geri alınır; yüklemede yalnız başarısız
müdürlük geri alınır. Kaydedilmiş temizleme/yüklemeyi topluca geri almak gerekirse
sahibi girişleri kapalı tutar ve [doğrulanmış yedek geri dönüş prosedürünü](../operations/db-backup.md)
sorumluyla uygular. Temizleme öncesi yedek ön baskıyı da, temizleme sonrası
yedek temiz başlangıcı geri getirir. Önce yeni boş yerel PostgreSQL 18'e
restore ile manifest/satır/sıra/şema doğrulanır. Canlı kurtarma hedefi ve
yedekten sonraki meşru değişikliklerin korunması ayrı yetkili operasyondur.
Bu araç canlı restore, migrasyon veya dağıtım yapmaz.

CIV-158 sentetik c086 provası ilk planın mevcut veriyi 0 yazmayla reddetmesini,
D-135 temizliğini, 2026/denetim/paket/katalog korunmasını, ikinci temizliğin
0 yazmasını, **34/64/263/291/1340** yüklemeyi ve son planın satır/sıra
parmak izlerinin değişmemesini kanıtlar. **Sentetik veri gerçek üretim yedeği
provası değildir.** Gerçek artifact ve bağlantı/rol, giriş molası ve canlı sonuç
ayrı operasyon sırasında doğrulanır; 2. adımın gerçek yedek PASS kaydı olmadan
canlı adıma geçilmez.

## 2026 yükleme

2026 için CIV-165 yükleyicisini, **c162a1b2c3d4** şemasını ve onaylı kitap
SHA256 öneki **1aaa0bb81c3c** kullanın. Sıra: **plan → doğrulanmış yedek →
2026 PP verified backup rehearsal → apply → resume plan**. Canlı adımları yalnız
sahibi yürütür; sorumlu provayı birleştirmeden sonra elle başlatır.

Önce `scripts/first_load_live.py --year 2026 --organization-id … --actor-id …`
ile salt okunur plan alın; bağlantıyı yukarıdaki gizli ortam değişkeni yöntemiyle
verin. Sonra yeni **Daily verified database backup** alın. Actions'ta
**2026 PP verified backup rehearsal** için varsayılan daldaki en yeni yeşil
çalışmanın `backup_run_id` numarasını ve `book_confirmation=1aaa0bb81c3c`
girin. Boş kurum/aktör alanları mevcut 2027 provasıyla aynı seçimi yapar.
Prova yalnız şifresi çözülmüş yedeğin geçici yerel PostgreSQL 18 kopyasını kullanır.

Summary'de **PASS**, **33 müdürlük / 105 kart / 226 gösterge**, sıfır ret ve
başarısız müdürlük, iki 2027 hash koruma kontrolü, kalıcı gösterge kimliği
atanan **0** ve devam planında **0 yazma / 33 atlanan** görülmelidir.
“**2026 dönemi dolu**” sonucu varsa mevcut sayımları inceleyin; `--resume` ile
ilk yükleme korumasını aşmayın. D-388 envanteriyle eşleşen onaylı pilot için
aşağıdaki **2026 pilot dönemini değiştirme** bölümünü izleyin; diğer dolu
dönemlerde durun.

PASS sonrasında sahibi veri girişini kapalı tutarak aynı 2026 komutuna
`--apply --backup …` ekler ve **1aaa0bb81c3c** onayını verir. Sonra `--apply`
olmadan `--resume` planı alır; bütün sayımlar 0, atlanan müdürlükler 33 olmalıdır.
Kaynak prova yedeği 48 saatten yeni olabilir; canlı uygulamanın doğrulanmış
yedeği ise **60 dakikadan yeni** olmalıdır. Prova ve onay 60 dakikalık pencereyi
sıkıştırıyorsa **iki yedek** alın: prova için birincisi, canlı uygulamadan hemen
önce ikincisi. Hash/sayım farkı veya herhangi bir FAIL varsa canlı uygulamaya
geçmeyin; sorumlu Summary'de belirtilen ilk başarısız kontrolü incelesin.

## Pilot öncesi envanter (CIV-221)

Salt okunur; hiçbir satır yazmaz, yedek gerekmez. Hedef şema **c219b1c2d3e4**.
Bağlantıyı yukarıdaki gizli terminal yöntemiyle yalnız
`CIVENSA_FIRST_LOAD_DATABASE_URL` üzerinden verin, sonra:
`python scripts/pilot_inventory.py`.
Çıktıda ad ve e-posta vardır: yalnız sorumluyla paylaşın, repoya veya
dosya paylaşımına koymayın. Sonda **Hedefe 0 satır yazıldı (salt okunur).**
görünmelidir.

## Pilot test hesaplarını kapatma (CIV-222)

CIV-221 envanteri deneme verisi göstermedi; yalnız 38 test hesabı kapatılır
(4 kayıtsız hesap silinir, 34 hesap pasife alınır; 1 ve 36 kalır). Hesap
listesi kodda sabittir; canlı farklıysa araç 0 yazmayla durur.
1. Salt okunur plan: `python scripts/pilot_accounts_cleanup.py --actor-id 1`.
2. GitHub Actions'ta **Daily verified database backup** çalıştırın (dal
   feature/authorization-workflow-phase5) ve yeşil bitmesini bekleyin.
3. Aynı komuta `--apply` ekleyin; istenen onay cümlesini yazın.
Pasife alma Kullanıcılar ekranından geri alınabilir.

## 2026 pilot dönemini değiştirme

CIV-172 / D-389 yalnız D-388'deki eski pilot envanterini kabul eder. Bu bölüm
canlı çalıştırma yetkisi vermez: sahibi ayrıca onayladıktan sonra, veri girişini
kapalı tutarak yürütür. Araç şema migrasyonu yapmaz; hedef **c162a1b2c3d4**.
Bağlantıyı önceki bölümlerdeki gizli terminal yöntemiyle yalnız
`CIVENSA_FIRST_LOAD_DATABASE_URL` üzerinden verin; komuta veya günlüğe yazmayın.

1. Önce salt okunur plan alın:
   `python scripts/clear_pilot_2026.py --organization-id … --actor-id …`.
   Beklenen: dönem **closed/verified**; 24 program, 40 alt program, 220 taslak
   gösterge, 1090 gösterge değeri, 174 faaliyet, 1119 faaliyet maliyeti,
   99 müdürlük maliyeti, 34 teslim (3 approved / 31 draft), 2 paket
   (1 applied / 1 preview), 136 ilişkili denetim kaydı. Diğer dönem tabloları
   sıfır olmalıdır. Fark varsa araç 0 yazmayla durur; sayımları sorumluya iletin.
2. Yeni **Daily verified database backup** alın. Önceki 2026 prova bölümündeki
   workflow'u `book_confirmation=1aaa0bb81c3c` ve isteğe bağlı
   `clear_confirmation=2026 PILOT DONEMINI SIL` ile çalıştırın. Bu açık onay,
   yalnız geçici kopyada temizleme planı → temizleme → 2026 yükleme planı →
   yükleme → devam planı zincirini açar. Boş bırakılırsa önceki davranış sürer;
   dolu 2026 dönemi reddedilir. **PASS**, temizleme sayımları, arşiv SHA256 ve
   zincirin başından sonuna değişmeyen 2027 hash kanıtını inceleyin.
3. Canlı temizleme için **60 dakikadan yeni**, doğrulanmış `.dump` ve manifest
   hazır olsun; gerekiyorsa provadan sonra yeniden yedek alın. Sahibi doğrudan
   etkileşimli terminalde çalıştırır (tee/grep veya boru kullanmayın):
   `python scripts/clear_pilot_2026.py --organization-id … --actor-id … --apply --backup …`.
   İstenen tam cümle: **2026 PILOT DONEMINI SIL**. Tek işlemde 2.802 pilot
   içerik satırı arşivlenip silinir; dönem kimliği, kullanıcılar, müdürlükler ve
   mevcut bütün denetim kayıtları korunur. Dönem **draft/verified** olur.
   `pilot_2026_cleared` denetim kaydında bütün silinen sütunları içeren gzip+base64
   JSON, açılmış JSON baytlarının SHA256'sı ve tablo sayımları saklanır.
   ÖZET yalnız sayımlar ve hash gösterir; arşivi açık günlüğe çıkarmayın.
4. Temizleme sonrasında **yeni doğrulanmış yedek** alın. Yukarıdaki **2026 yükleme**
   bölümünü izleyin: `--year 2026` planı → yeni yedeği kullanan yükleme uygulaması
   → `--resume` planı. Beklenen yükleme **33/105/226**, devam planı **0 yazma / 33 atlanan**.
   Temizleme komutunu yeniden uygulamayın; boş dönem artık pilot parmak iziyle
   eşleşmez. Kesinti veya ret varsa yeniden salt okunur plan alın ve sorumluya
   bildirin. Başarısız temizleme bütünüyle geri alınır; kaydedilmiş temizleme
   için 10. bölümdeki yedekten dönüş prosedürünü izleyin. Yükleme ayrı işlemdir;
   mevcut devam/kurtarma prosedürü geçerlidir.

## 2027 düzeltilmiş kitap ile değiştirme

CIV-214 komutu yalnız **2027 / dönem #2** içindir. Eski ONAYLI ilk yüklemesinin
bütün içerik satırları, özgün paket kimlikleri ve denetim geçmişi doğrulanır.
2026 ve diğer dönemler korunur. Şema **c197a1b2c3d4** olmalıdır; araç migrasyon
çalıştırmaz. Bu bölüm, önceki bölümlerdeki eski şema/2027 kitap onayının yerine
geçer: yeni ilk yüklemenin kaynağı **2027-performans-programi_SONN_duzeltilmis.idml**,
SHA256 **66d9d692bd9c324f6d4f492eca4d75721f28c80e248a971a2a331adf1170bf6f** (D-465).

**Katalog da değişir (D-466).** Düzeltilmiş kitapta 2027 kataloğu farklıdır:
Özel Kalem 0006 kaydı kalkar; Makine İkmal ve İşletme faaliyet kodları/adları
ile bir alt programın amaç/gerekçesi (110 → 119) değişir. Araç yalnız 2027'ye
ait program, alt program, resmî faaliyet ve sorumlu birim satırlarını aynı
işlemde siler ve düzeltilmiş kitaptan yeniden kurar. Plan her farkı
`Katalog farkı · …` satırlarıyla, `-` kaldırılacak ve `+` eklenecek olarak
Türkçe listeler. Başka bir dönemin satırı 2027 kataloğuna (ya da 2027 satırı
başka bir döneme) bağlıysa `ENGEL … dönemler arası bağ` yazar ve 0 satır yazar.

**Ön baskıdan kalan katalog (CIV-217).** Canlı 2027'de, D-135 ön baskı
temizliğinin bıraktığı eski programlar/alt programlar ve 30 Ekim yüklemesinin
üzerine yazmadığı eski alt program metinleri bulunabilir. Plan bunları ayrı
listeler: `Kullanılmayan eski katalog · …` (hiçbir kaydın bağlı olmadığı,
silinecek satırlar, `-` ile) ve `Eski alt program metni · …` (ONAYLI'dan farklı
Gerekçe/Amaç alanları, `~` ile; düzeltilmiş kitap metni yazılır). Bunlar engel
değildir ve aynı işlemde temizlenir; denetim kaydı ikisini de içerir. Buna
karşılık ONAYLI kitapta olmayan ama başka bir kaydın bağlı olduğu bir program/alt
program veya canlıda eksik bir ONAYLI katalog satırı `ENGEL` verir.
İçerik satırları alt programa adıyla bağlanır; eski metin bütün müdürlüklerde
imza farkı üretmez. 2026'ya ait katalog işlemleri, `period_id=1` PP değişikliği ve
kullanıcı hesabı işlemleri 2027 denetim engeli sayılmaz.

1. Veri girişini durdurun. Önceki bölümlerdeki gizli terminal yöntemiyle
   bağlantıyı yalnız `CIVENSA_FIRST_LOAD_DATABASE_URL` değişkenine girin.
   Bağlantıyı komut satırına, ekran görüntüsüne veya günlüğe yazmayın.
   Salt okunur plan alın:
   `python scripts/replace_approved_2027.py --organization-id … --actor-id …`.
   Plan bütün tablo sayımlarını **eski → yeni** ve her engeli listeler.
   `ENGEL` varsa uygulamaya geçmeyin. Müdürlük/tablo farkı, eşleştirme,
   yayın, teslim/inceleme, IC/FR veya başka yazma geçmişi otomatik olarak silinmez.
2. Engelsiz kaynakla yerel prova doğrulandıktan sonra
   [yedek prosedürüyle](../operations/db-backup.md) yeni doğrulanmış yedek alın.
   `.dump` ve yanındaki `.manifest.json` hazır olmalıdır. Manifestteki yedek zamanı
   **60 dakikadan yeni**, şema yukarıdaki başlıkla aynı olmalıdır.
3. Sahibin tek uygulama komutu, doğrudan etkileşimli terminalde:
   `python scripts/replace_approved_2027.py --organization-id … --actor-id … --apply --backup …`.
   Araç kilit altında planı tekrarlar, yedeği doğrular ve şu tam cümleyi ister:
   **2027 KITABINI DUZELTILMIS KITAPLA DEGISTIR**.
   Terminal yoksa veya cümle yanlışsa 0 satır yazılır. Onaydan sonra yedeğin
   güncelliği tekrar denetlenir.
4. Temizleme ve mevcut hizmetle düzeltilmiş kitabın yüklenmesi **tek işlemdir**.
   Kesinti/hata halinde bütün içerik değişiklikleri geri alınır. Başarı halinde
   `approved_book_2027_replaced` denetim kaydı iki kitap SHA256'sını, eski/yeni
   sayımları, kararı (D-466) ve kataloğun önce/sonra özetini içerir. Paketler taslak kalır; kaynak
   doğrulama bulguları kendiliğinden giderilmez. Başarıdan sonra aynı komutu
   yeniden uygulamayın; araç artık ONAYLI kökeniyle eşleşmediği için reddeder.
   Kesinti veya ret sonrasında salt okunur plan alın ve sorumluya bildirin.

Bu geliştirme sırasında canlı veritabanına bağlanılmadı, dağıtım yapılmadı.
Gerçek düzeltilmiş kitapla değiştirme provası yerel PostgreSQL'de yapılır
(`tests/test_replace_approved_2027.py`); canlı verinin ONAYLI ile eşitliğini
araç uygulama anında denetler.
