# Basılı PP 2027 — sahibin kontrollü ilk yükleme kılavuzu

Bu kılavuz komutları hazırlamak içindir. CIV-052 kapsamında canlı veritabanında
veya Render'da hiçbir komut çalıştırılmadı. Canlı uygulama yalnız proje sahibinin
onayladığı zamanda, güvenilir kendi bilgisayarında yapılır. Komutlar **Bash** içindir.

D-88 / D-111: basılı kitap değişmeden yüklenir. Paketler `draft` (taslak), kaynakta
inceleme gerektiren hücreler mevcut `needs_review` durumundadır. Müdürlük doğrulama
hataları raporlanır; tutarlar, boş hücreler ve kurallar değiştirilmez. D-109 uyarınca
kurum özetlerinin BOOK / CHECK / UNKNOWN bulguları veri değildir ve engel değildir.
İşletme ve İştirakler Müdürlüğü Meclis verisi gelene kadar **yüklenmez**.

## 1. Sorumlu ile hazırlığı tamamlayın

Proje sahibinin onayladığı **CIV-052 PR commit** numarasını, kurum numarasını ve
etkin Strateji/yönetici kullanıcı numarasını sorumludan alın. Bu kullanıcı denetim
kaydında yüklemeyi yapan kişidir. Bu numaralar gizli bağlantı değildir. Kullanıcı
hesabı veya kurum otomatik oluşturulmaz. Hedefte tek kurum olmalıdır.

Canlı için beklenen mevcut sürüm release #50 (`main` `6b4d834`), Alembic başlığı
`c048a1b2c3d4` olmalıdır. Bu yükleme bir yayın veya migrasyon işlemi değildir.
Sürüm farklıysa durun; [Render işletim belgesindeki](../operations/render.md)
başlatmanın migrasyon çalıştırabileceği bilgisini dikkate alarak sorumluya bildirin.
Bu işlem için Render ayarı değiştirmeyin, uygulamayı yeniden yayımlamayın.

Yükleme boyunca kullanıcıların veri girişine ara vereceği pencereyi önceden
belirleyin; yedekten sonra yeni düzeltme/gönderim yapılmamalıdır. İkinci bir yükleyici
aynı anda çalışamaz; bu koruma normal kullanıcı oturumlarını kapatmaz.

## 2. Onaylı kodu kendi bilgisayarınızda açın

Python 3.12+, Git, Bash ve PostgreSQL 18 `pg_restore`/`psql` araçları kurulu olmalıdır.
Terminalde deponun kök klasörüne geçin. İlk kez kuruluyorsa:

```bash
git clone https://github.com/dursuncavus/civensa.git
cd civensa
```

Mevcut depo kullanılıyorsa önce `cd civensa` ile aynı klasöre geçin; kaydedilmemiş
çalışmanız varsa sorumluya danışmadan dal değiştirmeyin.

```bash
git status --short
git fetch origin task/civ-052-live-first-load
read -r -p 'Sahibin onayladığı CIV-052 commit numarası: ' CIV052_COMMIT
git switch --detach "$CIV052_COMMIT"
git rev-parse HEAD
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/first_load_live.py --help
```

Beklenen: `git status --short` boş; commit numarası onaylananla aynı; yardımda
`--apply`, `--backup`, `--resume` görünür. Kurulum hatasında durun. Burada hiçbir
veritabanı bağlantısı veya migrasyon çalışmaz.

## 3. Bağlantıyı yalnız gizli istemde girin

Neon'da hedef canlı dal/veritabanı/rolü ve **doğrudan, havuzsuz** bağlantıyı doğrulayın.
Bağlantı `sslmode=require` veya daha güçlü TLS doğrulaması içermelidir. Neon Console'un
eklediği `channel_binding=require` kabul edilir; bu parametrenin başka değeri veya
başka ek bağlantı parametresi kabul edilmez. Bağlantıyı
chat, dosya, `.env`, komut satırı, ekran görüntüsü veya PR'a yapıştırmayın. Terminal
kaydını ve kabuk izlemeyi kapatın. Aşağıdaki gizli istem yazdığınızı göstermez ve
bağlantıyı komut geçmişine kaydetmez:

```bash
set +x
unset DATABASE_URL MIGRATION_DATABASE_URL
read -r -s -p 'Canlı doğrudan PostgreSQL bağlantısı (gizli): ' CIVENSA_FIRST_LOAD_DATABASE_URL
printf '\n'
export CIVENSA_FIRST_LOAD_DATABASE_URL
read -r -p 'Kurum numarası: ' CIV052_ORG_ID
read -r -p 'Yükleyen Strateji/yönetici kullanıcı numarası: ' CIV052_ACTOR_ID
```

