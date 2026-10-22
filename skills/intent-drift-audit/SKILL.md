---
name: intent-drift-audit
description: Audit in-progress or completed work against the user's latest stated intent, success criteria, and authorization boundaries. Use for long-session retrospectives, pre-merge checks, pre-delivery reviews, or direct requests to find scope or intent drift. This is a read-only review and does not implement fixes.
---

# Intent Drift Audit

Find where execution stopped matching the user's current goal. Preserve useful adaptation while exposing material divergence, unsupported claims, missing verification, and actions that exceeded authorization.

## Boundaries

- Treat this as read-only unless the user separately asks for corrections.
- Do not publish, send, schedule, deploy, approve, merge, or change files during the audit.
- The latest explicit user instruction controls when it conflicts with an older plan, summary, or agent decision.
- A task summary or model claim is not proof. Verify against available messages, files, diffs, test output, and live state in scope.
- State what evidence is unavailable instead of reconstructing missing history.

## Establish the contract

Recover the smallest accurate statement of:

- the outcome the user wanted
- what good was supposed to look like
- explicit exclusions and authorization limits
- decisions or corrections made after work began
- the expected deliverables and verification evidence

Keep user intent separate from agent-added assumptions. When the goal changed, use the most recent version and identify the change point.

## Reconstruct what happened

Narrate the material steps in the order they actually occurred. Use repository history, diffs, artifacts, and tool evidence when available. Omit low-value command trivia.

Classify each material choice as:

- `aligned`: directly served the current intent
- `approved adaptation`: changed the route without changing the outcome or exceeded scope only after approval
- `drift`: changed the outcome, scope, claim, audience, authorization, or definition of done without support
- `unresolved`: evidence is insufficient to classify it

Bold the drift inline where it appears in the chronology. Explain the consequence in concrete terms such as rework, risk, delay, cost, weakened positioning, or an unverified completion claim.

## Check the result

Compare the final state with the contract:

- requested deliverables versus actual deliverables
- verified evidence versus claims of completion
- user-supplied facts versus new claims or inference
- approved changes versus unapproved external actions
- source fidelity, privacy, client boundaries, and exact-copy requirements
- tests or acceptance checks required versus evidence actually produced

Do not call a deliberate, user-approved tradeoff drift merely because another approach was possible.

## Report

Lead with the verdict: `aligned`, `minor drift`, `material drift`, or `cannot verify`.

Then provide:

1. **Intent contract:** the current outcome, boundaries, and success test.
2. **Actual sequence:** a plain-language chronology with every drift item bolded inline.
3. **Drift findings:** severity, evidence, consequence, and the smallest correction for each item.
4. **Verification and authorization:** what is proven, what remains unverified, and which actions still require approval.
5. **Highest-leverage next move:** one action that restores alignment or closes the largest evidence gap.

If there is no material drift, say so directly and list only meaningful residual risk. Do not invent criticism to make the audit look thorough.

## Failure behavior

If the source conversation, diff, artifacts, or verification output are missing, complete the portion supported by evidence and label the rest `cannot verify`. Ask at most one question only when the missing input prevents any useful audit.
