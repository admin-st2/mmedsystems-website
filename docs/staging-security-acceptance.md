# Staging security acceptance

This review checks that the staging branch cannot publish the full public website before the designated Cloudflare Pages project has both its primary and preview/immutable URLs secured with Cloudflare Access.

**Requirements:** default build exports placeholder only, offline test's simulated private copy includes site assets but not private source, missing Access keeps private mode blocked, and no production main-branch edits occur.

No credentials, live patient information, email delivery, paid services, or production deployment are required for these tests.
