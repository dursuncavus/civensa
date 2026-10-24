# Şifreli, doğrulanmış günlük veritabanı yedeği

`Daily verified database backup`, `main` dalında her gün **00:30 UTC
(03:30 İstanbul)** çalışır; Actions üzerinden elle de başlatılabilir. Bu belge
CIV-092 değişikliğinin birleştirilmesinden sonraki davranışı anlatır. Bu görevde
canlı veritabanına bağlanılmaz ve gerçek yedek çalıştırılmaz.

PostgreSQL 18 `pg_dump -Fc`, salt okunur tek snapshot üzerinden yedek alır.
Manifest zaman, dosya adı/boyutu, SHA256, araç sürümü, Alembic sürümleri ve
public tablo sayımlarını içerir. Geçici PostgreSQL 18 kopyasına restore edilip
sayım ve sürümler eşleşmeden yükleme yapılamaz.

Doğrulanan dump **ve manifest**, age **1.2.1** ile `BACKUP_AGE_RECIPIENT`
alıcısına ayrı ayrı şifrelenir. İndirme arşivinin sabit SHA256 değeri
[setup-age](../../.github/actions/setup-age/action.yml) içinde doğrulanır.
Artifact yalnız `*.dump.age` ve `*.manifest.json.age` içerir; şifresiz dosya,
fazladan dosya, sembolik bağlantı veya age başlığı taşımayan dosya reddedilir.
Alıcı eksik/geçersizse veritabanı adımından önce işlem durur. Yedekleme işi özel
anahtarı almaz. Runner üzerindeki geçici şifresiz ve şifreli kopyalar iş sonunda
başarısızlık durumunda da temizlenir.

`civensa-db-backup-YYYYMMDD-HHMMZ` artifact saklama süresi **30 gün**dür;
şifreli verinin erişim süresini ve depolama maliyetini sınırlar. Bu ayar mevcut
90 günlük şifresiz artifact'leri değiştirmez veya silmez. Bunlar depo sahibi
tarafından ayrıca ele alınmadan depo açık yayına hazır sayılmaz.

## Sahibin yerel anahtar kurulumu

Bu komutlar sahibin güvendiği **yerel bilgisayarında**, `set -x` kapalıyken
çalıştırılır. `age`, `age-keygen` ve yetkili `gh` kurulu olmalıdır. Özel anahtar
hiçbir zaman sohbet, PR, terminal çıktısı, CI logu veya depo dosyasına yazılmaz.
Komutlar mevcut anahtarın üzerine yazmayı reddeder.

```bash
set -euo pipefail
set +x
umask 077
civensa_key_dir="$HOME/.config/civensa/backup-age"
install -d -m 700 "$civensa_key_dir"
age-keygen -o "$civensa_key_dir/identity.txt" 2>"$civensa_key_dir/keygen.log"
age-keygen -y "$civensa_key_dir/identity.txt" >"$civensa_key_dir/recipient.txt"
gh secret set BACKUP_AGE_RECIPIENT --repo dursuncavus/civensa <"$civensa_key_dir/recipient.txt"
gh secret set BACKUP_AGE_IDENTITY --repo dursuncavus/civensa <"$civensa_key_dir/identity.txt"
```

`keygen.log` yalnız age-keygen'in genel alıcı bilgisini tutar; `identity.txt`
özel anahtardır. Dosyayı şifreli, erişimi sınırlı bir kurtarma kasasında ayrıca
saklayın; anahtar kaybolursa bu yedekler çözülemez. Anahtar değiştirirken eski
30 günlük şifreli yedekleri açacak eski anahtarı da güvenli saklayın.
`BACKUP_AGE_RECIPIENT` ve `BACKUP_AGE_IDENTITY` bu uygulamada depo **Actions
secret** olarak kullanılır. Mevcut `NEON_BACKUP_DATABASE_URL` secret'ı ayrı kalır;
`postgresql://` doğrudan/non-pooled URL ve `sslmode=require` gerektirir. Bu PR
secret oluşturmaz/değiştirmez.

## İndirme ve yalnız yerel kopyaya geri yükleme

Başarılı şifreli yedek çalışmasının artifact'ini güvenli bir yerel klasöre alın:

