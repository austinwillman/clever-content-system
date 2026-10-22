import { copyFile, lstat, mkdir, readFile, readdir } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, isAbsolute, join, parse, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SKILLS = [
  { source: "intent-drift-audit", installed: "intent-drift-audit" },
  { source: "social-post-copy", installed: "social-post-copy" },
  { source: "kallaway-hooks", installed: "kallaway-hooks" },
  { source: "transcript-to-content", installed: "transcript-to-content" },
  { source: "trend-to-fit", installed: "trend-to-fit" },
];

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const canonicalSkillsRoot = resolve(scriptDirectory, "..", "skills");

function containsPath(parent, candidate) {
  const pathFromParent = relative(parent, candidate);
  return pathFromParent === "" || (
    pathFromParent !== ".."
    && !pathFromParent.startsWith(`..${sep}`)
    && !isAbsolute(pathFromParent)
  );
}

function resolveSafeRoot(label, root) {
  if (typeof root !== "string" || root.trim() === "") {
    throw new Error(`unsafe ${label} skill root: path is required`);
  }

  const resolvedRoot = resolve(root);
  const filesystemRoot = parse(resolvedRoot).root;
  const pathParts = resolvedRoot.slice(filesystemRoot.length).split(sep).filter(Boolean);

  if (resolvedRoot === filesystemRoot) {
    throw new Error(`unsafe ${label} skill root: filesystem root is too broad`);
  }
  if (pathParts.length < 2) {
    throw new Error(`unsafe ${label} skill root: path is too broad`);
  }

  const userHome = resolve(homedir());
  if (containsPath(resolvedRoot, userHome)) {
    throw new Error(`unsafe ${label} skill root: path contains the user home directory`);
  }
  if (containsPath(resolvedRoot, canonicalSkillsRoot) || containsPath(canonicalSkillsRoot, resolvedRoot)) {
    throw new Error(`unsafe ${label} skill root: path overlaps the canonical skill source`);
  }

  return resolvedRoot;
}

async function assertNoSymlinkInTargetPath(target, targetPath) {
  const pathFromRoot = relative(target.root, targetPath);
  if (pathFromRoot === ".." || pathFromRoot.startsWith(`..${sep}`) || isAbsolute(pathFromRoot)) {
    throw new Error(`unsafe ${target.label} target path: path escapes the skill root`);
  }

  const filesystemRoot = parse(targetPath).root;
  const paths = [filesystemRoot];
  let currentPath = filesystemRoot;
  for (const part of targetPath.slice(filesystemRoot.length).split(sep).filter(Boolean)) {
    currentPath = join(currentPath, part);
    paths.push(currentPath);
  }

  for (const [index, path] of paths.entries()) {
    try {
      const stats = await lstat(path);
      if (stats.isSymbolicLink()) {
        throw new Error(`unsafe symlink in ${target.label} target path: ${path}`);
      }
      const isFinalTarget = index === paths.length - 1;
      if (!isFinalTarget && !stats.isDirectory()) {
        throw new Error(`unsafe non-directory in ${target.label} target path: ${path}`);
      }
      if (isFinalTarget && !stats.isFile()) {
        throw new Error(`unsafe non-regular file in ${target.label} target path: ${path}`);
      }
    } catch (error) {
      if (error?.code === "ENOENT") return;
      throw error;
    }
  }
}

async function listKnownFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const entryPath = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await listKnownFiles(entryPath));
    else if (entry.isFile()) files.push(entryPath);
  }

  return files;
}

async function compareKnownFile(sourcePath, targetPath, displayPath) {
  const sourceBytes = await readFile(sourcePath);

  try {
    const targetBytes = await readFile(targetPath);
    return sourceBytes.equals(targetBytes) ? undefined : `${displayPath}: differs`;
  } catch (error) {
    if (error?.code === "ENOENT") return `${displayPath}: missing`;
    return `${displayPath}: unreadable (${error?.code ?? "unknown error"})`;
  }
}

export async function syncSkills({
  codexRoot = join(homedir(), ".codex", "skills"),
  claudeRoot = join(homedir(), ".claude", "skills"),
  mode,
} = {}) {
  if (mode !== "install" && mode !== "check") {
    throw new Error('mode must be either "install" or "check"');
  }

  const targets = [
    { label: "codex", root: resolveSafeRoot("codex", codexRoot) },
    { label: "claude", root: resolveSafeRoot("claude", claudeRoot) },
  ];
  if (containsPath(targets[0].root, targets[1].root) || containsPath(targets[1].root, targets[0].root)) {
    throw new Error("unsafe skill roots: Codex and Claude Code targets overlap");
  }

  const operations = [];
  const drift = [];

  for (const skill of SKILLS) {
    const sourceRoot = join(canonicalSkillsRoot, skill.source);
    const sourceFiles = await listKnownFiles(sourceRoot);

    for (const sourcePath of sourceFiles) {
      const relativePath = relative(sourceRoot, sourcePath);

      for (const target of targets) {
        const targetPath = join(target.root, skill.installed, relativePath);
        const displayPath = [target.label, skill.installed, relativePath].join("/");
        operations.push({ displayPath, sourcePath, target, targetPath });
      }
    }
  }

  if (mode === "install") {
    for (const operation of operations) {
      await assertNoSymlinkInTargetPath(operation.target, operation.targetPath);
    }
    for (const operation of operations) {
      await mkdir(dirname(operation.targetPath), { recursive: true });
      await copyFile(operation.sourcePath, operation.targetPath);
    }
  } else {
    for (const operation of operations) {
      const difference = await compareKnownFile(
        operation.sourcePath,
        operation.targetPath,
        operation.displayPath,
      );
      if (difference) drift.push(difference);
    }
  }

  return {
    mode,
    skills: SKILLS.map((skill) => skill.installed),
    files: operations.map((operation) => operation.displayPath),
    drift,
  };
}

export async function runSyncCli({
  args = process.argv.slice(2),
  codexRoot,
  claudeRoot,
  stdout = console.log,
  stderr = console.error,
} = {}) {
  const flag = args[0];
  const mode = flag === "--install" ? "install" : flag === "--check" ? "check" : undefined;

  if (!mode || args.length !== 1) {
    stderr("Usage: node content-system/scripts/sync-skills.mjs --check|--install");
    return 1;
  }

  try {
    const result = await syncSkills({ codexRoot, claudeRoot, mode });
    if (mode === "check" && result.drift.length) {
      stderr(`Skill drift detected:\n${result.drift.map((item) => `- ${item}`).join("\n")}`);
      return 1;
    }

    if (mode === "check") {
      stdout(`Skill check passed: ${result.files.length} known target files match.`);
    } else {
      stdout(`Installed ${result.files.length} known skill files across Codex and Claude Code.`);
    }
    return 0;
  } catch (error) {
    stderr(error instanceof Error ? error.message : String(error));
    return 1;
  }
}

const invokedScriptUrl = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : undefined;
if (import.meta.url === invokedScriptUrl) process.exitCode = await runSyncCli();
