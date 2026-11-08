#!/usr/bin/env python3
"""Build a candidate policy for local review. Does not configure GitHub Pages."""
from base64 import b64encode
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


class InlineScripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and not dict(attrs).get('src'):
            self.current = ''

    def handle_data(self, data):
        if self.current is not None:
            self.current += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.blocks.append(self.current)
            self.current = None


def candidate_headers():
    # Hash the current source bytes, including legacy redirects and JSON-LD.
    # These hashes authorize code; they do not establish that the code is safe.
    # Regenerate and review them after any inline-script change before activation.
    hashes = set()
    for path in sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('*/index.html')):
        parser = InlineScripts()
        parser.feed(path.read_text(encoding='utf-8'))
        for block in parser.blocks:
            digest = b64encode(sha256(block.encode('utf-8')).digest()).decode('ascii')
            hashes.add("'sha256-" + digest + "'")
    policy = '; '.join([
        "default-src 'none'",
        "script-src 'self' " + ' '.join(sorted(hashes)),
        # Existing static style attributes and the prototype notice's style block.
        # This allowance is for CSS only, never executable inline JavaScript.
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'none'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "frame-src 'none'",
        "frame-ancestors 'none'",
    ])
    return {
        'Content-Security-Policy': policy,
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    }


if __name__ == '__main__':
    print(json.dumps(candidate_headers(), indent=2))
