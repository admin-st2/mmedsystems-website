#!/usr/bin/env python3
"""Validate MMeD FAQ page locally before publication; no PHI, emails, or APIs."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"faq-review"
SIZES=[("desktop",1440,900),("tablet",768,1024),("mobile",390,844),("small-mobile",320,720)]

class NoLog(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

def main():
    OUT.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(NoLog,directory=str(ROOT)))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    base=f"http://127.0.0.1:{server.server_address[1]}"
    results=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                for label,width,height in SIZES:
                    ctx=browser.new_context(
                        viewport={"width":width,"height":height},
                        device_scale_factor=1,
                        reduced_motion="reduce",
                    )
                    page=ctx.new_page()
                    errors=[]
                    page.on("pageerror",lambda err:errors.append(str(err)))
                    response=page.goto(base+"/faq/",wait_until="networkidle",timeout=30000)
                    assert response and response.status==200,(label,"FAQ missing")
                    assert page.locator("main h1").count()==1
                    assert "Frequently asked" in page.locator("main h1").inner_text()
                    assert page.locator('meta[name="description"]').count()==1
                    assert page.locator('link[rel="canonical"]').get_attribute("href")=="https://mmedsystems.com/faq/"
                    assert page.locator("details.faq-item").count()==16
                    assert page.locator("footer a[href='/faq/']").count()==1
                    assert page.locator("nav[aria-label='Main navigation'] a[href='/faq/']").count()==0
                    font=page.evaluate("getComputedStyle(document.body).fontFamily")
                    assert "Times New Roman" in font,(label,font)
                    # Native details/summary: mouse and keyboard operability.
                    first=page.locator("details.faq-item").first
                    assert first.get_attribute("open") is None
                    summary=first.locator("summary")
                    assert summary.is_visible()
                    box=summary.bounding_box()
                    assert box and box["height"]>=44,(label,"FAQ touch area too small")
                    summary.click()
                    assert first.get_attribute("open") is not None,(label,"accordion failed to open")
                    assert first.locator(".faq-answer").is_visible()
                    summary.focus()
                    page.keyboard.press("Enter")
                    assert first.get_attribute("open") is None,(label,"keyboard failed to close")
                    # In-page category navigation and no CSS horizontal overflow.
                    page.locator(".faq-index a[href='#privacy']").click()
                    assert page.url.endswith("#privacy")
                    overflow=page.evaluate("document.documentElement.scrollWidth-window.innerWidth")
                    assert overflow<=3,(label,"horizontal overflow",overflow)
                    if label in ("desktop","mobile"):
                        page.goto(base+"/faq/",wait_until="networkidle")
                        page.add_style_tag(content="""*,*::before,*::after{
                            animation:none!important;transition:none!important}
                            [data-reveal]{opacity:1!important;transform:none!important}""")
                        page.screenshot(path=str(OUT/f"faq-{label}.png"),
                                        full_page=True,animations="disabled")
                    # Check that the live homepage source now carries FAQ in the footer.
                    page.goto(base+"/",wait_until="networkidle")
                    link=page.locator("footer .footer-column a[href='/faq/']")
                    assert link.count()==1,(label,"homepage footer missing FAQ")
                    link.click()
                    page.wait_for_url(base+"/faq/",timeout=12000)
                    assert page.locator("details.faq-item").count()==16
                    assert not errors,(label,errors)
                    results.append({"viewport":label,"width":width,"faqItems":16,
                                    "accordionClick":"passed","keyboard":"passed",
                                    "footerNavigation":"passed","overflowPx":max(overflow,0)})
                    print(f"PASS FAQ {label} {width}px: categories, accordions, footer and no overflow")
                    ctx.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    (OUT/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(f"PASS {len(results)} screen sizes; no live website changed during QA.")

if __name__=="__main__":
    main()
