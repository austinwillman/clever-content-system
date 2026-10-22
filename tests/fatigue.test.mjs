import assert from "node:assert/strict";
import test from "node:test";
import { parseCsv } from "../lib/csv.mjs";
import { contentFingerprint, findFatigueConflicts } from "../lib/fatigue.mjs";

const candidateTopic = {
  pillar: "get-chosen",
  owner_problem: "The owner keeps redesigning instead of testing the offer.",
  unique_pov: "A beautiful amplifier cannot fix an unvalidated signal.",
  hook_mechanism: "direct-question",
  format: "video",
  primary_cta_class: "reach",
};

test("flags a matching fingerprint inside the 45-day cooldown", () => {
  const candidate = { ...candidateTopic, publish_date: "2026-08-20" };
  const history = [{ ...candidate, publish_date: "2026-08-01" }];
  assert.equal(contentFingerprint(candidate), contentFingerprint(history[0]));
  assert.equal(findFatigueConflicts(candidate, history, { topic_cooldown_days: 45 }).length, 1);
});

test("uses the default 45-day cooldown when no cooldown rule is supplied", () => {
  const candidate = { ...candidateTopic, publish_date: "2026-08-20" };
  const history = [{ ...candidate, publish_date: "2026-08-01" }];
  assert.equal(findFatigueConflicts(candidate, history, {}).length, 1);
});

test("parses quoted commas, doubled quotes, and empty optional cells", () => {
  assert.deepEqual(parseCsv('title,notes,optional\n"Founders, listen","Say ""no""",\n'), [
    { title: "Founders, listen", notes: 'Say "no"', optional: "" },
  ]);
});

test("rejects CSV rows with a different cell count from the header", () => {
  assert.throws(() => parseCsv("one,two\nvalue\n"), /CSV row 2 has 1 cells, expected 2/);
});

test("ignores matching fingerprints outside the cooldown", () => {
  const candidate = { ...candidateTopic, publish_date: "2026-08-20" };
  const history = [{ ...candidate, publish_date: "2026-06-01" }];
  assert.deepEqual(findFatigueConflicts(candidate, history, { topic_cooldown_days: 45 }), []);
});

test("reads published_at from content-history rows", () => {
  const candidate = { ...candidateTopic, publish_date: "2026-08-20" };
  const history = [{ ...candidateTopic, published_at: "2026-08-01" }];
  assert.equal(findFatigueConflicts(candidate, history, { topic_cooldown_days: 45 }).length, 1);
});

test("checks an unscheduled candidate against an explicit evaluation date", () => {
  const history = [{ ...candidateTopic, published_at: "2026-08-01" }];
  assert.equal(
    findFatigueConflicts(candidateTopic, history, { topic_cooldown_days: 45 }, "2026-08-20").length,
    1,
  );
});
