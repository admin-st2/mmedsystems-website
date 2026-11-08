# MMeD Systems public website

Static GitHub Pages site for https://mmedsystems.com/. White, navy and blue visual identity, Times New Roman throughout, with a single homepage "Request a Demo" button.

## Operational notes
- All content describes a platform in development; illustrated dashboard data are fictional.
- Demo-request email links prepare a prefilled draft to partnerships@mmedsystems.com. Visitors must send it through their email client; there is no website inquiry form or submission backend. Booking buttons link to separate Google Calendar appointment pages.
- The current /prototype/index.html is a noindex informational notice, not an interactive prototype or authentication gateway. The separate clinical demonstration is invitation-managed. Do not place real patient data in demonstrations without independently verified safeguards.
- The original full site is preserved on backup/pre-coming-soon-2026-10-10.
- The pre-launch Coming Soon page is preserved on backup/coming-soon-2026-10-11.
- Never change CNAME without confirming domain/DNS configuration.

## Files
- styles.css: entire responsive design system
- site.js: mobile navigation + email-composer request form
- Dedicated HTML pages for platform, solutions, security, integrations and audiences
- sitemap.xml and robots.txt

## Security review
- Proposed browser-header policy, test limits, and separately approved branch/hosting settings: [security hardening review](docs/security-hardening-review.md).
- Local checks: `python scripts/verify_security.py` and `python scripts/security_browser_check.py` (requires Playwright Chromium). These do not configure production headers.
