# VeilSpace architecture

## Boundaries

Flutter Windows, Android, and web clients connect to one fixed HTTPS API. Only Windows watches a selected folder. Mobile and web select files manually. Configuration and credentials are operator concerns, absent from end-user screens.

Python FastAPI and a processing worker run on the Windows server. MySQL stores metadata and access rules; files live outside the public web root. API keys and MySQL credentials never ship with clients.

## Lifecycle

`queued -> extracting -> assessing -> sanitizing -> verifying -> published`

Any unsupported, ambiguous, incomplete, or failed job transitions to `pending` with a structured reason. A model's reported confidence alone is not sufficient to authorize publication. A member-facing library exposes only published sanitized revisions.

Raw uploads temporarily reach the private server staging area. Text sent to a cloud AI service also leaves this server. Do not claim local-only processing or guaranteed detection of every sensitive detail. Originals expire after processing or a bounded retention period; jobs cannot retain them indefinitely.

## Identity consistency

Aliases are scoped to one workspace. A protected mapping is accessible to processing code and authorized ownership/review flows, not ordinary members. Canonical exact matches can reuse aliases; ambiguous names or conflicts require review. Do not merge people solely because their names resemble each other.

## Cost controls

- Extract supported text with conventional libraries; use deterministic detection for predictable patterns.
- Key assessment caches by workspace, content digest, policy, and detector version.
- Avoid repeated assessments for unchanged uploads and debounced saves.
- Reuse chunk assessments only when relevant surrounding context is unchanged.
- Bound upload size, extracted text, model output, concurrency, and retries.
- Reserve estimated request costs atomically before dispatch. Stop new AI assessments when the remaining allowance is insufficient; reconcile actual usage afterward.
- Reading, previewing, downloading, and listing files never invoke AI.
- Exhausted limits leave jobs pending, not published through an unchecked fallback.

## Redaction output

Initial inputs are DOCX, TXT, and text-based PDF. Initial sanitized outputs are PDFs. Legacy DOC and scanned PDFs stay pending until a supported conversion/OCR pipeline exists. Remove sensitive underlying content and metadata; overlays alone do not redact. PDF annotations, embedded attachments, links, and metadata require explicit handling. Generated output is checked for known detected values, but that check is not a guarantee of complete privacy.

## Revisions

Store source identity separately from content digest so a changed file becomes a revision and a rename does not require another assessment. Preserve the current published revision until its replacement passes processing. Do not claim that deleting or replacing a server copy retracts a member's prior download.
