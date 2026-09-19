import assert from "node:assert/strict";
import test from "node:test";
import { access, mkdtemp, mkdir, readFile, realpath, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, parse } from "node:path";
import { runSyncCli, syncSkills } from "../scripts/sync-skills.mjs";

async function makeTemporaryRoot(prefix) {
  return realpath(await mkdtemp(join(tmpdir(), prefix)));
}

test("syncs known skill files to both roots without deleting unrelated files", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-");
  const codexRoot = join(root, "codex");
  const claudeRoot = join(root, "claude");
  const unrelatedPath = join(codexRoot, "transcript-to-content", "user-notes.md");

  await mkdir(join(codexRoot, "transcript-to-content"), { recursive: true });
  await writeFile(unrelatedPath, "preserve me\n");

  const result = await syncSkills({ codexRoot, claudeRoot, mode: "install" });

  assert.deepEqual(result.skills.sort(), [
    "intent-drift-audit",
    "kallaway-hooks",
    "social-post-copy",
    "transcript-to-content",
    "trend-to-fit",
  ]);
  assert.match(
    await readFile(join(codexRoot, "intent-drift-audit", "SKILL.md"), "utf8"),
    /name: intent-drift-audit/,
  );
  assert.equal(await readFile(join(codexRoot, "social-post-copy", "SKILL.md"), "utf8"), await readFile(join(claudeRoot, "social-post-copy", "SKILL.md"), "utf8"));
  assert.match(await readFile(join(codexRoot, "kallaway-hooks", "SKILL.md"), "utf8"), /name: kallaway-hooks/);
  assert.match(await readFile(join(codexRoot, "transcript-to-content", "SKILL.md"), "utf8"), /name: transcript-to-content/);
  assert.match(await readFile(join(claudeRoot, "trend-to-fit", "SKILL.md"), "utf8"), /name: trend-to-fit/);
  assert.equal(await readFile(unrelatedPath, "utf8"), "preserve me\n");
});

test("check mode reports known-file drift and ignores unrelated files", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-check-");
  const codexRoot = join(root, "codex");
  const claudeRoot = join(root, "claude");

  await syncSkills({ codexRoot, claudeRoot, mode: "install" });
  await writeFile(join(claudeRoot, "trend-to-fit", "SKILL.md"), "drifted\n");
  await writeFile(join(codexRoot, "transcript-to-content", "local-only.md"), "ignored\n");

  const result = await syncSkills({ codexRoot, claudeRoot, mode: "check" });

  assert.deepEqual(result.drift, ["claude/trend-to-fit/SKILL.md: differs"]);
});

test("rejects a filesystem root as an unsafe skill root", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-broad-root-");

  await assert.rejects(
    syncSkills({
      codexRoot: parse(root).root,
      claudeRoot: join(root, "claude"),
      mode: "check",
    }),
    /unsafe codex skill root: filesystem root is too broad/,
  );
});

test("refuses to install through a symlinked target path component", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-symlink-");
  const codexRoot = join(root, "codex");
  const claudeRoot = join(root, "claude");
  const outsideRoot = join(root, "outside");

  await mkdir(codexRoot, { recursive: true });
  await mkdir(outsideRoot, { recursive: true });
  await symlink(outsideRoot, join(codexRoot, "transcript-to-content"), "dir");

  await assert.rejects(
    syncSkills({ codexRoot, claudeRoot, mode: "install" }),
    /unsafe symlink in codex target path: .*transcript-to-content/,
  );
  await assert.rejects(access(join(outsideRoot, "SKILL.md")), { code: "ENOENT" });
});

test("refuses a symlinked ancestor above the configured target root", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-parent-symlink-");
  const outsideRoot = join(root, "outside");
  const linkedParent = join(root, "linked-parent");

  await mkdir(outsideRoot, { recursive: true });
  await symlink(outsideRoot, linkedParent, "dir");

  await assert.rejects(
    syncSkills({
      codexRoot: join(linkedParent, "codex"),
      claudeRoot: join(root, "claude"),
      mode: "install",
    }),
    /unsafe symlink in codex target path: .*linked-parent/,
  );
  await assert.rejects(
    access(join(outsideRoot, "codex", "transcript-to-content", "SKILL.md")),
    { code: "ENOENT" },
  );
});

test("rejects a directory at a final file path before writing earlier targets", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-final-directory-");
  const codexRoot = join(root, "codex");
  const claudeRoot = join(root, "claude");
  const blockedTarget = join(claudeRoot, "trend-to-fit", "SKILL.md");
  const earlierTarget = join(
    codexRoot,
    "transcript-to-content",
    "references",
    "output-contract.md",
  );

  await mkdir(blockedTarget, { recursive: true });

  await assert.rejects(syncSkills({ codexRoot, claudeRoot, mode: "install" }));
  await assert.rejects(access(earlierTarget), { code: "ENOENT" });
});

test("CLI check reports missing files and returns a nonzero exit code", async () => {
  const root = await makeTemporaryRoot("wv-content-skills-cli-");
  const stdout = [];
  const stderr = [];

  const exitCode = await runSyncCli({
    args: ["--check"],
    codexRoot: join(root, "codex"),
    claudeRoot: join(root, "claude"),
    stdout: (message) => stdout.push(message),
    stderr: (message) => stderr.push(message),
  });

  assert.equal(exitCode, 1);
  assert.deepEqual(stdout, []);
  assert.match(stderr.join("\n"), /Skill drift detected:/);
  assert.match(stderr.join("\n"), /codex\/transcript-to-content\/SKILL\.md: missing/);
});
