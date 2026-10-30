# Onaylı 2027 PP — 16 Ekim kaynağına göre fark

Muhatap: proje sahibi ve Strateji. 2027 ilk yüklemesinin tek kaynağı onaylı IDML’dir (D-316). Bu rapor kaynak değerlerini ve yükleyici/doğrulama kurallarını değiştirmez.

Eski: `2027-performans-programi_16102026_duzeltilmis 2.idml`; SHA256 `261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e`.

Yeni: `2027-performans-programi_ONAYLI.idml`; SHA256 `cbbf9018302d0a1d33d1dde0c4a64a2418d12b55cc29d046205371018673bd71`.

Karşılaştırma, iki kaynağı da aynı basılı sayfa geometrisi filtresiyle ve ayrı geçici yerel PostgreSQL veritabanlarında gerçek servislerle çalıştırır. Eski rapor `docs/first-load/dryrun-printed.md` ve `dryrun-d3.md` değiştirilmez. Onaylı arşivdeki 240 tablonun 229’u basılı, 7’si pasteboard ve 4’ü yerleşimsizdir; yerleşimsiz dört tablo önceki okuyucu tarafından da yüklenmiyordu.

## Yeniden üretme

```sh
# CIVENSA_TEST_POSTGRES_URL: yerel, disposable PostgreSQL 16+; CREATE DATABASE yetkisi.
python scripts/first_load_dryrun.py tests/fixtures/first_load/source/2027-performans-programi_ONAYLI.idml --out docs/first-load/dryrun-onayli.md --compare-source 'tests/fixtures/first_load/source/2027-performans-programi_16102026_duzeltilmis 2.idml' --diff-out docs/first-load/onayli-fark.md
```

## Müdürlük sayımları

Her hücre eski → yeni. Ekonomik değer sayısı kategori kayıtlarını sayar; toplam satırları ayrıca denetlenir. YOK müdürlüğün kaynakta bulunmadığı anlamına gelir.

| Müdürlük | Kart | Gösterge | Faaliyet | Ekonomik değer | Kitap maddesi | Hazır |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 2 → 2 | 10 → 10 | 16 → 16 | 30 → 30 | 0 → 4 | Evet → Hayır |
| Araştırma ve Geliştirme Müdürlüğü | 1 → 1 | 4 → 4 | 8 → 8 | 30 → 30 | 0 → 1 | Evet → Hayır |
| Bilgi İşlem Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 40 → 40 | 2 → 5 | Hayır → Hayır |
| Destek Hizmetleri Müdürlüğü | 2 → 2 | 9 → 9 | 7 → 7 | 40 → 40 | 0 → 0 | Evet → Evet |
| Dış İlişkiler Müdürlüğü | 1 → 1 | 3 → 3 | 10 → 10 | 40 → 40 | 3 → 5 | Hayır → Hayır |
| Emlak İstimlak Müdürlüğü | 2 → 2 | 7 → 7 | 11 → 11 | 50 → 50 | 0 → 4 | Evet → Hayır |
| Etüd Proje Müdürlüğü | 2 → 2 | 6 → 6 | 12 → 12 | 30 → 30 | 0 → 0 | Evet → Evet |
| Fen İşleri Müdürlüğü | 3 → 3 | 15 → 15 | 9 → 9 | 50 → 50 | 2 → 3 | Hayır → Hayır |
| Gelirler Müdürlüğü | 1 → 1 | 3 → 3 | 9 → 9 | 40 → 40 | 0 → 2 | Evet → Hayır |
| Gençlik ve Spor İşleri Müdürlüğü | 2 → 2 | 10 → 10 | 10 → 10 | 40 → 40 | 3 → 4 | Hayır → Hayır |
| Halkla İlişkiler Müdürlüğü | 4 → 4 | 16 → 16 | 10 → 10 | 40 → 40 | 2 → 3 | Hayır → Hayır |
| Hukuk İşleri Müdürlüğü | 1 → 1 | 4 → 4 | 6 → 6 | 30 → 30 | 0 → 3 | Evet → Hayır |
| Kentsel Dönüşüm Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 30 → 30 | 0 → 1 | Evet → Hayır |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 5 → 5 | 24 → 24 | 17 → 17 | 30 → 30 | 3 → 47 | Hayır → Hayır |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 40 → 40 | 1 → 2 | Hayır → Hayır |
| Mali Hizmetler Müdürlüğü | 1 → 1 | 2 → 2 | 5 → 5 | 90 → 90 | 0 → 3 | Evet → Hayır |
| Park ve Bahçeler Müdürlüğü | 2 → 2 | 7 → 7 | 13 → 13 | 40 → 40 | 3 → 15 | Hayır → Hayır |
| Plan Proje Müdürlüğü | 1 → 1 | 5 → 5 | 1 → 1 | 30 → 30 | 0 → 1 | Evet → Hayır |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 1 → 1 | 5 → 5 | 3 → 3 | 40 → 40 | 1 → 2 | Hayır → Hayır |
| Ruhsat ve Denetim Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 30 → 30 | 1 → 2 | Hayır → Hayır |
| Sağlık İşleri Müdürlüğü | 4 → 4 | 11 → 11 | 10 → 10 | 50 → 50 | 6 → 3 | Hayır → Hayır |
| Sosyal Destek Müdürlüğü | 4 → 4 | 20 → 20 | 19 → 19 | 40 → 40 | 0 → 0 | Evet → Evet |
| Strateji Geliştirme Müdürlüğü | 1 → 1 | 5 → 5 | 8 → 8 | 30 → 30 | 1 → 1 | Hayır → Hayır |
| Tarımsal Hizmetler Müdürlüğü | 2 → 2 | 9 → 9 | 11 → 11 | 40 → 40 | 3 → 7 | Hayır → Hayır |
| Temizlik İşleri Müdürlüğü | 1 → 1 | 4 → 4 | 8 → 8 | 40 → 40 | 0 → 0 | Evet → Evet |
| Veteriner İşleri Müdürlüğü | 1 → 1 | 5 → 5 | 6 → 6 | 50 → 50 | 0 → 4 | Evet → Hayır |
| Yazı İşleri Müdürlüğü | 4 → 4 | 19 → 19 | 11 → 11 | 50 → 50 | 1 → 4 | Hayır → Hayır |
| Zabıta Müdürlüğü | 2 → 2 | 9 → 9 | 9 → 9 | 40 → 40 | 0 → 1 | Evet → Hayır |
| Çevre Koruma ve Kontrol Müdürlüğü | 1 → 1 | 3 → 3 | 3 → 3 | 30 → 30 | 0 → 1 | Evet → Hayır |
| Özel Kalem Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 6 | 40 → 40 | 2 → 3 | Hayır → Hayır |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | 1 → 1 | 3 → 3 | 5 → 5 | 30 → 30 | 0 → 0 | Evet → Evet |
| İmar ve Şehircilik Müdürlüğü | 2 → 2 | 7 → 7 | 13 → 13 | 30 → 30 | 0 → 1 | Evet → Hayır |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 2 → 2 | 6 → 6 | 10 → 10 | 40 → 40 | 1 → 2 | Hayır → Hayır |
| İşletme ve İştirakler Müdürlüğü | 3 → 3 | 7 → 7 | 5 → 5 | 40 → 40 | 6 → 19 | Hayır → Hayır |
| **Toplam** | **64 → 64** | **263 → 263** | **290 → 291** | **1340 → 1340** | **41 → 153** | **17 → 5** |

