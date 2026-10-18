# CIV-046 · Faaliyet Raporu Word çıktısı

Birim ve idare faaliyet raporları, EK-1 bölüm tanımlarının sırası ve başlıklarıyla Word olarak indirilir. Tamamlanma görünümünde veya bölüm düzenleyicisinde **Word olarak indir** bağlantısını kullanın. Strateji tüm raporları, müdürlük kullanıcısı kendi birim raporunu indirebilir. İdare raporunun indirilmesi Stratejiye aittir.

Taslakların her sayfasında “TASLAK — onaylanmamış içerik”, eksik bölümlerde açıklama kutuları bulunur. Onaylı belgeler donmuş içerikten oluşturulur; altbilgide SHA-256 doğrulama kodunun ilk 16 karakteri ve sayfa numarası yer alır. Boş sayısal değer `—`, sıfır para tutarı `0,00` olarak gösterilir. Geniş tablolar yatay sayfaya alınır; tablo başlıkları sonraki sayfalarda yinelenir. Çok sütunlu bütçe verileri, tanımlayıcı sütunları tekrarlayan okunabilir tablolara ayrılır.

## Grafik tasarımcı için şablonu değiştirme

1. `app/templates_docx/faaliyet_raporu.docx` dosyasını Microsoft Word ile açın.
2. **Giriş → Stiller** bölmesini açın. İlgili stile sağ tıklayıp **Değiştir** seçeneğini kullanın.
3. Aşağıdaki stillerin yazı tipi, punto, renk, paragraf aralığı, kenarlık veya dolgu özelliklerini düzenleyin. Stillerin adlarını ve başlık düzeylerini koruyun.
4. **Düzen → Kenar Boşlukları** bölümünden A4 sayfanın kenar boşluklarını ayarlayabilirsiniz.
5. Dosyayı aynı konum ve adla `.docx` olarak kaydedin. Yeni indirmeler bu şablonu kullanır; Python kodunu değiştirmeniz gerekmez. Çalışan sunucunun kullandığı dosyanın güncellenmesi gerekir.

| Stil | Kullanım |
| --- | --- |
| Civensa Başlık 1–4 | EK-1 bölüm düzeyleri ve içindekiler girdileri |
| Civensa Gövde | Metinler ve tablo hücreleri |
| Civensa Madde | Gerçek Word madde işaretli listeleri |
| Civensa Tablo | Tablo kenarlıkları ve tablo biçimi |
| Civensa Tablo Başlık | Tablo başlık satırları ve tablo adları |
| Civensa Not | Eksik bilgi kutuları, açıklamalar, üstbilgi ve altbilgi |
| Civensa Kapak Başlık | Kapak ve içindekiler başlığı |

Oluşturucu doğrudan yazı tipi, punto veya renk uygulamaz. Şablondaki örnek gövde metni çıktıda yer almaz. Kapak ve bölüm içerikleri rapor payload'ından oluşturulur. Tablo genişliği şablonun sayfa alanına sığdırılır.

## İçindekiler ve onaylı kopyalar

İçindekiler gerçek Word alanıdır; başlık stillerine bağlanır ve açılışta güncelleme işareti taşır. Word güncelleme izni isterse izin verin. Elle güncellemek için **sağ tık → Alanı Güncelleştir** kullanın; gerekirse tüm tabloyu güncelleştirin. Sayfa numaraları da Word alanıdır.

Yeni donmuş kopyalarda kurum adı, yayın tanımına bağlı gösterge hedefleri, son gerçekleşme ve kaynakları, kaynak tablosu yerleşimi ve çözümlenmiş güvence metinleri payload içinde saklanır. DOCX oluşturucu veritabanına erişmez. Malî dosyaların payload'daki adı, özeti ve doğrulama kodu rapora alınır; PDF/XLSX dosyaları Word belgesine gömülmez.

CIV-046 öncesinde donmuş kopyalar değiştirilmez: o kopyada bulunmayan kurum adı veya ayrıntılı gösterge verileri canlı kayıtlardan tamamlanmaz. Eski kaynak tablolarına yalnız sabit bölüm eşlemesi eklenir; eski güvence değişkenleri mevcut doğrulanmış mevzuat metniyle çözümlenir. Yeni donmuş kopyaların güvence metni ayrıca anlık görüntüye dahildir.

## Örnek ve doğrulama

- [Örnek taslak](ornek-taslak.docx): 2027, Örnek Belediyesi / Fen İşleri Müdürlüğü. Kurum, kayıtlar ve imzalayan kurgusaldır; gerçek kişisel veri içermez.
- [Kapak görüntüsü](sayfa-01.png)
- [Yatay malî tablo görüntüsü](sayfa-mali.png)
- Örneği yeniden üretmek: `PYTHONPATH=. python tools/create_ar_docx_demo.py`.
- `tools/create_ar_docx_template.py` yalnız başlangıç şablonunu üretir. Tasarımcı değişikliklerinden sonra çalıştırılması tasarımı sıfırlar; normal kullanımda çalıştırmayın.

Yerel doğrulama PostgreSQL 18 üzerinde yapılır:

```sh
CIVENSA_TEST_POSTGRES_URL='<yalnız geçici yerel test veritabanı>' \
CIVENSA_CHROMIUM_PATH=/usr/bin/chromium \
python -m pytest -q --require-postgres \
  tests/test_activity_sections*.py tests/test_activity_financial*.py tests/test_assurance*.py
```

Test kapsamı: tanım sırası ve başlık düzeyleri, kurum/birim kapağı, Türkçe tutarlar ve boş/sıfır ayrımı, uygulanamaz gerekçesi, kaynaklar ve malî bölümler, güvence metinleri, donmuş içerik ve gösterge sonuçları, taslak/onaylı işaretler, sayfa alanları, yatay tablo ve yinelenen başlık, indirme yetkileri, şablon stilleri ve kod değiştirmeden yeniden biçimlendirme.

18 Ekim 2026 yerel sonucu: **105 test başarılı**, 1 mevcut Starlette/httpx kullanımdan kaldırma uyarısı. Sekiz yeni DOCX testi bu toplama dahildir. PostgreSQL sürümü 18.6; Alembic başlığı tek ve değişmedi: `c044a1b2c3d4`.

Örnek LibreOffice 25.2.3.2 ile 10 sayfalık PDF'e dönüştürüldü. İki görüntü bu dönüşümün 1. ve 5. sayfalarından alındı. On sayfanın tamamında taslak üstbilgisi ve sayfa sınırları kontrol edildi; kapak ve yatay malî tablo görsel olarak incelendi. PDF yalnız yerel doğrulama çıktısıdır; depoya eklenmez.

Microsoft Word bu Linux ortamında bulunmadığı için Word'ün onarım uyarısı davranışı burada doğrudan doğrulanamaz. Örnek python-docx ile açılır ve LibreOffice ile sayfalara dönüştürülerek görsel olarak kontrol edilir. CI sonucu, istek gereği push sonrasında beklenmez veya sorgulanmaz.
