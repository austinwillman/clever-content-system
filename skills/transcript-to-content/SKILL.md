---
name: transcript-to-content
description: Build and maintain a source-grounded client content foundation, mine complete interview transcripts, refresh timely signals, return a ranked video approval board, and create recording and editor briefs for approved short-form topics.
---

# Transcript to Content

Turn spoken source material into a ranked, strategy-aligned content queue. Preserve the source insight. Do not manufacture authority, client proof, demand, popularity, or certainty.

## Inputs and source of truth

Require an explicit client workspace manifest path from the caller. There is no default workspace.

If no manifest path is supplied, stop and ask which client workspace to use. Do not infer the client from the request topic, the transcript contents, the most recently used workspace, or the current working directory. Selecting the wrong workspace produces one client's strategy inside another client's batch, so an unresolved client is a hard stop rather than a guess.

Before mining, confirm that `client.identifier` in the resolved manifest matches the client the caller named. Every candidate you emit carries that identifier in its `client_id` field, and a batch that mixes identifiers fails validation.

Load strategy and assets through the manifest. Never replace manifest asset paths with hardcoded paths for any particular client. The durable inputs are:

- The client manifest and its context asset
- The approved one-time client foundation
- The persistent topic bank
- The full Plaud transcript for every mined recording
- The demand map
- The trend library when a trend or format pattern is relevant
- The hook library and its evidence grades
- The research log that separates foundation validation from batch signal scans
- The content history
- The transcript index when declared by the manifest

Read [references/client-foundation-and-research.md](references/client-foundation-and-research.md) when creating or refreshing a client foundation, topic bank, Search Target, or connector plan. Read [references/owner-recognition-filter.md](references/owner-recognition-filter.md) before refining a candidate. Read [references/scoring-and-routing.md](references/scoring-and-routing.md) before scoring or routing it. Read [references/live-hooks-and-production.md](references/live-hooks-and-production.md) when generating same-session hook pickups, green-screen direction, B-roll notes, or an editor package. Read [references/output-contract.md](references/output-contract.md) before returning an approval board, Recording Card, or editor package.

## Candidate contract

Every topic you propose is a content candidate governed by `schemas/content-candidate.schema.json`. Validate a candidate with `scripts/validate_candidate.py` before it reaches an approval board, and validate the batch before it becomes Recording Cards.

The contract enforces four rules that this workflow already assumes:

- `client_id` must equal `client.identifier` in the resolved manifest, and one batch may not mix clients.
- Every candidate needs at least one source reference and at least one supporting evidence entry.
- `approval.state` cannot be `approved` without an approver, a timestamp, and a workspace-relative approval record reference.
- A candidate cannot reach `approved_for_recording` unless it holds real approval, and approval requires at least one evidence entry whose `validation_status` is not `unavailable`.

The last rule is the abstention rule in code. A topic with no defensible evidence may be proposed and disclosed as such. It may not be approved into production.

## Workflow

Follow these steps in order. A failed gate stops the affected candidate. Do not skip ahead because an idea sounds promising.

### 1. Resolve the client and one-time foundation state

Load the client manifest from the explicit argument or the stated default. Resolve every declared asset relative to the manifest directory and keep every path inside that directory. Use the existing `loadClientConfig` and validation interfaces without changing their contract. State the resolved manifest path and `client_id` in the work log.

Client foundation intake happens once. If the approved foundation is missing, inspect the authorized workspace and connectors before asking questions. Extract answers with evidence references, identify conflicts and unresolved fields, and ask only for answers that cannot be found safely. Never infer access permission or search a connector outside the user's authorized workspace. The client must approve the completed foundation before the topic bank becomes the baseline.

Do not rerun full foundation research for each batch. Reopen it only when the ICP, positioning, offer, pillars, proof boundaries, or CTA strategy changes, during a scheduled strategic review, or when the active topic bank can no longer support a complete batch.

### 2. Run foundation research once, then persist the topic bank

Before creating the initial topic bank, run the foundation research pass from the research reference. Use customer language, sales and support conversations, reviews, search queries, analytics, proposals, and approved workspace documents when available. Preserve source IDs and distinguish observed language from the client's interpretation.

