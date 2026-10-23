# Authentication

Authentication bodies are JSON. Protected routes require `Authorization: Bearer <token>`.

| Method | Route | Body |
| --- | --- | --- |
| POST | `/api/auth/register` | `email`, `display_name`, `password` |
| POST | `/api/auth/login` | `email`, `password` |
| GET | `/api/auth/me` | None |
| POST | `/api/auth/logout` | None |

Signup and login return `access_token`, `token_type`, `expires_at`, and `user`. Logout revokes the current session. New accounts join the shared workspace.

Passwords use salted scrypt. Only token hashes are stored. Sessions expire after 24 hours by default. Registration and session lifetime can be controlled on the server. Authentication attempts are limited per connection address.

## Documents

| Method | Route | Result |
| --- | --- | --- |
| POST | `/api/documents?filename=...&source_id=...` | Raw file body, queued revision; source ID is optional |
| GET | `/api/documents` | Owner's latest revisions, including pending files |
| GET | `/api/documents/shared` | Latest published revisions for the workspace |
| GET | `/api/documents/usage` | UTC daily request count, reservation and allowance |
| GET | `/api/documents/{id}/download` | Sanitized PDF, latest published revision |
| GET | `/api/documents/{id}/preview` | Sanitized published text as JSON |
| POST | `/api/documents/{id}/retry` | Owner retries a pending revision |
| DELETE | `/api/documents/{id}` | Owner deletes the document and revisions |

Original files have no download route. New accounts join a single shared workspace. Shared filenames use generic document IDs to avoid exposing original filenames.
