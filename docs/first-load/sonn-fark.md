# 2027 PP SONN (11 Kasım) — canlıya yüklenen ONAYLI kaynağına göre fark

Muhatap: proje sahibi ve Strateji. 2027 ilk yüklemesinin tek kaynağı onaylı IDML’dir (D-316). Bu rapor kaynak değerlerini ve yükleyici/doğrulama kurallarını değiştirmez.

Eski: `2027-performans-programi_ONAYLI.idml`; SHA256 `cbbf9018302d0a1d33d1dde0c4a64a2418d12b55cc29d046205371018673bd71`.

Yeni: `SONN.idml`; SHA256 `8f8310138324bfe7560cae864595de1f7d1ad4bb7a982eebe4915a18e0728ec4`.

Karşılaştırma, iki kaynağı da aynı basılı sayfa geometrisi filtresiyle ve ayrı geçici yerel PostgreSQL veritabanlarında gerçek servislerle çalıştırır. Eski rapor `docs/first-load/dryrun-printed.md` ve `dryrun-d3.md` değiştirilmez. Onaylı arşivdeki 240 tablonun 229’u basılı, 7’si pasteboard ve 4’ü yerleşimsizdir; yerleşimsiz dört tablo önceki okuyucu tarafından da yüklenmiyordu.

## Yeniden üretme

```sh
# CIVENSA_TEST_POSTGRES_URL: yerel, disposable PostgreSQL 16+; CREATE DATABASE yetkisi.
python scripts/first_load_dryrun.py <SONN.idml (owner upload 11 Nov 2026, not committed)> --out /tmp/dry.md --compare-source tests/fixtures/first_load/source/2027-performans-programi_ONAYLI.idml --diff-out docs/first-load/sonn-fark.md
```

## Müdürlük sayımları

Her hücre eski → yeni. Ekonomik değer sayısı kategori kayıtlarını sayar; toplam satırları ayrıca denetlenir. YOK müdürlüğün kaynakta bulunmadığı anlamına gelir.

| Müdürlük | Kart | Gösterge | Faaliyet | Ekonomik değer | Kitap maddesi | Hazır |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 2 → 2 | 10 → 10 | 16 → 16 | 30 → 30 | 4 → 0 | Hayır → Evet |
| Araştırma ve Geliştirme Müdürlüğü | 1 → 1 | 4 → 4 | 8 → 8 | 30 → 30 | 1 → 0 | Hayır → Evet |
| Bilgi İşlem Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 40 → 40 | 5 → 2 | Hayır → Hayır |
| Destek Hizmetleri Müdürlüğü | 2 → 2 | 9 → 9 | 7 → 7 | 40 → 40 | 0 → 0 | Evet → Evet |
| Dış İlişkiler Müdürlüğü | 1 → 1 | 3 → 3 | 10 → 10 | 40 → 40 | 5 → 3 | Hayır → Hayır |
| Emlak İstimlak Müdürlüğü | 2 → 2 | 7 → 7 | 11 → 11 | 50 → 50 | 4 → 0 | Hayır → Evet |
| Etüd Proje Müdürlüğü | 2 → 2 | 6 → 6 | 12 → 12 | 30 → 30 | 0 → 0 | Evet → Evet |
| Fen İşleri Müdürlüğü | 3 → 3 | 15 → 15 | 9 → 9 | 50 → 50 | 3 → 2 | Hayır → Hayır |
| Gelirler Müdürlüğü | 1 → 1 | 3 → 3 | 9 → 9 | 40 → 40 | 2 → 0 | Hayır → Evet |
| Gençlik ve Spor İşleri Müdürlüğü | 2 → 2 | 10 → 10 | 10 → 10 | 40 → 40 | 4 → 3 | Hayır → Hayır |
| Halkla İlişkiler Müdürlüğü | 4 → 4 | 16 → 16 | 10 → 10 | 40 → 40 | 3 → 2 | Hayır → Hayır |
| Hukuk İşleri Müdürlüğü | 1 → 1 | 4 → 4 | 6 → 6 | 30 → 30 | 3 → 0 | Hayır → Evet |
| Kentsel Dönüşüm Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 30 → 30 | 1 → 0 | Hayır → Evet |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 5 → 5 | 24 → 24 | 17 → 17 | 30 → 30 | 47 → 3 | Hayır → Hayır |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 40 → 40 | 2 → 1 | Hayır → Hayır |
| Mali Hizmetler Müdürlüğü | 1 → 1 | 2 → 2 | 5 → 5 | 90 → 90 | 3 → 0 | Hayır → Evet |
| Park ve Bahçeler Müdürlüğü | 2 → 2 | 7 → 7 | 13 → 13 | 40 → 40 | 15 → 3 | Hayır → Hayır |
| Plan Proje Müdürlüğü | 1 → 1 | 5 → 5 | 1 → 1 | 30 → 30 | 1 → 0 | Hayır → Evet |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 1 → 1 | 5 → 5 | 3 → 3 | 40 → 40 | 2 → 1 | Hayır → Hayır |
| Ruhsat ve Denetim Müdürlüğü | 1 → 1 | 5 → 5 | 5 → 5 | 30 → 30 | 2 → 1 | Hayır → Hayır |
| Sağlık İşleri Müdürlüğü | 4 → 4 | 11 → 11 | 10 → 10 | 50 → 50 | 3 → 3 | Hayır → Hayır |
| Sosyal Destek Müdürlüğü | 4 → 4 | 20 → 20 | 19 → 19 | 40 → 40 | 0 → 0 | Evet → Evet |
| Strateji Geliştirme Müdürlüğü | 1 → 1 | 5 → 5 | 8 → 8 | 30 → 30 | 1 → 1 | Hayır → Hayır |
| Tarımsal Hizmetler Müdürlüğü | 2 → 2 | 9 → 9 | 11 → 11 | 40 → 40 | 7 → 3 | Hayır → Hayır |
| Temizlik İşleri Müdürlüğü | 1 → 1 | 4 → 4 | 8 → 8 | 40 → 40 | 0 → 0 | Evet → Evet |
| Veteriner İşleri Müdürlüğü | 1 → 1 | 5 → 5 | 6 → 6 | 50 → 50 | 4 → 0 | Hayır → Evet |
| Yazı İşleri Müdürlüğü | 4 → 4 | 19 → 19 | 11 → 11 | 50 → 50 | 4 → 1 | Hayır → Hayır |
| Zabıta Müdürlüğü | 2 → 2 | 9 → 9 | 9 → 9 | 40 → 40 | 1 → 0 | Hayır → Evet |
| Çevre Koruma ve Kontrol Müdürlüğü | 1 → 1 | 3 → 3 | 3 → 3 | 30 → 30 | 1 → 0 | Hayır → Evet |
| Özel Kalem Müdürlüğü | 1 → 1 | 5 → 5 | 6 → 5 | 40 → 40 | 3 → 2 | Hayır → Hayır |
| İklim Değişikliği ve Sıfır Atık Müdürlüğü | 1 → 1 | 3 → 3 | 5 → 5 | 30 → 30 | 0 → 0 | Evet → Evet |
| İmar ve Şehircilik Müdürlüğü | 2 → 2 | 7 → 7 | 13 → 13 | 30 → 30 | 1 → 0 | Hayır → Evet |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 2 → 2 | 6 → 6 | 10 → 10 | 40 → 40 | 2 → 1 | Hayır → Hayır |
| İşletme ve İştirakler Müdürlüğü | 3 → 3 | 7 → 7 | 5 → 5 | 40 → 40 | 19 → 3 | Hayır → Hayır |
| **Toplam** | **64 → 64** | **263 → 263** | **291 → 290** | **1340 → 1340** | **153 → 35** | **5 → 17** |

Müdürlük: 34 → 34; yeni: Yok; eksilen: Yok.

## Değişen bütün tutar / gösterge hücreleri

