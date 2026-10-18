# MMeD Systems | Organic search and qualified inquiries

Baseline review: 2026-10-18. Public website: https://mmedsystems.com/. Clinical demo remains separate at its invitation-only domain; this project contains no clinical access controls or patient data.

## Verified baseline (Google Search Console)
- Connected property: sc-domain:mmedsystems.com.
- Last 28 days of settled Google Search data: 4 clicks and 9 impressions. Query-level evidence is too sparse to treat these as reliable rankings for nonbranded healthcare terms.
- Indexing tracker: 5 of 25 canonical public pages indexed as of the October 18 check; remaining 20 were not indexed at that snapshot. Snapshot is not necessarily the latest live status of individual pages.
- Sitemap: valid/reachable but Search Console API reports processing/pending since October 12. Do not repeatedly submit an unchanged sitemap in the same day.
- IndexNow: root key verified, 25 canonical public URLs submitted and accepted (HTTP 202 means key validation pending; not proof of indexing).
- Bing Webmaster Tools API is not connected to the GSC Wizard account. Verify the property directly at Bing Webmaster Tools or import from the verified Google Search Console property; add the API connection for reporting.
- Google Analytics scope is not connected within the info@mmedsystems.com GSC Wizard account. A GA4 property may exist elsewhere; do not claim website traffic is absent.

## Changes in this release
- The single homepage primary CTA points to /request-demo/, not directly to a mailto URL.
- /request-demo/ explains how an introduction works, collects relevant screening information through a prepared email, and makes its limitations explicit: no direct form submission and no automatic demo access.
- Demonstration access stays invitation-only and NDA-governed, never linked directly from the corporate CTA. Do not place PHI in public inquiries.
- Contextual links reinforce site architecture for hospital information systems, healthcare integrations, pharmacy/laboratory operations, clinic management and business operations.
- Update sitemap lastmod values only on pages substantively changed on October 18; preserve unchanged page dates.

## Next operational decisions (not implemented here)
1. Verify Bing Webmaster Tools import/ownership, submit sitemap there, and connect its API key to GSC Wizard if desired. Search engine submission does not guarantee indexing.
2. Verify which account owns GA4 and establish a privacy-reviewed conversion event plan before installing tags or tracking users. Baseline: demo CTA clicks and confirmed inquiries per month.
3. For automatic inquiry capture, choose and secure a backend (e.g., serverless API with spam controls, server-side secrets, rate limits, consent/privacy requirements, monitoring). Static GitHub Pages cannot securely call Resend with a secret from browser JavaScript. Do not present the existing mailto flow as a submitted form.
4. Publish factual, distinctive detail about U.S. and international workflows: EMR documentation, billing and coding, pharmacy, laboratory, interoperability, and country configuration. Avoid unsupported deployment or regulatory-certification claims.
5. Track Google indexed URLs, relevant nonbrand impressions, qualified partnership inquiries, demo invites accepted, and conversions by origin every 28 days. Do not assume a low-traffic site improves immediately after publishing.

## Release acceptance
- Pull request automation: static SEO/link/privacy contract + public live HTTPS routing + desktop/mobile Chromium smoke checks.
- Post-merge: verify new homepage CTA and /request-demo/ with real Chromium after live deployment and compare live sitemap timestamps.
- Demo subdomain, DNS, MX/SPF/DKIM/DMARC, and confidential repositories remain untouched.
