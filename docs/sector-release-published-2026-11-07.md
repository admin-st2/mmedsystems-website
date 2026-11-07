# MMeD Systems — Sector website published

Status: **LIVE AND VERIFIED**, November 7, 2026.

## Production source of truth

- Public website: https://mmedsystems.com/
- Approved release PR: https://github.com/admin-st2/mmedsystems-website/pull/25
- Production merge commit: `167b932f562c8cd66c08a3814d72f5dbc0d675bb`.
- Previous production / rollback reference: `521d6a0c3d2dde978e3fa29954b3c97f9c8bcc6a`.
- GitHub Pages build and deploy: https://github.com/admin-st2/mmedsystems-website/actions/runs/42423656887 — succeeded.
- Actual public HTTP verification: https://github.com/admin-st2/mmedsystems-website/actions/runs/42423656877 — succeeded, completed at approximately 23:06 UTC / 6:06 PM Eastern.

## Published content

- Searchable, sector-only **Who We Serve** directory at `/where-we-serve/`, with 22 dedicated sector pages and no country list in that directory.
- Sector-specific copy, illustrations, workflow examples, buyer questions and related-sector links.
- Custom organization-specific pricing at `/pricing/`, with Request Itemized Pricing links to `/contact/#pricing-inquiries`; no fixed per-provider tier prices.
- Original connected-care illustration on `/faq/` only. Dedicated sector conceptual artwork remains on sector pages.
- Reviewed compact spacing, improved navigation, existing font family, exact brand palette and logo retained.
- Newly added production `/book/` page and approved Google Calendar meeting destinations preserved. No appointments were booked and no inquiry emails were sent during testing.
- 47 public canonical pages in the sitemap, including existing routes and booking. No existing sitemap URL was removed.
- Review-only noindex/robots restrictions removed from approved public pages; error-page noindex retained. Private clinical demo is unchanged.

## Verification evidence

The approved source import and 3-engine browser QA passed before merge: https://github.com/admin-st2/mmedsystems-website/actions/runs/42422903042.
- 168 browser/route/viewport checks: 120 Chromium, 24 Firefox, 24 WebKit.
- Chromium: all 22 sectors at 1440, 768, 390 and 320px plus core journeys.
- Firefox and WebKit: representative sectors and core journeys at desktop and phone widths.
- No browser script errors or horizontal overflow in tested views. Verified directory search, no-results/reset, image loading, native accordion keyboard use, menu focus restoration, contact pricing anchors and preserved booking links.
- This is engine-level automated testing, not a claim of exhaustive device testing or WCAG certification.

Final source checks also passed after temporary import tooling was removed:
- Corporate source/browser checks: run 42423372132.
- Firefox/WebKit release checks: run 42423372143.
- FAQ responsive/accessibility interaction checks: run 42423372113.

After deployment, the GitHub-hosted verifier fetched the real public website:
- **47/47 pages** returned HTTP 200 at their correct canonical addresses with the exact release marker.
- **30/30 referenced assets** returned successfully, including sector artwork and FAQ image.
- No public noindex barrier; robots allowed the checked search crawlers.
- Existing IndexNow key verified.
- One batch of **47 published URLs** submitted to `https://api.indexnow.org/indexnow` at 23:06:37 UTC; **HTTP 200 received**. This acknowledges receipt, not completed indexing or ranking.
- Artifact `mmed-live-release-42423656877` contains the per-page, per-asset results and receipt (90-day retention).

## Preserved boundaries and next-work caution

No DNS, MX/SPF/DKIM/DMARC, clinical demo, Supabase database, paid subscription, account permission or inbound-email changes were made. The live website is the reviewed source plus the previously approved booking integration—not the obsolete fixed-price mockup.

Future website work must branch from current `main`, not blindly merge older TLC/spacing/UX review branches or the old fixed-price concept. This staging document updates project continuity; older staging page files do not supersede the published main source.