Müdürlük: 34 → 34; yeni: Yok; eksilen: Yok.

## Değişen bütün tutar / gösterge hücreleri

**279 değişen hücre**. Kapsam: bütün basılı IDML tabloları; kurum özetleri ve diğer sayısal tablolar dahildir. T numarası üretilen Word tablosudur. Basılmayan tablolar kapsam dışıdır. Fark = yeni − eski; BOŞ, çizgi, sıfır ve YOK ayrı tutulur. Ham değerler aynen korunur; yalnız fark Türkçe sayı biçimiyle yazılır. Ham biçim değişip sayısal değer aynı kalırsa fark 0’dır. Belirsiz/okunamayan veya eksik bir taraf varsa fark hesaplanmaz.

Tablolar müdürlük + tür + basılı sıra ile; kurum tabloları başlık türüyle; diğer tablolar sayfa + ilk başlık + sıra ile eşlenir. IDML kimlikleri dışa aktarmada yenilendiğinden eşleme anahtarı değildir. Aynı boyutlu tablolarda satır konumu korunur; eklenen satırlar etiket dizisiyle hizalanır. Sütunlar fiziksel sıradadır; satır/sütun konumu ve başlık birlikte kanıttır.

| Müdürlük / kapsam | Sayfa eski → yeni | Tablo eski → yeni | Satır / etiket | Sütun / etiket | Eski ham değer | Yeni ham değer | Fark |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c5 / 2027 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c6 / 2028 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c7 / 2029 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T70 / Ekonomik tablo → T70 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 6.554.522,21 | 5.091.250,40 | -1.463.271,81 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T70 / Ekonomik tablo → T70 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 6.554.522,21 | 5.091.250,40 | -1.463.271,81 |
| Araştırma ve Geliştirme Müdürlüğü | 195 → 195 | T134 / Ekonomik tablo → T134 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 813.893,90 | 832.400,90 | 18.507,00 |
| Araştırma ve Geliştirme Müdürlüğü | 195 → 195 | T134 / Ekonomik tablo → T134 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 813.893,90 | 832.400,90 | 18.507,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c4 / 2027 Bütçe | 235.000.000,00 | 236.000.000,00 | 1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c4 / 2027 Bütçe | 282.812.848,00 | 283.812.848,00 | 1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c4 / 2027 Bütçe | 282.812.848,00 | 283.812.848,00 | 1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 480.825.142,00 | 454.155.142,00 | -26.670.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c6 / 2029 Tahmin | 810.640.269,00 | 777.302.769,00 | -33.337.500,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r32 → r32 / Toplam | c5 / 2027 Bütçe | 5.039.548,00 | 4.039.548,00 | -1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c5 / 2027 Bütçe | 5.039.548,00 | 4.039.548,00 | -1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r36 → r36 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 6.514.548,00 | 5.514.548,00 | -1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T120 / Ekonomik tablo → T120 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 6.414.231,00 | 7.414.231,00 | 1.000.000,00 |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c5 / 2027 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c6 / 2028 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c7 / 2029 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T30 / Ekonomik tablo → T30 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 113.787.163,62 | 113.352.771,64 | -434.391,98 |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T30 / Ekonomik tablo → T30 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 113.787.163,62 | 113.352.771,64 | -434.391,98 |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Fen İşleri Müdürlüğü | 118 → 118 | T37 / Faaliyet maliyetleri → T37 / Faaliyet maliyetleri | r29 → r29 / Toplam | c7 / 2029 Tahmin | 2.592.658.713,00 | 2.592.904.546,00 | 245.833,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T37 / Faaliyet maliyetleri → T37 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c7 / 2029 Tahmin | 2.592.658.713,00 | 2.592.904.546,00 | 245.833,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T38 / Ekonomik tablo → T38 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 949.340.000,00 | 950.000.000,00 | 660.000,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T38 / Ekonomik tablo → T38 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 949.340.000,00 | 950.000.000,00 | 660.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 132.225.430,00 | 130.725.430,0 | -1.500.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 52.551.283,13 | 52.551.283,3 | 0,17 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 132.225.430,00 | 130.725.430,0 | -1.500.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 52.551.283,13 | 52.551.283,3 | 0,17 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 16.195.121,93 | 15.375.121,93 | -820.000,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c5 / 2028 Tahmin | 89.807.672,00 | 89.807.692,00 | 20,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c6 / 2029 Tahmin | 99.193.663,00 | 102.973.097,00 | 3.779.434,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 16.195.121,93 | 15.375.121,93 | -820.000,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 89.807.672,00 | 89.807.692,00 | 20,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c6 / 2029 Tahmin | 99.193.663,00 | 102.973.097,00 | 3.779.434,00 |
| Halkla İlişkiler Müdürlüğü | 192 → 192 | T130 / Ekonomik tablo → T130 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 18.477.280,34 | 18.478.993,34 | 1.713,00 |
| Halkla İlişkiler Müdürlüğü | 192 → 192 | T130 / Ekonomik tablo → T130 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 18.477.280,34 | 18.478.993,34 | 1.713,00 |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kentsel Dönüşüm Müdürlüğü | 139 → 139 | T64 / Ekonomik tablo → T64 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 5.124.271,48 | 4.920.160,55 | -204.110,93 |
| Kentsel Dönüşüm Müdürlüğü | 139 → 139 | T64 / Ekonomik tablo → T64 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 5.124.271,48 | 4.920.160,55 | -204.110,93 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c6 / 2028 Tahmin | 4.912.500,00 | 3.825.000,00 | -1.087.500,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c7 / 2029 Tahmin | 6.215.625,00 | 3.825.000,00 | -2.390.625,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T188 / Ekonomik tablo → T188 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 283.751.680,00 | 265.909.180,00 | -17.842.500,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T169 / Faaliyet maliyetleri → T169 / Faaliyet maliyetleri | r21 → r21 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 888.224.835,00 | 888.224.210,00 | -625,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c5 / 2028 Tahmin | 320.792.302,00 | 291.167.302,00 | -29.625.000,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r11 → r11 / BÜTÇE İÇİ TOPLAM KAYNAK | c4 / 2027 Bütçe | 888.224.835,00 | 888.224.210,00 | -625,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r13 → r13 / FAALİYET MALİYETİ TOPLAMI | c4 / 2027 Bütçe | 888.224.835,00 | 888.224.210,00 | -625,00 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c4 / 2025 Gerçekleşme | 17.840 | 17,840 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c5 / 2026 Planlanan | 50.000 | 50,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 50.000 | 50,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c7 / 2027 Hedef | 50.000 | 50,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c8 / 2028 Tahmin | 60.000 | 60,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c9 / 2029 Tahmin | 60.000 | 60,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r10 → r10 / SH16/PG03. Bölge geneli bitkisel ve yapısal peyzaj alanlarının bakımı ve onarımı | c8 / 2028 Tahmin | 12.110.000 | 12.110,000 | -12.097.890 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r10 → r10 / SH16/PG03. Bölge geneli bitkisel ve yapısal peyzaj alanlarının bakımı ve onarımı | c9 / 2029 Tahmin | 12.170.000 | 12.170,000 | -12.157.830 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c4 / 2025 Gerçekleşme | 132.915 | 132,915 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c5 / 2026 Planlanan | 250.000 | 250,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 250.000 | 250,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c7 / 2027 Hedef | 200.000 | 200,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c8 / 2028 Tahmin | 250.000 | 250.000,000 | 0 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c9 / 2029 Tahmin | 300.000 | 300,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r12 → r12 / SH016/PG04. İklime uygun, dayanıklı ve az su tüketen bitki dikim ve bakım sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 3000 | 3.000,000 | 0 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r13 → r13 / SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 650 | 650,000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c5 / 2027 Bütçe | 543.583.357,00 | 528.076.250,00 | -15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c6 / 2028 Tahmin | 846.720.000,00 | 821.622.344,00 | -25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c7 / 2029 Tahmin | 1.016.063.999,00 | 984.691.330,00 | -31.372.669,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c5 / 2027 Bütçe | 543.583.357,00 | 528.076.250,00 | -15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c6 / 2028 Tahmin | 846.720.000,00 | 821.622.344,00 | -25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c7 / 2029 Tahmin | 1.016.063.999,00 | 984.691.330,00 | -31.372.669,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 566.807.107,00 | 551.300.000,00 | -15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c6 / 2028 Tahmin | 875.749.688,00 | 850.652.032,00 | -25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c7 / 2029 Tahmin | 1.052.351.109,00 | 1.020.978.440,00 | -31.372.669,00 |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T60 / Ekonomik tablo → T60 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 12.362.364,94 | 11.501.713,28 | -860.651,66 |
| Plan Proje Müdürlüğü | 136 → 136 | T60 / Ekonomik tablo → T60 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 12.362.364,94 | 11.501.713,28 | -860.651,66 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T151 / Faaliyet maliyetleri → T151 / Faaliyet maliyetleri | r11 → r11 / Toplam | c7 / 2029 Tahmin | 233.750,00 | 333.750,00 | 100.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T151 / Faaliyet maliyetleri → T151 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c7 / 2029 Tahmin | 233.750,00 | 333.750,00 | 100.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T152 / Ekonomik tablo → T152 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 936.918,72 | 955.735,48 | 18.816,76 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T152 / Ekonomik tablo → T152 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 936.918,72 | 955.735,48 | 18.816,76 |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T14 / Ekonomik tablo → T14 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 5.151.457,55 | 4.815.578,31 | -335.879,24 |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T14 / Ekonomik tablo → T14 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 5.151.457,55 | 4.815.578,31 | -335.879,24 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c5 / 2027 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c6 / 2028 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c7 / 2029 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c5 / 2027 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c6 / 2028 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c7 / 2029 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c5 / 2027 Bütçe | 9.221.747,00 | 9.171.747,00 | -50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c6 / 2028 Tahmin | 9.576.838,00 | 9.476.838,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c7 / 2029 Tahmin | 8.517.000,00 | 8.417.000,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c5 / 2027 Bütçe | 9.221.747,00 | 9.171.747,00 | -50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c6 / 2028 Tahmin | 9.576.838,00 | 9.476.838,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c7 / 2029 Tahmin | 8.517.000,00 | 8.417.000,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 15.337.207,00 | 15.287.207,00 | -50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c6 / 2028 Tahmin | 17.221.163,00 | 17.121.163,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c7 / 2029 Tahmin | 18.072.406,00 | 17.972.406,00 | -100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T84 / Ekonomik tablo → T84 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 16.365.381,00 | 16.565.381,00 | 200.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T84 / Ekonomik tablo → T84 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 16.365.381,00 | 16.565.381,00 | 200.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c5 / 2027 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c6 / 2028 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c7 / 2029 Tahmin | -0,00 | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c7 / 2029 Tahmin | 124.625.000,00 | 124.817.216,00 | 192.216,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c7 / 2029 Tahmin | 124.625.000,00 | 124.817.216,00 | 192.216,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 80.767.000,00 | 78.140.000,00 | -2.627.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 10.424.938,95 | ₺10.424.938,95 | 0,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 80.767.000,00 | 78.140.000,00 | -2.627.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 10.424.938,95 | ₺10.424.938,95 | 0,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r14 → r14 / 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması | c6 / 2028 Tahmin | 4.447.658,00 | 2.551.893,00 | -1.895.765,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r14 → r14 / 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması | c7 / 2029 Tahmin | 4.517.415,00 | 2.477.366,00 | -2.040.049,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c6 / 2028 Tahmin | 4.447.658,00 | 2.551.893,00 | -1.895.765,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c7 / 2029 Tahmin | 4.517.415,00 | 2.477.366,00 | -2.040.049,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r32 → r32 / 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri | c5 / 2027 Bütçe | 300.000,00 | 304.600,00 | 4.600,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c5 / 2027 Bütçe | 300.000,00 | 304.600,00 | 4.600,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T180 / Ekonomik tablo → T180 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c5 / 2028 Tahmin | 52.230.432,00 | 52.223.432,00 | -7.000,00 |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T20 / Ekonomik tablo → T20 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 51.258.201,04 | 45.863.621,38 | -5.394.579,66 |
| Zabıta Müdürlüğü | 104 → 104 | T20 / Ekonomik tablo → T20 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 51.258.201,04 | 45.863.621,38 | -5.394.579,66 |
| Çevre Koruma ve Kontrol Müdürlüğü | 153 → 153 | T78 / Ekonomik tablo → T78 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 4.085.221,72 | 3.967.964,02 | -117.257,70 |
| Çevre Koruma ve Kontrol Müdürlüğü | 153 → 153 | T78 / Ekonomik tablo → T78 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 4.085.221,72 | 3.967.964,02 | -117.257,70 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c5 / 2027 Bütçe | 6.300.000,00 | 6.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c6 / 2028 Tahmin | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c7 / 2029 Tahmin | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c5 / 2027 Bütçe | 6.300.000,00 | 6.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c6 / 2028 Tahmin | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c7 / 2029 Tahmin | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c5 / 2027 Bütçe | 6.800.000,00 | 6.500.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c6 / 2028 Tahmin | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c7 / 2029 Tahmin | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c5 / 2027 Bütçe | 6.800.000,00 | 6.500.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c6 / 2028 Tahmin | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c7 / 2029 Tahmin | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c5 / 2027 Bütçe | 8.050.000,00 | 7.750.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c6 / 2028 Tahmin | 9.162.500,00 | 8.862.500,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c7 / 2029 Tahmin | 8.803.125,00 | 8.503.125,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c5 / 2027 Bütçe | 8.050.000,00 | 7.750.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c6 / 2028 Tahmin | 9.162.500,00 | 8.862.500,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c7 / 2029 Tahmin | 8.803.125,00 | 8.503.125,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c5 / 2027 Bütçe | 2.300.000,00 | 2.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c6 / 2028 Tahmin | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c7 / 2029 Tahmin | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c5 / 2027 Bütçe | 2.300.000,00 | 2.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c6 / 2028 Tahmin | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c7 / 2029 Tahmin | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c5 / 2027 Bütçe | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c6 / 2028 Tahmin | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c7 / 2029 Tahmin | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c2 / 2026 Bütçe | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c5 / 2027 Bütçe | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c6 / 2028 Tahmin | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r15 / Bütçe İçi | c7 / 2029 Tahmin | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c2 / 2026 Bütçe | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c5 / 2027 Bütçe | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c6 / 2028 Tahmin | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r16 / Bütçe Dışı | c7 / 2029 Tahmin | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c2 / 2026 Bütçe | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c3 / 2026 Haziran Sonu Harcama | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c4 / 2026 Yıl Sonu Harcama Tahmini | YOK (satır/hücre yok) | - | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c5 / 2027 Bütçe | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c6 / 2028 Tahmin | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | rYOK → r17 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c7 / 2029 Tahmin | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → r18 / Bütçe İçi | c5 / 2027 Bütçe | 300.000,00 | 1.500.000,00 | 1.200.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → r18 / Bütçe İçi | c6 / 2028 Tahmin | 300.000,00 | 1.500.000,00 | 1.200.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → r18 / Bütçe İçi | c7 / 2029 Tahmin | 300.000,00 | 1.500.000,00 | 1.200.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c5 / → | 6.300.000,00 | 6.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c6 / → | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c7 / → | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c5 / → | 6.800.000,00 | 6.500.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c6 / → | 7.600.000,00 | 7.300.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c7 / → | 7.350.000,00 | 7.050.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c5 / → | 8.050.000,00 | 7.750.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c6 / → | 9.162.500,00 | 8.862.500,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c7 / → | 8.803.125,00 | 8.503.125,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c5 / → | 2.300.000,00 | 2.000.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c6 / → | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c7 / → | 3.100.000,00 | 2.800.000,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c5 / → | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c6 / → | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c7 / → | 300.000,00 | 0,00 | -300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c2 / → | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c3 / → | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c4 / → | YOK (satır/hücre yok) | 0,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c5 / → | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c6 / → | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | rYOK → r8 / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c7 / → | YOK (satır/hücre yok) | 1.500.000,00 | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T44 / Ekonomik tablo → T44 / Ekonomik tablo | r6 → r6 / BÜTÇE DIŞI TOPLAM KAYNAK | c2 / 2026 Bütçe | -0,00 | BOŞ | Hesaplanamaz |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 203 → 203 | T144 / Ekonomik tablo → T144 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 18.811.107,22 | 13.287.541,43 | -5.523.565,79 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 203 → 203 | T144 / Ekonomik tablo → T144 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 18.811.107,22 | 13.287.541,43 | -5.523.565,79 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c2 / 2026 Bütçe | - | BOŞ | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c3 / 2026 Haziran Sonu Harcama | - | BOŞ | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c4 / 2026 Yıl Sonu Harcama Tahmini | - | BOŞ | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r17 → r17 / Toplam | c5 / 2027 Bütçe | 84.942.000,00 | 84.375.000,00 | -567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c5 / 2027 Bütçe | 84.942.000,00 | 84.375.000,00 | -567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r20 → r20 / Personel ve SGK Giderleri Toplamı | c5 / 2027 Bütçe | 10.412.000,00 | 10.979.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r2 → r2 / Personel Giderleri | c2 / 2026 Bütçe | 0,00 | 58.995.430,00 | 58.995.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r2 → r2 / Personel Giderleri | c3 / 2026 Haziran Sonu Harcama | 0,00 | 29.032.954,0 | 29.032.954,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r3 → r3 / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | c2 / 2026 Bütçe | 0,00 | 7.400.000,00 | 7.400.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r3 → r3 / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | c3 / 2026 Haziran Sonu Harcama | 0,00 | 3.940.031,2 | 3.940.031,20 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c2 / 2026 Bütçe | 0,00 | 64.330.000,00 | 64.330.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c3 / 2026 Haziran Sonu Harcama | 0,00 | 18.209.313,23 | 18.209.313,23 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r5 → r5 / Cari Transferler | c2 / 2026 Bütçe | 0,00 | 1.500.000,0 | 1.500.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r5 → r5 / Cari Transferler | c3 / 2026 Haziran Sonu Harcama | 0,00 | 1.368.984,7 | 1.368.984,70 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 0,00 | 130.725.430,0 | 130.725.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 0,00 | 52.551.283,3 | 52.551.283,30 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 0,00 | 130.725.430,0 | 130.725.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 0,00 | 52.551.283,3 | 52.551.283,30 |
| Kurum / diğer | 244 → 244 | EKONOMİK KOD → EKONOMİK KOD | r5 → r5 / Mal ve Hizmet Alım Giderleri | c5 / → | 5.054.079.860,00 | 5.179.079.860,00 | 125.000.000,00 |

