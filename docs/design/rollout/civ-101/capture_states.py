#!/usr/bin/env python3
"""CIV-101 synthetic presentation fixtures, Chromium AA/layout/keyboard audit; GET only."""
from datetime import datetime, UTC
import argparse
import re
import json
import os
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(OUT))
from verify_rollout import shell
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models as m, activity_sections_service as sections
from app.activity_contract_service import digest
from scripts.first_load_dryrun import disposable_database
from playwright.sync_api import sync_playwright, expect
from PIL import Image

COLLECT = shell.contrast.COLLECT.replace('const scope = modal || document.body;',
    "const scope = modal || document.querySelector('.section-editor-page');")
# Native file buttons and checked controls have painted colors outside the DOM.
COLLECT = COLLECT.replace('  return rows;', """  for (const el of scope.querySelectorAll('input[type=file]')) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el,'::file-selector-button');
    add(el, rgb(s.color).slice(0,3), rgb(s.backgroundColor).slice(0,3), 'Dosya düğmesi metni', 4.5);
    add(el, rgb(s.borderTopColor).slice(0,3), background(el), 'Kontrol sınırı', 3);
  }
  for (const el of scope.querySelectorAll('input[type=checkbox]:checked')) {
    if (!visible(el)) continue;
    // Native Chromium uses the accent-color with a white check at this luminance.
    add(el, [255,255,255], rgb(getComputedStyle(el).accentColor).slice(0,3), 'Seçim işareti', 3);
  }
  return rows;""")
