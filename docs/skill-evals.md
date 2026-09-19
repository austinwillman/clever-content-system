# Skill Evaluation

The repository includes an A/B evaluation harness for checking whether an installed Codex skill improves observable behavior instead of merely changing the response.

## Current suite

`evals/social-post-copy/eval.config.json` contains six fictional cases covering:

- speaker ownership
- future proposals versus established behavior
- exact approved openings
- incomplete source material
- unresolved keyword mapping
- draft-only authorization

The cases contain no client data. Each run creates an isolated temporary workspace with a fictional manifest and uses a read-only Codex sandbox.

## Comparison method

For every case, the harness runs the same prompt twice:

1. Baseline with the target skill disabled through a per-run Codex configuration override.
2. Candidate with the installed target skill available.

Both outputs receive deterministic checks. A separate grader then reviews the two outputs in alternating A/B order against source fidelity, ownership, voice, instruction following, and authorization. The final report keeps the baseline and skill scores separate and records each grader reason.

Run reports are written to the ignored `eval-results/` directory. They may contain local paths and model output, so do not commit them.

## Commands

Inspect the planned cases and model-call count without spending model usage:

```sh
npm run eval:social-post-copy:dry
```

Run one smoke case before the complete suite:

```sh
npm run eval:social-post-copy -- --limit 1
```

Run all six cases:

```sh
npm run eval:social-post-copy
```

The complete suite makes 12 target calls and six grader calls. A single run is a directional comparison, not statistical proof. Repeat cases before treating a small score difference as a stable regression, and inspect the actual output and grader reason before changing a skill.

## Adding cases

Add a case when a verified bug, user correction, or product requirement identifies behavior worth protecting. Prefer a literal, hand-checked assertion for hard requirements and use the grader only for qualities that cannot be reduced to a reliable deterministic check.

Keep fixtures fictional and portable. Never place private source material, credentials, client names, or local filesystem paths in the committed eval configuration.
