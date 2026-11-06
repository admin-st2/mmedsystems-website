#!/usr/bin/env python3
"""Interactive buttons and navigation QA against proposed local MMeD site source.

No live deployment, customer data, account credentials, clinical-demo calls,
or external messages. Screenshots and report are attached to GitHub PR review.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"ux-review"
ROUTES=[
    ("home","/"),
    ("solutions","/solutions/"),
    ("clinic","/private-clinics/"),
    ("where-we-serve","/where-we-serve/"),
    ("contact","/contact/"),
]
SIZES=[
    ("desktop",1440,900),
    ("tablet",768,1024),
    ("mobile",390,844),
    ("small-phone",320,720),
]

class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

def main()->None:
    OUTPUT.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),
                                partial(SilentHandler,directory=str(ROOT)))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    base=f"http://127.0.0.1:{server.server_address[1]}"
    metrics=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                for device,width,height in SIZES:
                    context=browser.new_context(
                        viewport={"width":width,"height":height},
                        device_scale_factor=1,reduced_motion="reduce")
                    page=context.new_page()
                    console_errors=[]
                    page.on("pageerror",lambda error:console_errors.append(str(error)))
                    for slug,path in ROUTES:
                        response=page.goto(base+path,wait_until="networkidle",
                                           timeout=30000)
                        assert response and response.status==200,(path,device)
                        page.locator("h1").first.wait_for(state="visible")
                        page.add_style_tag(content="""*,*::before,*::after{
                            animation:none!important;transition:none!important}
                            [data-reveal]{opacity:1!important;transform:none!important}""")
                        page_width=page.evaluate("document.documentElement.scrollWidth")
                        assert page_width<=width+3,(
                            f"{slug}/{device} overflow: {page_width-width}px")
                        font=page.evaluate("getComputedStyle(document.body).fontFamily")
                        assert "Times New Roman" in font, "Brand font changed"
                        menu=page.locator("#menu-toggle")
                        panel=page.locator("#site-menu-panel")
                        assert menu.is_visible(), f"Menu hidden: {slug}/{device}"
                        assert menu.get_attribute("aria-expanded")=="false"
                        assert panel.is_hidden()
                        assert menu.get_attribute("aria-controls")=="site-menu-panel"
                        # All navigation links must have an accessible destination.
                        assert page.locator("#site-menu-panel a[href='/where-we-serve/']").count()==1
                        assert page.locator("#main-nav a[href='/where-we-serve/']").count()==0
                        menu.click()
                        assert menu.get_attribute("aria-expanded")=="true"
                        assert menu.locator("span").first.inner_text()=="Close"
                        assert panel.is_visible()
                        assert page.locator("body").evaluate("(node)=>node.classList.contains('menu-open')")
                        if slug=="where-we-serve":
                            link=panel.locator("a[href='/where-we-serve/']")
                            assert link.get_attribute("aria-current")=="page"
                            assert link.is_visible(), f"Where We Serve hidden: {device}"
                        if slug=="solutions":
                            link=panel.locator("a[href='/solutions/']").first
                            assert link.get_attribute("aria-current")=="page"
                        # Escape should close panel and restore focus to disclosure.
                        page.keyboard.press("Escape")
                        assert panel.is_hidden() and menu.get_attribute("aria-expanded")=="false"
                        assert menu.evaluate("(node)=>document.activeElement===node")
                        # Outside click closes without accidentally navigating.
                        menu.click()
                        page.locator("main h1").first.click(force=True)
                        assert panel.is_hidden()
                        # Interactive links must have touch-size targets where expected.
                        buttons=page.locator(".primary-cta,.solution-inline-cta,.solution-connect a")
                        for i in range(min(buttons.count(),6)):
                            el=buttons.nth(i)
                            if not el.is_visible():
                                continue
                            bounds=el.bounding_box()
                            assert bounds and bounds["height"]>=44,(
                                f"{slug}/{device} small CTA: {bounds}")
                        if slug=="home":
                            cta=page.locator("a.primary-cta[href='/request-demo/']")
                            assert cta.count()==1,"Homepage demo conversion route missing"
                            assert cta.is_visible()
                            assert page.locator("section.reach-teaser").count()==0
                        if device in ("desktop","mobile") and slug in ("home","where-we-serve","solutions"):
                            page.evaluate("window.scrollTo(0,0)")
                            target=OUTPUT/f"{slug}-{device}.png"
                            page.screenshot(path=str(target),full_page=True,animations="disabled")
                        metrics.append({"page":slug,"viewport":device,"width":width,
                            "horizontalOverflow":max(0,page_width-width),
                            "menuToggle":"pass","menuEscape":"pass","menuFocus":"pass",
                            "whereWeServe":"discoverable","buttons":"pass"})
                    # Verify menu navigation with an actual click from the homepage.
                    page.goto(base+"/",wait_until="networkidle")
                    page.locator("#menu-toggle").click()
                    region=page.locator("#site-menu-panel a[href='/where-we-serve/']")
                    assert region.is_visible(),f"Region menu link hidden at {device}"
                    region.click()
                    page.wait_for_url(base+"/where-we-serve/",timeout=12000)
                    assert page.locator("main h1").first.is_visible()
                    assert not console_errors,console_errors
                    print(f"PASS: {device} ({width}px), navigation, focus, CTAs, overflow")
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    (OUTPUT/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    (OUTPUT/"README.txt").write_text(
        "MMeD interactive UX review — not deployed.\n"
        "Menu open/close, escape focus, current-page navigation, Where We Serve,\n"
        "CTA click target sizes and no horizontal overflow tested at 4 widths.\n"
        "Rendered screenshots are captured from proposed source, not live pages.\n"
        "Owner must approve any publication.\n",encoding="utf-8")
    assert len(metrics)==len(SIZES)*len(ROUTES)
    print(f"PASS: {len(metrics)} page/viewport combinations.")


if __name__=="__main__":
    main()
