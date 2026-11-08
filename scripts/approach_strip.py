#!/usr/bin/env python3
"""Scoped homepage approach-link update and read-only acceptance checks."""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
from threading import Thread
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'approach-strip-qa'
CSS_LINK = '<link rel="stylesheet" href="/homepage-approach.css?v=1"/>'
OLD = '<div aria-label="Our approach" class="philosophy-strip"><div class="container philosophy-inner" data-reveal=""><span class="kicker">Our approach</span><p>Connected information.</p><p>Coordinated care.</p><p>Made to fit your scale.</p></div></div>'
LINKS = [('/integrations/', 'Connected information.', 'Connect records, systems, and workflows.', 'Integrations'),
         ('/care-teams/', 'Coordinated care.', 'Clarify handoffs, referrals, and follow-up.', 'Care Teams'),
         ('/where-we-serve/', 'Made to fit your scale.', 'Plan around your size, services, and needs.', 'Who We Serve')]
MARKUP = '''<div class="philosophy-strip approach-strip" id="our-approach">
<nav class="container philosophy-inner approach-links" aria-label="Explore our approach">
<span class="kicker">Our approach</span>
''' + '\n'.join(
    f'<a class="approach-link" href="{href}" aria-labelledby="approach-title-{i} approach-destination-{i}" aria-describedby="approach-description-{i}">'
    f'<span class="approach-title" id="approach-title-{i}">{title}</span>'
    f'<span class="approach-description" id="approach-description-{i}">{desc}</span>'
    f'<span class="approach-destination" id="approach-destination-{i}">{label} <span aria-hidden="true">→</span></span></a>'
    for i, (href, title, desc, label) in enumerate(LINKS, 1)) + '\n</nav>\n</div>'
CSS = '''/* Homepage approach: same palette and type, useful native links. */
.approach-strip .philosophy-inner{grid-template-columns:.65fr repeat(3,minmax(0,1fr));gap:24px;min-height:102px;padding-block:12px;align-items:center}
.approach-strip .kicker{margin:0;font-size:11px}
.approach-strip .approach-link{display:flex;flex-direction:column;gap:4px;min-width:0;min-height:72px;padding:7px 12px;border-left:1px solid var(--line);color:var(--navy);text-decoration:none;scroll-margin-top:130px}
.approach-title{font-size:20px;line-height:1.25}
.approach-description{font-size:15px;line-height:1.4;color:var(--body);overflow-wrap:break-word}
.approach-destination{display:inline-flex;align-items:center;gap:8px;font-size:14px;line-height:1.25;color:var(--blue-deep);text-decoration:underline;text-underline-offset:3px}
.approach-strip .approach-link:hover{background:var(--white);border-left-color:var(--blue)}
.approach-strip .approach-link:hover .approach-title{color:var(--blue-deep)}
.approach-strip .approach-link:focus-visible{background:var(--white);outline:3px solid var(--blue);outline-offset:3px}
@media(max-width:1100px){
 .approach-strip .philosophy-inner{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px 18px;padding-block:16px}
 .approach-strip .kicker{grid-column:1/-1}
 .approach-strip .approach-link{padding:5px 10px}
 .approach-title{font-size:19px}
}
@media(max-width:680px){
 .approach-strip .philosophy-inner{grid-template-columns:minmax(0,1fr);gap:0;padding-block:16px}
 .approach-strip .kicker{margin-bottom:6px}
 .approach-strip .approach-link{padding:11px 0;border-left:0;min-height:78px}
 .approach-strip .approach-link+.approach-link{border-top:1px solid var(--line)}
 .approach-title{font-size:19px}
 .approach-description{font-size:15px}
}
'''


def apply():
    path = ROOT / 'index.html'
    original = path.read_text(encoding='utf-8')
    if MARKUP in original and CSS_LINK in original:
        assert (ROOT / 'homepage-approach.css').read_text() == CSS
        return
    assert original.count(OLD) == 1, 'Homepage strip changed; refuse broad replacements'
    assert original.count('</head>') == 1 and 'homepage-approach.css' not in original
    updated = original.replace(OLD, MARKUP).replace('</head>', CSS_LINK + '</head>')
    assert updated.replace(MARKUP, OLD).replace(CSS_LINK, '') == original
    path.write_text(updated, encoding='utf-8')
    (ROOT / 'homepage-approach.css').write_text(CSS, encoding='utf-8')
    print('Applied only the approach strip and its homepage-only stylesheet.')


