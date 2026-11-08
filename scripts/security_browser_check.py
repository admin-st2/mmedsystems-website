#!/usr/bin/env python3
"""Exercise candidate response headers on localhost. Never changes deployment."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
from security_policy import candidate_headers

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'security-review'
HEADERS = candidate_headers()


class CandidateServer(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        for name, value in HEADERS.items():
            self.send_header(name, value)
        super().end_headers()


class FrameServer(SimpleHTTPRequestHandler):
    target = ''

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        if self.path == '/unprotected/':
            body = '<!doctype html><h1>Unprotected frame control</h1>'
        elif self.path == '/control-parent/':
            body = '<!doctype html><iframe src="/unprotected/"></iframe>'
        else:
            body = f'<!doctype html><iframe src="{self.target}/privacy/"></iframe>'
        self.wfile.write(body.encode())


def main():
    OUT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(CandidateServer, directory=str(ROOT)))
    base = f'http://127.0.0.1:{server.server_address[1]}'
    FrameServer.target = base
    frame_server = ThreadingHTTPServer(('127.0.0.1', 0), FrameServer)
    frame_base = f'http://127.0.0.1:{frame_server.server_address[1]}'
    for service in (server, frame_server):
        Thread(target=service.serve_forever, daemon=True).start()
    pages = [urlparse(n.text).path for n in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')]
    pages += ['/404.html', '/prototype/']
    aliases = sorted(p for p in ROOT.glob('*.html') if 'http-equiv="refresh"' in p.read_text())
    violations, errors, blocked, results, console = [], [], [], [], []
    try:
        with sync_playwright() as pw:
            launch = {'headless': True}
            if os.getenv('MMED_CHROMIUM_EXECUTABLE'):
                launch['executable_path'] = os.environ['MMED_CHROMIUM_EXECUTABLE']
            browser = pw.chromium.launch(**launch)
            context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
            def guard(route):
                if route.request.url.startswith((base + '/', frame_base + '/')):
                    route.continue_()
                else:
                    blocked.append(route.request.url)
                    route.abort()
            context.route('**/*', guard)
            phase = ['normal']
            # Keep violations across redirect/navigation document lifetimes.
            context.expose_function('__recordViolation',
                lambda violation: violations.append(violation) if phase[0] == 'normal' else None)
            context.add_init_script("""window.__cspViolations = [];
                document.addEventListener('securitypolicyviolation', e => {
                    const violation = {url:location.href, directive:e.effectiveDirective, blocked:e.blockedURI};
                    window.__cspViolations.push(violation);
                    window.__recordViolation(violation);
                });""")
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: console.append(message.text))
            for path in pages:
                response = page.goto(base + path, wait_until='networkidle')
                assert response and response.status == 200, path
                assert response.headers.get('content-security-policy') == HEADERS['Content-Security-Policy']
                expect(page.locator('main h1').first).to_be_visible()
                for img in page.locator('main img').all():
                    img.scroll_into_view_if_needed()
                    page.wait_for_function('(img) => img.complete && img.naturalWidth > 0', arg=img.element_handle())
                if page.locator('#menu-toggle').count():
                    page.locator('#menu-toggle').click()
                    expect(page.locator('#site-menu-panel')).to_be_visible()
                    page.keyboard.press('Escape')
                    expect(page.locator('#site-menu-panel')).to_be_hidden()
                results.append({'path': path, 'pass': True})
            for alias in aliases:
                target = re.search(r'url=([^";]+)', alias.read_text()).group(1)
                page.goto(base + '/' + alias.name + '?security-check=1#check', wait_until='networkidle')
                # The legacy script must run, not just the query-dropping meta refresh.
                page.wait_for_url(base + target + '?security-check=1#check')
                assert not page.evaluate('window.__cspViolations'), alias.name
                results.append({'path': '/' + alias.name, 'redirect': target, 'pass': True})
            for width in (320, 785, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                page.goto(base + '/privacy/', wait_until='networkidle')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 3'), width
                page.screenshot(path=str(OUT / f'privacy-{width}.png'), full_page=True)
            # Outbound appointment links remain ordinary navigation; never open or submit them.
            page.goto(base + '/book/', wait_until='networkidle')
            assert page.locator('a[href^="https://calendar.google.com/calendar/"]').count() >= 3
            assert not violations, violations
            phase[0] = 'negative-controls'
            # Negative control: an unapproved inline script must not execute.
            page.evaluate("""() => {let s=document.createElement('script');
                s.textContent='window.__unapprovedRan = true'; document.head.append(s);} """)
            page.wait_for_function('window.__cspViolations.length > 0')
            assert not page.evaluate('window.__unapprovedRan === true')
            assert any(v['directive'] == 'script-src-elem' for v in page.evaluate('window.__cspViolations'))
            # The CSP is response-header enforced on localhost, including framing denial.
            # Positive control proves the fixture/browser can render a frame.
            page.goto(frame_base + '/control-parent/', wait_until='networkidle')
            expect(page.frame_locator('iframe').locator('h1')).to_have_text('Unprotected frame control')
            console.clear()
            framed_responses = []
            page.on('response', lambda response: framed_responses.append(response)
                    if response.url == base + '/privacy/' else None)
            page.goto(frame_base + '/', wait_until='networkidle')
            assert framed_responses and framed_responses[-1].status == 200
            assert framed_responses[-1].headers.get('x-frame-options') == 'DENY'
            assert any('frame-ancestors' in msg or 'X-Frame-Options' in msg for msg in console), console
            assert not any(f.locator('h1').count() for f in page.frames[1:]), 'Framed page rendered'
            assert not violations, violations
            assert not errors, errors
            assert not blocked, blocked
            context.close()
            browser.close()
        report = {'scope': 'localhost candidate HTTP headers only; production unchanged',
                  'pages': results, 'privacy_widths': [320, 785, 1440],
                  'normal_page_csp_violations': violations, 'page_errors': errors,
                  'external_requests': blocked, 'inline_script_blocked': True,
                  'framing_blocked': True, 'headers': HEADERS}
        (OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'PASS: candidate headers on {len(results)} routes/redirects; privacy at 3 widths; inline-script and framing negative controls.')
        print('Local test only. GitHub Pages production response headers were not changed.')
    finally:
        server.shutdown()
        frame_server.shutdown()
        server.server_close()
        frame_server.server_close()


if __name__ == '__main__':
    main()
