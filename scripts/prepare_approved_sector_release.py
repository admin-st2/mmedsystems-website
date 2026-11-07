#!/usr/bin/env python3
"""One-time import of owner-approved public website source. Never pushes or deploys.
The exact approved archive is SHA256-pinned. Existing booking/DNS/keys remain intact.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import zipfile
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = '521d6a0c3d2dde978e3fa29954b3c97f9c8bcc6a'
ARCHIVE_SHA = '1f309835bfa79579f0d70198b23b61a45bf13b15f126ff459ab3e28921be11eb'
RELEASE = 'sectors-2026-11-07'
BOOKING_PAGES = ['index.html', 'contact/index.html', 'partnerships/index.html', 'request-demo/index.html']
ALLOWED = {'.html','.css','.js','.svg','.png','.jpg','.jpeg','.webp','.gif','.ico','.xml'}


def old(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT).decode('utf-8')


def parse(text):
    return BeautifulSoup(text, 'html.parser')


def clone(node):
    return parse(str(node)).find()


def main():
    expected_branch = 'release/approved-sectors-2026-11-07'
    assert os.environ.get('GITHUB_HEAD_REF') == expected_branch, 'Not the approved release branch'
    assert (ROOT/'CNAME').read_text().strip() == 'mmedsystems.com'
    baseline = {p: old(p) for p in BOOKING_PAGES}
    baseline_sitemap = old('sitemap.xml')
    protect = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
               ('CNAME','eb611612248808a93c490c08665b7db8.txt','booking.css')}
    url = os.environ['MMED_APPROVED_SOURCE_URL']
    # The transfer contains only approved public site material, never secrets or patient data.
    with urlopen(Request(url,headers={'User-Agent':'MMeD-Approved-Release/1.0'}),timeout=60) as r:
        payload = r.read(5_000_001)
    assert len(payload) < 5_000_000, 'Oversized source transfer'
    assert hashlib.sha256(payload).hexdigest() == ARCHIVE_SHA, 'Approved source checksum mismatch'
    archive = zipfile.ZipFile(io.BytesIO(payload))
    assert sum(x.file_size for x in archive.infolist()) < 12_000_000
    for item in archive.infolist():
        p = PurePosixPath(item.filename)
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in str(p)
        assert item.filename.startswith('Source/') or item.filename in (
            'Content/sector-content.json','ROUTE-MAP.csv','BUILD-MANIFEST.json')
    manifest = json.loads(archive.read('BUILD-MANIFEST.json'))
    assert manifest['sector_count'] == 22 and manifest['fixed_price_tiers'] is False
    manifest_hashes = {f['path']: f['sha256'] for f in manifest.get('files', [])}
    copied = []
    with tempfile.TemporaryDirectory(prefix='mmed-approved-') as temporary:
        archive.extractall(temporary)
        source = Path(temporary)/'Source'
        for f in sorted(source.rglob('*')):
            if not f.is_file():
                continue
            rel = f.relative_to(source)
            name = rel.as_posix()
            if name in ('robots.txt','sitemap.xml','_headers'):
                continue
            assert f.suffix in ALLOWED and not any(v.startswith('.') for v in rel.parts)
            assert not any(v in ('scripts','supabase','deployment','docs','prototype') for v in rel.parts)
            if name in manifest_hashes:
                assert hashlib.sha256(f.read_bytes()).hexdigest() == manifest_hashes[name], name
            target = ROOT/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(f,target)
            copied.append(name)
    # Preserve new public booking actions from the newer production commit.
    for name in BOOKING_PAGES:
        latest = parse(baseline[name])
        current = parse((ROOT/name).read_text())
        for section in latest.select('main .mmed-booking'):
            current.select_one('main').append(clone(section))
        if name == 'index.html':
            prior_cta = current.select_one('a.primary-cta')
            booking = latest.select_one('.hero-right .booking-hero-actions')
            note = latest.select_one('.hero-right .booking-handoff-note')
            assert prior_cta is not None and booking is not None and note is not None
            prior_cta.replace_with(clone(booking))
            current.select_one('.hero-right .booking-hero-actions').insert_after(clone(note))
        if latest.select_one('link[href^="/booking.css"]') and not current.select_one('link[href^="/booking.css"]'):
            current.head.append(clone(latest.select_one('link[href^="/booking.css"]')))
        (ROOT/name).write_text(str(current),encoding='utf-8')
    # Book route was added after the reviewed package; retain its actual content and approved calendar URLs.
    book = parse((ROOT/'book/index.html').read_text())
    template = parse((ROOT/'index.html').read_text())
    book.select_one('header.site-header').replace_with(clone(template.select_one('header.site-header')))
    book.select_one('footer.site-footer').replace_with(clone(template.select_one('footer.site-footer')))
    (ROOT/'book/index.html').write_text(str(book),encoding='utf-8')
    pages = [ROOT/'index.html'] + sorted(ROOT.glob('*/index.html'))
    pages = [p for p in pages if p.parent.name not in ('prototype','docs','design-review','deployment','scripts','supabase')]
    assert len(pages) == 47, f'Expected 47 public pages including existing book route; got {len(pages)}'
    original_home = parse(baseline['index.html'])
    for f in pages + [ROOT/'404.html']:
        page = parse(f.read_text())
        for meta in page.select('meta[name="robots"]'):
            meta.decompose()
        if f.name == '404.html':
            m = page.new_tag('meta',attrs={'name':'robots','content':'noindex,nofollow'})
            page.head.append(m)
        tag = page.new_tag('meta', attrs={'name':'mmed-release','content':RELEASE})
        page.head.append(tag)
        for node in page.select('link[href],script[src]'):
            attr = 'href' if node.name == 'link' else 'src'
            value = node.get(attr,'')
            file = value.split('?')[0].lstrip('/')
            if file in ('mmed-v6.css','mmed-v6.js','sector-pages.css','sector-pages.js'):
                node[attr] = '/'+file+'?v='+RELEASE
        # Keep the company's existing verified LinkedIn destination available.
        footer = page.select_one('footer.site-footer')
        if footer and not footer.select_one('a[href="https://www.linkedin.com/company/mmed-systems/"]'):
            old_link = original_home.select_one('footer a[href="https://www.linkedin.com/company/mmed-systems/"]')
            if old_link:
                groups = footer.select('.footer-column')
                groups[-1].append(clone(old_link))
        if f == ROOT/'index.html':
            # Preserve established Organization/WebSite identity, supplementing the approved WebPage markup.
            for script in original_home.select('script[type="application/ld+json"]'):
                try:
                    obj = json.loads(script.string or script.get_text())
                except ValueError:
                    continue
                if '@graph' in obj:
                    page.head.append(clone(script))
        # Correct obsolete email-only FAQ explanation now that approved booking is active.
        if f == ROOT/'faq/index.html':
            for details in page.select('details.faq-item'):
                q = details.select_one('summary').get_text(' ',strip=True).lower()
                if 'how do i request a demonstration' in q:
                    answer = details.select_one('.faq-answer')
                    if answer:
                        answer.clear()
                        answer.append(parse('<p>Visit <a href="/request-demo/">Request a Demo</a> to schedule a private demonstration or compose a business inquiry by email. You can also <a href="/book/">view all meeting options</a>. Scheduling a meeting does not grant access to the private demonstration; approval and NDA acceptance remain separate. Please do not submit patient information.</p>').p)
        f.write_text(str(page),encoding='utf-8')
    # Review-only source protections are not appropriate on approved public pages.
    (ROOT/'robots.txt').write_text(old('robots.txt'),encoding='utf-8')
    assert 'Disallow: /\n' not in (ROOT/'robots.txt').read_text()
    # Never copy the preview-only _headers noindex file. Existing unrelated config was not removed.
    if (ROOT/'_headers').exists():
        assert 'noindex' not in (ROOT/'_headers').read_text().lower()
    old_urls = {n.text.strip() for n in ET.fromstring(baseline_sitemap).findall('.//{*}loc') if n.text}
    urls=[]
    for f in pages:
        p = parse(f.read_text())
        canonical = p.select_one('link[rel="canonical"]')['href']
        assert canonical.startswith('https://mmedsystems.com/')
        assert 'noindex' not in ' '.join(x.get('content','') for x in p.select('meta[name="robots"]')).lower()
        urls.append(canonical)
    assert old_urls.issubset(urls), 'An existing indexed URL would be lost'
    assert len(urls)==len(set(urls))==47
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sorted(urls):
        sitemap += '<url><loc>'+url+'</loc><lastmod>2026-11-07</lastmod></url>\n'
    (ROOT/'sitemap.xml').write_text(sitemap+'</urlset>\n',encoding='utf-8')
    (ROOT/'docs/releases').mkdir(parents=True,exist_ok=True)
    (ROOT/'docs/releases/sector-routes-2026-11-07.json').write_text(json.dumps(manifest['routes'],indent=2),encoding='utf-8')
    for name,digest in protect.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, 'Protected file altered: '+name
    # Preserve all approved booking destinations exactly, and do not create active forms.
    for name in BOOKING_PAGES:
        before = parse(baseline[name])
        after = parse((ROOT/name).read_text())
        hrefs = {a['href'] for a in before.select('a[href^="https://calendar.google.com/"]')}
        assert hrefs.issubset({a['href'] for a in after.select('a[href]')}), name
    (ROOT/'scripts/verify_site.py').write_text('from verify_sector_release import main\nif __name__ == "__main__":\n    raise SystemExit(main())\n',encoding='utf-8')
    (ROOT/'scripts/browser_smoke.py').write_text('from sector_release_browser import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
    # Keep scheduled checks; pin only their runtime to the supported browser image.
    wf=ROOT/'.github/workflows/website-checks.yml'
    wf.write_text(wf.read_text().replace('runs-on: ubuntu-latest','runs-on: ubuntu-24.04'),encoding='utf-8')
    report={'release':RELEASE,'approved_archive_sha256':ARCHIVE_SHA,'base_commit':BASE,
            'sector_pages':22,'public_pages':47,'imported_files':copied,
            'booking_preserved':True,'private_demo_changed':False,
            'review_restrictions_removed_from_public_html':True}
    (ROOT/'docs/releases/sectors-2026-11-07.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PREPARED: 22 sectors, 47 public pages, custom pricing, FAQ-only artwork; booking preserved.')

if __name__=='__main__':
    main()
