import assert from "node:assert/strict";
import test from "node:test";
import { validateManifest } from "../lib/config.mjs";
import { validateWeeklyBatch } from "../lib/topic.mjs";
import { validTopic } from "./topic.test.mjs";

const clientManifest = {
  client_id: "example-client",
  pillars: [{ id: "teach", label: "Teach" }, { id: "trust", label: "Trust" }],
  content_output: { allowed_formats: ["video"], batch_size: 2 },
  initiative: { id: "trusted-expertise" },
  fatigue: { max_hook_uses_per_seven_posts: 2, hook_frequency_window_posts: 7 },
  cta_classes: ["engage", "book"],
  cta_destinations: {
    comment: { class: "engage", available: true },
    consultation: { class: "book", available: true },
  },
};

function topic(topicId, overrides = {}) {
  return { ...validTopic, topic_id: topicId, hook_mechanism: topicId, ...overrides };
}

function batch(overrides = []) {
  return [topic("topic-1", overrides[0] ?? {}), topic("topic-2", overrides[1] ?? {})];
}

test("a batch belonging entirely to the workspace client passes isolation", () => {
  const errors = validateWeeklyBatch(batch(), clientManifest).filter(
    (error) => error.includes("client_id"),
  );
  assert.deepEqual(errors, []);
});

test("a topic from another client cannot enter the batch", () => {
  const errors = validateWeeklyBatch(
    batch([{}, { client_id: "other-client" }]),
    clientManifest,
  );
  assert.ok(
    errors.includes("topic-2 client_id other-client does not belong to workspace example-client"),
    errors.join(" | "),
  );
});

test("a topic without a client_id cannot enter the batch", () => {
  const errors = validateWeeklyBatch(batch([{}, { client_id: undefined }]), clientManifest);
  assert.ok(errors.includes("topic-2 client_id is required"), errors.join(" | "));
});

test("manifest requires an approval gate", () => {
  const errors = validateManifest({ client_id: "example-client" });
  assert.ok(errors.includes("approval_gate is required"), errors.join(" | "));
});

test("approval gate rejects an undeclared stage and empty fields", () => {
  const errors = validateManifest({
    client_id: "example-client",
    approval_gate: { required_before: "whenever", approved_by: "  ", record_location: "" },
  });
  assert.ok(
    errors.includes("approval_gate.required_before must be one of production, distribution"),
    errors.join(" | "),
  );
  assert.ok(errors.includes("approval_gate.approved_by is required"), errors.join(" | "));
  assert.ok(errors.includes("approval_gate.record_location is required"), errors.join(" | "));
});

test("a valid approval gate raises no approval errors", () => {
  const errors = validateManifest({
    client_id: "example-client",
    approval_gate: {
      required_before: "production",
      approved_by: "example-approver",
      record_location: "approvals/approval-record.md",
    },
  }).filter((error) => error.startsWith("approval_gate"));
  assert.deepEqual(errors, []);
});