Build `topic_bank` from the approved foundation plus research evidence. Every entry keeps the ICP problem, buyer language, client POV, owner outcome, pillar, evidence IDs, status, and last validation date. This is the evergreen baseline. A weekly or batch run selects from and enriches the bank rather than rebuilding it.

### 3. Validate required assets and research availability

Confirm that the context, client foundation, topic bank, demand map, trend library, hook library, research log, transcript index, and content history exist and parse. Validate the client asset package before mining.

Inspect every `research_sources` entry. Report `not_connected`, `export_required`, stale, missing, or optional sources before scoring. Continue with honest available evidence when the manifest allows it. Never describe an unavailable source as checked, and never substitute transcript relevance for search volume or market popularity.

### 4. Run the abbreviated batch signal scan

Before each batch, inspect the configured `batch_signal` sources. Look for recent ICP language, questions, objections, timely events, high-retention hook observations, and content-performance changes. Metricool inbox threads, competitor observations, native analytics, search queries, and recent customer conversations are useful inputs when actually available.

Write a dated batch signal record to the research log. Attach a signal to an existing topic-bank entry when possible. Create a new bank entry only when the signal represents a durable, materially different problem or point of view. Missing current signals do not invalidate a sound evergreen topic.

### 5. Set the transcript mining window

Infer the narrowest useful scope from the request.

- For `recent` or no date range, inspect the last 30 days.
- For a named recording or topic, search by recording name first.
- Ask one question only when the intended client or business lane cannot be inferred safely.

Use Plaud in this sequence:

1. List recordings with the narrowest useful date or name filter.
2. Retrieve compact notes for candidate discovery only.
3. Retrieve full transcripts for likely candidates.
4. If notes or transcripts are empty, report incomplete processing and retry once before considering a transcription fallback.

Do not retrieve every full transcript by default. AI-generated notes, summaries, and outlines may discover candidates, but they cannot prove wording, ownership, context, or complete coverage.

### 6. Full-transcript validation gate

Prove complete coverage before extracting, scoring, drafting, or creating tasks:

1. Record the Plaud file duration.
2. Retrieve the transcript and compare `returned` with `total`.
3. Treat a non-null `next_cursor` or `returned < total` as incomplete pagination.
4. If the transcript tool cannot request the next cursor, retrieve the Plaud file details, locate the `source_list` entry whose `data_type` is `transaction`, and parse its `data_content` as the complete segment array.
5. Confirm that the parsed segment count equals the reported `total`.
6. Confirm that the final segment `end_time` reaches at least 98 percent of the recording duration.
7. Use only the validated complete segment array as the source of truth.

If either count or duration coverage fails, retry Plaud processing once. If it still fails, stop and report the recording as partial. Do not score topics, draft content, or create downstream tasks from incomplete coverage.

### 7. Apply ownership and confidentiality gates

Use an idea only when the client owner originated it, materially developed it, or clearly adopted it. When the manifest declares an owner speaker label, only segments attributed to that speaker may be treated as owner-originated claims. When no owner label is declared, treat ownership as unresolved and lower the ownership confidence rather than assuming.

- Attribute another speaker's distinctive idea.
- Do not present a guest's idea as the client's idea.
- Treat ambiguous speaker labels as unowned until manually resolved.
- Exclude confidential client names, private financials, credentials, personal data, health details, internal DWS information, and identifiable employee details unless publication is explicitly authorized.
- Generalize a sensitive example without changing its lesson. Use brackets when a quote needs a redaction. Never silently rewrite a quotation.
- Label unverifiable numbers and outcomes as placeholders. Plans, estimates, and illustrative claims are not proof.
- Do not claim a result, live offer, case study, integration, or research finding without a verifiable source.

### 8. Extract complete content atoms

Extract complete ideas, not isolated quotations:

- Contrarian belief or reframe
- Founder story with tension and resolution
- Operational lesson
- Framework or sequence
- Analogy or memorable phrase
- Failure, correction, or learned lesson
- Prediction
- Specific observation supported by experience
- Question the client is genuinely exploring

