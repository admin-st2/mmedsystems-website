# MMEd website UX review — Buttons & Navigation
Date: 2026-11-06
Status: **Review only; do not merge into live main or staging without owner approval.**

## What is unchanged
- The existing MMeD brand palette, Times New Roman typography, header/menu structure, logo, page hierarchy and menu order.
- URL paths and existing mailto destinations. No paid service, contact backend, or clinical demo changes.
- The compact spacing refinement from PR #20, which is still awaiting owner approval.
- Where We Serve remains in the hamburger menu, not the desktop header or homepage.

## Improvements in this review branch
- An expanded menu clearly switches its visible control label from **Menu** to **Close**, and back on exit.
- Escape closes the menu and returns keyboard focus to the menu control; links in the menu are reachable through Tab, and focus leaving the non-modal menu closes it.
- The page currently being viewed is identified with an active menu state and `aria-current="page"`, including deep solution pages.
- Clearer hover/focus states and 44–48px tap targets for menu items, service CTAs and inquiry buttons. Colors remain within the established design palette.
- Email-oriented buttons that previously said **Discuss your needs** or **Start a conversation** now read **Email about your needs** and **Email our team**, accurately signaling that they open the visitor's email client; URLs and meanings are otherwise unchanged.

## What comes next
- Run browser tests for open/close with mouse and touch, Esc, keyboard focus, current page, inquiry link labels and overflow at 320/390/768/1440px.
- Review screenshots for desktop, tablet, mobile and small phones. One owner revision round before release.
- Don't claim Cloudflare private staging is active; it still requires the authorized account owner to enable and verify Cloudflare Access.
- Once approved, prepare the content-safe path through staging toward production, preserving existing URLs and testing cache-busted CSS/JS loading.

## Limitations
This changes interaction consistency and clarity, not the entire website UX. The site's request-demo email-composer fallback remains in place until the independently staged and security-reviewed lead form is activated with consent. No unverified HIPAA badges, price plans or product screenshots are introduced.

## Additional verified defect fixed

At desktop widths, the existing `.menu-primary` group was hidden in the hamburger panel (CSS `display:none`), which made the only hamburger-only **Where We Serve** destination unreachable from desktop navigation. The review corrects the visibility of that existing group at every viewport while preserving its original link order and content. Chromium tests now verify the real desktop and mobile menu route, focus management, and no narrow-screen overflow.
