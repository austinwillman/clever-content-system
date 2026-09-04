# Client Onboarding Runbook

This runbook takes one client from signed to first approval board. Follow it in order. Every step names the artifact it produces so an interrupted onboarding can resume without archaeology.

## Isolation rules

These are not style preferences. Breaking one puts a client's confidential material somewhere it cannot be recalled from.

1. One private repository per client. A client workspace never shares a repository with another client, with the public engine, or with the provider's own marketing or website code.
2. The public engine never contains a client workspace. `scripts/new_client.py` refuses to write inside this checkout.
3. Skills receive an explicit workspace manifest path on every run. There is no default client. If the workspace is ambiguous, stop and ask.
4. A batch carries exactly one `client_id`. The candidate validator rejects a mixed batch.

## Step 1: Create the private workspace

Run from the engine checkout, writing to a directory outside it:

```sh
python3 scripts/new_client.py \
  --client-id example-client \
  --display-name "Example Client" \
  --destination ~/clients \
  --git-init
```

This copies `templates/client-workspace/` and stamps the client identity into the manifest. Produces: `~/clients/example-client/`.

Create the remote as a **private** repository and push. The workspace holds client transcripts, research, and strategy, so it must never be public.

## Step 2: Complete the manifest

Open `content-system.yaml` and replace every placeholder. The manifest is the routing source of truth, so an unfilled field becomes a guess later.

Required decisions:

- the 90-day objective, its success metric, and its target value
- four content pillars, each with a stated purpose
- the cadence cycle and the focus of each day
- the CTA ladder, its destinations, and whether each destination is actually live
- the approval gate: `required_before`, who approves, and where the record is written
- `sources.approved_recording_ids`, the exact recordings this workspace expects
- `research_sources`, with an honest status for each: connected, not_connected, export_required, optional, or unavailable
- fatigue rules: lookback window and reuse limits

An unavailable CTA destination is recorded as unavailable. Do not point a call to action at a page that does not exist yet.

## Step 3: Run the foundation intake once

The foundation is the one-time client understanding that every later batch draws on. Inspect the authorized workspace and any connected sources first, extract what can be evidenced, and ask the client only for what cannot be found safely.

The client approves the completed foundation before the topic bank becomes the baseline. Produces: the approved foundation and the persistent topic bank.

Do not rerun full foundation research per batch. Reopen it when the ICP, positioning, offer, pillars, proof boundaries, or CTA strategy changes, at a scheduled strategic review, or when the topic bank can no longer support a complete batch.

## Step 4: Confirm source access

Record which research and transcript sources are actually connected. Report anything not connected, export-required, stale, or missing before scoring rather than after.

Never describe an unavailable source as checked. Transcript relevance is not evidence of search demand.

## Step 5: Mine the first batch and return an approval board

Run the `transcript-to-content` skill with an explicit manifest path. It returns a ranked approval board with a decision required per candidate.

Validate before the board goes to the client:

```sh
npm run validate:client -- ~/clients/example-client/content-system.yaml
```

That checks the manifest, resolves every declared asset, and confirms the transcript index matches the workspace's declared `sources.approved_recording_ids`.

Produces: the approval board. Approval of a topic authorizes Recording Cards. It does not authorize recording, editing, rendering, scheduling, publishing, or any external write.

## Step 6: Run the recording session

Recording Cards are the input to the live session with the client. The provider runs the call, asks the card questions, and coaches delivery. The speaker sees plain language only: no scores, no evidence limits, no internal strategy terminology.

Produces: the raw recording, and the post-interview editor package once the recording transcript is processed and validated.

## Step 7: Record the outcome

Write verified results to `history/content-history.csv`. Keep proposed and verified strictly separate. A proposal that was never published is not a result, and a published post with no measured outcome is not a success.

## Recurring cycle

Per cycle, per client: batch signal scan, mine, approval board, client approval, Recording Cards, recording session, editor package, history update.

The software scales cleanly across clients. The recording session and the review do not, because both consume provider hours. Capacity is set by those two steps, not by the pipeline.

## Offboarding

The client workspace repository is the client's record. Transfer or delete it on exit. The engine keeps no client material, so nothing needs to be scrubbed from this repository.
