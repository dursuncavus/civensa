# CIV-108 · Müdürlük ana sayfası görev listesi

022 için statik tasarım önerisi. Kaynak: CIV-107 araştırması, GOV.UK görev listesi yapısı (D-271/D-272); görsel dil: D-224 ve mevcut Civensa tokenları. Üç adım gerçek bir `ol` içinde, numarası, bağlantısı ve metinli durum etiketiyle gösterilir. Renk yalnız metni destekler.

Başlangıç: `feature/authorization-workflow-phase5`, `fcfa8a9`. Yalnız yeni 022 HTML, ekran kapsamlı CSS/JS ekleri, on yeni PNG ve bu belge değişir. Uygulama, testler, şablonlar ve token dosyası değişmez.

Üç görev bağlantısının uygulama hedefi `/department/1?period_id=1`; kimlikler sentetiktir. Ortak prototip davranışı bağlantıyı hedef penceresinde gösterir. Gönderim işlemi bu ekranda yapılmaz. Gerçek veri, API, depolama veya yeni çalışma zamanı bağımlılığı yoktur.

CIV-106 özeti korunur: 1280 px ve üzerinde sağda yapışkan 18rem sütun; altında üstte kompakt kartlar (760 px ve altında iki sütun). Gösterge sayısı 12; sorun sayısı duruma göre 0/3. Özet gönderim metinleri mevcut `status_label` ile uyumludur: Taslak / İncelemede / İade edildi. Görev satırı ise pakette istendiği gibi Gönderilmedi / Gönderildi / İade edildi — düzeltip yeniden gönderin der.

## Durumlar ve ekran görüntüleri

Chromium 151.0.7922.173; 1440×900 ve 390×900, DPR 1, tr-TR, Europe/Istanbul, açık tema ve azaltılmış hareket. PNG'ler tam sayfadır; mobilde ortak prototip kabuğunun alt menüsü de görünür. Her PNG 1.500.000 bayt sınırının altındadır.

| Durum | Veri girişi | Civensa kontrolü | Gönderim | 1440 px | 390 px |
| --- | --- | --- | --- | --- | --- |
| a · Yeni dönem | Başlanmadı | Bekliyor | Gönderilmedi | [PNG · 98,252 bayt](../../prototype/screenshots/022-department-home-a-1440.png) | [PNG · 92,325 bayt](../../prototype/screenshots/022-department-home-a-390.png) |
| b · Veri girişi sürüyor | Devam ediyor | Düzeltme gerekli · 3 gösterge | Gönderilmedi | [PNG · 101,191 bayt](../../prototype/screenshots/022-department-home-b-1440.png) | [PNG · 95,472 bayt](../../prototype/screenshots/022-department-home-b-390.png) |
| c · Giriş tamamlandı | Tamamlandı | Sorun yok | Gönderilmedi | [PNG · 99,201 bayt](../../prototype/screenshots/022-department-home-c-1440.png) | [PNG · 93,227 bayt](../../prototype/screenshots/022-department-home-c-390.png) |
| d · Gönderildi | Tamamlandı | Sorun yok | Gönderildi | [PNG · 97,506 bayt](../../prototype/screenshots/022-department-home-d-1440.png) | [PNG · 91,720 bayt](../../prototype/screenshots/022-department-home-d-390.png) |
| e · İade edildi | Devam ediyor | Düzeltme gerekli · 3 gösterge | İade edildi — düzeltip yeniden gönderin | [PNG · 102,817 bayt](../../prototype/screenshots/022-department-home-e-1440.png) | [PNG · 96,968 bayt](../../prototype/screenshots/022-department-home-e-390.png) |

Veri durumu varsayımları: a hiçbir değer girilmedi; b bazı zorunlu alanlar eksik ve 3 göstergede sorun var; c/d tüm zorunlu değerler tamam ve sorun yok; e düzeltme bekleyen 3 gösterge olduğu için veri girişi yeniden Devam ediyor. Bu veriler sabit örneklerdir, uygulama bağlamından hesaplanmaz. Onaylandı eşlemesi başarı rengiyle tanımlıdır; istenen beş durum içinde onaylanmış örnek bulunmaz.

## Kontrast

Mevcut `check_contrast.py` kolektörüyle beş durumda, 1440/390 ve 1279/1280 genişliklerinde gerçekte çizilen renkler ölçüldü. Yeni bir renk tanımlanmadı. Görev listesinin kullandığı çiftler:

