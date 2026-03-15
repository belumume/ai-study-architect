---
status: pending
priority: p3
issue_id: "025"
tags: [testing, concurrency, integration]
dependencies: []
---

# Add concurrency and storage failure integration tests

## Problem Statement

From PR #31 review (Claude Code Review + Cubic AI):
1. Content processing status updates and mastery updates could benefit from concurrency testing
2. Concurrent session creation should be tested against the new partial unique index
3. Storage failure scenarios (Redis down, R2 unavailable) need integration coverage

## Proposed Tests

1. **Concurrent session creation**: Two parallel requests to start sessions for the same user — second should get IntegrityError (caught by the partial unique index)
2. **Concurrent mastery updates**: Two parallel concept mastery updates for the same user/concept — should not create duplicate records
3. **Redis failure**: Dashboard should degrade gracefully (skip cache, query DB directly)
4. **R2 failure**: Content upload should fail cleanly with appropriate error message

## Acceptance Criteria

- [ ] Concurrent session test validates partial unique index
- [ ] Concurrent mastery update test validates unique constraint
- [ ] Cache failure test validates NoOpCache fallback
- [ ] Storage failure test validates error handling
