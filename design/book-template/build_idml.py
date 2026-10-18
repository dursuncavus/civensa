"""Build the Civensa book starter template as IDML (InDesign Markup Language).

Scaffold resources (preferences, default styles, inks, stroke styles) are taken from the
real d3 print IDML so InDesign gets a document it already produced; everything visible
(styles, swatches, masters, pages, stories, tables) is generated here.
"""
import os, re, zipfile, html, uuid
from xml.sax.saxutils import escape, quoteattr
import data as D
from fontmetrics import width

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'idml')
OUT = os.path.join(HERE, 'out')
MM = 72 / 25.4
W, H = 566.9291338582677, 793.7007874015748
M_TOP, M_BOT, M_IN, M_OUT = 20 * MM, 22 * MM, 20 * MM, 15 * MM
TW = W - M_IN - M_OUT            # text width
TH = H - M_TOP - M_BOT           # text height
DOM = '19.5'
PKG = 'http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging'
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
LAYER = 'uLay1'
warnings = []


def a(v):
    return quoteattr(str(v))


def fmt(x):
    return repr(round(float(x), 6)).rstrip('0').rstrip('.') if isinstance(x, float) else str(x)


# ----------------------------------------------------------------------------- colours
COLORS = [  # name, CMYK
    ('Kurumsal Ana', '100 70 10 25'),
    ('Kurumsal Vurgu', '0 65 95 0'),
    ('Metin Koyu', '0 0 0 90'),
    ('Çizgi Gri', '0 0 0 35'),
    ('Zemin Gri', '0 0 0 6'),
    # chart colours = the SVG chart palette (#2a78d6 #eb6834 #1baf7a #eda100 #e87ba4 #008300), simple CMYK conversion
    ('Grafik 1', '80 44 0 16'), ('Grafik 2', '0 56 78 8'), ('Grafik 3', '85 0 30 31'),
    ('Grafik 4', '0 32 100 7'), ('Grafik 5', '0 47 29 9'), ('Grafik 6', '100 0 100 49'),
]
KEEP_COLORS = {'Color/Black', 'Color/Paper', 'Color/Registration', 'Color/C=21 M=51 Y=100 K=11'}


def C(name):
    return 'Color/' + name


def build_graphic():
    g = open(os.path.join(SRC, 'Resources', 'Graphic.xml'), encoding='utf-8').read()
    # drop non-default colours and gradients of the old design
    def keep(m):
        return m.group(0) if m.group(1) in KEEP_COLORS else ''
    g = re.sub(r'\n\t<Color Self="([^"]+)"[^>]*/>', keep, g)
    g = re.sub(r'\n\t<Gradient .*?</Gradient>', '', g, flags=re.S)
    g = re.sub(r'\n\t<PastedSmoothShade .*?(?:/>|</PastedSmoothShade>)', '', g, flags=re.S)
    swatch_refs = []
    def reref(m):
        swatch_refs.append(m.group(1))
        return m.group(0)
    re.sub(r'<(?:Color|Swatch) Self="([^"]+)"', reref, g)
    new = []
    for name, cmyk in COLORS:
        new.append(f'\t<Color Self={a(C(name))} Model="Process" Space="CMYK" ColorValue="{cmyk}" ColorOverride="Normal" '
                   f'ConvertToHsb="false" AlternateSpace="NoAlternateColor" AlternateColorValue="" Name={a(name)} '
                   f'ColorEditable="true" ColorRemovable="true" Visible="true" SwatchCreatorID="7937" SwatchColorGroupReference="CG_{len(swatch_refs) + len(new)}" />')
    i = g.find('\n\t<Ink ')
    g = g[:i] + '\n' + '\n'.join(new) + g[i:]
    # renumber all colour-group references
    ids = []
    def renum(m):
        ids.append(m.group(1))
        return f'{m.group(0).split("SwatchColorGroupReference=")[0]}SwatchColorGroupReference="CG_{len(ids) - 1}"'
    g = re.sub(r'<(?:Color|Swatch) Self="([^"]+)"[^>]*?SwatchColorGroupReference="[^"]*"', renum, g)
    return g, ids


# ----------------------------------------------------------------------------- styles
PS, CS, CELL, TS = [], [], [], []   # generated style XML snippets


def props(font=None, leading=None, based='$ID/[No paragraph style]', extra=''):
    p = []
    if leading is not None:
        p.append(f'<Leading type="unit">{fmt(leading)}</Leading>')
    if font:
        p.append(f'<AppliedFont type="string">{escape(font)}</AppliedFont>')
    if based.startswith('$ID/'):
        p.append(f'<BasedOn type="string">{escape(based)}</BasedOn>')
    else:
        p.append(f'<BasedOn type="object">ParagraphStyle/{escape(based)}</BasedOn>')
    return '<Properties>' + ''.join(p) + extra + '</Properties>'


PARA = {}   # name -> (family, style, size)


def para(name, family, style, size, leading, just='LeftAlign', color='Metin Koyu', based='$ID/[No paragraph style]', extra_props='', **attrs):
    PARA[name] = (family, style, size)
    base = dict(FontStyle=style, PointSize=fmt(size), Justification=just, FillColor=C(color),
                AppliedLanguage='$ID/Turkish', KerningMethod='$ID/Optical')
    base.update({k: fmt(v) if isinstance(v, float) else v for k, v in attrs.items()})
    at = ' '.join(f'{k}={a(v)}' for k, v in base.items())
    PS.append(f'\t\t<ParagraphStyle Self={a("ParagraphStyle/" + name)} Name={a(name)} NextStyle={a("ParagraphStyle/" + name)} {at}>'
              f'{props(family, leading, based, extra_props)}</ParagraphStyle>')


def charst(name, **attrs):
    at = ' '.join(f'{k}={a(v)}' for k, v in attrs.items())
    CS.append(f'\t\t<CharacterStyle Self={a("CharacterStyle/" + name)} Name={a(name)} {at}>'
              f'<Properties><BasedOn type="string">$ID/[No character style]</BasedOn></Properties></CharacterStyle>')


def edge(prefix, weight, color='Çizgi Gri'):
    return {f'{prefix}EdgeStrokeWeight': fmt(weight), f'{prefix}EdgeStrokeColor': C(color),
            f'{prefix}EdgeStrokeType': 'StrokeStyle/$ID/Solid', f'{prefix}EdgeStrokeTint': '100'}


