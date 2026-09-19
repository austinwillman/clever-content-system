#!/usr/bin/env node

import { spawn } from "node:child_process";
import { access, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildSkillToggleOverride,
  evaluateDeterministic,
  interpolatePrompt,
  summarizeResults,
  validateEvalConfig,
} from "../lib/skill-eval.mjs";

function readArgs(args) {
  const options = { dryRun: false };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--dry-run") options.dryRun = true;
    else if (arg === "--config") options.config = args[++index];
    else if (arg === "--limit") options.limit = Number(args[++index]);
    else if (arg === "--output") options.output = args[++index];
    else throw new Error(`unknown argument: ${arg}`);
  }
  return options;
}

async function runProcess(command, args, { cwd, input, timeoutMs }) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(command, args, { cwd, env: process.env, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`${command} timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      clearTimeout(timeout);
      if (code !== 0) {
        reject(new Error(`${command} exited ${code}\n${stderr || stdout}`));
        return;
      }
      resolvePromise({ stdout, stderr });
    });
    child.stdin.end(input);
  });
}

async function writeWorkspace(root, files) {
  for (const [relativePath, content] of Object.entries(files ?? {})) {
    const outputPath = join(root, relativePath);
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, content, "utf8");
  }
}

function parseStructuredResponse(text, label) {
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`${label} did not return valid structured JSON: ${error.message}\n${text}`);
  }
}

async function runCodex({
  cwd,
  model,
  reasoningEffort,
  outputSchema,
  prompt,
  skillOverride,
  timeoutMs,
}) {
  const outputPath = join(cwd, `response-${crypto.randomUUID()}.json`);
  const args = [
    "exec",
    "--ephemeral",
    "--json",
    "--skip-git-repo-check",
    "--sandbox",
    "read-only",
    "--output-schema",
    outputSchema,
    "--output-last-message",
    outputPath,
    "--model",
    model,
    "-c",
    `model_reasoning_effort=${JSON.stringify(reasoningEffort)}`,
  ];
  if (skillOverride) args.push("-c", skillOverride);
  args.push("-");

  await runProcess("codex", args, { cwd, input: prompt, timeoutMs });
  return parseStructuredResponse(await readFile(outputPath, "utf8"), "Codex run");
}

function targetPrompt(evalCase, manifestPath) {
  return interpolatePrompt(evalCase.prompt, { manifest_path: manifestPath });
}

function graderPrompt(evalCase, outputA, outputB, rubric) {
  return [
    "You are grading two candidate responses to the same social-copy task.",
    "Use only the supplied task, source, constraints, and rubric.",
    "Do not reward confidence, length, or polish when source fidelity fails.",
    "Score each rubric dimension from 0 to 2, then choose a winner or tie.",
    "",
    "RUBRIC",
    ...rubric.map((item) => `- ${item}`),
    "",
    "TASK",
    evalCase.prompt,
    "",
    "OUTPUT A",
    JSON.stringify(outputA, null, 2),
    "",
    "OUTPUT B",
    JSON.stringify(outputB, null, 2),
  ].join("\n");
}

function rubricTotal(grade) {
  return [
    grade.source_fidelity,
    grade.ownership,
    grade.voice,
    grade.instruction_following,
    grade.authorization,
  ].reduce((sum, score) => sum + score, 0);
}

async function main() {
  const options = readArgs(process.argv.slice(2));
  const scriptDirectory = dirname(fileURLToPath(import.meta.url));
  const repositoryRoot = resolve(scriptDirectory, "..");
  const configPath = resolve(repositoryRoot, options.config ?? "evals/social-post-copy/eval.config.json");
  const configDirectory = dirname(configPath);
  const config = validateEvalConfig(JSON.parse(await readFile(configPath, "utf8")));
  const cases = Number.isInteger(options.limit) && options.limit > 0
    ? config.cases.slice(0, options.limit)
    : config.cases;
  const skillPath = join(homedir(), ".codex", "skills", config.skill, "SKILL.md");
  const responseSchema = resolve(configDirectory, config.responseSchema);
  const graderSchema = resolve(configDirectory, config.graderSchema);

  if (options.dryRun) {
    console.log(JSON.stringify({
      name: config.name,
      skill: config.skill,
      cases: cases.map((item) => item.id),
      targetCalls: cases.length * 2,
      graderCalls: cases.length,
    }, null, 2));
    return;
  }

  await Promise.all([access(skillPath), access(responseSchema), access(graderSchema)]);
  const workspaceRoot = await mkdtemp(join(tmpdir(), "codex-skill-eval-"));
  await writeWorkspace(workspaceRoot, config.workspaceFiles);
  const manifestPath = join(workspaceRoot, config.manifestPath);
  const baselineOverride = buildSkillToggleOverride(skillPath, false);
  const results = [];

  for (const [index, evalCase] of cases.entries()) {
    console.log(`[${index + 1}/${cases.length}] ${evalCase.id}: baseline`);
    const baselineOutput = await runCodex({
      cwd: workspaceRoot,
      model: config.targetModel,
      reasoningEffort: config.targetReasoningEffort,
      outputSchema: responseSchema,
      prompt: targetPrompt(evalCase, manifestPath),
      skillOverride: baselineOverride,
      timeoutMs: config.timeoutMs,
    });

    console.log(`[${index + 1}/${cases.length}] ${evalCase.id}: skill`);
    const skillOutput = await runCodex({
      cwd: workspaceRoot,
      model: config.targetModel,
      reasoningEffort: config.targetReasoningEffort,
      outputSchema: responseSchema,
      prompt: targetPrompt(evalCase, manifestPath),
      timeoutMs: config.timeoutMs,
    });

    const skillIsA = index % 2 === 0;
    const outputA = skillIsA ? skillOutput : baselineOutput;
    const outputB = skillIsA ? baselineOutput : skillOutput;
    console.log(`[${index + 1}/${cases.length}] ${evalCase.id}: grade`);
    const grade = await runCodex({
      cwd: workspaceRoot,
      model: config.graderModel,
      reasoningEffort: config.graderReasoningEffort,
      outputSchema: graderSchema,
      prompt: graderPrompt(evalCase, outputA, outputB, config.rubric),
      skillOverride: baselineOverride,
      timeoutMs: config.timeoutMs,
    });

    const winner = grade.winner === "tie"
      ? "tie"
      : grade.winner === (skillIsA ? "a" : "b") ? "skill" : "baseline";
    results.push({
      id: evalCase.id,
      baseline: {
        output: baselineOutput,
        deterministic: evaluateDeterministic(baselineOutput, evalCase.assertions),
        rubricScore: rubricTotal(skillIsA ? grade.output_b : grade.output_a),
      },
      skill: {
        output: skillOutput,
        deterministic: evaluateDeterministic(skillOutput, evalCase.assertions),
        rubricScore: rubricTotal(skillIsA ? grade.output_a : grade.output_b),
      },
      winner,
      graderReason: grade.reason,
    });
  }

  const report = {
    eval: config.name,
    skill: config.skill,
    createdAt: new Date().toISOString(),
    models: { target: config.targetModel, grader: config.graderModel },
    summary: summarizeResults(results),
    results,
  };
  const defaultOutput = join(repositoryRoot, "eval-results", `${config.skill}-${Date.now()}.json`);
  const outputPath = resolve(repositoryRoot, options.output ?? defaultOutput);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(report.summary, null, 2));
  console.log(`Report: ${outputPath}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
