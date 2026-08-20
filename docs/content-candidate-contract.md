# Content Candidate Contract

Status: proposed. This contract is awaiting owner approval. No downstream skill may be built against it until that approval is recorded.

## Purpose

A content candidate is the shared interface between research, evaluation, approval, production, and learning history. It lets `transcript-to-content`, `trend-to-fit`, approval orchestration, and production routing exchange one portable record instead of trading free-form prose.

A candidate is a proposal. It is not approved, produced, distributed, or proven by default.

## Files

- `schemas/content-candidate.schema.json` is the versioned declarative contract.
- `scripts/validate_candidate.py` is the executable form of the same contract. Skills, tests, and CI share it so that a candidate cannot be valid in one place and invalid in another.
- `schemas/examples/content-candidate.example.json` is an obviously fictional proposed candidate.
- `templates/client-workspace/candidates/content-candidates.json` is the empty private starting file.

Candidate records are client data. They live in the private workspace. The public repository holds the contract, the validator, and empty or fictional fixtures only.

## Record shape

| Field | Required | Meaning |
| --- | --- | --- |
| `schema_version` | yes | Contract version. Currently `1.0`. |
| `candidate_id` | yes | Stable lowercase identifier for this proposal. |
| `created_date` | yes | Date the proposal was generated. |
| `status` | yes | Candidate lifecycle position. |
| `pillar_id` | yes | One configured workspace content pillar. |
| `topic` | yes | Short canonical topic label used for fatigue comparison. |
| `audience_problem` | yes | The audience problem this candidate serves. |
| `source` | yes | Source type and the private source references behind the proposal. |
| `proposal` | yes | Hook, core claim, supporting evidence, and format. |
| `cta_stage` | yes | Stage selected from the workspace CTA ladder. |
| `assessment` | yes | Confidence, rationale, uncertainties, risk notes, review notes. |
| `approval` | yes | Approval state and, when a decision exists, its record reference. |
| `extensions` | no | Skill-specific detail that is never authoritative. |

## Grounding rules

Every source reference carries a workspace-relative `locator`, a `locator_detail` that identifies the exact span used, and a `retrieved_date`. Absolute paths, parent-directory escapes, and Windows drive paths are rejected, so a candidate cannot point outside the workspace it belongs to.

The core claim and every supporting evidence item must cite at least one `reference_id`, and every cited identifier must resolve to a declared source reference. A claim with no source, or a claim citing an undeclared source, fails validation. Evidence records its own `strength`, which keeps a direct quote distinguishable from an inference.

Confidence below `high` must record at least one uncertainty. The contract prefers a visible gap over a filled one.

## Lifecycle and approval

`status` tracks the candidate: `proposed`, `in_review`, `needs_revision`, `rejected`, `approved`.

`approval.state` tracks the human decision: `not_requested`, `pending`, `approved`, `rejected`, `expired`.

The two are coupled and cannot drift:

- an `approved` status requires `approval.state` of `approved`
- a `rejected` status requires `approval.state` of `rejected`
- a `proposed`, `in_review`, or `needs_revision` candidate must not carry a decided approval state
- a `not_requested` or `pending` candidate must not carry any decision field, so approval evidence cannot be invented
- an `approved` candidate requires a record reference, a decider, a decision date, and an approved content digest
- a `rejected` or `expired` candidate requires a record reference, a decider, and a decision date

The candidate has no `produced`, `published`, or `performed` status. Production and publication are verified outcomes and belong in `history/content-history.csv`. A proposal must never be able to describe itself as published.

## Approved content digest

`approval.approved_content_digest` is the sha256 digest of the approvable content: `pillar_id`, `topic`, `audience_problem`, `source`, `proposal`, and `cta_stage`, serialized as JSON with sorted keys and compact separators.

Approval bookkeeping is excluded from the digest so that recording a decision does not invalidate the decision it records. If any approved element later changes, the stored digest stops matching and validation fails. That is how approval orchestration detects a changed candidate instead of carrying a stale approval into production.

Use `content_digest()` in `scripts/validate_candidate.py` to compute it. Do not reimplement the serialization.

## Production routing

`proposal.format.type` is the deterministic routing key: `short_video`, `long_video`, `image_post`, `carousel`, `text_post`, `newsletter`, `audio`.

`proposal.format.required_assets` lists the assets production must supply, such as `thumbnail`, `cover_image`, `captions`, or `graphic`. A candidate that requires a `thumbnail` routes through the `brand-thumbnail` skill. Routing reads these fields and does not infer format from prose.

## Content history mapping

Candidate fields map directly onto the private content history columns, so a verified outcome can be recorded without restating the proposal:

| Candidate | Content history |
| --- | --- |
| `candidate_id` | `content_id` |
| `created_date` | `created_date` |
| `pillar_id` | `pillar` |
| `topic` | `topic` |
| `proposal.hook` | `hook` |
| `proposal.format.type` | `format` |
| `cta_stage` | `cta_stage` |
| `approval.state` | `approval_status` |

`published_date`, `distribution_channel`, `performance_summary`, `fatigue_signal`, and `learning` have no candidate source. They are written only from verified results.

## Extensions

`extensions` holds optional skill-specific detail under a lower snake case namespace, for example a trend fit breakdown. Extension names may not shadow contract fields, and extension content is never authoritative for status, approval, or routing. A skill that needs an extension to decide approval or production is a skill that needs a contract change instead.

## Versioning

`schema_version` is currently `1.0`. Any change to required fields, enum values, coupling rules, or digest inputs is a version change, and the schema, validator, fixtures, tests, and this document change together.

## Validation

```sh
python3 scripts/validate_candidate.py <candidate-file.json>
python3 -m unittest discover -s tests
python3 scripts/validate_repo.py
```

`scripts/validate_candidate.py` accepts a single candidate object or an array of candidates, so the private `candidates/content-candidates.json` file can be validated as a whole.
