#!/usr/bin/env python3
"""Live public-site crawlability audit and optional one-off IndexNow submission.

No design deployment, account secrets, paid API, private demo or email access.
Uses the already-published IndexNow verification key. Default is read-only;
--submit explicitly sends ONE batch to the protocol's global endpoint.
Do not repeatedly submit unchanged URLs. Receipts do not prove indexing.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import socket
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = 'mmedsystems.com'
BASE = 'https://' + HOST
SITEMAP = BASE + '/sitemap.xml'
ENDPOINT = 'https://api.indexnow.org/indexnow'
OUT = ROOT / 'search-discovery-report'
MAX_BYTES = 2_000_000
AGENT = 'MMeD-Public-Search-Readiness/1.0'
BOTS = ('bingbot', 'DuckDuckBot', 'Slurp', 'Googlebot')
BLOCKED = ('/prototype', '/staging', '/preview', '/design-review', '/docs/',
           '/scripts/', '/supabase/', '/deployment/', '/visual-review/')


def safe_public_url(url: str) -> bool:
    p = urlparse(url)
    return (p.scheme == 'https' and p.netloc == HOST and not p.query and
            not p.fragment and not p.username and not p.password and
            not any(p.path.startswith(x) for x in BLOCKED))


def get(url: str, user_agent: str = AGENT) -> tuple[int, str, dict, str]:
    req = Request(url, headers={'User-Agent': user_agent, 'Cache-Control': 'no-cache'})
    try:
        with urlopen(req, timeout=20) as r:
            payload = r.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ValueError('response too large')
            return r.status, r.geturl(), dict(r.headers.items()), payload.decode('utf-8', errors='replace')
    except HTTPError as exc:
        return exc.code, exc.geturl(), dict(exc.headers.items()), exc.read(4096).decode('utf-8', errors='replace')


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.in_title = False
        self.title_seen = False
        self.canonicals = []
        self.directives = []
        self.h1s = 0
        self.description = ''
        self.bing_verification = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title' and not self.title_seen:
            self.in_title = True
            self.title_seen = True
        elif tag == 'link' and 'canonical' in (a.get('rel') or '').lower().split():
            self.canonicals.append(a.get('href', ''))
        elif tag == 'meta':
            name = (a.get('name') or '').lower()
            if name in ('robots', 'bingbot', 'googlebot', 'slurp', 'duckduckbot'):
                self.directives.append((a.get('content') or '').lower())
            if name == 'description':
                self.description = a.get('content') or ''
            if name == 'msvalidate.01':
                self.bing_verification = True
        elif tag == 'h1':
            self.h1s += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def audit_page(url: str, robots: RobotFileParser) -> dict:
    row = {'url': url, 'issues': [], 'eligibleForNotification': False}
    try:
        status, final, headers, body = get(url)
        row.update(status=status, finalUrl=final, bytes=len(body.encode('utf-8')))
        if status != 200:
            row['issues'].append('http_' + str(status))
        if final != url:
            row['issues'].append('redirect_or_wrong_final_url')
        parser = HeadParser()
        parser.feed(body)
        row.update(title=' '.join(parser.title).strip(), canonical=parser.canonicals,
                   descriptionPresent=bool(parser.description), h1Count=parser.h1s)
        if parser.canonicals != [url]:
            row['issues'].append('canonical_mismatch')
        h = {k.lower(): v for k, v in headers.items()}
        directives = ' '.join(parser.directives + [h.get('x-robots-tag', '').lower()])
        if re.search(r'\b(noindex|none)\b', directives):
            row['issues'].append('noindex')
        row['robotsAllowed'] = {bot: robots.can_fetch(bot, url) for bot in BOTS}
        if not all(row['robotsAllowed'].values()):
            row['issues'].append('robots_disallow')
        if not row['title'] or not parser.description or parser.h1s != 1:
            row['issues'].append('metadata_incomplete')
        row['eligibleForNotification'] = not row['issues']
        if url == BASE + '/':
            row['bingMetaVerificationPresent'] = parser.bing_verification
        return row
    except (OSError, URLError, ValueError) as exc:
        row['issues'].append(type(exc).__name__ + ': ' + str(exc)[:240])
        return row


def submit(urls: list[str], key: str, location: str) -> dict:
    if not urls or len(urls) > 100 or any(not safe_public_url(u) for u in urls):
        raise ValueError('Refusing invalid or unsafe URL batch')
    payload = json.dumps({'host': HOST, 'key': key, 'keyLocation': location,
                          'urlList': urls}).encode('utf-8')
    req = Request(ENDPOINT, data=payload, method='POST', headers={
        'Content-Type': 'application/json; charset=utf-8', 'User-Agent': AGENT})
    result = {'endpoint': ENDPOINT, 'attemptedUrls': len(urls), 'urls': urls,
              'submittedAtUtc': datetime.now(timezone.utc).isoformat(),
              'indexingConfirmed': False}
    try:
        with urlopen(req, timeout=30) as r:
            result.update(httpStatus=r.status, response=r.read(4096).decode('utf-8', errors='replace'))
    except HTTPError as exc:
        result.update(httpStatus=exc.code,
                      response=exc.read(4096).decode('utf-8', errors='replace'),
                      retryAfter=exc.headers.get('Retry-After'))
    except (URLError, OSError, TimeoutError) as exc:
        result.update(httpStatus=None, error=type(exc).__name__ + ': ' + str(exc)[:240],
                      outcome='receipt_unknown_do_not_assume_rejected')
        return result
    code = result['httpStatus']
    result['outcome'] = ('received_not_proof_of_indexing' if code == 200 else
                         'accepted_pending_validation' if code == 202 else
                         'not_accepted')
    return result


def save(report: dict) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (OUT / 'public-urls.txt').write_text('\n'.join(report.get('sitemapUrls', [])) + '\n', encoding='utf-8')
    lines = ['# MMeD public search discovery — ' + report['checkedAtUtc'],
             '', 'This run does not deploy or modify the website.',
             'Search-engine receipt is NOT proof of ranking or indexing.', '',
             '- Live pages audited: ' + str(len(report.get('pages', []))),
             '- Pages eligible for notification: ' + str(report.get('eligibleCount', 0)),
             '- Key reachable and matching: ' + str(report.get('keyFileVerified', False)),
             '- Submission: ' + json.dumps(report.get('submission', {'outcome': 'not attempted'})),
             '- Fatal errors: ' + json.dumps(report.get('fatalErrors', [])),
             '', '## Scope', 'Only canonical public mmedsystems.com URLs in the live sitemap.',
             'Private demo, other subdomains, previews, draft pricing and unmerged designs excluded.',
             '', '## Reporting limits',
             'Bing Webmaster account ownership and index status are not authenticated by this script.',
             'A missing Bing meta tag does not prove lack of verification: Google import or DNS may be used.',
             'No paid SEO connection, email access, or account permission change is used.']
    text = '\n'.join(lines)
    (OUT / 'SUMMARY.md').write_text(text, encoding='utf-8')
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(text + '\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--submit', action='store_true', help='Send one verified live URL batch')
    args = ap.parse_args()
    report = {'checkedAtUtc': datetime.now(timezone.utc).isoformat(),
              'host': HOST, 'githubSha': os.getenv('GITHUB_SHA'), 'fatalErrors': [],
              'submission': {'outcome': 'not_attempted'}, 'pages': []}
    try:
        if (ROOT / 'CNAME').read_text(encoding='utf-8').strip() != HOST:
            raise ValueError('CNAME differs from approved corporate hostname')
        report['dnsAddresses'] = sorted({x[4][0] for x in socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM)})
        key_files = [p for p in ROOT.glob('*.txt') if re.fullmatch(r'[a-zA-Z0-9-]{8,128}\.txt', p.name)]
        if len(key_files) != 1:
            raise ValueError('Expected exactly one existing public IndexNow key file')
        key = key_files[0].read_text(encoding='utf-8').strip()
        if key != key_files[0].stem:
            raise ValueError('Repository key does not match filename')
        location = BASE + '/' + key_files[0].name
        status, final, _, body = get(location)
        report['keyFileVerified'] = status == 200 and final == location and body.strip() == key
        if not report['keyFileVerified']:
            raise ValueError('Live IndexNow key file missing, redirected or mismatched')
        status, final, _, robots_text = get(BASE + '/robots.txt')
        if status != 200 or final != BASE + '/robots.txt':
            raise ValueError('Cannot verify live robots.txt')
        robots = RobotFileParser()
        robots.parse(robots_text.splitlines())
        report['robotsText'] = robots_text
        status, final, _, sitemap = get(SITEMAP)
        if status != 200 or final != SITEMAP:
            raise ValueError('Live sitemap unavailable at its canonical HTTPS URL')
        urls = [n.text.strip() for n in ET.fromstring(sitemap).findall('.//{*}loc') if n.text]
        if not urls or len(urls) > 100 or len(urls) != len(set(urls)) or any(not safe_public_url(u) for u in urls):
            raise ValueError('Unsafe, duplicate, empty or oversized sitemap; refusing submission')
        repo_urls = {n.text.strip() for n in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc') if n.text}
        if set(urls) != repo_urls:
            raise ValueError('Live sitemap differs from reviewed production source; refusing stale/draft batch')
        report['sitemapUrls'] = urls
        with ThreadPoolExecutor(max_workers=4) as pool:
            report['pages'] = list(pool.map(lambda u: audit_page(u, robots), urls))
        eligible = [p['url'] for p in report['pages'] if p['eligibleForNotification']]
        report['eligibleCount'] = len(eligible)
        report['issueCount'] = sum(bool(p['issues']) for p in report['pages'])
        for row in report['pages']:
            print(json.dumps(row), flush=True)
        # User-agent probes do not prove how a real search crawler is treated.
        status, final, _, body = get(BASE + '/', 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)')
        report['bingUserAgentProbe'] = {'status': status, 'finalUrl': final,
                                       'identityPresent': 'MMeD Systems' in body,
                                       'actualBingCrawl': False}
        if args.submit:
            report['submission'] = submit(eligible, key, location)
        print('SUMMARY ' + json.dumps({k: report.get(k) for k in
              ('checkedAtUtc', 'eligibleCount', 'issueCount', 'keyFileVerified', 'submission')}), flush=True)
    except (OSError, ValueError, URLError, ET.ParseError) as exc:
        report['fatalErrors'].append(type(exc).__name__ + ': ' + str(exc)[:400])
        print('BLOCKED ' + report['fatalErrors'][-1], flush=True)
    finally:
        save(report)
    if report['fatalErrors'] or report.get('issueCount', 0):
        return 1
    if args.submit and report['submission'].get('httpStatus') not in (200, 202):
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