For each atom, retain the recording identifier, title, date, speaker, timestamp, source excerpt or faithful paraphrase, necessary context, and ownership confidence.

### 9. Build the owner-facing tension map

Apply the reference structure to every candidate. It must include a real quote, objection, confusion, frustration, aha, unique POV, owner outcome, raw hook material, `not_about`, and `really_about`.

Run the **Five-second founder recognition** gate. A candidate must connect all three of these before it can advance:

1. A recognizable **business problem**.
2. The **founder experience** of living with it.
3. A human or commercial **owner outcome**.

Lead with the owner's situation, language, or consequence. Mechanism-first language such as AI, automation, APIs, integrations, databases, dashboards, workflows, agents, or software fails unless the owner used it naturally first.

The client owner owns the final hook unless they explicitly request hook writing. Return source-grounded raw hook material by default, not polished opening hooks.

### 10. Match strategy, demand, authority, and CTA

For every surviving candidate:

1. Assign one pillar declared by the client manifest. Scheduling remains the provider's decision.
2. Name the active strategic initiative it advances.
3. Attach **Demand evidence** IDs from the demand map, or set `demand_evidence_status` to `unavailable` when the validator permits it.
4. Label transcript-derived language as qualitative evidence. It does not prove search volume, trend status, or broad demand.
5. Attach relevant trend evidence only when the trend library contains a dated, attributable record.
6. State one authority signal that makes the idea discussable to a credible host, organizer, partner, or industry peer while still serving the founder first.
7. Select exactly one CTA class from the manifest and only an available destination. Begin with reach or conversation when trust and infrastructure are limited. Never promise a destination that does not exist.

Run the Search Target pass from the foundation and research reference before a topic becomes a recording brief. Select one attributable audience query, one natural spoken phrase, intent, supporting terms, evidence, and a validation status. Prefer owned query data, then paid keyword evidence, native platform search evidence, audience language, and finally dated manual search observation. Never label a phrase as a keyword merely because it sounds useful. Never invent search volume, difficulty, or LLM visibility.

### 11. Check the fatigue fingerprint

Build the **Fatigue fingerprint** from:

`pillar + owner_problem + unique_pov + hook_mechanism + format + primary_cta_class`

Parse the manifest-resolved CSV into **parsed content-history rows** named `historyRows`. Compare the full fingerprint with those rows using the manifest fatigue rules. Use the explicit batch review date for topic cooldown checks, not an invented publishing date. Check the topic cooldown and the configured **rolling hook window** across recent published history plus incoming topics. A repeated topic may advance only with new proof, a different buyer stage, or a materially different conclusion. Record every conflict and the disposition. Missing history means fatigue is unknown, not automatically clear. Existing history rows must still be enforced when a candidate is labeled unknown. CTA sequence is evaluated only after the provider schedules content.

### 12. Score and rank topics

Apply the scoring and routing reference only after all gates above. Reject or hold candidates that score below 60, depend on missing context, sound generic after extraction, require invented evidence, or duplicate recent content without a materially different angle.

Score Topic Score and short-form Video Score only. For every candidate, return **one concise video rationale** explaining why spoken delivery strengthens or weakens the topic. The topic must use a format declared in `content_output.allowed_formats`. A workspace may declare a single allowed format, and a topic that does not fit a declared format is not a candidate.

### 13. Return the approval board

Return the ranked Markdown approval board from the output contract. Include the gate status, strategy mapping, evidence quality, ownership confidence, fatigue result, Topic Score, Video Score, one concise video rationale, CTA class, and rejection or hold reason when relevant. End every detailed candidate section with `What do I do next? Approve / Refine / Reject`.

Mark a candidate as video-eligible only when its Video Score is at least 65, the complete source supports a founder-led recording, and no video-specific gate fails. Selecting `Approve` authorizes its post-approval Recording Card and detailed JSON record.

Do not write to ClickUp before explicit topic approval. Once the configured number of video-eligible approved topics reaches `content_output.batch_size`, create that number of briefs without asking for another approval. It does not authorize ClickUp creation, recording the video, editing, rendering, scheduling, publishing, uploading, or any other external action.

