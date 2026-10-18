# MMeD website lead capture — staged deployment checklist (October 18, 2026)

This branch prepares a safer, professional inquiry intake for the **public corporate** website. It is **disabled by default**; the existing mailto inquiry continues working. Do not deploy the Edge Function, migrate a database, enable browser form settings, or claim a working automatic form until all steps below pass.

## Environment isolation

The accessible Supabase account currently lists **ProjectPulse** and **E-Onus**, but no confirmed dedicated MMeD project. Do **not** insert corporate inquiries into unrelated projects. Confirm which Supabase organization owns the dedicated MMeD project, or select the organization for a new dedicated project and confirm any projected costs.

Store no patient records or PHI. Data collected is professional name/email, role, facility/organization, location and time zone, care/operations interests, timeline, and optional non-sensitive notes.

## Setup

1. Using the dedicated MMeD Supabase project, run `supabase migration new website_inquiries` in the project's local Supabase CLI workspace. Copy `deployment/website-inquiries-schema.sql` into the generated migration, apply to a **non-production test environment** first, and run security advisors. Public `anon` and `authenticated` roles have **no table access**; the server's service role exclusively writes and reads submitted leads. Avoid adding a broad policy or exposing the service role to the browser.
2. Register a Cloudflare Turnstile widget with hostname **mmedsystems.com** (and separate test hostname/widget, if needed); use a **new** site key for the business inquiry form. Turnstile must be verified server-side, including hostname and action `website_lead`. Tokens are single-use and expire after five minutes.
3. Verify `mmedsystems.com` sending is still enabled in Resend. Create a **domain-scoped sending** API key through the provider, with sender `MMeD Website <marketing@mmedsystems.com>`. Keep existing company email MX records unchanged. The only notification recipient in the server code is **partnerships@mmedsystems.com**. Never paste a real API key into GitHub or chat.
4. Store secrets in the *dedicated MMeD Supabase project's* Functions secret manager: `RESEND_API_KEY`, `TURNSTILE_SECRET_KEY`, `LEAD_HASH_SECRET` (cryptographically random, not public). Supabase-managed `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` should be available to the Edge Function. The service role secret must never be published to visitors. The public `website-leads-config.js` must contain **only** the Supabase function URL and **public** Turnstile site key.
5. Deploy the `supabase/functions/website-lead/index.ts` Edge Function with **JWT verification disabled for this function only**, since the endpoint is publicly called. It still enforces exact CORS origin, server-side Turnstile, validation, throttling, and server-only DB access. Before activation, use a managed gateway/WAF rate limit as an additional defense: the IP-based counter is best-effort and proxies affect its reliability.
6. Update the corporate website privacy policy **before** enabling automatic form submissions. Disclose the types of B2B contact data collected, purpose, processors (Supabase, Resend and Turnstile), retention/deletion process, and how privacy requests work. Obtain legal review where appropriate for jurisdictions targeted. Do not claim HIPAA or international data compliance certification.
7. Decide and implement a **90-day unqualified-lead retention and deletion procedure** and a daily alert for `notification_status = 'failed'`. Stored leads are not lost when email delivery fails, but the user sees receipt; failed notifications therefore need a reliable human-checked operational queue. Do not rely on console logs alone.
8. Run tests against a **test project** with test service keys, Resend sandbox and test Turnstile widget. Verify valid, invalid, expired/replayed captcha, input validation, duplicate/rate-limited, email failure, success, and privacy-deletion workflows. Use dummy B2B contact data only; no actual patient or outreach lists.
9. After successful testing and owner approval, update *only* these two public values in `website-leads-config.js`: `enabled:true`, `endpoint` for the dedicated project, and `turnstileSiteKey`. The browser then reveals the secure inquiry form. Keep email fallback visible.
10. Run desktop/mobile Chromium verification and one permissioned end-to-end test; confirm the inquiry is stored in MMeD database, notification reaches the business inbox **once**, and no secrets or protected patient records are exposed. Monitor for 24-hour error trends after release.

## Event and conversion measurement

The current GSC Wizard account is connected to Search Console **read-only** and has **no linked GA4 data scope**. Identify the actual GA4 owner, connect it through GSC Wizard, and review consent requirements before publishing tracking tags. Recommended eventual events: `demo_request_page_view`, `lead_form_started`, `lead_form_submitted` and `mailto_fallback_clicked`. Only send events after consent and security review. Do not send names, emails, company names, or inquiry text to GA4.

## Search platform owner actions

- In **GSC Wizard Account**, choose `Enable full access` and authorize Search Console `webmasters` scope. The current `webmasters.readonly` connection prevents programmatic sitemap submission.
- At **Bing Webmaster Tools**, import the verified Google Search Console property or use ownership verification, then link a Bing Webmaster Tools API key to GSC Wizard to retrieve Bing performance. IndexNow is already configured and its submissions are not evidence of indexing.
- Google sitemap `https://mmedsystems.com/sitemap.xml` is live; as of October 18 the GSC report still showed `isPending:true`.

## Safety acceptance checklist

- `website-leads-config.js` MUST remain `enabled:false` until a complete verified activation change is reviewed. The public site remains email-based in the meantime.
- No inbound email content is automatically evaluated by an AI agent. Visitor notes are untrusted text for human review only.
- No passwords, API secrets, personal customer data or production endpoint environment values committed to GitHub.
- Existing demo.mmedsystems.com private clinical application, invitation access, NDA requirements, and DNS/MX/SPF/DKIM/DMARC untouched.
