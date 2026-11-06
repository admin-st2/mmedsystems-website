# MMeD Systems — Website Refresh & Pricing Concept

**Status: MOCKUPS ONLY / NOT APPROVED / NOT IMPLEMENTED**

This branch contains a **design-review generator**, mockup-only CSS/JavaScript, and a proposed Pricing page template. None of the concept code is part of the current website or the production GitHub Pages `main` branch. The `staging` deployment configuration remains locked and no private staging URL was activated.

## Existing site baseline

The custom site source in `admin-st2/mmedsystems-website` is the design authority:
- Main font: **Times New Roman**, Times, serif.
- Existing color tokens: `--navy:#0b1f3a`, `--navy-soft:#183955`, `--blue:#1267b2`, `--blue-deep:#0759a4`, `--body:#4f647b`, `--muted:#6b7e90`, `--line:#d9e3eb`, `--pale:#f6f9fc`, `--white:#fff`.
- Logo SVG and brand assets reused without edit.
- Existing Home, Solutions, About and Contact page architecture and copy retained in the source tree.
- Existing URLs and menu order retained. Concept adds only `Pricing` before Contact, and honors the previously requested hamburger-only `Where We Serve` placement.
- Current homepage's one main CTA preserved; a second `View Pricing` CTA is proposed in the *concept only*.

## Preview pages

Use the Actions artifact to compare baseline vs concept:
- Home — desktop and mobile before/after.
- Solutions (Services/Products) — desktop and mobile before/after.
- About — desktop and mobile before/after.
- Contact — desktop and mobile before/after.
- Pricing — new proposed page, desktop and mobile.

**18 PNG screenshots** total plus a side-by-side local HTML gallery. No mockups are uploaded to the live site or to an unprotected staging host.

## Proposed pricing — supplied values, not live offer

| Plan | Monthly per provider | Annual per provider | Best for |
|---|---:|---:|---|
| Solo | $149/mo | $1,490/yr | Solo practitioner |
| Practice | $249/mo | $2,490/yr | 2–10 providers |
| Clinic Network | $399/mo | $3,990/yr | Multi-provider, multi-location |
| Enterprise | Custom | Custom | Groups, networks, hospitals |

The annual figures equal ten monthly charges, correctly representing two months free for a 12-month period. Feature lists for all plans are **placeholder proposals** and must be separately approved. The mockup displays them as provisional.

Still to confirm before launch: onboarding setup fee, possible annual-fee waiver, add-on availability/pricing (AI notes, modules, extra licenses), 10+ provider discount percentage, contract terms, cancellation, migration scope, support hours/SLA, taxes and billing terms.

## Trust and compliance truthfulness

- No verified regulatory certification, official HIPAA badge, client logo, licensed testimonial, case study, ROI statistic, deployment count, or integration partner logo has been provided.
- The mockups deliberately show neutral evidence placeholders and an accurate HIPAA / BAA readiness disclaimer, not a fake certification badge. HIPAA-regulated deployments need appropriate security assessment, contracted terms and business associate agreements as applicable.
- The hero's device frame is **NOT** a fabricated MMeD screenshot. It says plainly that an approved real product capture using fictional patient data is required before launch.
- The product-tour mockup provides a conceptual location and interaction, but real demo captures or a real walkthrough/video still need confirmation and review.
- The contact form is a disabled visual layout concept; it does not collect or send any information. The existing public email inquiry workflow remains unchanged. Live chat/bot service is not enabled.

## Acceptance before production implementation

1. Owner approves before/after layout on both desktop and phone.
2. Obtain real fictional-data product screenshot or permissioned 60–90-second screen recording; redact all customer/PHI data.
3. Verify certifications and legal/compliance wording before any badges; collect written approval for any customer logos/testimonials/results.
4. Finalize plan feature lists, commercial fees, discounts, contracts and cancellation terms. Avoid publishing unapproved pricing as a firm commercial offer.
5. Establish private clickable staging on an Access-protected hosting account; Cloudflare Pages still needs authenticated dashboard setup and Access verification before activation.
6. Build only approved changes in an isolated `staging` feature branch, then test at mobile, tablet and desktop; verify keyboard navigation, contrast, labels, keyboard tour/pricing controls, reduced motion, and real contact-form backend.
7. Run browser tests for Chrome, Firefox, Safari/WebKit and Edge, audit performance, and preserve SEO canonical URLs.
8. One structured owner revision round; only then submit a PR to `main`, with explicit publishing approval.

## Reference treatment

Elation Health: spacing and clarity. Canvas Medical: clean product visualization. athenahealth: evidence placement and CTA hierarchy. Only layout concepts are inspired; brand colors, logo, fonts and original site structure are MMeD's own.

No external image assets, trademarked logos or patented product screenshots were copied.

## Rendering details

`python design-review/build_refresh_mockups.py` builds before/after copies in a temporary local directory and captures them with Chromium. The script does not update existing site files. The comparison gallery is written to `refresh-review/index.html`, with desktop 1440×900 and mobile 390×844 screenshots.
