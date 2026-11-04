# Faaliyet Raporu → InDesign (CIV-179, AR-13)

Civensa, her faaliyet raporu için **InDesign metni** (`indesign.txt`, InDesign Tagged Text) üretir. Dosya, 2025 Faaliyet Raporu kitabının (`source/2025-faaliyet-raporu.idml`) kendi stil adlarını kullanır; InDesign'da yerleştirildiğinde kitabın stilleri uygulanır.

## Nereden indirilir
Rapor düzenleyicisi ve rapor listesi → **Dışa aktar** → **InDesign metni**. Sürüm ve birim onayı bağlantıları da vardır. Kaynak, erişim ve sürüm seçimi **Dizgi verisi (JSON)** ile aynıdır (`ar-typeset/1`); onaylı sürümde yalnız donmuş kopya kullanılır. Taslak indirmede ilk satır "TASLAK — bu metin onaylı rapor sürümü değildir." olur.

## InDesign'da kullanım
1. 2025 kitabını (veya ondan türetilmiş yeni yıl şablonunu) aç.
2. Bölümün metin çerçevesini seç → Dosya → Yerleştir → `.txt` dosyası, "İçe Aktarma Seçeneklerini Göster" işaretli.
3. Stil çakışmasında **Yayın Tanımı** seç.
4. Taşan metni Shift+tıklayarak akıt; sayfalar kendiliğinden eklenir.
5. Fotoğraflar, resim altları ve sütun genişlikleri tasarımcıda kalır.

## Stil eşlemesi
| İçerik | Stil |
| --- | --- |
| Müdürlük adı (birim bölümü), ana bölüm (idare) | `BOLUM BASLİK` |
| Alt başlık (ör. "Yetki, Görev ve Sorumluluklar") | `arabaslik stun 2` |
| Daha alt başlık | `Arabaslik stun` |
| Metin, madde (• ile) | `Metin` |
| Tablo başlığı "Tablo N: …" | `TABLO` |
| Tablo | tablo stili `TABLO 1`; başlık satırı hücre/paragraf `tablo başlık`, gövde `tablo yazı`, toplam satırı hücre `tablo sonuç` |

Birim bölümünde EK-1 kodları kitabın başlıklarına çevrilir: I.B → "Yetki, Görev ve Sorumluluklar", I.C → "Müdürlüğe İlişkin Bilgiler", II.B → "Müdürlüğün Amaç ve Hedefleri", III → "Faaliyetlere İlişkin Bilgi ve Değerlendirmeler". Başlıklardaki EK-1 numaraları ("A- ", "1- ") yazılmaz.

## Bilinçli sınırlar
- Boş ve "Uygulanamaz" bölümler, satırı olmayan tablolar yazılmaz. Tam kayıt JSON'dadır.
- Hesaplanmış özet tablolar (tür/birim toplamları) ve faaliyet maliyet alt tabloları bu sürümde yazılmaz.
- Gösterge tablosunda boş gerçekleşme "Kayıt yok", doğrulanmış sıfır "0" olarak yazılır.
- Serbest tabloların ilk satırı başlık satırı olarak biçimlenir (sunum kuralı; veri değişmez).
- Örnek çıktılar (sentetik veri): `tests/artifacts/civ179/`.
