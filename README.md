# Client Content System

Client Content System is a reusable public engine for building a client-owned content operation. It provides schemas, empty workspace templates, validation, and an installable thumbnail skill. It is not a repository of client work.

## Product boundary

This repository contains the reusable operating system:

- public documentation and architecture
- client workspace templates and schemas
- reusable skills and validation tools
- fictional or empty example structures only

It does not contain client transcripts, research, content history, strategy, credentials, source media, logos, or identifying details. Those materials belong in a separate private client workspace.

## First release

The first release supplies a white-labeled, installable thumbnail skill from `skills/brand-thumbnail`. The skill uses a client-owned `thumbnail-brand.md` file in the current workspace as its source of truth. It can inspect supplied media, protect exact copy and official logos through deterministic compositing, and verify the final image before handoff.

## Planned pipeline

The public foundation is designed to support a repeatable pipeline:

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

See [architecture documentation](docs/architecture.md) for the end-to-end model and [security guidance](SECURITY.md) before contributing.
