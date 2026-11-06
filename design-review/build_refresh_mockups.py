#!/usr/bin/env python3
"""BEFORE/AFTER screenshot mockups for MMeD website design approval.

Design-only! Copies current public HTML/CSS/JS to temporary local folders,
applies experimental DOM patches ONLY to the AFTER copy, captures screenshots,
and produces an offline HTML comparison gallery.

Nothing writes to the live website, GitHub Pages, staging branch or demo host.
No actual customer data, certifications, screenshots or integrations are invented.
"""
from __future__ import annotations

from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
import re
import shutil
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CONCEPT = ROOT / "design-review"
OUTPUT = ROOT / "refresh-review"
PAGES = [
    ("home", "/", "Home"),
    ("solutions", "/solutions/", "Services & Products"),
    ("about", "/about/", "About"),
    ("contact", "/contact/", "Contact"),
    ("pricing", "/pricing/", "Pricing — NEW"),
]
VIEWS = [("desktop", 1440, 900), ("mobile", 390, 844)]
EXTENSIONS = {".html", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg",
              ".webp", ".gif", ".ico", ".woff", ".woff2"}
EXCLUDE = {"design-review", "refresh-review", "scripts", "docs", "deployment",
           "supabase", "prototype", "node_modules", ".github", ".git",
           "visual-review", "dist-staging", "__pycache__"}


class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return


def make_site(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for file in ROOT.rglob("*"):
        if not file.is_file():
            continue
        relative = file.relative_to(ROOT)
        if any(segment in EXCLUDE or segment.startswith(".") for segment in relative.parts[:-1]):
            continue
        if file.suffix.lower() not in EXTENSIONS:
            continue
        output = root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, output)


def modify_chrome(html: str) -> str:
    """Insert Pricing at the end of existing links but before Contact.

    Preserve all pre-existing relative order, logo, colors and nav wrappers.
    """
    match = re.search(r'(<nav aria-label="Main navigation"[^>]*>)(.*?)(</nav>)', html, re.S)
    assert match, "Current MMeD desktop menu not found"
    body = match.group(2)
    assert 'href="/platform/"' in body and 'href="/solutions/"' in body, "Menu changed"
    contact = re.search(r'<a(?=[^>]*class="contact-link")[^>]*>', body)
    assert contact, "Contact navigation link missing"
    # Owner's existing direction: Where We Serve belongs in the hamburger,
    # not in main desktop navigation or in a large homepage section.
    body = body.replace('<a href="/where-we-serve/">Where We Serve</a>', "")
    contact = re.search(r'<a(?=[^>]*class="contact-link")[^>]*>', body)
    assert contact
    body = body[:contact.start()] + '<a href="/pricing/">Pricing</a>' + body[contact.start():]
    html = html[:match.start()] + match.group(1) + body + match.group(3) + html[match.end():]

    hamburger = '<a href="/contact/">Contact <span aria-hidden="true">↗</span></a>'
    assert hamburger in html, "Hamburger contact link missing"
    html = html.replace(hamburger,
        '<a href="/pricing/">Pricing <span aria-hidden="true">↗</span></a>' + hamburger, 1)

    # Add the sticky header CTA without removing the existing navigation or menu.
    needle = '</nav>\n<button aria-controls="site-menu-panel"'
    assert needle in html, "Header menu structure changed"
    html = html.replace(needle,
        '</nav>\n<a class="refresh-header-demo" href="/request-demo/">Request a Demo</a>\n'
        '<button aria-controls="site-menu-panel"', 1)

    footer_link = '<a href="/where-we-serve/">Where We Serve</a>'
    # Keep regional link in hamburger only in the preview, as previously requested.
    html = html.replace(footer_link, "", 1)
    assert '<a href="/where-we-serve/">Where We Serve <span' in html, "Hamburger region link lost"
    assert 'class="wordmark"' in html, "Existing logo lost"

    html = html.replace('</head>',
        '<meta name="robots" content="noindex,nofollow">'
        '<link rel="stylesheet" href="/refresh-concept.css"></head>', 1)
    html = html.replace('</body>',
        '<script src="/refresh-concept.js" defer></script></body>', 1)
    return html


