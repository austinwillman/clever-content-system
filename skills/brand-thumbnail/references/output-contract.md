# Output contract

Return a finished image unless the user explicitly requests planning or a prompt only.

## Required artifact

- One primary image in the requested dimensions and format
- Exact approved copy and official logo when supplied
- Source-grounded subject, object, or evidence
- A descriptive, versioned filename such as `<topic-slug>-thumbnail-v01.png`

Default a Reel cover to 1080 x 1920 PNG. Honor another requested platform, size, or format.

## Mechanical verification

Run `scripts/verify-image.sh` with the expected width and height. Treat a dimension mismatch or decode failure as a failed export.

## Required visual QA

Inspect the final asset at full size and approximately 25 percent scale. Confirm:

1. The file opens and matches the requested dimensions and format.
2. The subject, object, and claim are grounded in the supplied source.
3. An approved real person's identity remains recognizable and unaltered.
4. The headline matches approved wording, capitalization, punctuation, and line breaks.
5. The official logo comes from the supplied source asset and is not regenerated.
6. The headline is readable in under two seconds at phone size.
7. Critical content remains inside the brand profile's safe region and requested crop.
8. No weak orphan word or accidental line break remains.
9. Colors, typography, logo placement, and treatments match `thumbnail-brand.md`.
10. No fabricated proof, private data, or unsupported interface appears.
11. Every requested deliverable is present.

Revise any failed check before handoff. Mechanical validation alone is not completion.

## Handoff

Report:

- The finished file link
- The selected hook
- The source frame, portrait, or evidence used
- The layout chosen
- Mechanical verification result
- Visual QA result
- Any real limitation, such as a weak source frame or an unverified platform crop

## Prompt-only exception

When the user explicitly requests a generation prompt, include:

- Canvas dimensions
- Approved-source and real-person preservation requirements
- Composition, crop, lighting, and negative-space direction
- An explicit instruction to generate no text and no logo
- Separate exact headline and official-logo compositing instructions

Label the result as a prompt. Do not present it as a completed thumbnail.
