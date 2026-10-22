# Architecture

## Purpose

Clever Content System separates a reusable public engine from private client workspaces. The engine makes the operating model repeatable. The workspace holds the client-owned context and records required to use that model safely.

## Public engine

The public engine consists of:

- `schemas/` for the workspace contract
- `templates/client-workspace/` for empty, portable starting files
- `skills/` for installable, white-labeled production capabilities
- `scripts/` and `tests/` for repository validation
- public documentation and security controls

The engine has no dependency on a particular client, industry, geography, brand, creator, or local filesystem layout.

## Private client workspace

One private workspace is created per client from `templates/client-workspace/`. Its manifest defines the client identifier, display name, 90-day objective, content pillars, cadence, destinations, source locations, research locations, approval gate, fatigue rules, and refresh dates.

The workspace is intentionally outside the public checkout. A workspace may reference client-owned data, but the public engine stores only the relative paths that its templates define. This separation lets the method evolve publicly without exposing the client record.

## Skills

Skills are installable capability packages. A skill reads only the context supplied from the active workspace and produces only the requested output. The initial `brand-thumbnail` skill uses `thumbnail-brand.md` in that workspace as its brand-specific source of truth.

The skill analyzes actual supplied media before selecting a hook. It treats exact text and an official logo as deterministic compositing inputs rather than asking a generative system to redraw them. When an approved source portrait or frame exists, it protects the real person. It validates dimensions and requires visual quality review before handoff.

## Research inputs

Research remains private to the client workspace. The planned templates organize demand signals in `research/demand-map.csv`, trends in `research/trend-library.json`, and source references in `sources/transcript-index.json`.

Inputs should be truthful, attributable, and current enough for the content decision. The engine does not turn incomplete research into invented claims. A production request needs actual source material or an explicit decision to work from a clearly bounded brief.

## Approval gate

The workspace manifest defines the approval gate. Research and planning can produce proposals, but production and distribution require the approval state the client workspace specifies. No public skill may publish, schedule, or upload content without explicit authorization.

## Production layer

The production layer turns approved private inputs into client deliverables. It is responsible for format selection, crop safety, phone-size readability, exact-copy treatment, official-logo compositing, source fidelity, and deliverable verification.

Output assets, production files, and source media remain in the private workspace or another approved client-owned system. The public repository may contain instructions and validation logic, but not the resulting client work.

## Learning history

`history/content-history.csv` is the planned private record of what was created, approved, published, and learned. It supports cadence management and fatigue rules while preserving the distinction between a proposed idea and a verified result.

Learning history should improve future decisions within the client workspace. It should not be copied into the public engine, because performance data and content records can reveal client strategy and identity.

## Flow

```text
public engine and templates
          |
          v
private client workspace
          |
          +--> private research and sources
          |
          v
proposal and approval gate
          |
          v
production layer and verification
          |
          v
private learning history
```

The public repository defines the reusable interface at each step. The private workspace supplies the actual client context and retains the resulting record.
