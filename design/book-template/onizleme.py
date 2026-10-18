"""Özel tasarım v2 için kontrol önizlemesi (reportlab). InDesign çıktısının birebir kopyası değildir:
heceleme, harf aralığı ve OpenType ayrıntıları yaklaşık gösterilir. Amaç yerleşimi ve oranları görmektir."""
import os, math
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont as FTFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame, Table, TableStyle, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor

HERE = os.path.dirname(os.path.abspath(__file__))
GF = os.path.join(HERE, '..', 'gf', 'ofl')
CACHE = os.path.join(HERE, 'out_v2', '_onizleme_font')
MM = 72 / 25.4
FOLDER = {'Fira Sans': ('firasans', 'FiraSans'), 'Fira Sans Condensed': ('firasanscondensed', 'FiraSansCondensed'),
          'Fira Sans Extra Condensed': ('firasansextracondensed', 'FiraSansExtraCondensed'), 'Literata': ('literata', 'Literata')}
SUFFIX = {'Regular': 'Regular', 'Italic': 'Italic', 'Light': 'Light', 'Medium': 'Medium', 'SemiBold': 'SemiBold', 'Bold': 'Bold',
          'Light Italic': 'LightItalic', 'Medium Italic': 'MediumItalic', 'SemiBold Italic': 'SemiBoldItalic', 'Bold Italic': 'BoldItalic'}
_reg = {}


def font(family, style, tabular=False):
    key = (family, style, tabular)
    if key in _reg:
        return _reg[key]
    folder, prefix = FOLDER[family]
    path = os.path.join(GF, folder, f'{prefix}-{SUFFIX[style]}.ttf')
    name = f'{prefix}-{SUFFIX[style]}' + ('-tnum' if tabular else '')
    if tabular:
        os.makedirs(CACHE, exist_ok=True)
        out = os.path.join(CACHE, name + '.ttf')
        if not os.path.exists(out):
            f = FTFont(path)
            m = {}
            if 'GSUB' in f:
                g = f['GSUB'].table
                for fr in g.FeatureList.FeatureRecord:
                    if fr.FeatureTag == 'tnum':
                        for li in fr.Feature.LookupListIndex:
                            for st in g.LookupList.Lookup[li].SubTable:
                                mp = getattr(st, 'mapping', None)
                                if mp is None and hasattr(st, 'ExtSubTable'):
                                    mp = getattr(st.ExtSubTable, 'mapping', None)
                                if mp:
                                    m.update(mp)
            for t in f['cmap'].tables:
                for cp, gname in list(t.cmap.items()):
                    if gname in m:
                        t.cmap[cp] = m[gname]
            for rec in f['name'].names:
                if rec.nameID in (3, 4, 6):
                    rec.string = name
            f.save(out)
        path = out
    pdfmetrics.registerFont(TTFont(name, path))
    _reg[key] = name
    return name


VOW = set('aeıioöuüâîûAEIİOÖUÜÂÎÛ')
WORD = __import__('re').compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+")


def hyph_word(w):
    """Türkçe hece kuralı: ünlüler arasında 0 ünsüz → ünlüden önce; 1 → ünsüzden önce; 2 → aralarından;
    3+ → son ünsüzden önce. İlk 2 ve son 2 harf bölünmez (InDesign ayarıyla aynı)."""
    if len(w) < 6:
        return w
    v = [i for i, ch in enumerate(w) if ch in VOW]
    cuts = []
    for i, j in zip(v, v[1:]):
        c = j - i - 1
        b = j if c == 0 else i + 1 if c == 1 else i + 2 if c == 2 else j - 1
        if 2 <= b <= len(w) - 2:
            cuts.append(b)
    for b in reversed(cuts):
        w = w[:b] + '\u00ad' + w[b:]
    return w


def hyphenate(txt):
    return WORD.sub(lambda m: hyph_word(m.group(0)), txt)


def tr_upper(s):
    return s.replace('i', 'İ').replace('ı', 'I').upper()


