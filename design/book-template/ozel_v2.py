"""Civensa özel tasarım şablonu v2 — IDML + önizleme PDF.

Karışım: HiveArt "Sustainability and ESG Report" (sakin koyu yeşil zemin, bol boşluk, yay çizgileri,
yan sütunda büyük rakamlar, zaman çizelgesi) + BrandPacks "Sustainability Report" (kapak kurgusu,
büyük bölüm numaraları, iki renkli başlıklar, rakam şeritleri, turuncu halka göstergeler).
Esinlenme; hiçbir şablon dosyası kullanılmadı. Bütün sayfa öğeleri burada çizilir.

Tek bir sayfa tanımı iki çıktıya gider: InDesign IDML ve kontrol için reportlab önizlemesi.
Birim: mm, sayfa sol üst köşesi (0,0), y aşağı doğru.
"""
import os, re, zipfile, math, random
from xml.sax.saxutils import escape, quoteattr

import build_idml as B
import fontmetrics as FM
import data as D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out_v2')
GF = os.path.join(HERE, '..', 'gf', 'ofl')
FM.FILES['Literata'] = ('literata', 'Literata')

PW, PH, BL = 200.0, 280.0, 3.0
MM = 72 / 25.4
W, H = PW * MM, PH * MM
B.W, B.H = W, H
FS, FC, FX, LT = 'Fira Sans', 'Fira Sans Condensed', 'Fira Sans Extra Condensed', 'Literata'
TAB = 'TabularLining'

# ----------------------------------------------------------------------------- renkler
# (ad, CMYK, önizleme sRGB)
COLORS = [
    ('Kurumsal Ana', '85 45 65 45', '#1f4f47'),      # koyu yeşil (HiveArt mantığı)
    ('Kurumsal Vurgu', '5 65 95 0', '#e2742c'),      # turuncu (BrandPacks vurgusu)
    ('Ana Açık', '35 10 25 0', '#a9c7bd'),           # koyu zeminde ikincil yazı, yay çizgileri
    ('Metin Koyu', '0 0 0 90', '#262626'),
    ('Metin Açık', '0 0 0 60', '#6d6d6d'),
    ('Çizgi Gri', '0 0 0 30', '#b8b8b8'),
    ('Zemin Gri', '0 0 0 6', '#f1f1f1'),
    ('Açık Zemin', '3 2 6 0', '#f5f3ee'),
    ('Görsel Yer Tutucu', '10 5 10 15', '#c9cbc6'),
    ('Grafik 1', '85 45 65 45', '#1f4f47'),
    ('Grafik 2', '5 65 95 0', '#e2742c'),
    ('Grafik 3', '45 10 35 0', '#8fbfa9'),
    ('Grafik 4', '5 15 40 5', '#dcc59a'),
    ('Grafik 5', '0 0 0 45', '#929292'),
    ('Grafik 6', '60 20 45 10', '#5f8f80'),
]
RGB = {n: h for n, _, h in COLORS}
RGB['Paper'] = '#ffffff'
RGB['Black'] = '#000000'
B.COLORS = [(n, c) for n, c, _ in COLORS]


def tint_hex(hexc, tint):
    if tint is None or tint >= 100:
        return hexc
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    t = tint / 100
    r, g, b = (round(255 - (255 - v) * t) for v in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}'


# ----------------------------------------------------------------------------- stiller
STY = {}   # paragraf stili adı -> özellikler (önizleme için)


def para(name, family, style, size, leading, just='LeftAlign', color='Metin Koyu', tint=None, caps=False, tracking=0,
         before=0.0, after=0.0, tabular=False, hyph=False, left=0.0, first=0.0, keep=0, bullet=False, tabs=None, nobreak=False):
    STY[name] = dict(family=family, style=style, size=size, leading=leading, just=just, color=color, tint=tint, caps=caps,
                     before=before, after=after, tabular=tabular, left=left, first=first, bullet=bullet, tabs=tabs, hyph=hyph)
    attrs = dict(SpaceBefore=float(before), SpaceAfter=float(after), Hyphenation='true' if hyph else 'false')
    if hyph:   # Türkçe heceleme ve iki yana yaslamada aralık sınırları
        attrs.update(HyphenateWordsLongerThan='5', HyphenateAfterFirst='2', HyphenateBeforeLast='2', HyphenateLadderLimit='2',
                     HyphenateCapitalizedWords='true', HyphenationZone='0', MinimumWordSpacing='85', DesiredWordSpacing='100',
                     MaximumWordSpacing='125', MinimumLetterSpacing='-1', DesiredLetterSpacing='0', MaximumLetterSpacing='2')
    if tint is not None:
        attrs['FillTint'] = float(tint)
    if caps:
        attrs['Capitalization'] = 'AllCaps'
    if tracking:
        attrs['Tracking'] = str(tracking)
    if tabular:
        attrs['OTFFigureStyle'] = TAB
    if left:
        attrs['LeftIndent'] = float(left)
    if first:
        attrs['FirstLineIndent'] = float(first)
    if keep:
        attrs['KeepWithNext'] = str(keep)
    if nobreak:
        attrs['NoBreak'] = 'true'
    extra = ''
    if bullet:
        attrs.update(BulletsAndNumberingListType='BulletList', BulletsTextAfter='^t')
        extra += '<BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="8226" />'
    if tabs:
        items = ''.join(f'<ListItem type="record"><Alignment type="enumeration">{al}</Alignment><AlignmentCharacter type="string">.</AlignmentCharacter>'
                        f'<Leader type="string">{escape(ld)}</Leader><Position type="unit">{B.fmt(float(pos))}</Position></ListItem>' for al, pos, ld in tabs)
        extra += f'<TabList type="list">{items}</TabList>'
    B.para(name, family, style, size, leading, just=just, color=color, extra_props=extra, **attrs)


