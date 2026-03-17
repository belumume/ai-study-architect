---
title: "Session 14: Batch Todo Resolution (029-045) — Security, Performance, Full-Text Search"
category: integration-issues
date: 2026-03-17
tags:
  - batch-resolution
  - security-hardening
  - performance-optimization
  - full-text-search
  - parallel-agents
  - auth-cookies
  - refresh-token
  - dead-code-removal
  - postgresql
  - testing
severity: P1-P2 mixed (2 P1 blockers + 10 P2 improvements + 4 P3 docs)
components:
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/content.py
  - backend/app/api/dependencies.py
  - backend/app/core/security.py
  - backend/app/models/content.py
  - backend/alembic/versions/d1e2f3a4b5c6
  - frontend/src/services/api.ts
  - frontend/src/services/tokenStorage.ts
  - frontend/src/contexts/AuthContext.tsx
  - backend/tests/test_concept_extraction_integration.py
  - frontend/src/services/__tests__/api.test.ts
session: 14
prs_merged: ["#51", "#53", "#54", "#55"]
prs_closed: ["#48", "#49", "#50", "#52"]
todos_resolved: ["029-039", "041-045"]
todos_created: ["046-049"]
---

# Session 14: Batch Todo Resolution (029-045)

## Problem

17 todos (029-045) accumulated from session 13's post-merge CE review of PR #47. Mix of P1 security gaps (dead tokenStorage code, missing full-text search index), P2 improvements (refresh token replay, stats query consolidation, view count write-on-read), and P3 documentation cleanup. Needed systematic resolution without quality regression.

### Triggers
- **Todo 029 (P1)**: Content search used `LIKE '%term%'` on `extracted_text` — no index, O(n * text_size). Catastrophic on Neon serverless.
- **Todo 030 (P1)**: `tokenStorage.ts` was ~94 LOC dead code — class superseded by httpOnly cookie auth but never removed.
- **Todos 031-041 (P2)**: No refresh replay protection, optional-auth missing cookie fallback, tokens in response body, 5 redundant stats queries, sequential R2 delete, sync view count writes, untyped `_retry`, `catch(err: any)`, no extraction integration tests.
- **Todos 042-045 (P3)**: Unchecked plan checkboxes, missing todo files, unannotated Figma/Framer deferrals, minor audit gaps.

## Approach

### PR Strategy: 3+1 Split by Risk Profile
- **PR #51** (docs): Zero-risk documentation cleanup (042-045). Merge first to clear noise.
- **PR #54** (code): 12 code todos (030-041) as one reviewable unit.
- **PR #53** (migration): Full-text search with schema change — independently revertable.
- **PR #55** (tracking): Deferred review findings as new todos (046-049).

Original PRs #48/#49/#50 were closed and reopened as #51/#53/#54 after 2 rounds of review accumulated stale comments.

### Parallel Agent Execution
Used `/resolve_todo_parallel` with 6 agents on non-overlapping files:

| Agent | Files | Todos | Effort |
|-------|-------|-------|--------|
| 1 | `dependencies.py` | 033 (cookie fallback) | Small |
| 2 | `AuthContext.tsx` | 039 (err:unknown) | Small |
| 3 | New test file | 041 (19 integration tests) | Medium |
| 4 | `content.py` (3 functions) | 035, 036, 037 | Small each |
| 5 | `auth.py` + `security.py` | 034, 031 | Medium (critical path) |
| 6 | `tokenStorage.ts` + `api.ts` | 030, 038 | Small |
| 7 (sequential after 6) | `api.test.ts` | 032 (refresh queue tests) | Small |

**File conflict mapping was the critical pre-step.** Before dispatching, every todo was mapped to affected files. Overlapping line ranges merged (034+031 to Agent 5). Same-file-different-functions grouped (035+036+037 to Agent 4). Agent 7 blocked on Agent 6 (tests depend on final api.ts shape).

Agent 5 (auth rotation) was the critical path — finished last after ~16 min. All others completed in 3-8 min.

## Key Solutions

### 1. Refresh Token Rotation with Redis Families (`auth.py`)
- Login creates UUID family, embeds `fid` claim in both access + refresh JWTs
- Stores `SHA-256(refresh_token)` in Redis key `refresh_family:{fid}` with 30-day TTL
- Refresh validates hash. Match = rotate (issue new, store new hash). Mismatch = invalidate entire family (theft).
- Logout passes `reason="logout"` to `_invalidate_family()` — prevents drowning real theft signals in logs
- **Redis-down safeguard**: `redis_cache.is_connected` check at login — skip `fid` when Redis unavailable, preventing false theft detection on recovery

