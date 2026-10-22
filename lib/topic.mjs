const ALLOWED_APPROVAL_STATUSES = ["pending_topic_approval", "approved_for_recording"];
const DEFAULT_HOOK_FREQUENCY_WINDOW_POSTS = 7;
const REQUIRED_FIELDS = [
  "topic_id",
  "approval_status",
  "title",
  "pillar",
  "strategic_initiative",
  "owner_problem",
  "founder_experience",
  "owner_outcome",
  "source_excerpt",
  "source_recording_id",
  "source_timestamp_ms",
  "objection",
  "confusion",
  "frustration",
  "aha",
  "unique_pov",
  "authority_signal",
  "raw_hook_material",
  "not_about",
  "really_about",
  "recording_prompt",
  "hook_mechanism",
  "format",
  "primary_cta_class",
  "cta_destination",
  "cta_destination_available",
  "fatigue_status",
  "trend_evidence_ids",
  "content_history_conflicts",
  "ownership_confidence",
];

const READER_FACING_FIELDS = [
  "title",
  "owner_problem",
  "founder_experience",
  "owner_outcome",
  "source_excerpt",
  "objection",
  "confusion",
  "frustration",
  "aha",
  "unique_pov",
  "authority_signal",
  "not_about",
  "really_about",
  "recording_prompt",
];

const SEARCH_TARGET_STATUSES = ["validated", "provisional", "qualitative_only", "unavailable"];

function isMissing(value) {
  return value === undefined || value === null || value === "";
}

function hasForbiddenDash(value) {
  return typeof value === "string" && /[\u2013\u2014]/.test(value);
}

function publicationTime(item) {
  return new Date(item.publish_date ?? item.published_at).valueOf();
}

export function findHookFrequencyConflicts(topics, history = [], rules = {}) {
  const maxHookUses = rules.max_hook_uses_per_seven_posts;
  const windowPosts = rules.hook_frequency_window_posts ?? DEFAULT_HOOK_FREQUENCY_WINDOW_POSTS;
  if (!Number.isInteger(maxHookUses) || maxHookUses < 1) return [];
  if (!Number.isInteger(windowPosts) || windowPosts < 1) return [];

  const entries = [
    ...history.map((item, sequence) => ({ incoming: false, item, sequence })),
    ...topics.map((item, sequence) => ({ incoming: true, item, sequence })),
  ]
    .map((entry) => ({ ...entry, publishedAt: publicationTime(entry.item) }))
    .filter((entry) => (
      entry.item.hook_mechanism
      && (entry.incoming || !Number.isNaN(entry.publishedAt))
    ))
    .sort((left, right) => {
      const leftIsDated = !Number.isNaN(left.publishedAt);
      const rightIsDated = !Number.isNaN(right.publishedAt);
      if (leftIsDated && rightIsDated && left.publishedAt !== right.publishedAt) {
        return left.publishedAt - right.publishedAt;
      }
      if (leftIsDated !== rightIsDated) return leftIsDated ? -1 : 1;
      return Number(left.incoming) - Number(right.incoming) || left.sequence - right.sequence;
    });

  const conflicts = new Map();
  for (const [index, entry] of entries.entries()) {
    if (!entry.incoming) continue;
    const window = entries.slice(Math.max(0, index - windowPosts + 1), index + 1);
    const count = window.filter(
      (candidate) => candidate.item.hook_mechanism === entry.item.hook_mechanism,
    ).length;
    if (count > maxHookUses && !conflicts.has(entry.item.hook_mechanism)) {
      conflicts.set(entry.item.hook_mechanism, {
        hook_mechanism: entry.item.hook_mechanism,
        count,
        max: maxHookUses,
        window_posts: windowPosts,
        topic_id: entry.item.topic_id,
      });
    }
  }
  return [...conflicts.values()];
}

