---
name: trend-to-fit
description: Find and adapt attributable trend mechanics for a manifest-driven client without copying creators or presenting attention signals as business outcomes.
---

# Trend to Fit

Use this skill when asked to research current content patterns, evaluate supplied trend records, or turn a trend into a client-owned adaptation. The client manifest is the routing source of truth. The trend library is the durable output.

Read [references/trend-score.md](references/trend-score.md) before scoring or accepting a trend.

## Inputs

Require an explicit path to the client workspace manifest. There is no default workspace and no fallback client.

If no manifest path is supplied, stop and ask which client workspace to use. Do not infer the client from the trend topic or from recent work.

Resolve every other asset through the manifest:

- Client context
- Demand map
- Trend library
- Transcript index
- Content history
- Research source statuses
- Current initiative, pillars, output formats, CTA classes, and fatigue rules

Do not replace these paths with a remembered global skill path or an unverified external source.

## Workflow

### 1. Load the client manifest and research statuses

Load and validate the manifest before researching. State the resolved manifest path and `client_id` in the work log. Confirm that the context, demand map, trend library, transcript index, and content history exist and parse.

Inspect every declared research source. Report each source as connected, export required, not connected, optional, stale, or unavailable according to the manifest and supplied files. Do not describe a source as checked when it was unavailable.

### 2. Bound discovery to allowed sources

Search only configured platforms or supplied research exports.

- A connected source may be queried within its configured scope.
- An `export_required` source may be used only when the requested export is supplied.
- A `not_connected` source is unavailable.
- An optional source may be used only when the request or manifest activates it.
- A supplied export may be inspected even when live access is unavailable, but record its capture date and age.

Do not expand discovery to arbitrary platforms because they are convenient. If no configured or supplied source can answer the request, stop and return that source limitation.

### 3. Capture attributable source records

For every candidate, record:

- Platform and source creator
- Canonical source URL or supplied report identifier
- Published date when available
- Date discovered and date observed
- Observable metric name, value, unit, and observation window
- Format and duration or dimensions when observable
- Apparent audience, labeled as an observation only when the source directly supports it
- Research source and its manifest status

Use `Observed evidence` for facts visible in the source or export. Keep exact dates beside metrics because counters change. A metric without a source URL or report identifier and observation date is not usable evidence.

Views are not conversion proof. Likes, shares, comments, retention, search growth, and outlier ratios are attention or engagement signals unless attributable business-outcome evidence explicitly connects them to qualified conversations, leads, sales, or revenue.

### 4. Separate evidence from performance explanations

Use `Inference` for every explanation of why a pattern may have worked. Do not turn timing, topic choice, emotion, creator authority, audience fit, editing, or platform distribution into a causal claim without evidence.

For each inference:

1. Name the observed evidence it interprets.
2. State the proposed explanation in cautious language.
3. Record plausible alternative explanations.
4. Give a confidence of low, medium, or high.
5. Name what evidence would confirm or weaken it.

Never award evidence-quality points for an unlabeled causal story.

### 5. Decompose mechanics without copying execution

Describe the reusable mechanics:

- Format
- Hook mechanism
- Narrative structure
- Visual treatment
- Pacing or editing pattern when observable
- Audience participation or response mechanism

Do not copy source wording, claims, branded devices, shot-for-shot execution, proprietary frameworks, distinctive story beats, or a creator's voice. A valid adaptation preserves the abstract mechanism while replacing the language, examples, proof, and conclusion with client-owned material. Attribution does not make copying acceptable.

### 6. Require client fit and ownership

Require a matching ICP problem before scoring. The problem must appear in the client context, demand map, or attributable audience evidence. State the founder's recognizable situation, lived consequence, and desired human or commercial outcome.

Require a client-owned POV. Support it with the client context or a validated client-owned source referenced in the transcript index. An index summary can identify where to look, but it does not prove an exact quote or speaker ownership by itself. If the POV comes from a transcript, validate the complete source and speaker before quoting it.

Reject a candidate when the trend supplies the entire idea and the client contributes only a paraphrase. Research can validate or shape delivery. It cannot manufacture the client's perspective.

### 7. Match the strategy route

Assign exactly one:

