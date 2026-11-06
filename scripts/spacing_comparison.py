#!/usr/bin/env python3
"""Compare MMeD section spacing without deploying any site changes.

Locally serves two copies of the same PR HTML/CSS/JS. "Before" removes only
the final, tagged spacing calibration; "After" retains it. Content and brand
tokens are identical. Chromium measures height/overflow and captures both.
"""
from __future__ import annotations

from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spacing-review"
MARKER = "/* MMeD spacing calibration: compact section rhythm, review-only 2026-11-06. */"
PAGES = [
    ("home", "/", "Homepage"),
    ("solutions", "/solutions/", "Solutions"),
    ("clinic", "/private-clinics/", "Private Clinics"),
    ("where", "/where-we-serve/", "Where We Serve"),
]
VIEWS = [
    ("desktop", 1440, 900, True),
    ("tablet", 768, 1024, False),
    ("mobile", 390, 844, True),
    ("small-mobile", 320, 720, False),
]
EXTENSIONS = {".html", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg",
              ".webp", ".gif", ".ico", ".woff", ".woff2"}
EXCLUDE = {"docs", "scripts", "deployment", "supabase", "prototype",
           "dist-staging", "visual-review", "spacing-review", "node_modules",
           "design-review", ".git", ".github", "__pycache__"}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


def copy_site(dst: Path, before: bool) -> None:
    count = 0
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(v in EXCLUDE or v.startswith(".") for v in rel.parts[:-1]):
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel.as_posix() == "mmed-v6.css":
            css = path.read_text(encoding="utf-8")
            assert css.count(MARKER) == 1, "Unable to isolate the spacing-only CSS diff"
            if before:
                css = css.split(MARKER)[0]
            target.write_text(css, encoding="utf-8")
        else:
            shutil.copy2(path, target)
        count += 1
    assert (dst / "index.html").is_file()
    assert (dst / "where-we-serve" / "index.html").is_file()
    print(f"{'BEFORE' if before else 'AFTER'}: {count} public static assets copied")


def serve(folder):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(folder)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_address[1]}"


def capture(browser, root_url, version, view_name, width, height, save, rows):
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        reduced_motion="reduce",
    )
    page = context.new_page()
    for slug, route, title in PAGES:
        response = page.goto(root_url + route, wait_until="networkidle", timeout=30000)
        assert response and response.status == 200, f"Could not open {version} {route}"
        page.locator("h1").first.wait_for(state="visible")
        page.add_style_tag(content="""*,*::before,*::after{animation:none!important;
          transition:none!important;scroll-behavior:auto!important}
          [data-reveal]{opacity:1!important;transform:none!important}""")
        stats = page.evaluate("""() => {
            const main=document.querySelector('main');
            const sections=[...main.querySelectorAll(':scope > section, :scope > div.philosophy-strip')];
            const styles = el => {
                const v=getComputedStyle(el);
                const rect=el.getBoundingClientRect();
                return {selector:el.className||el.id||el.tagName.toLowerCase(),
                  height:Math.round(rect.height),
                  paddingTop:Math.round(parseFloat(v.paddingTop)||0),
                  paddingBottom:Math.round(parseFloat(v.paddingBottom)||0)}
            };
            return {
              docHeight:document.documentElement.scrollHeight,
              scrollWidth:document.documentElement.scrollWidth,
              innerWidth:window.innerWidth,
              sections:sections.map(styles),
              font:getComputedStyle(document.body).fontFamily,
              nav:document.querySelector('#site-menu-panel a[href="/where-we-serve/"]')!==null,
              mainCta:document.querySelector('a.primary-cta[href="/request-demo/"]')!==null
            }
        }""")
        assert stats["nav"], "Hamburger regional navigation missing"
        assert "Times New Roman" in stats["font"], "Existing font changed"
        overflow = stats["scrollWidth"] - stats["innerWidth"]
        if overflow > 3:
            culprits = page.evaluate("""() => [...document.querySelectorAll('body *')]
              .map(el => ({el,box:el.getBoundingClientRect()}))
              .filter(o => o.box.width > 0 && o.box.right > window.innerWidth + 3)
              .slice(0,8)
              .map(o => ({tag:o.el.tagName.toLowerCase(),
                className:String(o.el.className || '').slice(0,100),
                right:Math.round(o.box.right),width:Math.round(o.box.width)}))
            """)
            print(f"OVERFLOW {slug}/{version}/{view_name}: {overflow}px, elements={culprits}")
        if version == "after":
            assert overflow <= 3, (
                f"{slug}/{version}/{view_name}: horizontal overflow {overflow}px"
            )
        assert stats["mainCta"] if route == "/" else True, "Homepage main CTA missing"
        rows.append({"page": slug, "view": view_name, "version": version, **stats})
        if save:
            page.evaluate("window.scrollTo(0, 0)")
            file = OUT / f"{slug}-{version}-{view_name}.png"
            page.screenshot(path=str(file), full_page=True, animations="disabled")
            print(f"Captured {slug} {version} {view_name}: {stats['docHeight']}px tall")
    context.close()