def cell(name, pstyle, fill=None, tint=None, valign='TopAlign', inset=(2.5, 3, 2.5, 3), top=None, bottom=(0.25, 'Çizgi Gri'), left=0, right=0):
    t, l, b, r = inset
    at = dict(AppliedParagraphStyle='ParagraphStyle/' + pstyle, TopInset=fmt(t), LeftInset=fmt(l), BottomInset=fmt(b), RightInset=fmt(r),
              VerticalJustification=valign, FillColor=C(fill) if fill else 'Swatch/None')
    if tint is not None:
        at['FillTint'] = fmt(tint)
    at.update(edge('Left', left)); at.update(edge('Right', right))
    at.update(edge('Top', top[0], top[1]) if top else edge('Top', 0))
    at.update(edge('Bottom', bottom[0], bottom[1]) if bottom else edge('Bottom', 0))
    s = ' '.join(f'{k}={a(v)}' for k, v in at.items())
    CELL.append(f'\t\t<CellStyle Self={a("CellStyle/" + name)} Name={a(name)} {s}>'
                f'<Properties><BasedOn type="string">$ID/[None]</BasedOn></Properties></CellStyle>')


def tablestyle(name, header_cell, body_cell):
    at = dict(HeaderRegionSameAsBodyRegion='false', HeaderRegionCellStyle='CellStyle/' + header_cell,
              BodyRegionCellStyle='CellStyle/' + body_cell, FooterRegionSameAsBodyRegion='true', FooterRegionCellStyle='n',
              LeftColumnRegionSameAsBodyRegion='true', LeftColumnRegionCellStyle='n',
              RightColumnRegionSameAsBodyRegion='true', RightColumnRegionCellStyle='n',
              TopBorderStrokeWeight='0', LeftBorderStrokeWeight='0', RightBorderStrokeWeight='0',
              BottomBorderStrokeWeight='0.75', BottomBorderStrokeColor=C('Kurumsal Ana'), BottomBorderStrokeType='StrokeStyle/$ID/Solid',
              SpaceBefore='4', SpaceAfter='6')
    s = ' '.join(f'{k}={a(v)}' for k, v in at.items())
    TS.append(f'\t\t<TableStyle Self={a("TableStyle/" + name)} Name={a(name)} {s}>'
              f'<Properties><BasedOn type="string">$ID/[Basic Table]</BasedOn></Properties></TableStyle>')


FS, FC, FX = 'Fira Sans', 'Fira Sans Condensed', 'Fira Sans Extra Condensed'
TAB = 'TabularLining'


def define_styles():
    # 01 headings / text
    para('01 Bölüm Başlığı', FS, 'SemiBold', 22, 26, color='Kurumsal Ana', SpaceAfter=14 * 1.0, KeepWithNext='2', Hyphenation='false')
    para('02 Ara Başlık 1', FS, 'SemiBold', 14, 17, color='Kurumsal Ana', SpaceBefore=16.0, SpaceAfter=6.0, KeepWithNext='2', Hyphenation='false')
    para('03 Ara Başlık 2', FS, 'Medium', 11, 14, SpaceBefore=10.0, SpaceAfter=4.0, KeepWithNext='2', Hyphenation='false')
    para('04 Ara Başlık 3', FS, 'SemiBold', 8.5, 11, color='Kurumsal Ana', Capitalization='AllCaps', Tracking='40', SpaceBefore=8.0, SpaceAfter=3.0, KeepWithNext='2', Hyphenation='false')
    para('05 Gövde', FS, 'Regular', 9.5, 13.5, just='LeftJustified', SpaceAfter=4.0, Hyphenation='true')
    para('06 Gövde Giriş', FS, 'Light', 11.5, 15.5, SpaceAfter=8.0)
    para('07 Madde', FS, 'Regular', 9.5, 13.5, based='05 Gövde', LeftIndent=12.0, FirstLineIndent=-12.0, SpaceAfter=2.0,
         BulletsAndNumberingListType='BulletList', BulletsTextAfter='^t',
         extra_props='<BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="8226" />')
    para('08 Dipnot', FS, 'Regular', 7, 9, SpaceBefore=4.0)
    # 10 tables
    para('10 Tablo Başlık', FC, 'SemiBold', 7, 8.5, just='CenterAlign', color='Paper', Hyphenation='false')
    para('11 Tablo Başlık Sol', FC, 'SemiBold', 7, 8.5, color='Paper', Hyphenation='false')
    para('12 Tablo Etiket', FC, 'SemiBold', 7, 9, color='Kurumsal Ana', Hyphenation='false')
    para('13 Tablo Metin', FC, 'Regular', 7, 9, Hyphenation='true')
    para('14 Tablo Metin Uzun', FS, 'Regular', 7.5, 10.5, just='LeftJustified', SpaceAfter=3.0, Hyphenation='true')
    para('15 Tablo Alt Satır', FC, 'Italic', 6.5, 8.5, LeftIndent=8.0)
    para('16 Tablo Toplam Etiket', FC, 'SemiBold', 7, 9)
    para('17 Tablo Rakam', FX, 'Regular', 7, 9, just='RightAlign', OTFFigureStyle=TAB, Hyphenation='false', NoBreak='true')
    para('18 Tablo Rakam Toplam', FX, 'SemiBold', 7, 9, just='RightAlign', OTFFigureStyle=TAB, Hyphenation='false', NoBreak='true')
    para('19 Tablo Rakam Gösterge', FC, 'Regular', 7, 9, just='RightAlign', OTFFigureStyle=TAB, Hyphenation='false', NoBreak='true')
    para('20 Tablo Rakam Geniş Tablo', FX, 'Regular', 6.3, 8, just='RightAlign', OTFFigureStyle=TAB, Hyphenation='false', NoBreak='true')
    para('21 Tablo Kaynak', FC, 'Italic', 6.5, 8, SpaceBefore=2.0, SpaceAfter=10.0)
    para('22 Tablo Kapsayıcı', FS, 'Regular', 4, 4, SpaceAfter=2.0)
    # 30 charts / navigation
    para('30 Grafik Başlığı', FS, 'SemiBold', 9, 11, color='Kurumsal Ana', SpaceBefore=8.0, SpaceAfter=4.0, KeepWithNext='1')
    para('31 Grafik Kaynak', FC, 'Italic', 6.5, 8, SpaceBefore=2.0)
    para('40 İçindekiler Bölüm', FS, 'SemiBold', 10, 14, color='Kurumsal Ana', SpaceBefore=6.0,
         extra_props=f'<TabList type="list"><ListItem type="record"><Alignment type="enumeration">RightAlign</Alignment><AlignmentCharacter type="string">.</AlignmentCharacter><Leader type="string"> </Leader><Position type="unit">{fmt(TW)}</Position></ListItem></TabList>')
    para('41 İçindekiler Metin', FS, 'Regular', 9, 13, LeftIndent=10.0, OTFFigureStyle=TAB,
         extra_props=f'<TabList type="list"><ListItem type="record"><Alignment type="enumeration">RightAlign</Alignment><AlignmentCharacter type="string">.</AlignmentCharacter><Leader type="string">. </Leader><Position type="unit">{fmt(TW)}</Position></ListItem></TabList>')
    para('50 Sayfa Numarası', FC, 'Medium', 8, 10, OTFFigureStyle=TAB)
    para('51 Üst Bilgi', FC, 'Regular', 7, 10, color='Çizgi Gri', Capitalization='AllCaps', Tracking='60')
    # character styles
    charst('Kalın', FontStyle='SemiBold')
    charst('İtalik', FontStyle='Italic')
    charst('Rakam Tabular', OTFFigureStyle=TAB)
    charst('Vurgu Renk', FillColor=C('Kurumsal Vurgu'))
    # cell styles
    cell('Hücre Başlık', '10 Tablo Başlık', fill='Kurumsal Ana', valign='CenterAlign', bottom=(0.5, 'Paper'), right=0)
    cell('Hücre Başlık Sol', '11 Tablo Başlık Sol', fill='Kurumsal Ana', valign='CenterAlign', bottom=(0.5, 'Paper'))
    cell('Hücre Etiket', '12 Tablo Etiket', fill='Kurumsal Ana', tint=10, bottom=(0.5, 'Paper'))
    cell('Hücre Bölüm Satırı', '12 Tablo Etiket', fill='Kurumsal Ana', tint=25, valign='CenterAlign', bottom=(0.5, 'Paper'))
    cell('Hücre Metin', '13 Tablo Metin')
    cell('Hücre Metin Uzun', '14 Tablo Metin Uzun', inset=(3, 3, 1.5, 3))
    cell('Hücre Rakam', '17 Tablo Rakam')
    cell('Hücre Rakam Gösterge', '19 Tablo Rakam Gösterge')
    cell('Hücre Rakam Geniş', '20 Tablo Rakam Geniş Tablo', inset=(2, 1.5, 2, 1.5))
    cell('Hücre Alt Satır', '15 Tablo Alt Satır', bottom=(0.25, 'Zemin Gri'))
    cell('Hücre Alt Satır Rakam', '17 Tablo Rakam', bottom=(0.25, 'Zemin Gri'))
    cell('Hücre Toplam', '16 Tablo Toplam Etiket', fill='Kurumsal Ana', tint=12, top=(0.75, 'Kurumsal Ana'), bottom=(0.75, 'Kurumsal Ana'))
    cell('Hücre Toplam Rakam', '18 Tablo Rakam Toplam', fill='Kurumsal Ana', tint=12, top=(0.75, 'Kurumsal Ana'), bottom=(0.75, 'Kurumsal Ana'))
    tablestyle('Tablo Standart', 'Hücre Başlık', 'Hücre Metin')
    tablestyle('Tablo Kart', 'Hücre Başlık', 'Hücre Metin')


