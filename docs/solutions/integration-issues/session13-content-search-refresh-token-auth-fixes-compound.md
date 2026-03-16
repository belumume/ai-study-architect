---
title: "fix: Content Search 500 + Refresh Token Race Condition + Auth Token Cleanup"
category: integration-issues
date: 2026-03-16
tags: [sqlalchemy, auth, refresh-token, race-condition, cookie-auth, interceptor, content-search, pr-review-discipline]
affected_components:
  - backend/app/api/v1/content.py
  - frontend/src/services/api.ts
  - frontend/src/services/tokenStorage.ts
  - frontend/src/contexts/AuthContext.tsx
session: 13
pr_numbers: [42, 43, 44, 45, 46, 47]
resolved_todos: [027, 028]
created_todos: [029, 030, 031, 032, 033, 034, 035, 036, 037, 038, 039]
---

## Session Summary

Session 13 resolved two P2 bugs (content search 500, refresh token 30-minute logout) and established PR review discipline practices through an iterative 6-PR review cycle. The fixes evolved through reviewer feedback from Cubic, CodeRabbit, and Claude, with each round uncovering deeper issues in the auth token flow. Post-merge CE review (7 agents, serial) surfaced 13 pre-existing findings tracked as 11 new todos (029-039). An independent staleness audit (agent teammate) found and fixed 10 documentation inconsistencies.

## Problem 1: Content Search 500 (Todo 027)

### Symptoms
Every content search request returned HTTP 500 on Neon production. The endpoint had never been tested with a query parameter on production.

### Root Cause
`backend/app/api/v1/content.py` line 542 used `func.case()` for relevance-based ordering. SQLAlchemy's `func` namespace is for SQL functions (`func.count()`, `func.lower()`). SQL `CASE WHEN ... THEN ... ELSE ... END` is a statement construct, not a function. `func.case()` crashes at the Python level with `TypeError: Function.__init__() got an unexpected keyword argument 'else_'` before any SQL is generated.

### Solution

Import `case` directly from `sqlalchemy` (line 9):
```python
from sqlalchemy import and_, case, func
```

Replace `func.case(` with `case(` (line 542):
```python
.order_by(
    case(
        (func.lower(Content.title).like(search_term), 1),
        (func.lower(Content.description).like(search_term), 2),
        else_=3,
    ),
    Content.created_at.desc(),
)
```

### Verification
```python
# case() generates correct SQL:
# CASE WHEN (lower(title) LIKE ...) THEN 1 WHEN (lower(description) LIKE ...) THEN 2 ELSE 3 END

# func.case() crashes:
# TypeError: Function.__init__() got an unexpected keyword argument 'else_'
```

Production test: `GET /api/v1/content/search?q=test` returns 200 (was 500).

## Problem 2: Refresh Token Race Condition (Todo 028)

### Symptoms
Users logged out after ~30 minutes (access token expiry). The refresh flow existed in the backend but wasn't working end-to-end.

### Root Cause (Three-Layer)

**Layer 1 — Race condition:** Multiple concurrent requests fail with 401 simultaneously, each independently calling `/auth/refresh`. No coordination between them.

**Layer 2 — Stale Bearer tokens:** The app migrated from localStorage Bearer tokens to httpOnly cookies. `migrateFromLocalStorage()` (called on every boot in `App.tsx:15`) copies old tokens from localStorage to sessionStorage. The backend checks Bearer FIRST (`dependencies.py:48`), then cookies (`dependencies.py:53`). A stale Bearer token overrides the fresh cookie, causing 401 even after successful refresh.

**Layer 3 — Stale Authorization header on retry:** Even after `tokenStorage.clearTokens()`, the retried request carries the original `Authorization: Bearer <stale>` header from `error.config.headers`. The request interceptor only SET the header when a token existed but never DELETED it when absent.

### Solution (Evolved Through 7 Commits)

**Single-flight refresh queue** (`api.ts:32-47`):
```typescript
let isRefreshing = false
let refreshSubscribers: ((success: boolean) => void)[] = []

function onRefreshComplete(success: boolean) {
  for (const callback of refreshSubscribers) {
    callback(success)
  }
  refreshSubscribers = []
}
```

