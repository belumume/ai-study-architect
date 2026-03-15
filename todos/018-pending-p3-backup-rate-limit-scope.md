---
status: complete
priority: p3
issue_id: "018"
tags: [code-review, pre-existing]
dependencies: []
---

# Scope backup rate limiting to /trigger endpoint only

## Solution Implemented

Extracted rate limiting from `verify_backup_token` (shared dependency for all backup endpoints) into `_check_trigger_rate_limit()` called only from the `/trigger` endpoint handler.

- `verify_backup_token`: Now only handles authentication (token validation + logging)
- `_check_trigger_rate_limit`: Handles the 1-per-hour rate limit, called at start of `/trigger`
- `/status`, `/test`, `/debug`: No longer affected by rate limit cooldown

## Acceptance Criteria

- [x] /status, /test, /debug accessible without rate limit cooldown
- [x] /trigger still rate-limited to 1 per hour
