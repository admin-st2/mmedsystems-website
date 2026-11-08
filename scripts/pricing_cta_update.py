#!/usr/bin/env python3
"""Owner-requested Pricing placement update and regression checks.
--apply changes only header Pricing links, homepage CTA and its own CSS.
Default: read-only source checks. --browser adds local interaction tests.
--live checks deployed public pages without sending inquiries or appointments.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
from threading import Thread
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'pricing-cta-qa'
HEADER = re.compile(r'<header\b[^>]*>[\s\S]*?</header>', re.I)
ANCHOR = re.compile(r'<a\b[^>]*>[\s\S]*?</a>', re.I)
PRICE_HREF = re.compile(r'\bhref\s*=\s*[\"\']/pricing/[\"\']', re.I)
ID = 'home-pricing-title'
CSS = '''/* Homepage pricing CTA: existing MMeD palette and inherited typeface. */
.home-pricing{background:var(--navy);color:var(--white);padding:38px 0}
.home-pricing-inner{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:28px 40px}
.home-pricing-copy{max-width:800px;min-width:0}
.home-pricing-kicker{margin:0 0 12px;color:var(--white);font-size:12px;font-weight:700;letter-spacing:.12em;line-height:1.5}
.home-pricing h2{margin:0 0 12px;color:var(--white);font-size:clamp(30px,3.2vw,46px);font-weight:400;line-height:1.12;letter-spacing:-.035em}
.home-pricing-copy>p:last-child{margin:0;color:var(--line);font-size:18px;line-height:1.55;max-width:700px}
.home-pricing-cta{display:inline-flex;align-items:center;justify-content:space-between;gap:24px;min-height:52px;padding:14px 22px;border:2px solid var(--white);background:var(--white);color:var(--navy);font-size:18px;font-weight:700;line-height:1.25;text-decoration:none;white-space:nowrap}
.home-pricing-cta:hover{background:var(--pale);color:var(--navy)}
.home-pricing-cta:focus-visible{outline:3px solid var(--white);outline-offset:5px}
@media(max-width:780px){.home-pricing{padding:30px 0}.home-pricing-inner{grid-template-columns:minmax(0,1fr);gap:22px}.home-pricing-cta{justify-self:start}}
@media(max-width:480px){.home-pricing-cta{width:100%;white-space:normal}.home-pricing-copy>p:last-child{font-size:17px}}
'''
CTA = '''<section class="home-pricing" id="pricing" aria-labelledby="home-pricing-title">
<div class="container home-pricing-inner"><div class="home-pricing-copy">
<p class="home-pricing-kicker">YOUR ORGANIZATION. YOUR REQUIREMENTS.</p>
<h2 id="home-pricing-title">Pricing tailored to your organization.</h2>
<p>Explore how we scope your software, implementation, integrations, and support—then request an itemized proposal.</p>
</div><a class="home-pricing-cta" href="/pricing/">Explore Pricing <span aria-hidden="true">→</span></a></div>
</section>
'''

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a': self.links.append(dict(attrs).get('href',''))


def links(text):
    p=Links();p.feed(text);return p.links


def pages():
    urls=[n.text.strip() for n in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc') if n.text]
    assert len(urls)==47 and len(set(urls))==47,'Unexpected sitemap; review new scope first'
    result=[]
    for url in urls:
        p=urlparse(url)
        assert p.scheme=='https' and p.netloc=='mmedsystems.com' and not p.query and not p.fragment
        rel=p.path.lstrip('/')+'index.html'
        f=ROOT/rel
        assert f.is_file(),rel
        result.append((url,f))
    result.append(('https://mmedsystems.com/404.html',ROOT/'404.html'))
    return result


def apply():
    targets=pages();removed=0
    home=(ROOT/'index.html').read_text()
    assert ID not in home,'CTA already installed; refusing duplicate update'
    marker='<section aria-labelledby="adaptation-heading"'
    assert home.count(marker)==1,'Homepage insertion point changed'
    for _,file in targets:
        old=file.read_text();match=HEADER.search(old)
        assert match,file
        original=match.group()
        expected=[x for x in links(original) if x!='/pricing/']
        revised=ANCHOR.sub(lambda m: '' if PRICE_HREF.search(m.group().split('>',1)[0]) else m.group(),original)
        assert links(revised)==expected,'Non-pricing navigation would change'
        removed+=len(links(original))-len(expected)
        new=old[:match.start()]+revised+old[match.end():]
        if file==ROOT/'index.html':
            new=new.replace('</head>','<link rel="stylesheet" href="/homepage-pricing.css?v=1"/></head>',1)
            new=new.replace(marker,CTA+marker,1)
        file.write_text(new)
    (ROOT/'homepage-pricing.css').write_text(CSS)
    print(f'Applied: {removed} header links removed across {len(targets)} pages; one homepage CTA.')


def verify():
    count=0
    for url,file in pages():
        text=file.read_text();header=HEADER.search(text)
        assert header and '/pricing/' not in links(header.group()),url+' has header Pricing'
        assert '<main' in text and '/faq/' in links(text),url+' lost page scaffold'
        if not url.endswith('/404.html'):
            assert '/where-we-serve/' in links(header.group()),url+' lost sector menu'
        assert ('id="'+ID+'"' in text)==(file==ROOT/'index.html'),'CTA placement changed'
        count+=1
    home=(ROOT/'index.html').read_text()
    assert home.count('class="home-pricing-cta"')==1
    assert '/homepage-pricing.css?v=1' in home
    assert 'https://calendar.google.com/calendar/' in home
    assert (ROOT/'homepage-pricing.css').read_text()==CSS
    pricing=(ROOT/'pricing/index.html').read_text()
    assert '/contact/#pricing-inquiries' in pricing and 'itemized' in pricing.lower()
    assert not re.search(r'\$149|\$249|\$399|2 months free',pricing,re.I)
    print(f'PASS: {count} headers, preserved navigation, one homepage CTA and custom pricing.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


def browser():
    from playwright.sync_api import sync_playwright, expect
    OUT.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_address[1]}'
    rows=[];errors=[]
    try:
        with sync_playwright() as pw:
            launch={'headless':True}
            if os.getenv('MMED_CHROMIUM_PATH'):launch['executable_path']=os.environ['MMED_CHROMIUM_PATH']
            b=pw.chromium.launch(**launch)
            try:
                for label,width,height in [('desktop',1440,900),('tablet',768,1024),('phone',390,844),('small-phone',320,720)]:
                    ctx=b.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                    ctx.route('**/*',lambda r: r.continue_() if r.request.url.startswith(base+'/') else r.abort())
                    page=ctx.new_page();page.on('pageerror',lambda err:errors.append(str(err)))
                    for route in ('/','/pricing/','/where-we-serve/','/hospitals/','/book/'):
                        response=page.goto(base+route,wait_until='networkidle')
                        assert response.status==200,(route,label)
                        assert page.locator('header a[href="/pricing/"]').count()==0
                        assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=3,(route,label,'overflow')
                        page.locator('#menu-toggle').click()
                        expect(page.locator('#site-menu-panel')).to_be_visible()
                        page.keyboard.press('Escape')
                        expect(page.locator('#site-menu-panel')).to_be_hidden()
                        rows.append({'route':route,'viewport':label,'menu':'pass','overflow':'pass'})
                    page.goto(base+'/',wait_until='networkidle')
                    panel=page.locator('.home-pricing');button=panel.locator('a[href="/pricing/"]')
                    expect(panel).to_be_visible();expect(button).to_be_visible()
                    assert button.bounding_box()['height']>=44
                    assert 'Times New Roman' in button.evaluate('(e)=>getComputedStyle(e).fontFamily')
                    panel.scroll_into_view_if_needed()
                    if label in ('desktop','phone'):
                        panel.screenshot(path=str(OUT/f'pricing-cta-{label}.png'))
                    button.click();page.wait_for_url(base+'/pricing/')
                    expect(page.locator('main a[href="/contact/#pricing-inquiries"]').first).to_be_visible()
                    page.goto(base+'/',wait_until='networkidle');button=page.locator('.home-pricing-cta')
                    button.focus();page.keyboard.press('Enter');page.wait_for_url(base+'/pricing/')
                    rows.append({'viewport':label,'homepage_cta_pointer':'pass','homepage_cta_keyboard':'pass'})
                    ctx.close()
                    print('PASS',label,'navigation, CTA pointer/keyboard, touch targets and no overflow',flush=True)
            finally:b.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        (OUT/'browser-results.json').write_text(json.dumps({'checks':rows,'errors':errors},indent=2))
    assert not errors,errors


def live():
    OUT.mkdir(exist_ok=True)
    def get(url):
        req=Request(url,headers={'User-Agent':'MMeD-Pricing-Placement-Check/1.0','Cache-Control':'no-cache'})
        with urlopen(req,timeout=20) as r: return r.status,r.read().decode()
    deployed=False
    for attempt in range(16):
        try:
            status,text=get('https://mmedsystems.com/?check=pricing-homepage-cta-v1')
            h=HEADER.search(text)
            if status==200 and ID in text and h and '/pricing/' not in links(h.group()):
                deployed=True;break
        except OSError:pass
        print('Awaiting homepage CTA deployment',attempt+1,flush=True);time.sleep(12)
    assert deployed,'New homepage/header not yet confirmed live'
    def audit(pair):
        url,_=pair
        status,text=get(url)
        assert status==200,(url,status)
        h=HEADER.search(text)
        assert h and '/pricing/' not in links(h.group()),url+' header Pricing still present'
        assert '/where-we-serve/' in links(h.group()),url+' sector menu missing'
        return {'url':url,'status':status,'pricing_in_header':False}
    with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(audit,pages()[:-1]))
    status,css=get('https://mmedsystems.com/homepage-pricing.css?v=1')
    assert status==200 and css==CSS,'Live CTA stylesheet mismatch'
    status,pricing=get('https://mmedsystems.com/pricing/')
    assert status==200 and '/contact/#pricing-inquiries' in pricing
    report={'pages_verified':len(rows),'homepage_cta':'live','cta_stylesheet':'verified',
            'pricing_page':'live_custom_itemized','pages':rows}
    (OUT/'live-results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='pages'}),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true')
    ap.add_argument('--browser',action='store_true');ap.add_argument('--live',action='store_true')
    args=ap.parse_args()
    if args.apply: apply()
    verify()
    if args.browser:browser()
    if args.live:live()
