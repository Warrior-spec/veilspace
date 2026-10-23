# Authentication

All bodies are JSON. Protected routes require `Authorization: Bearer <token>`.

| Method | Route | Body |
| --- | --- | --- |
| POST | `/api/auth/register` | `email`, `display_name`, `password` |
| POST | `/api/auth/login` | `email`, `password` |
| GET | `/api/auth/me` | None |
| POST | `/api/auth/logout` | None |

Signup and login return `access_token`, `token_type`, `expires_at`, and `user`. Logout revokes the current session. New accounts join the shared workspace.

Passwords use salted scrypt. Only token hashes are stored. Sessions expire after 24 hours by default. Registration and session lifetime can be controlled on the server. Authentication attempts are limited per connection address.
