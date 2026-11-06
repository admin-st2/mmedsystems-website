#!/usr/bin/env python3
"""MMeD navigation/button usability review — source-only, not live.

Run using Python Playwright after installing Chromium. Tests real mouse,
keyboard, mobile/touch behavior and renders review screenshots from a local
server. No private demo, account, email, PHI or external website is accessed.
"""
from __future__ import annotations

from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "navigation-ux-review"
VIEWS = [("desktop",1440,900),("tablet",768,1024),
         ("mobile",390,844),("small-phone",320,720)]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1",0), partial(QuietHandler,directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host=f"http://127.0.0.1:{server.server_address[1]}"
    results=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                for name,width,height in VIEWS:
                    ctx=browser.new_context(
                        viewport={"width":width,"height":height},
                        device_scale_factor=1,
                        has_touch=width<=768,
                        is_mobile=False,
                        reduced_motion="reduce",
                    )
                    page=ctx.new_page()
                    errors=[]
                    page.on("pageerror",lambda err: errors.append(str(err)))
                    response=page.goto(host+"/",wait_until="networkidle",timeout=30000)
                    assert response and response.status==200
                    page.locator("h1").first.wait_for(state="visible")
                    page.add_style_tag(content="""
                        *, *::before, *::after {animation:none!important;transition:none!important}
                        [data-reveal]{opacity:1!important;transform:none!important}
                    """)
                    toggle=page.locator("#menu-toggle")
                    panel=page.locator("#site-menu-panel")
                    assert toggle.is_visible(),f"{name}: hamburger must be available"
                    assert toggle.get_attribute("aria-expanded")=="false"
                    rect=toggle.bounding_box()
                    assert rect and rect["width"]>=44 and rect["height"]>=44,\
                        f"{name}: hamburger touch target is too small"
                    assert page.locator("#main-nav a[href='/where-we-serve/']").count()==0,\
                        "Where We Serve must be in the hamburger only"
                    page.screenshot(path=str(OUT/f"{name}-buttons.png"),
                                    animations="disabled",full_page=False)
                    toggle.click()
                    assert toggle.get_attribute("aria-expanded")=="true",f"{name}: open state missing"
                    assert toggle.get_attribute("aria-label")=="Close navigation menu"
                    assert toggle.locator("span").first.inner_text()=="Close",\
                        f"{name}: visible Close label missing"
                    assert panel.is_visible()
                    debug_focus=page.evaluate("""() => {
                        const first=document.querySelector('#site-menu-panel a[href]');
                        const active=document.activeElement;
                        return {first:first?.outerHTML.slice(0,125),
                          visible:first?getComputedStyle(first).display:null,
                          parentVisible:first?.parentElement?.getBoundingClientRect().height,
                          active:active?.outerHTML.slice(0,180),
                          panelHidden:document.querySelector('#site-menu-panel').hidden};
                    }""")
                    print(f"DEBUG {name}: {debug_focus}",flush=True)
                    page.wait_for_function(
                        "document.activeElement===document.querySelector('#site-menu-panel a[href]')",
                        timeout=2000,
                    )
                    # Accessibility: Escape closes the disclosure and returns focus.
                    page.keyboard.press("Escape")
                    assert toggle.get_attribute("aria-expanded")=="false"
                    assert not panel.is_visible()
                    assert page.evaluate(
                        "document.activeElement===document.getElementById('menu-toggle')"
                    ),f"{name}: Escape did not restore keyboard focus"
                    assert toggle.locator("span").first.inner_text()=="Menu"
                    toggle.click()
                    page.screenshot(path=str(OUT/f"{name}-menu-open.png"),
                                    animations="disabled",full_page=False)
                    # A focus change outside the disclosure should close it.
                    page.locator("a.primary-cta[href='/request-demo/']").focus()
                    assert not panel.is_visible(),f"{name}: focus leaving menu failed to close"
                    toggle.click()
                    panel.locator("a[href='/where-we-serve/']").first.click()
                    page.wait_for_url(host+"/where-we-serve/",timeout=10000)
                    assert page.locator("h1").first.is_visible(),f"{name}: regional link did not work"
                    page.locator("#menu-toggle").click()
                    link=page.locator("#site-menu-panel a[href='/where-we-serve/']")
                    assert link.get_attribute("aria-current")=="page",f"{name}: current page not marked"
                    assert page.locator("#site-menu-panel").is_visible()
                    page.keyboard.press("Escape")
                    # Inquiry buttons must say what they do and maintain the original mailto action.
                    response=page.goto(host+"/private-clinics/",wait_until="networkidle")
                    assert response and response.status==200
                    assert page.locator("a.solution-inline-cta[href^='mailto:']",
                        has_text="Email about your needs").count()==1
                    assert page.locator(".solution-connect a[href^='mailto:']",
                        has_text="Email our team").count()==1
                    for selector in ("#menu-toggle", ".solution-inline-cta", ".solution-connect a"):
                        node=page.locator(selector).first
                        assert node.is_visible(),f"{name}: {selector} hidden"
                        metrics=node.bounding_box()
                        assert metrics and metrics["height"]>=44,\
                            f"{name}: {selector} lacks a usable tap target"
                    width_metrics=page.evaluate("""() => ({
                        doc: document.documentElement.scrollWidth,
                        viewport: window.innerWidth,
                    })""")
                    assert width_metrics["doc"]<=width_metrics["viewport"]+3,\
                        f"{name}: horizontal overflow by {width_metrics['doc']-width_metrics['viewport']}px"
                    assert not errors,f"{name}: browser script errors: {errors}"
                    results.append({"view":name,"width":width,"height":height,
                                    "menuTargetPx":round(rect["width"]*rect["height"]),
                                    "noHorizontalOverflow":True,
                                    "escapeFocusRestore":True,
                                    "emailButtonLabelsClear":True,
                                    "currentPageHighlighted":True,
                                    "whereWeServeNavigable":True})
                    print(f"PASS {name} ({width}x{height}): menu/escape/focus/links/buttons/overflow")
                    ctx.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    gallery=[]
    for row in results:
        view=row["view"]
        gallery.append(f'''<article><h2>{escape(view)} — {row["width"]}px</h2>
<div><figure><a href="{view}-buttons.png"><img src="{view}-buttons.png"
alt="{escape(view)} homepage buttons" loading="lazy"></a>
<figcaption>Visible navigation and buttons</figcaption></figure>
<figure><a href="{view}-menu-open.png"><img src="{view}-menu-open.png"
alt="{escape(view)} expanded navigation" loading="lazy"></a>
<figcaption>Expanded hamburger navigation</figcaption></figure></div></article>''')
    html='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MMeD Button & Navigation Review</title>
