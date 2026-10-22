const FINGERPRINT_FIELDS = ["pillar", "owner_problem", "unique_pov", "hook_mechanism", "format", "primary_cta_class"];

export function contentFingerprint(item) {
  return FINGERPRINT_FIELDS
    .map((field) => String(item[field] ?? "").trim().toLowerCase().replace(/\s+/g, " "))
    .join("|");
}

export function findFatigueConflicts(candidate, history, rules, evaluationDate) {
  const candidateDate = new Date(evaluationDate ?? candidate.publish_date);
  const cooldownDays = rules?.topic_cooldown_days ?? 45;
  if (Number.isNaN(candidateDate.valueOf()) || !Number.isFinite(cooldownDays)) return [];

  const candidateFingerprint = contentFingerprint(candidate);
  return history.filter((item) => {
    const publishedDate = new Date(item.publish_date ?? item.published_at);
    if (Number.isNaN(publishedDate.valueOf()) || contentFingerprint(item) !== candidateFingerprint) return false;
    const elapsedDays = Math.abs(candidateDate - publishedDate) / (24 * 60 * 60 * 1000);
    return elapsedDays <= cooldownDays;
  });
}