TRUST = '''
<section class="refresh-trust" aria-label="Trust and verification status">
  <div class="container refresh-trust-row">
   <div class="refresh-trust-item"><span class="refresh-small-kicker">SECURITY DESIGN</span>
    <h3>Protection built into the architecture</h3>
    <p>Technical safeguards and independent evidence require verification before any compliance claim.</p></div>
   <div class="refresh-trust-item"><span class="refresh-small-kicker">HIPAA / BAA READINESS</span>
    <h3>Compliance assessment in progress</h3>
    <p>No official certification or production readiness is claimed in this design concept.</p></div>
   <div class="refresh-trust-item"><span class="refresh-small-kicker">CUSTOMER EVIDENCE</span>
    <h3>Verified references only</h3>
    <p>Approved client logos, testimonials and measurable results are required before release.</p></div>
  </div>
</section>'''

DEVICE = '''
<div class="refresh-hero-device">
 <div class="refresh-device-window" aria-label="Reserved placement for verified product screenshot">
  <div class="refresh-device-top"><i></i><i></i><i></i></div>
  <div class="refresh-device-body">
   <div class="refresh-device-sidebar"><b></b><b></b><b></b><b></b></div>
   <div class="refresh-device-placeholder">
    <span class="kicker">ACTUAL MMED PRODUCT SCREENSHOT REQUIRED</span>
    <strong>The clinical workspace, as it really looks.</strong>
    <p>Design placeholder only. Replace with an approved product capture using fictional patient information; do not present this as a working feature screenshot.</p>
   </div>
  </div>
 </div>
 <p class="refresh-device-caption">Concept frame — real MMeD demo screenshot pending approval</p>
</div>'''

TOUR = '''
<section class="refresh-inline-tour container" aria-labelledby="tour-heading">
 <div class="refresh-tour-head"><div><p class="kicker">EXPLORE THE WORKFLOW</p>
  <h2 id="tour-heading">See how care<br><em>stays connected.</em></h2></div>
  <p>Walk through clinical, operational and patient-facing views. The final tour will use real, approved captures from MMeD's fictional-data demonstration.</p></div>
 <div class="refresh-tour-tabs" aria-label="Preview tour topics">
  <button type="button" aria-pressed="true" data-tour="clinical">Clinical care</button>
  <button type="button" aria-pressed="false" data-tour="operations">Operations</button>
  <button type="button" aria-pressed="false" data-tour="patient">Patient experience</button>
 </div>
 <div class="refresh-tour-panel"><div><span class="kicker">SCREEN CAPTURE PENDING</span>
  <h3 id="refresh-tour-title">Clinical workflows</h3>
  <p id="refresh-tour-desc">Approved interface screenshot required before publication. This panel marks the placement for encounter and documentation views.</p></div></div>
</section>'''

STORIES = '''
<section class="refresh-stories" aria-labelledby="stories-heading">
 <div class="container"><p class="kicker">EVIDENCE THAT EARNS TRUST</p>
 <h2 id="stories-heading">Real voices. Real outcomes.</h2>
 <p>After customers provide permission, this space can feature verified experiences with names, practices, photos, and measurable outcomes. No examples have been invented for this preview.</p>
 <div class="refresh-stories-grid">
  <article class="refresh-evidence-card"><span class="refresh-small-kicker">APPROVAL REQUIRED</span><strong>Customer story</strong><p>Verified clinician name, practice, authorized portrait, and a sourced outcome will appear here once available.</p></article>
  <article class="refresh-evidence-card"><span class="refresh-small-kicker">APPROVAL REQUIRED</span><strong>Clinical operations case study</strong><p>Publication requires customer consent and independently supportable before-and-after results.</p></article>
 </div></div>
</section>'''


