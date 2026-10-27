# MMeD Systems — Private, clickable website staging (Free-plan preparation)

**Status:** Code and staging branch prepared; Cloudflare Pages project and Access policies must be configured and verified by the authorized Cloudflare account owner. No changes to the live site are required.

## Decisions locked for this workstream

- **Design:** Preserve the current live MMeD Systems website's fonts, spacing, colors, header, footer and page structure. No broad redesign.
- **Changes:** Improve page content section by section, in staging first, then wait for owner approval.
- **Where We Serve:** A forthcoming content change should remove the large homepage section and place the page primarily in the hamburger menu. Do this only after private staging is working.
- **Production:** `https://mmedsystems.com/` remains hosted by GitHub Pages from `main`.
- **Staging source:** The `staging` GitHub branch is a copy of `main` plus staging-only build/verification tooling.
- **Staging destination (proposed):** a NEW Cloudflare Pages project named `mmed-website-staging`. Do not use or modify `mmed-mycarepage-preview`, which belongs to a different application.
- **Authorization:** Only explicitly authorized reviewers may sign in. Do not use a bypass rule, Everyone rule, or permit public access.
- **Costs:** Start with Cloudflare's existing Free plan only, no paid services or subscription changes.

## Why setup is two-stage

Cloudflare Pages Git-connected sites and deployment preview URLs are **public by default**. Cloudflare's default `Enable access policy` for previews does not automatically cover the main `<project>.pages.dev` hostname. Neither `robots.txt` nor `noindex` makes an otherwise public URL private.

This repository deliberately **fails closed**: the build command publishes only a neutral placeholder until Access is proven to protect the primary Pages hostname.

## Cloudflare setup in the account owner's authenticated dashboard

1. Open https://dash.cloudflare.com/ and go to **Workers & Pages**.
2. Create a **new Pages project** named `mmed-website-staging`; select **Connect to Git** and the existing `admin-st2/mmedsystems-website` repository. Grant access to **only this repository** where available. Do not replace the existing public GitHub Pages project.
3. Choose **Production branch: `staging`**, *not* `main`. Set **Framework preset: None**, **Build command:** `python3 scripts/build_private_staging.py`; **Build output directory:** `dist-staging`. Use the directory appropriate for a static HTML site; no custom domain is required.
4. **Do not set `MMED_STAGING_MODE` yet.** The first deployment must display only `Private staging is not active`; the live MMeD site content should be absent. If full site content appears, STOP and disable deployment.
5. Disable automatic builds for *non-production preview branches* initially using the project **Settings > Builds > Branch control > Preview branch: None**. Keep only the dedicated `staging` branch building until every Access hostname is secured.
6. In the Pages project's **Settings > General**, select **Enable access policy** for preview deployments. Under Cloudflare **Zero Trust > Access > Applications**, confirm this is linked to the new Pages project. Configure the Allow rule to an **explicit authorized email only**, with no Bypass and no Everyone rule.
7. **Protect the primary project hostname** as well, using Cloudflare's officially documented sequence:
   - After enabling the initial Access policy, select **Manage** on the Pages application.
   - **Access > Applications > Configure**, open the **Public hostname** and remove the default `*` subdomain using Cloudflare's supported method, then Save (rename the application first if required).
   - Return to **Pages project > Settings > General > Enable access policy** again.
   - Confirm there are now **two appropriately restricted Access applications**, protecting `mmed-website-staging.pages.dev` **and** `*.mmed-website-staging.pages.dev`.
   - If your dashboard differs, follow Cloudflare's official Known Issues article below. Never delete the wildcard in an unsupported way or remove the last working policy.
