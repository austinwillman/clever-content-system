# Commercial Setup and Operating Runbook

This system turns one client foundation into a persistent short-form video pipeline. It does not rebuild strategy every week.

Information and plan availability in this document were verified on 2026-08-20. Vendors change plans. Recheck linked official pages before selling a fixed software bundle.

## System flow

```text
Authorized client workspace and intake interview
                    |
                    v
       One-time foundation research
                    |
                    v
 Approved client foundation + demand map
                    |
                    v
         Persistent topic bank
                    |
        +-----------+-----------+
        |                       |
        v                       v
Batch signal scan        Content history
        |                       |
        +-----------+-----------+
                    v
        Ranked topic approval board
                    v
            Riverside interview
                    v
        Same-session hook pickups
                    v
      Transcript and editor package
                    v
        Edit, client review, schedule
```

Foundation research validates who the content is for, how that audience describes its pain, what the client can credibly say, and which outcomes matter. The batch signal scan adds timeliness. It does not replace the foundation.

## Required software

| Need | Recommended tool | Subscription | Connector or access | Fallback |
| --- | --- | --- | --- | --- |
| Repository and version control | GitHub | GitHub Free supports unlimited public and private repositories. Paid plans add team controls. | Git and GitHub authentication | Any Git remote, or a local repository ZIP if collaboration is not required |
| Agent workspace | Codex or Claude Code | Codex requires an eligible ChatGPT plan or usage credits. Claude Code supports Claude Pro or Max, Anthropic Console billing, Bedrock, or Vertex AI. | Local filesystem plus authorized apps or MCP servers | Run the same files with another capable coding agent and provide exports manually |
| Runtime and validation | Node.js 20 or newer | Free | Local terminal | A container or CI runner with Node.js 20 or newer |
| Source control review | GitHub pull request | Free for basic use | GitHub repository | Review the branch diff locally before merging |