**Success boolean pattern** — uses boolean, not token presence, so it works in cookie-only mode where no token is in the response body.

**Queued request handling** (`api.ts:91-103`):
```typescript
if (isRefreshing) {
  return new Promise((resolve, reject) => {
    addRefreshSubscriber((success: boolean) => {
      if (success) {
        resolve(api(originalRequest))
      } else {
        reject(error)
      }
    })
  })
}
```

**Three safeguards against stale Bearer tokens:**

1. Clear tokenStorage after successful refresh (`api.ts:114-117`):
```typescript
tokenStorage.clearTokens()
```

2. Delete Authorization header when no token exists (`api.ts:52-57`):
```typescript
const token = tokenStorage.getAccessToken()
if (token) {
  config.headers.Authorization = `Bearer ${token}`
} else {
  delete config.headers.Authorization
}
```

3. `clearTokens()` clears BOTH storages (`tokenStorage.ts:65-70`):
```typescript
clearTokens(): void {
  sessionStorage.removeItem(this.ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(this.REFRESH_TOKEN_KEY)
  localStorage.removeItem(this.ACCESS_TOKEN_KEY)
  localStorage.removeItem(this.REFRESH_TOKEN_KEY)
}
```

### Verification (Playwright on Production)

Network trace after deleting access_token cookie and reloading:
```
GET /auth/me       → 401 (no access token)
POST /auth/refresh → 200 (refresh token valid, new cookies set)
GET /auth/me       → 200 (retried with new cookies)
GET /dashboard/    → 200 (dashboard loaded)
```
Dashboard displayed "Welcome, Smoke Test" — user stayed authenticated.

## Additional Fixes

- **Exception chaining**: Added `from e` to 5 raise statements in content.py (B904 ruff rule)
- **Dict comprehension**: Kept explicit `{k: v for k, v in rows}` with `# noqa: C416` for SQLAlchemy Row objects (verified all 3 patterns work but comprehension is clearest)
- **Dead code removal**: Removed stale `localStorage.removeItem()` from AuthContext catch block
- **Plan doc updates**: Phase 2 acceptance criteria checkboxes, completed_summary, scope ("concept CRUD API" -> deferred)

## Investigation Timeline

1. Read content.py and frontend auth code directly (Explore agents failed — prompt too long)
2. Identified `func.case()` as the content search crash
3. Identified refresh queue as missing for concurrent 401s
4. **PR #42**: First PR. Cubic and CodeRabbit reviewed. Claude's review missed because it posts to issues endpoint, not reviews endpoint
5. **PR #43-46**: Iterative fixes addressing reviewer findings. Each round uncovered deeper auth issues:
   - Cubic: reject queued requests on failure (not resolve with doomed requests)
   - Cubic: use success boolean (not token presence) for cookie-only mode
   - CodeRabbit: clear stale Bearer tokens from sessionStorage after refresh
   - CodeRabbit: delete Authorization header when no token in storage
   - CodeRabbit: clear localStorage in clearTokens() to prevent migration loop
6. **PR #47**: Final clean PR. All three reviewers clean. Squash-merged.
7. Production verification via Playwright confirmed both fixes working

## CE Review Findings (Post-Merge)

7 agents (serial mode). 0 findings on PR diff. 13 pre-existing issues surfaced:

| Priority | Count | Key Findings |
|----------|-------|-------------|
| P1 | 2 | Full-text search needed (LIKE on extracted_text catastrophic at scale), tokenStorage.ts is 98 lines of dead code |
| P2 | 9 | Refresh token replay (no server-side invalidation), refresh queue tests (zero coverage), get_optional_current_user cookie gap, tokens in response body, stats query consolidation, parallel R2 delete, view-count write-on-read, untyped _retry flag, err: any in catch blocks |

All tracked as todos 029-039.

## Prevention Strategies