export function validateTopic(topic, manifest) {
  const errors = [];
  for (const field of REQUIRED_FIELDS) {
    if (isMissing(topic[field])) errors.push(`${field} is required`);
  }
  const allowedPillars = (manifest?.pillars ?? []).map((pillar) => pillar.id);
  if (topic.pillar && allowedPillars.length > 0 && !allowedPillars.includes(topic.pillar)) {
    errors.push(`pillar must be one of ${allowedPillars.join(", ")}`);
  }
  const allowedCtaClasses = manifest?.cta_classes ?? [];
  if (topic.primary_cta_class && allowedCtaClasses.length > 0 && !allowedCtaClasses.includes(topic.primary_cta_class)) {
    errors.push(`primary_cta_class must be one of ${allowedCtaClasses.join(", ")}`);
  }
  const allowedFormats = manifest?.content_output?.allowed_formats ?? [];
  if (topic.format && allowedFormats.length > 0 && !allowedFormats.includes(topic.format)) {
    errors.push(`format must be one of ${allowedFormats.join(", ")}`);
  }
  if (topic.approval_status && !ALLOWED_APPROVAL_STATUSES.includes(topic.approval_status)) {
    errors.push(`approval_status must be one of ${ALLOWED_APPROVAL_STATUSES.join(", ")}`);
  }
  if (typeof topic.cta_destination_available !== "boolean") {
    errors.push("cta_destination_available must be a boolean");
  }
  const destination = manifest?.cta_destinations?.[topic.cta_destination];
  if (manifest && topic.cta_destination && !destination) {
    errors.push(`CTA destination ${topic.cta_destination} is not declared in the manifest`);
  } else if (destination) {
    if (destination.class !== topic.primary_cta_class) {
      errors.push(`CTA destination ${topic.cta_destination} must use class ${topic.primary_cta_class}`);
    }
    if (destination.available !== true) {
      errors.push(`CTA destination ${topic.cta_destination} is unavailable`);
    }
    if (topic.cta_destination_available !== destination.available) {
      errors.push("cta_destination_available must match the manifest");
    }
  }
  if (
    (!Array.isArray(topic.demand_evidence_ids) || topic.demand_evidence_ids.length === 0) &&
    topic.demand_evidence_status !== "unavailable"
  ) {
    errors.push("demand_evidence_ids is required unless demand_evidence_status is unavailable");
  }
  if (topic.approval_status === "approved_for_recording" && isMissing(topic.search_target)) {
    errors.push("search_target is required");
  } else if (topic.search_target && typeof topic.search_target === "object") {
    for (const field of ["target_id", "primary_query", "spoken_phrase", "intent"]) {
      if (isMissing(topic.search_target[field])) errors.push(`search_target.${field} is required`);
    }
    if (!SEARCH_TARGET_STATUSES.includes(topic.search_target.validation_status)) {
      errors.push(`search_target.validation_status must be one of ${SEARCH_TARGET_STATUSES.join(", ")}`);
    }
    if (!Array.isArray(topic.search_target.supporting_terms)) {
      errors.push("search_target.supporting_terms must be an array");
    }
  }
  for (const field of READER_FACING_FIELDS) {
    if (hasForbiddenDash(topic[field])) errors.push(`${field} must not contain em dash or en dash`);
  }
  for (const hook of topic.raw_hook_material ?? []) {
    if (hasForbiddenDash(hook)) errors.push("raw_hook_material must not contain em dash or en dash");
  }
  return errors;
}

export function validateWeeklyBatch(topics, manifest, history = []) {
  const errors = [];
  const historyRows = Array.isArray(history) ? history : [];
  const batchSize = manifest.content_output?.batch_size;
  if (topics.length !== batchSize) {
    errors.push(`content batch must contain exactly ${batchSize} topics`);
  }
  if (new Set(topics.map((topic) => topic.topic_id)).size !== topics.length) {
    errors.push("content batch must contain unique topic ids");
  }

  if (historyRows.length === 0) {
    for (const topic of topics) {
      if (topic.fatigue_status !== "unknown") {
        errors.push(`${topic.topic_id} fatigue_status must be unknown when content history is unavailable`);
      }
    }
  }

  const initiativeId = manifest.initiative?.id;
  const manifestClientId = manifest.client_id;
  for (const topic of topics) {
    for (const error of validateTopic(topic, manifest)) {
      errors.push(`${topic.topic_id} ${error}`);
    }
    if (initiativeId && topic.strategic_initiative !== initiativeId) {
      errors.push(`${topic.topic_id} strategic_initiative must equal ${initiativeId}`);
    }
    // Client isolation. A batch that carries another client's work is a
    // confidentiality failure, not a formatting problem.
    if (isMissing(topic.client_id)) {
      errors.push(`${topic.topic_id} client_id is required`);
    } else if (manifestClientId && topic.client_id !== manifestClientId) {
      errors.push(
        `${topic.topic_id} client_id ${topic.client_id} does not belong to workspace ${manifestClientId}`,
      );
    }
  }

  const hookConflicts = findHookFrequencyConflicts(topics, historyRows, manifest.fatigue);
  for (const conflict of hookConflicts) {
    errors.push(
      `weekly batch hook mechanism ${conflict.hook_mechanism} exceeds ${conflict.max} uses in a rolling ${conflict.window_posts}-post window`,
    );
  }

  return errors;
}
