import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { loadClientConfig } from "../lib/config.mjs";
import { parseCsv } from "../lib/csv.mjs";

const DEMAND_HEADERS = [
  "topic_id",
  "query_or_question",
  "source",
  "source_url_or_report",
  "observed_at",
  "search_or_engagement_signal",
  "intent",
  "icp_problem",
  "pillar",
  "business_initiative",
  "funnel_stage",
  "freshness",
  "notes",
];
const HISTORY_HEADERS = [
  "content_id",
  "url",
  "published_at",
  "platform",
  "pillar",
  "business_initiative",
  "owner_problem",
  "unique_pov",
  "hook_mechanism",
  "format",
  "primary_cta",
  "primary_cta_class",
  "source_transcript_or_research_id",
  "reach",
  "retention",
  "saves",
  "shares",
  "comments",
  "profile_visits",
  "qualified_follows",
  "newsletter_subscriptions",
  "conversations",
  "leads",
  "repurpose_relationships",
];
function approvedRecordingIds(manifest) {
  // The approved recording set belongs to the client workspace, never to the
  // engine. A workspace that declares sources.approved_recording_ids gets an
  // exactness check. A workspace that declares none is not exempt from the
  // per-transcript metadata rules, it simply has no fixed expected set yet.
  const declared = manifest?.sources?.approved_recording_ids;
  if (!Array.isArray(declared)) return null;
  const usable = declared.filter(
    (recordingId) => typeof recordingId === "string" && recordingId.length > 0,
  );
  return usable.length > 0 ? usable : null;
}

function hasExactCsvHeaders(text, expectedHeaders) {
  const firstContentLine = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .find((line) => line.trim().length > 0);
  return firstContentLine === expectedHeaders.join(",");
}

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function isPositiveFiniteNumber(value) {
  return Number.isFinite(value) && value > 0;
}

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isIsoDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  return !Number.isNaN(timestamp) && new Date(timestamp).toISOString().slice(0, 10) === value;
}

function validateClientFoundation(foundation, clientId) {
  const errors = [];
  const requiredFields = [
    "icp",
    "positioning",
    "offers",
    "problems",
    "proof",
    "voice",
    "pillars",
    "cta",
    "boundaries",
  ];
  if (foundation?.schema_version !== 1) errors.push("client_foundation schema_version must equal 1");
  if (foundation?.client_id !== clientId) errors.push("client_foundation client_id must match manifest");
  if (foundation?.status !== "approved") errors.push("client_foundation status must be approved");
  if (!isIsoDate(foundation?.completed_at)) errors.push("client_foundation completed_at must be an ISO date");
  if (!isNonEmptyString(foundation?.method)) errors.push("client_foundation method is required");
  for (const field of requiredFields) {
    const record = foundation?.fields?.[field];
    if (!record || record.value === undefined || !Array.isArray(record.evidence_refs)) {
      errors.push(`client_foundation fields.${field} must include value and evidence_refs`);
    }
  }
  if (!Array.isArray(foundation?.unresolved_questions)) {
    errors.push("client_foundation unresolved_questions must be an array");
  }
  return errors;
}

function validateTopicBank(topicBank, clientId, pillarIds) {
  const errors = [];
  if (topicBank?.schema_version !== 1) errors.push("topic_bank schema_version must equal 1");
  if (topicBank?.client_id !== clientId) errors.push("topic_bank client_id must match manifest");
  if (!isIsoDate(topicBank?.last_full_refresh_date)) {
    errors.push("topic_bank last_full_refresh_date must be an ISO date");
  }
  if (!Array.isArray(topicBank?.topics) || topicBank.topics.length === 0) {
    errors.push("topic_bank topics must contain at least one topic");
    return errors;
  }
  const seenIds = new Set();
  for (const [index, topic] of topicBank.topics.entries()) {
    const label = isNonEmptyString(topic?.topic_id) ? topic.topic_id : `topic_bank entry ${index + 1}`;
    if (!isNonEmptyString(topic?.topic_id)) errors.push(`${label}: topic_id is required`);
    if (seenIds.has(topic?.topic_id)) errors.push(`duplicate topic_bank topic_id: ${topic.topic_id}`);
    seenIds.add(topic?.topic_id);
    if (!pillarIds.has(topic?.pillar)) errors.push(`${label}: pillar must belong to manifest`);
    for (const field of ["status", "owner_problem", "client_pov", "owner_outcome"]) {
      if (!isNonEmptyString(topic?.[field])) errors.push(`${label}: ${field} is required`);
    }
    if (!Array.isArray(topic?.buyer_language) || topic.buyer_language.length === 0) {
      errors.push(`${label}: buyer_language must contain at least one phrase`);
    }
    if (!Array.isArray(topic?.evidence_ids) || topic.evidence_ids.length === 0) {
      errors.push(`${label}: evidence_ids must contain at least one source`);
    }
    if (!isIsoDate(topic?.last_validated_at)) {
      errors.push(`${label}: last_validated_at must be an ISO date`);
    }
  }
  return errors;
}