### SQLAlchemy function vs expression confusion
- `func.*` is for database functions. `case`, `and_`, `or_` are expression constructs imported directly from `sqlalchemy`.
- Write query-level tests that compile SQL (even against SQLite) — the bug was invisible in HTTP-level tests.

### Auth token refresh race conditions
- Any interceptor with auto-retry on auth failure MUST implement single-flight refresh: one mutex, one queue, one notification.
- Signal refresh outcome with a success boolean, not token presence — cookie-only auth returns no token in the body.
- When queued requests are notified of failure, reject them — don't fire doomed retries.

### Stale header/token persistence
- After refresh, clear ALL token storage locations before retrying.
- Request interceptors must DELETE stale headers, not just skip setting them. Retried requests carry their original headers.
- When migrating auth mechanisms (Bearer to cookie), audit every read/write path of the old mechanism. `tokenStorage` was functionally dead but still caused harm through the migration function.

### Storage migration loops
- `clearTokens()` must clear ALL storage locations — not just the "current" one.
- Consider eliminating migration entirely: replace with a one-shot cleanup function (todo 030).

## Process Learnings

### PR Review Discipline (New Global Rule)
- Query ALL comment surfaces (reviews, issue comments, inline comments) — bots post unpredictably
- Read full bodies, no truncation — findings get buried in long text
- Verify every finding independently — never blind-accept or blind-reject
- Test claims with actual code when uncertain — don't argue from theory
- Open fresh PRs when stale comments accumulate

### Task List Continuity (Updated Global Rule)
- Every time tasks complete and work continues, create new tasks
- Committed pipeline steps (test -> review -> merge -> compound) are tasks
- Don't drop tracking during the iterative review phase — that's where steps get lost

### Independent Verification
- "I designed it this way" is not evidence for dismissing a reviewer's concern
- Multiple reviewers flagging the same issue is a signal to test harder, not dismiss faster
- Production testing (Playwright) resolved what code reading couldn't

## Test Cases That Should Exist

### Backend
- Content search: endpoint compiles valid SQL with query parameter (catches func.case vs case)
- Content search: relevance ordering (title > description > text)
- Content search: special characters in query (SQL injection/LIKE escaping)

### Frontend
- Concurrent 401s: only one refresh call, all retried on success
- Refresh failure: all queued requests reject, redirect to /login
- Stale Bearer: cleared from both storage and headers on retry
- Refresh/login endpoints: excluded from retry (no infinite loops)
- clearTokens: removes from both sessionStorage and localStorage
- migrateFromLocalStorage after clearTokens: no-op (no stale restoration)

### E2E
- Full login -> cookie deletion -> page reload -> dashboard loads (not login redirect)
- Content search returns 200 on production

## Cross-References

- **SQLAlchemy `case()` lineage**: Session 9 compound Bug 9 used `case()` correctly for dashboard. Content search was still using `func.case()`. This fix completes migration.
- **Auth infrastructure chain**: Session 11 (RSA key persistence across deploys) + Session 13 (refresh tokens within session) = complete auth persistence story.
- **Content search evolution**: Todo 027 (crash) -> PR #47 `case()` fix -> Todo 029 (full-text search performance). Crash -> correct -> optimized.
- **Token storage cleanup chain**: PR #47 (stale Bearer cleanup) -> Todo 030 (remove tokenStorage.ts, ~94 LOC) -> Todo 034 (stop returning tokens in body). Progressive elimination of Bearer path.

## Related Docs

- `docs/solutions/runtime-errors/sqlalchemy-model-import-order-dashboard-500.md` — SUM+case NULL handling
- `docs/solutions/integration-issues/phase2-concept-extraction-session9-compound.md` — `case()` import pattern for dashboard
- `docs/solutions/integration-issues/session11-phase2-followup-todos-rsa-migration-compound.md` — created todos 027+028
- `docs/solutions/integration-issues/session10-security-ci-phase2-monetization-compound.md` — user-scoping, cache patterns
- `docs/solutions/integration-issues/session12-dashboard-vercel-crash-backup-s3-aws-rotation.md` — "validate shape not truthiness"