**362 değişen hücre**. Kapsam: bütün basılı IDML tabloları; kurum özetleri ve diğer sayısal tablolar dahildir. T numarası üretilen Word tablosudur. Basılmayan tablolar kapsam dışıdır. Fark = yeni − eski; BOŞ, çizgi, sıfır ve YOK ayrı tutulur. Ham değerler aynen korunur; yalnız fark Türkçe sayı biçimiyle yazılır. Ham biçim değişip sayısal değer aynı kalırsa fark 0’dır. Belirsiz/okunamayan veya eksik bir taraf varsa fark hesaplanmaz.

Tablolar müdürlük + tür + basılı sıra ile; kurum tabloları başlık türüyle; diğer tablolar sayfa + ilk başlık + sıra ile eşlenir. IDML kimlikleri dışa aktarmada yenilendiğinden eşleme anahtarı değildir. Aynı boyutlu tablolarda satır konumu korunur; eklenen satırlar etiket dizisiyle hizalanır. Sütunlar fiziksel sıradadır; satır/sütun konumu ve başlık birlikte kanıttır.

| Müdürlük / kapsam | Sayfa eski → yeni | Tablo eski → yeni | Satır / etiket | Sütun / etiket | Eski ham değer | Yeni ham değer | Fark |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c5 / 2027 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c6 / 2028 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T69 / Faaliyet maliyetleri → T69 / Faaliyet maliyetleri | r46 → r46 / Bütçe Dışı | c7 / 2029 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T70 / Ekonomik tablo → T70 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 5.091.250,40 | 6.554.522,21 | 1.463.271,81 |
| Afet İşleri ve Risk Yönetimi Müdürlüğü | 144 → 144 | T70 / Ekonomik tablo → T70 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 5.091.250,40 | 6.554.522,21 | 1.463.271,81 |
| Araştırma ve Geliştirme Müdürlüğü | 195 → 195 | T134 / Ekonomik tablo → T134 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 832.400,90 | 813.893,90 | -18.507,00 |
| Araştırma ve Geliştirme Müdürlüğü | 195 → 195 | T134 / Ekonomik tablo → T134 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 832.400,90 | 813.893,90 | -18.507,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c4 / 2027 Bütçe | 236.000.000,00 | 235.000.000,00 | -1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c4 / 2027 Bütçe | 283.812.848,00 | 282.812.848,00 | -1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c4 / 2027 Bütçe | 283.812.848,00 | 282.812.848,00 | -1.000.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 454.155.142,00 | 480.825.142,00 | 26.670.000,00 |
| Bilgi İşlem Müdürlüğü | 207 → 207 | T148 / Ekonomik tablo → T148 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c6 / 2029 Tahmin | 777.302.769,00 | 810.640.269,00 | 33.337.500,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r32 → r32 / Toplam | c5 / 2027 Bütçe | 4.039.548,00 | 5.039.548,00 | 1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c5 / 2027 Bütçe | 4.039.548,00 | 5.039.548,00 | 1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T119 / Faaliyet maliyetleri → T119 / Faaliyet maliyetleri | r36 → r36 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 5.514.548,00 | 6.514.548,00 | 1.000.000,00 |
| Dış İlişkiler Müdürlüğü | 186 → 186 | T120 / Ekonomik tablo → T120 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 7.414.231,00 | 6.414.231,00 | -1.000.000,00 |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c5 / 2027 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c6 / 2028 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r16 → r16 / Bütçe Dışı | c7 / 2029 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T29 / Faaliyet maliyetleri → T29 / Faaliyet maliyetleri | r35 → r35 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T30 / Ekonomik tablo → T30 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 113.352.771,64 | 113.787.163,62 | 434.391,98 |
| Emlak İstimlak Müdürlüğü | 112 → 112 | T30 / Ekonomik tablo → T30 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 113.352.771,64 | 113.787.163,62 | 434.391,98 |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Etüd Proje Müdürlüğü | 133 → 133 | T55 / Faaliyet maliyetleri → T55 / Faaliyet maliyetleri | r38 → r38 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Fen İşleri Müdürlüğü | 118 → 118 | T37 / Faaliyet maliyetleri → T37 / Faaliyet maliyetleri | r29 → r29 / Toplam | c7 / 2029 Tahmin | 2.592.904.546,00 | 2.592.658.713,00 | -245.833,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T37 / Faaliyet maliyetleri → T37 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c7 / 2029 Tahmin | 2.592.904.546,00 | 2.592.658.713,00 | -245.833,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T38 / Ekonomik tablo → T38 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 950.000.000,00 | 949.340.000,00 | -660.000,00 |
| Fen İşleri Müdürlüğü | 118 → 118 | T38 / Ekonomik tablo → T38 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 950.000.000,00 | 949.340.000,00 | -660.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 130.725.430,0 | 132.225.430,00 | 1.500.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 52.551.283,3 | 52.551.283,13 | -0,17 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 130.725.430,0 | 132.225.430,00 | 1.500.000,00 |
| Gelirler Müdürlüğü | 232 → 232 | T184 / Ekonomik tablo → T184 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 52.551.283,3 | 52.551.283,13 | -0,17 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 15.375.121,93 | 16.195.121,93 | 820.000,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c5 / 2028 Tahmin | 89.807.692,00 | 89.807.672,00 | -20,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c6 / 2029 Tahmin | 102.973.097,00 | 99.193.663,00 | -3.779.434,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 15.375.121,93 | 16.195.121,93 | 820.000,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 89.807.692,00 | 89.807.672,00 | -20,00 |
| Gençlik ve Spor İşleri Müdürlüğü | 173 → 173 | T106 / Ekonomik tablo → T106 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c6 / 2029 Tahmin | 102.973.097,00 | 99.193.663,00 | -3.779.434,00 |
| Halkla İlişkiler Müdürlüğü | 192 → 192 | T130 / Ekonomik tablo → T130 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 18.478.993,34 | 18.477.280,34 | -1.713,00 |
| Halkla İlişkiler Müdürlüğü | 192 → 192 | T130 / Ekonomik tablo → T130 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 18.478.993,34 | 18.477.280,34 | -1.713,00 |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Hukuk İşleri Müdürlüğü | 212 → 212 | T155 / Faaliyet maliyetleri → T155 / Faaliyet maliyetleri | r19 → r19 / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kentsel Dönüşüm Müdürlüğü | 139 → 139 | T64 / Ekonomik tablo → T64 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 4.920.160,55 | 5.124.271,48 | 204.110,93 |
| Kentsel Dönüşüm Müdürlüğü | 139 → 139 | T64 / Ekonomik tablo → T64 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 4.920.160,55 | 5.124.271,48 | 204.110,93 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c6 / 2028 Tahmin | 3.825.000,00 | 4.912.500,00 | 1.087.500,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c7 / 2029 Tahmin | 3.825.000,00 | 6.215.625,00 | 2.390.625,00 |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r30 → r30 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r39 → r39 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r45 → r45 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r48 → r48 / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Kültür, Sanat ve Sosyal İşler Müdürlüğü | 167 → 167 | T99 / Faaliyet maliyetleri → T99 / Faaliyet maliyetleri | r52 → r52 / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T185 / Kart → T185 / Kart | r11 → r11 / SH64/PG03. Bakımonarım hizmeti verilen hizmet aracı sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 110 | 119 | 9 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T185 / Kart → T185 / Kart | r11 → r11 / SH64/PG03. Bakımonarım hizmeti verilen hizmet aracı sayısı | c7 / 2027 Hedef | 110 | 119 | 9 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T185 / Kart → T185 / Kart | r11 → r11 / SH64/PG03. Bakımonarım hizmeti verilen hizmet aracı sayısı | c8 / 2028 Tahmin | 110 | 119 | 9 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T185 / Kart → T185 / Kart | r11 → r11 / SH64/PG03. Bakımonarım hizmeti verilen hizmet aracı sayısı | c9 / 2029 Tahmin | 110 | 119 | 9 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r2 → r2 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c5 / 2027 Bütçe | 64.838.837,00 | 194.516.511,00 | 129.677.674,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r2 → r2 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c6 / 2028 Tahmin | 88.636.394,00 | 265.909.180,00 | 177.272.786,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r2 → r2 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c7 / 2029 Tahmin | 120.814.085,00 | 362.442.255,00 | 241.628.170,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c5 / 2027 Bütçe | 64.838.837,00 | 194.516.511,00 | 129.677.674,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c6 / 2028 Tahmin | 88.636.394,00 | 265.909.180,00 | 177.272.786,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c7 / 2029 Tahmin | 120.814.085,00 | 362.442.255,00 | 241.628.170,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r5 → r5 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | c5 / 2027 Bütçe | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r5 → r5 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | c6 / 2028 Tahmin | 88.636.394,00 | 0,00 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r5 → r5 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi | c7 / 2029 Tahmin | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c5 / 2027 Bütçe | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c6 / 2028 Tahmin | 88.636.394,00 | 0,00 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c7 / 2029 Tahmin | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r8 → r8 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | c5 / 2027 Bütçe | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r8 → r8 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | c6 / 2028 Tahmin | 88.636.394,00 | 0,00 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r8 → r8 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi | c7 / 2029 Tahmin | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c5 / 2027 Bütçe | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c6 / 2028 Tahmin | 88.636.394,00 | 0,0 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c7 / 2029 Tahmin | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r17 → r17 / Toplam | c6 / 2028 Tahmin | 265.909.182,00 | 265.909.180,00 | -2,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c6 / 2028 Tahmin | 265.909.182,00 | 265.909.180,00 | -2,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r20 → r20 / Personel ve SGK Giderleri Toplamı | c7 / 2029 Tahmin | 22.303.126,00 | 21.303.126.00 | Hesaplanamaz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r21 → r21 / Genel Bütçe Toplamı | c6 / 2028 Tahmin | 265.909.180,00 | 283.751.680,00 | 17.842.500,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T187 / Faaliyet maliyetleri → T187 / Faaliyet maliyetleri | r21 → r21 / Genel Bütçe Toplamı | c7 / 2029 Tahmin | 384.745.381,00 | 383.745.381,00 | -1.000.000,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T188 / Ekonomik tablo → T188 / Ekonomik tablo | r2 → r2 / Personel Giderleri | c6 / 2029 Tahmin | 19.292.188,00 | 19.292.188.00 | Hesaplanamaz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T188 / Ekonomik tablo → T188 / Ekonomik tablo | r3 → r3 / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | c6 / 2029 Tahmin | 3.010.938,00 | 3.010.938.00 | Hesaplanamaz |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 236 → 236 | T188 / Ekonomik tablo → T188 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c5 / 2028 Tahmin | 265.909.180,00 | 283.751.680,00 | 17.842.500,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r3 → r3 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c5 / → | 64.838.837,00 | 194.516.511,00 | 129.677.674,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r3 → r3 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c6 / → | 88.636.394,00 | 265.909.180,00 | 177.272.786,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r3 → r3 / 0001.Resmî araç ve iş makinelerinin periyodik ve koruyucu bakımlarının yapılması, hurdaya ayırma işlemleri ile araç sevk ve idare koordinasyonu. | c7 / → | 120.814.085,00 | 362.442.255,00 | 241.628.170,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r4 → r4 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi → 0002.Birimlerden gelen araç taleplerinin karşılanması | c5 / → | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r4 → r4 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi → 0002.Birimlerden gelen araç taleplerinin karşılanması | c6 / → | 88.636.394,00 | 0,00 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r4 → r4 / 0002.Akıllı Araç Takip ve Bakım Yönetim Sistemi Projesi → 0002.Birimlerden gelen araç taleplerinin karşılanması | c7 / → | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r5 → r5 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi → 0003.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | c5 / → | 64.838.837,00 | 0,00 | -64.838.837,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r5 → r5 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi → 0003.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | c6 / → | 88.636.394,00 | 0,00 | -88.636.394,00 |
| Makine İkmal Bakım ve Onarım Müdürlüğü | 235 → 235 | T186 / Kart faaliyet üyeliği → T186 / Kart faaliyet üyeliği | r5 → r5 / 0003.Bakım ve Onarım Atölyesi Modernizasyon Projesi → 0003.Dış paydaşlardan gelen araç taleplerinin mevzuat ve imkânlar çerçevesinde karşılanması | c7 / → | 120.814.085,00 | 0,00 | -120.814.085,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T169 / Faaliyet maliyetleri → T169 / Faaliyet maliyetleri | r21 → r21 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 888.224.210,00 | 888.224.835,00 | 625,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c5 / 2028 Tahmin | 291.167.302,00 | 320.792.302,00 | 29.625.000,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r11 → r11 / BÜTÇE İÇİ TOPLAM KAYNAK | c4 / 2027 Bütçe | 888.224.210,00 | 888.224.835,00 | 625,00 |
| Mali Hizmetler Müdürlüğü | 222 → 222 | T170 / Ekonomik tablo → T170 / Ekonomik tablo | r13 → r13 / FAALİYET MALİYETİ TOPLAMI | c4 / 2027 Bütçe | 888.224.210,00 | 888.224.835,00 | 625,00 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c4 / 2025 Gerçekleşme | 17,840 | 17.840 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c5 / 2026 Planlanan | 50,000 | 50.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 50,000 | 50.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c7 / 2027 Hedef | 50,000 | 50.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c8 / 2028 Tahmin | 60,000 | 60.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r9 → r9 / SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı | c9 / 2029 Tahmin | 60,000 | 60.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r10 → r10 / SH16/PG03. Bölge geneli bitkisel ve yapısal peyzaj alanlarının bakımı ve onarımı | c8 / 2028 Tahmin | 12.110,000 | 12.110.000 | 12.097.890 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r10 → r10 / SH16/PG03. Bölge geneli bitkisel ve yapısal peyzaj alanlarının bakımı ve onarımı | c9 / 2029 Tahmin | 12.170,000 | 12.170.000 | 12.157.830 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c4 / 2025 Gerçekleşme | 132,915 | 132.915 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c5 / 2026 Planlanan | 250,000 | 250.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 250,000 | 250.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c7 / 2027 Hedef | 200,000 | 200.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c8 / 2028 Tahmin | 250.000,000 | 250.000 | 0 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r11 → r11 / SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı | c9 / 2029 Tahmin | 300,000 | 300.000 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r12 → r12 / SH016/PG04. İklime uygun, dayanıklı ve az su tüketen bitki dikim ve bakım sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 3.000,000 | 3000 | 0 |
| Park ve Bahçeler Müdürlüğü | 125 → 125 | T45 / Kart → T45 / Kart | r13 → r13 / SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 650,000 | 650 | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c5 / 2027 Bütçe | 528.076.250,00 | 543.583.357,00 | 15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c6 / 2028 Tahmin | 821.622.344,00 | 846.720.000,00 | 25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r41 → r41 / Toplam | c7 / 2029 Tahmin | 984.691.330,00 | 1.016.063.999,00 | 31.372.669,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c5 / 2027 Bütçe | 528.076.250,00 | 543.583.357,00 | 15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c6 / 2028 Tahmin | 821.622.344,00 | 846.720.000,00 | 25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r42 → r42 / Bütçe İçi | c7 / 2029 Tahmin | 984.691.330,00 | 1.016.063.999,00 | 31.372.669,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 551.300.000,00 | 566.807.107,00 | 15.507.107,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c6 / 2028 Tahmin | 850.652.032,00 | 875.749.688,00 | 25.097.656,00 |
| Park ve Bahçeler Müdürlüğü | 128 → 128 | T49 / Faaliyet maliyetleri → T49 / Faaliyet maliyetleri | r45 → r45 / Genel Bütçe Toplamı | c7 / 2029 Tahmin | 1.020.978.440,00 | 1.052.351.109,00 | 31.372.669,00 |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T59 / Faaliyet maliyetleri → T59 / Faaliyet maliyetleri | r5 → r5 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Plan Proje Müdürlüğü | 136 → 136 | T60 / Ekonomik tablo → T60 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 11.501.713,28 | 12.362.364,94 | 860.651,66 |
| Plan Proje Müdürlüğü | 136 → 136 | T60 / Ekonomik tablo → T60 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 11.501.713,28 | 12.362.364,94 | 860.651,66 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T151 / Faaliyet maliyetleri → T151 / Faaliyet maliyetleri | r11 → r11 / Toplam | c7 / 2029 Tahmin | 333.750,00 | 233.750,00 | -100.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T151 / Faaliyet maliyetleri → T151 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c7 / 2029 Tahmin | 333.750,00 | 233.750,00 | -100.000,00 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T152 / Ekonomik tablo → T152 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 955.735,48 | 936.918,72 | -18.816,76 |
| Rehberlik ve Teftiş Kurulu Müdürlüğü | 210 → 210 | T152 / Ekonomik tablo → T152 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 955.735,48 | 936.918,72 | -18.816,76 |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T13 / Faaliyet maliyetleri → T13 / Faaliyet maliyetleri | r17 → r17 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T14 / Ekonomik tablo → T14 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 4.815.578,31 | 5.151.457,55 | 335.879,24 |
| Ruhsat ve Denetim Müdürlüğü | 101 → 101 | T14 / Ekonomik tablo → T14 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 4.815.578,31 | 5.151.457,55 | 335.879,24 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c5 / 2027 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c6 / 2028 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r24 → r24 / Bütçe İçi | c7 / 2029 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c5 / 2027 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c6 / 2028 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r27 → r27 / Bütçe İçi | c7 / 2029 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c5 / 2027 Bütçe | 9.171.747,00 | 9.221.747,00 | 50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c6 / 2028 Tahmin | 9.476.838,00 | 9.576.838,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r35 → r35 / Toplam | c7 / 2029 Tahmin | 8.417.000,00 | 8.517.000,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c5 / 2027 Bütçe | 9.171.747,00 | 9.221.747,00 | 50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c6 / 2028 Tahmin | 9.476.838,00 | 9.576.838,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r36 → r36 / Bütçe İçi | c7 / 2029 Tahmin | 8.417.000,00 | 8.517.000,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c5 / 2027 Bütçe | 15.287.207,00 | 15.337.207,00 | 50.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c6 / 2028 Tahmin | 17.121.163,00 | 17.221.163,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T83 / Faaliyet maliyetleri → T83 / Faaliyet maliyetleri | r39 → r39 / Genel Bütçe Toplamı | c7 / 2029 Tahmin | 17.972.406,00 | 18.072.406,00 | 100.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T84 / Ekonomik tablo → T84 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 16.565.381,00 | 16.365.381,00 | -200.000,00 |
| Tarımsal Hizmetler Müdürlüğü | 156 → 156 | T84 / Ekonomik tablo → T84 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 16.565.381,00 | 16.365.381,00 | -200.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c5 / 2027 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c6 / 2028 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r13 → r13 / Bütçe Dışı | c7 / 2029 Tahmin | BOŞ | -0,00 | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r20 → r20 / Toplam | c7 / 2029 Tahmin | 124.817.216,00 | 124.625.000,00 | -192.216,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T23 / Faaliyet maliyetleri → T23 / Faaliyet maliyetleri | r21 → r21 / Bütçe İçi | c7 / 2029 Tahmin | 124.817.216,00 | 124.625.000,00 | -192.216,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 78.140.000,00 | 80.767.000,00 | 2.627.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | ₺10.424.938,95 | 10.424.938,95 | 0,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 78.140.000,00 | 80.767.000,00 | 2.627.000,00 |
| Veteriner İşleri Müdürlüğü | 107 → 107 | T24 / Ekonomik tablo → T24 / Ekonomik tablo | r9 → r9 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | ₺10.424.938,95 | 10.424.938,95 | 0,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r14 → r14 / 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması | c6 / 2028 Tahmin | 2.551.893,00 | 4.447.658,00 | 1.895.765,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r14 → r14 / 0005.4109 sayılı Kanun kapsamında asker ailelerine yapılacak yardım ile ilgili işlemlerin yapılması | c7 / 2029 Tahmin | 2.477.366,00 | 4.517.415,00 | 2.040.049,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c6 / 2028 Tahmin | 2.551.893,00 | 4.447.658,00 | 1.895.765,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r15 → r15 / Bütçe İçi | c7 / 2029 Tahmin | 2.477.366,00 | 4.517.415,00 | 2.040.049,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r32 → r32 / 0011.Evlilik Öncesi Bilgilendirme ve Rehberlik Hizmetleri | c5 / 2027 Bütçe | 304.600,00 | 300.000,00 | -4.600,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T179 / Faaliyet maliyetleri → T179 / Faaliyet maliyetleri | r33 → r33 / Bütçe İçi | c5 / 2027 Bütçe | 304.600,00 | 300.000,00 | -4.600,00 |
| Yazı İşleri Müdürlüğü | 228 → 228 | T180 / Ekonomik tablo → T180 / Ekonomik tablo | r7 → r7 / BÜTÇE İÇİ TOPLAM KAYNAK | c5 / 2028 Tahmin | 52.223.432,00 | 52.230.432,00 | 7.000,00 |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T19 / Faaliyet maliyetleri → T19 / Faaliyet maliyetleri | r29 → r29 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| Zabıta Müdürlüğü | 104 → 104 | T20 / Ekonomik tablo → T20 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 45.863.621,38 | 51.258.201,04 | 5.394.579,66 |
| Zabıta Müdürlüğü | 104 → 104 | T20 / Ekonomik tablo → T20 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 45.863.621,38 | 51.258.201,04 | 5.394.579,66 |
| Çevre Koruma ve Kontrol Müdürlüğü | 153 → 153 | T78 / Ekonomik tablo → T78 / Ekonomik tablo | r5 → r5 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 3.967.964,02 | 4.085.221,72 | 117.257,70 |
| Çevre Koruma ve Kontrol Müdürlüğü | 153 → 153 | T78 / Ekonomik tablo → T78 / Ekonomik tablo | r7 → r7 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 3.967.964,02 | 4.085.221,72 | 117.257,70 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c5 / 2027 Bütçe | 6.000.000,00 | 6.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c6 / 2028 Tahmin | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r2 → r2 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c7 / 2029 Tahmin | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c5 / 2027 Bütçe | 6.000.000,00 | 6.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c6 / 2028 Tahmin | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c7 / 2029 Tahmin | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c5 / 2027 Bütçe | 6.500.000,00 | 6.800.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c6 / 2028 Tahmin | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r5 → r5 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c7 / 2029 Tahmin | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c5 / 2027 Bütçe | 6.500.000,00 | 6.800.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c6 / 2028 Tahmin | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r6 → r6 / Bütçe İçi | c7 / 2029 Tahmin | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c5 / 2027 Bütçe | 7.750.000,00 | 8.050.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c6 / 2028 Tahmin | 8.862.500,00 | 9.162.500,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r8 → r8 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c7 / 2029 Tahmin | 8.503.125,00 | 8.803.125,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c5 / 2027 Bütçe | 7.750.000,00 | 8.050.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c6 / 2028 Tahmin | 8.862.500,00 | 9.162.500,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r9 → r9 / Bütçe İçi | c7 / 2029 Tahmin | 8.503.125,00 | 8.803.125,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c5 / 2027 Bütçe | 2.000.000,00 | 2.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c6 / 2028 Tahmin | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r11 → r11 / 0004.Paydaş Talep ve İlişki Yönetimi | c7 / 2029 Tahmin | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c5 / 2027 Bütçe | 2.000.000,00 | 2.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c6 / 2028 Tahmin | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r12 → r12 / Bütçe İçi | c7 / 2029 Tahmin | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c5 / 2027 Bütçe | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c6 / 2028 Tahmin | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r14 → r14 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c7 / 2029 Tahmin | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c2 / 2026 Bütçe | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c3 / 2026 Haziran Sonu Harcama | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c4 / 2026 Yıl Sonu Harcama Tahmini | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c5 / 2027 Bütçe | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c6 / 2028 Tahmin | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r15 → rYOK / Bütçe İçi | c7 / 2029 Tahmin | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c2 / 2026 Bütçe | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c3 / 2026 Haziran Sonu Harcama | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c4 / 2026 Yıl Sonu Harcama Tahmini | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c5 / 2027 Bütçe | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c6 / 2028 Tahmin | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r16 → rYOK / Bütçe Dışı | c7 / 2029 Tahmin | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c2 / 2026 Bütçe | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c3 / 2026 Haziran Sonu Harcama | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c4 / 2026 Yıl Sonu Harcama Tahmini | - | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c5 / 2027 Bütçe | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c6 / 2028 Tahmin | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r17 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c7 / 2029 Tahmin | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r18 → r15 / Bütçe İçi | c5 / 2027 Bütçe | 1.500.000,00 | 300.000,00 | -1.200.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r18 → r15 / Bütçe İçi | c6 / 2028 Tahmin | 1.500.000,00 | 300.000,00 | -1.200.000,00 |
| Özel Kalem Müdürlüğü | 199 → 199 | T137 / Faaliyet maliyetleri → T137 / Faaliyet maliyetleri | r18 → r15 / Bütçe İçi | c7 / 2029 Tahmin | 1.500.000,00 | 300.000,00 | -1.200.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c5 / → | 6.000.000,00 | 6.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c6 / → | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r3 → r3 / 0001.Üst Yönetim Program ve Randevu Yönetimi | c7 / → | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c5 / → | 6.500.000,00 | 6.800.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c6 / → | 7.300.000,00 | 7.600.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r4 → r4 / 0002.Kurumsal İletişim ve Temsil Süreçleri Koordinasyonu | c7 / → | 7.050.000,00 | 7.350.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c5 / → | 7.750.000,00 | 8.050.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c6 / → | 8.862.500,00 | 9.162.500,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r5 → r5 / 0003.Protokol ve Resmi Organizasyon Yönetimi | c7 / → | 8.503.125,00 | 8.803.125,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c5 / → | 2.000.000,00 | 2.300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c6 / → | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r6 → r6 / 0004.Paydaş Talep ve İlişki Yönetimi | c7 / → | 2.800.000,00 | 3.100.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c5 / → | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c6 / → | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r7 → r7 / 0005.Veri Temelli Hizmet İyileştirme ve Kök Neden Analizler | c7 / → | 0,00 | 300.000,00 | 300.000,00 |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c2 / → | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c3 / → | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c4 / → | 0,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c5 / → | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c6 / → | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| Özel Kalem Müdürlüğü | 198 → 198 | T136 / Kart faaliyet üyeliği → T136 / Kart faaliyet üyeliği | r8 → rYOK / 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | c7 / → | 1.500.000,00 | YOK (satır/hücre yok) | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T43 / Faaliyet maliyetleri → T43 / Faaliyet maliyetleri | r41 → r41 / Toplam | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| İmar ve Şehircilik Müdürlüğü | 122 → 122 | T44 / Ekonomik tablo → T44 / Ekonomik tablo | r6 → r6 / BÜTÇE DIŞI TOPLAM KAYNAK | c2 / 2026 Bütçe | BOŞ | -0,00 | Hesaplanamaz |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 203 → 203 | T144 / Ekonomik tablo → T144 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 13.287.541,43 | 18.811.107,22 | 5.523.565,79 |
| İnsan Kaynakları ve Eğitim Müdürlüğü | 203 → 203 | T144 / Ekonomik tablo → T144 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 13.287.541,43 | 18.811.107,22 | 5.523.565,79 |
| İşletme ve İştirakler Müdürlüğü | 238 → 238 | T189 / Kart → T189 / Kart | r9 → r9 / SH61/PG01. Çocuk Bakım evlerinden yararlanan velilerin memnuniyet oranı | c9 / 2029 Tahmin | 7500 | 98 | -7.402 |
| İşletme ve İştirakler Müdürlüğü | 239 → 239 | T191 / Kart → T191 / Kart | r9 → r9 / SH62/PG01. Kadın kooperatifleri sayısının toplam tedarikçiye oranı | c9 / 2029 Tahmin | 7500 | 98 | -7.402 |
| İşletme ve İştirakler Müdürlüğü | 239 → 239 | T191 / Kart → T191 / Kart | r10 → r10 / SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı | c6 / 2026 Yıl Sonu Gerçekleşme Tahmini | 1 100 | 1.100 | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 239 → 239 | T191 / Kart → T191 / Kart | r10 → r10 / SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı | c7 / 2027 Hedef | 1 200 | 1.200 | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 239 → 239 | T191 / Kart → T191 / Kart | r10 → r10 / SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı | c9 / 2029 Tahmin | 10500 | 1.500 | -9.000 |
| İşletme ve İştirakler Müdürlüğü | 240 → 240 | T193 / Kart → T193 / Kart | r9 → r9 / SH63/PG01. İktisadi işletme toplam gelirlerinin kurumun toplam gelirine oranı | c9 / 2029 Tahmin | 7500 | 2,75 | -7.497,25 |
| İşletme ve İştirakler Müdürlüğü | 240 → 240 | T193 / Kart → T193 / Kart | r10 → r10 / SH63/PG02. İktisadi işletmeden edilen giderlerinin gelirlerine oranı (Personel hariç) | c9 / 2029 Tahmin | 95 | 57,50 | -37,5 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r2 → r2 / 0001.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek | c5 / 2027 Bütçe | 43.465.000,00 | 44.032.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r3 → r3 / Bütçe İçi | c5 / 2027 Bütçe | 43.465.000,00 | 44.032.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c2 / 2026 Bütçe | BOŞ | - | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c3 / 2026 Haziran Sonu Harcama | BOŞ | - | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r5 → r5 / 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, | c4 / 2026 Yıl Sonu Harcama Tahmini | BOŞ | - | Hesaplanamaz |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r17 → r17 / Toplam | c5 / 2027 Bütçe | 84.375.000,00 | 84.942.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r18 → r18 / Bütçe İçi | c5 / 2027 Bütçe | 84.375.000,00 | 84.942.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T195 / Faaliyet maliyetleri → T195 / Faaliyet maliyetleri | r20 → r20 / Personel ve SGK Giderleri Toplamı | c5 / 2027 Bütçe | 10.979.000,00 | 10.412.000,00 | -567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r2 → r2 / Personel Giderleri | c2 / 2026 Bütçe | 58.995.430,00 | 0,00 | -58.995.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r2 → r2 / Personel Giderleri | c3 / 2026 Haziran Sonu Harcama | 29.032.954,0 | 0,00 | -29.032.954,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r3 → r3 / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | c2 / 2026 Bütçe | 7.400.000,00 | 0,00 | -7.400.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r3 → r3 / Sosyal Güvenlik Kurumuna Devlet Primi Giderleri | c3 / 2026 Haziran Sonu Harcama | 3.940.031,2 | 0,00 | -3.940.031,20 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c2 / 2026 Bütçe | 64.330.000,00 | 0,00 | -64.330.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c3 / 2026 Haziran Sonu Harcama | 18.209.313,23 | 0,00 | -18.209.313,23 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r4 → r4 / Mal ve Hizmet Alım Giderleri | c4 / 2027 Bütçe | 84.375.000,00 | 84.942.000,00 | 567.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r5 → r5 / Cari Transferler | c2 / 2026 Bütçe | 1.500.000,0 | 0,00 | -1.500.000,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r5 → r5 / Cari Transferler | c3 / 2026 Haziran Sonu Harcama | 1.368.984,7 | 0,00 | -1.368.984,70 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c2 / 2026 Bütçe | 130.725.430,0 | 0,00 | -130.725.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r6 → r6 / BÜTÇE İÇİ TOPLAM KAYNAK | c3 / 2026 Haziran Sonu Harcama | 52.551.283,3 | 0,00 | -52.551.283,30 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c2 / 2026 Bütçe | 130.725.430,0 | 0,00 | -130.725.430,00 |
| İşletme ve İştirakler Müdürlüğü | 241 → 241 | T196 / Ekonomik tablo → T196 / Ekonomik tablo | r8 → r8 / FAALİYET MALİYETİ TOPLAMI | c3 / 2026 Haziran Sonu Harcama | 52.551.283,3 | 0,00 | -52.551.283,30 |
| İşletme ve İştirakler Müdürlüğü | 238 → 238 | T190 / Kart faaliyet üyeliği → T190 / Kart faaliyet üyeliği | r3 → r3 / 0011.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek → 0001.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek | c5 / → | 43.465.000,00 | 44.032.000,00 | 567.000,00 |
| Kurum / diğer | 244 → 244 | EKONOMİK KOD → EKONOMİK KOD | r5 → r5 / Mal ve Hizmet Alım Giderleri | c5 / → | 5.179.079.860,00 | 5.054.079.860,00 | -125.000.000,00 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r38 → r38 / 37 | c5 / MODEL | 2008 | 2026 | 18 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r39 → r39 / 38 | c5 / MODEL | 2012 | 2008 | -4 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r40 → r40 / 39 | c5 / MODEL | 2006 | 2012 | 6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r41 → r41 / 40 | c5 / MODEL | 2012 | 2006 | -6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r42 → r42 / 41 | c5 / MODEL | 2006 | 2012 | 6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r45 → r45 / 44 | c5 / MODEL | 2009 | 2006 | -3 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r46 → r46 / 45 | c5 / MODEL | 2006 | 2009 | 3 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r47 → r47 / 46 | c5 / MODEL | 2021 | 2006 | -15 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r49 → r49 / 48 | c5 / MODEL | 2006 | 2021 | 15 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r50 → r50 / 49 | c5 / MODEL | 1996 | 2006 | 10 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r51 → r51 / 50 | c5 / MODEL | 2018 | 1996 | -22 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r52 → r52 / 51 | c5 / MODEL | 2006 | 2018 | 12 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r53 → r53 / 52 | c5 / MODEL | 2007 | 2006 | -1 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r54 → r54 / 53 | c5 / MODEL | 2010 | 2007 | -3 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r55 → r55 / 54 | c5 / MODEL | 2020 | 2010 | -10 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r58 → r58 / 57 | c5 / MODEL | 2026 | 2020 | -6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r59 → r59 / 58 | c5 / MODEL | 2005 | 2026 | 21 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r60 → r60 / 59 | c5 / MODEL | 2009 | 2005 | -4 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r63 → r63 / 62 | c5 / MODEL | 2012 | 2009 | -3 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r64 → r64 / 63 | c5 / MODEL | 2008 | 2012 | 4 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r65 → r65 / 64 | c5 / MODEL | 2006 | 2008 | 2 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r66 → r66 / 65 | c5 / MODEL | 2018 | 2006 | -12 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r77 → r77 / 76 | c5 / MODEL | 2022 | 2018 | -4 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r78 → r78 / 77 | c5 / MODEL | 2020 | 2022 | 2 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r103 → r103 / 102 | c5 / MODEL | 2026 | 2020 | -6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r109 → r109 / 108 | c5 / MODEL | 2020 | 2026 | 6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r113 → r113 / 112 | c5 / MODEL | 2023 | 2020 | -3 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r114 → r114 / 113 | c5 / MODEL | 2006 | 2023 | 17 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r115 → r115 / 114 | c5 / MODEL | 2021 | 2006 | -15 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r116 → r116 / 115 | c5 / MODEL | 2011 | 2021 | 10 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r117 → r117 / 116 | c5 / MODEL | 2010 | 2011 | 1 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r118 → r118 / 117 | c5 / MODEL | 2016 | 2010 | -6 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | r119 → r119 / 118 | c5 / MODEL | 2014 | 2016 | 2 |
| Kurum / diğer | 46 → 46 | Başlıksız tablo → Başlıksız tablo | rYOK → r120 / 119 | c5 / MODEL | YOK (satır/hücre yok) | 2014 | Hesaplanamaz |

