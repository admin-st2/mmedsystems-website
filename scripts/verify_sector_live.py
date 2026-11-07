#!/usr/bin/env python3
"""Verify the actual public release after Pages publication; optional single IndexNow batch.
Never accesses private demo, booking services, inboxes or databases.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from verify_sector_release import Page

ROOT=Path(__file__).resolve().parents[1]
BASE='https://mmedsystems.com/'
RELEASE='sectors-2026-11-07'
OUT=ROOT/'live-release-report'
UA='MMeD-Approved-Release-Verification/1.0'


def get(url):
    req=Request(url,headers={'User-Agent':UA,'Cache-Control':'no-cache'})
    with urlopen(req,timeout=20) as r:
        body=r.read(3_000_001)
        assert len(body)<3_000_000,'Oversized response '+url
        return r.status,r.geturl(),dict(r.headers.items()),body


def inspect(url):
    row={'url':url,'issues':[],'assets':[]}
    try:
        status,final,headers,data=get(url)
        page=Page();page.feed(data.decode('utf-8'))
        row.update(status=status,final=final,release=page.meta.get('mmed-release'),canonical=page.canonical,title=page.title)
        if status!=200 or final!=url:row['issues'].append('status_or_redirect')
        if page.meta.get('mmed-release')!=RELEASE:row['issues'].append('wrong_release')
        if page.canonical!=[url]:row['issues'].append('canonical')
        if page.h1!=1 or not page.meta.get('description'):row['issues'].append('metadata')
        robots=page.meta.get('robots','')+' '+next((v for k,v in headers.items() if k.lower()=='x-robots-tag'),'')
        if re.search(r'\b(noindex|none)\b',robots,re.I):row['issues'].append('noindex')
        for value in page.assets:
            u=urljoin(url,value)
            if urlparse(u).netloc=='mmedsystems.com':row['assets'].append(u)
        if url==BASE+'where-we-serve/':
            row['sectorCards']=data.count(b'data-sector=')
            if row['sectorCards']!=22:row['issues'].append('sector_count')
            if b'sector-search' not in data:row['issues'].append('sector_search')
        if url==BASE+'faq/':
            row['originalFaqArtwork']=b'assets/faq/connected-care.webp' in data
            if not row['originalFaqArtwork']:row['issues'].append('faq_artwork')
        if url==BASE+'pricing/' and re.search(rb'\$149|\$249|\$399|2 months free',data,re.I):row['issues'].append('obsolete_fixed_pricing')
        if url in (BASE,BASE+'contact/',BASE+'request-demo/',BASE+'book/',BASE+'partnerships/'):
            row['calendarLinks']=sum(h.startswith('https://calendar.google.com/calendar/') for h in page.links)
            if row['calendarLinks']<1:row['issues'].append('booking_missing')
    except Exception as e:
        row['issues'].append(type(e).__name__+': '+str(e)[:200])
    return row


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--notify-indexnow',action='store_true');args=ap.parse_args()
    report={'checkedAtUtc':datetime.now(timezone.utc).isoformat(),'release':RELEASE,'pages':[], 'assets':[], 'errors':[], 'indexnow':{'attempted':False,'indexingConfirmed':False}}
    OUT.mkdir(exist_ok=True)
    try:
        expected={n.text.strip() for n in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc') if n.text}
        assert len(expected)==47 and all(urlparse(u).netloc=='mmedsystems.com' for u in expected)
        # GitHub Pages and its CDN publish asynchronously after the merge.
        # Wait boundedly for the exact release marker and sitemap, then validate every page.
        ready=False
        for attempt in range(16):
            try:
                home=inspect(BASE)
                _,_,_,xml=get(BASE+'sitemap.xml')
                actual={n.text.strip() for n in ET.fromstring(xml).findall('.//{*}loc') if n.text}
                if not home['issues'] and actual==expected:ready=True;break
            except Exception:pass
            print('Awaiting exact published release; probe',attempt+1,flush=True)
            time.sleep(15)
        assert ready,'Exact release not yet published; no search notification sent'
        _,_,_,robots=get(BASE+'robots.txt')
        policy=RobotFileParser();policy.parse(robots.decode().splitlines())
        assert all(policy.can_fetch(bot,u) for bot in ('bingbot','Googlebot','DuckDuckBot','OAI-SearchBot') for u in expected),'robots block'
        with ThreadPoolExecutor(max_workers=4) as pool:
            report['pages']=list(pool.map(inspect,sorted(expected)))
        bad=[p for p in report['pages'] if p['issues']]
        if bad:
            # Allow CDN paths to converge without issuing duplicate notifications.
            time.sleep(15)
            with ThreadPoolExecutor(max_workers=4) as pool:report['pages']=list(pool.map(inspect,sorted(expected)))
        assert not [p for p in report['pages'] if p['issues']], 'Some published pages failed release checks'
        assets=sorted({a for p in report['pages'] for a in p['assets']})
        for url in assets:
            status,final,headers,payload=get(url)
            assert status==200 and final==url and len(payload)>0,'Missing asset '+url
            report['assets'].append({'url':url,'status':status,'bytes':len(payload)})
        key='eb611612248808a93c490c08665b7db8'
        key_url=BASE+key+'.txt'
        _,_,_,key_data=get(key_url);assert key_data.decode().strip()==key,'IndexNow ownership mismatch'
        report.update(pagesPassed=len(report['pages']),assetsPassed=len(report['assets']),robotsAllowed=True,keyVerified=True)
        if args.notify_indexnow:
            payload=json.dumps({'host':'mmedsystems.com','key':key,'keyLocation':key_url,'urlList':sorted(expected)}).encode()
            req=Request('https://api.indexnow.org/indexnow',data=payload,method='POST',headers={'Content-Type':'application/json','User-Agent':UA})
            receipt={'attempted':True,'urlCount':len(expected),'indexingConfirmed':False,'atUtc':datetime.now(timezone.utc).isoformat()}
            try:
                with urlopen(req,timeout=30) as r:receipt.update(httpStatus=r.status,response=r.read(2048).decode())
            except HTTPError as e:receipt.update(httpStatus=e.code,response=e.read(2048).decode())
            except (URLError,OSError) as e:receipt.update(httpStatus=None,error=str(e)[:200],outcome='receipt_unknown_do_not_repeat_automatically')
            report['indexnow']=receipt
        print(json.dumps({k:report[k] for k in ('release','pagesPassed','assetsPassed','robotsAllowed','keyVerified','indexnow')},indent=2),flush=True)
    except Exception as e:
        report['errors'].append(type(e).__name__+': '+str(e));print('LIVE CHECK FAILED',report['errors'],flush=True)
    finally:
        (OUT/'report.json').write_text(json.dumps(report,indent=2))
        (OUT/'SUMMARY.md').write_text('# MMeD live release verification\n\n'+json.dumps({k:v for k,v in report.items() if k not in ('pages','assets')},indent=2))
    return 1 if report['errors'] else 0

if __name__=='__main__':raise SystemExit(main())
