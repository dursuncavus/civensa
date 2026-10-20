# Basılı PP 2027 — sahibin kontrollü ilk yükleme kılavuzu

D-88 / D-111: basılı kitap değiştirilmeden, taslak ve mevcut inceleme hücreleri
korunarak yüklenir. İşletme ve İştirakler Müdürlüğü Meclis verisi gelene kadar
atlanır. Beklenen sayım **33 müdürlük / 61 kart / 256 gösterge / 285 faaliyet /
1300 ekonomik değer**. Doğrulama hatası olan taslaklar da kaydedilir; kaynak
düzeltmesi bu araçta yapılmaz.

**CIV-058 / D-131 özel durumu:** normal ilk yükleme “2027 PP verisi zaten var”
diye durdu. Sahibin 20 Ekim 2026, 16:30 (Türkiye) salt okunur envanterinde dönem
2 aktif; 33 müdürlükte yalnız gösterge/faaliyet, teslimler taslak; paketler
3 önizleme, 4/5/7/8/9/10 uygulanmış, 6 geri alınmış; uygulamalar 21 Eylül tarihli.
Son uygulama sonrasında PP içerik düzenlemesi bulunmadığı bildirildi.
Araç bu beyanı yeterli saymaz; her çalışmada tekrar denetler.

**D-135 kapsam kararı:** doğrulanmış 20 Ekim 16:47 Türkiye saati yedeğinde
31 müdürlük için 93 müdürlük maliyet değeri bulundu. Yalnız personnel_sgk
kategorisi, ön baskı paketlerine izlenen müdürlükler ve arşiv planıyla tam eşleşen
personel değerleri temizlenebilir. Başka kategori, eksik/fazla/değişmiş hücre veya
son uygulamadan sonraki herhangi bir müdürlük denetim kaydı temizliği durdurur.

Bu görevde canlı veritabanı, Render, merge veya deploy çalıştırılmaz. Aşağıdaki
canlı adımları ayrı operasyon zamanında sahibi yürütür. Hedef release #50,
main 6b4d834, Alembic c048a1b2c3d4; farklıysa durun. Migrasyon veya Render
yeniden başlatması bu işlemin parçası değildir.

Her komut bloğu **zsh içinden tek başına** yapıştırılabilir: bash ile başlar,
gerekli bilgileri yeniden ister, önceki bloğun değişkenlerine dayanmaz.
İstemler /dev/tty üzerinden okunur; bağlantı komut geçmişine yazılmaz.
Terminal kaydı ve ekran paylaşımı kapalı olmalıdır. Bağlantıyı chat, dosya,
.env, komut argümanı, ekran görüntüsü veya PR'a koymayın.

## 1. Onaylı kodu hazırlayın

Python 3.12+, Git, Bash, yerel PostgreSQL **18** sunucusu ve PATH içinde
pg_dump / pg_restore 18 gerekir. Mac'te PostgreSQL 18 kurulumu/PATH seçimini
sorumlu bir kez tamamlasın. Kurum ve etkin Strateji/yönetici numaralarını
sorumludan alın. Kullanıcı veya kurum otomatik oluşturulmaz.

Depo zaten varsa tam yolunu girin; yoksa boş bir hedef klasör yolu girin.
Kirli çalışma ağacında bu blok durur. Sahibin onayladığı **CIV-058 PR başı
commit** numarasını kullanın; eski CIV-052 kodunda temizleme seçeneği yoktur.

```bash
bash <<'BASH'
set -euo pipefail
set +x
read -r -p 'Civensa depo klasörünün tam yolu (yoksa oluşturulur): ' CIV058_REPO </dev/tty
if [ ! -d "$CIV058_REPO" ]; then
  git clone https://github.com/dursuncavus/civensa.git "$CIV058_REPO"
fi
cd "$CIV058_REPO"
test -z "$(git status --porcelain)" || { echo 'DURDU: Kaydedilmemiş çalışma var.'; exit 1; }
git fetch origin task/civ-058-clear-preprint-2027
read -r -p 'Sahibin onayladığı CIV-058 tam commit numarası: ' CIV058_COMMIT </dev/tty
git switch --detach "$CIV058_COMMIT"
git rev-parse HEAD
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/first_load_live.py --help
BASH
```

Beklenen: gösterilen commit onaylananla aynı; yardımda --clear-preprint,
--apply, --backup ve --resume var. Kurulum hatasında durun.

## 2. Önce doğrulanmış üretim yedeğinde yerel prova yapın

