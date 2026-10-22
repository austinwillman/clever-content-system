# Trend Fit Score

Score only after source attribution, evidence labeling, ICP match, and client-owned POV gates pass. Record the points and a source-backed rationale for every dimension. Do not award points for assumptions, unavailable sources, or an `Inference` presented as fact.

## 100-point rubric

| Dimension | Points | Full-credit standard |
| --- | ---: | --- |
| ICP problem match | 15 | The pattern maps directly to a documented problem the primary client ICP recognizes, including a concrete founder consequence. |
| Pillar match | 10 | The adaptation clearly advances one approved manifest pillar. |
| Business initiative match | 10 | The adaptation materially supports the manifest's current initiative. |
| Client-owned POV strength | 15 | The client contributes a specific, defensible reframe, story, framework, or conclusion supported by client-owned source material. |
| Founder recognition | 15 | A founder can recognize the situation, lived experience, and owner outcome before the production mechanism takes over. |
| Authority signal | 10 | The idea gives a credible host, organizer, partner, or peer a distinctive framework worth discussing while serving the founder first. |
| Evidence quality | 10 | Observable metrics, source URL or report, dates, and limitations are complete and attributable. Performance explanations remain labeled as inference. |
| Freshness | 5 | The source is current for the platform and research cadence, and its expiration is explicit. |
| Format suitability | 5 | The mechanics suit the client's creator strengths, platform, available production, and intended message. |
| CTA compatibility | 5 | Exactly one CTA class and currently available destination naturally continue the content's job. |

Maximum: 100 points.

## Scoring rules

- Use whole points from zero through the dimension maximum.
- Give zero for a dimension that lacks attributable support.
- Do not substitute views or engagement for ICP fit, POV strength, authority, or conversion evidence.
- Treat transcript-derived audience language as qualitative support only. It does not prove market prevalence.
- Treat inferred reasons for performance as hypotheses. They may guide adaptation but do not raise evidence-quality points unless separate evidence supports them.
- A score cannot override a hard rejection gate in the canonical skill.

## Decision bands and rejection floor

- 90 to 100: `flagship-fit`
- 80 to 89: `strong`
- 70 to 79: `viable`
- Below 70: `reject`

Reject every candidate below 70. Do not round up, add discretionary bonus points, or reduce the denominator because evidence is unavailable.

## Fatigue post-score gate

Fatigue is not part of the 100 points. Apply it after the numeric score by comparing the full fingerprint:

`pillar + owner_problem + unique_pov + hook_mechanism + format + primary_cta_class`

Then apply the manifest rules for topic cooldown and hook-mechanism use. CTA sequence is evaluated only after the provider schedules content.

| Fatigue result | Decision |
| --- | --- |
| `clear` | Preserve the score band and allow acceptance when all other gates pass. |
| `review` | Preserve the score, document the overlap, and require a material difference in proof, buyer stage, or conclusion. |
| `hold` | Stop acceptance until the conflict is resolved. Do not subtract points to force it through. |
| `unknown` | Preserve the score but do not claim clearance. Hold for human review unless the user explicitly accepts incomplete history. |

## Required score record

Store this structure inside the adaptation brief:

```json
{
  "total": 84,
  "band": "strong",
  "dimensions": {
    "icp_problem_match": { "points": 13, "max": 15, "rationale": "Documented owner problem and consequence." },
    "pillar_match": { "points": 10, "max": 10, "rationale": "Matches one approved pillar." },
    "business_initiative_match": { "points": 9, "max": 10, "rationale": "Directly advances the current initiative." },
    "client_owned_pov_strength": { "points": 13, "max": 15, "rationale": "Client source supports a distinct conclusion." },
    "founder_recognition": { "points": 13, "max": 15, "rationale": "Situation and owner stakes are immediate." },
    "authority_signal": { "points": 8, "max": 10, "rationale": "Produces a defensible discussion framework." },
    "evidence_quality": { "points": 7, "max": 10, "rationale": "Dated metrics are attributable, with one stated limitation." },
    "freshness": { "points": 4, "max": 5, "rationale": "Current source with conservative expiration." },
    "format_suitability": { "points": 4, "max": 5, "rationale": "Mechanics suit founder-led video." },
    "cta_compatibility": { "points": 3, "max": 5, "rationale": "Available CTA fits, but the transition needs refinement." }
  },
  "fatigue_status": "clear"
}
```

The dimension points must sum exactly to `total`. The `band` must match the decision thresholds. Store fatigue beside the score, but never include it in the sum.
