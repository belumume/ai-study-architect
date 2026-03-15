---
status: pending
priority: p3
issue_id: "018"
tags: [code-review, pre-existing]
dependencies: []
---

# Scope backup rate limiting to /trigger endpoint only

## Problem Statement

`verify_backup_token` applies rate limiting to all backup endpoints (/status, /test, /debug, /trigger). A successful backup blocks read-only status checks for 1 hour.

## Proposed Solution

Move rate limiting logic inside the `/trigger` endpoint handler, not in the shared dependency.

## Acceptance Criteria

- [ ] /status, /test, /debug accessible without rate limit cooldown
- [ ] /trigger still rate-limited to 1 per hour
