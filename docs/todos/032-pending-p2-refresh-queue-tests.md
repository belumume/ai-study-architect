---
status: resolved
priority: p2
issue_id: "032"
tags: [code-review, quality]
---

## Problem Statement

Most complex new logic (concurrent request queuing with fan-out) has zero test coverage. Module-level mutable state not resettable in tests.

## Proposed Solution

Export `__resetRefreshStateForTesting`, add tests for: concurrent 401s, refresh failure redirect, state cleanup after completion.

## Files Affected

- `frontend/src/services/api.ts`
- `frontend/src/services/__tests__/api.test.ts`

## Effort Estimate

Small