### 2. Full-Text Search (`content.py`, migration `d1e2f3a4b5c6`)
- tsvector column + GIN index + PostgreSQL trigger
- Weighted: `setweight(title, 'A') || setweight(description, 'B') || setweight(extracted_text, 'C')`
- `plainto_tsquery` + `ts_rank` ordering replaces LIKE-based O(n*text_size) scan
- SQLAlchemy `after_create` event listener creates trigger + index for `create_all()` environments
- Drops obsolete LOWER() btree indexes
- Migration applied to Neon via deploy pipeline automatically

### 3. Cookie-Only Auth
- `tokenStorage.ts`: 98-line class replaced with 6-line `clearLegacyTokens()` stub
- Request interceptor: removed Bearer injection, always deletes stale Authorization header
- Login/refresh: return `{"token_type": "bearer"}` only — no tokens in response body
- `get_optional_current_user`: added cookie fallback matching `get_current_user` pattern
- `security.py`: `datetime.now(UTC)` replaced with `utcnow()` (4 occurrences)

### 4. Performance Optimizations (`content.py`)
- **Stats queries**: 5 → 2 (scalar aggregates + UNION ALL for grouped counts). Saves 3 Neon round-trips.
- **View count buffer**: Atomic Redis `INCR` (not get-then-set). `flush_view_counts()` exported for external scheduler, deletes keys after `db.commit()`.
- **Parallel R2 delete**: `ThreadPoolExecutor` with `max_workers=min(count, 10)`.

## Iteration & What Didn't Work

### CI Failures (2 rounds)
1. **InterceptorFn type**: First attempt used `(...args: unknown[]) => unknown` — caused `TS18046` on every interceptor test assertion. Fix: `(...args: any[]) => any` with eslint-disable.
2. **Redis mock for rotation test**: CI has no Redis → `is_connected` returns False → no `fid` in tokens → assertion fails. Fix: mock `redis_cache` with in-memory dict for hash storage.