## Kitap kontrolü ve gönderime hazırlık

Kitap kontrol maddesi: **41 → 153**; gönderime hazır müdürlük: **17/34 → 5/34**.

Mesajlar: kitap 145 → 432; yalnız program grubu 140 → 112; SYSTEM 0 → 10.

Eski 41 madde: **8 çözüldü, 33 açık**. **120 yeni madde** var. Kimlik müdürlük + kontrol başlığı/yılıdır; durum aynı kontrol alanının geçip geçmediğini gösterir, gerekçe ve tutar değişmiş olabilir. Örneğin Sağlık toplam etiketi düzelmiştir; 2026 Haziran ve 2029 ekonomik kontrolleri yeni aritmetik farklar nedeniyle açık kalır. Kurum özet bulguları bu sayıya dahil değildir.

| Durum | Müdürlük | Kontrol maddesi | Eski sayfa / tablo / hücre | Yeni sayfa / tablo / hücre |
| --- | --- | --- | --- | --- |
| Çözüldü | Dış İlişkiler Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2029 Tahmin | s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Sağlık İşleri Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.98 / T10 / sütun 2 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Sağlık İşleri Müdürlüğü | Ekonomik tablo · 2027 Bütçe | s.98 / T10 / sütun 4 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Sağlık İşleri Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.98 / T10 / sütun 5 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.156 / T83 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 4 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.156 / T83 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.156 / T83 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 6 / satır 2,3,4,5,6,7,8 | YOK |
| Açık | Bilgi İşlem Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.207 / T147 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8 | s.207 / T147 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Bilgi İşlem Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.207 / T147 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8 | s.207 / T147 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | Dış İlişkiler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.186 / T119 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8 | s.186 / T119 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Dış İlişkiler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.186 / T119 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 6 / satır 2,3,4,5,6,7,8 | s.186 / T119 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.186 / T120 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | Fen İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.118 / T37 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9 | s.118 / T37 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 5 / satır 2,3,4,5,6,7,8,9 |
| Açık | Fen İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.118 / T37 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9 | s.118 / T37 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,32; s.118 / T38 / sütun 6 / satır 2,3,4,5,6,7,8,9 |
| Açık | Gençlik ve Spor İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.173 / T105 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8 | s.173 / T105 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Gençlik ve Spor İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.173 / T105 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8 | s.173 / T105 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | Halkla İlişkiler Müdürlüğü | 0006. Çağrı hizmetlerinde görev yapan personele yönelik daha fazla iletişim, mevzuat ve sistem kullanımı eğitimler | s.192 / T129 / sütun 1 / satır 17,37,48,57 | s.192 / T129 / sütun 1 / satır 17,37,48,57 |
| Açık | Halkla İlişkiler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.192 / T129 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.192 / T130 / sütun 5 / satır 2,3,4,5,6,7,8 | s.192 / T129 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.192 / T130 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Kültür, Sanat ve Sosyal İşler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.167 / T99 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 4 / satır 2,3,4,5,6,7 | s.167 / T99 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 4 / satır 2,3,4,5,6,7 |
| Açık | Kültür, Sanat ve Sosyal İşler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.167 / T99 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 5 / satır 2,3,4,5,6,7 | s.167 / T99 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 5 / satır 2,3,4,5,6,7 |
| Açık | Kültür, Sanat ve Sosyal İşler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.167 / T99 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 6 / satır 2,3,4,5,6,7 | s.167 / T99 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,56; s.167 / T100 / sütun 6 / satır 2,3,4,5,6,7 |
| Açık | Makine İkmal Bakım ve Onarım Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.236 / T187 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8 | s.236 / T187 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Park ve Bahçeler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.128 / T49 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 4 / satır 2,3,4,5,6,7,8 | s.128 / T49 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 4 / satır 2,3,4,5,6,7,8 |
| Açık | Park ve Bahçeler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.128 / T49 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 5 / satır 2,3,4,5,6,7,8 | s.128 / T49 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Park ve Bahçeler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.128 / T49 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 6 / satır 2,3,4,5,6,7,8 | s.128 / T49 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,44; s.128 / T50 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | Rehberlik ve Teftiş Kurulu Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.210 / T151 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,14; s.210 / T152 / sütun 6 / satır 2,3,4,5,6,7,8 | s.210 / T151 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,14; s.210 / T152 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | Ruhsat ve Denetim Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.101 / T14 / sütun 2 / satır 2,3,4,5,6,7 | s.101 / T14 / sütun 2 / satır 2,3,4,5,6,7 |
| Açık | Sağlık İşleri Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.98 / T10 / sütun 3 / satır 2,3,4,5,6,7,8,9 | s.98 / T10 / sütun 3 / satır 2,3,4,5,6,7,8,9 |
| Açık | Sağlık İşleri Müdürlüğü | Ekonomik tablo · 2029 Tahmin | s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9 | s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9 |
| Açık | Sağlık İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.98 / T9 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9 | s.98 / T9 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.98 / T10 / sütun 6 / satır 2,3,4,5,6,7,8,9 |
| Açık | Strateji Geliştirme Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.215 / T159 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29; s.215 / T160 / sütun 5 / satır 2,3,4,5,6,7 | s.215 / T159 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29; s.215 / T160 / sütun 5 / satır 2,3,4,5,6,7 |
| Açık | Yazı İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.228 / T179 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9 | s.228 / T179 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9 |
| Açık | Özel Kalem Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.199 / T137 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 5 / satır 2,3,4,5,6,7,8 | s.199 / T137 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23; s.199 / T138 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Özel Kalem Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.199 / T137 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 6 / satır 2,3,4,5,6,7,8 | s.199 / T137 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23; s.199 / T138 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | İnsan Kaynakları ve Eğitim Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8 | s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2027 Bütçe | s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8 | s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 5 / satır 20 |
| Açık | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2029 Tahmin | s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 7 / satır 20 | s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 7 / satır 20 |
| Açık | İşletme ve İştirakler Müdürlüğü | Personel/SGK toplam farkı · 2029 | s.241 / T195 / sütun 7 / satır 20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 | s.241 / T195 / sütun 7 / satır 20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | İşletme ve İştirakler Müdürlüğü | SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2026 Yıl Sonu Tahmini | s.239 / T191 / sütun 6 / satır 10 | s.239 / T191 / sütun 6 / satır 10 |
| Açık | İşletme ve İştirakler Müdürlüğü | SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2027 Hedef | s.239 / T191 / sütun 7 / satır 10 | s.239 / T191 / sütun 7 / satır 10 |
| Açık | İşletme ve İştirakler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.241 / T195 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 | s.241 / T195 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Yeni | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2027 Bütçe | YOK | s.144 / T69 / sütun 5 / satır 44,45,46 |
| Yeni | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2028 Tahmin | YOK | s.144 / T69 / sütun 6 / satır 44,45,46 |
| Yeni | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2029 Tahmin | YOK | s.144 / T69 / sütun 7 / satır 44,45,46 |
| Yeni | Afet İşleri ve Risk Yönetimi Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.144 / T70 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Araştırma ve Geliştirme Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.195 / T134 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Bilgi İşlem Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Yeni | Bilgi İşlem Müdürlüğü | Ekonomik tablo · 2029 Tahmin | YOK | s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Yeni | Bilgi İşlem Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | YOK | s.207 / T147 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 4 / satır 2,3,4,5,6,7,8 |
| Yeni | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Bütçe | YOK | s.186 / T119 / sütun 2 / satır 17,18,19 |
| Yeni | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Haziran Sonu Harcama | YOK | s.186 / T119 / sütun 3 / satır 17,18,19 |
| Yeni | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Yıl Sonu Tahmini | YOK | s.186 / T119 / sütun 4 / satır 17,18,19 |
| Yeni | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2027 Bütçe | YOK | s.112 / T29 / sütun 5 / satır 14,15,16 |
| Yeni | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2028 Tahmin | YOK | s.112 / T29 / sütun 6 / satır 14,15,16 |
| Yeni | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2029 Tahmin | YOK | s.112 / T29 / sütun 7 / satır 14,15,16 |
| Yeni | Emlak İstimlak Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.112 / T30 / sütun 3 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Fen İşleri Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.118 / T38 / sütun 2 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Gelirler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.232 / T184 / sütun 2 / satır 2,3,4,5,6,7,8 |
| Yeni | Gelirler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.232 / T184 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.173 / T106 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Yeni | Halkla İlişkiler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.192 / T130 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Bütçe | YOK | s.212 / T155 / sütun 2 / satır 17,18,19 |
| Yeni | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Haziran Sonu Harcama | YOK | s.212 / T155 / sütun 3 / satır 17,18,19 |
| Yeni | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Yıl Sonu Tahmini | YOK | s.212 / T155 / sütun 4 / satır 17,18,19 |
| Yeni | Kentsel Dönüşüm Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.139 / T64 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2028 Tahmin | YOK | s.167 / T99 / sütun 6 / satır 8,9,10 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2029 Tahmin | YOK | s.167 / T99 / sütun 7 / satır 8,9,10 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 11,12,13 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 11,12,13 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 11,12,13 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 14,15,16 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 14,15,16 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 14,15,16 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 17,18,19 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 17,18,19 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 17,18,19 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 20,21,22 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 20,21,22 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 20,21,22 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 23,24,25 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 23,24,25 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 23,24,25 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 26,27,28 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 26,27,28 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 26,27,28 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 29,30,31 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 29,30,31 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 29,30,31 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 32,33,34 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 32,33,34 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 32,33,34 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 35,36,37 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 35,36,37 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 35,36,37 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 38,39,40 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 38,39,40 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 38,39,40 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 41,42,43 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 41,42,43 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 41,42,43 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 44,45,46 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 44,45,46 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 44,45,46 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 47,48,49 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 47,48,49 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 47,48,49 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Bütçe | YOK | s.167 / T99 / sütun 2 / satır 50,51,52 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Haziran Sonu Harcama | YOK | s.167 / T99 / sütun 3 / satır 50,51,52 |
| Yeni | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Yıl Sonu Tahmini | YOK | s.167 / T99 / sütun 4 / satır 50,51,52 |
| Yeni | Makine İkmal Bakım ve Onarım Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Yeni | Mali Hizmetler Müdürlüğü | Ekonomik tablo · 2027 Bütçe | YOK | s.222 / T170 / sütun 4 / satır 2,3,4,5,6,7,8,9,10,11,12,13 |
| Yeni | Mali Hizmetler Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.222 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13 |
| Yeni | Mali Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | YOK | s.222 / T169 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.222 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2025 Gerçekleşme | YOK | s.125 / T45 / sütun 4 / satır 11 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Planlanan | YOK | s.125 / T45 / sütun 5 / satır 11 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Yıl Sonu Tahmini | YOK | s.125 / T45 / sütun 6 / satır 11 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2027 Hedef | YOK | s.125 / T45 / sütun 7 / satır 11 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2029 Tahmin | YOK | s.125 / T45 / sütun 9 / satır 11 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı · 2026 Yıl Sonu Tahmini | YOK | s.125 / T45 / sütun 6 / satır 13 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2025 Gerçekleşme | YOK | s.125 / T45 / sütun 4 / satır 9 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Planlanan | YOK | s.125 / T45 / sütun 5 / satır 9 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Yıl Sonu Tahmini | YOK | s.125 / T45 / sütun 6 / satır 9 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2027 Hedef | YOK | s.125 / T45 / sütun 7 / satır 9 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2028 Tahmin | YOK | s.125 / T45 / sütun 8 / satır 9 |
| Yeni | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2029 Tahmin | YOK | s.125 / T45 / sütun 9 / satır 9 |
| Yeni | Plan Proje Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.136 / T60 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Rehberlik ve Teftiş Kurulu Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.210 / T152 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | Ruhsat ve Denetim Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.101 / T14 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2027 Bütçe | YOK | s.156 / T83 / sütun 5 / satır 23,24,25 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2028 Tahmin | YOK | s.156 / T83 / sütun 6 / satır 23,24,25 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2029 Tahmin | YOK | s.156 / T83 / sütun 7 / satır 23,24,25 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2027 Bütçe | YOK | s.156 / T83 / sütun 5 / satır 26,27,28 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2028 Tahmin | YOK | s.156 / T83 / sütun 6 / satır 26,27,28 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2029 Tahmin | YOK | s.156 / T83 / sütun 7 / satır 26,27,28 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.156 / T84 / sütun 2 / satır 2,3,4,5,6,7,8 |
| Yeni | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2027 Bütçe | YOK | s.107 / T23 / sütun 5 / satır 11,12,13 |
| Yeni | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2028 Tahmin | YOK | s.107 / T23 / sütun 6 / satır 11,12,13 |
| Yeni | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2029 Tahmin | YOK | s.107 / T23 / sütun 7 / satır 11,12,13 |
| Yeni | Veteriner İşleri Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.107 / T24 / sütun 2 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Yazı İşleri Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.228 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Yazı İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | YOK | s.228 / T179 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 4 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Yazı İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | YOK | s.228 / T179 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 6 / satır 2,3,4,5,6,7,8,9 |
| Yeni | Zabıta Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.104 / T20 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | Çevre Koruma ve Kontrol Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.153 / T78 / sütun 3 / satır 2,3,4,5,6,7 |
| Yeni | Özel Kalem Müdürlüğü | 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | YOK | s.199 / T137 / sütun 1 / satır 17,25,35 |
| Yeni | İmar ve Şehircilik Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.122 / T44 / sütun 2 / satır 2,3,4,5,6,7 |
| Yeni | İnsan Kaynakları ve Eğitim Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.203 / T144 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Bütçe | YOK | s.241 / T195 / sütun 2 / satır 5,6,7 |
| Yeni | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Haziran Sonu Harcama | YOK | s.241 / T195 / sütun 3 / satır 5,6,7 |
| Yeni | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Yıl Sonu Tahmini | YOK | s.241 / T195 / sütun 4 / satır 5,6,7 |
| Yeni | İşletme ve İştirakler Müdürlüğü | 0033.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek. | YOK | s.241 / T195 / sütun 1 / satır 8,22,32 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | YOK | s.241 / T196 / sütun 2 / satır 2,3,4,5,6,7,8 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | YOK | s.241 / T196 / sütun 3 / satır 2,3,4,5,6,7,8 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Personel/SGK toplam farkı · 2027 | YOK | s.241 / T195 / sütun 5 / satır 20; s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Tablo 190, satır 3: İşletme ve İştirakler Müdürlüğü / 0011.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | YOK | s.238 / T190 / sütun 1 / satır 3 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Tablo 192, satır 3: İşletme ve İştirakler Müdürlüğü / 0012.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek,: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | YOK | s.239 / T192 / sütun 1 / satır 3 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Tablo 192, satır 4: İşletme ve İştirakler Müdürlüğü / 0013.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | YOK | s.239 / T192 / sütun 1 / satır 4 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Tablo 194, satır 3: İşletme ve İştirakler Müdürlüğü / 0014.Belediyeye bağlı iktisadi işletme şubelerinin (sosyal tesis, otopark, düğün salonu vb.) işletmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | YOK | s.240 / T194 / sütun 1 / satır 3 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Tablo 194, satır 4: İşletme ve İştirakler Müdürlüğü / 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | YOK | s.240 / T194 / sütun 1 / satır 4 |
| Yeni | İşletme ve İştirakler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | YOK | s.241 / T195 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8 |