```bash
umask 077
gh run download RUN_ID --repo dursuncavus/civensa \
  --name civensa-db-backup-YYYYMMDD-HHMMZ --dir /guvenli/yedek/sifreli
export BACKUP_AGE_IDENTITY_FILE="$HOME/.config/civensa/backup-age/identity.txt"
python -m ops.backup_crypto decrypt /guvenli/yedek/sifreli /guvenli/yedek/cozulmus
```

Hedef klasör önceden bulunmamalıdır. Dosya çifti ve şifre doğrulaması başarısızsa
kısmi çözülmüş kopya kaldırılır. Başarı halinde yerel dump'ın boyutu ve SHA256
özeti çözülmüş manifest ile karşılaştırılmalıdır. Sonra PostgreSQL 18 araçlarıyla
**yeni, boş ve yerel** veritabanına geri yükleyin; canlı bağlantı kullanmayın:

```bash
createdb -h localhost -U postgres civensa_restore
pg_restore -h localhost -U postgres -d civensa_restore \
  --exit-on-error --single-transaction --no-owner --no-privileges \
  /guvenli/yedek/cozulmus/civensa-neon-YYYYMMDD-HHMMZ.dump
psql -h localhost -U postgres -d civensa_restore \
  -c 'SELECT version_num FROM public.alembic_version ORDER BY version_num;'
```

Her manifest tablosu için `SELECT count(*) FROM public."table_name";` sonucunu
`public_table_row_counts` ile karşılaştırın. Gerekli eklentilerin yerelde de
bulunması gerekir. Parola istemi veya yerel `.pgpass` kullanın. Şifresiz yerel
kopyaları yalnız gerektiği sürece erişimi sınırlı olarak saklayın.

## Provalar ve PR güvenliği

`preprint-backup-rehearsal.yml` ve `release-rehearsal.yml` yalnız
`workflow_dispatch` ile çalışır. Özel anahtar yalnız bu işlerdeki restore adımına
verilir; şifre çözmeden sonra ortamdan çıkarılır. Eski PR açıklamasıyla gerçek
yedeği indirme yolu kaldırılmıştır. `ops/preprint_rehearsal.py` ve
`ops/release_rehearsal.py` de elle başlatılmayan özel yedek provalarını reddeder.
Eski şifresiz Actions artifact'leri otomatik restore için kabul edilmez; yeni,
şifreli bir yedek gerekir.

Yerel preprint temizleme provası `scripts/rehearse_clear_preprint_2027.py
--backup /guvenli/yedek/sifreli/AD.dump.age ...` ile aynı çözme sınırını kullanır;
`BACKUP_AGE_IDENTITY_FILE` dosyasını yerel olarak seçin. Eşleşen şifreli manifest
aynı klasörde olmalıdır. Geçici klonların taze, yerel `.dump` doğrulama yolu da
korunur; bu dosyalar artifact olarak yüklenmez.

`clear-preprint.yml` PR işi yalnız sentetik veriyi kullanır. `age-keygen` her
çalışmada geçici test anahtarı üretir; bu anahtar veya sentetik dump yüklenmez.
Şifreleme → çözme → geçici PostgreSQL 18 restore zinciri SHA256, satır değerleri,
null değerler, tablo sayımları ve Alembic sürümüyle doğrulanır. Secret içermeyen
`security.yml` PR işi gerçek artifact yükleme desenini, alıcı olmadan kapanmayı,
bozuk şifreli dosya/yanlış anahtar reddini ve PR işlerinin secret almamasını sınar.

`security.yml` içindeki `full-history` yalnız elle başlatılır; `fetch-depth: 0`
ve `--log-opts="--all --full-history"` kullanır. `--redact=100` ile yalnız
redakte JSON raporu, 7 gün süreyle yükler. Bulgu varsa işi başarısız yapar;
rapordaki yollar ve commit kimlikleri de operasyonel bilgi sayılır.

Owner birleştirme ve secret kurulumu sonrasında yeni bir yedeği ve elle restore
provasını ayrıca doğrulamalıdır. Günlük yedek bir günlük kurtarma noktasıdır;
sürekli kurtarma değildir. Eksik secret, TLS/bağlantı hatası, yetki, restore,
sayım/sürüm veya şifreleme hatası işi durdurur. Ham bağlantı/age hataları loglara
basılmaz. Neon sürümü 18'i aşarsa istemci ve restore imajı birlikte yükseltilmelidir.