### Review Fix Rounds (4 rounds, 3 reviewers)
| Round | Source | Findings | Fixes |
|-------|--------|----------|-------|
| 1 | Cubic/CodeRabbit/Claude (PRs #48-50) | Non-atomic counter, Redis-down-login, flush ordering, logout log, IMPL_STATUS session ref, brainstorm annotations | 7 fixes across 3 PRs |
| 2 | Cubic (PR #52) | `_get_client()` never raises (P1), test assertion `if` vs `assert`, flush race comment | 3 fixes |
| 3 | Cubic (PR #54) | Todo 031 doc overstates Redis fallback, login test remember_me coverage, refresh token fid assertion | 3 fixes |
| 4 | CodeRabbit (PR #53 rebase) | CREATE TRIGGER idempotency | False positive (PG transactional DDL) |

### Approaches That Failed
- **Refresh queue test**: First attempt tried making `api(config)` callable via `Object.assign(mockCallable, mockAxiosInstance)`. Failed — vitest mock structure doesn't support callable instances. Simplified to testing observable behavior only.
- **View count flush race fix**: First attempt was overcomplicated (conditional delete based on re-read). Simplified to delete-after-commit with documented acceptable race window.
- **Redis availability**: `redis_cache._get_client()` in try/except — `_get_client()` never raises (returns `_NoOpCache`). Fixed to use `is_connected` property.

## Reusable Patterns

### Axios Interceptor Testing (`api.test.ts`)
- `__resetRefreshStateForTesting()` export for resetting module-level state between tests
- Manual promise control for concurrent 401 queuing: `let resolveRefresh!: (value: unknown) => void`
- Key limitation: `api(config)` not callable in mock — test queuing and state, not retry flow

### SQLAlchemy Event Listener for DDL (`content.py`)
```python
@event.listens_for(Content.__table__, "after_create")
def _create_search_trigger(_target: sa.Table, connection: sa.Connection, **_kw: object) -> None:
```
Ensures PostgreSQL functions, triggers, and indexes exist in both Alembic-managed and `create_all()` environments.

### Redis Availability Check
- `_get_client()` never raises — it returns `_NoOpCache`
- Correct: call `_get_client()` for lazy init, then check `redis_cache.is_connected`

### conftest Token Extraction (cookie-only auth)
- Extract `access_token` from `response.cookies.get("access_token")`
- `assert access_token, "Login did not set access_token cookie"` — fail fast
- Set as Bearer header for test requests: `client.headers["Authorization"] = f"Bearer {access_token}"`

## Prevention Strategies

1. **Cache wrapper design**: When wrapping external services, ensure callers can distinguish "not found" from "connection error". Return sentinels or raise — never return the same value for both. The Redis cache layer has produced 3 bugs from this same root cause across sessions 10 and 14.

2. **CI parity for Redis**: Any feature adding Redis dependency must wire its CI mock into conftest in the same commit. Pattern: `unittest.mock.patch` at service level with in-memory dict, not network-level mocking.

3. **TypeScript test types**: Use `any` for mock interceptor functions in test files. `unknown` breaks strict mode on return value access. Add `eslint-disable` inline.

4. **PR hygiene**: Close noisy PRs and open fresh on same branch after 2+ review fix rounds. Prevents stale comment confusion across 3 reviewers.

5. **Datetime consistency**: `utcnow()` utility exists — add CI grep for `datetime.now(UTC)` to catch drift. Session 14 found 4 stragglers in `security.py` that session 11's centralization missed.

6. **Parallel agent orchestration**: Map file conflicts BEFORE dispatching. Group same-file-different-function todos into one agent. Sequence dependent agents explicitly. The critical path agent (most complex) finishes last — plan for it.

## Systemic Patterns (across sessions 10-14)

### Redis/Cache Sentinel Confusion (Sessions 10, 14, todo 047)
Cache layer returns `None` for both missing keys and errors. Produced bugs in 3 sessions:
- Session 10: TTL=0 treated as falsy, cached 0/""/false treated as miss
- Session 14: `_get_client()` no-op, non-atomic get-then-set
- Todo 047: `get()` indistinguishable error vs missing key

**Systemic fix needed**: `RedisCache` wrapper needs principled error contract distinguishing hit/miss/error.

### Auth Token Path Stragglers (Sessions 11, 13, 14)
Bearer-to-cookie migration was never a single planned effort. Each session finds another leaked assumption:
- Session 11: RSA keys ephemeral (tokens invalidated on deploy)
- Session 13: Stale Bearer overrides fresh cookie
- Session 14: Tokens in response body, no replay protection, optional-auth missing cookies
- Pending: Session cookie type not preserved (048), register error masking (049)

### CE Review Creates Fewer Todos Over Time
- Session 10: 8 resolved, 15 created (ratio 0.5)
- Session 13: 2 resolved, 11 created (ratio 0.2)
- Session 14: 17 resolved, 4 created (ratio 4.3)

Codebase approaching quality plateau — reviews find diminishing new architectural issues.

## Test Impact

| | Before | After | Delta |
|---|--------|-------|-------|
| Backend | 431 | 452 | +21 |
| Frontend | 86 | 91 | +5 |
| Total | 517 | 543 | +26 |
| Coverage | 54.23% | 54.37% | +0.14% |

## Deferred Items (tracked as todos)

- **046 (P2)**: `plainto_tsquery` loses substring/typeahead behavior
- **047 (P2)**: `redis_cache.get()` indistinguishable error vs missing key
- **048 (P2)**: Refresh endpoint always sets persistent cookies (should preserve session type)
- **049 (P3)**: Register catch masks login failure as registration error
- **040 (P2)**: Concept extraction quality testing + cross-chunk dedup test gap

## Related Documentation

- [Session 13 compound](session13-content-search-refresh-token-auth-fixes-compound.md) — predecessor, surfaced the 17 todos
- [Session 12 compound](session12-dashboard-vercel-crash-backup-s3-aws-rotation.md) — "validate shape not truthiness" pattern (same class as todo 047)
- [Session 11 compound](session11-phase2-followup-todos-rsa-migration-compound.md) — `utcnow()` centralization (session 14 found 4 stragglers), RSA key persistence
- [Session 10 compound](session10-security-ci-phase2-monetization-compound.md) — security hardening foundation, cache TTL/falsy bugs (same Redis sentinel confusion)
- [Session 9 compound](phase2-concept-extraction-session9-compound.md) — `case()` vs `func.case()` (eliminated by full-text search)
- Todos 046-049 in `docs/todos/` — deferred review findings from this session
