# CIV-180 sunum kanıtları

Görseller geçici PostgreSQL'deki sentetik **Test Belediyesi / Test Müdürlüğü 2027**
raporundan `/sunum.html` indirilerek oluşturuldu. Gerçek kurum verisi içermez.
Her PNG 1920×1080'dir. `pdf.png`, `#pdf` görünümünü ve yalnız ekranda görünen
Yazdır → PDF olarak kaydet yönlendirmesini gösterir; yönlendirme basılan PDF'de yoktur.

`single-file-size.txt` indirilen UTF-8 HTML'in bayt uzunluğudur. Üretilen HTML/PDF
depoya eklenmez. Tarayıcı testi PDF sayfa sayısını, 16:9 oranını, son rakamları,
gizlenen notları/düğmeleri ve görünür maddeleri ayrıca denetler.

Yeniden üretim (yalnız geçici PostgreSQL 16+ test bağlantısı yapılandırılmışken):

```sh
CIVENSA_SUNUM_ARTIFACTS=tests/artifacts/civ180 \
python -m pytest -q --require-postgres tests/test_sunum_browser.py
```

Yerel ortamın yönetilen Chromium politikası `file://` erişimini engellediği için
yerel üretimde `CIVENSA_SUNUM_HTTP_FIXTURE=1` kullanıldı. Bu seçenek aynı dosyanın
baytlarını Playwright yakalamasıyla sunar; ağ sunucusu veya dış kaynak yoktur,
tarayıcı bağlamı çevrimdışıdır. CI varsayılan olarak gerçek `file://` yolunu dener.
Edge üzerinde elle kontrol yapılmadı.