function validateHookLibrary(hookLibrary, clientId) {
  const errors = [];
  const grades = new Set(["hypothesis", "validated", "proven"]);
  if (hookLibrary?.schema_version !== 1) errors.push("hook_library schema_version must equal 1");
  if (hookLibrary?.client_id !== clientId) errors.push("hook_library client_id must match manifest");
  if (!Array.isArray(hookLibrary?.templates)) errors.push("hook_library templates must be an array");
  if (!Array.isArray(hookLibrary?.observed_hooks)) errors.push("hook_library observed_hooks must be an array");
  for (const hook of [...(hookLibrary?.templates ?? []), ...(hookLibrary?.observed_hooks ?? [])]) {
    const label = hook?.hook_id ?? "hook_library entry";
    if (!isNonEmptyString(hook?.hook_id)) errors.push(`${label}: hook_id is required`);
    if (!isNonEmptyString(hook?.structure)) errors.push(`${label}: structure is required`);
    if (!grades.has(hook?.evidence_grade)) {
      errors.push(`${label}: evidence_grade must be hypothesis, validated, or proven`);
    }
    if (!Array.isArray(hook?.supported_topic_types)) {
      errors.push(`${label}: supported_topic_types must be an array`);
    }
    if (!Array.isArray(hook?.source_refs)) errors.push(`${label}: source_refs must be an array`);
    if (hook?.evidence_grade === "proven" && (hook.source_refs ?? []).length === 0) {
      errors.push(`${label}: proven hooks require source_refs`);
    }
  }
  return errors;
}

function validateResearchLog(researchLog, clientId) {
  const errors = [];
  if (researchLog?.schema_version !== 1) errors.push("research_log schema_version must equal 1");
  if (researchLog?.client_id !== clientId) errors.push("research_log client_id must match manifest");
  if (!isNonEmptyString(researchLog?.foundation_validation?.status)) {
    errors.push("research_log foundation_validation.status is required");
  }
  if (!isIsoDate(researchLog?.foundation_validation?.completed_at)) {
    errors.push("research_log foundation_validation.completed_at must be an ISO date");
  }
  if (!Array.isArray(researchLog?.foundation_validation?.source_ids)) {
    errors.push("research_log foundation_validation.source_ids must be an array");
  }
  if (!Array.isArray(researchLog?.foundation_validation?.limitations)) {
    errors.push("research_log foundation_validation.limitations must be an array");
  }
  if (!Array.isArray(researchLog?.batch_signal_scans)) {
    errors.push("research_log batch_signal_scans must be an array");
  }
  return errors;
}

