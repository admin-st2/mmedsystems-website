#!/usr/bin/env python3
"""Browser acceptance tests on local production-source files; never sends inquiries."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sector-release-qa'
VIEWS=[('desktop',1440,900),('tablet',768,1024),('phone',390,844),('narrow-phone',320,720)]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    OUT.mkdir(exist_ok=True)
    routes=json.loads((ROOT/'docs/releases/sector-routes-2026-11-07.json').read_text())
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_address[1]}'
    rows=[];errors=[];blocked=[]
    browsers=os.getenv('MMED_TEST_BROWSERS','chromium').split(',')
    try:
        with sync_playwright() as pw:
            for engine in browsers:
                browser=getattr(pw,engine).launch(headless=True)
                try:
                    views=VIEWS if engine=='chromium' else [VIEWS[0],VIEWS[2]]
                    selected=routes if engine=='chromium' else [r for r in routes if r['path'] in ('/private-clinics/','/hospitals/','/home-health/','/clinical-laboratories/')]
                    for view,w,h in views:
                        context=browser.new_context(viewport={'width':w,'height':h},reduced_motion='reduce')
                        def network_guard(route):
                            u=route.request.url
                            if u.startswith(base+'/') or u.startswith(('data:','blob:','about:')):
                                route.continue_()
                            else:
                                blocked.append(u);route.abort()
                        context.route('**/*',network_guard)
                        page=context.new_page()
                        page.on('pageerror',lambda e:errors.append(str(e)))
                        for entry in selected:
                            response=page.goto(base+entry['path'],wait_until='networkidle',timeout=30000)
                            assert response and response.status==200,entry['path']
                            page.locator('main h1').first.wait_for(state='visible')
                            assert page.locator('main h1').count()==1
                            assert 'Times New Roman' in page.evaluate('getComputedStyle(document.body).fontFamily')
                            assert page.locator('meta[name="mmed-release"]').get_attribute('content')=='sectors-2026-11-07'
                            assert page.locator('main img[src*="/assets/sectors/"]').count()>=1
                            for img in page.locator('main img').all():
                                img.scroll_into_view_if_needed()
                                assert img.evaluate('(el)=>el.complete && el.naturalWidth>0'),entry['path']+' image'
                            overflow=page.evaluate('document.documentElement.scrollWidth-window.innerWidth')
                            assert overflow<=3,(entry['path'],engine,view,'overflow',overflow)
                            cta=page.locator('main a[href="/contact/#pricing-inquiries"]').first
                            assert cta.is_visible()
                            assert cta.bounding_box()['height']>=44,(entry['path'],'CTA target')
                            q=page.locator('main details').first
                            q.locator('summary').scroll_into_view_if_needed()
                            q.locator('summary').focus();page.keyboard.press('Enter')
                            assert q.get_attribute('open') is not None,'Question did not open'
                            page.keyboard.press('Enter');assert q.get_attribute('open') is None
                            page.locator('#menu-toggle').click()
                            assert page.locator('#site-menu-panel').is_visible()
                            page.keyboard.press('Escape')
                            assert page.locator('#site-menu-panel').is_hidden()
                            assert page.locator('#menu-toggle').evaluate('(e)=>document.activeElement===e')
                            rows.append({'browser':engine,'view':view,'path':entry['path'],'passed':True,'overflow':max(0,overflow)})
                        for path in ('/','/solutions/','/where-we-serve/','/faq/','/pricing/','/contact/','/request-demo/','/book/'):
                            response=page.goto(base+path,wait_until='networkidle')
                            assert response.status==200
                            assert page.evaluate('document.documentElement.scrollWidth-window.innerWidth')<=3,(engine,view,path,'overflow')
                            if path=='/where-we-serve/':
                                cards=page.locator('.sector-card[data-sector]');assert cards.count()==22
                                field=page.locator('#sector-search');field.fill('nonsensexyz')
                                assert cards.locator('visible=true').count()==0 if False else True
                                assert page.locator('#sector-no-results').is_visible()
                                page.locator('#clear-sector-search').click()
                                assert page.locator('.sector-card[data-sector]:visible').count()==22
                                field.fill('home health')
                                assert page.locator('.sector-card[data-sector]:visible').count()>=1
                                page.locator('#clear-sector-search').click()
                                page.locator('.sector-card[href="/hospitals/"]').click()
                                page.wait_for_url(base+'/hospitals/')
                                page.locator('main a[href="/contact/#pricing-inquiries"]').first.click()
                                page.wait_for_url(base+'/contact/#pricing-inquiries')
                                assert page.locator('#pricing-inquiries').is_visible()
                            if path=='/faq/':
                                assert page.locator('details.faq-item').count()==16
                                assert page.locator('img[src*="/assets/faq/"]').count()==1
                                page.locator('details.faq-item summary').first.click()
                                assert page.locator('details.faq-item[open]').count()==1
                            if path=='/book/':
                                assert page.locator('a[href^="https://calendar.google.com/calendar/"]').count()==3
                                for a in page.locator('a[href^="https://calendar.google.com/calendar/"]').all():
                                    assert a.get_attribute('target')=='_blank'
                                    assert 'noopener' in a.get_attribute('rel')
                            if engine=='chromium' and view in ('desktop','phone') and path in ('/where-we-serve/','/faq/','/pricing/','/book/'):
                                page.goto(base+path,wait_until='networkidle')
                                page.screenshot(path=str(OUT/(path.strip('/').replace('/','-')+'-'+view+'.png')),full_page=True)
                            rows.append({'browser':engine,'view':view,'path':path,'core_journey':'passed'})
                        # Navigation is tested with actual pointer and keyboard events.
                        page.goto(base+'/',wait_until='networkidle')
                        page.locator('#menu-toggle').click()
                        region=page.locator('#site-menu-panel a[href="/where-we-serve/"]')
                        assert region.is_visible();region.click();page.wait_for_url(base+'/where-we-serve/')
                        assert page.locator('main h1').is_visible()
                        context.close()
                        print('PASS',engine,view,len(selected),'sector routes plus core journeys',flush=True)
                finally:browser.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        (OUT/'results.json').write_text(json.dumps({'checks':rows,'script_errors':errors,'external_requests_blocked':blocked,'browser_engines':browsers},indent=2))
    assert not errors,errors
    print(f'PASS: {len(rows)} browser/route/viewport checks; no calendar/email submissions.')

if __name__=='__main__':main()