### 14. Create the configured Recording Card batch after explicit approval

After the client selects `Approve` for the **configured number of video-eligible approved topics**, create exactly `content_output.batch_size` Recording Cards backed by detailed JSON records. Do not request an additional approval for brief creation. Every record must use a format declared by `content_output.allowed_formats`. Each record must include its Search Target, match the JSON contract in the output reference, pass `validateTopic(topic, manifest)`, and join a batch that passes `validateWeeklyBatch(topics, manifest, historyRows)`. This keeps the configured rolling hook window connected to parsed content-history rows instead of validating the incoming batch in isolation. Scheduling remains the provider's decision.

If fewer than `content_output.batch_size` video-eligible topics are explicitly approved, stop and **request more topic approvals**. Do not pad the batch or silently advance a held, refined, deferred, or rejected topic.

The human-facing output is a simple Recording Card for a fresh, founder-led recording. Write from the viewer's position. Give the speaker one viewer question, one story, scenario, myth, or teardown prompt, three to five short follow-up questions, one natural search phrase, one plain-language point of view, one next step, and an optional visual. Target a sixth-grade listening level. Keep scoring, fatigue, authority labels, proof limits, and internal strategy language in the JSON record. Do not turn the card into a script or make the speaker manage the strategy system.

Recommend a transcript clip only when the original delivery is strong enough. Green-screen concepts are production direction only. Do not create or render supporting assets without explicit authorization.

Approval of a topic does not transfer hook ownership. The client owner owns the final opening hook unless they explicitly ask for final hook options or a final script.

### 15. Generate same-session hook pickups when requested

After the client answers a topic during the interview, use live structured notes or an authorized live-transcription sidecar. Do not wait for Riverside's post-recording transcript. Match the answer to the hook library and generate three source-grounded options: owner recognition, contrarian reframe, and story or proof. Label every option with the hook template ID and evidence grade.

Require hook-to-body continuity. The hook cannot promise a claim, story, or outcome that the recorded answer does not deliver. The provider selects one or two options, places them in the recording teleprompter or reads them to the client, and records clean pickups during the same session. This is hook generation authorization, not publishing authorization.

### 16. Create the post-interview editor package

After the complete recording transcript is available and validated, create the editor package from the output contract. Include exact timestamps, selected hook pickup, body edit, B-roll map, green-screen route and source asset, creative direction, captions, CTA, claim warnings, and what not to overproduce.

Every visual intervention must prove, explain, orient, or reset attention. Green screen is optional production direction. Verify source rights and attribution before recommending an asset. Do not create or render the asset unless separately authorized.

### 17. Write approved briefs to ClickUp only when separately authorized

Topic approval authorizes brief creation only. A separate, explicit instruction is required before any ClickUp write.

When separately authorized, write only the configured approved brief batch, set the content type consistently with the selected format, and preserve the approved wording and source evidence. Never publish, schedule, upload, or mark content complete without additional authorization.

Use the existing ClickUp short-form video `Content Type`: `Reels`.

## Final quality gate

Before returning either stage:

1. Compare every claim and quotation with the validated transcript.
2. Confirm ownership, attribution, confidentiality, and proof labels.
3. Confirm the founder recognizes the situation before the mechanism appears.
4. Confirm the topic advances one pillar, the active initiative, and one honest CTA stage.
5. Confirm demand, trend, authority, and fatigue labels match available evidence.
6. Remove manufactured certainty, corporate filler, and generic AI phrasing.
7. Remove em dashes and en dashes from reader-facing copy.
8. Keep raw hook material distinct from final hooks.
9. Confirm every final hook has hook-to-body continuity and an evidence grade.
10. Confirm there were no external writes beyond the user's authorization.

## Handoff boundaries

- Use a podcast production workflow only when asked for a full episode package.
- Use a short-form rendering workflow only when asked to render or package an approved video.
- Planning does not authorize rendering, ClickUp creation, scheduling, publishing, or uploading.