def define_styles():
    B.PS.clear(); B.CS.clear(); B.CELL.clear(); B.TS.clear(); B.PARA.clear()
    K, KZ = 'Metin Koyu', 'Paper'
    # 01–09 başlık ve metin
    para('01 Bölüm Başlığı', FS, 'SemiBold', 26, 29, tracking=-10, after=8, keep=2)
    para('01b Bölüm Başlığı Koyu Zemin', FS, 'SemiBold', 26, 29, color=KZ, tracking=-10, after=8, keep=2)
    para('02 Ara Başlık 1', FS, 'SemiBold', 12.5, 15.5, color='Kurumsal Ana', before=12, after=5, keep=2)
    para('03 Ara Başlık 2', FS, 'Medium', 10, 13, before=8, after=3, keep=2)
    para('04 Ara Başlık 3', FS, 'SemiBold', 7, 10, color='Kurumsal Vurgu', caps=True, tracking=80, before=6, after=3, keep=2)
    para('04b Ara Başlık 3 Koyu Zemin', FS, 'SemiBold', 7, 10, color='Kurumsal Vurgu', caps=True, tracking=80, before=6, after=3, keep=2)
    para('05 Gövde', LT, 'Regular', 9.5, 14, just='LeftJustified', after=5, hyph=True)
    para('05b Gövde Koyu Zemin', LT, 'Regular', 9.5, 14, just='LeftJustified', color=KZ, after=5, hyph=True)
    para('06 Spot', FS, 'Light', 12.5, 17.5, after=10)
    para('06b Spot Koyu Zemin', FS, 'Light', 12.5, 17.5, color=KZ, after=10)
    para('07 Madde', LT, 'Regular', 9.5, 14, left=11, first=-11, after=2, bullet=True, hyph=True)
    para('08 Kenar Notu', FS, 'Regular', 7.5, 10.5, color='Metin Açık', after=6, hyph=True)
    para('08a Kenar Notu Başlık', FS, 'SemiBold', 7.5, 10.5, after=1, keep=1)
    para('09 Görsel Altı', FS, 'Regular', 7, 9.5, color='Metin Açık')
    # 10–22 tablo (v1 ile aynı numaralar, yeni renkler)
    para('10 Tablo Başlık', FC, 'SemiBold', 7, 8.5, just='RightAlign', color=KZ)
    para('11 Tablo Başlık Sol', FC, 'SemiBold', 7, 8.5, color=KZ)
    para('12 Tablo Etiket', FC, 'SemiBold', 7, 9, color='Kurumsal Ana')
    para('13 Tablo Metin', FC, 'Regular', 7.5, 9.5, hyph=True)
    para('16 Tablo Toplam Etiket', FC, 'SemiBold', 7.5, 9.5)
    para('17 Tablo Rakam', FX, 'Regular', 7.5, 9.5, just='RightAlign', tabular=True, nobreak=True)
    para('18 Tablo Rakam Toplam', FX, 'SemiBold', 7.5, 9.5, just='RightAlign', tabular=True, nobreak=True)
    para('14 Tablo Metin Uzun', FS, 'Regular', 7.5, 10.5, just='LeftJustified', after=3, hyph=True)
    para('15 Tablo Alt Satır', FC, 'Italic', 7, 9, color='Metin Açık', left=8)
    para('19 Tablo Rakam Gösterge', FC, 'Regular', 7.5, 9.5, just='RightAlign', tabular=True, nobreak=True)
    para('20 Tablo Rakam Geniş Tablo', FX, 'Regular', 6.5, 8, just='RightAlign', tabular=True, nobreak=True)
    para('21 Tablo Kaynak', FC, 'Italic', 6.5, 8.5, color='Metin Açık', before=3)
    para('22 Tablo Kapsayıcı', FS, 'Regular', 4, 4, after=2)
    para('23 Tablo Başlığı', FS, 'SemiBold', 9, 11.5, after=5, keep=1)
    # 30–34 grafik
    para('30 Grafik Başlığı', FS, 'SemiBold', 9, 11.5, after=2, keep=1)
    para('30b Grafik Başlığı Koyu Zemin', FS, 'SemiBold', 9, 11.5, color=KZ, after=2, keep=1)
    para('31 Grafik Kaynak', FC, 'Italic', 6.5, 8.5, color='Metin Açık')
    para('31b Grafik Kaynak Koyu Zemin', FC, 'Italic', 6.5, 8.5, color='Ana Açık')
    para('32 Grafik Etiket', FC, 'Regular', 7, 8.5, color='Metin Açık')
    para('32b Grafik Etiket Koyu Zemin', FC, 'Regular', 7, 8.5, color='Ana Açık')
    para('32r Grafik Etiket Sağ', FC, 'Regular', 7, 8.5, just='RightAlign', color='Metin Açık')
    para('33 Grafik Değer', FC, 'SemiBold', 7.5, 9, tabular=True)
    para('33b Grafik Değer Koyu Zemin', FC, 'SemiBold', 7.5, 9, color=KZ, tabular=True)
    para('34 Gösterge Halka Rakam', FS, 'Medium', 20, 22, just='CenterAlign', color=KZ, tracking=-10)
    para('35 Halka Merkez Rakam', FS, 'Medium', 18, 20, just='CenterAlign', color='Kurumsal Ana', tracking=-10)
    para('34a Gösterge Halka Etiket', FS, 'Regular', 7.5, 10, just='CenterAlign', color='Ana Açık')
    # 40–42 içindekiler
    para('40 İçindekiler Bölüm', FS, 'Medium', 12, 15, color=KZ, tabs=[('RightAlign', 140 * MM, ' ')])
    para('41 İçindekiler Alt', FS, 'Regular', 8.5, 12, color='Ana Açık')
    para('42 İçindekiler No', FS, 'Medium', 20, 22, color='Kurumsal Vurgu', tabular=True)
    para('43 Bölüm Listesi', FS, 'Regular', 9.5, 13, tabs=[('RightAlign', 112 * MM, ' ')])
    # 50–51 sayfa öğeleri
    para('50 Sayfa Numarası', FS, 'SemiBold', 9, 10, color='Kurumsal Ana', tabular=True)
    para('50r Sayfa Numarası Sağ', FS, 'SemiBold', 9, 10, just='RightAlign', color='Kurumsal Ana', tabular=True)
    para('50b Sayfa Numarası Koyu Zemin', FS, 'SemiBold', 9, 10, color=KZ, tabular=True)
    para('50br Sayfa Numarası Koyu Zemin Sağ', FS, 'SemiBold', 9, 10, just='RightAlign', color=KZ, tabular=True)
    para('51 Rubrik', FS, 'Medium', 6.5, 10, color='Metin Açık', caps=True, tracking=120)
    para('51r Rubrik Sağ', FS, 'Medium', 6.5, 10, just='RightAlign', color='Metin Açık', caps=True, tracking=120)
    para('51b Rubrik Koyu Zemin', FS, 'Medium', 6.5, 10, color='Ana Açık', caps=True, tracking=120)
    para('51br Rubrik Koyu Zemin Sağ', FS, 'Medium', 6.5, 10, just='RightAlign', color='Ana Açık', caps=True, tracking=120)
    # 60–79 özel tasarım öğeleri
    para('60 Bölüm No', FS, 'Medium', 110, 100, tracking=-30)
    para('61 Bölüm Spotu', FS, 'Light', 13, 18, after=8)
    para('62 Kapak Yıl', FS, 'Light', 66, 64, color='Kurumsal Vurgu', tracking=-20)
    para('63 Kapak Başlık', FS, 'SemiBold', 44, 44, color=KZ, tracking=-15)
    para('64 Kapak Slogan', FS, 'Medium', 15, 19, color=KZ)
    para('65 Kapak Künye', FS, 'Regular', 7.5, 10, color='Ana Açık')
    para('66 Büyük Rakam', FS, 'Medium', 34, 36, color='Kurumsal Vurgu', tracking=-10)
    para('66a Büyük Rakam Yeşil', FS, 'Medium', 34, 36, color='Kurumsal Ana', tracking=-10)
    para('67 Büyük Rakam Etiket', FS, 'Regular', 8, 10.5, after=2)
    para('67b Büyük Rakam Etiket Koyu Zemin', FS, 'Regular', 8, 10.5, color='Ana Açık', after=2)
    para('68 Alıntı', FS, 'Light', 17, 23, after=6)
    para('68b Alıntı Koyu Zemin', FS, 'Light', 15.5, 21, color=KZ, after=6)
    para('68a Alıntı Kenar', FS, 'Light', 13, 18, after=6)
    para('69a Alıntı İşareti', FS, 'Medium', 48, 40, color='Kurumsal Vurgu')
    para('69 Alıntı Kaynak', FS, 'Medium', 8, 10.5, color='Kurumsal Vurgu')
    para('70 İmza Ad', FS, 'Medium', 11, 14, color=KZ, before=10)
    para('71 İmza Unvan', FS, 'Regular', 8, 10.5, color='Ana Açık')
    para('72 Şema Kutu', FC, 'Medium', 7.5, 9, just='CenterAlign')
    para('72b Şema Kutu Koyu', FC, 'Medium', 7.5, 9, just='CenterAlign', color=KZ)
    para('73 Etiket Turuncu', FS, 'SemiBold', 7, 9, color='Kurumsal Vurgu', caps=True, tracking=100)
    para('74 Yol Haritası Yıl', FS, 'Medium', 16, 18, color='Kurumsal Ana', tabular=True)
    para('75 Yol Haritası Başlık', FS, 'SemiBold', 9, 11.5, after=2)
    para('76 Logo Yazısı', FS, 'SemiBold', 8.5, 10, color=KZ, caps=True, tracking=40)
    # karakter stilleri
    B.charst('Kalın', FontStyle='SemiBold')
    B.charst('İtalik', FontStyle='Italic')
    B.charst('Rakam Tabular', OTFFigureStyle=TAB)
    B.charst('Vurgu Renk', FillColor=B.C('Kurumsal Vurgu'))
    B.charst('Ana Renk', FillColor=B.C('Kurumsal Ana'))
    # hücre ve tablo stilleri
    B.cell('Hücre Başlık', '10 Tablo Başlık', fill='Kurumsal Ana', valign='BottomAlign', inset=(3, 3, 3, 3), bottom=(0.5, 'Paper'))
    B.cell('Hücre Başlık Sol', '11 Tablo Başlık Sol', fill='Kurumsal Ana', valign='BottomAlign', inset=(3, 3, 3, 3), bottom=(0.5, 'Paper'))
    B.cell('Hücre Metin', '13 Tablo Metin', inset=(2.5, 3, 2.5, 3), bottom=(0.25, 'Çizgi Gri'))
    B.cell('Hücre Rakam', '17 Tablo Rakam', inset=(2.5, 3, 2.5, 3), bottom=(0.25, 'Çizgi Gri'))
    B.cell('Hücre Toplam', '16 Tablo Toplam Etiket', fill='Açık Zemin', top=(0.75, 'Kurumsal Ana'), bottom=(1.5, 'Kurumsal Vurgu'))
    B.cell('Hücre Toplam Rakam', '18 Tablo Rakam Toplam', fill='Açık Zemin', top=(0.75, 'Kurumsal Ana'), bottom=(1.5, 'Kurumsal Vurgu'))
    B.cell('Hücre Etiket', '12 Tablo Etiket', fill='Açık Zemin', inset=(2.5, 3, 2.5, 3), bottom=(0.5, 'Paper'))
    B.cell('Hücre Bölüm Satırı', '12 Tablo Etiket', fill='Kurumsal Ana', tint=15, valign='CenterAlign', inset=(3, 3, 3, 3), bottom=(0.5, 'Paper'))
    B.cell('Hücre Metin Uzun', '14 Tablo Metin Uzun', inset=(3, 3, 1.5, 3), bottom=(0.25, 'Çizgi Gri'))
    B.cell('Hücre Rakam Gösterge', '19 Tablo Rakam Gösterge', inset=(2.5, 3, 2.5, 3), bottom=(0.25, 'Çizgi Gri'))
    B.cell('Hücre Rakam Geniş', '20 Tablo Rakam Geniş Tablo', inset=(2, 1.5, 2, 1.5), bottom=(0.25, 'Çizgi Gri'))
    B.cell('Hücre Alt Satır', '15 Tablo Alt Satır', inset=(1.5, 3, 1.5, 3), bottom=(0.25, 'Zemin Gri'))
    B.cell('Hücre Alt Satır Rakam', '17 Tablo Rakam', inset=(1.5, 3, 1.5, 3), bottom=(0.25, 'Zemin Gri'))
    B.tablestyle('Tablo Standart', 'Hücre Başlık', 'Hücre Metin')
    B.tablestyle('Tablo Kart', 'Hücre Başlık', 'Hücre Metin')