class TabLine(Flowable):
    """Sağa hizalı sekmeli tek satır (içindekiler, bölüm listesi)."""
    def __init__(self, left_markup, right_text, st, tabpos, rfont):
        super().__init__()
        self.left = Paragraph(left_markup, st)
        self.right, self.st, self.tabpos, self.rfont = right_text, st, tabpos, rfont

    def wrap(self, aw, ah):
        self.aw = aw
        w, h = self.left.wrap(min(aw, self.tabpos) - 20, ah)
        self.h = h
        return aw, h

    def draw(self):
        self.left.drawOn(self.canv, 0, 0)
        self.canv.setFont(self.rfont, self.st.fontSize)
        self.canv.setFillColor(self.st.textColor)
        base = self.h - self.st.leading + (self.st.leading - self.st.fontSize) / 2 + self.st.fontSize * 0.2
        self.canv.drawRightString(min(self.aw, self.tabpos), self.h - self.st.fontSize * 1.0 - (self.st.leading - self.st.fontSize) / 2 + 1.5, self.right)

    def getSpaceBefore(self):
        return self.st.spaceBefore

    def getSpaceAfter(self):
        return self.st.spaceAfter


def make_flowables(paras, STY, RGB, CELLSTY, pagenum=None):
    out = []
    for p in paras:
        if p[0] == 'TABLE':
            out.append(make_table(p[1], STY, RGB, CELLSTY))
            continue
        name, runs = p
        s = STY[name]
        color = tint(RGB[s['color']], s['tint'])
        base_font = font(s['family'], s['style'], s['tabular'])
        al = {'LeftAlign': TA_LEFT, 'RightAlign': TA_RIGHT, 'CenterAlign': TA_CENTER, 'LeftJustified': TA_JUSTIFY}[s['just']]
        st = ParagraphStyle(name, fontName=base_font, fontSize=s['size'], leading=s['leading'], alignment=al, textColor=HexColor(color),
                            spaceBefore=s['before'], spaceAfter=s['after'], leftIndent=s['left'], firstLineIndent=s['first'] if not s['bullet'] else 0,
                            bulletFontName=base_font, bulletFontSize=s['size'], bulletIndent=0, embeddedHyphenation=1 if s['hyph'] else 0)
        parts_l, parts_r, side = [], [], 'l'
        for r in runs:
            if r == ('PAGENUM', ''):
                r = str(pagenum)
            cs, txt = r if isinstance(r, tuple) else (None, r)
            if txt == '\t':
                side = 'r'
                continue
            if s['caps']:
                txt = tr_upper(txt)
            if s['hyph']:
                txt = hyphenate(txt)
            m = escape(txt).replace(' ', '<br/>')
            if cs == 'Kalın':
                sty = 'Bold' if s['style'] in ('SemiBold', 'Bold', 'Medium') else 'SemiBold'
                m = f'<font name="{font(s["family"], sty, s["tabular"])}">{m}</font>'
            elif cs == 'İtalik':
                m = f'<font name="{font(s["family"], "Italic")}">{m}</font>'
            elif cs == 'Vurgu Renk':
                m = f'<font color="{RGB["Kurumsal Vurgu"]}">{m}</font>'
            elif cs == 'Ana Renk':
                m = f'<font color="{RGB["Kurumsal Ana"]}">{m}</font>'
            (parts_l if side == 'l' else parts_r).append(m)
        if parts_r and s['tabs']:
            out.append(TabLine(''.join(parts_l), ''.join(parts_r), st, s['tabs'][0][1], base_font))
        else:
            kw = dict(bulletText='•') if s['bullet'] else {}
            out.append(Paragraph(''.join(parts_l + parts_r), st, **kw))
    return out


def tint(hexc, t):
    if t is None or t >= 100:
        return hexc
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    k = t / 100
    return '#%02x%02x%02x' % tuple(round(255 - (255 - v) * k) for v in (r, g, b))


