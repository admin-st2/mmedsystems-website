# MMeD Systems — GitHub Pages launch and SEO acceptance checklist

Snapshot: 2026-10-11. Canonical site: https://mmedsystems.com/. Repository: admin-st2/mmedsystems-website.

## Verified in GitHub
- Public repository, default branch main.
- CNAME file contains `mmedsystems.com`.
- Latest observed Pages build and deployment run (38170689803) succeeded for main commit `e16be07e503588879ceef70690a3e9c4dafc3171`.
- `robots.txt` allows crawling and points at `https://mmedsystems.com/sitemap.xml`.
- `sitemap.xml` contains 25 canonical HTTPS page URLs, excluding /prototype/.
- Public site pages already use self-referencing canonical tags. Old `.html` aliases are tagged noindex and point to clean paths.
- `/prototype/index.html` has noindex metadata and is not in the sitemap. It is **not** protected by authentication; do not use real patient data.

## DNS, HTTPS and GitHub Pages — blocking external checks
These were **not** independently confirmed via the public site as of the snapshot. Do not treat a successful Pages workflow as proof the custom hostname works.

1. At the DNS provider, confirm apex (`@`) A records match **all four** GitHub Pages addresses:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
2. Confirm `www` CNAME points to `admin-st2.github.io`. Remove conflicting parking/forwarding records; preserve email MX, SPF, DKIM and DMARC records.
3. In GitHub repository Settings → Pages, confirm custom domain `mmedsystems.com`, successful DNS check, certificate issuance and selected **Enforce HTTPS** option. GitHub notes HTTPS availability can take up to 24 hours.
4. Verify `https://mmedsystems.com/` loads and presents a trusted certificate. Verify `http://mmedsystems.com/`, `https://www.mmedsystems.com/` and `http://www.mmedsystems.com/` redirect to the canonical HTTPS site as expected.
5. Fetch `https://mmedsystems.com/robots.txt`, `/sitemap.xml`, `/platform/`, `/private-clinics/`, and `/request-demo/` and confirm correct content, no TLS warnings and HTTP 200 for canonical URLs.

## Changes in the SEO metadata pull request
- Search-intent-specific titles and unique meta descriptions on 22 core public pages.
- Matching Open Graph title and description tags, preserving existing canonical URLs.
- Added `WebPage` JSON-LD to these pages without making unsupported clinical or regulatory claims.
- Homepage lead copy explicitly references configurable EMR and healthcare management systems while preserving existing design and existing single main call to action.
- Existing Organization/WebSite structured data on the homepage is preserved.

## After HTTPS and release acceptance
- Validate the final served HTML titles, meta descriptions, canonical URLs and JSON-LD on desktop and mobile.
- Verify domain ownership in Google Search Console (domain property recommended) and submit `https://mmedsystems.com/sitemap.xml`. Use URL Inspection for key pages.
- Set up Bing Webmaster Tools and submit the sitemap.
- Confirm indexing/coverage status, crawling and page experience after search engines visit; indexing is not guaranteed or immediate.
- Consider a 1200 × 630 branded PNG/JPG Open Graph image for social sharing (not included in this metadata-only pull request).
- Publish genuine case studies, useful provider research and technical product detail as they become available; don't imply existing deployments or certifications.
- Review privacy/security copy and the email-composer demo request flow before broader promotion.
- Do not merge/deploy SEO PR until owner review if production deployment is gated.

Useful docs:
- GitHub Pages custom domains: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
- Google Search sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
