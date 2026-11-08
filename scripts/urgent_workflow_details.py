#!/usr/bin/env python3
"""Scoped Urgent Care workflow disclosures; no clinical actions or external sends."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen
import hashlib
import json
import os
import re
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'urgent-workflow-qa'
PAGE = ROOT / 'urgent-care/index.html'
STYLE = ROOT / 'urgent-care/workflow-details.css'
STYLE_LINK = '<link rel="stylesheet" href="/urgent-care/workflow-details.css?v=1"/>'
BASE_BLOB = 'd9b53f9049d19c14c9e3d7e98ffff79fe613d1a2'
HELP = 'Select a step to see what it covers and how we would plan it with your team.'
STEPS = [
 ('Arrival', 'Show where a visit begins and how responsibility passes from reception to the clinical team. We would define the arrival status, the information needed at that point, and who receives the next task.'),
 ('Registration', 'Connect patient identification and registration information to the encounter. We would review how your team checks an existing record, creates a new one when needed, and passes the visit to the appropriate staff.'),
 ('Clinical assessment', 'Connect the clinical assessment with the provider encounter. We would define the documentation needed, staff permissions, and how relevant information passes to the next team member according to your clinic’s policies.'),
 ('Provider encounter', 'Bring the assessment, consultation notes, and next actions together for professional review. We would map documentation responsibilities and how orders, results, and follow-up tasks connect to that visit.'),
 ('Diagnostics or treatment documentation', 'Keep diagnostic requests, results, and treatment documentation connected to the encounter. We would assess any required interfaces, review steps, and how completed services reach charge capture, without assuming an existing integration.'),
 ('Discharge', 'Bring completed documentation, remaining actions, and discharge information into a clear handoff. We would plan who reviews the visit, records its outcome, and gives the patient the agreed information.'),
 ('Follow-up instructions', 'Make the instructions and follow-up responsibilities clear after the visit. We would map who prepares the information, how referrals or next appointments are documented, and how outstanding tasks are reviewed.'),
]
CSS = '''/* Urgent Care only: preserve the existing palette, font and numbered workflow. */
.sector-journey .workflow-help{font-size:16px;line-height:1.5;color:var(--body);margin:0 0 18px}
.sector-flow.workflow-disclosures{align-items:start}
.sector-flow.workflow-disclosures>li{display:block;padding:0;min-height:0;gap:0}
.sector-flow.workflow-disclosures>li:after{top:16px;right:16px;pointer-events:none}
.workflow-step{margin:0;border:0}
.workflow-step>summary{display:flex;flex-direction:column;gap:8px;min-height:128px;padding:16px 17px;list-style:none;cursor:pointer;color:var(--navy);font:inherit}
.workflow-step>summary::-webkit-details-marker{display:none}
.workflow-step>summary::marker{content:""}
.workflow-step>summary svg{display:block;margin-right:28px}
.workflow-step-title{display:block;line-height:1.4;flex:1;padding-right:0}
.workflow-step-action{display:flex;justify-content:space-between;gap:12px;color:var(--blue-deep);font-size:15px;line-height:1.4}
.workflow-step-action .step-closed,.workflow-step-action .step-open{text-decoration:underline;text-underline-offset:3px}
.workflow-step .step-open{display:none}
.workflow-step[open] .step-closed{display:none}
.workflow-step[open] .step-open{display:inline}
.workflow-step>summary:hover{background:var(--pale)}
.workflow-step>summary:focus,.workflow-step>summary:focus-visible{outline:3px solid var(--blue-deep);outline-offset:3px;position:relative;z-index:1}
.workflow-step[open]>summary{background:var(--pale)}
.workflow-step-body{padding:16px 17px 20px;border-top:1px solid var(--line)}
.workflow-step-body p{font-size:16px;line-height:1.6;margin:0;color:var(--body);overflow-wrap:break-word}
@media(max-width:680px){
 .sector-flow.workflow-disclosures{grid-template-columns:1fr;gap:10px}
 .workflow-step>summary{min-height:84px;padding:14px 15px;display:grid;grid-template-columns:24px minmax(0,1fr);column-gap:10px;align-items:start}
 .workflow-step>summary svg{grid-column:1;grid-row:1;margin:0}
 .workflow-step-title{grid-column:2;grid-row:1;padding-right:26px;font-size:17px}
 .workflow-step-action{grid-column:2;grid-row:2;align-self:end}
 .sector-flow.workflow-disclosures>li:after{top:14px;right:14px}
 .workflow-step-body{padding:14px 15px 18px}
}
'''


def rendered_list(icon: str) -> str:
    rows=[]
    for i,(title,body) in enumerate(STEPS,1):
        rows.append(f'<li><details class="workflow-step" id="workflow-step-{i}"><summary>'
                    f'{icon}<span class="workflow-step-title">{escape(title)}</span>'
                    '<span class="workflow-step-action" aria-hidden="true"><span>'
                    '<span class="step-closed">View step</span><span class="step-open">Close step</span>'
                    '</span><span><span class="step-closed">+</span><span class="step-open">−</span>'
                    '</span></span></summary><div class="workflow-step-body">'
                    f'<p>{escape(body)}</p></div></details></li>')
    return ('<ol aria-label="Urgent Care and Walk-In Clinics workflow" class="sector-flow workflow-disclosures">'
            + '\n'.join(rows) + '</ol>')


def apply() -> None:
    data=PAGE.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==BASE_BLOB, 'Source changed; review before applying'
    source=data.decode('utf-8')
    match=re.search(r'<ol\b[^>]*class="sector-flow"[^>]*>.*?</ol>',source,re.S)
    assert match and len(re.findall(r'<li>',match.group()))==7, 'Expected seven original items'
    assert re.findall(r'<span>(.*?)</span>',match.group(),re.S)==[x[0] for x in STEPS], 'Original steps differ'
    icon=re.search(r'<svg\b.*?</svg>',match.group(),re.S).group()
    updated=source[:match.start()]+f'<p class="workflow-help">{HELP}</p>'+rendered_list(icon)+source[match.end():]
    updated=updated.replace('<section class="sector-journey">','<section class="sector-journey" id="visit-workflow">',1)
    updated=updated.replace('</head>',STYLE_LINK+'</head>',1)
    restored=updated.replace(STYLE_LINK,'',1).replace(' id="visit-workflow"','',1)
    restored=re.sub(r'<p class="workflow-help">.*?</p><ol\b[^>]*workflow-disclosures.*?</ol>',lambda _:match.group(),restored,count=1,flags=re.S)
    assert restored==source, 'Unexpected changes outside workflow'
    PAGE.write_text(updated,encoding='utf-8');STYLE.write_text(CSS,encoding='utf-8')
    print('PASS: only Urgent Care workflow markup and its new scoped stylesheet changed.')


def source_check() -> None:
    html=PAGE.read_text(encoding='utf-8')
    assert html.count('class="workflow-step"')==7
    assert html.count('class="workflow-step-body"')==7
    assert STYLE_LINK in html and HELP in html
    for title,body in STEPS:
        assert escape(title) in html and escape(body) in html
    assert 'A proposed journey for discussion.' in html
    assert 'not a claim that every workflow is available in production' in html
    assert STYLE.read_text(encoding='utf-8')==CSS
    header=re.search(r'<header\b.*?</header>',html,re.S).group()
    assert 'href="/pricing/"' not in header
    assert '/contact/#pricing-inquiries' in html
    print('PASS: seven disclosures; existing scope caveat, metadata and links preserved.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def browser_check() -> None:
    from playwright.sync_api import sync_playwright, expect
    OUT.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_address[1]}'
    rows=[];errors=[];external=[]
    try:
        with sync_playwright() as pw:
            for engine in os.getenv('MMED_TEST_BROWSERS','chromium').split(','):
                browser=getattr(pw,engine).launch(headless=True)
                widths=(1440,768,390,320) if engine=='chromium' else (1440,390)
                for width in widths:
                    print('Checking',engine,width,flush=True)
                    ctx=browser.new_context(viewport={'width':width,'height':900},reduced_motion='reduce')
                    def guard(route):
                        if route.request.url.startswith(base+'/'):route.continue_()
                        else:external.append(route.request.url);route.abort()
                    ctx.route('**/*',guard)
                    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                    assert page.goto(base+'/urgent-care/',wait_until='networkidle').status==200
                    assert page.locator('main h1').count()==1
                    assert 'Times New Roman' in page.evaluate('getComputedStyle(document.body).fontFamily')
                    details=page.locator('details.workflow-step');assert details.count()==7
                    assert page.locator('details.workflow-step[open]').count()==0
                    for i,(title,_) in enumerate(STEPS):
                        item=details.nth(i);summary=item.locator('summary')
                        assert summary.inner_text().splitlines()[0]==title
                        summary.scroll_into_view_if_needed();assert summary.bounding_box()['height']>=44
                        summary.click();expect(item).to_have_attribute('open','')
                        expect(item.locator('.workflow-step-body')).to_be_visible()
                        assert 'Close step' in summary.inner_text()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+3')
                        summary.focus();page.keyboard.press('Enter');assert item.get_attribute('open') is None
                        page.keyboard.press('Space');expect(item).to_have_attribute('open','')
                        assert summary.evaluate('(e)=>getComputedStyle(e).outlineStyle')!='none',(engine,width,title,'focus outline')
                        page.keyboard.press('Space');assert item.get_attribute('open') is None
                    page.locator('#menu-toggle').click();expect(page.locator('#site-menu-panel')).to_be_visible()
                    page.keyboard.press('Escape');expect(page.locator('#menu-toggle')).to_be_focused()
                    page.locator('.sector-actions a[href="/contact/#pricing-inquiries"]').first.click()
                    page.wait_for_url(base+'/contact/#pricing-inquiries')
                    expect(page.locator('#pricing-inquiries')).to_be_visible()
                    page.goto(base+'/urgent-care/',wait_until='networkidle')
                    if engine=='chromium' and width in (1440,390):
                        page.locator('.sector-journey').screenshot(path=str(OUT/f'workflow-{width}-closed.png'))
                        page.locator('details.workflow-step summary').first.click()
                        page.locator('.sector-journey').screenshot(path=str(OUT/f'workflow-{width}-expanded.png'))
                    rows.append({'engine':engine,'width':width,'steps':7,'pointer_and_keyboard':'passed','overflow':'none'})
                    ctx.close()
                ctx=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False)
                ctx.route('**/*',guard);page=ctx.new_page();page.goto(base+'/urgent-care/')
                for item in page.locator('details.workflow-step').all():
                    item.locator('summary').click();expect(item.locator('.workflow-step-body')).to_be_visible()
                    item.locator('summary').click()
                rows.append({'engine':engine,'javascript':False,'all_seven_steps':'passed'})
                ctx.close();browser.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        (OUT/'browser-results.json').write_text(json.dumps({'checks':rows,'errors':errors,'external_requests':external},indent=2))
    assert not errors and not external,(errors,external)
    print('PASS:',len(rows),'browser/viewport/no-JavaScript cases; seven steps per case; no external requests.')


def live_check() -> None:
    OUT.mkdir(exist_ok=True)
    def fetch(path):
        u='https://mmedsystems.com'+path
        with urlopen(Request(u,headers={'Cache-Control':'no-cache','User-Agent':'MMeD-Workflow-Verification/1.0'}),timeout=20) as r:
            assert r.status==200 and r.geturl()==u
            return r.read().decode('utf-8')
    expected=re.search(r'<section class="sector-journey".*?</section>',PAGE.read_text(),re.S).group()
    for attempt in range(16):
        html=fetch('/urgent-care/')
        if expected in html and STYLE_LINK in html: break
        if attempt==15: raise AssertionError('Published Urgent Care version has not updated')
        time.sleep(15)
    assert fetch('/urgent-care/workflow-details.css?v=1')==CSS
    assert html.count('class="workflow-step"')==7
    for title,body in STEPS:assert escape(title) in html and escape(body) in html
    assert 'A proposed journey for discussion.' in html
    report={'checkedAtUtc':datetime.now(timezone.utc).isoformat(),'url':'https://mmedsystems.com/urgent-care/','steps':7,'exact_markup':'passed','exact_stylesheet':'passed','clinical_actions':False,'status':'live_verified'}
    (OUT/'live-results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--browser',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args()
    if args.apply:apply()
    source_check()
    if args.browser:browser_check()
    if args.live:live_check()
