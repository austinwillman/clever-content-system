import assert from "node:assert/strict";
import test from "node:test";
import { validateTopic, validateWeeklyBatch } from "../lib/topic.mjs";

export const validTopic = {
  topic_id: "fixture-topic",
  approval_status: "pending_topic_approval",
  title: "Your website is not the first problem",
  pillar: "teach",
  client_id: "example-client",
  strategic_initiative: "trusted-expertise",
  owner_problem: "The owner keeps redesigning instead of testing the offer.",
  founder_experience: "They feel productive while avoiding market rejection.",
  owner_outcome: "They test the offer before spending more on presentation.",
  source_excerpt: "Is it a form of sophisticated procrastination?",
  source_recording_id: "fixture-recording",
  source_timestamp_ms: 4200000,
  objection: "My website has to look right first.",
  confusion: "They confuse a polished asset with market validation.",
  frustration: "The rebuild consumes time without creating evidence.",
  aha: "The market should shape the website, not the reverse.",
  unique_pov: "A beautiful amplifier cannot fix an unvalidated signal.",
  demand_evidence_ids: ["demand-001"],
  authority_signal: "Validation before amplification is a discussable framework.",
  raw_hook_material: ["How many times have you rebuilt the site without testing the offer?"],
  not_about: "Website design preferences",
  really_about: "Using polish to postpone market feedback",
  recording_prompt: "Tell the story of recognizing sophisticated procrastination.",
  search_target: {
    target_id: "search-fixture-topic",
    primary_query: "when should I redesign my website",
    spoken_phrase: "when to redesign your website",
    intent: "informational",
    validation_status: "provisional",
    supporting_terms: ["website redesign", "customer feedback"],
  },
  hook_mechanism: "owner-self-recognition",
  format: "video",
  primary_cta_class: "engage",
  cta_destination: "comment",
  cta_destination_available: true,
  fatigue_status: "unknown",
  trend_evidence_ids: [],
  content_history_conflicts: [],
  ownership_confidence: "high",
};

const clientManifest = {
  client_id: "example-client",
  pillars: [
    { id: "teach", label: "Teach" },
    { id: "trust", label: "Trust" },
  ],
  content_output: { allowed_formats: ["video"], batch_size: 4 },
  initiative: { id: "trusted-expertise" },
  fatigue: {
    max_hook_uses_per_seven_posts: 2,
    hook_frequency_window_posts: 7,
    max_consecutive_same_cta: 2,
  },
  cta_classes: ["engage", "book"],
  cta_destinations: {
    comment: { class: "engage", available: true },
    consultation: { class: "book", available: true },
    newsletter: { class: "engage", available: false },
  },
};

function topic(topicId, overrides = {}) {
  return {
    ...validTopic,
    topic_id: topicId,
    hook_mechanism: `mechanism-${topicId}`,
    ...overrides,
  };
}

function validBatch() {
  return [
    topic("one"),
    topic("two", { primary_cta_class: "book", cta_destination: "consultation" }),
    topic("three"),
    topic("four", { primary_cta_class: "book", cta_destination: "consultation" }),
  ];
}

test("validates an unscheduled topic against client-defined inputs", () => {
  assert.deepEqual(validateTopic(validTopic, clientManifest), []);
});

test("rejects a topic without founder experience", () => {
  const errors = validateTopic({ ...validTopic, founder_experience: "" }, clientManifest);
  assert.ok(errors.includes("founder_experience is required"));
});

test("requires a usable search target before a topic can become a recording brief", () => {
  const missing = validateTopic({
    ...validTopic,
    approval_status: "approved_for_recording",
    search_target: undefined,
  }, clientManifest);
  assert.ok(missing.includes("search_target is required"));

  const invalid = validateTopic({
    ...validTopic,
    approval_status: "approved_for_recording",
    search_target: {
      target_id: "",
      primary_query: "",
      spoken_phrase: "",
      intent: "informational",
      validation_status: "guessed",
      supporting_terms: "website redesign",
    },
  }, clientManifest);
  assert.ok(invalid.includes("search_target.target_id is required"));
  assert.ok(invalid.includes("search_target.primary_query is required"));
  assert.ok(invalid.includes("search_target.spoken_phrase is required"));
  assert.ok(invalid.includes("search_target.validation_status must be one of validated, provisional, qualitative_only, unavailable"));
  assert.ok(invalid.includes("search_target.supporting_terms must be an array"));
});