CELLSTY = {   # önizleme: hücre stili -> (zemin, tint, üst çizgi, alt çizgi)
    'Hücre Başlık': ('Kurumsal Ana', None, None, (0.5, 'Paper')),
    'Hücre Başlık Sol': ('Kurumsal Ana', None, None, (0.5, 'Paper')),
    'Hücre Metin': (None, None, None, (0.25, 'Çizgi Gri')),
    'Hücre Rakam': (None, None, None, (0.25, 'Çizgi Gri')),
    'Hücre Toplam': ('Açık Zemin', None, (0.75, 'Kurumsal Ana'), (1.5, 'Kurumsal Vurgu')),
    'Hücre Etiket': ('Açık Zemin', None, None, (0.5, 'Paper')),
    'Hücre Bölüm Satırı': ('Kurumsal Ana', 15, None, (0.5, 'Paper')),
    'Hücre Metin Uzun': (None, None, None, (0.25, 'Çizgi Gri')),
    'Hücre Rakam Gösterge': (None, None, None, (0.25, 'Çizgi Gri')),
    'Hücre Rakam Geniş': (None, None, None, (0.25, 'Çizgi Gri')),
    'Hücre Alt Satır': (None, None, None, (0.25, 'Zemin Gri')),
    'Hücre Alt Satır Rakam': (None, None, None, (0.25, 'Zemin Gri')),
    'Hücre Toplam Rakam': ('Açık Zemin', None, (0.75, 'Kurumsal Ana'), (1.5, 'Kurumsal Vurgu')),
}

# ----------------------------------------------------------------------------- sayfa modeli
PAGES = []          # dict(side, master, items)
STORIES = {}        # sid -> list of (style, runs) | ('TABLE', Table)
_n = [0]


def nid(p='u'):
    _n[0] += 1
    return f'{p}{_n[0]:x}'


class Page:
    def __init__(self, side, master='Y', register=True):
        self.side, self.master, self.items = side, master, []
        if register:
            PAGES.append(self)

    # yardımcılar
    @property
    def ml(self):
        return 20.0 if self.side == 'R' else 15.0

    @property
    def mr(self):
        return 15.0 if self.side == 'R' else 20.0

    def cols(self):
        """(ana sütun x, genişlik), (kenar sütun x, genişlik). Kenar sütunu dış kenarda."""
        if self.side == 'R':
            return (self.ml, 112.0), (self.ml + 120.0, 45.0)
        return (self.ml + 53.0, 112.0), (self.ml, 45.0)

    def bg(self, color, tint=None):
        x1 = 0.0 if self.side == 'R' else -BL
        x2 = PW + BL if self.side == 'R' else PW
        self.rect(x1, -BL, x2 - x1, PH + 2 * BL, fill=color, tint=tint)

    def rect(self, x, y, w, h, fill=None, tint=None, stroke=None, sw=0.0, stint=None, photo=False, label=None):
        self.items.append(dict(t='rect', pts=[(x, y), (x, y + h), (x + w, y + h), (x + w, y)], fill=fill, tint=tint,
                               stroke=stroke, sw=sw, stint=stint, photo=photo, label=label))

    def poly(self, pts, fill=None, tint=None, photo=False, label=None):
        self.items.append(dict(t='rect', pts=pts, fill=fill, tint=tint, stroke=None, sw=0, stint=None, photo=photo, label=label))

    def line(self, pts, stroke='Metin Koyu', sw=0.5, tint=None, cap='ButtEndCap', dash=False):
        self.items.append(dict(t='line', pts=pts, stroke=stroke, sw=sw, tint=tint, cap=cap, dash=dash))

    def oval(self, cx, cy, r, fill=None, tint=None, stroke=None, sw=0.0, stint=None):
        self.items.append(dict(t='oval', cx=cx, cy=cy, r=r, fill=fill, tint=tint, stroke=stroke, sw=sw, stint=stint))

    def arc(self, cx, cy, r, a0, a1, stroke, sw, tint=None, cap='ButtEndCap'):
        self.items.append(dict(t='arc', cx=cx, cy=cy, r=r, a0=a0, a1=a1, stroke=stroke, sw=sw, tint=tint, cap=cap))

    def text(self, x, y, w, h, paras=None, story=None, cols=1, gutter=5.0, valign='TopAlign', name=None, rot=False):
        """rot=True: alan (x, y, w, h) sayfada; metin 90° döner (yatay tablo). Satırlar soldan sağa ilerler."""
        if story is None:
            story = nid('uS')
            STORIES[story] = paras
        self.items.append(dict(t='text', x=x, y=y, w=w, h=h, story=story, cols=cols, gutter=gutter, valign=valign, rot=rot))
        return story


def P(style, *runs):
    return (style, list(runs))


def V(txt):
    return ('Vurgu Renk', txt)


def Kb(txt):
    return ('Kalın', txt)


LS = ' '   # satır kırma (paragraf içinde)

# ----------------------------------------------------------------------------- içerik
ORNEK = 'Örnek veri — biçim içindir.'
HIZMET_ALANLARI = [
    ('Bütüncül Kent Yönetimi', 78), ('Kamusal Mekân ve Kıyı Politikaları', 69), ('Kentsel Dönüşüm ve Afet Yönetimi', 64),
    ('Sürdürülebilir Gelecek ve İklim', 81), ('İnsan Odaklı Hizmetler', 75), ('Uluslararası İlişkiler ve Kurumsal İtibar', 70),
    ('Kurumsal Yönetim', 73),
]
METIN1 = ('Belediyemiz, ilçe sınırları içinde yaşayan herkesin ortak ihtiyaçlarını karşılamak için planlama, altyapı, çevre, '
          'sosyal hizmet ve kültür alanlarında hizmet üretir. Hizmetlerin önceliği stratejik plan ve performans programıyla '
          'belirlenir; bütçe bu önceliklere göre dağıtılır ve yıl içinde yapılan harcamalar bu raporla kamuoyuyla paylaşılır.')
METIN2 = ('İlçemiz; kıyı şeridi, göl havzası ve kırsal mahalleleriyle farklı ihtiyaçları olan bir yerleşim alanıdır. Yaz aylarında '
          'artan nüfus temizlik, ulaşım ve su hizmetlerinde mevsimlik planlama gerektirir. Göl çevresindeki düzenleme, kıyıdaki '
          'yürüyüş yolları ve mahalle ölçeğindeki küçük parklar son yıllarda en çok talep gören hizmetler arasında yer almıştır.')
METIN3 = ('Raporda yer alan tutarlar Türk lirası cinsindendir ve 31 Aralık 2026 itibarıyla kesinleşmiş verilere dayanır. '
          'Bir faaliyetin 1.250.000,00 TL olarak planlanan bütçesinin 1.187.430,55 TL tutarındaki kısmı harcanmışsa '
          'gerçekleşme oranı %95,0 olarak gösterilir. Ayrıntılı mali tablolar üçüncü bölümde yer alır.')
METIN4 = ('Müdürlüklerin faaliyet sonuçları, stratejik plandaki amaç ve hedeflerle ilişkilendirilerek değerlendirilir. '
          'Her göstergenin hedef ve gerçekleşme değeri birlikte verilir; sapma varsa nedeni açıklanır. Hedefi bulunmayan '
          'göstergelerde oran hesaplanmaz, yalnız gerçekleşme değeri gösterilir.')


RAPOR = '2026 Faaliyet Raporu'
PAGENUM = ('PAGENUM', '')


def header(pg, rubrik, dark=False):
    """Sayfa üstü: dış köşede sayfa numarası, ince dikey çizgi, rubrik. Sol ve sağ sayfa aynalı."""
    d = 'b' if dark else ''
    line_col = 'Ana Açık' if dark else 'Çizgi Gri'
    y, h = 10.0, 5.0
    if pg.side == 'L':
        pg.text(15, y, 11, h, [P(f'50{d} Sayfa Numarası' + (' Koyu Zemin' if dark else ''), PAGENUM)])
        pg.line([(27.5, y + 0.6), (27.5, y + 3.9)], stroke=line_col, sw=0.5)
        pg.text(30.5, y + 0.5, 110, h, [P('51b Rubrik Koyu Zemin' if dark else '51 Rubrik', rubrik)])
    else:
        pg.text(PW - 15 - 11, y, 11, h, [P('50br Sayfa Numarası Koyu Zemin Sağ' if dark else '50r Sayfa Numarası Sağ', PAGENUM)])
        pg.line([(PW - 27.5, y + 0.6), (PW - 27.5, y + 3.9)], stroke=line_col, sw=0.5)
        pg.text(PW - 30.5 - 110, y + 0.5, 110, h, [P('51br Rubrik Koyu Zemin Sağ' if dark else '51r Rubrik Sağ', rubrik)])


# ana sayfalar: anahtar -> (ad, ön ek, taban ad, sağ sayfa rubriği); sol sayfa rubriği her zaman rapor adı
MASTERS = {
    'A': ('A-Ön Bölüm', 'A', 'Ön Bölüm', 'Sunuş ve Yönetici Özeti'),
    'B': ('B-Genel Bilgiler', 'B', 'Genel Bilgiler', 'Genel Bilgiler'),
    'C': ('C-Amaçlar ve Hedefler', 'C', 'Amaçlar ve Hedefler', 'Amaçlar ve Hedefler'),
    'D': ('D-Faaliyetler', 'D', 'Faaliyetler', 'Faaliyetlere İlişkin Bilgi ve Değerlendirmeler'),
    'E': ('E-Kurumsal Kabiliyet', 'E', 'Kurumsal Kabiliyet', 'Kurumsal Kabiliyet ve Kapasitenin Değerlendirilmesi'),
    'F': ('F-Öneri ve Tedbirler', 'F', 'Öneri ve Tedbirler', 'Öneri ve Tedbirler'),
    'G': ('G-Ekler', 'G', 'Ekler', 'Ekler'),
    'Y': ('Y-Boş', 'Y', 'Boş', None),
}
MASTER_PAGES = {}   # anahtar -> (sol Page, sağ Page)


