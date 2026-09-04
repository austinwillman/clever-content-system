# Clever Content System

Clever Content System is a reusable public engine for building a client-owned content operation. It provides schemas, empty workspace templates, validation, workspace scaffolding, and installable skills that turn client source material into approved content candidates. It is not a repository of client work.

## Product boundary

This repository contains the reusable operating system:

- public documentation and architecture
- client workspace templates and schemas
- reusable skills and validation tools
- fictional or empty example structures only

It does not contain client transcripts, research, content history, strategy, credentials, source media, logos, or identifying details. Those materials belong in a separate private client workspace.

## Running it

The engine runtime is Node. The Python scripts are the repository privacy boundary and the portable contract checker.

```sh
npm install
npm run check                       # Node tests, Python tests, repository validator
npm run validate:client -- path/to/client/content-system.yaml
npm run skills:install              # install the pipeline skills for a local agent
```

## What ships today

- `schemas/content-system.schema.json` defines the client workspace manifest.
- `schemas/content-candidate.schema.json` defines the content candidate contract that every skill in the pipeline reads and writes.
- `scripts/new_client.py` scaffolds a private client workspace and refuses to create one inside this repository.
- `lib/` is the engine runtime: manifest loading and validation, topic and batch validation, fatigue rules, and CSV parsing.
- `scripts/validate-client.mjs` validates a complete client asset package before mining.
- `scripts/validate_candidate.py` checks the portable candidate contract outside the Node runtime.
- `skills/transcript-to-content` turns supplied transcript material into ranked, source-grounded candidates and post-approval recording briefs.
- `skills/trend-to-fit` decides whether a supplied trend signal fits the client before it becomes a candidate.
- `skills/brand-thumbnail` produces a thumbnail from a client-owned brand profile, protecting exact copy and official logos through deterministic compositing.

See [docs/client-onboarding.md](docs/client-onboarding.md) for the runbook that takes one client from signed to first approval board.

## Multi-client rules

The engine serves many clients at once only because these rules hold:

1. One private repository per client. A workspace never shares a repository with another client or with the engine.
2. Skills take an explicit workspace manifest path. There is no default client, and an ambiguous workspace is a hard stop.
3. Every topic carries its `client_id`, and `validateWeeklyBatch` rejects a batch that mixes clients or omits one.
4. The manifest declares an `approval_gate` naming who approves and where the record lives.
5. The engine holds no client-specific data. A workspace declares its own approved recordings in `sources.approved_recording_ids`.

## Pipeline

1. Configure a client workspace from `templates/client-workspace`.
2. Capture source and research locations in the workspace manifest.
3. Use reusable skills to turn approved source material into production-ready content.
4. Keep an explicit approval gate before production or distribution.
5. Record outcomes and fatigue signals in the client workspace learning history.

The repository ships the engine and templates. Each client supplies and retains its own private inputs, approvals, production assets, and history.

## Installation

Clone this repository, then copy `templates/client-workspace` into a private location for the client. Do not create a client workspace inside this public repository.

Install the thumbnail skill by copying `skills/brand-thumbnail` into the target agent's skills directory, or use the agent's supported skill installation workflow. From a private client workspace, initialize `thumbnail-brand.md` from the bundled template only when explicitly requested.

This repository uses only Python standard-library dependencies for validation. Run the checks with:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```

## Client workspace model

Each client has a separate private workspace with this planned structure:

```text
client-workspace/
  content-system.yaml
  content-context.md
  research/
    demand-map.csv
    trend-library.json
  sources/
    transcript-index.json
  history/
    content-history.csv
  approvals/
    approval-record.md
  thumbnail-brand.md
```

The workspace manifest records locations and operating rules. The workspace itself holds client data, stays outside this repository, and is never committed here.

## Repository map

```text
docs/                         Architecture and public operating guidance
schemas/                      Public workspace schemas
templates/client-workspace/   Empty, reusable client workspace templates
skills/brand-thumbnail/       Installable white-labeled thumbnail skill
scripts/                      Standard-library repository validation
tests/                        Validation tests
```

See [architecture documentation](docs/architecture.md) for the end-to-end model, the [delivery roadmap](docs/roadmap.md) for the remaining pipeline, and [security guidance](SECURITY.md) before contributing. Claude Code should also follow the repository instructions in [`CLAUDE.md`](CLAUDE.md).
