# CI güvenlik ve hata notları

`security.yml` içindeki `secrets` işi her PR'ın `base..head` commit'lerini
gitleaks 8.30.0 CLI ile tarar; bulgu işi başarısız yapar. Silinmiş bir ara
commit'teki sır da yakalanır. İndirme SHA-256 ile doğrulanır; çıktı tamamen
maskelenir. `gitleaks:allow` yorumları dikkate alınmaz. Birleştirmeyi zorunlu
engellemek için depo kuralları `secrets` kontrolünü gerekli kontrol yapmalıdır.

İzin listesi yalnız tam eşleşen `disposable_test_only` ve
`tests/test_live_pilot_hardening.py` içindeki tarihsel, sahte giriş parolasını
kapsar. Dosyanın tamamı veya gerçek anahtarlar kapsam dışı bırakılmaz.

Aynı iş, workflow dosyaları değiştiğinde SHA-256 doğrulanmış actionlint 1.7.7
çalıştırır. Bulgular `warning` notudur; `continue-on-error` nedeniyle engellemez.
Yardımcıların standart kütüphane birim testleri de bu işte çalışır.

Test komutu, seçim, shard ve süreler korunur. Küçük pytest eklentisi xdist ana
sürecine gelen hataları shard'a özel geçici JSON'a yazar. Başarısızlık sonrası
adım test kimliği, dosyası, bir tabanlı satırı ve istisnanın ilk 10 satırını
`error` notu yapar. Kurulum/temizlik hataları da dahildir. Shard başına en çok
50 not vardır; runner'ın adım başına 10 hata sınırı için beş küçük adım kullanılır.
50'den fazla test hatasında önce toplam sayılı özet, sonra 49 test yazılır.
Ana süreç zorla öldürülürse rapor oluşmayabilir; adım bunu uyarır.

Lead, log indirmeden check sonucunu ve
`GET /repos/dursuncavus/civensa/check-runs/{id}/annotations` yanıtını okuyabilir.
Yerel doğrulama: `python -m unittest discover -s ops/ci -p 'test_*.py' -v`.
pytest-xdist kuruluysa gerçek dört worker ile bütünleşme kanıtı da çalışır.