test("allows a pending topic to reach approval before search-target research", () => {
  const errors = validateTopic({ ...validTopic, search_target: undefined }, clientManifest);
  assert.deepEqual(errors, []);
});

test("rejects reader-facing em and en dashes", () => {
  const errors = validateTopic({ ...validTopic, title: "A polished site \u2014 without proof" }, clientManifest);
  assert.ok(errors.includes("title must not contain em dash or en dash"));
});

test("rejects a pillar or format outside the client manifest", () => {
  const errors = validateTopic({ ...validTopic, pillar: "unknown", format: "carousel" }, clientManifest);
  assert.ok(errors.includes("pillar must be one of teach, trust"));
  assert.ok(errors.includes("format must be one of video"));
});

test("rejects unavailable, missing, and class-mismatched client CTAs", () => {
  assert.ok(
    validateTopic({ ...validTopic, cta_destination: "newsletter" }, clientManifest)
      .includes("CTA destination newsletter is unavailable"),
  );
  assert.ok(
    validateTopic({ ...validTopic, cta_destination: "missing" }, clientManifest)
      .includes("CTA destination missing is not declared in the manifest"),
  );
  assert.ok(
    validateTopic({ ...validTopic, primary_cta_class: "book" }, clientManifest)
      .includes("CTA destination comment must use class book"),
  );
});

test("validates a four-topic scheduling-neutral batch", () => {
  assert.deepEqual(validateWeeklyBatch(validBatch(), clientManifest), []);
});

test("requires the manifest batch size and unique topic ids", () => {
  const topics = validBatch().slice(0, 3);
  topics[2].topic_id = "one";
  const errors = validateWeeklyBatch(topics, clientManifest);
  assert.ok(errors.includes("content batch must contain exactly 4 topics"));
  assert.ok(errors.includes("content batch must contain unique topic ids"));
});

test("requires every topic to match the active strategic initiative", () => {
  const topics = validBatch();
  topics[2].strategic_initiative = "off-strategy";
  const errors = validateWeeklyBatch(topics, clientManifest);
  assert.ok(errors.includes("three strategic_initiative must equal trusted-expertise"));
});

test("requires unknown fatigue status when content history is unavailable", () => {
  const topics = validBatch().map((item) => ({ ...item, fatigue_status: "clear" }));
  const errors = validateWeeklyBatch(topics, clientManifest);
  for (const item of topics) {
    assert.ok(errors.includes(`${item.topic_id} fatigue_status must be unknown when content history is unavailable`));
  }
});

test("does not infer a CTA publication streak from an unscheduled brief array", () => {
  const topics = validBatch().map((item) => ({
    ...item,
    primary_cta_class: "engage",
    cta_destination: "comment",
  }));
  const errors = validateWeeklyBatch(topics, clientManifest);
  assert.ok(!errors.includes("weekly batch must not contain more than two consecutive identical CTA classes"));
});

test("enforces hook frequency across dated history and unscheduled incoming topics", () => {
  const topics = validBatch();
  topics[0].hook_mechanism = "provocative-question";
  const history = [
    { content_id: "h1", published_at: "2026-08-18", hook_mechanism: "case-study" },
    { content_id: "h2", published_at: "2026-08-19", hook_mechanism: "provocative-question" },
    { content_id: "h3", published_at: "2026-08-20", hook_mechanism: "direct-statement" },
    { content_id: "h4", published_at: "2026-08-21", hook_mechanism: "owner-quote" },
    { content_id: "h5", published_at: "2026-08-22", hook_mechanism: "visible-moment" },
    { content_id: "h6", published_at: "2026-08-23", hook_mechanism: "provocative-question" },
  ];
  const errors = validateWeeklyBatch(topics, clientManifest, history);
  assert.ok(
    errors.includes(
      "weekly batch hook mechanism provocative-question exceeds 2 uses in a rolling 7-post window",
    ),
  );
});