CIV-050 yaklaşımı kullanılır: doğrulanmış yedeğin SHA256/boyutu kontrol edilir,
**yeni boş** geçici PostgreSQL 18 veritabanına geri yüklenir, bütün public tablo
sayımları ve Alembic sürümü manifestle karşılaştırılır. Migrasyon çalışmaz.
Kaynak yedek mevcut yeşil **Daily verified database backup** artifact'inden
alınır; iki dosyayı (.dump ve .manifest.json) depo dışında birlikte tutun.
CIV-050 gibi kaynak en çok 48 saatlik olabilir. Eski/eksikse ayrı yetkili
operasyonda yedek prosedürünü tamamlamadan ilerlemeyin.

**Sahibin yerel betiği** aşağıda hazırdır: yeni bir workflow'un main'e taşınmasına veya
üretim sırrına gerek duymaz; yedek GitHub'dan güvenilir sahibin bilgisayarına
indirilir. CIVENSA_TEST_POSTGRES_URL yalnız localhost/127.0.0.1/::1 ve sorgu
parametresiz yerel bağlantı kabul eder. Betik rastgele adlı boş veritabanlarını
kendisi oluşturur ve sonunda siler; girilen yönetim veritabanını silmez.
Yerel rol CREATE DATABASE yetkili olmalıdır. Canlı URL burada kabul edilmez.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Doğrulanmış üretim .dump dosyasının tam yolu: ' CIV058_DUMP </dev/tty
read -r -p 'Yedekteki kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Yedekteki etkin Strateji/yönetici numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Yalnız yerel PostgreSQL 18 test bağlantısı (gizli): ' CIVENSA_TEST_POSTGRES_URL </dev/tty
printf '\n'
export CIVENSA_TEST_POSTGRES_URL
trap 'unset CIVENSA_TEST_POSTGRES_URL' EXIT
python scripts/rehearse_clear_preprint_2027.py --backup "$CIV058_DUMP" \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" </dev/tty
BASH
```

Betik sırayla temizleme planı → temizleme uygulaması → ikinci temizleme
(0 yazma) → ilk yükleme planı → ilk yükleme uygulaması → --resume ile son
planı (0 yazma) çalıştırır. Planlarda bütün satırlar ve sıra sayaçları karşılaştırılır.
İki uygulamadan hemen önce geçici hedefin **yeni gerçek yedeği** alınır; başka
boş veritabanına geri yüklenip satır/sıra/sayım/şema doğrulanır. Bu hedef yedekleri
60 dakikadan yeni olmalıdır. Üretim artifact'inin tarihi değiştirilmez.

D-135 provasında temizleme planı **tam 93 department_cost_values** göstermelidir;
her müdürlüğün sayımı JSON'a yazılır. Fark varsa hiçbir uygulama başlamaz.
Kaynak olarak en güncel mevcut yeşil artifact'i seçin; kaynak en çok 48 saatlik,
her apply öncesi üretilen doğrulanmış geçici hedef yedeği 60 dakikadan yeni olmalıdır.

İki yazma için ayrı istemde sırasıyla **2027 ON BASKI TASLAGINI SIL** ve
**261cd17fd0be** yazın. Yalnız geçici yerel kopya değişir.
Beklenen son satır CIV-058 yerel prova: PASS; civ058-rehearsal-counts.json her
adımın sayımlarını içerir. Dosya yalnız sayım/hash/zaman içerir; veri satırı veya
bağlantı içermez. Sorumlu bu dosyayı operasyon kaydına almalıdır. FAIL veya
eksik adımda canlı işleme geçmeyin. Betik sonlandığında geçici dump'lar silinir;
asıl artifact'i erişimi kısıtlı yerde tutun. İşletim sistemi zorla kapanırsa
civensa_civ058_ önekli yarım kalmış yerel kopyayı sorumlu temizlesin.

### Üretim yedeğini bilgisayarınıza indirmeden Actions provası

**CIV-058 verified backup rehearsal**, CIV-050 gibi mevcut yeşil yedek artifact'ini
Actions içinde indirir, bütün işlemleri yalnız geçici PostgreSQL 18'de yürütür.
Canlı bağlantı/üretim sırrı almaz; yeni canlı yedek başlatmaz; migrasyon çalıştırmaz.
Yedek/kopyalar iş sonunda silinir; artifact yüklenmez. Sonuç yalnız işin Summary
bölümünde ve gizli bilgi içermeyen JSON sayım günlüğünde görünür.

Workflow main'e ulaştıktan sonra: Actions → **CIV-058 verified backup rehearsal**
→ Run workflow; onaylı dalı ve mevcut yeşil yedeğin çalışma numarasını seçin.
İki onay alanına **2027 ON BASKI TASLAGINI SIL** ve **261cd17fd0be** yazın.
Kurum/aktör alanları isteğe bağlıdır: boşken yalnız kopya için yedekteki tek kurum
ve mevcut etkin Strateji/yönetici hesabı seçilir, kullanılan sayısal kimlikler
Summary'de kaydedilir; kullanıcı oluşturulmaz/etkinleştirilmez. Canlı CLI'da
kimlikleri sahibi ayrıca açıkça girer.

Bu PR main'e birleşmeden prova için, yalnız aynı depodaki
task/civ-058-clear-preprint-2027 PR açıklamasına şu **görünür tek satırın eklenmesi**
manuel başlatmadır:

**CIV058_PROVA_BASLAT 2027 ON BASKI TASLAGINI SIL 261cd17fd0be**

Bu özel istek mevcut yeşil **39433446455** yedek çalışmasını kullanır.
Normal kod gönderimi veya bu satır zaten varken açıklama düzenlemek yedek
indirmez. Tekrar için satırı kaldırıp açıklamayı kaydedin; sonra yeniden ekleyin.
Fork PR'larında çalışmaz. Bu geçiş yolu merge/deploy gerektirmez.
Summary'deki PASS ve tüm aşama sayımlarını kontrol etmeden canlı adımlara geçmeyin.

## 3. Yazmadan normal ilk yükleme planını alın

Doğru Neon dal/veritabanı/rolü ve doğrudan havuzsuz adresi sahibi doğrular.
Uzak hedefte sslmode=require veya verify-ca/verify-full zorunludur;
channel_binding=require kabul edilir. Başka URL parametresi kabul edilmez.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR"
BASH
```

