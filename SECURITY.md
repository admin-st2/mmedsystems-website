# Security Policy

## Scope

This public repository contains the MMEd Systems public website. It is not
intended to host production electronic medical record (EMR/EHR), patient-portal,
pharmacy, billing, laboratory, or other confidential healthcare application
source code, credentials, patient data, or operational secrets.

## Reporting security concerns

Please privately report suspected vulnerabilities to
**info@mmedsystems.com**, with subject **Security report — MMEd Systems**.
Describe the affected URL, observed behavior, and reproducible steps without
including real patient records, passwords, API keys, or other sensitive data.

Do not publish vulnerability details in public GitHub issues before the
maintainer has had an opportunity to investigate and coordinate a fix.

## Development safeguards

- Keep sensitive applications and source code in private repositories with
  least-privilege access.
- Enable multi-factor authentication, protected default branches, and code
  review for changes.
- Never commit secrets; use managed encrypted environment variables.
- Review dependencies, third-party licenses, and AI-assisted code.
- Never use identifiable patient data in public demonstrations.

**Note:** This document describes required safeguards, not a certification
that all controls have already been implemented.
