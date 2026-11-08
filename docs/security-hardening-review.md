# Security and privacy changes for owner review

Prepared 8 November 2026 against main `b70611fc794eb94610004b3514197ef94691be06`.
Reconciled with main `5a76d7c45042a2a70257618cbbf46ef2b13e0bc4` before approved publication,
preserving the homepage approach links and Urgent Care workflow disclosures. The two
new workflows receive the same reviewed action pins, for 27 references total.
Branch protection, CDN/DNS configuration and production browser headers remain separate
approval decisions; merging the code publishes the revised privacy notice.

## Code changes

- Pin all 27 GitHub Actions references to exact official same-major release commits.
  Disable persisted checkout credentials in the three steps that previously lacked it.
- Run the existing corporate `static-site` and `browser-smoke` jobs on every PR to
  `main`, including workflow-only and documentation-only changes. Keep the other
  workflows and job identities. Production DNS/HTTPS checks still run on main pushes,
  the existing schedule, and manual runs; they do not gate unpublished PR source.
- Add source checks and local candidate-header browser tests to the corporate workflow.
- Correct the privacy notice to describe email links, separate Google Calendar booking
  pages, and GitHub Pages hosting. There is no inquiry form, submission endpoint, or
  embedded calendar in the current website. No booking, email, or personal data was
  submitted during this review.

### Verified action identities

