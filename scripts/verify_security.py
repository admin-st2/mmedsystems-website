#!/usr/bin/env python3
"""Dependency-free source checks for the public website's security review."""
from html.parser import HTMLParser
from pathlib import Path
import re
from security_policy import candidate_headers

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'actions/checkout': '11d5960a326750d5838078e36cf38b85af677262',
    'actions/setup-python': 'a26af69be951a213d495a4c3e4e4022e16d87065',
    'actions/upload-artifact': 'ea165f8d65b6e75b540449e92b4886f43607fa02',
}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if any(name.startswith('on') for name in attrs):
            self.errors.append('Inline event handler requires security review')
        if tag in ('form', 'iframe', 'object', 'embed'):
            self.errors.append('New data-entry or embedded service requires privacy/CSP review')
        if tag == 'script' and attrs.get('src', '').startswith(('https:', 'http:', '//')):
            self.errors.append('External script requires security/privacy review')
        if tag == 'a' and attrs.get('target') == '_blank':
            if not {'noopener', 'noreferrer'} <= set(attrs.get('rel', '').split()):
                self.errors.append('New-tab link missing noopener noreferrer')


def main():
    errors = []
    uses = 0
    for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
        text = path.read_text()
        for action, ref in re.findall(r'uses:\s*([^\s@]+)@([^\s#]+)', text):
            uses += 1
            if not re.fullmatch(r'[0-9a-f]{40}', ref) or PINS.get(action) != ref:
                errors.append(f'{path.name}: unreviewed action {action}@{ref}')
        for step in re.split(r'(?m)^      - ', text)[1:]:
            if 'uses: actions/checkout@' in step and 'persist-credentials: false' not in step:
                errors.append(f'{path.name}: checkout retains credentials')
    workflow = (ROOT / '.github/workflows/website-checks.yml').read_text()
    pr = workflow.split('  pull_request:\n', 1)[1].split('  push:\n', 1)[0]
    if 'paths' in pr or 'types:' in pr:
        errors.append('Required corporate checks must run on every main-targeting PR')
    for path in sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('*/index.html')):
        parser = Page()
        parser.feed(path.read_text())
        errors.extend(f'{path.relative_to(ROOT)}: {err}' for err in parser.errors)
    privacy = (ROOT / 'privacy/index.html').read_text()
    for required in ('Google Calendar', 'https://policies.google.com/privacy',
                     'GitHub Pages', 'email application', 'patient information',
                     'no inquiry submission form'):
        # Match the intentional sentence rather than generic substrings elsewhere.
        if required == 'no inquiry submission form':
            required = 'does not have an inquiry submission form'
        if required not in privacy:
            errors.append(f'Privacy notice missing {required}')
    if 'demo inquiry form' in privacy or 'The demo form prepares' in privacy:
        errors.append('Privacy notice still describes a removed form')
    policy = candidate_headers()['Content-Security-Policy']
    script_policy = next(d for d in policy.split('; ') if d.startswith('script-src '))
    if "'unsafe-inline'" in script_policy or "'unsafe-eval'" in script_policy:
        errors.append('Candidate policy permits unsafe JavaScript')
    for error in errors:
        print('FAIL:', error)
    if errors:
        return 1
    print(f'PASS: {uses} action references pinned, checkout credentials disabled, unconditional main PR checks, privacy routes and candidate CSP source checks.')
    print('This is source validation only; no production headers or branch rules were activated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
