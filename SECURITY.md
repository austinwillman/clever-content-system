# Security Policy

## Public data

This public repository may contain reusable code, schemas, empty templates, fictional placeholders, documentation, and generic skill instructions. `.env.example` may document required environment variable names without values.

## Private data

Keep the following outside the repository and out of commits, issues, pull requests, screenshots, and generated artifacts:

- client names and identifying details
- transcripts, recordings, source media, and research
- content plans, approvals, performance history, and strategy
- credentials, API keys, tokens, passwords, and populated environment files
- logos, portraits, brand files, and other client assets unless explicit written permission permits public use
- private workspace locations and local filesystem paths

The `.gitignore` file excludes `clients/`, `private/`, `secrets/`, `.env`, and `.env.*`, while allowing `.env.example`. Ignore rules are a safety net, not permission to place private materials in this checkout.

## Reporting a vulnerability

Do not open a public issue for a suspected exposure or vulnerability. Use [GitHub private security advisories](https://github.com/austinwillman/client-content-system/security/advisories/new) to report it privately to the repository owner with:

- a concise description of the issue
- the affected file, path, or component
- reproduction steps when safe to share
- the potential impact
- any suggested mitigation

Do not include credentials, client data, or private media in the report. The reporter should receive an acknowledgment and follow-up on the remediation path.

## Pre-publication checklist

Before pushing, opening a pull request, publishing a release, or sharing an archive:

- [ ] Review `git status` and the staged diff for unexpected files.
- [ ] Confirm no client workspace, client material, local filesystem path, or private asset path is present.
- [ ] Confirm no credentials, populated environment files, tokens, or secrets are present.
- [ ] Confirm examples are empty or clearly fictional and contain no real people, brands, or records.
- [ ] Confirm source media, logos, and portraits are not bundled without explicit public-use permission.
- [ ] Run the repository validation and tests documented in `README.md`.
- [ ] Check that repository documentation points only to public repository paths and the planned private workspace model.

If any item is uncertain, do not publish. Remove the material or obtain a clear approval before continuing.