Beklenen: gizli istemde bağlantı görünmez. Yükleyici hedefi yalnız
`CIVENSA_FIRST_LOAD_DATABASE_URL` değişkeninden alır; `DATABASE_URL` veya
`MIGRATION_DATABASE_URL` hedef olarak kullanılmaz. URL hiçbir çıktıda gösterilmez.

## 4. Yazmadan plan alın

```bash
python scripts/first_load_live.py \
  --organization-id "$CIV052_ORG_ID" --actor-id "$CIV052_ACTOR_ID"
```

Beklenen: `PLAN: Hedefe 0 satır yazıldı.`, her kaynak müdürlük için kısa bir Türkçe
işlem satırı ve ardından JSON çıktısı. `departments` listesinde her müdürlük için:

- `match`: mevcut müdürlüğün `department_id` numarası ve `name` adı; satır `Eşleştir:` ile başlar.
- `create`: oluşturulacak müdürlüğün `name` adı; satır `Oluştur:` ile başlar.
- `skip`: atlama gerekçesi `reason`; satır `Atla:` ile başlar.

Sahibi her `match` numarasını/adını ve her `create` kaydını tek tek kontrol etmelidir.
Her `create` gerçekten **yeni bir müdürlük** olmalıdır; sistemde adı değiştirilmiş
mevcut bir müdürlük için yeni kayıt oluşturmayın. **Beklenmeyen her `create` veya
`skip` = DURUN**; sorumlu eşleşmeyi doğrulamadan uygulamayın. İşletme ve İştirakler'in
Meclis verisi gerekçesiyle atlanması beklenir. Uygulama çıktısı da `departments`
listesini içerir; hizmetin reddettiği müdürlük `skip` ve gerekçesiyle gösterilir.

JSON içindeki `counts` sayımları:

| Alan | Beklenen |
| --- | ---: |
| departments | 33 |
| cards | 61 |
| indicators | 256 |
| activities | 285 |
| economic_values | 1300 |

Tam basılı kitap **34 / 64 / 263 / 290 / 1340** içerir. Atlanan İşletme ve İştirakler
**1 / 3 / 7 / 5 / 40** çıkarılır. `created_departments` hedefte mevcut müdürlüklere
göre 0–33 arasında değişir; mevcut doğru eşleşmeler yeniden oluşturulmaz.
`skipped` listesinde İşletme ve İştirakler ve Meclis verisi gerekçesi görünür.
Plan hedefte yalnız salt okunur işlem kullanır; sıra sayaçları bile ilerlemez.
Doğrulama hata ayrıntıları mevcut [basılı kitap provasında](dryrun-printed.md)
bulunur; bu plan hedefe deneme verisi yazıp geri almaz.

**Durun:** `DURDU`, farklı başlık, yetkisiz kullanıcı, yanlış kurum, açık/doğrulanmış
olmayan 2027 dönemi, belirsiz eşleşme, beklenmeyen atlama veya sayım farkı varsa
sorumluya bildirin. 2027 PP verisi zaten varsa normal çalıştırma 0 satır yazar ve
reddeder. Veri silerek veya üstüne yazarak engeli aşmayın; yalnız adım 8'deki
belgelenmiş devam koşulları uygunsa devam edin.

## 5. Kullanıcı girişini durdurun ve yeni doğrulanmış yedek alın

[Mevcut yedek prosedürünü](../operations/db-backup.md) uygulayın:
GitHub → Actions → **Daily verified database backup** → **Run workflow**, dal
**main**. Prosedürün gerektirdiği bağlantı sırrı önceden repository Actions secret
olarak sahibi tarafından güvenli ayarda girilmiş olmalıdır. Yükleyiciye bu sırrı
vermeyin ve yeni bir sır dosyası oluşturmayın.

İş **yeşil** tamamlanınca o çalıştırmanın `civensa-db-backup-YYYYMMDD-HHMMZ`
eserini indirin. ZIP'i erişimi kısıtlı, depo dışındaki bir klasöre açın. `.dump` ve
aynı adlı `.manifest.json` birlikte kalmalıdır. Yedek doğrulaması, ayrı PostgreSQL'e
geri yükleme ve tablo sayımı karşılaştırmasının geçtiğini yeşil çalıştırmada görün.
Bu adımın mevcut prosedürü yalnız canlıdan okur.

