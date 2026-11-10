# MMeD corporate website — staged content TLC (Nov 6, 2026)

**This is a review candidate, NOT a live redesign.**

## Design lock

No edits to `mmed-v6.css`, the corporate logo, footer structure, icon assets, Times New Roman typography, navy/white/blue palette, homepage section order (except removing the unrequested regional promo block), or private clinical demo.

## Direct owner feedback addressed

- Remove the large `Where We Serve` region promo from the homepage, restoring the shorter original homepage.
- Place the destination in the existing **hamburger navigation** (primary menu list) rather than adding it to the desktop header or footer.
- Rebuild the `Where We Serve` page using the exact existing interior-site component classes: `solution-hero`, `solution-statement`, `solution-workflows` and `solution-connect`; no bespoke card-grid style or new CSS.
- Keep international context truthful: United States, Uganda and East Africa, wider Africa, other locations. Market interest does not establish offices, installed clients, certifications, or local availability.

## Content specificity refined inside existing sections

- Homepage: clearer EMR/EHR, documentation, lab/pharmacy, billing and reporting language; realistic, useful demo-inquiry next step.
- Platform: more meaningful description of an encounter-to-operations workflow.
- Private clinics and medical centers: first paragraph now ties the offering to particular departmental responsibilities and daily processes.
- Resources: contact callout speaks to EMR evaluation rather than a vague newsletter.

## Preserved

- Single homepage Request a Demo CTA leading to the public request page.
- Existing public site hosting and production `main` branch unchanged.
- Existing `mmedsystems.com` copy and global design system.
- Staged secure lead capture PR #11 remains **disabled**, never published.
- No production healthcare credentials, clinical demo changes, new paid services or outgoing email.

## Owner review

Inspect the desktop/mobile screenshot gallery attached to the pull request. Mark sections needing further correction. Do **not** merge into the production `main` branch without explicit approval.

The private clickable Cloudflare Pages staging address is a separate pending setup: the `staging` branch is ready, but its guarded build publishes only a placeholder until Cloudflare Access verifies the primary and preview hostnames. No private staging URL should be claimed ready without an authenticated deployment check.

## Technical acceptance

- Sitemap remains 26 HTTPS canonical public pages, with lastmod updated only for changed content.
- Every indexable page retains one `Where We Serve` link in the hamburger menu and none in the desktop nav/footer.
- Homepage does not contain the region teaser block.
- Regional page stays in the existing site layout.
- Static SEO/link/access checks, staging fail-closed checks, and Chromium screenshot jobs should all be green.