Normal boş hedefte PLAN: Hedefe 0 satır yazıldı. ve 33/61/256/285/1300
beklenir. Her Eşleştir/Oluştur numarasını ve adını sahibi kontrol eder;
beklenmeyen create veya skip durumunda durur. İşletme ve İştirakler'in Meclis
gerekçesiyle atlanması beklenir. Tam kitap 34/64/263/290/1340'tır.
Bu özel durumda “2027 PP verisi zaten var” beklenir; **yalnız D-131 onaylı
envanter** için aşağıdaki 4. adıma geçin. Diğer hatalarda durun.

## 4. D-131 için araya giren adım: ön baskı temizleme planı

Bu adım normal plan ile yeni yedek arasındadır. **Henüz silmez.**

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" --clear-preprint
BASH
```

Beklenen: PLAN: Hedefe 0 satır yazıldı.; her müdürlükte Temizle satırı,
paket numarası ve gösterge/değer/faaliyet/maliyet/teslim sayısı; ardından
JSON counts ve departments; ayrıca her müdürlüğün personel/SGK maliyet sayısı. Salt okunur işlem sıra sayaçlarını da değiştirmez.
Sahibi tüm müdürlükleri/sayımları yerel PASS provasıyla karşılaştırsın.

Araç şu durumların her birinde Türkçe gerekçeyle **0 satır yazıp durur**:

- Herhangi bir 2027 rapor kartı, ekonomik değer veya yayın; taslak dışı teslim;
  first_load_department işareti.
- Müdürlük maliyetlerinde personnel_sgk dışında kategori; pakete izlenmeyen
  müdürlük; arşiv personel planına göre eksik/fazla/değişmiş hücre.
  Importer'ın seen_personnel döngüsü gibi uygun ilk (year, kind) kaydı alınır;
  (year, value_kind, category, amount, raw_text, state) çoklu kümesi birebir eşleşmelidir.
  Boş ile sıfır ve ham metin/durum farkları korunur.
- Son uygulanan ön baskı paketinden sonra personnel_cost_update veya herhangi
  bir department denetim kaydı; başka PP içerik düzenlemesi, silinmiş kayda veya
  dönemi belirsiz kayda ilişkin düzenleme de durdurur.
- 3–10 dışı/değişmiş paket envanteri veya 21 Eylül dışı uygulama zamanı.
- Son ilgili paket planıyla birebir uyuşmayan gösterge/faaliyet/değer,
  inceleme geçmişi, kalıcı gösterge kimliği veya kökeni kanıtlanamayan başka
  2027 dönem satırı.

Onaylı eski paket planı/snapshot biçimi kapsam/katalog bağlantısı veya teslim
olayı için oluşturma kökeni taşımıyor. Böyle kayıtlar varsa “ön baskıda oluşturuldu”
diye varsayılmaz; oluşturulma izi olmadığı için temizleme reddedilir. Koruma gevşetilmez.
Yalnız login, doğrulanmış kullanıcı işlemleri, yedek dışa aktarma, dönem
etkinleştirme ve civ025_tracking_started gibi içerik dışı kayıtlar engel değildir.
2026'ya kesin bağlanabilen tekil gösterge/faaliyet gibi içerik denetimleri korunur;
müdürlük denetimleri, açıklamasında 2026 yazsa da D-135 gereği reddedilir.

## 5. Veri girişini durdurun; yeni doğrulanmış yedek alın

Kullanıcı girişine ara verilen pencereyi sahibi belirlesin. Danışma kilidi
yükleyicileri sıraya koyar; normal kullanıcı oturumlarını kapatmaz.
[db-backup.md](../operations/db-backup.md) prosedürüyle Actions →
**Daily verified database backup** → Run workflow → main; yeşil biten
çalıştırmanın artifact'ini indirin. Bu, sahibin ayrı canlı salt okunur yedek
operasyonudur. Üretim sırrını bu araca vermeyin. İndirilen .dump ile aynı adlı
.manifest.json depo dışında yan yana kalsın.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Yeni yeşil yedeğin .dump tam yolu: ' CIV058_DUMP </dev/tty
python - "$CIV058_DUMP" <<'PY'
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

Yükleyici dosya biçimi, boyut, SHA256, Alembic başlığı ve manifestteki asıl yedek
zamanını kontrol eder; indirme zamanı yetmez. Bu dosyanın doğru canlı hedefe ait
olduğunu yalnız sahibi yeşil çalıştırma ve Neon hedefi üzerinden doğrular.

## 6. Yalnız ön baskı temizliğini uygulayın; yeniden plan alın

Önce 2. adımın PASS sonucu, 4. adımın planı ve 5. adımın doğru hedef yedeği
sahibi tarafından kontrol edilmiş olmalıdır. Veri girişi kapalı kalır.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p '60 dakikadan yeni doğrulanmış .dump tam yolu: ' CIV058_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" --clear-preprint --apply --backup "$CIV058_DUMP" </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR"
BASH
```

