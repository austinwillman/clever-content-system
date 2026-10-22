# Output Contract

The workflow has three separate outputs: the approval board, post-approval Recording Cards backed by detailed JSON, and the post-interview editor package. Return the approval board before creating Recording Cards. Topic approval does not authorize ClickUp writes.

Scheduling remains the provider's decision. Do not require or assign a weekday or publishing date in a topic or Recording Card.

## Ranked approval board

Lead with `Is this good?`

### Pending approval comparison

Start every pending approval board with a compact comparison. It must surface Topic score, Video Score, Video rationale, CTA, and the explicit choice `Approve / Refine / Reject` for every candidate.

Every candidate includes one concise video rationale grounded in the validated source.

| Rank | Working topic | Pillar | Owner problem | Initiative | Demand and authority | Fatigue | Topic score | Video Score | Video rationale | CTA | Decision needed |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | Plain-language topic, not a final hook | client-defined pillar | Recognizable problem | active initiative | Evidence IDs, limits, and authority signal | clear, review, hold, or unknown | 86 | 91 | Source delivery and story make this founder-led short strong. | client-defined CTA | Approve / Refine / Reject |

The client manifest supplies pillars, `content_output.allowed_formats`, `content_output.batch_size`, CTA classes, CTA destinations, and destination availability. The complete transcript supplies the owner problem, founder experience, outcome, and source evidence. The workflow selects only declared and available client inputs.

Under the table, include only the evidence needed to decide:

1. Business problem, founder experience, and owner outcome
2. Real quote, recording ID, timestamp, speaker, and ownership confidence
3. Objection, confusion, frustration, and aha
4. Unique POV and authority signal
5. Raw hook material, not final hook copy
6. `not_about` and `really_about`
7. Evidence limits, confidentiality risk, and fatigue conflicts

End each candidate with `What do I do next? Approve / Refine / Reject`.

Once the client approves the **configured number of video-eligible approved topics**, create the configured recording-brief batch without asking for another approval. Topic approval does not authorize ClickUp creation, recording the video, editing, rendering, scheduling, publishing, uploading, or any other external action.

## Approval routing

A candidate is video-eligible only when:

1. Its Video Score is at least 65.
2. The complete transcript supports a founder-led recording.
3. No source, ownership, confidentiality, proof, recognition, or fatigue gate fails.
4. The client explicitly approves it.

If approvals are below `content_output.batch_size`, stop and **request more topic approvals**. Do not pad the batch or advance a held, refined, deferred, or rejected topic.

## Search Target gate

Before an approved topic becomes a Recording Card, attach a Search Target supported by the research reference. The detailed JSON keeps the evidence and validation status. The human card shows only the viewer question and the natural phrase to use once when it fits.

Do not call an invented phrase a keyword. `validated` requires attributable query data. `provisional` may use dated search-result or platform-search evidence without volume. `qualitative_only` uses customer or audience language without query evidence. `unavailable` means no defensible search target was found and must be disclosed rather than disguised.

## Recording brief JSON

After approval, create exactly `content_output.batch_size` video records. Every record must pass `validateTopic(topic, manifest)` and belong to an array that passes `validateWeeklyBatch(topics, manifest, historyRows)`. `historyRows` must be the parsed content-history rows from the manifest asset so the configured rolling hook window includes recent published content plus the incoming batch.