def build_masters():
    MASTER_PAGES.clear()
    for k, (name, pre, base, rub) in MASTERS.items():
        l, r = Page('L', register=False), Page('R', register=False)
        if rub:
            header(l, RAPOR)
            header(r, rub)
        MASTER_PAGES[k] = (l, r)


def kpi_block(pg, x, y, w, num, label, style='66 Büyük Rakam', lstyle='67 Büyük Rakam Etiket', rule=True):
    if rule:
        pg.line([(x, y), (x + w, y)], stroke='Çizgi Gri', sw=0.5)
    pg.text(x, y + 2.5, w, 14.0, [P(style, num)])
    pg.text(x, y + 16.0, w, 12.0, [P(lstyle, label)])


def photo(pg, x, y, w, h, label='Görsel'):
    pg.rect(x, y, w, h, fill='Görsel Yer Tutucu', photo=True, label=label)


def arcs(pg, cx, cy, radii, stroke='Ana Açık', tint=45, sw=0.6):
    for r in radii:
        pg.oval(cx, cy, r, stroke=stroke, sw=sw, stint=tint)


def build_pages():
    PAGES.clear(); STORIES.clear()
    build_masters()

    # ---- 1 KAPAK (sağ, tek sayfa)
    p = Page('R', master='Y')
    p.bg('Kurumsal Ana')
    arcs(p, 205, 30, [62, 84, 106])
    p.rect(18, 18, 11, 11, fill='Paper', label='Logo')
    p.text(32, 18.2, 80, 12, [P('76 Logo Yazısı', f'T.C. Büyükçekmece{LS}Belediyesi')])
    photo(p, 62, 96, PW + BL - 62, 112, label='Kapak görseli')
    p.items[-1]['pts'] = [(62, 136), (62, 208), (PW + BL, 208), (PW + BL, 96), (102, 96)]   # sol üst köşe kesik
    p.text(18, 70, 120, 26, [P('62 Kapak Yıl', '2026')])
    p.text(18, 96, 150, 40, [P('63 Kapak Başlık', f'Faaliyet{LS}Raporu')])
    p.text(18, 222, 130, 22, [P('64 Kapak Slogan', f'Daha yaşanabilir bir ilçe için{LS}bir yılın hesabı.')])
    p.line([(18, 252), (185, 252)], stroke='Ana Açık', sw=0.5, tint=60)
    p.text(18, 255, 70, 12, [P('65 Kapak Künye', f'Strateji Geliştirme Müdürlüğü{LS}Nisan 2027')])
    p.text(100, 255, 85, 12, [P('65 Kapak Künye', f'2021 tarihli Usul ve Esaslar Yönetmeliği{LS}EK-1 yapısına göre hazırlanmıştır.')])

    # ---- 2–3 BAŞKANIN MESAJI
    p = Page('L', master='Y')
    p.bg('Kurumsal Ana')
    arcs(p, -25, 305, [48, 68])
    header(p, 'Sunuş', dark=True)
    p.text(15, 30, 150, 40, [P('01b Bölüm Başlığı Koyu Zemin', 'Başkanın', LS, V('Mesajı'))])
    body = [P('05b Gövde Koyu Zemin', METIN1), P('05b Gövde Koyu Zemin', METIN2), P('05b Gövde Koyu Zemin', METIN4),
            P('05b Gövde Koyu Zemin', METIN3), P('05b Gövde Koyu Zemin', 'Hizmetlerimizi değerlendirirken yalnız tamamlanan işleri '
              'değil, tamamlanamayanları ve nedenlerini de açıkça yazdık. Bu rapor, önümüzdeki yılın planlamasına da yön verecektir.'),
            P('70 İmza Ad', 'Ad Soyad'), P('71 İmza Unvan', 'Büyükçekmece Belediye Başkanı')]
    p.text(15, 76, 165, 150, body, cols=2, gutter=8)
    p = Page('R', master='Y')
    photo(p, 0, -BL, PW + BL, PH + 2 * BL, label='Başkan fotoğrafı (tam sayfa)')
    p.rect(0, 186, 128, PH + BL - 186, fill='Kurumsal Ana')
    p.text(14, 194, 104, 16, [P('69a Alıntı İşareti', '“')])
    p.text(14, 210, 104, 60, [P('68b Alıntı Koyu Zemin', 'Bir yılın hesabını verirken rakamların arkasındaki insanı ve mahalleyi unutmadık.')])

    # ---- 4–5 İÇİNDEKİLER + BİR BAKIŞTA
    p = Page('L', master='Y')
    p.bg('Kurumsal Ana')
    arcs(p, -20, -20, [70, 92])
    header(p, RAPOR, dark=True)
    p.text(15, 30, 150, 20, [P('01b Bölüm Başlığı Koyu Zemin', 'İçindekiler')])
    toc = [('01', 'Genel Bilgiler', '6', ['Misyon ve Vizyon', 'Yetki, Görev ve Sorumluluklar', 'İdareye İlişkin Bilgiler'], ),
           ('02', 'Amaçlar ve Hedefler', '24', ['Temel Politika ve Öncelikler', 'Stratejik Plandaki Amaç ve Hedefler']),
           ('03', 'Faaliyetlere İlişkin Bilgi ve Değerlendirmeler', '32', ['Mali Bilgiler', 'Performans Bilgileri']),
           ('04', 'Kurumsal Kabiliyet ve Kapasitenin Değerlendirilmesi', '248', ['Üstünlükler', 'Zayıflıklar', 'Değerlendirme']),
           ('05', 'Öneri ve Tedbirler', '256', [])]
    y = 62.0
    for no, title, pg_, subs in toc:
        p.line([(15, y), (180, y)], stroke='Ana Açık', sw=0.4, tint=55)
        p.text(15, y + 3, 22, 12, [P('42 İçindekiler No', no)])
        paras = [P('40 İçindekiler Bölüm', title, '\t', pg_)] + [P('41 İçindekiler Alt', s) for s in subs]
        p.text(40, y + 4.2, 140, 12 + 4.3 * len(subs), paras)
        y += 18 + 4.3 * len(subs) + 5
    p.line([(15, y), (180, y)], stroke='Ana Açık', sw=0.4, tint=55)
    p.text(40, y + 4.2, 140, 12, [P('40 İçindekiler Bölüm', 'Ekler: İç Kontrol Güvence Beyanları', '\t', '262')])

    p = Page('R', master='A')
    p.text(20, 30, 160, 34, [P('01 Bölüm Başlığı', 'Bir Bakışta ', V('2026'))])
    p.text(20, 50, 112, 22, [P('06 Spot', 'Yılın sonuçları altı rakamda. Ayrıntılar ilgili bölümlerde.')])
    kp = [('%72', 'Kurum performans gerçekleşme oranı'), ('227', 'Performans göstergesi izlendi'), ('37', 'Müdürlük raporlarını sundu'),
          ('9,8 Mr TL', 'Yıl sonu bütçe gideri'), ('1.250', 'Personel'), ('118', 'Tamamlanan proje')]
    for i, (n_, l_) in enumerate(kp):
        cx = 20 + (i % 3) * 56.0
        cy = 80 + (i // 3) * 38.0
        kpi_block(p, cx, cy, 50, n_, l_)
    photo(p, 20, 162, 165, 72, label='Görsel (ilçeden geniş açı)')
    p.text(20, 236, 165, 8, [P('09 Görsel Altı', 'Görsel altı yazısı: Kıyı düzenleme alanından bir görünüm. Fotoğraf: Basın Yayın ve Halkla İlişkiler Müdürlüğü')])
    p.text(20, 246, 165, 6, [P('31 Grafik Kaynak', ORNEK)])

    # ---- 6–7 BÖLÜM AÇILIŞI
    p = Page('L', master='Y')
    photo(p, -BL, -BL, PW + BL, PH + 2 * BL, label='Bölüm görseli (tam sayfa)')
    p = Page('R', master='Y')
    p.text(20, 22, 120, 40, [P('60 Bölüm No', '01')])
    p.text(20, 66, 150, 40, [P('01 Bölüm Başlığı', 'Genel', LS, V('Bilgiler'))])
    p.text(20, 98, 112, 36, [P('61 Bölüm Spotu', 'Belediyenin görev alanı, teşkilat yapısı, insan kaynakları ve sunduğu hizmetler.')])
    subs = [('Misyon ve Vizyon', '8'), ('Yetki, Görev ve Sorumluluklar', '10'), ('İdareye İlişkin Bilgiler', '12'), ('Diğer Hususlar', '22')]
    y = 140.0
    for s, n_ in subs:
        p.line([(20, y), (132, y)], stroke='Çizgi Gri', sw=0.4)
        p.text(20, y + 2.6, 112, 7, [P('43 Bölüm Listesi', s, '\t', n_)])
        y += 10.5
    p.line([(20, y), (132, y)], stroke='Çizgi Gri', sw=0.4)
    p.rect(0, 210, PW + BL, PH + BL - 210, fill='Kurumsal Ana')
    arcs(p, 205, 285, [40, 58])
    for i, (n_, l_) in enumerate([('35', 'Müdürlük'), ('7', 'Hizmet alanı'), ('81', 'Mahalle')]):
        x = 20 + i * 45.0
        p.text(x, 222, 40, 14, [P('66 Büyük Rakam', n_)])
        p.text(x, 238, 40, 10, [P('67b Büyük Rakam Etiket Koyu Zemin', l_)])

    # ---- 8–9 UZUN METİN (akan tek hikâye: sayfa 8 ana sütun → sayfa 9 ana sütun)
    long_story = 'uLong'
    STORIES[long_story] = [
        P('01 Bölüm Başlığı', 'Misyon ve ', V('Vizyon')),
        P('06 Spot', 'Kurumun neden var olduğunu ve beş yıl sonra nerede olmak istediğini kısa ve ölçülebilir cümlelerle anlatır.'),
        P('02 Ara Başlık 1', 'Misyonumuz'),
        P('05 Gövde', METIN1), P('05 Gövde', METIN2),
        P('02 Ara Başlık 1', 'Vizyonumuz'),
        P('05 Gövde', METIN4), P('05 Gövde', METIN3),
        P('03 Ara Başlık 2', 'Temel değerlerimiz'),
        P('07 Madde', 'Şeffaflık: bütçe ve sonuçlar herkesin erişebileceği biçimde yayımlanır.'),
        P('07 Madde', 'Katılımcılık: mahalle toplantıları ve anketler planlamaya girdi sağlar.'),
        P('07 Madde', 'Hesap verebilirlik: her hedefin sorumlu müdürlüğü ve göstergesi bellidir.'),
        P('02 Ara Başlık 1', 'Yetki, Görev ve Sorumluluklar'),
        P('05 Gövde', METIN2), P('05 Gövde', METIN1), P('05 Gövde', METIN4),
        P('03 Ara Başlık 2', 'Kanuni dayanak'),
        P('05 Gövde', METIN3), P('05 Gövde', METIN2),
        P('03 Ara Başlık 2', 'Meclis ve encümen'),
        P('05 Gövde', METIN1),
    ]
    p = Page('L', master='B')
    (mx, mw), (sx, sw_) = p.cols()
    p.text(mx, 24, mw, 228, story=long_story)
    p.text(sx, 92, sw_, 60, [P('04 Ara Başlık 3', 'Kısaca'), P('08 Kenar Notu', 'Misyon ve vizyon metinleri 2025–2029 Stratejik Planı’ndan alınmıştır. '
                                                                    'Plan, Meclisin 2024 tarihli kararıyla kabul edilmiştir.')])
    p.line([(sx, 160), (sx + sw_, 160)], stroke='Kurumsal Vurgu', sw=1.5)
    p.text(sx, 164, sw_, 70, [P('68a Alıntı Kenar', 'Planlama, kaynakların nereye gideceğine birlikte karar vermektir.')])
    p = Page('R', master='B')
    (mx, mw), (sx, sw_) = p.cols()
    p.text(mx, 24, mw, 186, story=long_story)
    photo(p, sx, 24, sw_, 60, label='Görsel')
    p.text(sx, 86, sw_, 16, [P('09 Görsel Altı', 'Görsel altı yazısı iki satıra kadar uzayabilir.')])
    p.rect(0, 214, PW + BL, 44, fill='Açık Zemin')
    for i, (n_, l_) in enumerate([('%95,0', 'Bütçe gerçekleşme oranı'), ('412', 'Mahalle toplantısı'), ('14 Bin', 'Ankete katılan vatandaş')]):
        x = 20 + i * 56.0
        p.text(x, 221, 52, 14, [P('66 Büyük Rakam', n_)])
        p.text(x, 237, 52, 10, [P('67 Büyük Rakam Etiket', l_)])

    # ---- 10–11 MÜDÜRLÜK AÇILIŞI
    p = Page('L', master='D')
    p.text(15, 24, 165, 8, [P('73 Etiket Turuncu', 'Hizmet alanı · Bütüncül Kent Yönetimi')])
    p.text(15, 32, 165, 36, [P('01 Bölüm Başlığı', 'Sağlık İşleri ', V('Müdürlüğü'))])
    p.text(15, 46, 112, 24, [P('06 Spot', 'Evde sağlık, psikolojik danışmanlık ve hasta nakli hizmetleri.')])
    # teşkilat şeması
    p.text(15, 72, 165, 8, [P('30 Grafik Başlığı', 'Teşkilat Şeması')])
    bx, by, bw, bh = 72.5, 84.0, 50.0, 12.0
    p.rect(bx, by, bw, bh, fill='Kurumsal Ana')
    p.text(bx, by + 3.2, bw, 8, [P('72b Şema Kutu Koyu', 'Müdür')])
    p.line([(bx + bw / 2, by + bh), (bx + bw / 2, by + bh + 6)], stroke='Kurumsal Ana', sw=0.6)
    p.line([(40, by + bh + 6), (155, by + bh + 6)], stroke='Kurumsal Ana', sw=0.6)
    for i, nm in enumerate(['Sağlık Hizmetleri Şefliği', 'Evde Bakım Birimi', 'İdari İşler Şefliği']):
        cx = 40 + i * 57.5
        p.line([(cx, by + bh + 6), (cx, by + bh + 12)], stroke='Kurumsal Ana', sw=0.6)
        p.rect(cx - 25, by + bh + 12, 50, 12, fill='Kurumsal Ana', tint=12)
        p.text(cx - 25, by + bh + 15.2, 50, 8, [P('72 Şema Kutu', nm)])
    # personel tablosu
    t = B.Table([80 * MM, 30 * MM], header_rows=1)
    t.row([('Unvan', 'Hücre Başlık Sol', '11 Tablo Başlık Sol'), ('Kişi', 'Hücre Başlık', '10 Tablo Başlık')])
    for u, k in [('Memur', '9'), ('Sözleşmeli Personel', '6'), ('İşçi (Kadrolu)', '14'), ('Şirket Personeli', '41')]:
        t.row([(u, 'Hücre Metin', '13 Tablo Metin'), (k, 'Hücre Rakam', '17 Tablo Rakam')])
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket'), ('70', 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')])
    STORIES['uPers'] = [P('23 Tablo Başlığı', 'Personel Durumu'), ('TABLE', t), P('21 Tablo Kaynak', ORNEK)]
    p.text(15, 130, 112, 70, story='uPers')
    p.text(135, 130, 45, 90, [P('04 Ara Başlık 3', 'Araç ve tesis'), P('08 Kenar Notu', '3 hasta nakil aracı, 2 hizmet aracı, 1 sağlık merkezi. Ayrıntılı liste Ekler bölümündedir.'),
                              P('04 Ara Başlık 3', 'Bütçe'), P('08 Kenar Notu', 'Başlangıç ödeneği 70.000.000,00 TL; yıl sonu gideri 48.342.217,01 TL.')])
    p.text(15, 206, 112, 50, [P('02 Ara Başlık 1', 'Faaliyetler'), P('05 Gövde', METIN4)])
    p = Page('R', master='D')
    p.text(20, 24, 165, 60, [P('03 Ara Başlık 2', 'Evde sağlık hizmetleri'), P('05 Gövde', METIN2), P('05 Gövde', METIN3)], cols=2, gutter=8)
    gx, gy, gw, gh = 20.0, 90.0, 80.5, 55.0
    caps = ['Evde sağlık ziyareti', 'Fizyoterapi hizmeti', 'Hasta nakil aracı', 'Psikolojik danışmanlık']
    for i in range(4):
        x = gx + (i % 2) * (gw + 4)
        y = gy + (i // 2) * (gh + 13)
        photo(p, x, y, gw, gh)
        p.text(x, y + gh + 2, gw, 8, [P('09 Görsel Altı', caps[i])])
    for i, (n_, l_) in enumerate([('2.165', 'Evde sağlık ziyareti'), ('1.480', 'Hasta nakli'), ('612', 'Danışmanlık görüşmesi')]):
        kpi_block(p, 20 + i * 56.0, 222, 50, n_, l_, style='66a Büyük Rakam Yeşil')

    # ---- 12–13 PERFORMANS GRAFİKLERİ
    p = Page('L', master='Y')
    p.bg('Kurumsal Ana')
    header(p, RAPOR, dark=True)
    p.text(15, 30, 165, 34, [P('01b Bölüm Başlığı Koyu Zemin', 'Performans ', V('Sonuçları'))])
    p.text(15, 46, 120, 24, [P('06b Spot Koyu Zemin', 'Kurum genelinde gösterge gerçekleşmesi altı yıldır düzenli artıyor.')])
    # çizgi grafik
    p.text(15, 74, 165, 8, [P('30b Grafik Başlığı Koyu Zemin', 'Kurum Performans Gerçekleşme Oranı (%)')])
    yrs = ['2021', '2022', '2023', '2024', '2025', '2026']
    vals = [61, 64, 66, 69, 70, 72]
    gx0, gx1, gy0, gy1 = 22.0, 178.0, 92.0, 150.0      # alan
    lo, hi = 50, 80
    for v in (50, 60, 70, 80):
        yy = gy1 - (v - lo) / (hi - lo) * (gy1 - gy0)
        p.line([(gx0, yy), (gx1, yy)], stroke='Ana Açık', sw=0.3, tint=40)
        p.text(15, yy - 2.4, 6, 5, [P('32b Grafik Etiket Koyu Zemin', str(v))])
    pts = []
    for i, (yr, v) in enumerate(zip(yrs, vals)):
        xx = gx0 + 6 + i * (gx1 - gx0 - 12) / (len(yrs) - 1)
        yy = gy1 - (v - lo) / (hi - lo) * (gy1 - gy0)
        pts.append((xx, yy))
        p.text(xx - 8, gy1 + 2.5, 16, 5, [P('32b Grafik Etiket Koyu Zemin', yr)])
    p.line(pts, stroke='Kurumsal Vurgu', sw=1.6, cap='RoundEndCap')
    for i, (xx, yy) in enumerate(pts):
        p.oval(xx, yy, 1.4, fill='Kurumsal Vurgu')
        p.text(xx - 8, yy - 7.5, 16, 5, [P('33b Grafik Değer Koyu Zemin', f'%{vals[i]}')])
    p.text(15, 160, 165, 6, [P('31b Grafik Kaynak Koyu Zemin', ORNEK)])
    # halka göstergeler
    p.text(15, 176, 165, 8, [P('30b Grafik Başlığı Koyu Zemin', 'Göstergelerin Durumu')])
    for i, (v, l_) in enumerate([(72, 'Kurum performansı'), (84, 'Hedefine ulaşan gösterge'), (91, 'Tamamlanan faaliyet')]):
        cx, cy, r, ring = 41.5 + i * 56.0, 216.0, 19.0, 7.0 * MM     # halka kalınlığı 7 mm
        p.oval(cx, cy, r, stroke='Ana Açık', sw=ring, stint=30)
        p.arc(cx, cy, r, 0, 360 * v / 100, stroke='Kurumsal Vurgu', sw=ring)
        p.text(cx - 15, cy - 4.6, 30, 10, [P('34 Gösterge Halka Rakam', f'%{v}')])
        p.text(cx - 25, cy + r + 7, 50, 10, [P('34a Gösterge Halka Etiket', l_)])
    p = Page('R', master='D')
    p.text(20, 24, 165, 10, [P('30 Grafik Başlığı', 'Hizmet Alanlarına Göre Gösterge Gerçekleşme Oranı (%)')])
    y = 37.0
    mx_ = max(v for _, v in HIZMET_ALANLARI)
    for nm, v in HIZMET_ALANLARI:
        p.text(20, y, 150, 5, [P('32 Grafik Etiket', nm)])
        bw = (v / 100) * 150
        p.rect(20, y + 4.6, bw, 2.4, fill='Kurumsal Vurgu' if v == mx_ else 'Kurumsal Ana')
        p.text(20 + bw + 2, y + 3.6, 14, 5, [P('33 Grafik Değer', f'%{v}')])
        y += 12.0
    p.line([(20, 35), (20, y - 3)], stroke='Çizgi Gri', sw=0.4)
    p.text(20, y - 1, 165, 6, [P('31 Grafik Kaynak', ORNEK)])
    # eşik tablosu (renk kodlu)
    p.text(20, 134, 112, 10, [P('23 Tablo Başlığı', 'Performans Değerlendirme Ölçeği')])
    scale = [('0', 'Gerçekleşmemiş', 'Grafik 5'), ('1–45', 'Düşük', 'Grafik 4'), ('46–75', 'Orta', 'Grafik 3'),
             ('76–109', 'Yüksek', 'Grafik 6'), ('110 ve üstü', 'Hedefin çok üstü', 'Kurumsal Vurgu')]
    y = 144.0
    for rng_, nm, col in scale:
        p.rect(20, y + 1, 4, 4, fill=col)
        p.text(27, y + 0.6, 40, 6, [P('13 Tablo Metin', nm)])
        p.text(70, y + 0.6, 30, 6, [P('17 Tablo Rakam', rng_)])
        p.line([(20, y + 7.5), (100, y + 7.5)], stroke='Çizgi Gri', sw=0.25)
        y += 9.0
    p.text(115, 134, 70, 60, [P('04 Ara Başlık 3', 'Nasıl okunur'), P('08 Kenar Notu', 'Gerçekleşme oranı, gerçekleşme değerinin hedefe bölünmesiyle bulunur. '
                                                                          'Hedefi olmayan göstergede oran hesaplanmaz.')])
    p.text(20, 202, 112, 50, [P('03 Ara Başlık 2', 'Değerlendirme'), P('05 Gövde', METIN4)])

    # ---- 14–15 TABLOLAR
    p = Page('L', master='D')
    p.text(15, 24, 165, 34, [P('01 Bölüm Başlığı', 'Bütçe Uygulama ', V('Sonuçları'))])
    rng = random.Random(2026)
    rows = []
    tot = [0.0, 0.0, 0.0]
    for d in D.DIRECTORATES[:14]:
        a0 = rng.uniform(20e6, 400e6)
        if d.startswith('Fen'):
            a0 = 2_634_147_337.0
        a1 = a0 * rng.uniform(0.96, 1.08)
        g = a1 * rng.uniform(0.62, 0.97)
        rows.append((d, a0, a1, g))
        tot = [tot[0] + a0, tot[1] + a1, tot[2] + g]
    mv = 27.0 * MM
    t = B.Table([165 * MM - 3 * mv - 16 * MM, mv, mv, mv, 16 * MM], header_rows=1)
    t.row([('Müdürlük', 'Hücre Başlık Sol', '11 Tablo Başlık Sol'), ('Başlangıç Ödeneği (TL)', 'Hücre Başlık', '10 Tablo Başlık'),
           ('Kesinleşen Ödenek (TL)', 'Hücre Başlık', '10 Tablo Başlık'), ('Yıl Sonu Gideri (TL)', 'Hücre Başlık', '10 Tablo Başlık'),
           ('Gerçekleşme (%)', 'Hücre Başlık', '10 Tablo Başlık')])
    for d, a0, a1, g in rows:
        t.row([(d, 'Hücre Metin', '13 Tablo Metin'), (D.tr_money(a0), 'Hücre Rakam', '17 Tablo Rakam'), (D.tr_money(a1), 'Hücre Rakam', '17 Tablo Rakam'),
               (D.tr_money(g), 'Hücre Rakam', '17 Tablo Rakam'), (D.tr_money(g / a1 * 100).rsplit(',', 1)[0] + ',' + D.tr_money(g / a1 * 100).rsplit(',', 1)[1][:1], 'Hücre Rakam', '17 Tablo Rakam')])
    t.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.tr_money(v), 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam') for v in tot] +
          [(f'{tot[2] / tot[1] * 100:.1f}'.replace('.', ','), 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')])
    STORIES['uTab1'] = [P('23 Tablo Başlığı', 'Müdürlüklerin Bütçe Ödenekleri ve Yıl Sonu Giderleri'), ('TABLE', t),
                        P('21 Tablo Kaynak', 'Kaynak: Mali Hizmetler Müdürlüğü. ' + ORNEK)]
    p.text(15, 48, 165, 205, story='uTab1')
    p = Page('R', master='D')
    p.text(20, 24, 165, 10, [P('30 Grafik Başlığı', 'Ekonomik Sınıflandırmaya Göre Gider Dağılımı (%)')])
    parts = [('Personel', 18.4, 'Grafik 1'), ('SGK', 2.9, 'Grafik 6'), ('Mal ve Hizmet Alımı', 52.6, 'Grafik 3'),
             ('Faiz', 0.4, 'Grafik 5'), ('Cari Transfer', 3.1, 'Grafik 4'), ('Sermaye', 22.6, 'Kurumsal Vurgu')]
    x = 20.0
    for nm, v, col in parts:
        w_ = 165 * v / 100
        p.rect(x, 38, w_, 7, fill=col)
        x += w_
    for i, (nm, v, col) in enumerate(parts):
        lx = 20 + (i % 3) * 56.0
        ly = 50 + (i // 3) * 9.0
        p.rect(lx, ly + 0.8, 3.5, 3.5, fill=col)
        p.text(lx + 5.5, ly, 50, 6, [P('32 Grafik Etiket', f'{nm}  ', ('Kalın', f'%{str(v).replace(".", ",")}'))])
    p.text(20, 70, 165, 6, [P('31 Grafik Kaynak', ORNEK)])
    t2 = B.Table([165 * MM - 3 * mv, mv, mv, mv], header_rows=1)
    t2.row([('Ekonomik Sınıflandırma', 'Hücre Başlık Sol', '11 Tablo Başlık Sol'), ('Başlangıç Ödeneği (TL)', 'Hücre Başlık', '10 Tablo Başlık'),
            ('Kesinleşen Ödenek (TL)', 'Hücre Başlık', '10 Tablo Başlık'), ('Yıl Sonu Gideri (TL)', 'Hücre Başlık', '10 Tablo Başlık')])
    for c_, n_ in D.ECON_CATEGORIES:
        t2.row([(f'{c_} {n_}', 'Hücre Metin', '13 Tablo Metin')] + [(D.MONEY_UNIT, 'Hücre Rakam', '17 Tablo Rakam')] * 3)
    t2.row([('Toplam', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.MONEY_IDARE, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')] * 3)
    STORIES['uTab2'] = [P('23 Tablo Başlığı', 'Ekonomik Sınıflandırmaya Göre Bütçe Uygulama Sonuçları'), ('TABLE', t2),
                        P('21 Tablo Kaynak', 'Tutarlar en uzun değerle sınandı (9.999.999.999,99 / 99.999.999.999,99). ' + ORNEK)]
    p.text(20, 92, 165, 120, story='uTab2')
    p.text(20, 214, 112, 40, [P('03 Ara Başlık 2', 'Açıklama'), P('05 Gövde', METIN3)])

    # ---- 16 YOL HARİTASI (sol, tek)
    p = Page('L', master='C')
    p.text(15, 24, 110, 34, [P('01 Bölüm Başlığı', 'Stratejik Plan', LS, V('2025–2029'))])
    steps = [('2025', 'Planın kabulü', 'Amaç, hedef ve göstergeler belirlendi; sorumlu müdürlükler atandı.'),
             ('2026', 'İlk izleme yılı', 'Göstergelerin ilk gerçekleşme değerleri bu raporla yayımlandı.'),
             ('2027', 'Ara değerlendirme', 'Sapma gösteren hedefler gözden geçirilecek.'),
             ('2028', 'Güncelleme', 'Gerekirse hedefler ve göstergeler güncellenecek.'),
             ('2029', 'Plan sonu', 'Plan dönemi sonuç raporu hazırlanacak.')]
    x0 = 42.0
    y = 66.0
    p.line([(x0, y + 4), (x0, y + 4 + 34 * (len(steps) - 1))], stroke='Kurumsal Ana', sw=0.8)
    for yr, t_, d_ in steps:
        p.text(15, y, 24, 9, [P('74 Yol Haritası Yıl', yr)])
        p.oval(x0, y + 4, 2.0, fill='Kurumsal Ana' if yr != '2026' else 'Kurumsal Vurgu')
        p.text(x0 + 7, y, 80, 30, [P('75 Yol Haritası Başlık', t_), P('08 Kenar Notu', d_)])
        y += 34.0
    p.rect(130, -BL, PW - 130, PH + 2 * BL, fill='Kurumsal Ana')
    arcs(p, 210, 140, [40, 60, 80])
    p.text(138, 150, 46, 60, [P('68b Alıntı Koyu Zemin', 'Birlikte planlıyor, birlikte ölçüyoruz.')])
    return PAGES


# ----------------------------------------------------------------------------- IDML
def sx(pg, x):
    return x * MM + (0.0 if pg.side == 'R' else -W)


def sy(y):
    return y * MM - H / 2


def pp_xml(pts):
    out = []
    for a_, l_, r_ in pts:
        out.append(f'<PathPointType Anchor="{B.fmt(a_[0])} {B.fmt(a_[1])}" LeftDirection="{B.fmt(l_[0])} {B.fmt(l_[1])}" '
                   f'RightDirection="{B.fmt(r_[0])} {B.fmt(r_[1])}" />')
    return ''.join(out)


def geom(pts, open_=False):
    return (f'<Properties><PathGeometry><GeometryPathType PathOpen="{"true" if open_ else "false"}"><PathPointArray>{pp_xml(pts)}'
            '</PathPointArray></GeometryPathType></PathGeometry></Properties>')


def color_attrs(fill=None, tint=None, stroke=None, sw=0.0, stint=None):
    a_ = dict(FillColor=B.C(fill) if fill else 'Swatch/None', StrokeColor=B.C(stroke) if stroke else 'Swatch/None',
              StrokeWeight=B.fmt(float(sw)) if stroke else '0')
    if fill and tint is not None:
        a_['FillTint'] = B.fmt(float(tint))
    if stroke and stint is not None:
        a_['StrokeTint'] = B.fmt(float(stint))
    return ' '.join(f'{k}={B.a(v)}' for k, v in a_.items())


def arc_points(cx, cy, r, a0, a1):
    """Saat yönünde, 12'den başlayan derece. Bezier noktaları (anchor, left, right)."""
    segs = max(1, math.ceil(abs(a1 - a0) / 90))
    step = (a1 - a0) / segs
    k = 4 / 3 * math.tan(math.radians(step) / 4) * r
    out = []
    for i in range(segs + 1):
        ang = math.radians(a0 + i * step)
        px, py = cx + r * math.sin(ang), cy - r * math.cos(ang)
        tx, ty = math.cos(ang), math.sin(ang)          # saat yönünde teğet
        left = (px - k * tx, py - k * ty) if i > 0 else (px, py)
        right = (px + k * tx, py + k * ty) if i < segs else (px, py)
        out.append(((px, py), left, right))
    return out


def item_xml(pg, it):
    fx = lambda x: sx(pg, x)
    if it['t'] == 'rect':
        pts = [((fx(x), sy(y)),) * 3 for x, y in it['pts']]
        ctype = 'GraphicType' if it['photo'] else 'Unassigned'
        ostyle = '$ID/[Normal Graphics Frame]' if it['photo'] else '$ID/[None]'
        name = it['label'] or '$ID/'
        tag = 'Rectangle' if len(pts) == 4 else 'Polygon'
        extra = '<FrameFittingOption FittingOnEmptyFrame="FillProportionally" />' if it['photo'] else ''
        return (f'<{tag} Self="{nid()}" ContentType="{ctype}" StoryTitle="$ID/" Visible="true" Name={B.a(name)} ItemLayer="{B.LAYER}" '
                f'{color_attrs(it["fill"], it["tint"], it["stroke"], it["sw"], it["stint"])} AppliedObjectStyle={B.a("ObjectStyle/" + ostyle)} '
                f'ItemTransform="1 0 0 1 0 0">{geom(pts)}{extra}</{tag}>')
    if it['t'] == 'line':
        pts = [((fx(x), sy(y)),) * 3 for x, y in it['pts']]
        return (f'<GraphicLine Self="{nid()}" ContentType="Unassigned" Visible="true" Name="$ID/" ItemLayer="{B.LAYER}" '
                f'{color_attrs(None, None, it["stroke"], it["sw"], it["tint"])} EndCap="{it["cap"]}" '
                + ('StrokeType="StrokeStyle/$ID/Canned Dashed 3x2" ' if it.get('dash') else '')
                + f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">{geom(pts, open_=len(pts) > 1)}</GraphicLine>')
    if it['t'] == 'oval':
        cx, cy, r = it['cx'], it['cy'], it['r']
        k = 0.5523 * r
        raw = [((cx, cy + r), (cx - k, cy + r), (cx + k, cy + r)), ((cx + r, cy), (cx + r, cy + k), (cx + r, cy - k)),
               ((cx, cy - r), (cx + k, cy - r), (cx - k, cy - r)), ((cx - r, cy), (cx - r, cy - k), (cx - r, cy + k))]
        pts = [tuple((fx(p_[0]), sy(p_[1])) for p_ in trip) for trip in raw]
        return (f'<Oval Self="{nid()}" ContentType="Unassigned" StoryTitle="$ID/" Visible="true" Name="$ID/" ItemLayer="{B.LAYER}" '
                f'{color_attrs(it["fill"], it["tint"], it["stroke"], it["sw"], it["stint"])} AppliedObjectStyle="ObjectStyle/$ID/[None]" '
                f'ItemTransform="1 0 0 1 0 0">{geom(pts)}</Oval>')
    if it['t'] == 'arc':
        raw = arc_points(it['cx'], it['cy'], it['r'], it['a0'], it['a1'])
        pts = [tuple((fx(p_[0]), sy(p_[1])) for p_ in trip) for trip in raw]
        return (f'<GraphicLine Self="{nid()}" ContentType="Unassigned" Visible="true" Name="$ID/" ItemLayer="{B.LAYER}" '
                f'{color_attrs(None, None, it["stroke"], it["sw"], it["tint"])} EndCap="{it["cap"]}" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
                f'ItemTransform="1 0 0 1 0 0">{geom(pts, open_=True)}</GraphicLine>')
    if it['t'] == 'text':
        x1, y1, x2, y2 = fx(it['x']), sy(it['y']), fx(it['x'] + it['w']), sy(it['y'] + it['h'])
        transform = '1 0 0 1 0 0'
        if it.get('rot'):
            # iç kutu: genişlik = alan yüksekliği, yükseklik = alan genişliği; saat yönü tersine 90°
            iw, ih = it['h'] * MM, it['w'] * MM
            transform = f'0 -1 1 0 {B.fmt(x1)} {B.fmt(y2)}'
            x1, y1, x2, y2 = 0.0, 0.0, iw, ih
        pts = [((x1, y1),) * 3, ((x1, y2),) * 3, ((x2, y2),) * 3, ((x2, y1),) * 3]
        fid = it['fid']
        return (f'<TextFrame Self="{fid}" ParentStory="{it["story"]}" PreviousTextFrame="{it["prev"]}" NextTextFrame="{it["next"]}" '
                f'ContentType="TextType" ItemLayer="{B.LAYER}" FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
                f'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" ItemTransform="{transform}" Visible="true" Name="$ID/">'
                f'{geom(pts)}<TextFramePreference TextColumnCount="{it["cols"]}" TextColumnGutter="{B.fmt(it["gutter"] * MM)}" '
                f'AutoSizingType="Off" VerticalJustification="{it["valign"]}" /></TextFrame>')
    raise ValueError(it['t'])


def story_xml(sid, paras):
    s = B.Story(sid)
    for p_ in paras:
        if p_[0] == 'TABLE':
            s.table(p_[1])
            continue
        body = []
        for r in p_[1]:
            if r == PAGENUM:
                body.append('<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Content><?ACE 18?></Content></CharacterStyleRange>')
                continue
            cs, txt = (r if isinstance(r, tuple) else ('$ID/[No character style]', r))
            body.append(f'<CharacterStyleRange AppliedCharacterStyle={B.a("CharacterStyle/" + cs)}><Content>{escape(txt)}</Content></CharacterStyleRange>')
        body.append('<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Br /></CharacterStyleRange>')
        s.parts.append(f'<ParagraphStyleRange AppliedParagraphStyle={B.a("ParagraphStyle/" + p_[0])}>{"".join(body)}</ParagraphStyleRange>')
    return s.xml()


def master_xml(mid, name, prefix, base, mpages):
    sec = 'uSec1'
    parts = [B.page_xml(f'{mid}p1', prefix, 'L', 'n', sec).replace(' AppliedAlternateLayout="uSec1"', ''),
             B.page_xml(f'{mid}p2', prefix, 'R', 'n', sec).replace(' AppliedAlternateLayout="uSec1"', '')]
    for mp in mpages:
        for it in mp.items:
            parts.append(item_xml(mp, it))
    return (B.HEAD + f'<idPkg:MasterSpread xmlns:idPkg="{B.PKG}" DOMVersion="{B.DOM}">\n'
            f'<MasterSpread Self="{mid}" Name="{name}" NamePrefix="{prefix}" BaseName="{base}" ShowMasterItems="true" PageCount="2" '
            f'OverriddenPageItemProps="" PrimaryTextFrame="n" ItemTransform="1 0 0 1 0 0">' + ''.join(parts) + '</MasterSpread>\n</idPkg:MasterSpread>\n')


def footer_story(sid, left):
    st = B.Story(sid)
    if left:
        st.raw_para('50 Sayfa Numarası', '<Content><?ACE 18?></Content><Content>   2026 FAALİYET RAPORU</Content>')
    else:
        st.parts.append('<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/50 Sayfa Numarası" Justification="RightAlign">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Content>BÜYÜKÇEKMECE BELEDİYESİ   </Content><Content><?ACE 18?></Content></CharacterStyleRange></ParagraphStyleRange>')
    return st.xml()


def build_idml(pages, name='Civensa_Ozel_Tasarim_v2'):
    B.SRC = os.path.join(HERE, '..', 'idml')
    os.makedirs(OUT, exist_ok=True)
    define_styles()
    graphic, swatch_ids = B.build_graphic()
    styles = B.build_styles().replace('<AppliedFont type="string">Fira Sans</AppliedFont>', '<AppliedFont type="string">Literata</AppliedFont>', 1)

    # metin çerçevelerine kimlik ve zincir bağları
    frames_by_story = {}
    for pg in pages + [mp for pair in MASTER_PAGES.values() for mp in pair]:
        for it in pg.items:
            if it['t'] == 'text':
                it['fid'] = nid('uTF')
                frames_by_story.setdefault(it['story'], []).append(it)
    for sid, frs in frames_by_story.items():
        for i, it in enumerate(frs):
            it['prev'] = frs[i - 1]['fid'] if i else 'n'
            it['next'] = frs[i + 1]['fid'] if i + 1 < len(frs) else 'n'

    stories = {sid: story_xml(sid, STORIES[sid]) for sid in frames_by_story}
    masters = {k: (f'uM{k}', v[0], v[1], v[2]) for k, v in MASTERS.items()}
    master_files = {f'MasterSpreads/MasterSpread_{m[0]}.xml': master_xml(*m, MASTER_PAGES[k]) for k, m in masters.items()}

    sec = 'uSec1'
    spreads_pages = [[0]] + [[i, i + 1] if i + 1 < len(pages) else [i] for i in range(1, len(pages), 2)]
    spreads = []
    first_page = None
    for si, plist in enumerate(spreads_pages):
        sid = f'uSp{si}'
        parts = []
        for pi in plist:
            pid = f'uPg{pi}'
            first_page = first_page or pid
            pg = pages[pi]
            parts.append(B.page_xml(pid, str(pi + 1), pg.side, masters[pg.master][0], sec))
        for pi in plist:
            for it in pages[pi].items:
                parts.append(item_xml(pages[pi], it))
        binding = 1 if len(plist) == 2 else (0 if pages[plist[0]].side == 'R' else 1)
        spreads.append((sid, B.HEAD + f'<idPkg:Spread xmlns:idPkg="{B.PKG}" DOMVersion="{B.DOM}">\n'
                        f'<Spread Self="{sid}" PageTransitionType="None" PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium" '
                        f'ShowMasterItems="true" PageCount="{len(plist)}" BindingLocation="{binding}" SpreadHidden="false" AllowPageShuffle="true" '
                        f'ItemTransform="1 0 0 1 0 {B.fmt(si * (H + 40.0))}" FlattenerOverride="Default">'
                        + ''.join(parts) + '</Spread>\n</idPkg:Spread>\n'))

    d = open(os.path.join(B.SRC, 'designmap.xml'), encoding='utf-8').read()
    head_end = d.find('<Document ')
    pis, body = d[:head_end], d[head_end:]
    chunks = re.split(r'\n\t(?=<[A-Za-z])', body)
    doc_open, rest = chunks[0], chunks[1:]
    drop = ('<idPkg:Story', '<idPkg:Spread', '<idPkg:MasterSpread', '<Section', '<Hyperlink', '<Bookmark', '<ColorGroup', '<Layer',
            '<Assignment', '<CrossReferenceFormat', '<HyperlinkURLDestination', '<HyperlinkPageDestination', '<HyperlinkTextDestination', '<HyperlinkTextSource')
    last = rest[-1]
    rest[-1] = last[:last.rfind('</Document>')].rstrip()
    kept = [c for c in rest if not c.startswith(drop)]
    story_ids = list(stories)
    doc_open = re.sub(r'StoryList="[^"]*"', f'StoryList="{" ".join(story_ids)}"', doc_open)
    doc_open = re.sub(r'Name="[^"]*\.indd"', f'Name="{name}.indd"', doc_open)
    doc_open = re.sub(r'ActiveLayer="[^"]*"', f'ActiveLayer="{B.LAYER}"', doc_open)
    layer = (f'<Layer Self="{B.LAYER}" Name="Katman 1" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true" LockGuides="false" UI="true" Expendable="true" Printable="true">'
             '<Properties><LayerColor type="enumeration">LightBlue</LayerColor></Properties></Layer>')
    mine = [layer] + [f'<idPkg:MasterSpread src="{f}" />' for f in master_files]
    mine += [f'<idPkg:Spread src="Spreads/Spread_{sid}.xml" />' for sid, _ in spreads]
    mine.append(f'<Section Self="{sec}" Length="{len(pages)}" Name="" ContinueNumbering="false" IncludeSectionPrefix="false" Marker="" PageStart="{first_page}" '
                f'SectionPrefix="" PageNumberStart="1" AlternateLayoutLength="{len(pages)}" AlternateLayout="Custom V">'
                '<Properties><PageNumberStyle type="enumeration">Arabic</PageNumberStyle></Properties></Section>')
    after_backing = [f'<idPkg:Story src="Stories/Story_{sid}.xml" />' for sid in story_ids]
    cg = ['<ColorGroup Self="ColorGroup/[Root Color Group]" Name="[Root Color Group]" IsRootColorGroup="true">']
    cg += [f'\t\t<ColorGroupSwatch Self="CG_{i}" SwatchItemRef={B.a(ref)} />' for i, ref in enumerate(swatch_ids)]
    cg.append('\t</ColorGroup>')
    out = []
    for c in kept:
        if c.startswith('<DocumentUser') and mine:
            out.extend(mine); mine = []
        out.append(c)
        if c.startswith('<idPkg:BackingStory'):
            out.extend(after_backing)
    out.extend(mine)
    out.append('\n'.join(cg))
    designmap = pis + doc_open + ''.join('\n\t' + c for c in out) + '\n</Document>\n'
    designmap = designmap.replace('ParagraphStyle/SEPERATOR', 'ParagraphStyle/$ID/NormalParagraphStyle')

    prefs = open(os.path.join(B.SRC, 'Resources', 'Preferences.xml'), encoding='utf-8').read()
    prefs = prefs.replace('ParagraphStyle/BOLUM BASLIK 2', 'ParagraphStyle/05 Gövde')
    prefs = re.sub(r'(<TextDefault [^>]*?)AppliedLanguage="[^"]*"', r'\1AppliedLanguage="$ID/Turkish"', prefs)
    prefs = re.sub(r'PageHeight="[^"]*"', f'PageHeight="{B.fmt(H)}"', prefs)
    prefs = re.sub(r'PageWidth="[^"]*"', f'PageWidth="{B.fmt(W)}"', prefs)

    files = {
        'designmap.xml': designmap, 'Resources/Graphic.xml': graphic, 'Resources/Fonts.xml': B.build_fonts(),
        'Resources/Styles.xml': styles, 'Resources/Preferences.xml': prefs,
        'XML/BackingStory.xml': open(os.path.join(B.SRC, 'XML', 'BackingStory.xml'), encoding='utf-8').read(),
        'XML/Tags.xml': open(os.path.join(B.SRC, 'XML', 'Tags.xml'), encoding='utf-8').read(),
        'META-INF/container.xml': open(os.path.join(B.SRC, 'META-INF', 'container.xml'), encoding='utf-8').read(),
    }
    files.update(master_files)
    for sid, x in spreads:
        files[f'Spreads/Spread_{sid}.xml'] = x
    for sid, x in stories.items():
        files[f'Stories/Story_{sid}.xml'] = x
    missing = B.check_style_refs(list(files.values()), styles)
    if missing:
        raise SystemExit(f'tanımsız stil: {missing}')
    target = os.path.join(OUT, f'{name}.idml')
    with zipfile.ZipFile(target, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/vnd.adobe.indesign-idml-package', compress_type=zipfile.ZIP_STORED)
        for name, text in files.items():
            z.writestr(name, text.encode('utf-8'), compress_type=zipfile.ZIP_DEFLATED)
    import xml.dom.minidom
    for name, text in files.items():
        xml.dom.minidom.parseString(text.encode('utf-8'))
    return target


if __name__ == '__main__':
    pages = build_pages()
    print('sayfa', len(pages))
    print('IDML', build_idml(pages))
    import onizleme
    print('PDF', onizleme.render(pages, STORIES, STY, RGB, CELLSTY, os.path.join(OUT, 'Civensa_Ozel_Tasarim_v2_onizleme.pdf'), MASTER_PAGES))
    for w_ in B.warnings:
        print('UYARI', w_)
