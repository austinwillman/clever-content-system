# Confidential Content Runner Version 1 Design

## Status

Proposed design for owner review. This document defines the smallest commercially reusable release that proves a client-controlled confidential-content workflow.

## Product outcome

The Confidential Content Runner turns approved private source documents into source-grounded content candidates without giving the service provider access to the source documents. The client controls source selection, model credentials, processing, draft review, and release.

The first release proves one transaction:

```text
private source in -> structured candidates -> client approval -> approved output out
```

This creates leverage in two ways. It converts a custom privacy promise into a repeatable product boundary, and it lets one engine serve multiple regulated or trust-sensitive workflows through configuration instead of client-specific forks.

## Scope classification

This is a new subsystem inside the existing public engine. Version 1 is intentionally limited to a client-side runner and one approval flow.

## User and buyer

The initial buyer is the owner or CEO of a small professional-services or technology company who:

- has valuable conversations, interviews, notes, or transcripts
- wants outside help turning those sources into useful content
- will not grant the outside provider access to the raw material
- needs a security boundary they can personally understand and verify
- does not have an internal security engineering team

The end user is the client-side approver. The service provider supplies reusable research and content configuration, then receives only client-approved output.

## Trust statement

Version 1 may make this claim:

> The service provider cannot access source documents through the runner. Source documents are selected and processed with client-controlled credentials on the client's computer. The provider receives only output the client explicitly approves for release.

Version 1 must not claim:

- that no person or system can ever access the source
- that a compromised client device remains secure
- that the selected model provider cannot process the source
- that local processing provides confidential-computing guarantees
- that the runner is mathematically or cryptographically unbreakable

The client selects the model provider, owns the model account, and accepts that provider's data terms directly.

## Design principles

1. **Client custody:** Source files and model credentials stay under client control.
2. **No provider retrieval:** The service provider has no source-folder permission and no application path for retrieving source text.
3. **One-way configuration:** Research and content instructions enter the runner. Source-derived queries do not return to research agents or provider systems.
4. **Explicit release:** No draft or source-derived output leaves the device until a human approves it.
5. **Deterministic boundary:** Code, not the model, decides what may be released.
6. **Portable configuration:** Client identity, source connector, model adapter, research packet, output schema, and release destination are configuration.
7. **No private data in the engine:** The public repository contains reusable code, empty templates, schemas, tests, and generic documentation only.

## Version 1 architecture

```text
client-owned source folder
          |
          | explicit document selection
          v
client-side runner
  - source importer
  - signed configuration loader
  - client-owned model adapter
  - candidate validator
  - approval interface
  - metadata audit log
          |
          | explicit client approval
          v
approved candidate package
          |
          v
configured provider destination
```

The service provider does not host a transcript-processing backend in Version 1.

## Components

### 1. Source importer

The importer lets the client select specific source documents from a dedicated client-owned folder. The first connector targets Google Drive through Google Picker with the narrowest practical OAuth scope. The runner reads or exports only files explicitly selected by the client.

The importer must:

- display the selected file list before processing
- reject unsupported file types
- keep imported plaintext in a temporary per-run workspace
- never copy source text into repository paths, analytics, crash reports, or application logs
- remove the temporary workspace when the run completes, fails, or is cancelled

Email identifies the two test roles. Email is not a source-document transport.

### 2. Signed configuration packet

The provider creates a versioned packet containing:

- audience and positioning context
- content rules
- sanitized research evidence
- model instructions
- the allowed output schema
- release-policy settings
- packet version, digest, and signature

The packet contains no client transcript, credentials, or previously generated private output. The runner verifies its signature and digest before use. This establishes exactly which provider methodology was applied without giving the provider runtime access.

### 3. Model adapter

The model adapter sends the selected source and verified configuration directly from the client device to a model account controlled by the client.

Version 1 supports one model provider. The internal adapter contract must keep provider-specific authentication, request formatting, and response parsing isolated so later providers do not change the approval or output contracts.

