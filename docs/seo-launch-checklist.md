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

## DNS and HTTPS status — owner confirmation and remaining browser checks
**Owner-confirmed on 2026-10-11:** GitHub Pages reports DNS check successful, and **Enforce HTTPS** has passed / been enabled. Treat these GitHub Pages settings as user-confirmed. Public HTTP/TLS checks were attempted but could not be completed from this execution environment due to host access / DNS resolution limits; this is not evidence of a site outage.

The following items are historical configuration and remaining verification checks. Do not confuse site accessibility with a successful GitHub Pages workflow.

1. At the DNS provider, confirm apex (`@`) A records match **all four** GitHub Pages addresses:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
2. Confirm `www` CNAME points to `admin-st2.github.io`. Remove conflicting parking/forwarding records; preserve email MX, SPF, DKIM and DMARC records.
3. **Owner-confirmed complete:** In GitHub repository Settings → Pages, the custom-domain DNS check passed and **Enforce HTTPS** is enabled. Certificate trust and real-browser HTTPS behavior still require an independent smoke test.
4. Verify `https://mmedsystems.com/` loads and presents a trusted certificate. Verify `http://mmedsystems.com/`, `https://www.mmedsystems.com/` and `http://www.mmedsystems.com/` redirect to the canonical HTTPS site as expected.
5. Fetch `https://mmedsystems.com/robots.txt`, `/sitemap.xml`, `/platform/`, `/private-clinics/`, and `/request-demo/` and confirm correct content, no TLS warnings and HTTP 200 for canonical URLs.

## Changes in the SEO metadata pull request
- Search-intent-specific titles and unique meta descriptions on 22 core public pages.
- Matching Open Graph title and description tags, preserving existing canonical URLs.
- Added `WebPage` JSON-LD to these pages without making unsupported clinical or regulatory claims.
- Homepage lead copy explicitly references configurable EMR and healthcare management systems while preserving existing design and existing single main call to action.
- Existing Organization/WebSite structured data on the homepage is preserved.

## Google Search Console connection — check on 2026-10-11
- GSC Wizard plugin connected successfully, but `list_sites` returned **no registered properties** for the authenticated Google account.
- Attempt to register `sc-domain:mmedsystems.com` through GSC Wizard returned **site not found** in the connected Google Search Console account. This does not establish whether another Google account has a verified property.
- **Next owner action**: in https://search.google.com/search-console/, select **Add property → Domain**, enter `mmedsystems.com`, obtain the unique Google-issued TXT verification value, add it as an `@` TXT record in the DNS host, preserving existing MX/SPF/DKIM/DMARC and GitHub Pages records. Return to Google to click Verify. Do **not** guess or synthesize the token.
- After successful verification, retry GSC Wizard `add_site` for `sc-domain:mmedsystems.com`, activate property if needed, then submit `https://mmedsystems.com/sitemap.xml` and inspect key pages.
- Bing Webmaster Tools connection through GSC Wizard is not configured; Bing setup remains separate. Google sitemap submission and indexing are **not yet complete**.
- Attempts to independently fetch the public hostname and sitemap via web browsing were not successful in this environment, so real-browser/TLS smoke tests remain pending. This does **not** override the owner's report that GitHub Pages DNS and HTTPS checks passed.

## Search Console verified and first indexing inspection — 2026-10-12
- Domain property `sc-domain:mmedsystems.com` is now registered in GSC Wizard with `siteOwner` permission and activated.
- Google Search Console's URL Inspection API returned **URL is unknown to Google** for `https://mmedsystems.com/` (verdict NEUTRAL; no crawl date or Google canonical yet). This does not imply a crawling error: Google may not have discovered a new site.
- Search Console returned zero registered sitemaps for this property.
- An attempted submission of `https://mmedsystems.com/sitemap.xml` was **refused by GSC Wizard** because the Google OAuth connection currently grants read-only API scope (`webmasters.readonly`); ownership does not automatically grant the connector full OAuth scope. No submission occurred. To resolve: manually submit through Search Console → Sitemaps, or enable full GSC Wizard access at https://tool.gscwizard.com/account and retry.
- Search Console's AMP report shows **Processing data, please check again in a day or so**. It does not list an actual invalid AMP URL yet. The normal responsive MMEd site does not require AMP.
- Public HTTP access remains unverified from this execution environment; the owner's GitHub Pages DNS and HTTPS success remains noted above.

## After live browser smoke test and release acceptance
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