8. In an **unauthorized incognito browser session**, verify that the primary URL, a nested path (`/where-we-serve/`), and a generated deployment-hash URL all require Access login or are denied. In the authorized account, verify sign-in works. Confirm preview URLs and branch aliases are not public.
9. Only after Step 8 passes, add Pages **production** environment variables:
   - `MMED_STAGING_MODE=private`
   - `MMED_STAGING_HOST=mmed-website-staging.pages.dev` (replace this value with the **actual hostname Cloudflare issued** if different).
   - Redeploy **only the staging project**. The build command itself anonymously probes four routes and **refuses to export the full website** if the primary Access login redirect cannot be verified.
10. Authorized tester opens the protected staging URL. Browse Home, Solutions, Private Clinics, Hospitals, Contact, Where We Serve, and Request a Demo. The staging version has a small fixed notice at the bottom; it otherwise reproduces the live site's existing HTML, CSS, and JavaScript.
11. Repeat incognito denial verification after each security or deployment configuration change. Keep main Pages staging address and hashed previews protected by their Access policies.

**Critical:** There is no ChatGPT Cloudflare dashboard connector authorized in the current conversation. This repository setup alone does *not* create an actual Pages project or Access policies. An authorized user must complete the Cloudflare dashboard portion, or use ChatGPT Work's cloud browser to complete it interactively. Do not paste access tokens or secrets in chat.

## What the staging build does (and does not do)

- `scripts/build_private_staging.py` is **staging-only**. Its default mode exports only a generic placeholder and `robots.txt` / `_headers`.
- The guarded private build exports public static HTML, images, CSS and JavaScript from the **live design's GitHub source** in the `staging` branch, preserving layouts and internal navigation.
- It excludes private source directories, `prototype`, CNAME, production sitemap, IndexNow verification key, operational code and GitHub configs.
- The staged copy gets `X-Robots-Tag: noindex` on **all** static URLs, a robots disallow directive, and an unmistakable staging notice.
- For safety, `mailto:` and outgoing links, including production service URLs, are blocked inside the staging copy; user-submitted forms are blocked. This is a **visual/navigation preview**, not an end-to-end test of live contact and payment flows.
- No real patient data should appear in the corporate staging environment. The clinical demo remains separate and untouched.

## How changes progress to the live site

1. Begin with the **live website source** on GitHub `main` and create a small, descriptive content feature branch.
2. Introduce only a requested page/section change. Stage the *same public HTML/CSS/JS changes* on `staging` for visual/interactive review.
3. Run static checks and manual desktop/mobile browser testing. Capture before/after screenshots.
4. Receive the owner's **explicit design/content approval**.
5. Prepare a clean pull request targeting `main` containing **only the approved website content changes** (not `scripts/build_private_staging.py`, staging environment settings or private deploy tooling).
6. When approved PR checks pass, merge to `main`, which continues deploying through GitHub Pages. Verify the live result; only then consider the change complete.
7. Rebase/sync `staging` from the latest live `main` after each release. Any staging-only setup files remain restricted to `staging`.

Avoid simply merging the entire `staging` branch into `main` because it contains staging infrastructure. Do not connect this Pages staging project directly to `main`.

## Verification commands

The independent GitHub Actions workflow `MMeD staging readiness — no production deploy` runs on pushes to `staging` and confirms safe defaults.

To test from a developer clone:
```
python3 -m unittest discover -s scripts -p test_private_staging.py -v
python3 scripts/build_private_staging.py
```
The default `dist-staging/index.html` must say **Private staging is not active**. A full copy is impossible via the documented Cloudflare deployment mode until the access gateway is verifiably enabled.

## Official Cloudflare documentation

- https://developers.cloudflare.com/pages/configuration/git-integration/
- https://developers.cloudflare.com/pages/configuration/branch-build-controls/
- https://developers.cloudflare.com/pages/configuration/preview-deployments/
- https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain
- https://developers.cloudflare.com/pages/configuration/headers/

## Activation acceptance

Do not mark staging ready until the owner has opened the *real* protected URL, tested desktop and mobile navigation, confirmed unauthorized access fails on the main and hashed preview hostnames, and confirmed no public DNS or live site changes.