The adapter must not expose browsing, shell, email, file-writing, deployment, or arbitrary HTTP tools to the model.

### 4. Candidate validator

The model returns content candidates matching the repository's content candidate contract. The deterministic validator rejects output that:

- does not match the exact schema
- lacks source references for material claims
- contains unapproved URLs, HTML, Markdown, executable content, or encoded blobs
- exceeds configured field lengths
- claims approval, publication, or performance that did not occur
- includes fields outside the release contract

Rejected output remains local and cannot be approved or delivered.

### 5. Approval interface

The interface shows the client:

- selected source filenames
- configuration packet version and digest
- proposed content candidates
- source references supporting each material claim
- the exact fields that will leave the device
- the configured recipient or destination

The client may approve selected candidates, reject them, or cancel the run. Editing a candidate invalidates any earlier approval and creates a new digest.

### 6. Release exporter

The exporter creates a structured package containing only approved candidate fields and approval evidence. It never includes source text, source files, prompts, model credentials, local paths, or rejected drafts.

Version 1 supports one simple delivery mechanism selected during implementation. The preferred pilot is a client-initiated file export because the client can inspect the package before manually sharing it. Automated email or webhook delivery remains out of scope until the release contract is proven.

### 7. Metadata audit log

The local audit log records:

- run identifier
- timestamps
- runner version and application digest
- configuration packet version and digest
- selected source identifiers and content hashes, but not filenames when filenames are sensitive
- model adapter name and model identifier
- validation result
- candidate and approval digests
- release time and destination type
- deletion result for the temporary workspace

It must not record source text, prompts, model responses, credentials, candidate copy, private filenames, or local filesystem paths.

## Data lifecycle

1. The client installs a signed runner build.
2. The client configures a client-owned model credential locally.
3. The runner verifies the provider's signed configuration packet.
4. The client selects approved source documents.
5. The importer creates an isolated temporary run workspace.
6. The model adapter requests structured candidates.
7. The validator accepts or rejects the response.
8. The client reviews the exact releasable fields.
9. The client approves selected candidates.
10. The exporter writes the approved package to a client-selected location.
11. The runner deletes the temporary workspace and records the deletion result.

No step gives the provider access to the source folder, model credential, temporary workspace, rejected output, or unapproved candidates.

## Failure behavior

The runner fails closed.

- Invalid configuration signature: stop before reading source documents.
- Expired or unsupported configuration version: stop and request a new packet.
- Source import failure: identify the failed file without logging its contents.
- Model request failure: preserve no remote retry queue and disclose whether the request may have reached the model provider.
- Invalid model output: keep it local, show the validation errors, and disable approval.
- Destination mismatch: stop release and require the client to confirm the destination again.
- Temporary-workspace deletion failure: show a blocking warning with the exact local cleanup action.
- Application integrity mismatch: refuse to process sources.

## Version 1 security controls

Required controls:

- signed application releases with a visible version and digest
- signed configuration packets
- client-owned source and model credentials
- no provider analytics or remote application telemetry
- no automatic updates while a run is active
- no model tools or arbitrary network destinations
- temporary per-run storage with cleanup verification
- strict structured-output validation
- explicit approval immediately before export
- source-free export packages
- negative tests for prompt injection and data exfiltration

The runner should make its network destinations visible to the user. Version 1 does not need to implement a universal endpoint firewall if the packaged runtime and model adapter can be independently verified to contact only the documented destinations.

## Pilot verification protocol

The pilot uses two accounts representing client and provider roles.

1. Confirm the provider account cannot open the source folder or selected files.
2. Add a unique synthetic canary string to a test source.
3. Run the application while recording its network destinations.
4. Confirm only the approved source service and model endpoint are contacted.
5. Include adversarial instructions in a test source and confirm nothing is released automatically.
6. Confirm invalid or extra output fields fail validation.
7. Approve one candidate and inspect the exported package byte for byte.
8. Confirm the canary, source text, prompts, credentials, and local paths are absent.
9. Confirm the temporary workspace is deleted.
10. Confirm the provider receives only the manually shared approved package.

