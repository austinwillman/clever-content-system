import { readFile, realpath } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { parse } from "yaml";

const REQUIRED_ASSETS = [
  "context",
  "client_foundation",
  "topic_bank",
  "demand_map",
  "trend_library",
  "hook_library",
  "research_log",
  "transcript_index",
  "content_history",
];
const SUPPORTED_FORMATS = ["video"];
const RESEARCH_MODES = ["foundation", "batch_signal"];
const APPROVAL_GATE_STAGES = ["production", "distribution"];
const RESEARCH_SOURCE_STATUSES = [
  "connected",
  "not_connected",
  "export_required",
  "optional",
  "unavailable",
];

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function isIsoDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  return !Number.isNaN(timestamp) && new Date(timestamp).toISOString().slice(0, 10) === value;
}

function pathsOverlap(parent, candidate) {
  const pathFromParent = relative(parent, candidate);
  return pathFromParent === "" || (
    pathFromParent !== ".."
    && !pathFromParent.startsWith(`..${sep}`)
    && !isAbsolute(pathFromParent)
  );
}

export function validateManifest(manifest) {
  const errors = [];
  if (manifest.schema_version !== 1) errors.push("schema_version must equal 1");
  if (!manifest.client_id) errors.push("client_id is required");
  if (!isNonEmptyString(manifest.initiative?.id)) errors.push("initiative.id is required");
  if (!isPositiveInteger(manifest.initiative?.horizon_days)) {
    errors.push("initiative.horizon_days must be a positive integer");
  }
  if (!isNonEmptyString(manifest.initiative?.objective)) errors.push("initiative.objective is required");
  const pillarIds = (manifest.pillars ?? []).map((pillar) => pillar?.id);
  if (pillarIds.length === 0 || pillarIds.some((pillarId) => !isNonEmptyString(pillarId))) {
    errors.push("pillars must contain at least one non-empty id");
  } else if (new Set(pillarIds).size !== pillarIds.length) {
    errors.push("pillar ids must be unique");
  }

  const allowedFormats = manifest.content_output?.allowed_formats ?? [];
  if (allowedFormats.length === 0) {
    errors.push("content_output.allowed_formats must contain at least one format");
  } else if (allowedFormats.some((format) => !SUPPORTED_FORMATS.includes(format))) {
    errors.push(`content_output.allowed_formats must use ${SUPPORTED_FORMATS.join(", ")}`);
  }
  if (!isPositiveInteger(manifest.content_output?.batch_size)) {
    errors.push("content_output.batch_size must be a positive integer");
  }
  for (const key of REQUIRED_ASSETS) {
    if (!manifest.assets?.[key]) errors.push(`assets.${key} is required`);
  }

  const ctaClasses = manifest.cta_classes ?? [];
  if (ctaClasses.length === 0 || ctaClasses.some((ctaClass) => !isNonEmptyString(ctaClass))) {
    errors.push("cta_classes must contain at least one non-empty class");
  } else if (new Set(ctaClasses).size !== ctaClasses.length) {
    errors.push("cta_classes must be unique");
  }
  const ctaDestinations = manifest.cta_destinations ?? {};
  const destinationClasses = new Set();
  for (const [name, destination] of Object.entries(ctaDestinations)) {
    if (!ctaClasses.includes(destination?.class)) {
      errors.push(`cta_destinations.${name}.class must belong to cta_classes`);
    } else {
      destinationClasses.add(destination.class);
    }
    if (typeof destination?.available !== "boolean") {
      errors.push(`cta_destinations.${name}.available must be a boolean`);
    }
  }
  if (ctaClasses.some((ctaClass) => !destinationClasses.has(ctaClass))) {
    errors.push("cta_destinations must include a destination for every CTA class");
  }

  if (!isPositiveInteger(manifest.fatigue?.topic_cooldown_days)) {
    errors.push("fatigue.topic_cooldown_days must be a positive integer");
  }
  const maxHookUses = manifest.fatigue?.max_hook_uses_per_seven_posts;
  if (!isPositiveInteger(maxHookUses) || maxHookUses > 7) {
    errors.push("fatigue.max_hook_uses_per_seven_posts must be an integer from 1 to 7");
  }
  const hookFrequencyWindow = manifest.fatigue?.hook_frequency_window_posts;
  if (hookFrequencyWindow !== undefined && !isPositiveInteger(hookFrequencyWindow)) {
    errors.push("fatigue.hook_frequency_window_posts must be a positive integer");
  }
  const approvalGate = manifest.approval_gate;
  if (!approvalGate || typeof approvalGate !== "object") {
    errors.push("approval_gate is required");
  } else {
    if (!APPROVAL_GATE_STAGES.includes(approvalGate.required_before)) {
      errors.push(`approval_gate.required_before must be one of ${APPROVAL_GATE_STAGES.join(", ")}`);
    }
    if (!isNonEmptyString(approvalGate.approved_by)) {
      errors.push("approval_gate.approved_by is required");
    }
    if (!isNonEmptyString(approvalGate.record_location)) {
      errors.push("approval_gate.record_location is required");
    }
  }

  if (!isIsoDate(manifest.last_research_refresh_date)) {
    errors.push("last_research_refresh_date must be an ISO date");
  }
  if (!isIsoDate(manifest.last_content_history_refresh_date)) {
    errors.push("last_content_history_refresh_date must be an ISO date");
  }

  const researchSources = manifest.research_sources ?? {};
  if (Object.keys(researchSources).length === 0) {
    errors.push("research_sources must declare at least one source");
  }
  const coveredResearchModes = new Set();
  for (const [sourceId, source] of Object.entries(researchSources)) {
    if (!RESEARCH_SOURCE_STATUSES.includes(source?.status)) {
      errors.push(
        `research_sources.${sourceId}.status must be one of ${RESEARCH_SOURCE_STATUSES.join(", ")}`,
      );
    }
    if (typeof source?.required !== "boolean") {
      errors.push(`research_sources.${sourceId}.required must be a boolean`);
    }
    if (!isNonEmptyString(source?.subscription)) {
      errors.push(`research_sources.${sourceId}.subscription is required`);
    }
    if (!isNonEmptyString(source?.fallback)) {
      errors.push(`research_sources.${sourceId}.fallback is required`);
    }
    const modes = source?.modes ?? [];
    if (modes.length === 0 || modes.some((mode) => !RESEARCH_MODES.includes(mode))) {
      errors.push(
        `research_sources.${sourceId}.modes must use ${RESEARCH_MODES.join(", ")}`,
      );
    } else {
      for (const mode of modes) coveredResearchModes.add(mode);
    }
  }
  for (const mode of RESEARCH_MODES) {
    if (!coveredResearchModes.has(mode)) {
      errors.push(`research_sources must include the ${mode} mode`);
    }
  }
  return errors;
}

export async function loadClientConfig(manifestPath) {
  const source = await readFile(manifestPath, "utf8");
  const manifest = parse(source);
  const errors = validateManifest(manifest);
  if (errors.length) throw new Error(`Invalid content manifest:\n${errors.join("\n")}`);
  const root = dirname(resolve(manifestPath));
  const resolvedRoot = await realpath(root);
  const assets = {};
  for (const [key, relativePath] of Object.entries(manifest.assets)) {
    const absolutePath = resolve(root, relativePath);
    const pathFromRoot = relative(root, absolutePath);
    if (
      isAbsolute(relativePath) ||
      pathFromRoot === ".." ||
      pathFromRoot.startsWith(`..${sep}`) ||
      isAbsolute(pathFromRoot)
    ) {
      throw new Error("asset paths must remain within the manifest root");
    }
    const resolvedAssetPath = await realpath(absolutePath);
    if (!pathsOverlap(resolvedRoot, resolvedAssetPath)) {
      throw new Error("asset paths must resolve within the manifest root");
    }
    assets[key] = absolutePath;
  }
  return { manifest, root, assets };
}