| Ön plan | Arka plan | Kullanım | Oran | Sonuç |
| --- | --- | --- | ---: | --- |
| `--text-secondary` | `--surface-muted` | Başlanmadı / Devam ediyor / Bekliyor / Gönderilmedi / Gönderildi | 5,87:1 | Geçti |
| `--warning` | `--warning-bg` | Düzeltme gerekli / İade edildi | 5,41:1 | Geçti |
| `--success` | `--success-bg` | Tamamlandı / Sorun yok; Onaylandı için aynı çift | 4,71:1 | Geçti |
| `--accent` | `--surface` | Görev bağlantısı | 6,28:1 | Geçti |
| `--accent-hover` | `--surface` | Bağlantı üzerine gelme | 8,58:1 | Geçti |
| `--text` | `--surface` | Başlık / adım numarası | 15,80:1 | Geçti |
| `--text-secondary` | `--surface` | Yardım / özet etiketi | 6,87:1 | Geçti |
| `--warning` | `--surface` | Özette sorun sayısı | 5,93:1 | Geçti |

## Doğrulama

- Beş durum × dört genişlik: metinler, üç bağlantının aynı hedefe gitmesi, tek h1, etiketli alanlar, SVG kuralları ve yatay taşma kontrolü geçti. 390 px'te her durum etiketi adım adının altında; belge ve gövde genişliği tam 390 px.
- 1279/1280 px sınırında özetin üstteki kartlardan sağ sütuna geçişi doğrulandı.
- Klavyeyle durum seçimi, Tab ile görev bağlantısına erişim, Enter ile hedef penceresi, Escape ile kapanış ve odağın bağlantıya dönüşü geçti.
- Yerel fontlar beklendi; JavaScript hatası, dış ağ isteği veya GET dışında istek yok.
- Dört mevcut prototip ekranı × iki genişlik: temel daldaki CSS/JS ile bu değişiklikteki CSS/JS kullanılarak alınan PNG baytları aynı. Mevcut yerleşim/eleman eşleme ve menü/pencere/sekme/hover/odak kontrast kontrolleri de geçti.
- CI yardımcılarının yerel kontrolü: `python -m unittest discover -s ops/ci -p 'test_*.py' -q` — 9 test, 1 atlama, başarı. `python -m unittest ops.test_backup_security -q` — yerelde `age-keygen` bulunmadığı için 8 kurulum hatası; CI kendi age kurulumunu yapar.
- `git diff --check` geçti. PostgreSQL/pytest çalıştırılmadı: bu görev yalnız statik prototip; uygulama veya veritabanı başlatılmadı. Gerçek uygulama verisi, sunucu davranışı ve gerçek kullanıcı kullanılabilirlik testi bu prototiple doğrulanamaz.

Aşağıdaki komut depo kökünden çalıştırılır; mevcut yakalama betiğinin sunucusunu, Chromium ayarlarını, yerleşim kontrollerini ve kontrast kolektörünü kullanır. Yalnız CIV-108 PNG'lerini üretir; ortak manifesti veya eski görselleri değiştirmez. Playwright/Pillow/Chromium mevcut geliştirme araçlarıdır.

```bash
python - <<'PY_CAPTURE'
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('docs/design/prototype').resolve()))
from browser_helpers import ROOT,static_server,launch,context,MAX_PNG_BYTES
from capture_screenshots import assert_layout
from check_contrast import COLLECT,ratio,collect_states
from playwright.sync_api import sync_playwright,expect
from PIL import Image
expected={'a':['Başlanmadı','Bekliyor','Gönderilmedi'],'b':['Devam ediyor','Düzeltme gerekli · 3 gösterge','Gönderilmedi'],'c':['Tamamlandı','Sorun yok','Gönderilmedi'],'d':['Tamamlandı','Sorun yok','Gönderildi'],'e':['Devam ediyor','Düzeltme gerekli · 3 gösterge','İade edildi — düzeltip yeniden gönderin']}
results=[]; pairs={}
with static_server() as base,sync_playwright() as pw:
    browser=launch(pw)
    version=browser.version
    for width in (1440,390,1279,1280):
        ctx=context(browser,width); page=ctx.new_page(); errors=[]; requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def guard(route):
            if route.request.url.startswith(base+'/') and route.request.method=='GET':route.continue_()
            else:requests.append(route.request.url);route.abort()
        ctx.route('**/*',guard)
        page.goto(base+'/screens/022-department-home.html');page.evaluate('''() => Promise.all([400,500,600].map(w => document.fonts.load(w + ' 16px "Fira Sans"', 'İıŞşĞğÇçÖöÜü')))''')
        for state,tags in expected.items():
            page.select_option('#home-state',state)
            page.evaluate('document.fonts.ready')
            assert page.locator('.home-task-list .badge').all_text_contents()==tags
            assert_layout(page,width)
            assert page.locator('.home-task-list li').count()==3
            assert page.locator('.home-task-list a').evaluate_all('(els)=>els.every(e=>e.getAttribute("href")==="/department/1?period_id=1")')
            assert page.locator('.home-summary').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length') == (1 if width>=1280 else 2 if width<=760 else 3)
            for item in page.locator('.home-task-list li').all():
                a=item.locator('a').bounding_box(); b=item.locator('.badge').bounding_box()
                if width==390: assert b['y']>=a['y']+a['height']
                elif width>=1280:assert b['x']>a['x']
            assert page.evaluate('''()=>[...document.querySelectorAll('body *')].every(e=>getComputedStyle(e).textTransform!=='uppercase')''')
            for row in page.evaluate(COLLECT):
                value=ratio(row['color'],row['bg']);assert value>=row['minimum'],row
                pairs[(tuple(row['color']),tuple(row['bg']),row['kind'])]=round(value,3)
            if width in (1440,390):
                page.locator('#home-state').blur()
                target=ROOT/'screenshots'/f'022-department-home-{state}-{width}.png'
                page.screenshot(path=str(target),full_page=True,animations='disabled',caret='hide')
                with Image.open(target) as png:png.save(target,optimize=True)
                assert target.stat().st_size<=MAX_PNG_BYTES
                results.append({'state':state,'width':width,'bytes':target.stat().st_size})
        # Keyboard state switch and link/dialog focus restoration.
        page.select_option('#home-state','a');page.locator('#home-state').focus();page.keyboard.press('ArrowDown')
        expect(page.locator('#home-state')).to_have_value('b')
        page.keyboard.press('Tab');expect(page.locator('.home-task-list a').first).to_be_focused()
        page.keyboard.press('Enter');expect(page.locator('#destination-dialog')).to_be_visible()
        expect(page.locator('#destination-target')).to_have_text('/department/1?period_id=1')
        page.keyboard.press('Escape');expect(page.locator('.home-task-list a').first).to_be_focused()
        assert not errors and not requests,(errors,requests)
        ctx.close()
    browser.close()
print(json.dumps({'browser':version,'screenshots':results,'contrast':[{'fg':fg,'bg':bg,'kind':kind,'ratio':value} for (fg,bg,kind),value in pairs.items()]},ensure_ascii=False,indent=2))
PY_CAPTURE
```

