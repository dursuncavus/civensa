#!/usr/bin/env python3
"""Replay 033/034 using the existing synthetic fixture and disposable PostgreSQL."""
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('civ096', ROOT / 'docs/design/rollout/civ-096/verify_rollout.py')
rollout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rollout)
guide = rollout.guide
from scripts.first_load_dryrun import disposable_database, local_test_url

MEASURE = r'''() => {
  const box = el => { const r = el.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}; };
  const cards = [...document.querySelectorAll('.module')];
  return {
    contentWidth:document.querySelector('.module-list').getBoundingClientRect().width,
    cards:cards.map(box),
    titles:cards.map(c => box(c.querySelector('h2'))),
    descriptions:cards.map(c => box(c.querySelector('p'))),
    help:[...document.querySelectorAll('.module .help')].map(box),
    buttons:cards.map(c => [...c.querySelectorAll('a')].map(box)),
    icons:cards.map(c => { const el = c.querySelector('svg'), s = getComputedStyle(el); return {
      ...box(el), color:s.color, surface:getComputedStyle(c).backgroundColor,
      stroke:s.strokeWidth, hidden:el.getAttribute('aria-hidden'), focusable:el.getAttribute('focusable')}; }),
    numbers:document.querySelectorAll('.module-number').length
  };
}'''


def main():
    baseline = {s['filename']:s for s in json.loads((ROOT / 'docs/screenshots/ui-map-v1/screens.json').read_text())['screens']}
    reports, screenshots = [], []
    with disposable_database(local_test_url()) as engine:
        import app.db as app_db
        import app.main as app_main
        app_db.engine.dispose()
        app_db.engine = app_main.engine = engine
        app_db.SessionLocal.configure(bind=engine)
        data = guide.ui_setup(engine)
        data.update(ui_map=True, _shots=[], _screen_meta={}, _unexpected=[])
        for number, role in [('033','strategy'), ('034','department')]:
            name = f'{number}-modules-{role}.png'
            data['_shots'].append(guide.Shot(name, '/modules', 'Modüller', role, 'top', True))
            data['_screen_meta'][name] = dict(status=200, response='')
        def verify(page, shot, meta):
            old = baseline[shot.filename]['dom']['controls']
            current = meta['dom']['controls']
            for c in current:
                c['target'] = guide.ui_control(c)[0]
            missing = Counter(map(rollout.signature, old)) - Counter(map(rollout.signature, current))
            layout = page.evaluate(rollout.LAYOUT)
            measured = page.evaluate(MEASURE)
            assert not missing and not layout['overflow'] and not layout['clipped'] and not layout['overlaps']
            assert layout['document'] == layout['viewport']
            assert measured['numbers'] == 0 and len(measured['icons']) == 3
            rgb = lambda s: tuple(map(int, rollout.re.findall(r'\d+', s)))
            for icon in measured['icons']:
                icon['contrast'] = rollout.contrast.ratio(rgb(icon['color']), rgb(icon['surface']))
                assert icon['contrast'] >= 3 and icon['stroke'] == '1.5px'
                assert icon['width'] == icon['height'] == 28 and icon['hidden'] == 'true' and icon['focusable'] == 'false'
            cards = measured['cards']
            if measured['contentWidth'] >= 960:
                for key in ('y','width','height','bottom'):
                    assert max(c[key] for c in cards)-min(c[key] for c in cards) <= 1
                for group in ('titles','descriptions','help'):
                    assert max(c['y'] for c in measured[group])-min(c['y'] for c in measured[group]) <= 1
                bottoms = [buttons[-1]['bottom'] for buttons in measured['buttons']]
                assert max(bottoms)-min(bottoms) <= 1
                assert cards[0]['x'] < cards[1]['x'] < cards[2]['x']
            else:
                assert len({c['x'] for c in cards}) == 1
                assert cards[0]['bottom'] < cards[1]['y'] < cards[2]['y']
            for button in page.locator('.module a').all():
                button.focus()
                focus = button.evaluate('el => {const s=getComputedStyle(el); return [s.outlineStyle,s.outlineWidth,s.outlineColor];}')
                assert focus == ['solid','2px',measured['icons'][0]['color']]
            page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
            reports.append(dict(filename=shot.filename, width=data['viewport_width'], elements=len(old), missing=list(missing.elements()), layout=layout, measured=measured))
        data['_verify_page'] = verify
        with guide.local_http(engine, data) as base:
            for width in (1440,390,1303,1304):
                data['viewport_width'] = width
                folder = Path('/tmp/civ098-captures') / str(width)
                folder.mkdir(parents=True, exist_ok=True)
                before = guide.ui_state_digest(engine)
                results = {}
                guide.capture(base, folder, data, results)
                assert all(v is None for v in results.values()), results
                assert before == guide.ui_state_digest(engine)
                if width in (1440,390):
                    from PIL import Image
                    for shot in data['_shots']:
                        dest = OUT / f'{Path(shot.filename).stem}-{width}.png'
                        dest.write_bytes((folder / shot.filename).read_bytes())
                        assert dest.stat().st_size <= 1_500_000
                        with Image.open(dest) as img:
                            screenshots.append(dict(file=dest.name, width=img.width, height=img.height, bytes=dest.stat().st_size))
    (OUT / 'capture-summary.json').write_text(json.dumps(dict(browser=data['browser'], captures=len(reports), failures=0, screens=reports),ensure_ascii=False,indent=2)+'\n')
    (OUT / 'screenshots.json').write_text(json.dumps(screenshots,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(reports)} captures, 0 missing/overflow/layout/contrast failures.')

if __name__ == '__main__':
    main()