The pilot report records the runner digest, configuration digest, model identifier, test results, and known limitations.

## Commercial product boundary

The commercial asset is not a custom desktop application for one content client. It is a reusable confidential transformation runner with replaceable configuration.

Version 1 separates:

| Product surface | Client-specific value | Reusable contract |
| --- | --- | --- |
| Source | Transcripts, interviews, notes | Source connector interface |
| Method | Audience strategy and content judgment | Signed configuration packet |
| Intelligence | Client-owned model account | Model adapter interface |
| Result | Content opportunities and drafts | Versioned output schema |
| Authority | Client approval decision | Approval digest and record |
| Delivery | Approved handoff destination | Export adapter interface |

This allows later offerings such as:

- confidential transcript-to-content
- executive interview-to-thought-leadership
- customer-call-to-product-insight
- legal matter-to-approved knowledge summary
- recruiting interview-to-structured evaluation
- financial conversation-to-client-approved action brief

Each offering requires its own claims, output schema, tests, and regulatory review. Shared infrastructure does not make every use case automatically compliant.

## Commercial packaging assumptions

Version 1 should be packageable as:

- a signed client-side runner
- a setup and verification service
- a recurring subscription for signed research and configuration packets
- an optional managed content service operating only on approved exports

The recurring value is the improving methodology, research, schemas, and workflow configuration. The application alone will become a commodity.

Licensing, billing, multi-user administration, automated updates, usage telemetry, and a customer dashboard are intentionally excluded from Version 1. They should follow evidence that buyers will complete and pay for the protected transaction.

## Competitive research workstream

Competitor analysis is separate from implementation. It should distinguish:

1. confidential-computing and clean-room infrastructure vendors
2. enterprise data-loss-prevention and AI-governance platforms
3. local or privacy-focused AI applications
4. vertical workflow products that process confidential source material

The comparison should measure buyer, custody model, provider access, deployment burden, approval control, model flexibility, pricing, and proof offered. A large competitor validates the risk category, but not this workflow or willingness to pay.

The initial positioning hypothesis is:

> Turn confidential conversations into approved business assets without handing the source material to the service provider.

This hypothesis must be tested in buyer conversations before it becomes website copy or a broad platform claim.

## Explicitly out of scope

- provider-hosted transcript processing
- live transcript-derived research queries
- background folder synchronization
- automatic publishing or distribution
- provider-accessible analytics
- multi-user organizations and role management
- confidential VMs or trusted execution environments
- local model inference
- multiple model or source providers
- billing and licensing enforcement
- mobile applications
- compliance certification

## Acceptance criteria

Version 1 is acceptable when:

- the provider account has no source-folder access
- only explicitly selected documents are processed
- the provider configuration signature is verified before source access
- the runner uses a client-owned model credential
- the model has no tools or arbitrary network access
- every candidate satisfies the existing content candidate contract
- no data leaves before explicit client approval
- the exported package contains only approved contract fields
- logs and temporary storage contain no retained private payload after the run
- the full pilot verification protocol passes against the signed release build
- documentation states the trust claim and limitations without exaggeration

## Implementation sequence

1. Define and test the signed configuration-packet contract.
2. Define the runner boundary and network contract.
3. Implement local source selection for generic text fixtures.
4. Connect one client-owned model adapter.
5. Reuse the existing content candidate validator.
6. Add the approval and local-export flow.
7. Add metadata-only auditing and cleanup verification.
8. Package and sign the runner.
9. Run the two-account pilot and produce the verification report.

The first implementation slice should stop after a generic local text fixture produces one valid, locally exported candidate through explicit approval. Google Drive and production model credentials follow only after that boundary is tested.