```bash
read -r -p 'İndirilen .dump dosyasının tam yolu: ' CIV052_BACKUP
```

Beklenen: yakın tarihli yeşil yedeğin iki dosyası yan yanadır. **Yedeğin alındığı
andan uygulamaya kadar 60 dakikadan az** geçmiş olmalıdır; indirme zamanı yetmez.
Yükleyici manifestteki yedek zamanını, SHA256, boyut, biçim ve Alembic başlığını
kontrol eder. Yerel dosya bu yedeğin canlı hedefe ait olduğunu ispatlayamaz; bunu
sahibi doğru yeşil çalıştırma/dal ve hedef üzerinden doğrular. Yedek başarısızsa,
eskiyse veya yanlış hedefe aitse durun ve yeni yedek alın.

## 6. Sahip onayıyla yalnız bir kez uygulayın

Önce adım 4'ün planını ve adım 5'in yedeğini sahibi kontrol etsin. Tüm kullanıcı
veri girişleri hâlâ duruyorken, sahibi uygulamaya onay verdikten sonra:

```bash
python scripts/first_load_live.py \
  --organization-id "$CIV052_ORG_ID" --actor-id "$CIV052_ACTOR_ID" \
  --apply --backup "$CIV052_BACKUP"
```

Beklenen istem:

```text
Yazma onayı: kitap SHA256 ilk 12 karakterini yazın (261cd17fd0be):
```

Kitabın tam SHA256 değeri
`261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e`.
Kontrol ettikten sonra **261cd17fd0be** yazıp Enter'a basın. Bu bağlantı sırrı
değildir. Hatalı/boş onay yazmayı engeller. Onayı komuta argüman olarak eklemeyin.

Her başarılı müdürlük için `Yüklendi: … · taslak · … doğrulama hatası` görünür.
Sonda `UYGULAMA SONUCU:` altında adım 4 sayımları, `skipped`, `failed` ve müdürlük
bazında `validation` içindeki Türkçe hatalar/uyarılar görünür. Doğrulama hatası
beklenir ve yüklemeyi engellemez. `failed` boşsa komut çıkış kodu 0'dır. Her
müdürlük kendi işlemiyle kaydedilir; hizmetin reddettiği müdürlüğün tüm kayıtları
birlikte geri alınır ve neden `failed` listesine yazılır (çıkış kodu 2).

## 7. Sonucu uygulamada kontrol edin

Sayımları ve atlanan müdürlüğü kontrol edin; Strateji hesabıyla 2027 dönemindeki
kartları, faaliyetleri, ekonomik tabloları ve denetim geçmişini açın. Paketler taslak
olmalı; boş değerler sıfıra dönüşmemeli; mevcut inceleme hücreleri incelemede kalmalı.
Kaynakta hata olan değerleri kitap dışında özel bir kopyada düzeltmeyin. Strateji
Civensa'nın mevcut yetkili ekranında gerekçesi/denetim iziyle düzeltir.

İlerleme panosunun mevcut davranışı korunur: müdürlük kullanıcısının ilk kayıtlı
veri girişinden önce `Başlamadı` görünebilir; gerçek bir müdürlük düzenlemesinden
sonra doğrulama hatası olan taslak `Eksikleri / hataları var` (`needs_attention`)
görünür. Bu yükleme sahte müdürlük düzenleme kaydı oluşturmaz.

Beklenmeyen sonuçta girişleri açmayın; sorumluya yalnız gizli bilgi içermeyen
sonuç raporunu iletin. Başarılı yükleme sayımlarını ve kullanılan yedek eserini
operasyon kaydına yazın. Bağlantıyı terminalden kaldırın:

```bash
unset CIVENSA_FIRST_LOAD_DATABASE_URL
```

## 8. Kesinti/hata sonrası kontrollü devam

Normal ikinci uygulama, 2027 verisini görüp **0 satır yazarak durur**. `--resume`
yalnız bu kitap SHA256'sıyla başarıyla uygulanmış `ImportBatch` ve aynı işlemde
kaydedilmiş `first_load_department` denetim izi olan müdürlükleri atlar. Sonraki
kullanıcı düzeltmeleri dahil hiçbir kayıtlarına dokunmaz. İz bulunmayan mevcut
2027 PP verisi varsa devam reddedilir. Başarısız ve dolayısıyla geri alınmış
müdürlükler tekrar denenebilir. İşletme ve İştirakler her durumda atlanır.

Bağlantı kaldırılmışsa adım 3'ün gizli istemini yeniden kullanın. Önce:

