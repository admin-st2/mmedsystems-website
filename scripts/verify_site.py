#!/usr/bin/env python3
"""Validate the static MMeD corporate website before approving a deployment.

No network, third-party dependencies, credentials, or clinical-demo access needed.
Run with: python3 scripts/verify_site.py
"""
from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import sys
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
HOST = "mmedsystems.com"
BASE = f"https://{HOST}/"
ERRORS: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def local_file(path: str) -> Path:
    path = path.lstrip("/")
    if not path or path.endswith("/"):
        return ROOT / path / "index.html"
    plain = ROOT / path
    if plain.is_dir():
        return plain / "index.html"
    return plain


class HTMLChecks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.in_title = False
        self.title_seen = False
        self.h1s = 0
        self.meta: dict[str, str] = {}
        self.canonicals: list[str] = []
        self.hrefs: list[str] = []
        self.assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "title" and not self.title_seen:
            self.in_title = True
            self.title_seen = True
        elif tag == "h1":
            self.h1s += 1
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key.lower()] = a.get("content") or ""
        elif tag == "link":
            rel = (a.get("rel") or "").lower().split()
            href = a.get("href") or ""
            if "canonical" in rel:
                self.canonicals.append(href)
            if "stylesheet" in rel or "icon" in rel:
                self.assets.append(href)
        elif tag == "a" and a.get("href"):
            self.hrefs.append(a["href"] or "")
        elif tag == "script" and a.get("src"):
            self.assets.append(a["src"] or "")
        elif tag == "img" and a.get("src"):
            self.assets.append(a["src"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title.append(data)


def check_link(href: str, page_url: str, source: str) -> None:
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return
    absolute = urlparse(urljoin(page_url, href))
    if absolute.netloc != HOST or absolute.scheme not in ("http", "https"):
        return
    dest = local_file(absolute.path)
    check(dest.is_file(), f"{source}: broken local link/asset {href} -> {dest.relative_to(ROOT)}")


def main() -> int:
    check((ROOT / "CNAME").read_text(encoding="utf-8").strip() == HOST, "CNAME differs from canonical host")
    # IndexNow uses a deliberately public root-level key file. Validate its filename
    # and payload without printing the key or contacting any private service.
    indexnow_files = [p for p in ROOT.glob("*.txt")
                      if re.fullmatch(r"[a-zA-Z0-9-]{8,128}\.txt", p.name)]
    check(len(indexnow_files) == 1, "expected one public IndexNow verification file")
    for file in indexnow_files:
        check(file.read_text(encoding="utf-8").strip() == file.stem,
              "IndexNow verification content differs from its filename")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    check("Sitemap: https://mmedsystems.com/sitemap.xml" in robots, "robots.txt sitemap directive missing")
    check("Disallow: /" not in robots, "robots.txt blocks the entire website")

    tree = ET.parse(ROOT / "sitemap.xml")
    urls = [n.text.strip() for n in tree.findall(".//{*}loc") if n.text]
    check(bool(urls), "sitemap.xml has no URLs")
    check(len(urls) == len(set(urls)), "sitemap.xml contains duplicate URLs")
    check(BASE in urls, "homepage is missing from sitemap.xml")
    check(not any("demo.mmedsystems.com" in u or "/prototype/" in u for u in urls),
          "public sitemap must not expose the private demo or prototype")
    page_paths: set[Path] = set()
    for url in urls:
        parsed = urlparse(url)
        check(parsed.scheme == "https" and parsed.netloc == HOST, f"invalid canonical sitemap URL {url}")
        page_file = local_file(parsed.path)
        page_paths.add(page_file)
        if not page_file.is_file():
            ERRORS.append(f"{url}: sitemap URL does not resolve to a site file")
            continue
        content = page_file.read_text(encoding="utf-8")
        parser = HTMLChecks()
        parser.feed(content)
        label = str(page_file.relative_to(ROOT))
        title = " ".join(parser.title).strip()
        description = parser.meta.get("description", "")
        check(bool(title), f"{label}: missing title")
        check(bool(description), f"{label}: missing description")
        check(len(description) <= 180, f"{label}: description unusually long ({len(description)})")
        check(parser.h1s == 1, f"{label}: expected one H1, found {parser.h1s}")
        check(parser.canonicals == [url], f"{label}: canonical mismatch: {parser.canonicals}")
        check(parser.meta.get("viewport") is not None, f"{label}: missing viewport")
        check("noindex" not in parser.meta.get("robots", "").lower(), f"{label}: noindex in sitemap")
        if "og:title" in parser.meta:
            check(parser.meta["og:title"] == title, f"{label}: Open Graph title differs from title")
        if "og:description" in parser.meta:
            check(parser.meta["og:description"] == description, f"{label}: Open Graph description differs from meta")
        for href in parser.hrefs + parser.assets:
            check_link(href, url, label)

    # The site uses folder-based clean URLs; include new public pages in the sitemap.
    for file in ROOT.glob("*/index.html"):
        if file.parts[-2] == "prototype":
            continue
        check(file in page_paths, f"{file.relative_to(ROOT)}: public page absent from sitemap")

    # GitHub Pages serves 404.html for arbitrary missing paths. Root-relative assets
    # prevent broken CSS/JS on /missing/nested/ routes.
    not_found = (ROOT / "404.html").read_text(encoding="utf-8")
    not_found_parsed = HTMLChecks()
    not_found_parsed.feed(not_found)
    check("noindex" in not_found_parsed.meta.get("robots", "").lower(), "404.html must be noindex")
    check(all(asset.startswith("/") for asset in not_found_parsed.assets),
          "404.html asset references must start with /")

    prototype = ROOT / "prototype" / "index.html"
    if prototype.exists():
        p = HTMLChecks()
        p.feed(prototype.read_text(encoding="utf-8"))
        check("noindex" in p.meta.get("robots", "").lower(), "public prototype notice must stay noindex")

    if ERRORS:
        for error in ERRORS:
            print("FAIL:", error)
        print(f"\n{len(ERRORS)} issue(s) found.")
        return 1
    print(f"PASS: {len(urls)} sitemap URLs, page metadata, links, assets, canonical URLs, and demo exclusion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
