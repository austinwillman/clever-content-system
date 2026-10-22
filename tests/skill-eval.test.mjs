import assert from "node:assert/strict";
import test from "node:test";
import {
  buildSkillToggleOverride,
  evaluateDeterministic,
  summarizeResults,
  validateEvalConfig,
} from "../lib/skill-eval.mjs";

test("config validation rejects duplicate case ids before spending model calls", () => {
  assert.throws(
    () => validateEvalConfig({
      name: "Duplicate fixture",
      skill: "social-post-copy",
      cases: [
        { id: "same", prompt: "First", assertions: [] },
        { id: "same", prompt: "Second", assertions: [] },
      ],
    }),
    /duplicate eval case id: same/,
  );
});

test("config validation rejects eval fixture files that escape the isolated workspace", () => {
  assert.throws(
    () => validateEvalConfig({
      name: "Unsafe fixture",
      skill: "social-post-copy",
      workspaceFiles: { "../private.txt": "must not escape" },
      cases: [{ id: "safe-id", prompt: "Write a draft", assertions: [] }],
    }),
    /unsafe eval workspace file path: \.\.\/private\.txt/,
  );
});

test("deterministic checks catch ownership inflation and preserve exact openings", () => {
  const result = evaluateDeterministic(
    {
      post: "The bottleneck was never the software. I want to test a weekly review.",
      limitations: [],
      authorization: { status: "draft_only" },
    },
    [
      { path: "post", operator: "starts_with", value: "The bottleneck was never the software." },
      { path: "post", operator: "includes_any", values: ["I want", "could"] },
      { path: "post", operator: "excludes_all", values: ["I use", "saved me"] },
      { path: "authorization.status", operator: "equals", value: "draft_only" },
    ],
  );

  assert.equal(result.passed, 4);
  assert.equal(result.total, 4);
  assert.equal(result.checks.every((check) => check.passed), true);
});

test("deterministic checks fail when a missing-source case hides its limitation", () => {
  const result = evaluateDeterministic(
    { post: "A confident but invented ending.", limitations: [] },
    [{ path: "limitations", operator: "non_empty" }],
  );

  assert.equal(result.passed, 0);
  assert.equal(result.checks[0].passed, false);
});

test("summary reports separate baseline and skill scores instead of pooling them", () => {
  const summary = summarizeResults([
    {
      baseline: { deterministic: { passed: 1, total: 2 }, rubricScore: 5 },
      skill: { deterministic: { passed: 2, total: 2 }, rubricScore: 9 },
      winner: "skill",
    },
    {
      baseline: { deterministic: { passed: 2, total: 2 }, rubricScore: 7 },
      skill: { deterministic: { passed: 2, total: 2 }, rubricScore: 7 },
      winner: "tie",
    },
  ]);

  assert.deepEqual(summary, {
    cases: 2,
    baseline: { deterministicPassed: 3, deterministicTotal: 4, averageRubric: 6 },
    skill: { deterministicPassed: 4, deterministicTotal: 4, averageRubric: 8 },
    wins: { baseline: 0, skill: 1, tie: 1 },
  });
});

test("skill toggle override quotes the resolved path and selected state", () => {
  assert.equal(
    buildSkillToggleOverride("/tmp/skills/social-post-copy/SKILL.md", false),
    'skills.config=[{ path = "/tmp/skills/social-post-copy/SKILL.md", enabled = false }]',
  );
});
