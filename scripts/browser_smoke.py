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
    actions = page.locator(".booking-hero-actions .mmed-booking-button")
    if actions.count():
        assert actions.count() == 2, "Homepage needs two booking buttons"
        for link in actions.all():
            assert link.get_attribute("href").startswith("https://calendar.google.com/calendar/"), "Booking link must open Google Calendar"
        assert_page(page, "/book/")
        assert page.locator(".mmed-booking .card > a").count() == 3, "Expected three booking options"
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "Booking page overflows"
        assert "patient information" in page.locator("main").inner_text(), "Privacy guidance missing"
        assert_page(page, "/")
    else:
        assert os.environ.get("GITHUB_EVENT_NAME") == "pull_request", "Booking integration not live"
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(255, 255, 255)", "White background changed"
    # A PR's browser-smoke target is the already deployed website. The new
    # region route becomes testable only after the merge deploys to Pages.
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        assert_page(page, "/where-we-serve/")
        assert page.locator('main h1').first.is_visible(), "Regional page heading missing"
        assert page.locator('text=East Africa').count() >= 1, "Regional focus missing"
    assert_page(page, "/request-demo/")
    assert page.locator('a[href^="mailto:partnerships@mmedsystems.com"]').count() >= 1, "Demo request email route missing"
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        assert "NDA" in page.locator("main").inner_text(), "Private demo NDA conditions missing"
    assert_page(page, "/")
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        assert page.locator('section.reach-teaser a[href="/where-we-serve/"]').count() == 3, "Home regional cards missing"
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