def make_table(t, STY, RGB, CELLSTY):
    ncol = len(t.widths)
    data = [['' for _ in range(ncol)] for _ in t.rows]
    cmds, covered = [], set()
    for r, cells in enumerate(t.rows):
        col = 0
        for cdef in cells:
            while (col, r) in covered:
                col += 1
            content, cstyle, pstyle = cdef[0], cdef[1], cdef[2]
            span = cdef[3] if len(cdef) > 3 else 1
            rowspan = 1
            if isinstance(span, tuple):
                span, rowspan = span
            for dc in range(span):
                for dr in range(rowspan):
                    if dc or dr:
                        covered.add((col + dc, r + dr))
            runs = content if isinstance(content, list) else [content]
            data[r][col] = make_flowables([(pstyle, runs)], STY, RGB, CELLSTY)[0]
            c2, r2 = col + span - 1, r + rowspan - 1
            if span > 1 or rowspan > 1:
                cmds.append(('SPAN', (col, r), (c2, r2)))
            fill, ft, top, bot = CELLSTY[cstyle]
            if fill:
                cmds.append(('BACKGROUND', (col, r), (c2, r2), HexColor(tint(RGB[fill], ft))))
            if top:
                cmds.append(('LINEABOVE', (col, r), (c2, r), top[0], HexColor(RGB[top[1]])))
            if bot:
                cmds.append(('LINEBELOW', (col, r2), (c2, r2), bot[0], HexColor(RGB[bot[1]])))
            col += span
    cmds += [('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
             ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]
    if t.header_rows:
        cmds.append(('VALIGN', (0, 0), (-1, t.header_rows - 1), 'BOTTOM'))
    tb = Table(data, colWidths=t.widths, repeatRows=t.header_rows)
    tb.setStyle(TableStyle(cmds))
    tb.hAlign = 'LEFT'
    return tb


def flow(frame, fl, canv):
    """Frame.addFromList bölmez; tablo ve paragrafları kalan alana göre böl."""
    while fl:
        f = fl[0]
        if frame.add(f, canv):
            fl.pop(0)
            continue
        parts = frame.split(f, canv)
        if len(parts) >= 2:
            fl.pop(0)
            fl[0:0] = parts
            if frame.add(fl[0], canv):
                fl.pop(0)
                continue
        break


def path_of(c, pts, close=True):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def render(pages, STORIES, STY, RGB, CELLSTY, out_pdf, master_pages=None):
    from ozel_v2 import arc_points, PW, PH
    W, H = PW * MM, PH * MM
    spreads = [[0]] + [[i, i + 1] if i + 1 < len(pages) else [i] for i in range(1, len(pages), 2)]
    c = canvas.Canvas(out_pdf)
    c.setTitle('Civensa Özel Tasarım v2 — önizleme')
    remaining = {}
    warnings = []
    for sp in spreads:
        c.setPageSize((W * len(sp), H))
        for k, pi in enumerate(sp):
            pg = pages[pi]
            ox = 0 if len(sp) == 1 else k * W
            c.saveState()
            c.rect(ox, 0, W, H, stroke=0, fill=0)
            clip = c.beginPath(); clip.rect(ox, 0, W, H); c.clipPath(clip, stroke=0, fill=0)
            c.setFillColor(HexColor('#ffffff')); c.rect(ox, 0, W, H, stroke=0, fill=1)
            X = lambda x: ox + x * MM
            Y = lambda y: H - y * MM
            mitems = []
            if master_pages and pg.master in master_pages:
                mitems = master_pages[pg.master][0 if pg.side == 'L' else 1].items
            for it in [dict(m, _master=True) for m in mitems] + pg.items:
                t_ = it['t']
                if t_ == 'rect':
                    pts = [(X(x), Y(y)) for x, y in it['pts']]
                    p = path_of(c, pts)
                    fill = it['fill']
                    if fill:
                        c.setFillColor(HexColor(tint(RGB[fill], it['tint'])))
                    if it['stroke']:
                        c.setStrokeColor(HexColor(tint(RGB[it['stroke']], it['stint']))); c.setLineWidth(it['sw'])
                    c.drawPath(p, fill=1 if fill else 0, stroke=1 if it['stroke'] else 0)
                    if it['photo']:
                        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
                        c.saveState(); c.clipPath(path_of(c, pts), stroke=0, fill=0)
                        c.setStrokeColor(HexColor('#ffffff')); c.setLineWidth(0.4)
                        c.line(min(xs), min(ys), max(xs), max(ys)); c.line(min(xs), max(ys), max(xs), min(ys))
                        c.restoreState()
                        c.setFillColor(HexColor('#4a4d48')); c.setFont(font('Fira Sans', 'Medium'), 7)
                        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                        cx = max(ox + 30, min(ox + W - 30, cx)); cy = max(20, min(H - 20, cy))
                        c.drawCentredString(cx, cy - 2, (it['label'] or 'Görsel').upper())
                    elif it['label'] and fill:
                        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
                        c.setFillColor(HexColor(RGB['Kurumsal Ana'])); c.setFont(font('Fira Sans', 'SemiBold'), 5.5)
                        c.drawCentredString((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2 - 2, it['label'].upper())
                elif t_ == 'line':
                    pts = [(X(x), Y(y)) for x, y in it['pts']]
                    c.setStrokeColor(HexColor(tint(RGB[it['stroke']], it['tint']))); c.setLineWidth(it['sw'])
                    c.setLineCap(1 if it['cap'] == 'RoundEndCap' else 0)
                    c.setDash([3 * it['sw'], 2 * it['sw']] if it.get('dash') else [])
                    c.drawPath(path_of(c, pts, close=False), stroke=1, fill=0)
                    c.setDash([])
                elif t_ == 'oval':
                    if it['fill']:
                        c.setFillColor(HexColor(tint(RGB[it['fill']], it['tint'])))
                    if it['stroke']:
                        c.setStrokeColor(HexColor(tint(RGB[it['stroke']], it['stint']))); c.setLineWidth(it['sw'])
                    c.circle(X(it['cx']), Y(it['cy']), it['r'] * MM, stroke=1 if it['stroke'] else 0, fill=1 if it['fill'] else 0)
                elif t_ == 'arc':
                    pts = arc_points(it['cx'], it['cy'], it['r'], it['a0'], it['a1'])
                    p = c.beginPath()
                    (ax, ay), _, _ = pts[0]
                    p.moveTo(X(ax), Y(ay))
                    for i in range(1, len(pts)):
                        r0 = pts[i - 1][2]; l1 = pts[i][1]; a1 = pts[i][0]
                        p.curveTo(X(r0[0]), Y(r0[1]), X(l1[0]), Y(l1[1]), X(a1[0]), Y(a1[1]))
                    c.setStrokeColor(HexColor(tint(RGB[it['stroke']], it['tint']))); c.setLineWidth(it['sw']); c.setLineCap(0)
                    c.drawPath(p, stroke=1, fill=0)
                elif t_ == 'text':
                    sid = it['story']
                    has_num = any(r == ('PAGENUM', '') for p_ in STORIES[sid] if p_[0] != 'TABLE' for r in p_[1])
                    if has_num or it.get('_master'):
                        fl = make_flowables(STORIES[sid], STY, RGB, CELLSTY, pagenum=pi + 1)
                    else:
                        if sid not in remaining:
                            remaining[sid] = make_flowables(STORIES[sid], STY, RGB, CELLSTY)
                        fl = remaining[sid]
                    x0, top, w, h = X(it['x']), Y(it['y']), it['w'] * MM, it['h'] * MM
                    n = it['cols']; g = it['gutter'] * MM
                    cw = (w - g * (n - 1)) / n
                    if it['valign'] != 'TopAlign' and n == 1:
                        tot = sum(f.wrap(cw, h)[1] + (f.getSpaceAfter() if hasattr(f, 'getSpaceAfter') else 0) for f in fl)
                        shift = (h - tot) if it['valign'] == 'BottomAlign' else (h - tot) / 2
                        top -= max(0, shift)
                    if it.get('rot'):
                        # alan sol-alt köşesine taşı, 90° döndür: iç genişlik = alan yüksekliği
                        c.saveState()
                        c.translate(X(it['x']), Y(it['y'] + it['h']))
                        c.rotate(90)
                        iw, ih = it['h'] * MM, it['w'] * MM
                        fr = Frame(0, -ih, iw, ih, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
                        flow(fr, fl, c)
                        c.restoreState()
                        continue
                    for k2 in range(n):
                        fr = Frame(x0 + k2 * (cw + g), top - h, cw, h, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
                        flow(fr, fl, c)
            c.restoreState()
        c.showPage()
    # taşan metin kontrolü (son çerçeveden sonra kalan)
    for sid, fl in remaining.items():
        if fl:
            warnings.append(f'taşan metin: {sid} ({len(fl)} öğe kaldı)')
    c.save()
    for w_ in warnings:
        print('UYARI', w_)
    return out_pdf
