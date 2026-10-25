#!/usr/bin/env python3
"""Gerçekte çizilen token çiftlerini Chromium ile ölçer; AA başarısızsa exit 1.

Çalıştırma: python docs/design/prototype/check_contrast.py
Hem 1440 hem 390 px, kapalı/açık menüler ve her pencere, sekmeler,
gerçek hover/odak ve bileşen galerisinin pasif/yükleniyor/hata durumları ölçülür.
Devre dışı alanlar da 4,5:1 eşiğine tabidir (AA muafiyeti kullanılmaz).
--border dekoratif ayırıcıları kontrol sınırı sayılmaz. Etkileşimli sınırlar,
odak çizgileri ve onay kutusu/radyo işaretleri ayrıca 3:1 ile denetlenir.
"""
import json
from pathlib import Path
import re
import sys

from playwright.sync_api import sync_playwright
from browser_helpers import ROOT, PAGES, static_server, launch, context

# Metin ve kontrollerin arka planı opak ataların bileşkesidir.
# Bir modal açıldığında yalnız modal ölçülür; backdrop arkasındaki inert içerik ölçülmez.
COLLECT = r"""() => {
  const rows = [];
  const rgb = s => (s.match(/[\d.]+/g) || []).map(Number);
  const blend = (top, base) => {
    const a = top.length > 3 ? top[3] : 1;
    return top.slice(0,3).map((v,i) => v*a + base[i]*(1-a));
  };
  const background = el => {
    if (!el) return [255,255,255];
    const c = rgb(getComputedStyle(el).backgroundColor);
    if ((c[3] ?? 1) === 1) return c.slice(0,3);
    return blend(c, background(el.parentElement));
  };
  const visible = el => {
    const s = getComputedStyle(el);
    return el.getClientRects().length && s.visibility !== 'hidden' &&
      s.display !== 'none' && !el.closest('.sr-only');
  };
  const modal = document.querySelector('dialog[open]');
  const scope = modal || document.body;
  const add = (el, color, bg, kind, minimum) => rows.push({
    color: color.map(Math.round), bg: bg.map(Math.round), kind, minimum,
    example: el.tagName.toLowerCase() + (el.id ? '#'+el.id : '')
  });
  for (const el of [scope, ...scope.querySelectorAll('*')]) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    if (Number(s.opacity) !== 1) throw new Error('Opak olmayan öğe için bileşke ölçümü ekleyin.');
    const bg = background(el);
    const isControl = el.matches('input:not([type=checkbox]):not([type=radio]), textarea, select');
    if (isControl || [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
      const size = parseFloat(s.fontSize);
      const large = size >= 24 || (size >= 18.6667 && Number(s.fontWeight) >= 700);
      add(el, blend(rgb(s.color), bg), bg, large ? 'Büyük metin' : 'Normal metin', large ? 3 : 4.5);
    }
    if (el.matches('input, textarea, select, button, .button, summary, .step-number')) {
      const outside = background(el.parentElement);
      for (const side of ['Top','Right','Bottom','Left']) {
        const color = rgb(s['border'+side+'Color']);
        if (parseFloat(s['border'+side+'Width']) && s['border'+side+'Style'] !== 'none' &&
            (color[3] ?? 1) > 0) add(el, blend(color,outside), outside, 'Kontrol sınırı', 3);
      }
      if (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth))
        add(el, blend(rgb(s.outlineColor),outside), outside, 'Odak çizgisi', 3);
    }
    if (el.matches('input:checked')) {
      const pseudo = getComputedStyle(el,'::before');
      add(el, rgb(el.type === 'radio' ? pseudo.backgroundColor : pseudo.color).slice(0,3), bg, 'Seçim işareti', 3);
    }
  }
  return rows;
}"""


def luminance(color):
    channels = [c / 255 for c in color]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def ratio(a, b):
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def collect_states(page):
    """Her durumu tek başına aç; gezinme veya veri yazma yapma."""
    rows = page.evaluate(COLLECT)
    page.evaluate("document.querySelectorAll('details').forEach(e => e.open = true)")
    rows += page.evaluate(COLLECT)
    # CSS :target ile değişen faaliyet sekmesi.
    page.evaluate("location.hash = 'activities'")
    rows += page.evaluate(COLLECT)
    page.evaluate("location.hash = ''")
    for selector in ('button.primary', 'button.secondary', 'button.ghost', 'input:not(:disabled)',
                     'textarea:not(:disabled)', 'select:not(:disabled)', 'a:not(.skip)', '.breadcrumb a', '.report-summary a',
                     '.error-summary a', '.prototype-footer a', '.section-link.selected', 'summary'):
        candidate = page.locator(selector).filter(visible=True).first
        if candidate.count():
            candidate.hover()
            candidate.focus()
            rows += page.evaluate(COLLECT)
    for dialog_id in page.locator('dialog').evaluate_all('(els) => els.map(e=>e.id)'):
        page.evaluate('(id) => document.getElementById(id).showModal()', dialog_id)
        rows += page.evaluate(COLLECT)
        for selector in ('button', '.danger-button'):
            candidate = page.locator('#' + dialog_id).locator(selector).filter(visible=True).first
            if candidate.count():
                candidate.hover()
                candidate.focus()
                rows += page.evaluate(COLLECT)
        page.evaluate('(id) => document.getElementById(id).close()', dialog_id)
    return rows


def run():
    tokens = {tuple(bytes.fromhex(v)): '--' + k for k, v in
              re.findall(r'--([\w-]+):\s*#([\da-fA-F]{6})', (ROOT / 'tokens.css').read_text())}
    pairs = {}
    with static_server() as base, sync_playwright() as pw:
        browser = launch(pw)
        for width in (1440, 390):
            ctx = context(browser, width)
            page = ctx.new_page()
            for path in PAGES:
                page.goto(base + '/' + path)
                page.evaluate('document.fonts.ready')
                for row in collect_states(page):
                    fg, bg = tuple(row['color']), tuple(row['bg'])
                    if fg not in tokens or bg not in tokens:
                        raise AssertionError(f'Token dışı renk: {row} ({path})')
                    key = (tokens[fg], tokens[bg], row['kind'])
                    pairs[key] = {'ratio': ratio(fg, bg), 'minimum': row['minimum']}
            ctx.close()
        browser.close()
    lines = ['| Ön plan | Arka plan | Kullanım | Oran | AA eşiği | Sonuç |',
             '| --- | --- | --- | ---: | ---: | --- |']
    failures = 0
    for (fg, bg, kind), result in sorted(pairs.items()):
        passed = result['ratio'] >= result['minimum']
        failures += not passed
        lines.append(f"| `{fg}` | `{bg}` | {kind} | {result['ratio']:.2f}:1 | {result['minimum']:g}:1 | {'Geçti' if passed else 'KALDI'} |")
    lines += ['', f'{len(pairs)} kullanım çifti · {failures} başarısız.']
    print('\n'.join(lines))
    return bool(failures)


if __name__ == '__main__':
    sys.exit(run())
