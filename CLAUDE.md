# Claude Code Instructions

This repository is the reusable public engine for a client content system. It is not a client workspace and must never become one.

## Start every session here

1. Run `git status -sb` and confirm the active branch.
2. Read `README.md`, `docs/architecture.md`, `docs/roadmap.md`, and `SECURITY.md`.
3. Run the baseline checks before changing behavior:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```

4. Inspect the current pull request and recent commits instead of relying on chat history.

## Product boundary

The public repository may contain reusable code, schemas, empty templates, tests, and generic skill instructions. Keep all real client names, transcripts, research, history, strategy, credentials, source media, logos, portraits, and generated deliverables in a separate private workspace.

Do not add real or realistic client example records. Empty templates and clearly generic placeholders are the safer default.

The reusable engine must not depend on a particular person, company, industry, geography, brand token, local username, or filesystem layout.

## Architecture rules

- `templates/client-workspace/` defines the empty private-workspace starting point.
- `schemas/` defines portable contracts.
- `skills/` contains installable, white-labeled capabilities.
- `scripts/validate_repo.py` validates the exact Git index state that would be committed.
- Research and source truth stay private. Public skills receive only the active workspace context supplied at runtime.
- Proposals may be generated before approval. Production and distribution must respect the workspace approval gate.
- No skill may publish, schedule, upload, or send content without explicit authorization.
- Content history records verified outcomes. Do not represent a proposal as published or successful.

## Skill requirements

Every new skill must:

- have a focused `SKILL.md` with valid `name` and `description` frontmatter
- remain white-labeled and workspace-driven
- define its inputs, outputs, failure behavior, and approval boundary
- ground claims in supplied source material and expose uncertainty
- include tests or executable verification proportional to its risk
- keep exact copy and official logos deterministic when assets require fidelity
- protect a real person's likeness when approved source media exists
- avoid publishing or distribution side effects by default

Keep the main `SKILL.md` concise. Put detailed contracts and examples in `references/`, and reusable mechanics in `scripts/`.

## Engineering workflow

- Work on a feature branch. Do not commit feature work directly to `main`.
- Build one thin, testable pipeline slice at a time.
- Write contract and validator tests before implementation when behavior changes.
- Keep repository validation on the Python standard library.
- Preserve macOS and Ubuntu compatibility for shell tooling.
- Run the full test suite, repository validator, shell syntax checks, and skill-specific smoke tests before handoff.
- Commit focused changes, push the branch, and use a pull request.
- Use standard hyphens in reader-facing copy. Do not introduce em dashes or en dashes.

## Current implementation state

The completed foundation includes:

- the public/private architecture and security boundary
- the client workspace manifest schema and empty templates
- the installable `brand-thumbnail` skill
- staged-content privacy and contract validation
- regression tests and GitHub Actions CI
- GitHub private vulnerability reporting

The remaining pipeline is intentionally not presented as implemented. Continue it in the order defined in `docs/roadmap.md`.

## Definition of done

A pipeline slice is done only when its public contract is documented, its private-data boundary is preserved, negative and positive tests pass, the repository validator passes against the committed index, the branch is pushed, and CI is green. A local proof is not evidence that an external publish or integration occurred.
