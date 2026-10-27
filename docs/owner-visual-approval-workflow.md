# MMeD corporate website — owner visual review before publication

The purpose of this workflow is to let the owner evaluate how proposed website changes **look** on a desktop and mobile device **before** any change is published to the live corporate site.

## Non-negotiable release policy

**Do not merge a design or substantive content pull request into `main` until the owner has explicitly approved the visual preview.** A passing test suite is necessary, but not a substitute for visual approval.

The `main` branch publishes to the live GitHub Pages site. Opening a pull request and generating visual previews does **not** publish the PR's changes.

## Owner preview instructions

1. Make the change in a separate GitHub branch and open a pull request against `main`.
2. Wait for the `MMeD corporate site checks` run to finish on that PR. Its `visual-review` job generates desktop (1440px) and mobile (390px) full-page screenshots from the proposed HTML/CSS/JS **on a local server**.
3. Open the PR's **Checks** tab and choose the successful workflow run. At the bottom of the run page, under **Artifacts**, download `mmed-visual-preview-pr-<number>`. On mobile, GitHub's web browser interface may be easier than its app.
4. Unzip the downloaded artifact and open `index.html` for a gallery of all screenshots. Open an image for detailed zoom.
5. Give comments on typography, spacing, layout, links, information hierarchy, international coverage and responsiveness. Revise the pull request and regenerate screenshots as needed.
6. Only after explicit owner approval and green automated checks, merge the PR to trigger GitHub Pages deployment.
7. Independently check the live homepage and affected pages after deployment.

## Screenshots included

- Homepage
- Where We Serve
- Solutions
- Private Clinics
- Hospitals
- Resources
- Request a Demo

Each page has desktop and mobile screenshots, for 14 full-page images. These are **source-based screenshots**, not a substitute for functional browser, accessibility or mobile-device testing. They are not interactive preview links. Artifacts expire after 14 days; regenerate on a new PR revision as required.

## Site security and scope

- Uses only public corporate source files and headless Chromium in GitHub Actions; screenshots are rendered against `127.0.0.1`, not any private clinical domain.
- Does not access medical records, Supabase, contact inboxes, provider demos, secrets, or passwords.
- Does not install third-party preview hosting, add DNS, create paid accounts or grant new permissions.
- Current publication of `main` remains unchanged until the owner authorizes a future merge.

## Optional later enhancement

A fully clickable, access-protected **staging website** on a separate non-production domain would allow testing menus, forms and responsiveness in the browser. Do not set up or expose a public staging domain without an explicit access-control, ownership and cost review. GitHub Actions screenshots are the initial zero-subscription-cost visual review method.