<style>
body{margin:0;background:#f6f9fc;color:#0b1f3a;font:18px/1.5 "Times New Roman",Times,serif}
header{padding:34px 5%;background:#0b1f3a;color:#fff}
header h1{font-size:clamp(35px,5vw,62px);font-weight:400;margin:.2em 0}
header p{max-width:900px}
main{max-width:1450px;padding:26px 4%;margin:auto}
article{background:#fff;border:1px solid #d9e3eb;padding:24px;margin-bottom:24px}
article h2{font-size:28px;font-weight:400;margin:0 0 18px}
article>div{display:grid;grid-template-columns:1fr 1fr;gap:24px}
figure{margin:0;min-width:0}
img{display:block;width:100%;height:435px;object-fit:cover;object-position:top;border:1px solid #d9e3eb}
figcaption{font-size:15px;color:#4f647b;margin-top:8px}
@media(max-width:680px){article>div{grid-template-columns:1fr}img{height:380px}}
</style></head><body><header><p>MMED SYSTEMS / UX DESIGN REVIEW — NOT LIVE</p>
<h1>Buttons & navigation</h1><p>Original colors, logo and typography retained. Review the new visible menu states,
keyboard focus, current-page highlighting and clearer inquiry buttons.
All screenshots are generated locally from the review branch; no site deployment occurred.</p></header>
<main>'''+''.join(gallery)+'</main></body></html>'
    (OUT/"index.html").write_text(html,encoding="utf-8")
    (OUT/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(f"PASS: {len(results)} responsive UX checks and {len(results)*2} screenshots")


if __name__=="__main__":
    main()