Official references: [GitHub plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans), [Codex plan access](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan), and [Claude Code authentication](https://docs.anthropic.com/en/docs/claude-code/getting-started).

## Research and intake tools

None of these research subscriptions is universally required. The manifest declares what is connected, what needs an export, and the fallback for each client.

| Source | What it validates | Subscription guidance | Preferred connector | Fallback |
| --- | --- | --- | --- | --- |
| Google Drive | Positioning, offers, strategy, proposals, call notes, case studies, brand voice | ChatGPT Google Drive sync is available on eligible paid plans. Claude's Google Drive integration is available on paid Claude.ai plans. Claude Code may use an authorized MCP server. | Google Drive app or approved MCP server with read-only scope | Export an approved folder into `sources/intake/` and include an index of filenames and dates |
| Google Search Console | Owned search queries, pages, clicks, impressions, and search language | Free with a verified property | Connector, API, or dated CSV export | Export the Performance report as CSV |
| Metricool | Audience comments, inbox language, content performance, competitor observations, and scheduling | Free can support one brand and limited history. Starter supports more brands. Advanced adds team controls and API or MCP access. | Metricool MCP or API when the plan supports it | Export analytics and copy approved comment threads with URLs and dates |
| Plaud | Recorded client interviews and source transcripts | Starter includes limited monthly transcription. Paid tiers increase transcription capacity. | Plaud MCP when available | Export complete timestamped TXT, SRT, or JSON transcript files |
| Riverside | Mobile recording, separate tracks, transcription, and same-session pickups | Use Pro when the host needs the teleprompter. Business adds broader producer and guest capabilities. | Riverside studio and export | Any reliable camera or meeting platform, plus a separate transcript and a printed or shared hook sheet |
| Ahrefs | Search demand, questions, ranking difficulty, and competitor evidence | Optional paid plan or client export | API or dated export | Search Console, Google Trends, and attributed manual search-result observations |
| vidIQ | YouTube search and outlier observations | Optional paid plan | Export or authorized integration | YouTube search, native channel analytics, and dated manual observations |
| Apify | Structured public research at larger volume | Optional usage-based credits | Authorized actor or dataset | Review a small attributed sample manually |
| Native social analytics | Retention, average watch time, completion, shares, and account baseline | Included with the social account | Platform export or Metricool | Record screenshots or CSV exports with date range and account name |

Official references: [Google Drive sync for ChatGPT](https://help.openai.com/en/articles/10948259), [Claude Google Drive integration](https://support.anthropic.com/en/articles/10166901-using-the-google-docs-integration), [Google Search Console](https://support.google.com/webmasters/answer/9128668), [Metricool plans](https://metricool.com/pricing/), [Plaud plans](https://global.plaud.ai/pages/plaud-ai-plan-pricing), and [Riverside teleprompter](https://support.riverside.fm/hc/en-us/articles/14269623297309-Launch-the-teleprompter-in-the-studio).

## Production and scheduling tools

| Need | Recommended tool | Subscription | Fallback |
| --- | --- | --- | --- |
| Recorded interview | Riverside | Pro is the practical baseline for host teleprompter use | Phone camera, Zoom, Meet, or another recorder with a clean transcript export |
| Editing | The client's chosen editor in Premiere Pro, Final Cut Pro, CapCut, Descript, or Riverside | Tool-dependent | Any editor that accepts the source video, timestamps, captions, and editor brief |
| Asset storage | Google Drive, Dropbox, or approved client storage | Tool-dependent | Repository-excluded local storage with a documented handoff path |
| Work tracking | ClickUp | Optional | GitHub Issues, Notion, Trello, or the batch directory |
| Scheduling | Metricool or native platform scheduling | Metricool plan or the platform's native access | Manual scheduling after approval |

ClickUp is not required for the pipeline. If it is used, create tasks only after topic approval.

## One-time client foundation

The provider-led version is a client interview. The self-service version is an evidence extraction pass followed by a short gap interview.

### Provider-led intake

Use [client-foundation-intake.md](templates/client-foundation-intake.md) as the interview guide. Record the conversation, validate the complete transcript, and write each answer into `strategy/client-foundation.json` with evidence references.

Do not ask the client to approve an unstructured call summary. Present the structured foundation, unresolved conflicts, and proof limits. Once approved, set `status` to `approved` and build the topic bank.

### Self-service intake with Codex or Claude Code

Give the agent the manifest path and this instruction:

```text
Build my one-time client content foundation.

First, inspect the manifest and list the workspace connectors and local sources you can actually access. Search only the client-approved scope. Review customer conversations, reviews, CRM or support notes, search queries, proposals, service pages, case studies, strategy documents, brand guidance, and prior content when available.

Use the questions in content-system/templates/client-foundation-intake.md as the required field list. For every answer, preserve evidence references and label it confirmed, conflicted, inferred, or unresolved. Do not treat an inference as confirmed. Ask me one consolidated set of questions containing only the fields you could not answer or could not reconcile from the authorized sources.

Then show me the completed foundation for approval. Do not activate the topic bank until I approve it.
```

The agent must not browse private tools merely because a connector exists. The user must authorize the workspace and scope.

## Foundation research and validation

After extraction and before the topic bank:

1. Consolidate exact customer and ICP language.
2. Map phrases to pains, objections, desired outcomes, buyer stage, and source.
3. Compare customer language with the client's positioning and offer.
4. Flag mismatches rather than smoothing them over.
5. Validate recurring pains across at least two source categories when the evidence exists.
6. Record evidence limits when only one transcript or one source category is available.
7. Add dated records to `research/demand-map.csv`.
8. Record the completed pass and its limitations in `research/research-log.json`.
9. Build `strategy/topic-bank.json` from the approved foundation and validated evidence.

Source priority for ICP pain and language:

1. Customer calls, reviews, surveys, support, and CRM notes
2. Search Console queries, site search, inbox threads, and comments
3. Sales calls, objections, proposals, and lost-deal notes
4. Client marketing copy and strategy documents
5. Attributed public market sources

The research pass is incomplete when the system has only client assumptions and no customer or demand evidence. It may still proceed with explicit limitations, but it must not label the findings market-validated.

## Persistent topic bank

The topic bank is the durable baseline. Do not rebuild it for every batch.

Run a full refresh only when:

- The ICP, offer, or positioning changes
- Pillars or CTA strategy change
- A quarterly strategy review finds a gap
- The active bank cannot support a complete batch

Before each batch, run only the abbreviated signal scan. Attach new signals to existing topics when possible. Create a new topic only when the underlying problem or client POV is materially different.

## Search Target pass

After topic approval and before creating the speaker's Recording Card, research one audience query for each video. Use Search Console first when available, then Ahrefs or another keyword platform, native YouTube and social search evidence, audience language, and finally a dated manual Google observation.

Store the primary query, natural spoken phrase, intent, supporting terms, source, observation date, validation status, and limitations. Record volume and difficulty only when the connected source supplies them. A manual search result is `provisional`, not proof of volume. A customer phrase without query evidence is `qualitative_only`.

The Recording Card should ask a question that makes the search phrase natural to say once. Use the same search intent in the title, transcript, captions, description, and on-screen language. Do not stuff the phrase or make the speaker manage the research record.

## Hook evidence and same-session pickup

Store hook structures and attributed observations in `research/hook-library.json`.

Evidence grades:

- `hypothesis`: useful pattern with no retention evidence
- `validated`: one attributed observation or client result above baseline
- `proven`: repeated relevant retention evidence with source references

Views alone do not make a hook proven.

During the Riverside call, do not wait for the final transcript. Capture the owner problem, strongest phrase, client POV, story or proof, and conclusion as live structured notes. Generate three hook options matched to the library, let the provider select one or two, and record the pickups before moving to the next topic.

After the transcript is available, confirm that the hook delivers into the body without a bait-and-switch.

## Editor production package

Use `templates/editor-production-brief.json` after the Riverside transcript is complete. The package includes:

- Selected hook, take ID, timestamp, template ID, and evidence grade
- Body in and out timestamps
- Must-keep ideas and removable context
- Creative direction
- B-roll map with purpose and fallback
- Talking-head, green-screen, or hybrid route
- Rights and attribution status for external assets
- Caption and on-screen-text direction
- CTA and claim warnings
- What not to overproduce

Every visual intervention must prove, explain, orient, or reset attention.

## ClickUp statuses

Use no more than these six statuses:

1. `Ready to Record`
2. `Recorded`
3. `In Production`
4. `Client Review`
5. `Approved`
6. `Scheduled`

Track pillar, hook, production route, B-roll, green-screen asset, editor, CTA, revision count, platform, and scheduled time as fields. Do not turn fields into statuses.

## Installation and validation

The export-only v1 requires no API environment variables. Connector authentication stays inside Codex, Claude, or the provider platform.

If API adapters are added later, keep credentials in a gitignored `.env.local` file and document the adapter-specific names. A typical local file may contain placeholders such as:

```text
AHREFS_API_TOKEN=
APIFY_API_TOKEN=
METRICOOL_API_TOKEN=
```

Do not store credentials in the client manifest, research log, source exports, commits, or screenshots.

Before processing client data, confirm recording consent, connector scope, storage location, retention policy, and who can approve public claims.

### Local setup

From the repository root:

```sh
npm install
npm run test:content-system
npm run validate:content-system
npm run skills:check
```

Install the canonical skills for Codex and Claude Code:

```sh
npm run skills:install
```

Restart each agent or begin a new task so its skill registry refreshes.
