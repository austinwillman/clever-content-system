import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

test("transcript skill contains every mandatory gate and approval boundary", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  for (const phrase of [
    "Load the client manifest",
    "Full-transcript validation gate",
    "Five-second founder recognition",
    "business problem",
    "founder experience",
    "owner outcome",
    "Demand evidence",
    "Fatigue fingerprint",
    "The client owner owns the final hook",
    "Do not write to ClickUp before explicit topic approval",
  ]) assert.ok(skill.includes(phrase), `missing contract phrase: ${phrase}`);
});

test("transcript skill separates one-time foundation research from batch signal scans", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const research = await readFile(
    "skills/transcript-to-content/references/client-foundation-and-research.md",
    "utf8",
  );
  for (const phrase of [
    "Client foundation intake happens once",
    "persistent topic bank",
    "abbreviated batch signal scan",
    "ask only for answers that cannot be found safely",
  ]) {
    assert.ok(`${skill}\n${research}`.includes(phrase), `missing foundation phrase: ${phrase}`);
  }
});

test("transcript skill supports same-session hooks and post-interview editor direction", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const production = await readFile(
    "skills/transcript-to-content/references/live-hooks-and-production.md",
    "utf8",
  );
  const output = await readFile(
    "skills/transcript-to-content/references/output-contract.md",
    "utf8",
  );
  for (const phrase of [
    "hook-to-body continuity",
    "evidence grade",
    "green-screen",
    "B-roll map",
    "do_not_overproduce",
  ]) {
    assert.ok(`${skill}\n${production}\n${output}`.includes(phrase), `missing production phrase: ${phrase}`);
  }
});

test("commercial runbook declares tools, fallbacks, intake extraction, and six statuses", async () => {
  const runbook = await readFile("docs/commercial-setup.md", "utf8");
  for (const phrase of [
    "Required software",
    "Research and intake tools",
    "Fallback",
    "Self-service intake with Codex or Claude Code",
    "Foundation research and validation",
    "Persistent topic bank",
    "ClickUp statuses",
    "Ready to Record",
    "Scheduled",
  ]) assert.ok(runbook.includes(phrase), `commercial runbook missing phrase: ${phrase}`);
  assert.equal(
    [...runbook.matchAll(/^\d\. `(?:Ready to Record|Recorded|In Production|Client Review|Approved|Scheduled)`$/gm)].length,
    6,
  );
});

test("transcript skill uses the manifest-defined video-only approval threshold", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const output = await readFile("skills/transcript-to-content/references/output-contract.md", "utf8");
  for (const phrase of [
    "configured number of video-eligible approved topics",
    "content_output.batch_size",
    "request more topic approvals",
    "Video Score",
    "video rationale",
  ]) {
    assert.ok(skill.includes(phrase), `skill missing routing phrase: ${phrase}`);
    assert.ok(output.includes(phrase), `output contract missing routing phrase: ${phrase}`);
  }
  assert.doesNotMatch(skill, /score static image|carousel fit score|all three format scores/i);
  assert.doesNotMatch(output, /\| Image \||\| Carousel \||all three format scores/i);
});

test("output contract requires a scannable pending approval comparison", async () => {
  const output = await readFile("skills/transcript-to-content/references/output-contract.md", "utf8");
  for (const phrase of [
    "Pending approval comparison",
    "Topic score",
    "Video Score",
    "Video rationale",
    "Approve / Refine / Reject",
  ]) assert.ok(output.includes(phrase), `output contract missing comparison phrase: ${phrase}`);
});

test("recording brief contract leaves scheduling to the provider", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const output = await readFile("skills/transcript-to-content/references/output-contract.md", "utf8");
  for (const contract of [skill, output]) {
    assert.ok(contract.includes("Scheduling remains the provider's decision"));
    assert.doesNotMatch(contract, /calendar_day|publish_date|aligned to the manifest's six calendar slots/);
  }
});

test("topic approval creates recording briefs without authorizing external actions", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const output = await readFile("skills/transcript-to-content/references/output-contract.md", "utf8");
  for (const contract of [skill, output]) {
    assert.ok(contract.includes("without asking for another approval"));
    assert.ok(contract.includes(
      "does not authorize ClickUp creation, recording the video, editing, rendering, scheduling, publishing, uploading, or any other external action",
    ));
  }
  assert.doesNotMatch(output, /does not authorize recording-brief production/i);
});

test("transcript contract passes parsed content history into weekly hook validation", async () => {
  const skill = await readFile("skills/transcript-to-content/SKILL.md", "utf8");
  const output = await readFile("skills/transcript-to-content/references/output-contract.md", "utf8");
  for (const phrase of [
    "parsed content-history rows",
    "rolling hook window",
    "validateWeeklyBatch(topics, manifest, historyRows)",
  ]) {
    assert.ok(skill.includes(phrase), `skill missing history phrase: ${phrase}`);
    assert.ok(output.includes(phrase), `output contract missing history phrase: ${phrase}`);
  }
});

test("trend skill distinguishes evidence from inference and refuses copying", async () => {
  const skill = await readFile("skills/trend-to-fit/SKILL.md", "utf8");
  for (const phrase of [
    "Observed evidence",
    "Inference",
    "Views are not conversion proof",
    "Do not copy",
    "Require a client-owned POV",
    "Check content history",
    "expiration",
  ]) assert.ok(skill.includes(phrase), `missing trend contract phrase: ${phrase}`);
});

test("trend score reference preserves the exact rubric, thresholds, and post-score fatigue gate", async () => {
  const score = await readFile("skills/trend-to-fit/references/trend-score.md", "utf8");
  const expectedRubric = [
    ["ICP problem match", 15],
    ["Pillar match", 10],
    ["Business initiative match", 10],
    ["Client-owned POV strength", 15],
    ["Founder recognition", 15],
    ["Authority signal", 10],
    ["Evidence quality", 10],
    ["Freshness", 5],
    ["Format suitability", 5],
    ["CTA compatibility", 5],
  ];
  const rubric = [...score.matchAll(/^\| ([^|]+?) \| (\d+) \|/gm)]
    .map((match) => [match[1].trim(), Number(match[2])])
    .slice(0, expectedRubric.length);

  assert.deepEqual(rubric, expectedRubric);
  assert.equal(rubric.reduce((total, [, points]) => total + points, 0), 100);
  for (const threshold of [
    "90 to 100: `flagship-fit`",
    "80 to 89: `strong`",
    "70 to 79: `viable`",
    "Below 70: `reject`",
  ]) assert.ok(score.includes(threshold), `missing trend threshold: ${threshold}`);
  assert.ok(score.indexOf("## Fatigue post-score gate") > score.indexOf("## Decision bands and rejection floor"));
  assert.match(score, /Fatigue is not part of the 100 points\. Apply it after the numeric score/);
});