Temizleme istemine **2027 ON BASKI TASLAGINI SIL** yazın. Eksik/yanlış onay,
eski yedek, yanlış şema/kurum/aktör veya kilit yazmayı engeller. Yedek onay
isteminden sonra ve kilit/köken kontrolleri bitip ilk silme başlamadan hemen önce
tekrar denetlenir; tablo kilidi beklemesi 10 saniye ile sınırlıdır.

Tek işlemde yalnız 2027 göstergelerinin değerleri/göstergeler, faaliyet maliyetleri/
faaliyetler, arşiv planına birebir eşlenen personel/SGK müdürlük maliyetleri ve
kökeni doğrulanmış taslak teslimler temizlenir. Denetim tüm
ret kontrollerini kilitler alındıktan sonra yapar. Hata olursa tüm temizlik geri
alınır. Temizlenecek kapsam/bağlantı/olay varsa oluşturulma kökeni de zorunludur;
bu onaylı eski paketlerde böyle bir köken bulunmadığından varlıkları reddedilir.

Müdürlükler, kullanıcılar, dönemler, 2026 verisi, program/alt program kataloğu,
tüm audit_log ve import_batches satırları tutulur. Paketlerin içerik/snapshot/
hash/tarih alanları değişmez; 3–10 paketlerinin durumu **superseded** olur.
Bu durum eski preview/apply/revert düğmelerinin artık kullanılmasını engeller.
Tek preprint_2027_cleared denetim kaydı sürüm 2 / D-135, personel/SGK dahil silinen sayımlar ve korunan
paket/katalog hash'lerini içerir.

Bloktaki ikinci komut artık normal ilk yükleme planını vermelidir:
**33/61/256/285/1300** ve yalnız İşletme ve İştirakler atlanmış.
Fark varsa durun; yazma çalıştırmayın. İkinci temizleme, yeni içerik yoksa
zaten temizlendi diyerek **0 satır** yazar; yeni içerik/ilk yükleme işareti
varsa reddeder. Bu seçenek basılı yüklemeyi geri almak için kullanılamaz.

## 7. Basılı kitabı sahibin onayıyla yükleyin