def replace_home(html: str) -> str:
    # Keep existing hero/headline and all site sections intact.
    lead = '<p class="hero-lead">'
    assert lead in html
    html = html.replace(lead,
        '<p class="refresh-hero-statement">Connected information. Coordinated care.</p>' + lead, 1)
    cta = re.search(r'<a class="primary-cta" href="/request-demo/">.*?</a>', html, re.S)
    assert cta, "Existing homepage Request a Demo CTA missing"
    original = cta.group(0)
    html = html[:cta.start()] + '<div class="refresh-hero-actions">' + original + \
        '<a class="refresh-secondary-cta" href="/pricing/">View Pricing</a></div>' + html[cta.end():]
    start = html.index('<section aria-labelledby="hero-headline"')
    close = html.index('</section>', start)
    html = html[:close] + DEVICE + '</section>' + TRUST + html[close+len('</section>'):]

    # Keep the user-requested regional page in the hamburger, off the homepage.
    region = re.search(r'<section class="reach-teaser"[\s\S]*?</section>', html)
    if region:
        html = html[:region.start()] + html[region.end():]
    assert '<section class="reach-teaser"' not in html

    # Add a previewable product tour without rewriting existing clinical copy.
    marker = '<section aria-labelledby="adaptation-heading"'
    assert marker in html
    html = html.replace(marker, TOUR + '\n' + marker, 1)

    # Insert evidence placeholder before the closing main to avoid fake client data.
    html = html.replace('</main>', STORIES + '\n</main>', 1)

    # Use EXISTING "who we serve" category structure, add contextual pricing links.
    copy = '''
<div class="refresh-section-copy">
 <h3>Find a plan by care setting.</h3>
 <p>Exploring care for one provider, a growing clinic or a network?
 <a href="/pricing/#solo">Solo</a>, <a href="/pricing/#practice">Practice</a> and
 <a href="/pricing/#clinic-network">Clinic Network</a> are proposed starting points.
 Hospital and enterprise requirements are scoped individually.</p>
</div>'''
    marker = '</section>\n</main>'
    if marker in html:
        html = html.replace(marker, copy + '\n' + marker, 1)
    # In pages where the inserted Stories section follows existing audience section,
    # add the copy immediately after the existing audience grid instead.
    elif 'class="audience-grid' in html:
        pos = html.index('</section>', html.index('class="audience-grid'))
        html = html[:pos] + copy + html[pos:]
    return html


def replace_solutions(html: str) -> str:
    block = '''
<div class="refresh-section-copy container">
 <h3>Plans that match the size of your organization.</h3>
 <p>View our proposed <a href="/pricing/#solo">Solo</a>,
 <a href="/pricing/#practice">Practice</a>,
 <a href="/pricing/#clinic-network">Clinic Network</a>, and
 <a href="/pricing/#enterprise">Enterprise</a> tiers. Final features and terms are still subject to approval.</p>
</div>'''
    marker = '<section class="solution-connect">'
    assert marker in html
    return html.replace(marker, block + marker, 1)


def replace_about(html: str) -> str:
    block = '''
<div class="refresh-section-copy container">
 <h3>Trust is built with evidence.</h3>
 <p>Our security-first design, clinical safety review, and planned local configuration should be supported by verified documentation. Certifications, customer references and measurable claims will be published only after approval.</p>
</div>'''
    marker = '<section class="solution-connect">'
    assert marker in html
    return html.replace(marker, block + marker, 1)


def replace_contact(html: str) -> str:
    block = '''
<section class="refresh-contact-form" aria-labelledby="short-form-title">
 <div class="container"><p class="kicker">DEMO INQUIRY / DESIGN CONCEPT</p>
 <h2 id="short-form-title">Tell us about your practice.</h2>
 <p>A shorter demo-request form could reduce friction, but it will not collect or transmit information until a secure backend is separately approved and activated.</p>
 <form class="refresh-form-fields" aria-label="Inactive demo request form design preview">
  <label>Full name <input type="text" name="name" autocomplete="name" placeholder="Full name" disabled></label>
  <label>Work email <input type="email" name="email" autocomplete="email" placeholder="name@practice.com" disabled></label>
  <label>Practice size <select name="practice-size" disabled><option>Select practice size</option><option>1 provider</option><option>2–10 providers</option><option>11+ providers</option></select></label>
  <label>Specialty <input type="text" name="specialty" placeholder="Your specialty" disabled></label>
 </form><button class="refresh-form-preview" disabled>Submit request — preview only</button>
 <p class="refresh-copy-note">Do not enter patient information. The live website's existing business email inquiry workflow is unchanged.</p>
 </div>
</section>'''
    marker = '<section class="solution-connect">'
    assert marker in html
    return html.replace(marker, block + marker, 1)