## Okuma sınırları, kaynak sorunları ve teyit

Onaylı PDF bu çalışmada ayrıca açılıp doğrulanmadı; PDF ile eşleşme bilgisi görevde verilen D-320 teyididir. IDML SHA256 değeri doğrulandı. Çok sayfalı story için ilk basılı sayfa gösterilir; InDesign dizgi motoru kullanılmadığından hücrenin kesin devam sayfası doğrulanamaz.

Özel Kalem’de 0006 emekli ikramiyesi maliyet satırı onaylı kaynakta vardır: faaliyet sayısının 290’dan 291’e çıkması bu satırdır; maliyet uydurulmadı. Sağlık ekonomik tablosunun eski BOŞ toplam etiketi onaylı kaynakta “BÜTÇE İÇİ TOPLAM KAYNAK” olmuştur; aynı tutarın artık tanınması sayısal düzeltmeyle karıştırılmamalıdır.

İşletme ve İştirakler’de basılı kart üyelik kodları 0011/0012/0013/0014/0015, maliyet kodları 0001/0002/0033/0004/0005’tir. Tekil kod eşlemesi beş faaliyeti bağlayamaz: 5 üyelik kontrol maddesi ve 10 SYSTEM bağlantı mesajı vardır. Bu, kaynak kod uyuşmazlığıdır; parser kusuru olduğu kanıtlanmadı. Kodlar düzeltilmedi, ad benzerliğiyle bağlanmadı, tablo dışlanmadı.

Diğer çözülmemiş SYSTEM bulguları onaylı dry-run’da ayrı listelenir. Bu görevde pasteboard dışında kanıtlanmış parser kusuru düzeltilmedi. Belirsiz sayı biçimi, eksik kaynak ve doğrulama sorunları raporda korunur. Canlı veritabanına bağlanılmadı.

`2027-performans-programi_16102026_duzeltilmis 2.idml`: kurum 1036 PASS / 184 FAIL; sınıflar {'BOOK': 53, 'UNKNOWN': 27, 'CHECK': 104}. Geometriyle dışlanan: 2 pasteboard + 4 yerleşimsiz tablo.

`2027-performans-programi_ONAYLI.idml`: kurum 1036 PASS / 184 FAIL; sınıflar {'BOOK': 53, 'UNKNOWN': 27, 'CHECK': 104}. Geometriyle dışlanan: 7 pasteboard + 4 yerleşimsiz tablo.
