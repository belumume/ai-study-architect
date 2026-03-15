---
status: pending
priority: p2
issue_id: "014"
tags: [code-review, data-integrity, database]
dependencies: []
---

# Add partial unique index for one active session per user

## Problem Statement

The session state machine enforces "one active session per user" in application code, but there's no database-level constraint. Race conditions could create duplicate active sessions.

## Proposed Solution

Alembic migration adding: `CREATE UNIQUE INDEX ix_one_active_session ON study_sessions(user_id) WHERE status IN ('in_progress', 'paused')`

## Acceptance Criteria

- [ ] Partial unique index exists in production
- [ ] Attempting to start a second session raises IntegrityError (caught by endpoint)
- [ ] Migration tested locally before Neon deploy
