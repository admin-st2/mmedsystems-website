#!/usr/bin/env python3
"""Desktop/mobile smoke tests for the PUBLIC MMeD corporate website.

No private demo hosts, credentials or user data are accessed.
Run after installing playwright and Chromium:
  python -m playwright install chromium
  python scripts/browser_smoke.py
"""
from __future__ import annotations
import os
from playwright.sync_api import sync_playwright
BASE = "https://mmedsystems.com"
PUBLIC_PATHS = ["/", "/platform/", "/solutions/", "/contact/", "/private-clinics/", "/request-demo/"]


def assert_page(page, path: str) -> None:
    response = page.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
    assert response and response.status == 200, f"{path}: non-200 response"
    page.locator("h1").first.wait_for(state="visible")
    assert page.locator('link[rel="canonical"]').get_attribute("href") == BASE + path, f"{path}: wrong canonical"
    assert page.locator('meta[name="viewport"]').count() == 1, f"{path}: missing mobile viewport"
    assert "Times New Roman" in page.evaluate("getComputedStyle(document.body).fontFamily"), f"{path}: typography changed"


def test_view(browser, width: int, height: int) -> None:
    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
    for path in PUBLIC_PATHS:
        assert_page(page, path)
    assert_page(page, "/")
    assert page.locator("a.primary-cta").count() == 1, "Homepage must have exactly one primary demo CTA"
    demo_route = page.locator("a.primary-cta").get_attribute("href")
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        # PR checks run against the already-deployed site, which may still be on
        # the previous release. The static checker enforces the NEW source route.
        assert demo_route == "/request-demo/" or demo_route.startswith("mailto:"), "Unexpected demo route"
    else:
        assert demo_route == "/request-demo/", "Live homepage has not deployed the inquiry path"
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(255, 255, 255)", "White background changed"
    assert_page(page, "/request-demo/")
    assert page.locator('a[href^="mailto:partnerships@mmedsystems.com"]').count() >= 1, "Demo request email route missing"
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        assert "NDA" in page.locator("main").inner_text(), "Private demo NDA conditions missing"
    assert_page(page, "/")
    if width <= 680:
        toggle = page.locator("#menu-toggle")
        assert toggle.is_visible(), "Mobile menu toggle hidden"
        toggle.click()
        assert toggle.get_attribute("aria-expanded") == "true", "Mobile menu did not open"
        panel = page.locator("#site-menu-panel")
        assert panel.is_visible(), "Mobile menu panel hidden"
        panel.locator('a[href="/platform/"]').first.click()
        page.wait_for_url(BASE + "/platform/", timeout=30000)
        assert_page(page, "/")
    else:
        assert page.locator("#main-nav").is_visible(), "Desktop navigation is hidden"

    missing = page.goto(BASE + "/missing/nested/qa-route-2026/", wait_until="domcontentloaded")
    assert missing and missing.status == 404, "Missing nested page must return HTTP 404"
    assert page.locator('meta[name="robots"]').get_attribute("content").startswith("noindex"), "404 missing noindex"
    assert page.locator('link[rel="stylesheet"]').get_attribute("href").startswith("/"), "404 uses relative stylesheet"
    print(f"PASS: {width}x{height} routes, menu, brand, CTA and nested 404.")
    page.close()


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            test_view(browser, 1440, 900)
            test_view(browser, 390, 844)
            test_view(browser, 320, 720)
        finally:
            browser.close()
    print("All public corporate desktop/mobile browser smoke tests passed. Demo untouched.")


if __name__ == "__main__":
    main()
