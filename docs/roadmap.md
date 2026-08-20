# Delivery Roadmap

## Outcome

Complete a portable content pipeline that turns approved private research and source material into verified client deliverables while keeping client data outside the public repository.

The system should compound as reusable contracts, skills, and orchestration. It should not become a pile of one-off prompts.

## Completed foundation

The repository currently provides:

- a public engine and private workspace separation
- a versioned client workspace manifest schema
- empty research, source, approval, and history templates
- a white-labeled thumbnail production skill
- repository privacy and contract validation
- automated tests and CI

Treat those components as established interfaces. Change them deliberately and update their tests and documentation together.

## Build sequence

### 1. Define the content candidate contract

Create a versioned schema for a proposed content candidate before implementing additional generation skills.

At minimum, the contract should distinguish:

- candidate identifier and status
- source type and source references
- audience problem and content pillar
- proposed hook, core claim, supporting evidence, and format
- CTA ladder stage
- confidence, uncertainty, and review notes
- approval state and approval record reference

A candidate starts as a proposal. It is not approved, produced, distributed, or proven by default.

Acceptance criteria:

- the schema rejects missing source references and invented approval states
- example fixtures are empty or obviously fictional
- the repository validator checks the public contract
- the owner approves the contract before skill implementation begins

### 2. Add `transcript-to-content`

Purpose: turn supplied private transcript material into source-grounded content candidates.

Inputs:

- `content-system.yaml`
- `content-context.md`
- `sources/transcript-index.json`
- transcript files explicitly supplied from the private workspace
- the approved content candidate contract

Required behavior:

- read the actual transcript before proposing hooks or claims
- preserve traceable source references for every material claim
- map candidates to one of the four configured content pillars
- select a CTA stage from the workspace ladder
- expose uncertainty instead of filling evidence gaps
- produce candidates only, with no production or distribution side effects

Acceptance criteria:

- source-free claims fail validation
- missing transcript files produce a clear failure
- approved and unapproved states cannot be confused
- tests cover one valid candidate and the major negative paths

### 3. Add `trend-to-fit`

Purpose: evaluate whether a private trend signal fits the client's audience, objective, evidence, and timing before it becomes a content candidate.

Inputs:

- `content-system.yaml`
- `content-context.md`
- `research/demand-map.csv`
- `research/trend-library.json`
- the approved content candidate contract

Required behavior:

- separate observed trend evidence from interpretation
- score strategic fit without inventing demand or client proof
- reject or flag stale, weakly sourced, off-pillar, or off-objective trends
- record the fit rationale and risk notes
- emit candidates only when the minimum evidence threshold is met

Acceptance criteria:

- empty or stale trend evidence does not become a confident recommendation
- output remains traceable to the source signal and audience problem
- generic popularity alone is not treated as client fit
- tests cover accepted, rejected, stale, and insufficient-evidence paths

### 4. Add approval orchestration

Purpose: move only approved candidates into production.

Required behavior:

- read the manifest approval gate and approval record
- block production when approval is missing, expired, or ambiguous
- preserve the approved copy, source references, format, and CTA intent
- write no approval on behalf of a human unless explicitly authorized

Acceptance criteria:

- an unapproved candidate cannot reach a production skill
- approval records resolve inside the private workspace
- tests cover approval, rejection, missing record, and changed-candidate cases

### 5. Add fatigue-aware production routing

Purpose: select the right production capability while preventing repetitive topics and hooks.

Required behavior:

- inspect `history/content-history.csv` before routing
- apply the manifest lookback and reuse limits
- route thumbnail requests through `brand-thumbnail`
- keep production outputs and source assets in the private workspace
- record a proposed history update separately from verified publication results

Acceptance criteria:

- fatigue violations block or require a refreshed angle
- routing is deterministic from the approved format
- production verification is required before handoff
- no distribution action occurs without separate explicit authorization

### 6. Add the top-level pipeline command

Purpose: provide one documented entry point that coordinates research, candidate creation, approval, production, verification, and history without collapsing their boundaries.

The command should report its current stage, required inputs, blocked reason, produced artifacts, and next authorized action. A stage failure should stop downstream work cleanly.

## Release gates

Before calling the pipeline complete:

- every stage has an explicit input and output contract
- every stage has positive and negative tests
- the public repository contains no real client material
- the workspace manifest paths resolve safely
- approval is enforced before production
- distribution remains a separate authorization
- local validation and GitHub Actions both pass
- installation and continuation steps are documented for Claude Code and Codex

## Highest-leverage next action

Define and approve the content candidate schema. It is the shared interface that lets transcript research, trend evaluation, approval, production, and learning history connect without turning the pipeline into agent soup.
