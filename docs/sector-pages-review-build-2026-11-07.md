# MMeD Systems — 22-sector implementation handoff

Date: November 7, 2026. Status: **built and tested locally for owner review; not deployed and not merged into production**.

The owner approved executing the expanded 22-sector copy. The resulting static website source and clickable offline review have been delivered as conversation attachments. This document records the state for project continuity; **the generated page files are in the delivered source ZIP, not yet imported into this repository branch**.

## Review artifacts

- `MMeD-Sector-Website-Review.html` — 46-page standalone clickable review, beginning at Who We Serve. SHA256: `861068509a3a24941c96f6a070b503abb2bf00487c34a81bfd95b2b7d1f24731`.
- `MMeD-Sector-Website-Review-Package.zip` — source, structured approved copy, screenshots, QA results, route map and handover. SHA256: `b6e44766a968d5f55323d74f8a3a78377ad5bb88dbdfbdde808612779f3feca7`.
- `MMeD-Sector-Website-Source.zip` — source and handover only. SHA256: `d3ff79aad371d82e5b597d41816ee97d40c146109a2ace5b69aeb2db3a85de42`.

The interactive review is offline, not a hosted staging address. It disables email/external-service actions and submissions. The source is marked noindex and robots-disallowed until an explicitly approved production release.

## Built scope

The existing `/where-we-serve/` URL is retained but changed into a sector-only **Who We Serve** directory with six groups, 22 cards, category anchors and local filtering. Countries/regions are removed from that page. `/solutions/` remains a broad overview and links to the directory. Existing URLs are not removed. Four established sector URLs are reused and 18 new ones are added.

Each page contains the approved sector-specific copy, implementation approach, native-text workflow visual, expandable buyer question, related-sector links, Request a Demo and Request Itemized Pricing. There are no fixed-price tiers. The original FAQ illustration remains FAQ-only.

| Sector | Route |
|---|---|
| Primary Care and Independent Practices | /private-clinics/ |
| Urgent Care and Walk-In Clinics | /urgent-care/ |
| Specialty Medical Practices | /specialty-practices/ |
| Outpatient Surgery and Procedure Centers | /outpatient-surgery/ |
| Medical Centers and Multispecialty Facilities | /medical-centers/ |
| Hospitals and Acute Care Organizations | /hospitals/ |
| Rehabilitation and Allied Health Services | /rehabilitation/ |
| Nursing Homes and Long-Term Care Facilities | /long-term-care/ |
| Therapy and Counseling Practices | /therapy-counseling/ |
| Psychiatry and Medication-Management Practices | /psychiatry/ |
| Community Behavioral Health Organizations | /community-behavioral-health/ |
| Substance Use Treatment and Recovery Programs | /substance-use-treatment/ |
| Community Health Centers | /community-health/ |
| Home Health and Visiting Nursing Services | /home-health/ |
| Public Health and Outreach Programs | /public-health/ |
| Community and Retail Pharmacies | /community-pharmacies/ |
| Hospital and Health-System Pharmacies | /hospital-pharmacies/ |
| Clinical Laboratories | /clinical-laboratories/ |
| Imaging and Diagnostic Centers | /imaging-diagnostics/ |
| Multi-Site Groups and Care Networks | /care-networks/ |
| Billing and Revenue Cycle Teams | /billing-revenue-cycle/ |
| Procurement, Inventory, and Supply Chain Teams | /procurement-inventory/ |

## Illustration status

Every sector has a separately rendered SVG composition combining a relevant existing illustration with a sector-specific three-role map, plus a workflow visual matching its approved journey. Seven underlying artwork families are reused across related sectors; these are **not 22 independently drawn people scenes**. They are labeled concept artwork, not real customer installations or product screenshots. The reference artwork is user-provided in the conversation. No actual patient data is present.

## Tests actually completed

- 46 source pages: one H1, non-empty unique title, description, canonical, JSON-LD validity, all internal links and fragment targets. Zero broken internal targets found.
- 22 sector pages × 4 viewport widths (1440, 768, 390, 320px): **88 passing combinations** covering image load, horizontal overflow, CTA target size, accordion keyboard interaction and menu focus restoration.
- Directory search, no-results behavior, reset, sector navigation, itemized-pricing contact anchor, demo route, FAQ interaction and disabled external actions tested in the delivered offline wrapper at all four widths.
- Chromium only, using isolated offline HTML. No claim of full WCAG certification or cross-browser/hardware coverage. Safari/WebKit, Firefox, Edge and production hosting remain release checks.

## Preserved boundaries

Existing Times New Roman and exact brand palette retained; no main-branch merge, DNS modification, paid subscription, inbound-email access, data-store change, private-demo access or live clinical data use. The package is based on the reviewed v2 website, incorporating the earlier compact-spacing and navigation candidate plus FAQ/custom quotation wording.

## Next release gate

Owner reviews the clickable version. After approval, reconcile the delivered source with latest main into a dedicated implementation branch, update legacy tests that expect geography/26–27 pages, verify protected staging and cross-browser behavior, then obtain explicit publication approval. Only at release remove review noindex/robots restrictions and notify search engines of genuinely published URLs. Do not deploy the offline wrapper or import review-source files blindly over newer production changes.
