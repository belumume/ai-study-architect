---
status: resolved
priority: p1
issue_id: "030"
tags: [code-review, architecture]
---

## Problem Statement

`tokenStorage.ts` is 98 lines of dead code. Bearer injection in request interceptor creates stale-token problems the refresh interceptor then fixes. 7 of 8 methods are unused.

## Proposed Solution

Replace class with a one-shot `clearLegacyTokens()` function called at app startup. Remove Bearer injection from request interceptor. ~94 LOC reduction.

## Files Affected

- `frontend/src/services/tokenStorage.ts`
- `frontend/src/services/api.ts:51-57`
- `frontend/src/App.tsx:15`

## Effort Estimate

Small