export async function validateClientAssets(config) {
  const errors = [];
  const demandText = await readFile(config.assets.demand_map, "utf8");
  const historyText = await readFile(config.assets.content_history, "utf8");
  const demandRows = parseCsv(demandText);
  const historyRows = parseCsv(historyText);
  const trends = JSON.parse(await readFile(config.assets.trend_library, "utf8"));
  const transcripts = JSON.parse(await readFile(config.assets.transcript_index, "utf8"));
  const foundation = JSON.parse(await readFile(config.assets.client_foundation, "utf8"));
  const topicBank = JSON.parse(await readFile(config.assets.topic_bank, "utf8"));
  const hookLibrary = JSON.parse(await readFile(config.assets.hook_library, "utf8"));
  const researchLog = JSON.parse(await readFile(config.assets.research_log, "utf8"));

  errors.push(...validateClientFoundation(foundation, config.manifest.client_id));
  errors.push(...validateTopicBank(
    topicBank,
    config.manifest.client_id,
    new Set(config.manifest.pillars.map((pillar) => pillar.id)),
  ));
  errors.push(...validateHookLibrary(hookLibrary, config.manifest.client_id));
  errors.push(...validateResearchLog(researchLog, config.manifest.client_id));

  if (!hasExactCsvHeaders(demandText, DEMAND_HEADERS)) {
    errors.push(`demand_map headers must equal ${DEMAND_HEADERS.join(",")}`);
  }
  if (!hasExactCsvHeaders(historyText, HISTORY_HEADERS)) {
    errors.push(`content_history headers must equal ${HISTORY_HEADERS.join(",")}`);
  }
  if (!Array.isArray(trends)) errors.push("trend_library must be an array");
  if (!Array.isArray(transcripts)) {
    errors.push("transcript_index must be an array");
  } else {
    const declaredRecordingIds = approvedRecordingIds(config.manifest);
    const requiredIds = new Set(declaredRecordingIds ?? []);
    const seenIds = new Set();

    for (const [index, transcript] of transcripts.entries()) {
      const validRecordingId = typeof transcript?.recording_id === "string" && transcript.recording_id.length > 0;
      const label = validRecordingId ? transcript.recording_id : `transcript entry ${index + 1}`;
      if (!validRecordingId) {
        errors.push(`${label}: recording_id must be a non-empty string`);
      } else {
        if (seenIds.has(transcript.recording_id)) {
          errors.push(`duplicate transcript recording_id: ${transcript.recording_id}`);
        }
        seenIds.add(transcript.recording_id);
        if (declaredRecordingIds && !requiredIds.has(transcript.recording_id)) {
          errors.push(`unexpected transcript recording_id: ${transcript.recording_id}`);
        }
      }

      const validReportedTotal = isPositiveInteger(transcript?.reported_total);
      const validParsedSegments = isPositiveInteger(transcript?.parsed_segments);
      const validDuration = isPositiveFiniteNumber(transcript?.duration_ms);
      const validFinalEnd = isPositiveFiniteNumber(transcript?.final_end_ms);
      const validCoverage = Number.isFinite(transcript?.coverage_ratio);

      if (!validReportedTotal) errors.push(`${label}: reported_total must be a positive integer`);
      if (!validParsedSegments) errors.push(`${label}: parsed_segments must be a positive integer`);
      if (!validDuration) errors.push(`${label}: duration_ms must be a positive finite number`);
      if (!validFinalEnd) errors.push(`${label}: final_end_ms must be a positive finite number`);

      if (validReportedTotal && validParsedSegments && transcript.reported_total !== transcript.parsed_segments) {
        errors.push(`${label}: transcript segment count mismatch`);
      }
      if (validDuration && validFinalEnd && transcript.final_end_ms > transcript.duration_ms) {
        errors.push(`${label}: final_end_ms must not exceed duration_ms`);
      }
      if (!validCoverage) {
        errors.push(`${label}: coverage_ratio must be a finite number`);
      }
      if (validDuration && validFinalEnd && transcript.final_end_ms <= transcript.duration_ms) {
        const derivedCoverage = transcript.final_end_ms / transcript.duration_ms;
        if (derivedCoverage < 0.98) {
          errors.push(`${label}: derived transcript coverage below 0.98`);
        }
        if (validCoverage && Math.abs(transcript.coverage_ratio - derivedCoverage) > 0.000001) {
          errors.push(`${label}: coverage_ratio must match final_end_ms / duration_ms`);
        }
      }
    }

    if (declaredRecordingIds) {
      for (const recordingId of declaredRecordingIds) {
        if (!seenIds.has(recordingId)) errors.push(`missing transcript recording_id: ${recordingId}`);
      }
    }
  }

  return {
    errors,
    summary: {
      pillars: config.manifest.pillars.length,
      batch_size: config.manifest.content_output?.batch_size ?? 0,
      allowed_formats: config.manifest.content_output?.allowed_formats ?? [],
      demand_rows: demandRows.length,
      trend_rows: Array.isArray(trends) ? trends.length : 0,
      transcript_rows: Array.isArray(transcripts) ? transcripts.length : 0,
      history_rows: historyRows.length,
      topic_bank_rows: Array.isArray(topicBank?.topics) ? topicBank.topics.length : 0,
      hook_template_rows: Array.isArray(hookLibrary?.templates) ? hookLibrary.templates.length : 0,
      hook_observation_rows: Array.isArray(hookLibrary?.observed_hooks)
        ? hookLibrary.observed_hooks.length
        : 0,
    },
  };
}

async function runCli() {
  const manifestPath = process.argv[2];
  if (!manifestPath) {
    console.error("Usage: node content-system/scripts/validate-client.mjs <manifest-path>");
    process.exitCode = 1;
    return;
  }

  try {
    const config = await loadClientConfig(manifestPath);
    const result = await validateClientAssets(config);
    console.log(JSON.stringify(result, null, 2));
    if (result.errors.length) process.exitCode = 1;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}

const invokedScriptUrl = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : undefined;
if (import.meta.url === invokedScriptUrl) await runCli();
