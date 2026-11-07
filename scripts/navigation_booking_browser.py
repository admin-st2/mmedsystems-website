#!/usr/bin/env python3
"""Regression checks for responsive navigation and booking. Local pages only."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
import json
import os
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'navigation-review'
WIDTHS = (320, 390, 720, 721, 768, 785, 1024, 1120, 1121, 1440)
PRIMARY = ('/platform/', '/solutions/', '/integrations/', '/where-we-serve/', '/pricing/', '/contact/', '/book/')
CONTEXTUAL = ('platform', 'solutions', 'pricing', 'clinical-care', 'communication',
              'pharmacy-laboratory', 'business-operations', 'integrations',
              'care-teams', 'healthcare-operators')

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    OUT.mkdir(exist_ok=True)
    routes = [urlparse(n.text).path for n in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')]
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    rows, errors, external = [], [], []
    try:
        with sync_playwright() as pw:
            args = {'headless': True}
            if os.getenv('MMED_CHROMIUM_EXECUTABLE'):
                args['executable_path'] = os.environ['MMED_CHROMIUM_EXECUTABLE']
            browser = pw.chromium.launch(**args)
            context = browser.new_context(reduced_motion='reduce')
            def network_guard(route):
                if route.request.url.startswith(base + '/'):
                    route.continue_()
                else:
                    external.append(route.request.url)
                    route.abort()
            context.route('**/*', network_guard)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            for width in WIDTHS:
                page.set_viewport_size({'width': width, 'height': 900})
                page.goto(base + '/', wait_until='networkidle')
                assert page.locator('.scroll-indicator').count() == 0
                page.keyboard.press('End')
                # Keyboard scrolling can animate even with reduced motion.
                # Wait for the destination before measuring or taking a screenshot.
                page.wait_for_function('Math.abs(scrollY - (document.documentElement.scrollHeight - innerHeight)) < 2')
                assert page.evaluate('window.scrollY > 0')
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                assert page.locator('.site-header').bounding_box()['y'] == 0, width
                if width == 785:
                    page.screenshot(path=str(OUT / 'header-scrolled-785.png'))
                page.keyboard.press('Home')
                page.wait_for_function('window.scrollY === 0')
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                toggle = page.locator('#menu-toggle')
                panel = page.locator('#site-menu-panel')
                toggle.focus()
                page.keyboard.press('Enter')
                expect(panel).to_be_visible()
                expect(toggle).to_have_attribute('aria-expanded', 'true')
                visible = page.locator('.menu-primary-list a:visible')
                expected = PRIMARY if width <= 1120 else ('/where-we-serve/', '/book/')
                assert visible.evaluate_all('(els) => els.map(a => a.getAttribute("href"))') == list(expected), width
                expect(visible.first).to_be_focused()
                for index, href in enumerate(expected):
                    a = page.locator(f'.menu-primary-list a[href="{href}"]')
                    assert a.bounding_box()['height'] >= 44, (width, href)
                    if index:
                        page.keyboard.press("Tab")
                    expect(a).to_be_focused()
                assert page.locator('#main-nav').is_visible() == (width > 1120), width
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 3'), width
                if width in (390, 785, 1121, 1440):
                    page.screenshot(path=str(OUT / f'menu-{width}.png'), full_page=False)
                page.keyboard.press('Escape')
                expect(panel).to_be_hidden()
                expect(toggle).to_be_focused()
                # Repeated toggle, outside click, focus departure, and real navigation.
                toggle.click(); toggle.click()
                expect(panel).to_be_hidden()
                toggle.click()
                page.locator('.wordmark').first.click()
                expect(panel).to_be_hidden()
                toggle.click()
                page.locator('main a').first.focus()
                expect(panel).to_be_hidden()
                toggle.click()
                page.locator('.menu-primary-list a[href="/book/"]').click()
                page.wait_for_url(base + '/book/')
                expect(page.locator('#site-menu-panel')).to_be_hidden()
                page.go_back(wait_until='networkidle')
                expect(page.locator('#site-menu-panel')).to_be_hidden()
                rows.append({'width': width, 'menu': 'passed', 'keyboard': 'passed', 'booking_navigation': 'passed'})
            # A breakpoint switch must not strand keyboard focus on a hidden link.
            page.set_viewport_size({'width': 785, 'height': 900})
            page.locator('#menu-toggle').click()
            page.locator('.menu-primary-list a[href="/platform/"]').focus()
            page.set_viewport_size({'width': 1440, 'height': 900})
            expect(page.locator('#site-menu-panel')).to_be_hidden()
            expect(page.locator('#menu-toggle')).to_be_focused()
            page.locator('#menu-toggle').click()
            page.set_viewport_size({'width': 785, 'height': 900})
            expect(page.locator('#site-menu-panel')).to_be_hidden()
            expect(page.locator('#menu-toggle')).to_be_focused()
            # Every canonical page has the same one-copy meeting destination.
            for path in routes:
                page.goto(base + path, wait_until='domcontentloaded')
                assert page.locator('.scroll-indicator').count() == 0, path
                assert page.locator('.menu-primary-list a[href="/book/"]').count() == 1, path
                for a in page.locator('a.solution-back').all():
                    if 'Back to solutions' in a.inner_text():
                        assert a.get_attribute('href') == '/solutions/', path
                for a in page.locator('a[href="/where-we-serve/"]').all():
                    label = a.inner_text().lower()
                    assert not any(word in label for word in ('geograph', 'market', 'localization', 'where we serve')), (path, label)
            for width in (320, 785, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                for route in CONTEXTUAL:
                    page.goto(base + '/' + route + '/', wait_until='networkidle')
                    cta = page.locator('main a[href="/book/"]')
                    assert cta.count() == 1, (route, width)
                    cta.scroll_into_view_if_needed()
                    expect(cta).to_be_visible()
                    assert cta.bounding_box()['height'] >= 44, (route, width)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 3'), (route, width)
                    cta.focus(); page.keyboard.press('Enter')
                    page.wait_for_url(base + '/book/')
                    assert page.locator('main a[href^="https://calendar.google.com/"]').count() == 3
                    rows.append({'width': width, 'route': route, 'contextual_booking': 'passed'})
            for width in (390, 785, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                for route in ('request-demo', 'book', 'pricing', 'platform'):
                    page.goto(base + '/' + route + '/', wait_until='networkidle')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 3'), (route, width)
                    if route in ('request-demo', 'book'):
                        assert 'MMeD approval and NDA acceptance' in page.locator('main').inner_text()
                        for a in page.locator('a[href^="https://calendar.google.com/"]').all():
                            assert a.get_attribute('target') == '_blank'
                            assert 'noopener' in a.get_attribute('rel')
                    if route == 'request-demo':
                        assert page.locator('.mmed-booking').bounding_box()['y'] < page.locator('.demo-request').bounding_box()['y']
                        assert 'No request is submitted automatically' in page.locator('.demo-request').inner_text()
                    page.screenshot(path=str(OUT / f'{route}-{width}.png'), full_page=True)
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        (OUT / 'results.json').write_text(json.dumps({'checks': rows, 'canonical_pages': len(routes),
            'script_errors': errors, 'external_requests_blocked': external}, indent=2))
    assert not errors, errors
    assert not external, external
    print(f'PASS: {len(WIDTHS)} navigation widths, {len(routes)} page menus, {len(CONTEXTUAL)} booking routes at 3 widths; keyboard, resize, back, links and demo clarity. No external requests.')

if __name__ == '__main__':
    main()
