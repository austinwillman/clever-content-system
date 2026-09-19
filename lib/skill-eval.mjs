import { isAbsolute, normalize, resolve, sep } from "node:path";

const SUPPORTED_OPERATORS = new Set([
  "equals",
  "excludes_all",
  "includes_any",
  "non_empty",
  "starts_with",
]);

function requireString(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${label} must be a non-empty string`);
  }
}

function isSafeRelativePath(path) {
  if (typeof path !== "string" || path.trim() === "" || isAbsolute(path)) return false;
  const normalized = normalize(path);
  return normalized !== ".." && !normalized.startsWith(`..${sep}`);
}

export function validateEvalConfig(config) {
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("eval config must be an object");
  }

  requireString(config.name, "eval name");
  requireString(config.skill, "eval skill");
  if (!Array.isArray(config.cases) || config.cases.length === 0) {
    throw new Error("eval config must include at least one case");
  }

  const ids = new Set();
  for (const evalCase of config.cases) {
    requireString(evalCase?.id, "eval case id");
    requireString(evalCase?.prompt, `eval case ${evalCase?.id ?? "unknown"} prompt`);
    if (ids.has(evalCase.id)) throw new Error(`duplicate eval case id: ${evalCase.id}`);
    ids.add(evalCase.id);

    if (!Array.isArray(evalCase.assertions)) {
      throw new Error(`eval case ${evalCase.id} assertions must be an array`);
    }
    for (const assertion of evalCase.assertions) {
      requireString(assertion?.path, `eval case ${evalCase.id} assertion path`);
      if (!SUPPORTED_OPERATORS.has(assertion?.operator)) {
        throw new Error(`unsupported assertion operator: ${assertion?.operator}`);
      }
    }
  }

  for (const path of Object.keys(config.workspaceFiles ?? {})) {
    if (!isSafeRelativePath(path)) throw new Error(`unsafe eval workspace file path: ${path}`);
  }

  return config;
}

function valueAtPath(subject, path) {
  return path.split(".").reduce(
    (current, part) => current != null ? current[part] : undefined,
    subject,
  );
}

function normalizedText(value) {
  if (Array.isArray(value)) return value.join("\n").toLowerCase();
  return String(value ?? "").toLowerCase();
}

function runAssertion(actual, assertion) {
  if (assertion.operator === "non_empty") {
    if (Array.isArray(actual)) return actual.length > 0;
    return typeof actual === "string" && actual.trim().length > 0;
  }
  if (assertion.operator === "equals") return actual === assertion.value;
  if (assertion.operator === "starts_with") {
    return typeof actual === "string" && actual.trimStart().startsWith(assertion.value);
  }

  const text = normalizedText(actual);
  const values = assertion.values.map((value) => String(value).toLowerCase());
  if (assertion.operator === "includes_any") {
    return values.some((value) => text.includes(value));
  }
  if (assertion.operator === "excludes_all") {
    return values.every((value) => !text.includes(value));
  }
  return false;
}

export function evaluateDeterministic(response, assertions) {
  const checks = assertions.map((assertion) => {
    const actual = valueAtPath(response, assertion.path);
    return {
      path: assertion.path,
      operator: assertion.operator,
      description: assertion.description ?? undefined,
      passed: runAssertion(actual, assertion),
    };
  });
  return {
    passed: checks.filter((check) => check.passed).length,
    total: checks.length,
    checks,
  };
}

export function buildSkillToggleOverride(skillPath, enabled) {
  requireString(skillPath, "skill path");
  if (typeof enabled !== "boolean") throw new Error("skill enabled state must be boolean");
  return `skills.config=[{ path = ${JSON.stringify(resolve(skillPath))}, enabled = ${enabled} }]`;
}

function average(values) {
  if (values.length === 0) return 0;
  return Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 100) / 100;
}

export function summarizeResults(results) {
  const summary = {
    cases: results.length,
    baseline: { deterministicPassed: 0, deterministicTotal: 0, averageRubric: 0 },
    skill: { deterministicPassed: 0, deterministicTotal: 0, averageRubric: 0 },
    wins: { baseline: 0, skill: 0, tie: 0 },
  };

  const baselineRubrics = [];
  const skillRubrics = [];
  for (const result of results) {
    summary.baseline.deterministicPassed += result.baseline.deterministic.passed;
    summary.baseline.deterministicTotal += result.baseline.deterministic.total;
    summary.skill.deterministicPassed += result.skill.deterministic.passed;
    summary.skill.deterministicTotal += result.skill.deterministic.total;
    baselineRubrics.push(result.baseline.rubricScore);
    skillRubrics.push(result.skill.rubricScore);
    summary.wins[result.winner] += 1;
  }
  summary.baseline.averageRubric = average(baselineRubrics);
  summary.skill.averageRubric = average(skillRubrics);
  return summary;
}

export function interpolatePrompt(prompt, variables) {
  return prompt.replace(/\{\{([a-z_]+)\}\}/g, (match, key) => (
    Object.hasOwn(variables, key) ? variables[key] : match
  ));
}