| Action | Pinned commit | Official release |
| --- | --- | --- |
| actions/checkout | `11d5960a326750d5838078e36cf38b85af677262` | [v4.4.0](https://github.com/actions/checkout/releases/tag/v4.4.0) |
| actions/setup-python | `a26af69be951a213d495a4c3e4e4022e16d87065` | [v5.6.0](https://github.com/actions/setup-python/releases/tag/v5.6.0) |
| actions/upload-artifact | `ea165f8d65b6e75b540449e92b4886f43607fa02` | [v4.6.2](https://github.com/actions/upload-artifact/releases/tag/v4.6.2) |

Official exact tags, commit signatures, and action.yml identities were checked.
All three retain the Node 20 runtime and support the inputs used here. Pinning prevents
a mutable release tag from silently changing the action; it does not prove all
transitive dependencies or future behavior safe. Future upgrades require a reviewed
SHA update in the workflows and the check's allowlist.

## Separately approve: main branch protection

Apply only after the revised PR workflow has produced successful runs and the owner
approves the exact settings. A ruleset for `main` should use:

1. Require a pull request; required approvals **0** while there is only one maintainer.
2. Require checks **static-site** and **browser-smoke**, from the **GitHub Actions** app.
   Require the branch to be up to date before merging.
3. Require conversation resolution. Block force pushes and branch deletion.
4. No bypass actors. With classic branch protection, enable **Do not allow bypassing
   the above settings** so administrator pushes are covered too.
5. Leave code-owner approval and approval of the most recent push OFF for now. The
   sole listed owner cannot approve their own PR. CODEOWNERS remains an ownership
   signal, not a claim of independent review.
6. Do not enable **Restrict updates** with an empty bypass list; that can block all merges.
   When a second trusted maintainer is added, separately approve one independent review
   and suitable CODEOWNERS coverage.

Do not require path-filtered `faq-check`, `pricing-preview`, or `sector-source-check`
until they are made unconditional. Do not require push-only publication jobs.
Never solve a failed check by enabling a blanket admin bypass. A rule change or an
emergency exception needs separate owner approval. This is not equivalent to two-person
review while the project has one maintainer.

Sources: [ruleset options](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
[self-review restriction](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews),
[administrator enforcement](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[required check pitfalls](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## Separately approve: hosting and response headers

The current deployment is GitHub Pages. At review time the live homepage bytes matched
main exactly; sampled response headers did not include CSP, X-Frame-Options,
X-Content-Type-Options, Referrer-Policy, or Permissions-Policy. These are observations,
not proof of a vulnerability or an assessment of the private clinical application.

GitHub staff state that Pages does not offer custom HTTP response headers
([Pages discussion](https://github.com/orgs/community/discussions/54257)). A repository
`_headers` file is not a supported Pages header configuration. A CSP meta element cannot
set `frame-ancestors` or provide report-only deployment, and X-Frame-Options cannot be
set by a meta tag. No misleading `_headers` file or meta framing rule is added here.
See [CSP delivery limits](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
and [frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).

`scripts/security_policy.py` builds a **candidate** HTTP header set for the exact reviewed
source. It is used only by the local test server:

- CSP defaults to no resource loads. Same-origin scripts, styles, images and fonts are
  allowed; the current inline redirect scripts and JSON-LD have exact SHA-256 hashes.
- Inline CSS remains allowed because the current pages use style attributes. Inline
  JavaScript and eval remain prohibited except for the exact hashes above.
- No fetch/XHR connections, embedded frames, objects, form submissions, or base URL
  overrides. `frame-ancestors 'none'` and `X-Frame-Options: DENY` prevent embedding.
- `X-Content-Type-Options: nosniff`; `Referrer-Policy: no-referrer`;
  `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- Ordinary outbound email and Google Calendar links are navigation, not fetch/frame
  resources; they do not require widening the resource allowlist.

Before any activation: select an approved header-capable hosting/proxy arrangement,
review costs and DNS consequences, regenerate the hashes from the exact deployed
bytes, test every route plus redirects/errors in Chromium, Firefox and WebKit, and
review the required header-size limits. Stage CSP as report-only first where supported;
any external reporting endpoint and data it receives need separate approval. Test
framing protection and booking journeys in that deployment, then enforce only after
approval. No new provider, proxy, reporting endpoint, or paid service is selected here.
HSTS includeSubDomains/preload is deliberately not proposed without a subdomain audit.

## Privacy review limits

The updated description is based on the current source and official provider
information, including [Google Calendar appointment schedules](https://support.google.com/calendar/answer/11608416)
and [GitHub Pages IP logging](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection).
No email, calendar account, analytics account, or private demo was accessed.

The existing statements about operational use, not selling inquiry data, retention,
and handling access/correction/deletion requests remain unchanged. They are business
practices the owner must confirm before publication; a source review cannot verify
retention periods, service contracts, legal bases, international transfers, or actual
request handling. No new retention deadline, compliance certification, jurisdictional
claim, or third-party contract term has been invented. This is a draft, not legal advice.

## Reproduction and verification boundaries

Run `python scripts/verify_site.py`, `python scripts/verify_security.py`, and
`python -m py_compile scripts/*.py`. With Playwright 1.57.0 and browsers installed, run
`python scripts/browser_smoke.py`, `python scripts/faq_browser_check.py`,
`python scripts/pricing_cta_update.py --browser`, and
`python scripts/security_browser_check.py`. The last command writes candidate headers,
route results and privacy screenshots to ignored `security-review/`.

The local header test checks the 47 canonical pages, 404 and prototype notice,
legacy redirects, privacy layout at 320/785/1440 pixels, normal CSP violations,
unapproved inline script blocking, and framing denial. It never submits an inquiry
or booking. Local response-header enforcement proves only the fixture behavior;
it does not establish production enforcement or replace deployment testing.

### Results in the preparation environment

- PASS: 47-page/22-sector release source validation, all 27 action references and
  checkout credential settings, privacy/source checks, pricing/header regression
  source check, Python compilation, workflow YAML parsing, and whitespace checks.
- PASS: independent source review after addressing redirect and framing test weaknesses.
- NOT COMPLETED: browser execution and visual review. Playwright's official Chromium
  download returned gateway HTTP 400; the installed Chromium exited with
  `socket() failed: Operation not permitted`, including the permitted escalated attempt.
  No successful CSP or browser result is claimed. Firefox/WebKit were not run.
- PENDING: GitHub CI for the owner-authorized public draft PR. Merge/publication,
  branch rules, hosting configuration and header activation remain separate decisions.