def build_styles():
    s = open(os.path.join(SRC, 'Resources', 'Styles.xml'), encoding='utf-8').read()
    # keep only $ID/ default styles in every root group
    def strip(group, tag):
        nonlocal s
        m = re.search(rf'(<{group} [^>]*>)(.*?)(\n\t</{group}>)', s, re.S)
        body = m.group(2)
        kept = [x.group(0) for x in re.finditer(rf'\n\t\t<{tag} Self="{tag}/\$ID/[^"]*".*?(?:/>|</{tag}>)', body, re.S)
                if not x.group(0).split('>', 1)[0].endswith('/') or True]
        # an element is either self-closing or has a closing tag; the regex above is lazy, fix nested
        kept = []
        for x in re.finditer(rf'\n\t\t<{tag} Self="({tag}/[^"]*)"', body):
            start = x.start()
            close_self = body.find('/>', start)
            close_full = body.find(f'</{tag}>', start)
            gt = body.find('>', start)
            end = gt + 1 if body[gt - 1] == '/' else close_full + len(f'</{tag}>')
            if '$ID/' in x.group(1):
                kept.append(body[start:end])
        return m, kept
    out = s
    for group, tag, extra in [('RootCharacterStyleGroup', 'CharacterStyle', CS), ('RootParagraphStyleGroup', 'ParagraphStyle', PS),
                              ('RootCellStyleGroup', 'CellStyle', CELL), ('RootTableStyleGroup', 'TableStyle', TS)]:
        m, kept = strip(group, tag)
        body = ''.join(kept) + '\n' + '\n'.join(extra)
        out = out.replace(m.group(0), m.group(1) + body + m.group(3))
        s = out
    # default text: Fira Sans, Turkish
    out = out.replace('<AppliedFont type="string">Minion Pro</AppliedFont>', '<AppliedFont type="string">Fira Sans</AppliedFont>', 1)
    out = re.sub(r'(<ParagraphStyle Self="ParagraphStyle/\$ID/\[No paragraph style\]"[^>]*?)AppliedLanguage="[^"]*"', r'\1AppliedLanguage="$ID/Turkish"', out, count=1)
    # remove user TOC styles referring to deleted paragraph styles
    out = re.sub(r'\n\t<TOCStyle Self="TOCStyle/(?!\$ID/).*?</TOCStyle>', '', out, flags=re.S)
    out = re.sub(r'\n\t\t<TOCStyleEntry .*?</TOCStyleEntry>', '', out, flags=re.S)
    # object styles: keep defaults only
    m = re.search(r'(<RootObjectStyleGroup [^>]*>)(.*?)(\n\t</RootObjectStyleGroup>)', out, re.S)
    body = m.group(2); kept = []
    for x in re.finditer(r'\n\t\t<ObjectStyle Self="(ObjectStyle/[^"]*)"', body):
        start = x.start(); gt = body.find('>', start)
        end = gt + 1 if body[gt - 1] == '/' else body.find('</ObjectStyle>', start) + len('</ObjectStyle>')
        if '$ID/' in x.group(1):
            kept.append(body[start:end])
    out = out.replace(m.group(0), m.group(1) + ''.join(kept) + m.group(3))
    return out


def check_style_refs(xml_texts, styles_xml):
    defined = set(re.findall(r'Self="((?:ParagraphStyle|CharacterStyle|CellStyle|TableStyle|ObjectStyle)/[^"]*)"', styles_xml))
    used = set()
    for t in xml_texts:
        used |= set(re.findall(r'"((?:ParagraphStyle|CharacterStyle|CellStyle|TableStyle|ObjectStyle)/[^"]*)"', t))
        used |= set('ParagraphStyle/' + x for x in re.findall(r'<BasedOn type="object">ParagraphStyle/([^<]*)<', t))
    missing = sorted(u for u in used if u not in defined and not u.endswith('/n'))
    return missing


