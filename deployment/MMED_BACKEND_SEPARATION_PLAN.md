# MMeD Systems | Verified Backend Separation and Implementation Decision
**Review date:** October 21, 2026
**Status:** Architecture recommendation — no migration or new subscription authorized.

## What was verified directly
- Connected Supabase account has one organization, **e-onus.com's Org**, on the **Free** plan.
- The organization contains two active projects: `ProjectPulse` (`uoajcbnnvtblijkwrwrl`) and `e-onus-operations`. There is no project named MMeD.
- Read-only live inspection of the **ProjectPulse** project found **10 MMeD demo/communications tables** (plus two ProjectPulse tables), including `mmed_demo_access`, `mmed_demo_sessions`, `mmed_demo_module_activity`, `mmed_demo_feedback`, `mmed_demo_alerts`, `mmed_demo_followups`, `mmed_email_events`, `mmed_demo_patient_requests`, `mmed_demo_patient_messages`, and `mmed_patient_app_access`. All visible public tables have RLS enabled, but this alone is not proof that every policy is correct.
- That same project has MMeD functions (`mmed-demo-alert`, `mmed-demo-invite`, `mmed-demo-followup`, `mmed-resend-webhook`, `mmed-email-e2e-test`, `mmed-patient-app-invite`) and `projectpulse-gateway`.
- Current `projectpulse-gateway`, `mmed-resend-webhook`, and `mmed-email-e2e-test` have `verify_jwt:false`. This is not automatically insecure for verified webhooks, but endpoint authentication must be independently evaluated and test routes should not be left available unnecessarily.
- The latest Supabase security advisor for ProjectPulse reports **Leaked Password Protection Disabled**. It does not validate the public Next.js bundle, invitations, custom webhook signatures, or cross-service credentials.
- On October 12, the MMeD security assessment independently identified this cross-project mixture and urged separation. It also reported a critical Next.js dependency and visible protected interface bundle; their current status cannot be confirmed from the connected corporate GitHub repository.
- GitHub integration lists the public `mmedsystems-website` repository, but does not expose a separate clinical demo source repository. Therefore frontend deployment owner/provider and latest clinical app patch level remain **unverified**.

## Best target structure
Dedicated Supabase organization **MMeD Systems**, with separate billing and access administration from E-Onus:

1. **mmed-business** — corporate website lead intake and future MMeD CRM/partnerships. Only business contact records, never patient/test clinical tables.
2. **mmed-demo** — invitation-only demonstration and separate patient-app test environment. No real PHI; move *only* MMeD-specific tables/functions, required Auth users and NDA/access logs, and required service configuration from today's shared ProjectPulse database.
3. **mmed-clinical-production** — not create yet. Establish later with explicit production compliance, BAA/region/security and operational decisions before any real patient data.

Keep the public corporate site on GitHub Pages unless a verified hosting change is needed. Keep the private demo on its present host until a tested replacement is ready and access controls are validated.

## Why a whole-project transfer is wrong
ProjectPulse currently holds mixed resources from two systems. Supabase project transfers move the **entire project** between organizations. A transfer would relocate ProjectPulse's own resources too, defeating business independence. A full clone would similarly copy unrelated tables/functions. Perform a **selective logical migration** of MMeD-specific database objects/data with a reviewed allowlist; rebuild Auth dependencies and redeploy only approved MMeD Edge Functions with new project-specific secrets. Never bulk-copy `projectpulse-gateway`, ProjectPulse portfolio, audit, or unrelated records.

Official Supabase docs:
- https://supabase.com/docs/guides/platform/project-transfer
- https://supabase.com/docs/guides/platform/migrating-within-supabase
- https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore
- https://supabase.com/kb/troubleshooting/transfer-edge-function-from-one-project-to-another

## Cost planning (public list price, NOT a project-specific quote)
Supabase publicly lists a **Pro** organization starting at **$25/mo** with compute credit for one Micro project and additional Micro projects starting at **$10/mo**. At these starting assumptions, `mmed-business` and `mmed-demo` in one dedicated MMeD Pro organization would be roughly **$35/mo before extra usage, add-ons and taxes**. A third Micro production project would start at about **$45/mo** on those assumptions, but a compliant clinical production build may cost substantially more. Quote must be checked in the target organization before paid provisioning.

Source: https://supabase.com/pricing

## Safe implementation order
1. Establish that the company controls the new MMeD organization, billing, MFA, and privileged access; create only after billing approval.
2. Create **mmed-business** and migrate the staged public lead form schema/function from draft PR #11 to a non-production test environment before turning on public intake. Configure new dedicated Resend domain-scoped key, Turnstile, data retention, privacy disclosure, alerts and tests. Keep the email fallback until this passes.
3. Create **mmed-demo** with different database/auth/function secrets. Audit and patch the Next.js dependency and authenticated asset boundary. Export/import **only** MMeD tables, records and essential Auth dependencies; preserve invitation/NDA history appropriately. Test RLS revocation, revoked sessions, time zones, private URLs, email notifications, 30 tester concurrency and rollback. Never move real patient data without a separate lawful production review.
4. Update the clinical demo frontend configuration, deploy safely, verify with permissioned testers, and only then point the demo domain to the new MMeD backend. Retain rollback until signoff.
5. Remove MMeD tables, functions and privileged credentials from the old ProjectPulse project only after verified cutover, backup and owner signoff. Re-audit both projects.
6. Keep future MMeD clinical production physically separate from both MMeD public-leads and fictional demo projects.

## Do not do now
- Do not use the current E-Onus project for MMeD data.
- Do not create a third project under E-Onus for MMeD operations.
- Do not transfer or clone entire ProjectPulse into MMeD.
- Do not activate PR #11's public lead intake without isolated backend, secrets, anti-spam, privacy/legal review and end-to-end tests.
- Do not treat a working demo as authorization to store real patient data.
- Do not provision billable resources or change the demo without explicit approval.
