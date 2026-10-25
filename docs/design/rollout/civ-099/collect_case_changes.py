#!/usr/bin/env python3
"""Enumerate every rendered legacy-uppercase → source-case label/header on 012."""
import json
import os
import re
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
from capture_states import shell, CODES
from scripts.first_load_dryrun import disposable_database
from playwright.sync_api import sync_playwright

COLLECT = r'''() => {
  const sheet = document.querySelector('link[href="/static/design/section-editor.css"]').sheet;
  const nodes = [...document.querySelectorAll('.section-editor-page :is(label,th,.eyebrow)')];
  const source = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g,' ').trim();
  const render = el => getComputedStyle(el).textTransform === 'uppercase' ? source(el).toLocaleUpperCase('tr') : source(el);
  sheet.disabled = true; const before = nodes.map(render);
  sheet.disabled = false; const after = nodes.map(render);
  return nodes.map((el,i) => ({before:before[i],after:after[i]})).filter(row => row.before && row.before !== row.after);
}'''


def main():
    pairs = set()
    with disposable_database(shell.local_test_url()) as engine:
        data = shell.guide.ui_setup(engine)
        with shell.guide.local_http(engine,data) as base, sync_playwright() as pw, pw.chromium.launch(headless=True,executable_path=os.getenv('CIVENSA_CHROMIUM_PATH','/usr/bin/chromium')) as browser:
            for account in ('department','strategy'):
                with browser.new_context(viewport={'width':1440,'height':900},extra_http_headers={'X-Guide-Account':account}) as context:
                    blocked = []
                    def guard(route):
                        from urllib.parse import urlsplit
                        if route.request.method=='GET' and urlsplit(route.request.url).netloc==urlsplit(base).netloc: route.continue_()
                        else:
                            blocked.append(route.request.method); route.abort()
                    context.route('**/*',guard)
                    page = context.new_page()
                    for code in CODES:
                        document = data['unit'] if account=='department' else data['document']
                        assert page.goto(f'{base}/activity-sections/reports/{document}?code={code}',wait_until='networkidle').status==200
                        pairs.update((row['before'],row['after']) for row in page.evaluate(COLLECT))
                    assert not blocked
    # Reviewer-only return/reopen fields are conditional, unlike the draft
    # replay. Their field/action conditions are frozen by the 120-case test.
    # Extract their exact existing Turkish source wording; only CSS case changes.
    workflow = (OUT.parents[3]/'app/templates/ar_unit_workflow.html').read_text()
    for source in set(re.findall(r"'(İade gerekçesi|Yeniden açma gerekçesi)'",workflow)):
        pairs.add((source.replace('i','İ').upper(),source))
    result = [dict(before=a,after=b) for a,b in sorted(pairs)]
    (OUT/'case-changes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(result)} legacy-uppercase label/header pairs.')

if __name__=='__main__': main()
