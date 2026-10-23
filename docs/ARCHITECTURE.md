# VeilSpace architecture

## Boundaries

Flutter Windows and Android clients connect to one fixed HTTP demo API. Web clients use their own origin. Only Windows watches a selected folder. Mobile and web select files manually. Configuration and credentials are operator concerns, absent from end-user screens.

Python FastAPI and a processing worker run on the Windows server. SQLite stores metadata and access rules; files live outside the public web root. API keys never ship with clients. The server executable initializes its database and directories beside itself.

## Lifecycle

`queued -> processing -> published`, with failures held as `pending`.

Any unsupported, ambiguous, incomplete, or failed job transitions to `pending` with a structured reason. A model's reported confidence alone is not sufficient to authorize publication. A member-facing library exposes only published sanitized revisions.

Raw uploads reach the private server staging area. Text sent to the AI service also leaves this server. Successful processing deletes the original. Pending originals remain private until retry or owner deletion. Processing is not local-only, and detection is not guaranteed to find every sensitive detail.

## Identity consistency

Aliases are scoped to the single workspace. The private mapping is accessible only to processing code. Case and whitespace normalization reuse exact name aliases. Ambiguous assessments remain pending. Similar-looking names are not merged automatically.

## Cost controls

- Extract supported text with conventional libraries; use deterministic detection for predictable patterns.
- Key assessment caches by workspace, content digest, policy, and detector version.
- Avoid repeated assessments for unchanged uploads and debounced saves.
- Bound upload size, extracted text, model output, concurrency, and retries.
- Reserve conservative estimated request costs atomically before dispatch. Stop new AI assessments when the allowance is insufficient. Reservations are not reduced afterward and are not provider billing totals.
- Reading, previewing, downloading, and listing files never invoke AI.
- Exhausted limits leave jobs pending, not published through an unchecked fallback.

## Redaction output

Initial inputs are DOCX, TXT, and text-based PDF. Initial sanitized outputs are PDFs. Legacy DOC and scanned PDFs stay pending until a supported conversion/OCR pipeline exists. Remove sensitive underlying content and metadata; overlays alone do not redact. PDF annotations, embedded attachments, links, and metadata require explicit handling. Generated output is checked for known detected values, but that check is not a guarantee of complete privacy.

## Revisions

Store source identity separately from content digest so a changed file becomes a revision and a rename does not require another assessment. Preserve the current published revision until its replacement passes processing. Do not claim that deleting or replacing a server copy retracts a member's prior download.