## Kitap kontrolü ve gönderime hazırlık

Kitap kontrol maddesi: **153 → 35**; gönderime hazır müdürlük: **5/34 → 17/34**.

Mesajlar: kitap 432 → 111; yalnız program grubu 112 → 140; SYSTEM 10 → 1.

Eski 153 madde: **124 çözüldü, 29 açık**. **6 yeni madde** var. Kimlik müdürlük + kontrol başlığı/yılıdır; durum aynı kontrol alanının geçip geçmediğini gösterir, gerekçe ve tutar değişmiş olabilir. Örneğin Sağlık toplam etiketi düzelmiştir; 2026 Haziran ve 2029 ekonomik kontrolleri yeni aritmetik farklar nedeniyle açık kalır. Kurum özet bulguları bu sayıya dahil değildir.

| Durum | Müdürlük | Kontrol maddesi | Eski sayfa / tablo / hücre | Yeni sayfa / tablo / hücre |
| --- | --- | --- | --- | --- |
| Çözüldü | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2027 Bütçe | s.144 / T69 / sütun 5 / satır 44,45,46 | YOK |
| Çözüldü | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2028 Tahmin | s.144 / T69 / sütun 6 / satır 44,45,46 | YOK |
| Çözüldü | Afet İşleri ve Risk Yönetimi Müdürlüğü | 0015.Kurum Personelinin Afet Eğitimi Projesi · 2029 Tahmin | s.144 / T69 / sütun 7 / satır 44,45,46 | YOK |
| Çözüldü | Afet İşleri ve Risk Yönetimi Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.144 / T70 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Araştırma ve Geliştirme Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.195 / T134 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Bilgi İşlem Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.207 / T148 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Bilgi İşlem Müdürlüğü | Ekonomik tablo · 2029 Tahmin | s.207 / T148 / sütun 6 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Bilgi İşlem Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.207 / T147 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.207 / T148 / sütun 4 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Bütçe | s.186 / T119 / sütun 2 / satır 17,18,19 | YOK |
| Çözüldü | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Haziran Sonu Harcama | s.186 / T119 / sütun 3 / satır 17,18,19 | YOK |
| Çözüldü | Dış İlişkiler Müdürlüğü | 0006.Uluslararası kuruluşlar ve belediye ağları ile kurumsal ilişkilerin sürdürülmesi · 2026 Yıl Sonu Tahmini | s.186 / T119 / sütun 4 / satır 17,18,19 | YOK |
| Çözüldü | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2027 Bütçe | s.112 / T29 / sütun 5 / satır 14,15,16 | YOK |
| Çözüldü | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2028 Tahmin | s.112 / T29 / sütun 6 / satır 14,15,16 | YOK |
| Çözüldü | Emlak İstimlak Müdürlüğü | 0005.4734 sayılı yasa kapsamında mal ve/veya hizmet alımı ihale işlemlerinin yapılması · 2029 Tahmin | s.112 / T29 / sütun 7 / satır 14,15,16 | YOK |
| Çözüldü | Emlak İstimlak Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.112 / T30 / sütun 3 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Fen İşleri Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.118 / T38 / sütun 2 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Gelirler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.232 / T184 / sütun 2 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Gelirler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.232 / T184 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.173 / T106 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.173 / T106 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Halkla İlişkiler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.192 / T130 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Bütçe | s.212 / T155 / sütun 2 / satır 17,18,19 | YOK |
| Çözüldü | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Haziran Sonu Harcama | s.212 / T155 / sütun 3 / satır 17,18,19 | YOK |
| Çözüldü | Hukuk İşleri Müdürlüğü | 0006. Kamu kaynaklarının etkin kullanımı için sulh ve uzlaşma yöntemleri yaygınlaştırılacaktır · 2026 Yıl Sonu Tahmini | s.212 / T155 / sütun 4 / satır 17,18,19 | YOK |
| Çözüldü | Kentsel Dönüşüm Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.139 / T64 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2028 Tahmin | s.167 / T99 / sütun 6 / satır 8,9,10 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0003.İş Birliği ve Ortaklıklar: Öğretim Kurumları, teknoloji transfer ofisleri, sivil toplum kuruluşları ve özel sektörle iş birliği yapmak. · 2029 Tahmin | s.167 / T99 / sütun 7 / satır 8,9,10 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 11,12,13 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 11,12,13 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0004.Ulusal ve Uluslararası Etkinlikler: Ulusal ve uluslararası festivaller, fuarlar ve etkinliklere katılım ve düzenleme. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 11,12,13 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 14,15,16 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 14,15,16 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0005.Sanatsal Eğitimler: Sahne sanatları eğitimleri, el sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında atölye, çalıştay ve gösteriler düzenleme. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 14,15,16 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 17,18,19 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 17,18,19 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0006.Sanatsal Etkinlikler: Kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kültür Park, Büyükçekmece Kordon ve Albatros sahili) · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 17,18,19 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 20,21,22 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 20,21,22 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0007.Uluslararası Fotoğraf Yarışması: Dünyanın farklı coğrafyalarından fotoğrafçılarının özgün bakış açılarını ve yaratıcı anlatımı teşvik etmek, profesyonel ve amatör tüm fotoğrafçılara kendilerini ifade etme fırsatı sunmak için platform oluşturmak. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 20,21,22 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 23,24,25 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 23,24,25 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0008.Toplumsal Etkinlikler: Önemli gün ve bayramlarda etkinlikler düzenlemek · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 23,24,25 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 26,27,28 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 26,27,28 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0009.Sanatsal Etkinlikler: Marmara Denizi kıyısında kültürel ve sanatsal etkinlikler düzenlemek (Büyükçekmece Gölü, Kıyı Marina ve Albatros sahili) · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 26,27,28 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 29,30,31 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 29,30,31 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0010.Kent Tiyatroları Sezon Programı: Her yaş grubu için yıl boyunca düzenli tiyatro oyunlarının sergilenmesi · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 29,30,31 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 32,33,34 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 32,33,34 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0011.Okullara Yönelik Rehberli Müze Turları: İlçemizdeki okullarla iş birliği içerisinde yürütülen rehberli müze gezileri · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 32,33,34 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 35,36,37 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 35,36,37 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0012.Atölye Çalışmaları: Çocuk, Genç ve yetişkinlere yönelik atölye çalışmaları · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 35,36,37 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 38,39,40 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 38,39,40 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0013.Meslek Kursları: Yabancı dil eğitimleri, teknoloji eğitimleri, güzellik hizmetleri eğitimleri, mutfak sanatları eğitimleri vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 38,39,40 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 41,42,43 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 41,42,43 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0014.Sahne Sanatları Kursları: Türk Halk Oyunları, modern dans, bale, tiyatro, enstrüman vb. kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 41,42,43 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 44,45,46 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 44,45,46 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0015.Örgün Eğitime Destek ve Sınavlara Hazırlık Kursları: Dezavantajlı bölgelerde yaşayan öğrenciler için örgün eğitimlerine destek ve sınavlara hazırlık kursları düzenlemek. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 44,45,46 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 47,48,49 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 47,48,49 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0016.Teknoloji Eğitimleri: Yapay zeka, yazılım, kodlama, web sayfası ve grafik tasarım gibi alanlarda kurslar düzenlemek. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 47,48,49 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Bütçe | s.167 / T99 / sütun 2 / satır 50,51,52 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Haziran Sonu Harcama | s.167 / T99 / sütun 3 / satır 50,51,52 | YOK |
| Çözüldü | Kültür, Sanat ve Sosyal İşler Müdürlüğü | 0017. Sanatsal Eğitimler: El sanatları, güzel sanatlar, unutulmaya yüz tutmuş görsel-dramatik sanatlar (fotoğraf, sinema vb.) alanında gösteriler ve yaz okulları düzenleme. · 2026 Yıl Sonu Tahmini | s.167 / T99 / sütun 4 / satır 50,51,52 | YOK |
| Çözüldü | Makine İkmal Bakım ve Onarım Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Makine İkmal Bakım ve Onarım Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.236 / T187 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.236 / T188 / sütun 5 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Mali Hizmetler Müdürlüğü | Ekonomik tablo · 2027 Bütçe | s.222 / T170 / sütun 4 / satır 2,3,4,5,6,7,8,9,10,11,12,13 | YOK |
| Çözüldü | Mali Hizmetler Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.222 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13 | YOK |
| Çözüldü | Mali Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.222 / T169 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.222 / T170 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2025 Gerçekleşme | s.125 / T45 / sütun 4 / satır 11 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Planlanan | s.125 / T45 / sütun 5 / satır 11 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2026 Yıl Sonu Tahmini | s.125 / T45 / sütun 6 / satır 11 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2027 Hedef | s.125 / T45 / sütun 7 / satır 11 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG03. Bitkisel peyzaj elemanlarının dikim ve bakım sayısı · 2029 Tahmin | s.125 / T45 / sütun 9 / satır 11 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH016/PG05. Onaylanan Peyzaj Proje ve İskân Sayısı · 2026 Yıl Sonu Tahmini | s.125 / T45 / sütun 6 / satır 13 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2025 Gerçekleşme | s.125 / T45 / sütun 4 / satır 9 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Planlanan | s.125 / T45 / sütun 5 / satır 9 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2026 Yıl Sonu Tahmini | s.125 / T45 / sütun 6 / satır 9 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2027 Hedef | s.125 / T45 / sütun 7 / satır 9 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2028 Tahmin | s.125 / T45 / sütun 8 / satır 9 | YOK |
| Çözüldü | Park ve Bahçeler Müdürlüğü | SH16.PG01. Bitkisel ve yapısal peyzaj düzenlemelerinin yapımı · 2029 Tahmin | s.125 / T45 / sütun 9 / satır 9 | YOK |
| Çözüldü | Plan Proje Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.136 / T60 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Rehberlik ve Teftiş Kurulu Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.210 / T152 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Ruhsat ve Denetim Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.101 / T14 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2027 Bütçe | s.156 / T83 / sütun 5 / satır 23,24,25 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2028 Tahmin | s.156 / T83 / sütun 6 / satır 23,24,25 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0008.Üretim alanlarının hazırlanması, üretim materyal ve ekipmanlarının temini · 2029 Tahmin | s.156 / T83 / sütun 7 / satır 23,24,25 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2027 Bütçe | s.156 / T83 / sütun 5 / satır 26,27,28 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2028 Tahmin | s.156 / T83 / sütun 6 / satır 26,27,28 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | 0009.Üretimin zehirsiz gıda, toprak kirliliği önleyici ve çevre korunma etmenlerinin önemi çerçevesinde tasarruflu ve sürdürülebilir olarak yürütülmesi · 2029 Tahmin | s.156 / T83 / sütun 7 / satır 26,27,28 | YOK |
| Çözüldü | Tarımsal Hizmetler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.156 / T84 / sütun 2 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2027 Bütçe | s.107 / T23 / sütun 5 / satır 11,12,13 | YOK |
| Çözüldü | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2028 Tahmin | s.107 / T23 / sütun 6 / satır 11,12,13 | YOK |
| Çözüldü | Veteriner İşleri Müdürlüğü | 0004.Mevcut barınak kapasitesinin artırılması ve teknik altyapının iyileştirilmesini sağlamak. · 2029 Tahmin | s.107 / T23 / sütun 7 / satır 11,12,13 | YOK |
| Çözüldü | Veteriner İşleri Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.107 / T24 / sütun 2 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Yazı İşleri Müdürlüğü | Ekonomik tablo · 2028 Tahmin | s.228 / T180 / sütun 5 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Yazı İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.228 / T179 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 4 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Yazı İşleri Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.228 / T179 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.228 / T180 / sütun 6 / satır 2,3,4,5,6,7,8,9 | YOK |
| Çözüldü | Zabıta Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.104 / T20 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | Çevre Koruma ve Kontrol Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.153 / T78 / sütun 3 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | Özel Kalem Müdürlüğü | 0006.Sosyal Güvenlik Kurumuna 5434 Sayılı Kanun Kapsamında Emekli İkramiyeleri Karşılığı Yapılan Ödemeler | s.199 / T137 / sütun 1 / satır 17,25,35 | YOK |
| Çözüldü | İmar ve Şehircilik Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.122 / T44 / sütun 2 / satır 2,3,4,5,6,7 | YOK |
| Çözüldü | İnsan Kaynakları ve Eğitim Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.203 / T144 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Bütçe | s.241 / T195 / sütun 2 / satır 5,6,7 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Haziran Sonu Harcama | s.241 / T195 / sütun 3 / satır 5,6,7 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | 0002.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek, · 2026 Yıl Sonu Tahmini | s.241 / T195 / sütun 4 / satır 5,6,7 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | 0033.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek. | s.241 / T195 / sütun 1 / satır 8,22,32 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2026 Bütçe | s.241 / T196 / sütun 2 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2026 Haziran Sonu Harcama | s.241 / T196 / sütun 3 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2027 Bütçe | s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 5 / satır 20 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Personel/SGK toplam farkı · 2027 | s.241 / T195 / sütun 5 / satır 20; s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2026 Yıl Sonu Tahmini | s.239 / T191 / sütun 6 / satır 10 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | SH62/PG02. Satış Mağazasında satışa sunulan ürün çeşidi sayısı · 2027 Hedef | s.239 / T191 / sütun 7 / satır 10 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Tablo 190, satır 3: İşletme ve İştirakler Müdürlüğü / 0011.Çocuk Bakımevleri ile Çocuk Oyun ve Etkinlik Merkezlerinde çocuklara yönelik olarak okul öncesinde sosyal uyumu sağlamaya, motor ve bilişsel becerilerini geliştirmeye yönelik programları gerçekleştirmek: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | s.238 / T190 / sütun 1 / satır 3 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Tablo 192, satır 3: İşletme ve İştirakler Müdürlüğü / 0012.Kadın kooperatifleri, kadın üreticiler, yerel üreticiler ile diğer kooperatiflerin ürettiği sağlıklı, ekonomik ve güvenilir ürünlerin satışa sunulduğu Büyükçekmece’den Tarım Market mağazasını işletmek,: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | s.239 / T192 / sütun 1 / satır 3 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Tablo 192, satır 4: İşletme ve İştirakler Müdürlüğü / 0013.Yerel üreticilerle birlikte ilçede yetişen tarımsal ürünleri işleyerek katma değeri daha yüksek ürün haline getirmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | s.239 / T192 / sütun 1 / satır 4 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Tablo 194, satır 3: İşletme ve İştirakler Müdürlüğü / 0014.Belediyeye bağlı iktisadi işletme şubelerinin (sosyal tesis, otopark, düğün salonu vb.) işletmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | s.240 / T194 / sütun 1 / satır 3 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Tablo 194, satır 4: İşletme ve İştirakler Müdürlüğü / 0015.Vergi beyannameleri, müşavirlik, eğitim vb. çeşitli ödemeleri zamanında eksiksiz ve tam olarak yürütmek.: faaliyet maliyet kaydı tekil eşleşmedi. Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin. | s.240 / T194 / sütun 1 / satır 4 | YOK |
| Çözüldü | İşletme ve İştirakler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | s.241 / T195 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 4 / satır 2,3,4,5,6,7,8 | YOK |
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
| Açık | Özel Kalem Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.199 / T137 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23; s.199 / T138 / sütun 5 / satır 2,3,4,5,6,7,8 | s.199 / T137 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | Özel Kalem Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.199 / T137 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23; s.199 / T138 / sütun 6 / satır 2,3,4,5,6,7,8 | s.199 / T137 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.199 / T138 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | İnsan Kaynakları ve Eğitim Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8 | s.203 / T143 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,35; s.203 / T144 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Açık | İşletme ve İştirakler Müdürlüğü | Ekonomik tablo · 2029 Tahmin | s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 7 / satır 20 | s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8; s.241 / T195 / sütun 7 / satır 20 |
| Açık | İşletme ve İştirakler Müdürlüğü | Personel/SGK toplam farkı · 2029 | s.241 / T195 / sütun 7 / satır 20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 | s.241 / T195 / sütun 7 / satır 20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Açık | İşletme ve İştirakler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | s.241 / T195 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 | s.241 / T195 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,20; s.241 / T196 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Yeni | Dış İlişkiler Müdürlüğü | Ekonomik tablo · 2028 Tahmin | YOK | s.186 / T120 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Yeni | Gençlik ve Spor İşleri Müdürlüğü | Ekonomik tablo · 2029 Tahmin | YOK | s.173 / T106 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Yeni | Makine İkmal Bakım ve Onarım Müdürlüğü | Ekonomik tablo · 2029 Tahmin | YOK | s.236 / T188 / sütun 6 / satır 2,3,4,5,6,7,8 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2027 | YOK | s.156 / T83 / sütun 5 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 4 / satır 2,3,4,5,6,7,8 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2028 | YOK | s.156 / T83 / sütun 6 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 5 / satır 2,3,4,5,6,7,8 |
| Yeni | Tarımsal Hizmetler Müdürlüğü | Çapraz maliyet/toplam farkı · 2029 | YOK | s.156 / T83 / sütun 7 / satır 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,38; s.156 / T84 / sütun 6 / satır 2,3,4,5,6,7,8 |

