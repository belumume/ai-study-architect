---
status: complete
priority: p2
issue_id: "014"
tags: [code-review, data-integrity, database]
dependencies: []
---

# Add partial unique index for one active session per user

## Solution Implemented

Alembic migration `c1d2e3f4a5b6` creates:
```sql
CREATE UNIQUE INDEX ix_one_active_session
ON study_sessions (user_id)
WHERE status IN ('IN_PROGRESS'::sessionstatus, 'PAUSED'::sessionstatus)
```

Note: PostgreSQL enum labels are uppercase (IN_PROGRESS, PAUSED) despite Python enum values being lowercase. Required explicit `::sessionstatus` cast.

## Acceptance Criteria

- [x] Partial unique index exists (verified locally)
- [x] Attempting to start a second session raises IntegrityError (enforced by DB)
- [x] Migration tested locally before Neon deploy
