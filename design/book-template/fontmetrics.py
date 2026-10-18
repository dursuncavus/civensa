"""Approximate advance widths (no kerning) for Fira Sans families, tabular digits on request."""
import os
from fontTools.ttLib import TTFont

BASE = os.path.join(os.path.dirname(__file__), '..', 'gf', 'ofl')
FILES = {
    'Fira Sans': ('firasans', 'FiraSans'),
    'Fira Sans Condensed': ('firasanscondensed', 'FiraSansCondensed'),
    'Fira Sans Extra Condensed': ('firasansextracondensed', 'FiraSansExtraCondensed'),
}
STYLE_FILE = {'Regular': 'Regular', 'Italic': 'Italic', 'Light': 'Light', 'Medium': 'Medium',
              'SemiBold': 'SemiBold', 'Bold': 'Bold', 'Light Italic': 'LightItalic',
              'Medium Italic': 'MediumItalic', 'SemiBold Italic': 'SemiBoldItalic', 'Bold Italic': 'BoldItalic'}
_cache = {}


def path(family, style):
    folder, prefix = FILES[family]
    return os.path.join(BASE, folder, f'{prefix}-{STYLE_FILE[style]}.ttf')


def _load(family, style):
    key = (family, style)
    if key not in _cache:
        t = TTFont(path(family, style))
        cmap = t.getBestCmap()
        hm = t['hmtx'].metrics
        tnum = {}
        g = t['GSUB'].table
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag == 'tnum':
                for li in fr.Feature.LookupListIndex:
                    for st in g.LookupList.Lookup[li].SubTable:
                        m = getattr(st, 'mapping', None)
                        if m is None and hasattr(st, 'ExtSubTable'):
                            m = getattr(st.ExtSubTable, 'mapping', None)
                        if m:
                            tnum.update(m)
        _cache[key] = (cmap, hm, tnum, t['head'].unitsPerEm)
    return _cache[key]


def width(text, family, style, size, tabular=True):
    cmap, hm, tnum, upm = _load(family, style)
    total = 0
    for ch in text:
        g = cmap.get(ord(ch)) or cmap.get(ord('?'))
        if tabular:
            g = tnum.get(g, g)
        total += hm[g][0]
    return total * size / upm