# ----------------------------------------------------------------------------- stories
class Story:
    def __init__(self, sid):
        self.sid = sid
        self.parts = []
        self.tcount = 0

    def p(self, style, *runs):
        """runs: str or (charstyle, str)."""
        body = []
        for r in runs:
            cs, txt = (r if isinstance(r, tuple) else ('$ID/[No character style]', r))
            body.append(f'<CharacterStyleRange AppliedCharacterStyle={a("CharacterStyle/" + cs)}><Content>{escape(txt)}</Content></CharacterStyleRange>')
        body.append('<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Br /></CharacterStyleRange>')
        self.parts.append(f'<ParagraphStyleRange AppliedParagraphStyle={a("ParagraphStyle/" + style)}>{"".join(body)}</ParagraphStyleRange>')

    def raw_para(self, style, inner):
        self.parts.append(f'<ParagraphStyleRange AppliedParagraphStyle={a("ParagraphStyle/" + style)}>'
                          f'<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">{inner}<Br /></CharacterStyleRange></ParagraphStyleRange>')

    def table(self, t):
        self.tcount += 1
        self.raw_para('22 Tablo Kapsayıcı', t.xml(f'{self.sid}t{self.tcount}'))

    def xml(self):
        return (HEAD + f'<idPkg:Story xmlns:idPkg="{PKG}" DOMVersion="{DOM}">\n'
                f'\t<Story Self="{self.sid}" UserText="true" IsEndnoteStory="false" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">\n'
                '\t\t<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection" />\n'
                '\t\t<InCopyExportOption IncludeGraphicProxies="true" IncludeAllResources="false" />\n\t\t'
                + '\n\t\t'.join(self.parts) + '\n\t</Story>\n</idPkg:Story>\n')


class Table:
    def __init__(self, widths, header_rows=0, style='Tablo Standart'):
        self.widths = widths
        self.header_rows = header_rows
        self.style = style
        self.rows = []   # list of list of cells (col, colspan, rowspan, cellstyle, pstyle, runs)

    def row(self, cells):
        """cells: list of (text|runs, cellstyle, pstyle, colspan)."""
        self.rows.append(cells)

    def xml(self, tid):
        ncol = len(self.widths)
        out = [f'<Table Self="{tid}" HeaderRowCount="{self.header_rows}" FooterRowCount="0" BodyRowCount="{len(self.rows) - self.header_rows}" '
               f'ColumnCount="{ncol}" AppliedTableStyle={a("TableStyle/" + self.style)} TableDirection="LeftToRightDirection">']
        for r in range(len(self.rows)):
            out.append(f'<Row Self="{tid}Row{r}" Name="{r}" SingleRowHeight="10" MinimumHeight="10" AutoGrow="true" />')
        for c, w in enumerate(self.widths):
            out.append(f'<Column Self="{tid}Column{c}" Name="{c}" SingleColumnWidth="{fmt(float(w))}" />')
        n = 0
        covered = set()
        for r, cells in enumerate(self.rows):
            col = 0
            for cdef in cells:
                while (col, r) in covered:
                    col += 1
                content, cstyle, pstyle, span = (list(cdef) + [1])[:4]
                rowspan = 1
                if isinstance(span, tuple):
                    span, rowspan = span
                for dc in range(span):
                    for dr in range(rowspan):
                        if dc or dr:
                            covered.add((col + dc, r + dr))
                runs = content if isinstance(content, list) else [content]
                paras = []
                cur = []
                for run in runs:
                    if run == '\n':
                        paras.append(cur); cur = []
                    else:
                        cur.append(run)
                paras.append(cur)
                inner = []
                for i, pr in enumerate(paras):
                    crs = []
                    for run in pr:
                        cs, txt = (run if isinstance(run, tuple) else ('$ID/[No character style]', run))
                        crs.append(f'<CharacterStyleRange AppliedCharacterStyle={a("CharacterStyle/" + cs)}><Content>{escape(txt)}</Content></CharacterStyleRange>')
                    if i < len(paras) - 1:
                        crs.append('<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Br /></CharacterStyleRange>')
                    if not crs:
                        crs.append('<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" />')
                    inner.append(f'<ParagraphStyleRange AppliedParagraphStyle={a("ParagraphStyle/" + pstyle)}>{"".join(crs)}</ParagraphStyleRange>')
                out.append(f'<Cell Self="{tid}i{n}" Name="{col}:{r}" RowSpan="{rowspan}" ColumnSpan="{span}" CellType="TextTypeCell" '
                           f'AppliedCellStyle={a("CellStyle/" + cstyle)} AppliedCellStylePriority="0">{"".join(inner)}</Cell>')
                # width check for numbers (no wrap allowed)
                if pstyle in ('17 Tablo Rakam', '18 Tablo Rakam Toplam', '19 Tablo Rakam Gösterge', '20 Tablo Rakam Geniş Tablo') and isinstance(content, str):
                    fam, sty, size = PARA[pstyle]
                    need = width(content, fam, sty, size) + (3 if pstyle.startswith('20') else 6)
                    have = sum(self.widths[col:col + span])
                    if need > have:
                        warnings.append(f'{tid}: "{content}" needs {need:.1f}pt, column has {have:.1f}pt')
                n += 1
                col += span
        out.append('</Table>')
        return ''.join(out)


def money_col(sample, pstyle, inset=6):
    fam, sty, size = PARA[pstyle]
    return width(sample, fam, sty, size) + inset + 2


def H_(t):
    return (t, 'Hücre Başlık', '10 Tablo Başlık')


