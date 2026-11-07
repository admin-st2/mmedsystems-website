#!/usr/bin/env python3
"""Dependency-free release audit for the owner-approved sector website."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='https://mmedsystems.com/'
ERRORS=[]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1=0; self.meta={}; self.canonical=[]; self.links=[]; self.assets=[]; self.ids=set()
        self.title=''; self.in_title=False; self.title_seen=False; self.json_blocks=[]; self.in_json=False
        self.buffer=''; self.images=[]; self.forms=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag=='title' and not self.title_seen: self.in_title=True; self.title_seen=True
        if tag=='h1': self.h1+=1
        if tag=='meta': self.meta[(a.get('name') or a.get('property') or '').lower()]=a.get('content','')
        if tag=='link':
            rel=(a.get('rel') or '').split()
            if 'canonical' in rel: self.canonical.append(a.get('href',''))
            if 'stylesheet' in rel or 'icon' in rel: self.assets.append(a.get('href',''))
        if tag=='a': self.links.append(a.get('href',''))
        if tag=='script':
            if a.get('src'): self.assets.append(a['src'])
            if a.get('type')=='application/ld+json': self.in_json=True; self.buffer=''
        if tag=='img': self.assets.append(a.get('src','')); self.images.append(a)
        if tag=='form': self.forms+=1
    def handle_endtag(self,tag):
        if tag=='title': self.in_title=False
        if tag=='script' and self.in_json:
            self.json_blocks.append(self.buffer); self.buffer=''; self.in_json=False
    def handle_data(self,data):
        if self.in_title: self.title+=data
        if self.in_json: self.buffer+=data


def check(ok,msg):
    if not ok: ERRORS.append(msg)


def local(path):
    rel=unquote(path).lstrip('/')
    p=ROOT/rel
    if not rel or rel.endswith('/') or p.is_dir(): p=p/'index.html'
    return p


def main():
    ERRORS.clear()
    check((ROOT/'CNAME').read_text().strip()=='mmedsystems.com','CNAME changed')
    robots=(ROOT/'robots.txt').read_text()
    check('Sitemap: '+BASE+'sitemap.xml' in robots,'Missing sitemap directive')
    check(not re.search(r'^\s*Disallow:\s*/\s*$',robots,re.M),'Whole-site crawl block')
    keys=[p for p in ROOT.glob('*.txt') if re.fullmatch(r'[A-Za-z0-9-]{8,128}\.txt',p.name)]
    check(len(keys)==1,'Expected existing single IndexNow key')
    for key in keys: check(key.read_text().strip()==key.stem,'IndexNow key mismatch')
    urls=[n.text.strip() for n in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc') if n.text]
    check(len(urls)==len(set(urls))==47,'Expected 47 unique canonical pages including booking')
    route_file=ROOT/'docs/releases/sector-routes-2026-11-07.json'
    sectors=json.loads(route_file.read_text())
    check(len(sectors)==22,'Expected 22 reviewed sectors')
    cache={}; titles=[]; faq_art_pages=[]
    for url in urls:
        u=urlparse(url)
        check(u.scheme=='https' and u.netloc=='mmedsystems.com' and not u.query and not u.fragment,'Unsafe sitemap URL '+url)
        check(not any(x in u.path for x in ('/prototype','/staging','/preview','/docs/')),'Private/draft sitemap route '+url)
        file=local(u.path)
        if not file.is_file(): check(False,'Missing page '+url); continue
        text=file.read_text(); page=Page(); page.feed(text); cache[file]=page; titles.append(page.title)
        check(page.h1==1,url+': expected one H1')
        check(bool(page.title.strip()),url+': missing title')
        check(bool(page.meta.get('description')),url+': missing description')
        check(page.canonical==[url],url+': wrong canonical '+str(page.canonical))
        check('noindex' not in page.meta.get('robots','').lower(),url+': still noindex')
        check(page.meta.get('mmed-release')=='sectors-2026-11-07',url+': missing release marker')
        check(page.meta.get('viewport') is not None,url+': missing viewport')
        if page.meta.get('og:title'): check(page.meta['og:title']==page.title,url+': inconsistent sharing title')
        if page.meta.get('og:description'): check(page.meta['og:description']==page.meta.get('description'),url+': inconsistent description')
        for js in page.json_blocks:
            try: json.loads(js)
            except ValueError: check(False,url+': invalid JSON-LD')
        for im in page.images:
            check('alt' in im,url+': image missing alt')
            check(bool(im.get('width')) and bool(im.get('height')),url+': image dimensions absent')
        check('/faq/' in page.links,url+': FAQ footer missing')
        check('/where-we-serve/' in page.links,url+': sector directory unreachable')
        check('https://demo.mmedsystems.com' not in text,url+': private demo URL leaked')
        check('MMeD-Sector-Website-Review.html' not in text,url+': offline wrapper leaked')
        check(not re.search(r'(\$149|\$249|\$399|2 months free)',text,re.I),url+': obsolete tier pricing leaked')
        if 'assets/faq/connected-care.webp' in text: faq_art_pages.append(url)
    check(len(titles)==len(set(titles)),'Duplicate public page titles')
    check(faq_art_pages==[BASE+'faq/'],'Original FAQ artwork used on other pages')
    for url in urls:
        file=local(urlparse(url).path)
        if file not in cache: continue
        page=cache[file]
        for href in page.links+page.assets:
            if not href or href.startswith(('mailto:','tel:','data:','javascript:')): continue
            absolute=urlparse(urljoin(url,href))
            if absolute.netloc!='mmedsystems.com': continue
            target=local(absolute.path)
            check(target.is_file(),url+': broken internal target '+href)
            if absolute.fragment and target.is_file() and target.suffix=='.html':
                if target not in cache:
                    v=Page(); v.feed(target.read_text()); cache[target]=v
                check(unquote(absolute.fragment) in cache[target].ids,url+': broken anchor '+href)
    hub=(ROOT/'where-we-serve/index.html').read_text()
    hp=Page();hp.feed(hub)
    check('sector-search' in hp.ids,'Hub filter missing')
    check(hub.count('data-sector=')==22,'Hub must link all 22 sectors')
    main_hub=re.search(r'<main\b[^>]*>([\s\S]*?)</main>',hub).group(1)
    check(not re.search(r'\b(Uganda|Kenya|Tanzania|Rwanda|Africa|United States)\b',main_hub),'Sector hub still contains geography')
    for sector in sectors:
        url=BASE.rstrip('/')+sector['path'];file=local(sector['path']);text=file.read_text()
        check(url in urls,'Sector not in sitemap '+url)
        check(sector['path'] in hp.links,'Sector not in hub '+url)
        check('/assets/sectors/' in text,'Sector art missing '+url)
        check('/contact/#pricing-inquiries' in text,'Itemized pricing path missing '+url)
        check('/request-demo/' in text,'Demo path missing '+url)
        check('<details' in text,'Buyer question missing '+url)
    for name in ('index.html','contact/index.html','partnerships/index.html','request-demo/index.html','book/index.html'):
        check('https://calendar.google.com/calendar/' in (ROOT/name).read_text(),'Existing booking lost: '+name)
    check('NDA' in (ROOT/'request-demo/index.html').read_text(),'NDA explanation lost')
    check('fictional' in (ROOT/'faq/index.html').read_text().lower(),'Fictional-only demo explanation lost')
    check('noindex' in (ROOT/'404.html').read_text(),'404 must remain noindex')
    if (ROOT/'_headers').exists(): check('noindex' not in (ROOT/'_headers').read_text(),'Review X-Robots header leaked')
    for bad in ('__review_router.js','__staging_guard.js','__staging_guard.css'):
        check(not (ROOT/bad).exists(),'Preview-only guard shipped: '+bad)
    public_files={local(urlparse(u).path) for u in urls}
    for file in ROOT.glob('*/index.html'):
        if file.parent.name in ('prototype','docs','deployment','scripts','supabase','design-review'):continue
        check(file in public_files,'Public folder page missing from sitemap: '+str(file.relative_to(ROOT)))
    if ERRORS:
        for error in ERRORS:print('FAIL:',error)
        print(f'{len(ERRORS)} release issues');return 1
    print('PASS: 47 canonical pages, 22 sectors, internal links/assets/anchors, robots, booking, FAQ-only imagery, custom pricing and private-demo separation.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