def change_pages(after: Path) -> None:
    for file in after.rglob("index.html"):
        original = file.read_text(encoding="utf-8")
        updated = modify_chrome(original)
        path = file.relative_to(after).as_posix()
        if path == "index.html":
            updated = replace_home(updated)
        elif path == "solutions/index.html":
            updated = replace_solutions(updated)
        elif path == "about/index.html":
            updated = replace_about(updated)
        elif path == "contact/index.html":
            updated = replace_contact(updated)
        file.write_text(updated, encoding="utf-8")

    (after / "pricing").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONCEPT / "pricing-proposal.html", after / "pricing" / "index.html")
    shutil.copy2(CONCEPT / "refresh-concept.css", after / "refresh-concept.css")
    shutil.copy2(CONCEPT / "refresh-concept.js", after / "refresh-concept.js")

    # Verify the original design system was copied unchanged.
    assert (after / "mmed-v6.css").read_bytes() == (ROOT / "mmed-v6.css").read_bytes()
    assert (after / "mmed-v6.js").read_bytes() == (ROOT / "mmed-v6.js").read_bytes()

    homepage = (after / "index.html").read_text(encoding="utf-8")
    assert homepage.count('class="primary-cta"') == 1
    assert "refresh-device-placeholder" in homepage
    assert "reach-teaser" not in homepage
    pricing = (after / "pricing" / "index.html").read_text(encoding="utf-8")
    for figure in ("$149", "$1,490", "$249", "$2,490", "$399", "$3,990", "Custom"):
        assert figure in pricing, f"Pricing figure missing: {figure}"
    assert "to be confirmed" in pricing.lower()
    assert "pending final confirmation" in pricing.lower()


def serve(folder: Path):
    handler = partial(SilentHandler, directory=str(folder))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_address[1]}"


def screenshot_set(browser, base: str, label: str, output: Path, entries: list):
    for view, width, height in VIEWS:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            reduced_motion="reduce",
        )
        page = context.new_page()
        for slug, route, title in PAGES:
            if label == "before" and slug == "pricing":
                continue
            response = page.goto(base + route, wait_until="networkidle", timeout=30000)
            assert response and response.status == 200, f"Could not render {label} {route}"
            page.locator("h1").first.wait_for(state="visible")
            page.add_style_tag(content="""
              *,*::before,*::after{animation:none!important;transition:none!important}
              [data-reveal]{opacity:1!important;transform:none!important}
              html{scroll-behavior:auto!important}
            """)
            if label == "after":
                assert page.locator("#main-nav a[href='/where-we-serve/']").count() == 0, (
                    "Where We Serve must remain hamburger-only"
                )
                assert page.locator("#site-menu-panel a[href='/where-we-serve/']").count() == 1, (
                    "Where We Serve missing from hamburger menu"
                )
                assert page.evaluate("getComputedStyle(document.querySelector('.site-header')).position") == "sticky", (
                    "Header is not sticky"
                )
                assert page.locator('.refresh-header-demo[href="/request-demo/"]').count() == 1
                assert page.locator('#main-nav a[href="/pricing/"]').count() == 1
                if slug == "pricing":
                    assert page.locator(".pricing-card").count() == 4
                    page.locator('[data-billing="annual"]').click()
                    assert page.locator('#solo [data-price]').inner_text() == "$1,490"
                    assert page.locator('#practice [data-price]').inner_text() == "$2,490"
                    assert page.locator('#clinic-network [data-price]').inner_text() == "$3,990"
                    page.locator('[data-billing="monthly"]').click()
                    assert page.locator('#solo [data-price]').inner_text() == "$149"
                    assert page.locator(".pricing-faq details").count() >= 6
                if slug == "contact":
                    assert page.locator(".refresh-contact-form input:disabled").count() == 3
                    assert page.locator(".refresh-contact-form button:disabled").count() == 1
                if slug == "home" and view == "mobile":
                    toggle = page.locator("#menu-toggle")
                    assert toggle.is_visible(), "Mobile hamburger toggle missing"
                    toggle.click()
                    panel = page.locator("#site-menu-panel")
                    assert panel.is_visible(), "Mobile hamburger did not open"
                    panel.locator('a[href="/pricing/"]').first.click()
                    page.wait_for_url(base + "/pricing/", timeout=10000)
                    assert page.locator(".pricing-card").count() == 4, "Mobile Pricing navigation failed"
                    page.goto(base + "/", wait_until="networkidle", timeout=30000)
                    page.locator("h1").first.wait_for(state="visible")
                    page.add_style_tag(content="[data-reveal]{opacity:1!important;transform:none!important}")
            page.evaluate("window.scrollTo(0,0)")
            target = output / f"{slug}-{label}-{view}.png"
            page.screenshot(path=str(target), full_page=True, animations="disabled")
            entries.append((slug, label, view, title, target.name))
            print(f"PASS screenshot: {title} / {label} / {view} ({width}x{height})")
        context.close()