```json
{
  "topic_id": "client-batch-01",
  "approval_status": "approved_for_recording",
  "title": "Your website is not the first problem",
  "pillar": "client-defined-pillar",
  "strategic_initiative": "client-defined-initiative",
  "owner_problem": "The owner keeps redesigning instead of testing the offer.",
  "founder_experience": "The redesign feels productive while market feedback feels exposed.",
  "owner_outcome": "The owner tests the offer before investing in more polish.",
  "source_excerpt": "Is it a form of sophisticated procrastination?",
  "source_recording_id": "fixture-recording",
  "source_timestamp_ms": 4200000,
  "objection": "My website has to look right first.",
  "confusion": "Polish is being treated as market validation.",
  "frustration": "The rebuild consumes time without creating evidence.",
  "aha": "The market should shape the website.",
  "unique_pov": "A beautiful amplifier cannot fix an unvalidated signal.",
  "demand_evidence_ids": ["demand-001"],
  "authority_signal": "Validation before amplification is a discussable framework.",
  "raw_hook_material": ["How many times have you rebuilt the site without testing the offer?"],
  "not_about": "Website design preferences",
  "really_about": "Using polish to postpone market feedback",
  "recording_prompt": "Tell the story of recognizing sophisticated procrastination.",
  "search_target": {
    "target_id": "search-client-batch-01",
    "primary_query": "when should I redesign my website",
    "spoken_phrase": "when to redesign your website",
    "intent": "informational",
    "validation_status": "provisional",
    "supporting_terms": ["website redesign", "customer feedback"]
  },
  "hook_mechanism": "owner-self-recognition",
  "format": "video",
  "primary_cta_class": "client-defined-class",
  "cta_destination": "client-defined-destination",
  "cta_destination_available": true,
  "fatigue_status": "unknown",
  "trend_evidence_ids": [],
  "content_history_conflicts": [],
  "ownership_confidence": "high",
  "recording_beat_map": ["Recognition", "Reframe", "Owner outcome"],
  "must_land_ideas": ["The market should shape the site"],
  "improvisation_pockets": ["Add a personal example if it stays source-grounded"],
  "target_duration_seconds": 45,
  "on_screen_direction": "Founder-led direct-to-camera delivery"
}
```

## Human Recording Card

The speaker should see one screen of plain language. Use this order:

1. Simple title and pillar
2. One specific viewer
3. The viewer's question in first-person language
4. One story, scenario, myth, or teardown prompt
5. Three to five short follow-up questions
6. One natural spoken search phrase to use once when it fits
7. One plain-language point of view
8. One natural ending tied to the available client CTA
9. One optional visual or a clear direction to stay on camera

Use the rule: one video, one viewer question, one story or scenario, one clear opinion, and one next step. Target a sixth-grade listening level. Do not show the speaker Topic Score, Video Score, evidence limits, fatigue, ownership confidence, authority labels, or internal strategy terminology. Preserve those fields in JSON.

The client owns the final opening hook unless final hook writing is explicitly requested. A Recording Card is speaking direction, not authorization to render, write to ClickUp, schedule, publish, or upload.

## Post-interview editor package

Create this package only after the complete recording transcript is processed and validated. Same-session hook pickups may be selected during the call, but their final timestamps and body continuity are confirmed here.

```json
{
  "topic_id": "client-batch-01",
  "source_recording_id": "riverside-project-or-recording-id",
  "production_route": "hybrid",
  "selected_hook": {
    "text": "The approved pickup wording",
    "take_id": "topic-01-hook-b",
    "timestamp_ms": 120000,
    "template_id": "client-hook-004",
    "evidence_grade": "validated",
    "body_continuity": "pass"
  },
  "body_edit": {
    "in_ms": 180000,
    "out_ms": 232000,
    "must_keep": ["The client-owned reframe", "The owner outcome"],
    "removable_context": ["Repeated setup"]
  },
  "creative_direction": "Direct and conversational. Preserve the pause before the reframe.",
  "b_roll_map": [
    {
      "in_ms": 196000,
      "out_ms": 202000,
      "asset": "Attributed dashboard crop",
      "purpose": "prove",
      "framing": "Crop to the single metric being discussed",
      "on_screen_text": "",
      "rights_status": "client_owned",
      "fallback": "Stay on the client"
    }
  ],
  "green_screen": {
    "enabled": false,
    "source_asset": "",
    "source_url": "",
    "rights_status": "not_required",
    "spoken_line": "",
    "placement": "",
    "fallback": "Talking head"
  },
  "caption_direction": "Accurate sentence-case captions with safe margins.",
  "on_screen_text": [],
  "cta": {
    "class": "client-defined-class",
    "destination": "client-defined-destination"
  },
  "claim_warnings": [],
  "do_not_overproduce": ["Do not add decorative stock footage", "Do not remove the human pause"]
}
```

Every B-roll or green-screen instruction must prove, explain, orient, or reset attention. Include a fallback for every external asset. The package does not authorize editing, rendering, scheduling, publishing, or uploading.