COLLECT = COLLECT.replace('return el.getClientRects().length', 'return el.checkVisibility() && el.getClientRects().length')
CODES = ['I.A','I.B','I.C.1','I.C.3','I.C.4','III.A','III.A.2','III.A.3','III.A.4','III.B.1','III.B.2.i','EKLER']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', choices=['draft-content','draft-empty','returned','submitted','approved'])
    parser.add_argument('--position', choices=['director','staff','strategy'])
    parser.add_argument('--codes', nargs='+')
    parser.add_argument('--merge', action='store_true', help='Retain previous passing checks; recheck only selected cases.')
    args = parser.parse_args()
    pairs, report, screenshots = {}, [], []
    if args.merge:
        report = json.loads((OUT/'states-summary.json').read_text())['checks']
        screenshots = json.loads((OUT/'screenshots.json').read_text())
        for line in (OUT/'contrast.md').read_text().splitlines():
            match = re.match(r'\| `([^`]+)` \| `([^`]+)` \| ([^|]+) \| ([\d.]+):1 \| ([\d.]+):1',line)
            if match:
                fg,bg,kind,ratio,minimum = match.groups()
                palette = {v:k for k,v in shell.TOKENS.items()}
                pairs[(fg,bg,kind.strip())] = dict(ratio=shell.contrast.ratio(palette[fg],palette[bg]),minimum=float(minimum))
    def audit(page):
        for row in page.evaluate(COLLECT):
            fg,bg = tuple(row['color']),tuple(row['bg'])
            assert fg in shell.TOKENS and bg in shell.TOKENS, f'Token dışı renk: {row}'
            key = (shell.TOKENS[fg],shell.TOKENS[bg],row['kind'])
            pairs[key] = dict(ratio=shell.contrast.ratio(fg,bg),minimum=row['minimum'])
    with sync_playwright() as pw, pw.chromium.launch(headless=True, executable_path=os.getenv('CIVENSA_CHROMIUM_PATH','/usr/bin/chromium')) as browser:
        for state in ([args.state] if args.state else ('draft-content','draft-empty','returned','submitted','approved')):
            with disposable_database(shell.local_test_url()) as engine:
                data = shell.guide.ui_setup(engine)
                with Session(engine) as db:
                    user = db.scalar(select(m.User).where(m.User.email=='ui.department@example.invalid'))
                    doc = db.get(m.ARDocument,data['unit'])
                    from app import activity_financial_service as finance
                    finance.save_entries(db,user,doc.id,'audit',[dict(
                        audit_type='iç denetim', auditor='Sentetik denetim birimi', period='2027',
                        report_date='2027-09-30', report_number='SENTETİK-01',
                        findings='Sentetik kaynak kontrolü', measures='Kaynak açıklaması tamamlandı.',
                        status='Tamamlandı')],doc.revision)
                    payload = sections.numeric_canonical(sections.report_data(db,user,doc.id,use_freeze=False,include_typeset=True))
                    transitions = [] if state.startswith('draft') else [('submit','draft','submitted')]
                    if state == 'returned': transitions += [('return','submitted','returned')]
                    if state == 'approved': transitions += [('approve','submitted','approved')]
                    for index,(action,before,after) in enumerate(transitions,1):
                        db.add(m.ARUnitWorkflowEvent(document_id=doc.id,revision=doc.revision+index,
                            action=action,from_status=before,to_status=after,
                            reason='Hizmet kayıtlarıyla karşılaştırıp kaynak açıklamasını tamamlayın. (Sentetik iade notu)' if action=='return' else '',
                            actor_id=user.id,actor_name='Sentetik inceleyen',
                            payload_json=payload if action!='return' else None,
                            sha256=digest(payload) if action!='return' else None,
                            content_event_cursor=0,created_at=datetime(2026,10,25,9,tzinfo=UTC)))
                    # Staff without delegation must never acquire the submit action.
                    staff = db.scalar(select(m.User).where(m.User.email=='ui.staff@example.invalid'))
                    staff.can_submit = False
                    db.commit()
                with shell.guide.local_http(engine,data) as base:
                    positions = ('director','staff','strategy') if state=='draft-content' else ('director','staff')
                    for position in ([args.position] if args.position else positions):
                        account = 'strategy' if position=='strategy' else 'department'
                        email = f'ui.{"department" if position=="director" else position}@example.invalid'
                        client = data['_clients'][account]
                        assert client.post('/login',data={'email':email,'password':data['password']}).status_code == 303
                        for width in (1440,390):
                            with browser.new_context(viewport={'width':width,'height':900},device_scale_factor=1,color_scheme='light',locale='tr-TR',timezone_id='Europe/Istanbul',reduced_motion='reduce',extra_http_headers={'X-Guide-Account':account}) as context:
                                blocked,errors = [],[]
                                def guard(route):
                                    from urllib.parse import urlsplit
                                    if route.request.method=='GET' and urlsplit(route.request.url).netloc==urlsplit(base).netloc: route.continue_()
                                    else:
                                        blocked.append(route.request.method); route.abort()
                                context.route('**/*',guard)
                                page = context.new_page()
                                page.on('pageerror',lambda error:errors.append(str(error)))
                                codes = CODES if state=='draft-content' else (['I.B'] if state=='draft-empty' else ['I.A','I.C.1','III.A','EKLER'])
                                for code in (args.codes or codes):
                                    before = shell.guide.ui_state_digest(engine)
                                    doc_id = data['document'] if position=='strategy' else data['unit']
                                    response = page.goto(f'{base}/activity-sections/reports/{doc_id}?code={code}',wait_until='networkidle')
                                    assert response.status == 200
                                    page.evaluate('document.fonts.ready')
                                    layout = page.evaluate(shell.LAYOUT)
                                    assert layout['document']==width and not any(layout[k] for k in ('overflow','clipped','overlaps','shell_issues')), layout
                                    audit(page)
                                    page.keyboard.press('Tab')
                                    focus_failures = page.evaluate("""() => {
                                      const errors = [];
                                      for (const el of document.querySelectorAll('.section-editor-page :is(a,button,input,select,textarea,summary,[tabindex])')) {
                                        if (!el.checkVisibility() || el.matches(':disabled,[type=hidden]')) continue;
                                        el.focus(); const s = getComputedStyle(el);
                                        if (s.outlineColor !== 'rgb(30, 107, 101)' || s.outlineWidth !== '2px' || s.outlineStyle !== 'solid')
                                          errors.push([el.tagName,el.name,s.outlineColor,s.outlineWidth,s.outlineStyle]);
                                      }
                                      return errors;
                                    }""")
                                    assert not focus_failures, focus_failures
                                    for selector in ('.button','.button.primary','input:not([type=hidden])','textarea','select','.ar-selected','.ar-tree a','summary'):
                                        control = page.locator('.section-editor-page '+selector).filter(visible=True).first
                                        if control.count(): control.hover(); control.focus(); audit(page)
                                    for file in page.locator('.section-editor-page input[type=file]').filter(visible=True).all():
                                        file.hover(position={'x':24,'y':24}); audit(page)
                                    # Disclosures keep the original data and open with the keyboard.
                                    for details in page.locator('.section-editor-page details').all():
                                        trigger = details.locator(':scope > summary')
                                        trigger.focus()
                                        if not details.evaluate('el => el.open'): page.keyboard.press('Enter')
                                        assert details.evaluate('el => el.open')
                                        audit(page)
                                        page.keyboard.press('Escape')
                                        expect(trigger).to_be_focused()
                                        assert not details.evaluate('el => el.open')
                                    report = [r for r in report if (r['width'],r['position'],r['state'],r['code']) != (width,position,state,code)]
                                    report.append(dict(width=width,position=position,state=state,code=code,**layout))
                                    publish = position=='director' and code in {'I.A','III.A.3'} and state=='draft-content'
                                    if publish:
                                        for menu in [False]:
                                            page.locator('[data-section-export]').evaluate('(el,open) => el.open=open',menu)
                                            if code=='III.A.3':
                                                page.locator('.ar-scroll').evaluate_all('(items) => items.forEach(el => el.scrollLeft=el.scrollWidth)')
                                            audit(page)
                                            page.evaluate('document.activeElement.blur();window.scrollTo(0,0)')
                                            page.mouse.move(0,0)
                                            name = f'012-{"history" if code=="I.A" else "financial-audit"}-{width}.png'
                                            page.screenshot(path=str(OUT/name),full_page=True,animations='disabled',caret='hide')
                                            with Image.open(OUT/name) as png:
                                                png.save(OUT/name,optimize=True)
                                                screenshots = [r for r in screenshots if r['file'] != name]
                                                screenshots.append(dict(file=name,width=png.width,height=png.height,bytes=(OUT/name).stat().st_size))
                                            assert screenshots[-1]['bytes']<=1_500_000
                                    assert before==shell.guide.ui_state_digest(engine), 'Browser changed persisted state'
                                    assert not blocked and not errors
                                print(f'{state} {position} {width}: {len(args.codes or codes)} sections passed',flush=True)
    failures = [k for k,v in pairs.items() if v['ratio']<v['minimum']]
    lines = ['| Ön plan | Arka plan | Kullanım | Oran | AA eşiği | Sonuç |','| --- | --- | --- | ---: | ---: | --- |']
    for (fg,bg,kind),v in sorted(pairs.items()):
        lines.append(f'| `{fg}` | `{bg}` | {kind} | {v["ratio"]:.2f}:1 | {v["minimum"]:g}:1 | {"Geçti" if v["ratio"]>=v["minimum"] else "KALDI"} |')
    lines += ['',f'{len(pairs)} kullanım çifti · {len(failures)} başarısız.']
    (OUT/'contrast.md').write_text('\n'.join(lines)+'\n')
    (OUT/'states-summary.json').write_text(json.dumps(dict(captures=len(report),contrast_pairs=len(pairs),failures=len(failures),checks=report),ensure_ascii=False,indent=2)+'\n')
    (OUT/'screenshots.json').write_text(json.dumps(screenshots,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(report)} state/section/width/position checks; {len(pairs)} contrast pairs; {len(failures)} failures.')
    return bool(failures)

if __name__=='__main__': raise SystemExit(main())
