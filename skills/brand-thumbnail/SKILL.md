---
name: brand-thumbnail
description: Create and quality-check white-labeled thumbnails and cover images from videos, transcripts, screenshots, approved portraits, logos, and supplied copy. Use when asked to design, generate, revise, or QA a Reel cover, YouTube thumbnail, social video thumbnail, or other branded cover image. Read the workspace's thumbnail-brand.md contract, inspect real source media, preserve approved likenesses, composite exact text and official logos deterministically, export the requested dimensions, and verify the finished asset before handoff.
---

# Brand Thumbnail

Create a finished asset unless the user explicitly asks for a prompt or plan only.

## Load the workspace contract

Look for `thumbnail-brand.md` in the current workspace. Treat it as the only brand-specific source of truth. Read it before choosing copy, art direction, colors, typography, logo treatment, or layout.

If it is missing:

- Do not create it automatically.
- If the user explicitly asks to initialize it, copy [references/brand-profile-template.md](references/brand-profile-template.md) to `thumbnail-brand.md` in the workspace. Preserve the bundled template as the generic source. Ask the user to replace every bracketed field before production.
- Otherwise, stop before production and request the completed contract. Continue with source inspection or a clearly labeled unbranded draft only when the user authorizes that narrower path.

Read [references/layouts.md](references/layouts.md) before choosing a composition. Read [references/output-contract.md](references/output-contract.md) before export and handoff.

## Workflow

### 1. Lock the deliverable

Infer the platform, source, output format, approved copy, and output location from the request. Default a vertical Reel cover to 1080 x 1920 PNG. Honor other requested formats and dimensions.

Ask at most one question, only when the missing answer would materially change the artifact. Track every requested deliverable internally. A thumbnail plus companion copy is two deliverables. For requested companion posts, use the installed `social-post-copy` skill with the explicitly resolved client manifest, source material, and voice references. Do not treat the cover headline as enough evidence for a post. Do not draft post copy when it was not requested.

### 2. Inspect real source material

For a local video, run:

```sh
scripts/analyze-video.sh '<video-path>' '<analysis-output-directory>'
```

The script requires `ffmpeg`, `ffprobe`, and POSIX shell utilities. Inspect `contact-sheet.jpg` visually. Read any supplied transcript and inspect supplied screenshots, portraits, logos, or other evidence.

Record:

- The actual claim, tension, or subject
- Up to three truthful hook candidates
- The strongest usable expression, gesture, object, or proof
- Existing captions or objects that constrain placement
- Source dimensions and orientation
- Any uncertainty that limits the claim

Never infer the topic from a filename when the media is available. Do not turn uncertain transcript language into a definitive claim.

### 3. Select the hook

Choose one source-grounded hook. Prefer a recognizable problem, sharp contrast, concrete consequence, or distinct reframe. Keep cover copy short enough to read at phone size, usually 3 to 8 words. Use compact line breaks and avoid a one-word final line.

Treat user-approved wording, capitalization, punctuation, and line breaks as locked. Do not silently rewrite them.

### 4. Choose one composition

Select the layout that fits the source from [references/layouts.md](references/layouts.md). Let the hook and source frame determine the structure. Produce one primary direction first. Create alternatives only when requested or when a real testing plan requires them.

### 5. Build in separate layers

Keep generated treatment separate from exact elements:

1. Build or edit a text-free, logo-free background and subject treatment. Leave deliberate negative space for later compositing.
2. Composite the exact approved headline and official logo with a deterministic renderer such as SVG, HTML and CSS, Sharp, ImageMagick, Canva, or the workspace's established production system.

Never ask an image model to spell final copy or recreate an official logo. Never substitute a generated logo for an approved source asset.

When an approved source portrait or video frame exists, preserve the real person from that source. Do not synthesize, replace, or materially alter their identity. Keep natural facial structure, skin texture, and recognizable features. If no approved likeness exists, use a composition that does not invent one unless the user explicitly authorizes a fictional subject.

### 6. Apply the workspace brand

Use only the values in `thumbnail-brand.md`. Follow its colors, typography, logo rules, voice, audience, safe regions, and prohibited treatments. Do not invent missing brand rules.

Favor one dominant idea and one obvious reading path. Use decoration only when it clarifies the hook. Protect phone-size readability, crop safety, exact copy, and official asset fidelity.

### 7. Verify before handoff

Run:

```sh
scripts/verify-image.sh '<thumbnail-path>' 1080 1920
```

Replace the width and height when the request specifies another format. Then perform the visual QA in [references/output-contract.md](references/output-contract.md) at full size and approximately 25 percent scale.

Revise until both mechanical verification and visual QA pass. A script result does not replace visual inspection.

## Boundaries

- Do not publish, schedule, upload, or replace live assets without explicit authorization.
- Do not fabricate claims, metrics, testimonials, outcomes, interfaces, or evidence.
- Do not present a contact sheet, background, or prompt as a finished thumbnail.
- Do not claim completion until every requested deliverable exists and passes its applicable checks.
- Keep unrequested companion assets out of scope.