```bash
python scripts/first_load_live.py \
  --organization-id "$CIV052_ORG_ID" --actor-id "$CIV052_ACTOR_ID" --resume
```

Tamamlanmış bir yüklemede bütün sayaçlar 0, `skipped` 34 müdürlüktür. Kısmi yüklemede
sayımlar yalnız eksik müdürlükleri gösterir. Beklenmeyen mevcut veride durun.
Sahip eksikleri ve nedenleri onaylarsa, kullanıcı girişleri duruyorken **yeni yeşil
yedek** alın (adım 5); devamın geri dönüş noktası bu yeni yedektir. Sonra:

```bash
python scripts/first_load_live.py \
  --organization-id "$CIV052_ORG_ID" --actor-id "$CIV052_ACTOR_ID" \
  --resume --apply --backup "$CIV052_BACKUP"
unset CIVENSA_FIRST_LOAD_DATABASE_URL
```

SHA256 onayı yine zorunludur. Tam yükleme sonrasında bu komut da 0 satır yazar.
Bir müdürlükteki kaynak/hizmet hatasını çözmek için kitabı değiştirmeyin; sorumluya
bildirin. Veri silme, otomatik temizleme veya mevcut düzeltmelerin üstüne yazma
seçeneği yoktur.

## 9. Geri dönüş — yüklemeden önceki yedeği geri yükleyin

Bir müdürlük başarısız olduğunda yalnız onun işlemi otomatik geri alınır. Önceki
başarılı müdürlükler korunur. **Tüm ilk yüklemeyi** geri almak için yüklemeden hemen
önce alınan yeşil yedeği kullanmak gerekir; tek tek satır silmeyin ve içe aktarma
paketinin eski geri alma düğmesini bu operasyon için kullanmayın.

Sahibi geri dönüş kararı verirse kullanıcı girişleri kapalı kalır. Sorumlu
[db-backup.md](../operations/db-backup.md) uyarınca aynı `.dump` dosyasını önce
**yeni boş yerel veritabanına**, PostgreSQL 18 araçlarıyla geri yükler:

```bash
createdb -h localhost -U postgres civensa_first_load_restore
pg_restore -h localhost -U postgres -d civensa_first_load_restore \
  --exit-on-error --single-transaction --no-owner --no-privileges \
  "$CIV052_BACKUP"
psql -h localhost -U postgres -d civensa_first_load_restore \
  -c 'SELECT version_num FROM public.alembic_version ORDER BY version_num;'
```

Parola istenirse yalnız gizli parola istemine girilir. Beklenen:
`c048a1b2c3d4`; manifestteki **her** public tablonun satır sayısı geri yüklemede
aynı olmalıdır. Hata/sayım farkında durun. Daha sonra yetkili veritabanı sorumlusu,
sahip onayıyla, bu doğrulanmış yedeği **yeni boş Neon kurtarma veritabanına** geri
yükler; hedef bağlantısını yalnız gizli istem/ortam değişkeniyle verir. Proje sahibi
kurtarma veritabanını uygulamanın bağlantı hedefi olarak güvenli Render ayarından
seçtirir; önceki veritabanını korur. Bu canlı geri dönüş ayrı, sorumlu tarafından
yönetilen operasyondur; burada otomatik canlı restore veya silme komutu yoktur.
[Render belgesindeki](../operations/render.md) bağlantı, giriş ve sayım kontrollerini
tekrarlamadan kullanıcı girişini açmayın. Kod/şema bu yüklemede değişmediğinden
veri geri dönüşü için eski uygulama sürümüne geçilmez. Yedekten sonra yapılan
meşru kullanıcı değişiklikleri geri dönüşte kaybolabilir; bunları sorumlu ayrıca
korur ve hesaplar.

## Testlerin sınırı

CI yalnız disposable yerel PostgreSQL kullanır: planın tüm tablo/sıra sayaçlarını
koruması, kaynak/URL/onay/yedek/başlık/yetki korumaları, taslak ve inceleme hücreleri,
tekrarın 0 yazması, düzeltmeleri koruyan devam, tek müdürlük geri alması ve atlama
listesi doğrulanır. Canlı endpoint/rol yetkileri, sahibin onayı, seçilen yedeğin o
hedefe ait olması, veri girişine gerçekten ara verilmesi ve canlı son sayımlar
ancak sahip tarafından bu operasyon sırasında doğrulanabilir. Bu PR CI'da canlı
bağlantı veya sır kullanmaz.