- Approved pillar
- Current business initiative
- Valid client-defined pillar and output format
- Primary CTA class with an available destination

Saturday may accept the highest-match pillar. Other days must follow the manifest's pillar and flexibility rules. Serve the primary ICP first and state one secondary authority signal. Use the demand map only within the limits of its source. Transcript-derived demand is qualitative evidence, not market volume.

### 8. Score trend fit

Apply the 100-point rubric in `references/trend-score.md`. Record every dimension, its points, and one evidence-based rationale.

- Below 70: reject.
- 70 to 79: viable.
- 80 to 89: strong.
- 90 to 100: flagship-fit.

A high score cannot rescue copied execution, missing source attribution, an unsupported conversion claim, an expired record, or an absent client-owned POV.

### 9. Check content history and fatigue

Check content history after scoring. Compare the full fatigue fingerprint:

`pillar + owner_problem + unique_pov + hook_mechanism + format + primary_cta_class`

Apply the manifest's topic cooldown and hook frequency rules. Fatigue is a post-score gate, not negative points. Label the result `clear`, `review`, `hold`, or `unknown`. CTA sequence is evaluated only after the provider schedules content.

- `clear`: no known conflict in complete available history.
- `review`: partial overlap may be justified by new proof, buyer stage, or conclusion.
- `hold`: a cooldown or frequency rule would be breached. Reject until resolved.
- `unknown`: history is missing or incomplete. Do not call it clear. Hold for human review unless the user explicitly accepts the uncertainty.

### 10. Apply rejection gates

Reject the candidate and return a clear reason when any of these applies:

- Score below 70
- Missing, stale beyond usefulness, or unverifiable source evidence
- Missing source URL or report identifier and observation date
- Expired trend record
- No matching ICP problem
- No client-owned POV
- Copied wording or distinctive execution
- Unsupported popularity, causation, conversion, lead, sales, or revenue claim
- No valid pillar, initiative, output format, or available CTA route
- Fatigue status `hold`
- Confidential, unsafe, or unapproved material is required for the adaptation

Name the failed gate and the smallest missing evidence or change that could make the candidate eligible. Do not write rejected candidates into the trend library.

### 11. Write the adaptation brief

For an accepted candidate, append one adaptation record to the manifest-resolved trend library. Preserve valid existing records and its JSON array shape. Do not edit unrelated records.

The record must contain:

- Stable trend ID
- Platform, source URL, source creator, research source, and source status
- Published date when available, discovered date, observed date, and `expiration` date
- `Observed evidence` entries with metrics, values, units, dates, and attribution
- `Inference` entries with linked evidence, alternatives, confidence, and validation need
- Format, hook mechanism, narrative structure, visual treatment, and pacing
- Apparent audience and the matching ICP problem
- Client-owned POV with source attribution and ownership confidence
- Pillar, current initiative, output format, CTA class, and authority signal
- Demand evidence IDs and explicit limits
- Trend score total, band, and dimension breakdown
- Full fatigue fingerprint, fatigue status, and content-history conflicts
- Adaptation opportunity using original client language, proof, examples, and conclusion
- Compliance and attribution notes

Set expiration from source freshness, platform velocity, and the manifest's research cadence. If the evidence does not support a precise shelf life, choose a conservative date and label that choice as inference. Never leave freshness implied.

Before writing, check for an existing source URL or trend ID and update only when the new observation is newer and attributable. Return the written record path and ID. If the candidate fails, return the rejection reason and make no mutation.

## Output boundary

The output is a trend-library adaptation brief or a clear rejection. It is not a finished hook, script, design, rendered asset, scheduled post, published post, or external task. Do not write to ClickUp or any external production system without separate authorization.

## Final quality gate

1. Every metric has a source and date.
2. Every causal explanation is labeled `Inference`.
3. Every fact is labeled `Observed evidence` or traced to a client asset.
4. The adaptation uses a client-owned POV and original wording.
5. The route matches one ICP problem, pillar, initiative, output format, and CTA class.
6. The score follows the reference and fatigue runs afterward.
7. The source has not expired and the record includes an expiration date.
8. No attention metric is presented as conversion proof.
9. No confidential detail or unsupported claim survives.
10. No external write exceeds the request.
