import assert from "node:assert/strict";
import { cp, mkdtemp, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse } from "yaml";
import { loadClientConfig, validateManifest } from "../lib/config.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const fixture = join(here, "fixtures", "valid-client", "content-system.yaml");
const validManifest = parse(await readFile(fixture, "utf8"));

test("loads a complete client manifest and resolves every required asset", async () => {
  const config = await loadClientConfig(fixture);
  assert.equal(config.manifest.client_id, "fixture-client");
  assert.deepEqual(config.manifest.pillars.map((pillar) => pillar.id), [
    "get-found",
    "get-chosen",
    "get-free",
    "stay-human",
  ]);
  assert.equal(Object.keys(config.assets).length, 9);
});

test("accepts client-defined pillars, video output, batch size, and no calendar", () => {
  const manifest = structuredClone(validManifest);
  manifest.pillars = [
    { id: "teach", label: "Teach" },
    { id: "trust", label: "Trust" },
  ];
  manifest.content_output = { allowed_formats: ["video"], batch_size: 4 };
  manifest.cta_classes = ["engage", "book"];
  manifest.cta_destinations = {
    comment: { class: "engage", available: true },
    consultation: { class: "book", available: true },
  };
  delete manifest.calendar;

  assert.deepEqual(validateManifest(manifest), []);
});

test("requires a configured output format and batch size", () => {
  const manifest = structuredClone(validManifest);
  delete manifest.content_output;
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("content_output.allowed_formats must contain at least one format"));
  assert.ok(errors.includes("content_output.batch_size must be a positive integer"));
});

test("rejects duplicate pillars and unsupported output formats", () => {
  const manifest = structuredClone(validManifest);
  manifest.pillars = [{ id: "trust" }, { id: "trust" }];
  manifest.content_output.allowed_formats = ["carousel"];
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("pillar ids must be unique"));
  assert.ok(errors.includes("content_output.allowed_formats must use video"));
});

test("requires a complete strategic initiative", () => {
  const manifest = structuredClone(validManifest);
  manifest.initiative = { id: "", horizon_days: 0, objective: "" };
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("initiative.id is required"));
  assert.ok(errors.includes("initiative.horizon_days must be a positive integer"));
  assert.ok(errors.includes("initiative.objective is required"));
});

test("validates CTA destinations and availability", () => {
  const manifest = structuredClone(validManifest);
  delete manifest.cta_destinations.follow;
  manifest.cta_destinations.newsletter.available = "yes";
  manifest.cta_destinations.lead_magnet.class = "invalid";
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("cta_destinations must include a destination for every CTA class"));
  assert.ok(errors.includes("cta_destinations.newsletter.available must be a boolean"));
  assert.ok(errors.includes("cta_destinations.lead_magnet.class must belong to cta_classes"));
});

test("requires usable fatigue rules", () => {
  const manifest = structuredClone(validManifest);
  manifest.fatigue = {
    topic_cooldown_days: 0,
    max_hook_uses_per_seven_posts: 8,
    hook_frequency_window_posts: 0,
  };
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("fatigue.topic_cooldown_days must be a positive integer"));
  assert.ok(errors.includes("fatigue.max_hook_uses_per_seven_posts must be an integer from 1 to 7"));
  assert.ok(errors.includes("fatigue.hook_frequency_window_posts must be a positive integer"));
});

test("does not require a consecutive CTA rule before the provider schedules content", () => {
  const manifest = structuredClone(validManifest);
  delete manifest.fatigue.max_consecutive_same_cta;
  assert.deepEqual(validateManifest(manifest), []);
});

test("requires ISO research and content-history refresh dates", () => {
  const manifest = structuredClone(validManifest);
  delete manifest.last_research_refresh_date;
  manifest.last_content_history_refresh_date = "August 19";
  const errors = validateManifest(manifest);
  assert.ok(errors.includes("last_research_refresh_date must be an ISO date"));
  assert.ok(errors.includes("last_content_history_refresh_date must be an ISO date"));
});

test("requires connector purpose, subscription, and fallback metadata", () => {
  const manifest = structuredClone(validManifest);
  manifest.research_sources.google_search_console = {
    status: "mystery",
    modes: ["weekly"],
    required: "sometimes",
    subscription: "",
    fallback: "",
  };
  const errors = validateManifest(manifest);
  assert.ok(errors.some((error) => error.startsWith("research_sources.google_search_console.status")));
  assert.ok(errors.includes("research_sources.google_search_console.required must be a boolean"));
  assert.ok(errors.includes("research_sources.google_search_console.subscription is required"));
  assert.ok(errors.includes("research_sources.google_search_console.fallback is required"));
  assert.ok(errors.some((error) => error.startsWith("research_sources.google_search_console.modes")));
});

test("requires both foundation and batch signal research modes", () => {
  const manifest = structuredClone(validManifest);
  for (const source of Object.values(manifest.research_sources)) source.modes = ["foundation"];
  assert.ok(
    validateManifest(manifest).includes("research_sources must include the batch_signal mode"),
  );
});

test("rejects normalized impossible ISO dates", () => {
  const manifest = structuredClone(validManifest);
  manifest.last_research_refresh_date = "2026-02-31";

  assert.ok(validateManifest(manifest).includes("last_research_refresh_date must be an ISO date"));
});

test("rejects an absolute asset path", async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), "content-system-config-"));
  const manifestPath = join(tempRoot, "content-system.yaml");
  const source = await readFile(fixture, "utf8");
  await writeFile(
    manifestPath,
    source.replace("context: content-context.md", `context: ${join(here, "config.test.mjs")}`),
  );

  try {
    await assert.rejects(loadClientConfig(manifestPath), /asset paths must remain within the manifest root/);
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
});

test("rejects an asset path that escapes the manifest root", async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), "content-system-config-"));
  const manifestPath = join(tempRoot, "content-system.yaml");
  const source = await readFile(fixture, "utf8");
  await writeFile(manifestPath, source.replace("context: content-context.md", "context: ../outside.md"));

  try {
    await assert.rejects(loadClientConfig(manifestPath), /asset paths must remain within the manifest root/);
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
});

test("rejects an in-root asset symlink that resolves outside the manifest root", async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), "content-system-config-symlink-"));
  const clientRoot = join(tempRoot, "client");
  const outsideContext = join(tempRoot, "outside-context.md");
  const manifestPath = join(clientRoot, "content-system.yaml");

  await cp(dirname(fixture), clientRoot, { recursive: true });
  await rm(join(clientRoot, "content-context.md"));
  await writeFile(outsideContext, "outside\n");
  await symlink(outsideContext, join(clientRoot, "content-context.md"));

  try {
    await assert.rejects(loadClientConfig(manifestPath), /asset paths must resolve within the manifest root/);
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
});