def create_gallery(rows):
    cases = []
    for slug, _, label in PAGES:
        for view in ("desktop", "mobile"):
            b = next(x for x in rows if x["page"]==slug and x["view"]==view and x["version"]=="before")
            a = next(x for x in rows if x["page"]==slug and x["view"]==view and x["version"]=="after")
            improvement = b["docHeight"]-a["docHeight"]
            cases.append(f"""<section><h2>{escape(label)} — {view}</h2>
<p>Document height: {b['docHeight']}px → {a['docHeight']}px
({improvement:+d}px less scrolling). Brand colors and font unchanged.</p>
<div class="pair"><div><strong>BEFORE</strong><a href="{slug}-before-{view}.png">
<img src="{slug}-before-{view}.png" alt="{escape(label)} original {view} screenshot"></a></div>
<div><strong>AFTER</strong><a href="{slug}-after-{view}.png">
<img src="{slug}-after-{view}.png" alt="{escape(label)} compact {view} screenshot"></a></div></div></section>""")
    css = """body{margin:0;color:#0b1f3a;background:#f6f9fc;font:18px/1.55 'Times New Roman',serif}
header{background:#0b1f3a;color:#fff;padding:28px max(24px,5vw)}
header h1{font-size:clamp(32px,5vw,62px);font-weight:400;margin:.2em 0}
header p{max-width:940px}main{padding:20px max(16px,4vw);max-width:1560px;margin:auto}
section{padding:20px;background:white;margin:22px 0;border:1px solid #d9e3eb}
h2{font-size:26px;font-weight:400}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.pair>div{min-width:0}.pair strong{font-size:14px;letter-spacing:.1em;color:#1267b2}
img{object-fit:cover;object-position:top;display:block;width:100%;height:430px;border:1px solid #d9e3eb}
a:focus-visible{outline:3px solid #1267b2}
@media(max-width:680px){.pair{grid-template-columns:1fr}img{height:330px}}"""
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>MMeD Section Spacing Before/After</title><style>{css}</style></head>'
            f'<body><header><p>MMeD SYSTEMS / DESIGN REVIEW ONLY</p>'
            f'<h1>Compact, consistent section spacing.</h1>'
            f'<p>Same website, same brand, same content. Before/after screenshots '
            f'are captured locally from the review branch. No live deployment.</p>'
            f'</header><main>{"".join(cases)}</main></body></html>')
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "measurements.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (OUT / "REVIEW.txt").write_text(
        "MMeD Systems spacing-only visual review.\n"
        "Unzip and open index.html; see before/after desktop and mobile comparisons.\n"
        "measurements.json includes tablet (768px) and small mobile (320px) overflow checks.\n"
        "No production deployment, new platform, paid service, or clinical demo access.\n",
        encoding="utf-8",
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    all_rows = []
    with TemporaryDirectory(prefix="mmed-spacing-") as scratch:
        temp = Path(scratch)
        before, after = temp / "before", temp / "after"
        copy_site(before, True)
        copy_site(after, False)
        server_before, thread_before, url_before = serve(before)
        server_after, thread_after, url_after = serve(after)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for view, width, height, save in VIEWS:
                        capture(browser, url_before, "before", view, width, height, save, all_rows)
                        capture(browser, url_after, "after", view, width, height, save, all_rows)
                finally:
                    browser.close()
        finally:
            for server, thread in [(server_before,thread_before),(server_after,thread_after)]:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
    create_gallery(all_rows)
    for key in {(x["page"],x["view"]) for x in all_rows}:
        before = next(x for x in all_rows if (x["page"],x["view"])==key and x["version"]=="before")
        after = next(x for x in all_rows if (x["page"],x["view"])==key and x["version"]=="after")
        assert after["docHeight"] < before["docHeight"], f"No spacing reduction: {key}"
    print(f"PASS: {len(all_rows)} measurements, 16 full-page images, no mobile overflow.")


if __name__ == "__main__":
    main()
