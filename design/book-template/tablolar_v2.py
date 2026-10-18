"""Tablo şablonu v2 — v1'deki en uzun gerçek verilerle altı tablo + grafikler, özel tasarım v2.1 stilleriyle.

Çıktı: out_v2/Civensa_Tablo_Sablonu_v2.idml ve önizleme PDF'i.
Kurallar: başlık yanında numara yok (tablo numarası başlık numarası değildir); birim sütun başlığında, hücrede sembol yok.
"""
import os, sys
import ozel_v2 as O
from ozel_v2 import Page, P, V, MM, PW, ORNEK
import build_idml as B
import data as D

N_MAIN = int(os.environ.get('N_MAIN', '6'))   # akan tablo hikâyesi için sayfa sayısı


def H_(t):
    return (t, 'Hücre Başlık', '10 Tablo Başlık')


def HL(t, span=1):
    return (t, 'Hücre Başlık Sol', '11 Tablo Başlık Sol', span)


TW = 165 * MM


def main_story():
    S = []
    S.append(P('01 Bölüm Başlığı', 'Tablo ', V('Şablonu')))
    S.append(P('06 Spot', 'Altı tablo türü, gerçek kitaptaki en uzun değerlerle dolduruldu. Şablon bu uzunluklarda çalışıyorsa '
                          'kısa verilerde de çalışır. İçerik doğru değildir; yalnız biçim içindir.'))
    S.append(P('04 Ara Başlık 3', 'Kurallar'))
    S.append(P('07 Madde', 'Birim sütun başlığında yazar: “2027 Bütçe (TL)”, “Oran (%)”. Hücrelerde TL ve % işareti yoktur.'))
    S.append(P('07 Madde', '“-” veri yok, “0,00” sıfır demektir; ikisi farklı görünür.'))
    S.append(P('07 Madde', 'Tablo sayfa sonunda bölünür, başlık satırı yeni sayfada tekrarlanır.'))
    S.append(P('07 Madde', 'Rakam stillerinde OpenType “Tablo Biçiminde Hizalı” açıktır; kalın toplam satırı da hizalı kalır.'))

    # ---- Tablo 1: program bütçe kartı
    S.append(P('23 Tablo Başlığı', 'Tablo 1. Performans Esaslı Program Bütçe Kartı'))
    lab, unit = 72.0, 46.0
    val = B.money_col(D.IND_MAX, '19 Tablo Rakam Gösterge')
    name2 = TW - lab - unit - 6 * val
    t = B.Table([lab, name2, unit] + [val] * 6, header_rows=0, style='Tablo Kart')

    def kv(label, value_runs, cstyle='Hücre Metin', pstyle='13 Tablo Metin'):
        t.row([(label, 'Hücre Etiket', '12 Tablo Etiket'), (value_runs, cstyle, pstyle, 8)])
    kv('BÜTÇE YILI', [('Kalın', '2027/1')])
    kv('PROGRAM ADI', D.PROGRAM)
    kv('İDARE/BİRİM ADI', D.BIRIM)
    kv('ALT PROGRAM ADI', D.ALT_PROGRAM)
    g = D.GEREKCE
    if 'AÇIKLAMALAR:' in g:
        g1, g2 = g.split('AÇIKLAMALAR:', 1)
        runs = [('Kalın', 'GEREKÇE: '), g1.replace('GEREKÇE:', '').strip(), '\n', ('Kalın', 'AÇIKLAMALAR: '), g2.strip()]
    else:
        runs = [('Kalın', 'GEREKÇE: '), g.replace('GEREKÇE:', '').strip(), '\n', ('Kalın', 'AÇIKLAMALAR: '), D.HEDEF]
    kv('GEREKÇE ve AÇIKLAMALAR', runs, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('ALT PROGRAMIN HEDEFİ', D.HEDEF, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    t.row([('PERFORMANS GÖSTERGELERİ', 'Hücre Bölüm Satırı', '12 Tablo Etiket', 9)])
    t.row([HL('Performans Göstergesi', 2), H_('Ölçü Birimi'), H_('2025 Gerçekleşme'), H_('2026 Planlanan'),
           H_('2026 Yıl Sonu Gerçekleşme Tahmini'), H_('2027 Hedef'), H_('2028 Tahmin'), H_('2029 Tahmin')])
    for name, unit_, vals in D.INDICATORS:
        t.row([(name, 'Hücre Metin', '13 Tablo Metin', 2), (unit_, 'Hücre Metin', '13 Tablo Metin')] +
              [(v, 'Hücre Rakam Gösterge', '19 Tablo Rakam Gösterge') for v in vals])
    kv('Göstergeye İlişkin Açıklama', D.G_ACIKLAMA, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Hesaplama Yöntemi', D.HESAPLAMA, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Verinin Kaynağı', D.KAYNAK, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Sorumlu İdare', D.SORUMLU)
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', 'Örnek: gerçek kitaptaki en uzun gerekçe (1.792 karakter), gösterge adı (164 karakter) ve ölçü birimi; '
                                  'gösterge değerleri 99.999.999 ile sınandı. Göstergelerde birim satır başına değiştiği için ayrı sütundadır.'))

    # ---- Tablo 2: alt program faaliyet maliyetleri
    S.append(P('23 Tablo Başlığı', 'Tablo 2. Alt Program Faaliyet Maliyetleri'))
    mv = B.money_col(D.MONEY_UNIT, '17 Tablo Rakam')
    years = ['2026 Bütçe', '2026 Haziran Sonu Harcama', '2026 Yıl Sonu Harcama Tahmini', '2027 Bütçe', '2028 Tahmin', '2029 Tahmin']
    t = B.Table([TW - 6 * mv] + [mv] * 6, header_rows=2)
    t.row([HL('Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri (TL)', 7)])
    t.row([HL('Faaliyetler')] + [H_(y) for y in years])
    for name, vals in D.ACTIVITIES_CARD:
        t.row([(name, 'Hücre Metin', '13 Tablo Metin')] + [(v, 'Hücre Rakam', '17 Tablo Rakam') for v in vals])
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(v, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam') for v in D.TOTAL_CARD])
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', 'Örnek: en uzun faaliyet adı 272 karakter; tutarlar 9.999.999.999,99 ile sınandı.'))

    # ---- Tablo 3: müdürlük faaliyet maliyetleri (bütçe içi / dışı)
    S.append(P('23 Tablo Başlığı', 'Tablo 3. Müdürlük Faaliyet Maliyetleri (Bütçe İçi ve Bütçe Dışı)'))
    t = B.Table([TW - 6 * mv] + [mv] * 6, header_rows=1)
    t.row([HL('Faaliyetler')] + [H_(y + ' (TL)') for y in years])
    for name, inside, outside in D.ACTIVITIES_ORTAK:
        total = []
        for x, y in zip(inside, outside):
            if x == '-' and y == '-':
                total.append('-')
            else:
                num = lambda v: 0.0 if v == '-' else float(v.replace('.', '').replace(',', '.'))
                total.append(D.tr_money(num(x) + num(y)))
        t.row([(name, 'Hücre Metin', '13 Tablo Metin')] + [(v, 'Hücre Rakam', '17 Tablo Rakam') for v in total])
        t.row([('Bütçe İçi', 'Hücre Alt Satır', '15 Tablo Alt Satır')] + [(v, 'Hücre Alt Satır Rakam', '17 Tablo Rakam') for v in inside])
        t.row([('Bütçe Dışı', 'Hücre Alt Satır', '15 Tablo Alt Satır')] + [(v, 'Hücre Alt Satır Rakam', '17 Tablo Rakam') for v in outside])
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.MONEY_UNIT, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')] * 6)
    t.row([([('Kalın', 'Faaliyetlere ilişkin açıklama: '), D.UZUN_METIN], 'Hücre Metin Uzun', '14 Tablo Metin Uzun', 7)])
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', 'Örnek: en uzun ortak tablo faaliyet adı 324 karakter; tablo içindeki açıklama paragrafı 930 karakter.'))

    # ---- Tablo 4: ekonomik sınıflandırma
    S.append(P('23 Tablo Başlığı', 'Tablo 4. Ekonomik Sınıflandırmaya Göre Kaynak İhtiyacı'))
    code = 16.0
    t = B.Table([code, TW - code - 6 * mv] + [mv] * 6, header_rows=1)
    t.row([HL('Ekonomik Kod ve Ad', 2), H_('2025 Bütçe (TL)'), H_('2025 Haziran Sonu Harcama (TL)'),
           H_('2025 Yıl Sonu Harcama (TL)'), H_('2026 Bütçe (TL)'), H_('2027 Tahmin (TL)'), H_('2028 Tahmin (TL)')])
    for c, n in D.ECON_CATEGORIES:
        t.row([(c, 'Hücre Metin', '19 Tablo Rakam Gösterge'), (n, 'Hücre Metin', '13 Tablo Metin')] + [(D.MONEY_UNIT, 'Hücre Rakam', '17 Tablo Rakam')] * 6)
    for lbl in D.ECON_TOTALS:
        sub = lbl[0].islower() or lbl.startswith('Diğer')
        nice = lbl if sub else lbl.capitalize().replace('i̇', 'i')
        nice = {'TOPLAM': 'Toplam', 'BÜTÇE İÇİ TOPLAM KAYNAK': 'Bütçe İçi Toplam Kaynak', 'BÜTÇE DIŞI TOPLAM KAYNAK': 'Bütçe Dışı Toplam Kaynak',
                'FAALİYET MALİYETİ TOPLAMI': 'Faaliyet Maliyeti Toplamı'}.get(lbl, lbl)
        if sub:
            t.row([(nice, 'Hücre Alt Satır', '15 Tablo Alt Satır', 2)] + [('0,00', 'Hücre Alt Satır Rakam', '17 Tablo Rakam')] * 6)
        else:
            t.row([(nice, 'Hücre Toplam', '16 Tablo Toplam Etiket', 2)] + [(D.MONEY_UNIT, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')] * 6)
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', 'Örnek: en uzun ekonomik ad “Sosyal Güvenlik Kurumlarına Devlet Primi Giderleri”.'))

    # ---- Tablo 5: müdürlükler bazında dağılım
    S.append(P('23 Tablo Başlığı', 'Tablo 5. 2027 Yılı Bütçesinin Müdürlükler Bazında Dağılımı'))
    rows, total = D.directorate_budget()
    pct = B.money_col('100,00', '17 Tablo Rakam') + 28
    amt = B.money_col(D.MONEY_IDARE, '17 Tablo Rakam') + 28
    t = B.Table([TW - pct - amt, amt, pct], header_rows=1)
    t.row([HL('Müdürlük'), H_('2027 Yılı Müdürlük Bütçesi (TL)'), H_('Toplam Bütçeye Oranı (%)')])
    for d, v, p in rows:
        t.row([(d, 'Hücre Metin', '13 Tablo Metin'), (v, 'Hücre Rakam', '17 Tablo Rakam'), (p, 'Hücre Rakam', '17 Tablo Rakam')])
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket'), (D.MONEY_IDARE, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam'),
           ('100,00', 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')])
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', 'Örnek: 33 müdürlük; en uzun ad “Basın, Yayın ve Halkla İlişkiler Müdürlüğü”.'))
    return S


def wide_story():
    S = [P('23 Tablo Başlığı', 'Tablo 6. Ekonomik Koda Göre Program Grubu Dağılımı (yatay sayfa)')]
    LW = 232 * MM
    mv = B.money_col(D.MONEY_IDARE, '20 Tablo Rakam Geniş Tablo', inset=3)
    first = LW - 12 * mv
    t = B.Table([first] + [mv] * 12, header_rows=2)
    t.row([('Ekonomik Kod', 'Hücre Başlık Sol', '11 Tablo Başlık Sol', (1, 2)), ('2027 Bütçe (TL)', 'Hücre Başlık', '10 Tablo Başlık', 4),
           ('2028 Tahmin (TL)', 'Hücre Başlık', '10 Tablo Başlık', 4), ('2029 Tahmin (TL)', 'Hücre Başlık', '10 Tablo Başlık', 4)])
    sub = ['Hizmet Programları', 'Yönetim ve Destek Programı', 'Program Dışı Giderler', 'Toplam']
    t.row([H_(x) for x in sub * 3])
    for c, n in D.ECON_CATEGORIES:
        t.row([(f'{c} {n}', 'Hücre Metin', '13 Tablo Metin')] + [(D.MONEY_IDARE, 'Hücre Rakam Geniş', '20 Tablo Rakam Geniş Tablo')] * 12)
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.MONEY_IDARE, 'Hücre Toplam Rakam', '20 Tablo Rakam Geniş Tablo')] * 12)
    S.append(('TABLE', t))
    S.append(P('21 Tablo Kaynak', f'Örnek: kurum toplamı tutarları 99.999.999.999,99 ile sınandı (gerçek en büyük değer 11.904.930.191,00). '
                                  f'İlk sütun {first / MM:.0f} mm.'))
    return S


def chart_pages(sides):
    """sides: üç sayfanın kenarı. Grafik 1: 33 müdürlük (uzun etiket); Grafik 2–3 ve 4–5 ikişer grafik."""
    pages = []
    p = Page(sides[0], master='G')
    x0 = p.ml
    p.text(x0, 24, 165, 10, [P('30 Grafik Başlığı', 'Grafik 1. Müdürlükler Bazında 2027 Bütçesinin Dağılımı (%)')])
    rows, _ = D.directorate_budget()
    vals = sorted(((d, float(pv.replace('.', '').replace(',', '.'))) for d, _v, pv in rows), key=lambda r: -r[1])
    lab_w, bar_x, bar_max = 66.0, x0 + 69.0, 82.0
    vmax = vals[0][1]
    y = 36.0
    for i, (d, v) in enumerate(vals):
        p.text(x0, y - 0.9, lab_w, 5, [P('32r Grafik Etiket Sağ', d)])
        bw = max(0.6, v / vmax * bar_max)
        p.rect(bar_x, y, bw, 2.4, fill='Kurumsal Vurgu' if i == 0 else 'Kurumsal Ana')
        p.text(bar_x + bw + 1.5, y - 1.1, 16, 5, [P('33 Grafik Değer', f'{v:.2f}'.replace('.', ','))])
        y += 6.4
    p.line([(bar_x, 34), (bar_x, y - 2)], stroke='Çizgi Gri', sw=0.4)
    p.text(x0, y + 1, 165, 6, [P('31 Grafik Kaynak', 'En uzun etiket: “Basın, Yayın ve Halkla İlişkiler Müdürlüğü”. ' + ORNEK)])
    pages.append(p)

    # --- iki sayfalık grafik açılımı
    p = Page(sides[1], master='G')
    x0 = p.ml
    p.text(x0, 24, 165, 10, [P('30 Grafik Başlığı', 'Grafik 2. Ekonomik Sınıflandırmaya Göre 2027 Bütçe Dağılımı (%)')])
    parts = [('Mal ve Hizmet Alım Giderleri', 52.6, 'Grafik 1'), ('Sermaye Giderleri', 22.6, 'Kurumsal Vurgu'),
             ('Personel Giderleri', 18.4, 'Grafik 6'), ('Cari Transferler', 3.1, 'Grafik 3'),
             ('Sosyal Güvenlik Kurumlarına Devlet Primi Giderleri', 2.9, 'Grafik 4'), ('Diğer (Faiz, Sermaye Transferleri, Yedek Ödenekler)', 0.4, 'Grafik 5')]
    cx, cy, r, ring = x0 + 32, 72.0, 24.0, 10 * MM
    a = 0.0
    for nm, v, col in parts:
        a1 = a + 360 * v / 100
        p.arc(cx, cy, r, a + 0.6, max(a + 0.8, a1 - 0.6), stroke=col, sw=ring)
        a = a1
    p.text(cx - 18, cy - 4.6, 36, 12, [P('35 Halka Merkez Rakam', '9,8 Mr')])
    ly = 50.0
    for nm, v, col in parts:
        p.rect(x0 + 70, ly + 0.8, 3.5, 3.5, fill=col)
        p.text(x0 + 76, ly, 70, 9, [P('32 Grafik Etiket', nm)])
        p.text(x0 + 148, ly, 17, 6, [P('33 Grafik Değer', f'{v:.1f}'.replace('.', ','))])
        ly += 8.5
    p.text(x0, 104, 165, 6, [P('31 Grafik Kaynak', 'Halkanın ortasındaki tutar toplam bütçedir (TL). ' + ORNEK)])
    # sütun grafik
    p.text(x0, 120, 165, 10, [P('30 Grafik Başlığı', 'Grafik 3. İlçe Nüfusu (Kişi)')])
    yrs = ['2021', '2022', '2023', '2024', '2025', '2026']
    pop = [267_500, 271_900, 275_400, 278_800, 281_000, 284_600]
    gx, gy0, gh = x0 + 4, 134.0, 50.0
    lo = 250_000
    for v_ in (250_000, 260_000, 270_000, 280_000, 290_000):
        yy = gy0 + gh - (v_ - lo) / 40_000 * gh
        p.line([(gx, yy), (x0 + 165, yy)], stroke='Çizgi Gri', sw=0.3)
        p.text(x0 - 12, yy - 2.4, 15, 5, [P('32r Grafik Etiket Sağ', f'{v_:,}'.replace(',', '.'))])
    for i, (yr, v_) in enumerate(zip(yrs, pop)):
        bx = gx + 8 + i * 26.0
        hh = (v_ - lo) / 40_000 * gh
        p.rect(bx, gy0 + gh - hh, 12, hh, fill='Kurumsal Vurgu' if i == len(yrs) - 1 else 'Kurumsal Ana')
        p.text(bx - 6, gy0 + gh - hh - 6, 24, 5, [P('33 Grafik Değer', f'{v_:,}'.replace(',', '.'))])
        p.text(bx - 6, gy0 + gh + 2, 24, 5, [P('32 Grafik Etiket', yr)])
    p.text(x0, gy0 + gh + 10, 165, 6, [P('31 Grafik Kaynak', 'Eksen 250.000’den başlar; değerler sütun üstünde yazılıdır. ' + ORNEK)])
    pages.append(p)

    p = Page(sides[2], master='G')
    x0 = p.ml
    # çizgi grafik: gerçekleşme düz, tahmin kesikli
    p.text(x0, 24, 165, 10, [P('30 Grafik Başlığı', 'Grafik 4. Program Gruplarına Göre Bütçe (Milyon TL)')])
    yrs = ['2025', '2026', '2027', '2028', '2029']
    series = [('Hizmet Programları', [6100, 6900, 7600, 8300, 9100], 'Kurumsal Ana'),
              ('Yönetim ve Destek Programı', [2100, 2350, 2500, 2700, 2900], 'Kurumsal Vurgu'),
              ('Program Dışı Giderler', [300, 320, 340, 360, 380], 'Grafik 5')]
    gx0, gx1, gy0, gy1 = x0 + 12, x0 + 120, 38.0, 96.0
    vmax = 10000
    for v_ in (0, 2500, 5000, 7500, 10000):
        yy = gy1 - v_ / vmax * (gy1 - gy0)
        p.line([(gx0, yy), (gx1, yy)], stroke='Çizgi Gri', sw=0.3)
        p.text(x0 - 4, yy - 2.4, 14, 5, [P('32r Grafik Etiket Sağ', f'{v_:,}'.replace(',', '.'))])
    xs = [gx0 + 6 + i * (gx1 - gx0 - 12) / 4 for i in range(5)]
    for i, yr in enumerate(yrs):
        p.text(xs[i] - 10, gy1 + 2, 20, 5, [P('32 Grafik Etiket', yr + (' tahmin' if i >= 3 else ''))])
    for nm, vs, col in series:
        pts = [(xs[i], gy1 - v_ / vmax * (gy1 - gy0)) for i, v_ in enumerate(vs)]
        p.line(pts[:3], stroke=col, sw=1.6, cap='RoundEndCap')
        p.line(pts[2:], stroke=col, sw=1.6, dash=True)
        for q in pts:
            p.oval(q[0], q[1], 1.1, fill=col)
        p.text(gx1 + 3, pts[-1][1] - 2.6, 45, 6, [P('32 Grafik Etiket', nm)])
    p.text(x0, gy1 + 10, 165, 6, [P('31 Grafik Kaynak', 'Düz çizgi bütçe, kesikli çizgi tahmindir. Seri adı çizginin ucunda yazılıdır; ayrı açıklama kutusu yoktur. ' + ORNEK)])
    # %100 yığılmış çubuk
    p.text(x0, 122, 165, 10, [P('30 Grafik Başlığı', 'Grafik 5. Personelin İstihdam Türüne Göre Dağılımı (%)')])
    cats = [('Memur', 'Grafik 1'), ('Sözleşmeli Personel', 'Grafik 6'), ('İşçi (Kadrolu)', 'Grafik 3'), ('Şirket Personeli (Hizmet Alımı)', 'Kurumsal Vurgu')]
    data_ = [('2025', [14.2, 6.1, 22.4, 57.3]), ('2026', [13.6, 6.8, 21.0, 58.6]), ('2027 Plan', [13.1, 7.4, 20.3, 59.2])]
    y = 136.0
    for yr, vs in data_:
        p.text(x0, y + 0.4, 20, 5, [P('32 Grafik Etiket', yr)])
        x = x0 + 22
        for (nm, col), v_ in zip(cats, vs):
            w_ = 143 * v_ / 100
            p.rect(x, y, w_, 6.5, fill=col)
            if v_ >= 6:
                dark = col in ('Grafik 1', 'Grafik 6', 'Kurumsal Vurgu')
                p.text(x + 1.5, y + 1.0, w_ - 2, 5, [P('33b Grafik Değer Koyu Zemin' if dark else '33 Grafik Değer', f'{v_:.1f}'.replace('.', ','))])
            x += w_
        y += 11.0
    for i, (nm, col) in enumerate(cats):
        lx = x0 + 22 + (i % 2) * 72.0
        ly = y + 2 + (i // 2) * 7.5
        p.rect(lx, ly + 0.8, 3.5, 3.5, fill=col)
        p.text(lx + 5.5, ly, 66, 6, [P('32 Grafik Etiket', nm)])
    p.text(x0, y + 19, 165, 6, [P('31 Grafik Kaynak', ORNEK)])
    pages.append(p)
    return pages


def build():
    O.PAGES.clear(); O.STORIES.clear()
    O.RAPOR = '2027 Performans Programı'
    O.MASTERS = {
        'T': ('A-Tablolar', 'A', 'Tablolar', 'Program ve Müdürlük Tabloları'),
        'G': ('B-Grafikler', 'B', 'Grafikler', 'Grafikler'),
        'Y': ('Y-Boş', 'Y', 'Boş', None),
    }
    O.define_styles()
    O.build_masters()
    O.STORIES['uMainT'] = main_story()
    O.STORIES['uWideT'] = wide_story()
    sides = ['R' if i % 2 == 0 else 'L' for i in range(N_MAIN)]
    for i in range(N_MAIN):
        p = Page(sides[i], master='T')
        p.text(p.ml, 24, 165, 232, story='uMainT')
    # yatay tablo bir açılımda (sol + sağ) dursun; grafik sayfaları boşluğu doldurur
    def nxt():
        return 'R' if len(O.PAGES) % 2 == 0 else 'L'
    if nxt() == 'R':
        chart_pages(['R', 'L', 'R'])
    for k in range(2):
        p = Page(nxt(), master='T')
        p.text(p.ml, 24, 165, 232, story='uWideT', rot=True)
    if len(O.PAGES) < N_MAIN + 5:
        chart_pages([nxt(), 'R' if nxt() == 'L' else 'L', nxt()])
    return O.PAGES


if __name__ == '__main__':
    pages = build()
    print('sayfa', len(pages), [p.side + p.master for p in pages])
    print('IDML', O.build_idml(pages, name='Civensa_Tablo_Sablonu_v2'))
    import onizleme
    print('PDF', onizleme.render(pages, O.STORIES, O.STY, O.RGB, O.CELLSTY, os.path.join(O.OUT, 'Civensa_Tablo_Sablonu_v2_onizleme.pdf'), O.MASTER_PAGES))
    for w_ in B.warnings:
        print('UYARI', w_)
