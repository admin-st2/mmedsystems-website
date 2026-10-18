#!/usr/bin/env python3
"""Check the public MMeD website from a GitHub Actions network.

Uses default trusted TLS verification. Does not contact the private demo.
Run: python3 scripts/check_live_site.py
"""
from __future__ import annotations

from urllib.request import Request, urlopen
from urllib.parse import urlparse
from urllib.error import URLError
import socket
import sys
import xml.etree.ElementTree as ET

DOMAIN = "mmedsystems.com"
CANONICAL = "https://mmedsystems.com/"
PAGES = [
    ("https://mmedsystems.com/", CANONICAL, "html"),
    ("http://mmedsystems.com/", CANONICAL, "html"),
    ("https://www.mmedsystems.com/", CANONICAL, "html"),
    ("http://www.mmedsystems.com/", CANONICAL, "html"),
    ("https://mmedsystems.com/platform/", CANONICAL + "platform/", "html"),
    ("https://mmedsystems.com/private-clinics/", CANONICAL + "private-clinics/", "html"),
    ("https://mmedsystems.com/contact/", CANONICAL + "contact/", "html"),
    ("https://mmedsystems.com/robots.txt", CANONICAL + "robots.txt", "robots"),
    ("https://mmedsystems.com/sitemap.xml", CANONICAL + "sitemap.xml", "xml"),
]


def main() -> int:
    errors: list[str] = []
    for host in (DOMAIN, "www." + DOMAIN):
        try:
            addresses = sorted({r[4][0] for r in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
            print(f"DNS {host}: {', '.join(addresses)}", flush=True)
        except OSError as exc:
            errors.append(f"DNS lookup failed for {host}: {exc}")

    for url, final_url, kind in PAGES:
        try:
            req = Request(url, headers={"User-Agent": "MMeD-Site-Health-Check/1.0"})
            with urlopen(req, timeout=15) as response:
                status = response.status
                actual_url = response.geturl()
                body = response.read(1_000_000)
                print(f"{status} {url} -> {actual_url} ({len(body)} bytes)", flush=True)
                if status != 200:
                    errors.append(f"{url}: expected 200 final status, got {status}")
                if actual_url != final_url:
                    errors.append(f"{url}: expected canonical {final_url}, got {actual_url}")
                if kind == "html" and b"MMeD Systems" not in body:
                    errors.append(f"{url}: missing MMeD identity in returned page")
                elif kind == "robots" and b"Sitemap: https://mmedsystems.com/sitemap.xml" not in body:
                    errors.append("robots.txt missing sitemap directive")
                elif kind == "xml":
                    root = ET.fromstring(body)
                    urls = root.findall(".//{*}loc")
                    if len(urls) < 20:
                        errors.append(f"sitemap.xml only exposes {len(urls)} URLs")
        except (OSError, URLError, ValueError, ET.ParseError) as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    if errors:
        for msg in errors:
            print("FAIL:", msg, flush=True)
        return 1
    print("PASS: public DNS, trusted HTTPS, canonical redirects, public pages, robots.txt and sitemap.xml.")
    print("Private clinical demo was not requested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
