#!/usr/bin/env python3
"""Render desktop and mobile screenshots from a pull request's LOCAL files.

This is a preview of proposed public-site code, not a production deployment.
No private demo, PHI, account credentials, or external host is accessed.
"""
from __future__ import annotations

from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "visual-review"
ROUTES = [
    ("home", "/", "Homepage"),
    ("where-we-serve", "/where-we-serve/", "Where We Serve"),
    ("solutions", "/solutions/", "Solutions"),
    ("private-clinics", "/private-clinics/", "Private Clinics"),
    ("hospitals", "/hospitals/", "Hospitals"),
    ("resources", "/resources/", "Resources"),
    ("request-demo", "/request-demo/", "Request a Demo"),
]
VIEWS = [
    ("desktop", 1440, 900),
    ("mobile", 390, 844),
]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    captures: list[tuple[str, str, str]] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for view_name, width, height in VIEWS:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=1,
                        reduced_motion="reduce",
                    )
                    page = context.new_page()
                    for slug, path, heading in ROUTES:
                        response = page.goto(base_url + path, wait_until="networkidle", timeout=30000)
                        assert response is not None and response.status == 200, (
                            f"{path} preview failed to load"
                        )
                        page.locator("h1").first.wait_for(state="visible")
                        # Disable entrances and scrolling offsets for review screenshots.
                        page.add_style_tag(content="""
                            *, *::before, *::after { animation: none !important;
                              transition: none !important; scroll-behavior: auto !important; }
                            [data-reveal] { opacity: 1 !important;
                              transform: none !important; }
                        """)
                        page.evaluate("window.scrollTo(0, 0)")
                        name = f"{slug}-{view_name}.png"
                        page.screenshot(
                            path=str(OUTPUT / name),
                            full_page=True,
                            animations="disabled",
                        )
                        captures.append((view_name, heading, name))
                        print(f"Preview: {heading} — {view_name} ({width} x {height})")
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    cards: list[str] = []
    for view, title, filename in captures:
        cards.append(
            f'<article><h2>{escape(title)} — {escape(view)}</h2>'
            f'<a href="{escape(filename)}"><img src="{escape(filename)}" '
            f'alt="Screenshot of {escape(title)} at {escape(view)} viewport" loading="lazy"></a>'
            f'<p><a href="{escape(filename)}">Open full-size image</a></p></article>'
        )
    gallery = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MMeD Website — Pre-Publication Visual Review</title>
<style>
body{margin:0;background:#f5f8fc;color:#0b1f3a;font:18px/1.45 "Times New Roman",Times,serif}
header{padding:36px max(24px,5vw);background:#0b1f3a;color:white}
header h1{margin:.2em 0;font-size:clamp(36px,5vw,64px);font-weight:400}
header p{max-width:950px}main{max-width:1500px;margin:auto;padding:35px max(22px,4vw)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,380px),1fr));gap:28px}
article{background:white;padding:22px;border:1px solid #d9e3eb}
article h2{font-size:26px;font-weight:400}
img{width:100%;height:400px;object-fit:cover;object-position:top;box-shadow:0 3px 20px #0001}
a{color:#1267b2}a:focus-visible{outline:3px solid #1267b2;outline-offset:3px}
</style></head><body>
<header><p>MMeD SYSTEMS / DESIGN REVIEW</p>
<h1>Preview before publishing.</h1>
<p>These desktop and mobile screenshots are rendered from the pull-request files on a local test server, not the live website. Review typography, navigation, spacing, regional content, and CTA placement before approving a release.</p>
</header><main><div class="grid">
""" + "\n".join(cards) + """</div></main></body></html>"""
    (OUTPUT / "index.html").write_text(gallery, encoding="utf-8")
    (OUTPUT / "REVIEW_INSTRUCTIONS.txt").write_text(
        "MMeD Website Visual Review\n"
        "==========================\n"
        "1. Unzip this artifact.\n"
        "2. Open index.html in a browser to review desktop and mobile layouts.\n"
        "3. Open any individual PNG to zoom in.\n"
        "4. Comment with adjustments on the pull request or in the ChatGPT project.\n"
        "5. Do not merge or deploy until the owner explicitly approves.\n"
        "Screenshots use pull-request code served locally, not the live domain.\n",
        encoding="utf-8",
    )
    print(f"Rendered {len(captures)} screenshots with an offline HTML gallery.")


if __name__ == "__main__":
    main()