def build_main_story(sid):
    s = Story(sid)
    s.p('51 Üst Bilgi', 'Civensa · Kitap şablonu · Sürüm 1 · Örnek veri')
    s.p('01 Bölüm Başlığı', 'Kitap Şablonu ve Stil Kılavuzu')
    s.p('06 Gövde Giriş', 'Bu dosya 2027 Performans Programı kitabının yeni tasarımı için başlangıç şablonudur. Tablolardaki metinler ve '
        'tutarlar gerçek kitaptaki en uzun değerlerden alındı; tutarlara güvenlik payı eklendi. Şablon bu uzunluklarda sorunsuz '
        'çalışıyorsa daha kısa verilerde de çalışır. İçerik doğru olmak zorunda değildir; yalnızca biçim içindir.')
    s.p('02 Ara Başlık 1', 'Font ailesi')
    s.p('05 Gövde', 'Şablonda tek aile kullanıldı: Fira Sans. Ailenin üç genişliği var: metin ve başlıklar için ', ('Kalın', 'Fira Sans'),
        ', tablo metinleri için ', ('Kalın', 'Fira Sans Condensed'), ', tablo rakamları için ', ('Kalın', 'Fira Sans Extra Condensed'),
        '. Her genişlikte dokuz ağırlık ve italikler bulunur; Türkçe karakterlerin tamamı ve ₺ işareti vardır. Lisansı ücretsizdir (SIL Open Font License); kitapta, web ekranlarında ve Word çıktısında aynı font kullanılabilir.')
    s.p('05 Gövde', 'Rakamların alt alta hizalanması için tablo rakam stillerinde OpenType “Tablo Biçiminde Hizalı” (Tabular Lining) seçeneği açıktır. '
        'Fira Sans’ın varsayılan rakamları orantılıdır; bu seçenek kapatılırsa rakamlar kayar. Yeni bir rakam stili oluştururken bu '
        'seçeneği koruyun. Fira Sans’ta normal ve kalın ağırlıkların tabular rakamları aynı genişliktedir; bu nedenle kalın toplam satırı da normal satırlarla aynı hizada kalır.')
    s.p('03 Ara Başlık 2', 'Stil adları ve sıralama')
    s.p('05 Gövde', 'Paragraf stilleri numaralıdır: 01–08 başlık ve metin, 10–22 tablo, 30–31 grafik, 40–41 içindekiler, 50–51 sayfa öğeleri. '
        'Hücre stilleri “Hücre …”, tablo stilleri “Tablo …” adını taşır. Renkler “Kurumsal Ana”, “Kurumsal Vurgu”, “Metin Koyu”, '
        '“Çizgi Gri”, “Zemin Gri” ve “Grafik 1–6” örnek renklerine bağlıdır; renk örneğini değiştirdiğinizde bütün stiller güncellenir.')
    s.p('04 Ara Başlık 3', 'Ara başlık 3 örneği')
    s.p('05 Gövde', D.UZUN_METIN)
    s.p('07 Madde', 'Madde işaretli liste örneği: kısa bir madde.')
    s.p('07 Madde', 'İkinci madde daha uzundur ve satırın sonuna ulaştığında ikinci satıra geçer; girinti madde işaretinin hizasını korur.')
    s.p('07 Madde', 'Üçüncü madde.')
    s.p('08 Dipnot', 'Dipnot örneği: Kaynak: Belediye Strateji Geliştirme Müdürlüğü, 2026.')

    # ---- T1 program card
    s.p('02 Ara Başlık 1', 'Tablo 1 — Performans Esaslı Program Bütçe Kartı')
    lab = 72.0
    unit = 46.0
    val = money_col(D.IND_MAX, '19 Tablo Rakam Gösterge')
    name2 = TW - lab - unit - 6 * val
    t = Table([lab, name2, unit] + [val] * 6, header_rows=0, style='Tablo Kart')
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
    t.row([('Performans Göstergesi', 'Hücre Başlık Sol', '11 Tablo Başlık Sol', 2), H_('Ölçü Birimi'), H_('2025 Gerçekleşme'),
           H_('2026 Planlanan'), H_('2026 Yıl Sonu Gerçekleşme Tahmini'), H_('2027 Hedef'), H_('2028 Tahmin'), H_('2029 Tahmin')])
    for name, unit_, vals in D.INDICATORS:
        t.row([(name, 'Hücre Metin', '13 Tablo Metin', 2), (unit_, 'Hücre Metin', '13 Tablo Metin')] +
              [(v, 'Hücre Rakam Gösterge', '19 Tablo Rakam Gösterge') for v in vals])
    kv('Göstergeye İlişkin Açıklama', D.G_ACIKLAMA, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Hesaplama Yöntemi', D.HESAPLAMA, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Verinin Kaynağı', D.KAYNAK, 'Hücre Metin Uzun', '14 Tablo Metin Uzun')
    kv('Sorumlu İdare', D.SORUMLU)
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: gerçek kitaptaki en uzun gerekçe (1.792 karakter), gösterge adı (164 karakter) ve ölçü birimi; gösterge değerleri 99.999.999 ile sınandı.')

    # ---- T2 activity costs (card)
    s.p('02 Ara Başlık 1', 'Tablo 2 — Alt Program Faaliyet Maliyetleri')
    mv = money_col(D.MONEY_UNIT, '17 Tablo Rakam')
    years = ['2026 Bütçe', '2026 Haziran Sonu Harcama', '2026 Yıl Sonu Harcama Tahmini', '2027 Bütçe', '2028 Tahmin', '2029 Tahmin']
    t = Table([TW - 6 * mv] + [mv] * 6, header_rows=2)
    t.row([('Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri', 'Hücre Başlık Sol', '11 Tablo Başlık Sol', 7)])
    t.row([('Faaliyetler', 'Hücre Başlık Sol', '11 Tablo Başlık Sol')] + [H_(y) for y in years])
    for name, vals in D.ACTIVITIES_CARD:
        t.row([(name, 'Hücre Metin', '13 Tablo Metin')] + [(v, 'Hücre Rakam', '17 Tablo Rakam') for v in vals])
    t.row([('TOPLAM', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(v, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam') for v in D.TOTAL_CARD])
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: en uzun faaliyet adı 272 karakter; tutarlar 9.999.999.999,99 TL ile sınandı. “-” veri yok, “0,00” sıfır anlamındadır.')

    # ---- T3 directorate activity costs with funding split
    s.p('02 Ara Başlık 1', 'Tablo 3 — Müdürlük Faaliyet Maliyetleri (Bütçe İçi / Bütçe Dışı)')
    t = Table([TW - 6 * mv] + [mv] * 6, header_rows=1)
    t.row([('Faaliyetler', 'Hücre Başlık Sol', '11 Tablo Başlık Sol')] + [H_(y) for y in years])
    for name, inside, outside in D.ACTIVITIES_ORTAK:
        total = []
        for x, y in zip(inside, outside):
            if x == '-' and y == '-':
                total.append('-')
            else:
                def num(v):
                    return 0.0 if v == '-' else float(v.replace('.', '').replace(',', '.'))
                total.append(D.tr_money(num(x) + num(y)))
        t.row([(name, 'Hücre Metin', '13 Tablo Metin')] + [(v, 'Hücre Rakam', '17 Tablo Rakam') for v in total])
        t.row([('Bütçe İçi', 'Hücre Alt Satır', '15 Tablo Alt Satır')] + [(v, 'Hücre Alt Satır Rakam', '17 Tablo Rakam') for v in inside])
        t.row([('Bütçe Dışı', 'Hücre Alt Satır', '15 Tablo Alt Satır')] + [(v, 'Hücre Alt Satır Rakam', '17 Tablo Rakam') for v in outside])
    t.row([('TOPLAM', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.MONEY_UNIT, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')] * 6)
    t.row([([('Kalın', 'Faaliyetlere ilişkin açıklama: '), D.UZUN_METIN], 'Hücre Metin Uzun', '14 Tablo Metin Uzun', 7)])
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: en uzun ortak tablo faaliyet adı 324 karakter; tablo içindeki açıklama paragrafı 930 karakter.')

    # ---- T4 economic classification
    s.p('02 Ara Başlık 1', 'Tablo 4 — Ekonomik Sınıflandırmaya Göre Kaynak İhtiyacı')
    code = 16.0
    t = Table([code, TW - code - 6 * mv] + [mv] * 6, header_rows=1)
    t.row([('Ekonomik Ad', 'Hücre Başlık Sol', '11 Tablo Başlık Sol', 2), H_('2025 Bütçe'), H_('2025 Haziran Sonu Harcama'),
           H_('2025 Yıl Sonu Harcama'), H_('2026 Bütçe'), H_('2027 Tahmin'), H_('2028 Tahmin')])
    for c, n in D.ECON_CATEGORIES:
        t.row([(c, 'Hücre Metin', '19 Tablo Rakam Gösterge'), (n, 'Hücre Metin', '13 Tablo Metin')] + [(D.MONEY_UNIT, 'Hücre Rakam', '17 Tablo Rakam')] * 6)
    for lbl in D.ECON_TOTALS:
        sub = lbl[0].islower() or lbl.startswith('Diğer')
        if sub:
            t.row([(lbl, 'Hücre Alt Satır', '15 Tablo Alt Satır', 2)] + [('0,00', 'Hücre Alt Satır Rakam', '17 Tablo Rakam')] * 6)
        else:
            t.row([(lbl, 'Hücre Toplam', '16 Tablo Toplam Etiket', 2)] + [(D.MONEY_UNIT, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')] * 6)
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: en uzun ekonomik ad “Sosyal Güvenlik Kurumlarına Devlet Primi Giderleri”.')

    # ---- T5 directorate distribution
    s.p('02 Ara Başlık 1', 'Tablo 5 — 2027 Yılı Bütçesinin Müdürlükler Bazında Dağılımı')
    rows, total = D.directorate_budget()
    pct = money_col('100,00', '17 Tablo Rakam') + 10
    amt = money_col(D.MONEY_IDARE, '17 Tablo Rakam') + 10
    t = Table([TW - pct - amt, amt, pct], header_rows=1)
    t.row([('Müdürlük Adı', 'Hücre Başlık Sol', '11 Tablo Başlık Sol'), H_('2027 Yılı Müdürlük Bütçesi (TL)'), H_('Toplam Bütçeye Oranı (%)')])
    for d, v, p in rows:
        t.row([(d, 'Hücre Metin', '13 Tablo Metin'), (v, 'Hücre Rakam', '17 Tablo Rakam'), (p, 'Hücre Rakam', '17 Tablo Rakam')])
    t.row([('TOPLAM', 'Hücre Toplam', '16 Tablo Toplam Etiket'), (D.MONEY_IDARE, 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam'), ('100,00', 'Hücre Toplam Rakam', '18 Tablo Rakam Toplam')])
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: 33 müdürlük; en uzun ad “Basın, Yayın ve Halkla İlişkiler Müdürlüğü”. Tablo sayfa sonunda bölündüğünde başlık satırı tekrarlanır.')

    # ---- charts note
    s.p('02 Ara Başlık 1', 'Grafikler')
    s.p('05 Gövde', 'Grafik örnekleri ayrı dosyalardadır (grafikler klasörü). SVG dosyaları Illustrator’da açıldığında yazılar canlı metin olarak gelir; '
        'fontu ve renkleri değiştirebilirsiniz. PDF dosyaları InDesign’a doğrudan yerleştirilebilir. Grafik başlığı ve kaynak satırı için '
        '“30 Grafik Başlığı” ve “31 Grafik Kaynak” stillerini kullanın.')
    s.p('30 Grafik Başlığı', 'Grafik 1 — Ekonomik Sınıflandırmaya Göre 2027 Bütçe Dağılımı')
    s.p('31 Grafik Kaynak', 'Kaynak: 2027 Yılı Performans Programı, Tablo 4.')
    s.p('02 Ara Başlık 1', 'İçindekiler örneği')
    s.p('40 İçindekiler Bölüm', 'Kitap Şablonu ve Stil Kılavuzu\t1')
    for i, x in enumerate(['Tablo 1 — Performans Esaslı Program Bütçe Kartı', 'Tablo 2 — Alt Program Faaliyet Maliyetleri',
                           'Tablo 3 — Müdürlük Faaliyet Maliyetleri', 'Tablo 4 — Ekonomik Sınıflandırma', 'Tablo 5 — Müdürlükler Bazında Dağılım']):
        s.p('41 İçindekiler Metin', f'{x}\t{2 + i * 2}')
    return s


def build_wide_story(sid):
    s = Story(sid)
    s.p('02 Ara Başlık 1', 'Tablo 6 — Ekonomik Koda Göre Program Grubu Dağılımı (yatay sayfa)')
    LW = TH   # landscape frame width = portrait text height
    mv = money_col(D.MONEY_IDARE, '20 Tablo Rakam Geniş Tablo', inset=3)
    first = LW - 12 * mv
    if first < 60:
        warnings.append(f'Tablo 6 first column only {first:.1f}pt')
    t = Table([first] + [mv] * 12, header_rows=2)
    t.row([('EKONOMİK KOD', 'Hücre Başlık Sol', '11 Tablo Başlık Sol', (1, 2)), ('2027 Bütçe', 'Hücre Başlık', '10 Tablo Başlık', 4),
           ('2028 Tahmin', 'Hücre Başlık', '10 Tablo Başlık', 4), ('2029 Tahmin', 'Hücre Başlık', '10 Tablo Başlık', 4)])
    sub = ['Hizmet Programları', 'Yönetim ve Destek Programı', 'Program Dışı Giderler', 'Toplam']
    t.row([H_(x) for x in sub * 3])
    for c, n in D.ECON_CATEGORIES:
        t.row([(f'{c} {n}', 'Hücre Metin', '13 Tablo Metin')] + [(D.MONEY_IDARE, 'Hücre Rakam Geniş', '20 Tablo Rakam Geniş Tablo')] * 12)
    t.row([('TOPLAM', 'Hücre Toplam', '16 Tablo Toplam Etiket')] + [(D.MONEY_IDARE, 'Hücre Toplam Rakam', '20 Tablo Rakam Geniş Tablo')] * 12)
    s.table(t)
    s.p('21 Tablo Kaynak', 'Örnek: kurum toplamı tutarları 99.999.999.999,99 TL ile sınandı (gerçek en büyük değer 11.904.930.191,00).')
    return s


# ----------------------------------------------------------------------------- pages
def frame(fid, story, x1, y1, x2, y2, prev='n', nxt='n', transform='1 0 0 1 0 0'):
    pts = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
    pp = ''.join(f'<PathPointType Anchor="{fmt(x)} {fmt(y)}" LeftDirection="{fmt(x)} {fmt(y)}" RightDirection="{fmt(x)} {fmt(y)}" />' for x, y in pts)
    return (f'<TextFrame Self="{fid}" ParentStory="{story}" PreviousTextFrame="{prev}" NextTextFrame="{nxt}" ContentType="TextType" '
            f'ItemLayer="{LAYER}" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" ItemTransform="{transform}" Visible="true" Name="$ID/">'
            f'<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>{pp}</PathPointArray></GeometryPathType></PathGeometry></Properties>'
            '<TextFramePreference TextColumnCount="1" TextColumnGutter="12" AutoSizingType="Off" /></TextFrame>')


def page_xml(pid, name, side, master, sec):
    tx = -W if side == 'L' else 0
    return (f'<Page Self="{pid}" Name="{name}" AppliedMaster="{master}" OverrideList="" MasterPageTransform="1 0 0 1 0 0" '
            f'AppliedTrapPreset="TrapPreset/$ID/kDefaultTrapStyleName" GeometricBounds="0 0 {fmt(H)} {fmt(W)}" ItemTransform="1 0 0 1 {fmt(tx)} {fmt(-H / 2)}" '
            f'AppliedAlternateLayout="{sec}" LayoutRule="Off" SnapshotBlendingMode="IgnoreLayoutSnapshots" OptionalPage="false" GridStartingPoint="TopOutside" UseMasterGrid="true">'
            '<Properties><PageColor type="enumeration">UseMasterColor</PageColor></Properties>'
            f'<MarginPreference ColumnCount="1" ColumnGutter="12" Top="{fmt(M_TOP)}" Bottom="{fmt(M_BOT)}" Left="{fmt(M_IN)}" Right="{fmt(M_OUT)}" '
            f'ColumnDirection="Horizontal" ColumnsPositions="0 {fmt(TW)}" /></Page>')


def text_box(side):
    """Spread coordinates of the text area for a page side."""
    if side == 'R':
        x1, x2 = M_IN, W - M_OUT
    else:
        x1, x2 = -W + M_OUT, -M_IN
    return x1, -H / 2 + M_TOP, x2, H / 2 - M_BOT


def build():
    os.makedirs(OUT, exist_ok=True)
    define_styles()
    graphic, swatch_ids = build_graphic()
    styles = build_styles()

    stories = {}
    main = build_main_story('uMain')
    wide = build_wide_story('uWide')
    stories['uMain'] = main.xml()
    stories['uWide'] = wide.xml()

    # master footer stories
    def footer_story(sid, left):
        st = Story(sid)
        if left:
            st.raw_para('50 Sayfa Numarası', '<Content><?ACE 18?></Content><Content>   2027 YILI PERFORMANS PROGRAMI</Content>')
        else:
            st.parts.append('<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/50 Sayfa Numarası" Justification="RightAlign">'
                            '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"><Content>BÜYÜKÇEKMECE BELEDİYESİ   </Content><Content><?ACE 18?></Content></CharacterStyleRange></ParagraphStyleRange>')
        return st.xml()
    stories['uFootL'] = footer_story('uFootL', True)
    stories['uFootR'] = footer_story('uFootR', False)

    sec = 'uSec1'
    # master spread
    fy1 = H / 2 - M_BOT + 8 * MM
    fy2 = fy1 + 12
    master = (HEAD + f'<idPkg:MasterSpread xmlns:idPkg="{PKG}" DOMVersion="{DOM}">\n'
              f'<MasterSpread Self="uMA" Name="A-Metin" NamePrefix="A" BaseName="Metin" ShowMasterItems="true" PageCount="2" '
              f'OverriddenPageItemProps="" PrimaryTextFrame="n" ItemTransform="1 0 0 1 0 0">'
              + page_xml('uMAp1', 'A', 'L', 'n', sec).replace(' AppliedAlternateLayout="uSec1"', '')
              + page_xml('uMAp2', 'A', 'R', 'n', sec).replace(' AppliedAlternateLayout="uSec1"', '')
              + frame('uMAf1', 'uFootL', -W + M_OUT, fy1, -M_IN, fy2)
              + frame('uMAf2', 'uFootR', M_IN, fy1, W - M_OUT, fy2)
              + '</MasterSpread>\n</idPkg:MasterSpread>\n')

    # pages: 1 (R), then pairs; last spread holds the landscape table on two right/left pages
    n_main = 19
    n_pages = n_main + 2
    sides = ['R'] + ['L' if i % 2 == 0 else 'R' for i in range(n_pages - 1)]
    spreads = []
    pages_by_spread = [[0]] + [[i, i + 1] for i in range(1, n_pages, 2)]
    main_frames = [f'uMf{i}' for i in range(n_main)]
    wide_frames = ['uWf0', 'uWf1']
    first_page = None
    for si, plist in enumerate(pages_by_spread):
        sid = f'uSp{si}'
        parts = []
        for pi in plist:
            pid = f'uPg{pi}'
            first_page = first_page or pid
            side = sides[pi]
            parts.append(page_xml(pid, str(pi + 1), side, 'uMA', sec))
        for pi in plist:
            side = sides[pi]
            x1, y1, x2, y2 = text_box(side)
            if pi < n_main:
                i = pi
                parts.append(frame(main_frames[i], 'uMain', x1, y1, x2, y2,
                                   prev=main_frames[i - 1] if i else 'n', nxt=main_frames[i + 1] if i + 1 < n_main else 'n'))
            else:
                j = pi - n_main
                # rotated frame: inner box 0..TH (x) by 0..TW (y), rotated 90° counter-clockwise
                tx, ty = x1, y2
                parts.append(frame(wide_frames[j], 'uWide', 0, 0, TH, TW, prev=wide_frames[j - 1] if j else 'n',
                                   nxt=wide_frames[j + 1] if j + 1 < len(wide_frames) else 'n',
                                   transform=f'0 -1 1 0 {fmt(tx)} {fmt(ty)}'))
        spreads.append((sid, HEAD + f'<idPkg:Spread xmlns:idPkg="{PKG}" DOMVersion="{DOM}">\n'
                        f'<Spread Self="{sid}" PageTransitionType="None" PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium" '
                        f'ShowMasterItems="true" PageCount="{len(plist)}" BindingLocation="{0 if len(plist) == 1 else 1}" SpreadHidden="false" AllowPageShuffle="true" '
                        f'ItemTransform="1 0 0 1 0 {fmt(si * (H + 40.0))}" FlattenerOverride="Default">'
                        + ''.join(parts) + '</Spread>\n</idPkg:Spread>\n'))

    # designmap
    d = open(os.path.join(SRC, 'designmap.xml'), encoding='utf-8').read()
    head_end = d.find('<Document ')
    pis = d[:head_end]
    body = d[head_end:]
    chunks = re.split(r'\n\t(?=<[A-Za-z])', body)
    doc_open, rest = chunks[0], chunks[1:]
    drop = ('<idPkg:Story', '<idPkg:Spread', '<idPkg:MasterSpread', '<Section', '<Hyperlink', '<Bookmark', '<ColorGroup', '<Layer',
            '<Assignment', '<CrossReferenceFormat', '<HyperlinkURLDestination', '<HyperlinkPageDestination', '<HyperlinkTextDestination', '<HyperlinkTextSource')
    tail_end = '\n</Document>'
    last = rest[-1]
    if last.endswith('</Document>\n') or last.rstrip().endswith('</Document>'):
        rest[-1] = last[:last.rfind('</Document>')].rstrip()
    kept = [c for c in rest if not c.startswith(drop)]
    story_ids = list(stories)
    doc_open = re.sub(r'StoryList="[^"]*"', f'StoryList="{" ".join(story_ids)}"', doc_open)
    doc_open = re.sub(r'Name="[^"]*\.indd"', 'Name="Civensa_Kitap_Sablonu.indd"', doc_open)
    doc_open = re.sub(r'ActiveLayer="[^"]*"', f'ActiveLayer="{LAYER}"', doc_open)
    insert_after_tags = []
    layer = (f'<Layer Self="{LAYER}" Name="Katman 1" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true" LockGuides="false" UI="true" Expendable="true" Printable="true">'
             '<Properties><LayerColor type="enumeration">LightBlue</LayerColor></Properties></Layer>')
    mine = [layer, '<idPkg:MasterSpread src="MasterSpreads/MasterSpread_uMA.xml" />']
    mine += [f'<idPkg:Spread src="Spreads/Spread_{sid}.xml" />' for sid, _ in spreads]
    mine.append(f'<Section Self="{sec}" Length="{n_pages}" Name="" ContinueNumbering="false" IncludeSectionPrefix="false" Marker="" PageStart="{first_page}" '
                f'SectionPrefix="" PageNumberStart="1" AlternateLayoutLength="{n_pages}" AlternateLayout="Custom V">'
                '<Properties><PageNumberStyle type="enumeration">Arabic</PageNumberStyle></Properties></Section>')
    after_backing = [f'<idPkg:Story src="Stories/Story_{sid}.xml" />' for sid in story_ids]
    cg = ['<ColorGroup Self="ColorGroup/[Root Color Group]" Name="[Root Color Group]" IsRootColorGroup="true">']
    cg += [f'\t\t<ColorGroupSwatch Self="CG_{i}" SwatchItemRef={a(ref)} />' for i, ref in enumerate(swatch_ids)]
    cg.append('\t</ColorGroup>')
    out = []
    for c in kept:
        if c.startswith('<DocumentUser') and mine:
            out.extend(mine); mine = []
        out.append(c)
        if c.startswith('<idPkg:BackingStory'):
            out.extend(after_backing)
    if mine:
        out.extend(mine)
    out.append('\n'.join(cg))
    designmap = pis + doc_open + ''.join('\n\t' + c for c in out) + tail_end + '\n'
    designmap = designmap.replace('ParagraphStyle/SEPERATOR', 'ParagraphStyle/$ID/NormalParagraphStyle')

    prefs = open(os.path.join(SRC, 'Resources', 'Preferences.xml'), encoding='utf-8').read()
    prefs = prefs.replace('ParagraphStyle/BOLUM BASLIK 2', 'ParagraphStyle/05 Gövde')
    prefs = re.sub(r'(<TextDefault [^>]*?)AppliedLanguage="[^"]*"', r'\1AppliedLanguage="$ID/Turkish"', prefs)

    fonts = build_fonts()

    files = {
        'designmap.xml': designmap,
        'Resources/Graphic.xml': graphic,
        'Resources/Fonts.xml': fonts,
        'Resources/Styles.xml': styles,
        'Resources/Preferences.xml': prefs,
        'MasterSpreads/MasterSpread_uMA.xml': master,
        'XML/BackingStory.xml': open(os.path.join(SRC, 'XML', 'BackingStory.xml'), encoding='utf-8').read(),
        'XML/Tags.xml': open(os.path.join(SRC, 'XML', 'Tags.xml'), encoding='utf-8').read(),
        'META-INF/container.xml': open(os.path.join(SRC, 'META-INF', 'container.xml'), encoding='utf-8').read(),
    }
    for sid, x in spreads:
        files[f'Spreads/Spread_{sid}.xml'] = x
    for sid, x in stories.items():
        files[f'Stories/Story_{sid}.xml'] = x
    missing = check_style_refs(list(files.values()), styles)
    if missing:
        raise SystemExit(f'undefined style references: {missing}')
    target = os.path.join(OUT, 'Civensa_Kitap_Sablonu.idml')
    with zipfile.ZipFile(target, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/vnd.adobe.indesign-idml-package', compress_type=zipfile.ZIP_STORED)
        for name, text in files.items():
            z.writestr(name, text.encode('utf-8'), compress_type=zipfile.ZIP_DEFLATED)
    return target, files


def build_fonts():
    from fontTools.ttLib import TTFont
    from fontmetrics import FILES, STYLE_FILE, path
    fams = []
    for fi, fam in enumerate(FILES):
        fonts = []
        for sty in STYLE_FILE:
            p = path(fam, sty)
            if not os.path.exists(p):
                continue
            n = TTFont(p)['name']
            ps = n.getDebugName(6); full = n.getDebugName(4); ver = n.getDebugName(5) or ''
            fonts.append(f'\t\t<Font Self={a(f"uFont{fi}Fontn{fam} {sty}")} FontFamily={a(fam)} Name={a(f"{fam} {sty}")} PostScriptName={a(ps)} '
                         f'Status="Installed" FontStyleName={a(sty)} FontType="OpenTypeTT" WritingScript="0" FullName={a(full)} FullNameNative={a(full)} '
                         f'FontStyleNameNative={a(sty)} PlatformName="$ID/" Version={a(ver)} TypekitID="$ID/" />')
        fams.append(f'\t<FontFamily Self="uFont{fi}" Name={a(fam)}>\n' + '\n'.join(fonts) + '\n\t</FontFamily>')
    return HEAD + f'<idPkg:Fonts xmlns:idPkg="{PKG}" DOMVersion="{DOM}">\n' + '\n'.join(fams) + '\n</idPkg:Fonts>\n'


if __name__ == '__main__':
    target, files = build()
    import xml.dom.minidom
    for name, text in files.items():
        xml.dom.minidom.parseString(text.encode('utf-8'))
    print('OK', target, os.path.getsize(target))
    print('text width pt', round(TW, 1), 'height', round(TH, 1))
    for w in warnings:
        print('WARN', w)