## Metin envanteri

Yeni 022 dosyasındaki görünür metinler ve erişilebilir adlar (ortak kabuktan alınanlar dahil), ayrıca durum seçicinin ürettiği metinler:

- Müdürlük ana sayfası · Civensa prototip
- İçeriğe geç
- Civensa
- Kurumsal raporlama
- Ana gezinme
- Performans programı
- Genel bakış
- Veri girişi
- Faaliyet raporu
- Faaliyet raporu · EK-1
- İç kontrol
- İç kontrol eylemlerimiz
- Yönetim
- Modüller
- Gönderim yetkileri
- Parolamı değiştir
- Çıkış
- Örnek Hizmet Müdürlüğü
- Sentetik çalışma alanı
- Menüye git
- Bildirimler
- Müdürlük
- Birim Müdürü (sentetik)
- İçerik yolu
- /
- 2026 Performans programı
- Örnek Hizmet Müdürlüğü çalışma alanı
- Statik prototip · 022
- Prototip durumu
- a · Yeni dönem, veri girilmedi
- b · Veri girişi sürüyor, 3 sorun
- c · Veri girişi tamamlandı, gönderilmedi
- d · Gönderildi
- e · İade edildi, 3 sorun
- Özet
- Gösterge
- 12
- Civensa kontrolü
- 0
- Gönderim
- Taslak
- Bu dönem yapılacaklar
- Gönderimden önce Civensa tüm göstergelerdeki zorunlu alanları ve temel tutarlılık kontrollerini çalıştırır.
- Başlanmadı
- Bekliyor
- Gönderilmedi
- CIV-108 · Görsel inceleme
- Prototip sayfaları
- Tasarım sistemi
- 024 Veri girişi
- Bağlantı hedefi
- Bu ekran prototip kapsamı dışındadır.
- Mevcut uygulamadaki hedef:
- Ekran haritasında belirtilen bağlantı
- Kapat
- Statik prototip
- Bu işlem görsel inceleme için temsil edilir. Veri kaydedilmez, gönderilmez veya silinmez.
- Statik form örneği; gerçek parola girmeyin.
- Mevcut parola
- Yeni parola
- Yeni parola (tekrar)
- Vazgeç
- Parolayı değiştir
- Yeni bildirim yok.
- Sentetik bildirim paneli örneği.
- Devam ediyor
- Tamamlandı
- Düzeltme gerekli · 3 gösterge
- Sorun yok
- Gönderildi
- İade edildi — düzeltip yeniden gönderin
- Onaylandı
- İncelemede
- İade edildi
- 3

`Düzeltme gerekli · N gösterge` kalıbında bu örneklerde N = 3. Sayısal örnekler: 12 gösterge, 0/3 sorun. Uygulama hedefi ve diyalogda görünen yol: `/department/1?period_id=1`.
