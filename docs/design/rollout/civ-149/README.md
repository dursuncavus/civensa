# CIV-149 · Gönderim yetkisi buton rengi

Yetkili gönderim düğmesi, Kullanıcılar ekranındakiyle aynı başarı renklerini kullanır (`--success`, `--success-bg`). Yetkisiz düğmenin mevcut varsayılan renkleri ve tüm düğme metinleri korunur. Durum, `/submit-authorizations` ekranında 1440px ve 390px genişliklerinde renkle ayırt edilir.

| Ekran | 1440px | 390px |
| --- | --- | --- |
| Yetkili ve yetkisiz satırlar | [Görüntüle](submit-authorizations-1440.png) | [Görüntüle](submit-authorizations-390.png) |

`tests/test_submit_authorizations_design.py` tarayıcı testi, her iki görünüm alanında yetkili/varsayılan düğme renklerini ve en az 4,5:1 metin kontrastını denetler; düğme çevrildikten sonra yeniden yüklenen ekranda rengin yeni yetki durumunu izlediğini doğrular.