def gallery(entries: list, output: Path) -> None:
    items = []
    for slug, route, title in PAGES:
        for view, _, _ in VIEWS:
            before = next((v[4] for v in entries if v[0]==slug and v[1]=="before" and v[2]==view), None)
            after = next((v[4] for v in entries if v[0]==slug and v[1]=="after" and v[2]==view), None)
            if not after:
                continue
            left = (f'<div><span>BEFORE — EXISTING LIVE DESIGN</span><a href="{before}"><img src="{before}" alt="{escape(title)} before at {view}"></a></div>'
                    if before else '<div><span>BEFORE — NOT PRESENT</span><p>This is a proposed new Pricing page.</p></div>')
            right = f'<div><span>AFTER — CONCEPT ONLY</span><a href="{after}"><img src="{after}" alt="{escape(title)} concept at {view}"></a></div>'
            items.append(f'<article><h2>{escape(title)} · {view}</h2><div class="pair">{left}{right}</div></article>')
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MMeD website | Before and After Mockups</title>
<style>body{margin:0;background:#f6f9fc;color:#0b1f3a;font:17px/1.5 "Times New Roman",serif}
header{background:#0b1f3a;color:white;padding:40px max(24px,5vw)}
header h1{font-size:clamp(34px,5vw,65px);font-weight:400;margin:9px 0}
header p{max-width:900px}main{max-width:1440px;padding:30px max(18px,4vw);margin:auto}
article{background:white;margin:0 0 28px;padding:23px;border:1px solid #d9e3eb}
article h2{font-size:29px;font-weight:400;margin:0 0 18px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.pair div{min-width:0}
.pair span{font-size:12px;font-weight:700;letter-spacing:.11em;color:#1267b2}
.pair img{width:100%;height:460px;object-fit:cover;object-position:top;border:1px solid #d9e3eb;margin-top:8px}
.pair img:hover{opacity:.88}.pair a:focus-visible{outline:3px solid #1267b2}
@media(max-width:680px){.pair{grid-template-columns:1fr}.pair img{height:400px}}
</style></head><body><header><p>MMeD SYSTEMS · DESIGN APPROVAL</p>
<h1>Before & After — Website Refresh</h1>
<p>Real screenshots rendered from the existing public website source, and proposed visual mockups. The concepts retain the original fonts, logo, palette and page architecture. Neither preview has been deployed to production or private staging.</p>
<p>All customer logos, certifications, testimonials, product screenshots, integration badges and unapproved commercial terms remain explicitly unverified. Pricing plan features and add-ons are provisional.</p>
</header><main>""" + "\n".join(items) + "</main></body></html>"
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "README.txt").write_text(
        "MMED DESIGN REVIEW — NOT FOR PRODUCTION\n"
        "Open index.html to compare before/after desktop/mobile screenshots.\n"
        "18 screenshots total: 4 existing pages before+after at two viewports, plus new Pricing at two viewports.\n"
        "The actual product screenshot, verified customer evidence and commercial terms are intentionally not fabricated.\n"
        "Do not publish this concept without the owner's approval and real data verification.\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT.glob("*.png"):
        old.unlink()
    entries = []
    with tempfile.TemporaryDirectory(prefix="mmed-review-") as scratch:
        tmp = Path(scratch)
        before = tmp / "before"
        after = tmp / "after"
        make_site(before)
        make_site(after)
        change_pages(after)
        bserver, bt, burl = serve(before)
        aserver, at, aurl = serve(after)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    screenshot_set(browser, burl, "before", OUTPUT, entries)
                    screenshot_set(browser, aurl, "after", OUTPUT, entries)
                finally:
                    browser.close()
        finally:
            bserver.shutdown()
            aserver.shutdown()
            bserver.server_close()
            aserver.server_close()
            bt.join(timeout=5)
            at.join(timeout=5)
    gallery(entries, OUTPUT)
    assert len(entries)==18, f"Expected 18 screenshots; got {len(entries)}"
    print("PASS: 18 screenshots and gallery generated without changing live/staging pages.")


if __name__ == "__main__":
    main()
