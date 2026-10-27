#!/usr/bin/env python3
"""Prepare a fail-closed Cloudflare Pages staging build from the LIVE-design source.

Default mode publishes only a neutral setup page. A complete site build is
refused unless the destination pages.dev hostname independently returns a
Cloudflare Access login redirect for several anonymous probe URLs.

Cloudflare Pages build command:
  python3 scripts/build_private_staging.py
Build output directory:
  dist-staging

Deploy to a NEW staging-only Pages project; NEVER the production site.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist-staging"

# Only extensions required to serve the existing public static website.
PUBLIC_EXTENSIONS = {
    ".html", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg",
    ".webp", ".avif", ".gif", ".ico", ".woff", ".woff2",
}
EXCLUDED_DIRS = {
    ".git", ".github", "docs", "deployment", "scripts", "supabase",
    "prototype", "node_modules", "dist-staging", "visual-review",
    ".venv", "__pycache__", "tests",
}
# This public-site build must not publish source, CNAME, service tokens,
# the IndexNow key, SQL, migrations, robots/sitemap files from production,
# or operational docs.
SKIP_FILES = {"CNAME", "robots.txt", "sitemap.xml", "_headers", "_redirects"}
PROBES = ("/", "/where-we-serve/", "/private-clinics/", "/request-demo/")


class PreventRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def access_is_active(host: str) -> bool:
    """Fail closed unless several anonymous requests hit an Access login gate."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.pages\.dev", host):
        print("ERROR: Stage hostname must be the exact <project>.pages.dev hostname.", file=sys.stderr)
        return False
    opener = build_opener(PreventRedirect())
    for route in PROBES:
        req = Request(
            "https://" + host + route,
            headers={"User-Agent": "MMeD-Staging-Anonymous-Access-Check/1.0",
                     "Cache-Control": "no-cache"},
            method="GET",
        )
        try:
            result = opener.open(req, timeout=12)
            status = result.status
            result.close()
            print(f"DENIED: {route} anonymously returned HTTP {status}.", file=sys.stderr)
            return False
        except HTTPError as error:
            destination = error.headers.get("Location", "")
            # Cloudflare Access commonly redirects to an account
            # *.cloudflareaccess.com URL or a /cdn-cgi/access/login endpoint.
            if error.code not in (301, 302, 303, 307, 308) or not (
                "cloudflareaccess.com" in destination.lower()
                or "/cdn-cgi/access/login" in destination.lower()
            ):
                print(
                    f"DENIED: {route} did not return a verified Cloudflare "
                    f"Access login redirect (HTTP {error.code}).", file=sys.stderr
                )
                return False
        except (URLError, TimeoutError, OSError) as error:
            print(f"DENIED: Cannot verify anonymous Access gate for {route}: {type(error).__name__}",
                  file=sys.stderr)
            return False
    print("PASS: Primary Pages hostname requires Cloudflare Access on all probed routes.")
    print("WARNING: Separately verify immutable deployment and wildcard preview hostnames.")
    return True


HEADERS = """/
  X-Robots-Tag: noindex, nofollow, noarchive, nosnippet
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
"""
ROBOTS = "User-agent: *\nDisallow: /\n"


def reset_output() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)


def write_safety_files() -> None:
    (OUTPUT / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (OUTPUT / "_headers").write_text(HEADERS, encoding="utf-8")


def write_placeholder() -> None:
    reset_output()
    (OUTPUT / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>MMeD Systems — Staging Setup</title>'
        '<style>body{margin:0;min-height:100vh;display:grid;place-items:center;'
        'font:20px/1.5 "Times New Roman",serif;background:white;color:#0b1f3a}'
        'main{padding:40px;max-width:640px}h1{font-weight:400;font-size:48px}'
        '</style></head><body><main><h1>Private staging is not active.</h1>'
        '<p>This placeholder contains no draft website content.</p></main></body></html>',
        encoding="utf-8",
    )
    write_safety_files()
    print("SAFE: Setup placeholder only; the corporate website was NOT deployed.")


def copy_site() -> None:
    reset_output()
    copied = 0
    for source in ROOT.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in relative.parts[:-1]):
            continue
        if source.name.startswith(".") or source.name in SKIP_FILES:
            continue
        if source.suffix.lower() not in PUBLIC_EXTENSIONS:
            continue
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1
    if not (OUTPUT / "index.html").is_file():
        raise RuntimeError("No homepage found in staging export")
    # Apply a small STAGING watermark and disable transactional actions only
    # to the COPY. No change is made to the actual website's page or stylesheet.
    guard_css = """#mmed-staging-flag{position:fixed;z-index:2147483600;
right:12px;bottom:12px;padding:9px 13px;border:1px solid #d9e3eb;
background:#0b1f3a;color:#fff;font:700 12px "Times New Roman",serif;
letter-spacing:.08em;box-shadow:0 4px 20px #0003}"""
    guard_js = r"""(() => {
const flag=document.createElement('div');flag.id='mmed-staging-flag';
flag.textContent='PRIVATE STAGING — NOT LIVE';document.body.appendChild(flag);
document.addEventListener('click',e=>{
 const el=e.target instanceof Element?e.target.closest('a[href]'):null;
 if(!el)return;
 const href=el.getAttribute('href')||'';
 if(/^(mailto:|tel:|sms:)/i.test(href) ||
    (/^https?:\/\//i.test(href) && new URL(href,location.href).origin!==location.origin)){
   e.preventDefault();
   alert('Staging preview: external links and email actions are disabled.');
 }
},true);
document.addEventListener('submit',e=>{
  e.preventDefault();e.stopImmediatePropagation();
  alert('Staging preview: form submission is disabled.');
},true);
})();"""
    (OUTPUT / "__staging_guard.css").write_text(guard_css, encoding="utf-8")
    (OUTPUT / "__staging_guard.js").write_text(guard_js, encoding="utf-8")
    injection = ('<meta name="robots" content="noindex,nofollow,noarchive">'
                 '<link rel="stylesheet" href="/__staging_guard.css">')
    for path in OUTPUT.rglob("*.html"):
        markup = path.read_text(encoding="utf-8")
        if "</head>" not in markup or "</body>" not in markup:
            raise RuntimeError(f"Malformed source HTML: {path.relative_to(OUTPUT)}")
        markup = markup.replace("</head>", injection + "</head>", 1)
        markup = markup.replace("</body>",
                                '<script src="/__staging_guard.js" defer></script></body>', 1)
        path.write_text(markup, encoding="utf-8")
    write_safety_files()
    print(f"PASS: Copied {copied} public website assets into Access-protected staging export.")
    print("No DNS, production files or private clinical demo assets changed.")


def main() -> None:
    # Never copy the public site before Cloudflare Access is working.
    if os.getenv("MMED_STAGING_MODE", "locked").strip().lower() != "private":
        write_placeholder()
        return
    host = os.getenv("MMED_STAGING_HOST", "").strip().lower()
    if not access_is_active(host):
        raise SystemExit("SECURITY BLOCK: Refusing to deploy site without Cloudflare Access.")
    copy_site()


if __name__ == "__main__":
    main()