6. adımın normal planını kontrol edin. Yedek hâlâ 60 dakikadan yeniyse aynı
geri dönüş noktası kullanılabilir; değilse 5. adımdan yeni yeşil yedek alın.
Kullanıcı girişi hâlâ kapalı olmalıdır.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p '60 dakikadan yeni doğrulanmış .dump tam yolu: ' CIV058_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" --apply --backup "$CIV058_DUMP" </dev/tty
BASH
```

Kitap SHA256 onayına **261cd17fd0be** yazın. Tam SHA256:
261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e.
Onayı komut argümanına eklemeyin. Her müdürlük ayrı işlemde kaydolur; başarısız
müdürlük geri alınır. UYGULAMA SONUCU içinde counts beklenenle aynı, failed boş
olmalıdır. Taslak doğrulama hataları beklenebilir; validation içinde raporlanır.

## 8. Sonucu kontrol edin; sıfır yazan son planı alın

Strateji hesabında 2027 kart/faaliyet/ekonomik tablo ve denetim geçmişini
kontrol edin. Boşlar sıfıra dönüşmemeli; inceleme hücreleri korunmalı; paketler
taslak olmalıdır. İlerleme panosu ilk gerçek müdürlük düzenlemesine kadar
Başlamadı görünebilir; araç sahte düzenleme geçmişi üretmez.

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" --resume
BASH
```

Beklenen: counts tüm alanlarda 0, skipped 34; hiçbir satır/sıra değişmez.
Beklenmeyen sonuçta girişleri açmayın. Sonuç sayımlarını, onaylı commit'i,
yedek artifact'ini ve yerel prova JSON'unu operasyon kaydına alın.
Her blok bittiğinde gizli bağlantı değişkeni otomatik kaldırılır.

## 9. Kesinti sonrası devam

Normal ikinci yükleme mevcut veri yüzünden durur. --resume yalnız bu kitap
SHA256'sına ait applied paket ve first_load_department izi olan müdürlükleri
kullanıcı düzeltmeleriyle birlikte koruyup atlar. Önce 8. adımın planını alın;
kısmi yüklemede yalnız eksik müdürlükler sayılır. Beklenmeyen veride durun.
Sahibi eksikleri onayladıktan ve 5. adımla **yeni** yedek aldıktan sonra:

```bash
bash <<'BASH'
set -euo pipefail
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Civensa depo klasörünün tam yolu: ' CIV058_REPO </dev/tty
cd "$CIV058_REPO"
source .venv/bin/activate
read -r -p 'Kurum numarası: ' CIV058_ORG </dev/tty
read -r -p 'Etkin Strateji/yönetici kullanıcı numarası: ' CIV058_ACTOR </dev/tty
read -r -s -p 'Doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL </dev/tty
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT
read -r -p 'Yeni doğrulanmış .dump tam yolu: ' CIV058_DUMP </dev/tty
python scripts/first_load_live.py \
  --organization-id "$CIV058_ORG" --actor-id "$CIV058_ACTOR" --resume --apply --backup "$CIV058_DUMP" </dev/tty
BASH
```

Kitap SHA256 onayı yine zorunludur. Tam yüklemede bu da 0 satır yazar.
Temizleme seçeneğini kesinti kurtarması için kullanmayın.

## 10. Geri dönüş

Temizleme kendi tek işlemi başarısızsa tamamen geri alınır. Temizleme veya
yükleme kaydedildikten sonra genel geri dönüş gerekirse sahibi veri girişini
kapalı tutar ve [doğrulanmış yedek geri dönüş prosedürünü](../operations/db-backup.md)
sorumluyla uygular. Temizlemeden önceki yedek eski ön baskıyı da geri getirir;
temizleme sonrası yedek temiz başlangıcı geri getirir. Doğru geri dönüş noktasını
seçin. Önce yeni boş yerel PostgreSQL 18'e restore ve bütün manifest sayımları
doğrulanır; canlı kurtarma veritabanı seçimi ayrı yetkili operasyondur.
Burada otomatik canlı restore, migrasyon veya deploy yoktur. Yedekten sonraki
meşru değişikliklerin korunmasını sorumlu ayrıca planlar.

## Prova/test kanıtının sınırı

Disposable PostgreSQL 18 testleri planın bütün tablo/sıra değerlerini korumasını,
ret koşullarını, atomik geri almayı, 2026 ve korunan kayıtları, ikinci temizlemenin
0 yazmasını ve 33/61/256/285/1300 basılı yükleme zincirini doğrular.
D-135 regresyonları eşleşen 93 personel/SGK satırının kaldırılmasını, tek tutar/ham
metin/durum değişikliğini, eksik/fazla satırı, başka kategoriyi ve sonradan
personnel_cost_update/müdürlük denetimini 0 yazmayla reddetmeyi kapsar.
**Sentetik CI verisi gerçek üretim yedeği provası değildir.** Gerçek yedek
provasının kanıtı 2. adımda sahibin ürettiği PASS JSON'udur; bu kanıt olmadan
canlı işleme geçilmez. Canlı bağlantı/rol, doğru artifact, gerçek veri giriş
molası ve canlı sonuç sayımları yalnız ayrı operasyon sırasında doğrulanır.
