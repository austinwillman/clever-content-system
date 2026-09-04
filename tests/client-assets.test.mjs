import assert from "node:assert/strict";
import { cp, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { loadClientConfig } from "../lib/config.mjs";
import { validateClientAssets } from "../scripts/validate-client.mjs";

const DEMAND_HEADER = "topic_id,query_or_question,source,source_url_or_report,observed_at,search_or_engagement_signal,intent,icp_problem,pillar,business_initiative,funnel_stage,freshness,notes";
const HISTORY_HEADER = "content_id,url,published_at,platform,pillar,business_initiative,owner_problem,unique_pov,hook_mechanism,format,primary_cta,primary_cta_class,source_transcript_or_research_id,reach,retention,saves,shares,comments,profile_visits,qualified_follows,newsletter_subscriptions,conversations,leads,repurpose_relationships";
// Fictional identifiers. The engine holds no real client recording list.
const REQUIRED_RECORDING_IDS = [
  "fixture-recording-01",
  "fixture-recording-02",
  "fixture-recording-03",
  "fixture-recording-04",
];

function validTranscripts() {
  return REQUIRED_RECORDING_IDS.map((recordingId) => ({
    recording_id: recordingId,
    reported_total: 10,
    parsed_segments: 10,
    duration_ms: 1000,
    final_end_ms: 990,
    coverage_ratio: 0.99,
  }));
}

async function withClientAssets(overrides, assertion) {
  const root = await mkdtemp(join(tmpdir(), "content-client-validation-"));
  const demandMap = join(root, "demand-map.csv");
  const contentHistory = join(root, "content-history.csv");
  const trendLibrary = join(root, "trend-library.json");
  const transcriptIndex = join(root, "transcript-index.json");
  const clientFoundation = join(root, "client-foundation.json");
  const topicBank = join(root, "topic-bank.json");
  const hookLibrary = join(root, "hook-library.json");
  const researchLog = join(root, "research-log.json");
  const clientId = overrides.clientId ?? "example-client";

  await Promise.all([
    writeFile(demandMap, overrides.demandMap ?? `${DEMAND_HEADER}\n`),
    writeFile(contentHistory, overrides.contentHistory ?? `${HISTORY_HEADER}\n`),
    writeFile(trendLibrary, JSON.stringify(overrides.trends ?? [])),
    writeFile(transcriptIndex, JSON.stringify(overrides.transcripts ?? validTranscripts())),
    writeFile(clientFoundation, JSON.stringify(overrides.foundation ?? {
      schema_version: 1,
      client_id: clientId,
      status: "approved",
      completed_at: "2026-08-19",
      method: "interview",
      fields: Object.fromEntries([
        "icp", "positioning", "offers", "problems", "proof", "voice", "pillars", "cta", "boundaries",
      ].map((field) => [field, { value: [], evidence_refs: [] }])),
      unresolved_questions: [],
    })),
    writeFile(topicBank, JSON.stringify(overrides.topicBank ?? {
      schema_version: 1,
      client_id: clientId,
      last_full_refresh_date: "2026-08-19",
      topics: [{
        topic_id: "test-topic",
        status: "active",
        pillar: "test-pillar",
        owner_problem: "Owner problem",
        buyer_language: ["Buyer phrase"],
        client_pov: "Client point of view",
        owner_outcome: "Owner outcome",
        evidence_ids: ["test-evidence"],
        last_validated_at: "2026-08-19",
      }],
    })),
    writeFile(hookLibrary, JSON.stringify(overrides.hookLibrary ?? {
      schema_version: 1,
      client_id: clientId,
      templates: [],
      observed_hooks: [],
    })),
    writeFile(researchLog, JSON.stringify(overrides.researchLog ?? {
      schema_version: 1,
      client_id: clientId,
      foundation_validation: {
        status: "complete_with_limits",
        completed_at: "2026-08-19",
        source_ids: ["test-evidence"],
        limitations: [],
      },
      batch_signal_scans: [],
    })),
  ]);

  try {
    const result = await validateClientAssets({
      manifest: {
        client_id: clientId,
        pillars: [{ id: "test-pillar" }],
        calendar: [],
        sources: {
          approved_recording_ids: overrides.approvedRecordingIds ?? REQUIRED_RECORDING_IDS,
        },
      },
      assets: {
        demand_map: demandMap,
        content_history: contentHistory,
        trend_library: trendLibrary,
        transcript_index: transcriptIndex,
        client_foundation: clientFoundation,
        topic_bank: topicBank,
        hook_library: hookLibrary,
        research_log: researchLog,
      },
    });
    await assertion(result);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("rejects a foundation that is not approved and a proven hook without evidence", async () => {
  await withClientAssets({
    foundation: {
      schema_version: 1,
      client_id: "example-client",
      status: "draft",
      completed_at: "2026-08-19",
      method: "interview",
      fields: Object.fromEntries([
        "icp", "positioning", "offers", "problems", "proof", "voice", "pillars", "cta", "boundaries",
      ].map((field) => [field, { value: [], evidence_refs: [] }])),
      unresolved_questions: [],
    },
    hookLibrary: {
      schema_version: 1,
      client_id: "example-client",
      templates: [{
        hook_id: "unsupported-proof",
        structure: "A hook",
        evidence_grade: "proven",
        supported_topic_types: [],
        source_refs: [],
      }],
      observed_hooks: [],
    },
  }, (result) => {
    assert.ok(result.errors.includes("client_foundation status must be approved"));
    assert.ok(result.errors.includes("unsupported-proof: proven hooks require source_refs"));
  });
});

test("rejects incomplete transcript coverage and segment count mismatches", async () => {
  const transcripts = validTranscripts();
  transcripts[0].parsed_segments = 9;
  transcripts[0].final_end_ms = 950;
  transcripts[0].coverage_ratio = 0.95;

  await withClientAssets({ transcripts }, (result) => {
    assert.deepEqual(result.errors, [
      `${REQUIRED_RECORDING_IDS[0]}: transcript segment count mismatch`,
      `${REQUIRED_RECORDING_IDS[0]}: derived transcript coverage below 0.98`,
    ]);
  });
});

test("derives transcript coverage from timestamps instead of trusting the supplied ratio", async () => {
  const transcripts = validTranscripts();
  transcripts[0].final_end_ms = 970;
  transcripts[0].coverage_ratio = 0.99;

  await withClientAssets({ transcripts }, (result) => {
    assert.ok(result.errors.includes(`${REQUIRED_RECORDING_IDS[0]}: derived transcript coverage below 0.98`));
    assert.ok(
      result.errors.includes(
        `${REQUIRED_RECORDING_IDS[0]}: coverage_ratio must match final_end_ms / duration_ms`,
      ),
    );
  });
});

test("rejects a supplied coverage ratio that disagrees with complete timestamps", async () => {
  const transcripts = validTranscripts();
  transcripts[0].coverage_ratio = 0.98;

  await withClientAssets({ transcripts }, (result) => {
    assert.ok(
      result.errors.includes(
        `${REQUIRED_RECORDING_IDS[0]}: coverage_ratio must match final_end_ms / duration_ms`,
      ),
    );
  });
});

test("requires the exact four approved transcript recording IDs", async () => {
  const transcripts = validTranscripts();
  transcripts[3].recording_id = "unexpected-recording";

  await withClientAssets({ transcripts }, (result) => {
    assert.ok(result.errors.includes("unexpected transcript recording_id: unexpected-recording"));
    assert.ok(result.errors.includes(`missing transcript recording_id: ${REQUIRED_RECORDING_IDS[3]}`));
  });
});

test("rejects duplicate approved transcript recording IDs", async () => {
  const transcripts = validTranscripts();
  transcripts.push({ ...transcripts[0] });

  await withClientAssets({ transcripts }, (result) => {
    assert.ok(result.errors.includes(`duplicate transcript recording_id: ${REQUIRED_RECORDING_IDS[0]}`));
  });
});

test("rejects missing required transcript metadata", async () => {
  const transcripts = validTranscripts();
  transcripts[0] = { recording_id: REQUIRED_RECORDING_IDS[0] };

  await withClientAssets({ transcripts }, (result) => {
    assert.deepEqual(result.errors, [
      `${REQUIRED_RECORDING_IDS[0]}: reported_total must be a positive integer`,
      `${REQUIRED_RECORDING_IDS[0]}: parsed_segments must be a positive integer`,
      `${REQUIRED_RECORDING_IDS[0]}: duration_ms must be a positive finite number`,
      `${REQUIRED_RECORDING_IDS[0]}: final_end_ms must be a positive finite number`,
      `${REQUIRED_RECORDING_IDS[0]}: coverage_ratio must be a finite number`,
    ]);
  });
});

test("rejects malformed transcript metadata and an end time beyond duration", async () => {
  const transcripts = validTranscripts();
  transcripts[0] = {
    recording_id: REQUIRED_RECORDING_IDS[0],
    reported_total: 10.5,
    parsed_segments: -1,
    duration_ms: 1000,
    final_end_ms: 1001,
    coverage_ratio: null,
  };

  await withClientAssets({ transcripts }, (result) => {
    assert.deepEqual(result.errors, [
      `${REQUIRED_RECORDING_IDS[0]}: reported_total must be a positive integer`,
      `${REQUIRED_RECORDING_IDS[0]}: parsed_segments must be a positive integer`,
      `${REQUIRED_RECORDING_IDS[0]}: final_end_ms must not exceed duration_ms`,
      `${REQUIRED_RECORDING_IDS[0]}: coverage_ratio must be a finite number`,
    ]);
  });
});

test("rejects a transcript entry without a recording ID", async () => {
  const transcripts = validTranscripts();
  transcripts[0] = {
    reported_total: 10,
    parsed_segments: 10,
    duration_ms: 1000,
    final_end_ms: 990,
    coverage_ratio: 0.99,
  };

  await withClientAssets({ transcripts }, (result) => {
    assert.ok(result.errors.includes("transcript entry 1: recording_id must be a non-empty string"));
    assert.ok(result.errors.includes(`missing transcript recording_id: ${REQUIRED_RECORDING_IDS[0]}`));
  });
});

test("rejects blank demand-map and content-history CSV files", async () => {
  await withClientAssets({ demandMap: "", contentHistory: "" }, (result) => {
    assert.ok(result.errors.includes(`demand_map headers must equal ${DEMAND_HEADER}`));
    assert.ok(result.errors.includes(`content_history headers must equal ${HISTORY_HEADER}`));
  });
});

test("rejects CSV files with unrelated headers", async () => {
  await withClientAssets(
    { demandMap: "one,two\n", contentHistory: "alpha,beta\n" },
    (result) => {
      assert.ok(result.errors.includes(`demand_map headers must equal ${DEMAND_HEADER}`));
      assert.ok(result.errors.includes(`content_history headers must equal ${HISTORY_HEADER}`));
    },
  );
});

test("accepts a header-only content-history CSV", async () => {
  await withClientAssets({}, (result) => {
    assert.equal(result.summary.history_rows, 0);
    assert.deepEqual(result.errors, []);
  });
});

test("rejects a trend library that is not an array", async () => {
  await withClientAssets({ trends: {} }, (result) => {
    assert.deepEqual(result.errors, ["trend_library must be an array"]);
  });
});

