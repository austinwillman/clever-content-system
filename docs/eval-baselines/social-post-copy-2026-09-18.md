# Social Post Copy A/B Baseline

Date: 2026-09-18

This is the first directional run of the six-case social-post-copy skill evaluation. It is evidence for iteration, not proof that one condition is universally better.

## Setup

- Target model: `gpt-5.6-luna`, medium reasoning
- Grader model: `gpt-5.6-terra`, medium reasoning
- Conditions: same prompt with `social-post-copy` disabled versus available
- Cases: guest ownership, future proposal, exact opening, incomplete source, unresolved keyword, draft authorization
- Grading: deterministic checks plus a blinded rubric with alternating A/B order

## Result

| Condition | Deterministic checks | Average rubric score | Case wins |
| --- | ---: | ---: | ---: |
| Baseline | 18/18 | 9.33/10 | 3 |
| Skill | 18/18 | 8.67/10 | 2 |
| Tie | n/a | n/a | 1 |

The skill did not beat the baseline in this run.

## Useful findings

1. Guest ownership improved with the skill. It excluded the guest's hiring story and exposed the bounded-source limitation.
2. Draft-only authorization improved with the skill. The response stayed closer to the source and avoided unnecessary extrapolation.
3. Future-proposal language weakened with the skill. Its opening changed `could flag` into `flags` before later restoring the caveat.
4. Incomplete-source handling weakened slightly with the skill. It added the interpretation that the handoff was the part the author needed to examine.
5. The unresolved-keyword loss is not strong regression evidence. The grader preferred the baseline mainly because it reused more source wording, although both outputs passed all hard requirements.
6. The exact-opening case exposed prompt ambiguity. Both outputs treated the `Source:` label as copy. Refine that fixture before using it as a release gate.

## Decision

Keep the skill and the eval suite, but do not claim the skill is proven better. Before changing the skill, refine the ambiguous fixture and repeat the two meaningful failure cases across multiple runs. The first candidate change should enforce prospective language at every occurrence, not only in a later disclaimer.