def source_check():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert html.count(MARKUP) == html.count(CSS_LINK) == 1
    assert OLD not in html
    for href, _, _, _ in LINKS:
        assert (ROOT / href.strip('/') / 'index.html').is_file(), href
    assert (ROOT / 'homepage-approach.css').read_text(encoding='utf-8') == CSS
    header = re.search(r'<header\b[^>]*>[\s\S]*?</header>', html).group()
    assert 'href="/pricing/"' not in header
    assert 'id="pricing"' in html and 'class="home-pricing-cta" href="/pricing/"' in html
    assert 'https://calendar.google.com/calendar/' in html
    print('PASS: three native links, explanations, stylesheet, pricing CTA and booking preserved.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def browser_check():
    from playwright.sync_api import sync_playwright, expect
    OUT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    results, errors, external = [], [], []
    try:
        with sync_playwright() as pw:
            for engine in os.getenv('MMED_TEST_BROWSERS', 'chromium').split(','):
                options = {'headless': True}
                if engine == 'chromium' and os.getenv('MMED_CHROMIUM_EXECUTABLE'):
                    options['executable_path'] = os.environ['MMED_CHROMIUM_EXECUTABLE']
                browser = getattr(pw, engine).launch(**options)
                views = (1440, 1100, 768, 390, 320) if engine == 'chromium' else (1440, 390)
                try:
                    for width in views:
                        context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
                        def guard(route):
                            if route.request.url.startswith(base + '/'):
                                route.continue_()
                            else:
                                external.append(route.request.url)
                                route.abort()
                        context.route('**/*', guard)
                        page = context.new_page()
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(base + '/', wait_until='networkidle')
                        strip = page.locator('#our-approach')
                        strip.scroll_into_view_if_needed()
                        expect(strip).to_be_visible()
                        assert page.locator('.approach-link').count() == 3
                        assert 'Times New Roman' in strip.evaluate('(e)=>getComputedStyle(e).fontFamily')
                        assert strip.evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(246, 249, 252)'
                        assert page.evaluate('document.documentElement.scrollWidth-innerWidth') <= 3
                        desktop_height = round(strip.bounding_box()['height'])
                        if width == 1440:
                            assert desktop_height <= 118, ('Strip too tall', desktop_height)
                        first = page.locator('.approach-link').first
                        first.focus()
                        for i, (href, title, desc, label) in enumerate(LINKS):
                            link = page.locator('.approach-link').nth(i)
                            expect(link).to_be_focused()
                            assert link.get_attribute('href') == href
                            assert title in link.inner_text() and desc in link.inner_text()
                            assert link.bounding_box()['height'] >= 44
                            assert link.evaluate('(e)=>getComputedStyle(e).outlineStyle') != 'none'
                            if i < 2:
                                page.keyboard.press('Tab')
                        for href, _, _, _ in LINKS:
                            for mode in ('pointer', 'keyboard'):
                                page.goto(base + '/', wait_until='networkidle')
                                link = page.locator(f'.approach-link[href="{href}"]')
                                if mode == 'pointer':
                                    link.click()
                                else:
                                    link.focus()
                                    page.keyboard.press('Enter')
                                page.wait_for_url(base + href)
                                expect(page.locator('main h1')).to_be_visible()
                        page.goto(base + '/', wait_until='networkidle')
                        page.locator('.approach-link').first.hover()
                        assert page.locator('.approach-link').first.evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(255, 255, 255)'
                        page.mouse.move(0, 0)
                        if engine == 'chromium' and width in (1440, 390):
                            page.locator('#our-approach').screenshot(path=str(OUT / f'approach-{width}.png'))
                        results.append({'engine': engine, 'width': width, 'stripHeight': desktop_height, 'links': 3, 'pointerAndKeyboard': 'passed', 'overflow': 'none'})
                        context.close()
                    context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
                    page = context.new_page()
                    page.goto(base + '/', wait_until='load')
                    expect(page.locator('.approach-link').first).to_be_visible()
                    page.locator('.approach-link').first.click()
                    page.wait_for_url(base + '/integrations/')
                    context.close()
                finally:
                    browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        (OUT / 'browser-results.json').write_text(json.dumps({'views': results, 'errors': errors, 'externalRequests': external}, indent=2))
    assert not errors and not external, (errors, external)
    print('PASS:', len(results), 'engine/viewport checks; keyboard, pointer, focus, compact layout and no-JS links.')


def live_check():
    OUT.mkdir(exist_ok=True)
    base = 'https://mmedsystems.com'
    def get(path):
        with urlopen(Request(base + path, headers={'User-Agent': 'MMeD-Approach-Release-Check/1.0', 'Cache-Control': 'no-cache'}), timeout=20) as r:
            assert r.status == 200 and r.geturl() == base + path, path
            return r.read(2_000_000).decode('utf-8')
    for attempt in range(20):
        try:
            html = get('/')
            if MARKUP in html and CSS_LINK in html:
                break
        except OSError:
            pass
        if attempt == 19:
            raise AssertionError('The updated approach strip is not yet verified live')
        time.sleep(15)
    assert get('/homepage-approach.css') == CSS
    for href, _, _, _ in LINKS:
        content = get(href)
        assert '<h1' in content and 'noindex' not in content
    header = re.search(r'<header\b[^>]*>[\s\S]*?</header>', html).group()
    assert 'href="/pricing/"' not in header
    assert 'class="home-pricing-cta" href="/pricing/"' in html
    result = {'homepage': base + '/', 'approachLinks': [base + x[0] for x in LINKS], 'stylesheet': 'exact-match', 'live': True, 'pricingPlacement': 'preserved'}
    (OUT / 'live-results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.apply:
        apply()
    source_check()
    if args.browser:
        browser_check()
    if args.live:
        live_check()