## Okuma sınırları, kaynak sorunları ve teyit

Onaylı PDF bu çalışmada ayrıca açılıp doğrulanmadı; PDF ile eşleşme bilgisi görevde verilen D-320 teyididir. IDML SHA256 değeri doğrulandı. Çok sayfalı story için ilk basılı sayfa gösterilir; InDesign dizgi motoru kullanılmadığından hücrenin kesin devam sayfası doğrulanamaz.

Özel Kalem’de 0006 emekli ikramiyesi maliyet satırı onaylı kaynakta vardır: faaliyet sayısının 290’dan 291’e çıkması bu satırdır; maliyet uydurulmadı. Sağlık ekonomik tablosunun eski BOŞ toplam etiketi onaylı kaynakta “BÜTÇE İÇİ TOPLAM KAYNAK” olmuştur; aynı tutarın artık tanınması sayısal düzeltmeyle karıştırılmamalıdır.

İşletme ve İştirakler’de basılı kart üyelik kodları 0011/0012/0013/0014/0015, maliyet kodları 0001/0002/0033/0004/0005’tir. Tekil kod eşlemesi beş faaliyeti bağlayamaz: 5 üyelik kontrol maddesi ve 10 SYSTEM bağlantı mesajı vardır. Bu, kaynak kod uyuşmazlığıdır; parser kusuru olduğu kanıtlanmadı. Kodlar düzeltilmedi, ad benzerliğiyle bağlanmadı, tablo dışlanmadı.

Diğer çözülmemiş SYSTEM bulguları onaylı dry-run’da ayrı listelenir. Bu görevde pasteboard dışında kanıtlanmış parser kusuru düzeltilmedi. Belirsiz sayı biçimi, eksik kaynak ve doğrulama sorunları raporda korunur. Canlı veritabanına bağlanılmadı.

`2027-performans-programi_ONAYLI.idml`: kurum 1036 PASS / 184 FAIL; sınıflar {'BOOK': 53, 'UNKNOWN': 27, 'CHECK': 104}. Geometriyle dışlanan: 7 pasteboard + 4 yerleşimsiz tablo.

`SONN.idml`: kurum 1036 PASS / 184 FAIL; sınıflar {'BOOK': 53, 'UNKNOWN': 27, 'CHECK': 104}. Geometriyle dışlanan: 2 pasteboard + 4 yerleşimsiz tablo.
