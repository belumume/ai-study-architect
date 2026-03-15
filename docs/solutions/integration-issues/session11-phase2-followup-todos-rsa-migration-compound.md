---
title: "Session 11: Phase 2 Follow-up Todos, RSA Persistence, Migration Compatibility"
category: integration-issues
date: 2026-03-15
session: 11
tags: [rsa-keys, datetime, migration, caching, jwt, fastapi-routing, svg, worktree-safety, pass-cli]
prs: [31, 33, 34, 35, 36, 37, 38]
todos_resolved: [009, 010, 011, 012, 014, 015, 017, 018, 019, 020, 021, 022, 023, 024]
todos_created: [025, 026, 027, 028]
---

# Session 11: Phase 2 Follow-up Todos + RSA Persistence + Migration Compatibility

## Overview

Resolved all 14 Phase 2 follow-up todos (009-024) identified by CE review agents in session 10. The P1 blocker (RSA key persistence) was the highest-impact fix -- users were logged out on every deploy. Session also discovered and fixed: datetime tz-aware/naive mismatch across 19 files, Neon migration incompatibility, and multiple process failures that led to 9 new behavioral rules.

**PRs**: #31 (14 todos), #33 (migration fix), #34 (wrangler update), #35-38 (session close items)
**Tests**: 430 backend + 86 frontend = 516. Coverage: 54.23% (ratcheted from 53% to 54%).
**Production**: Deployed and verified. RSA key persistence confirmed across both idle restart and deploy.

---

## Solutions

### 1. RSA Key Persistence (P1 Blocker)

**Problem**: Every deploy logged out all users. The Dockerfile generated fresh RSA keys at build time, invalidating all JWTs.

**Root cause**: Keys were ephemeral -- tied to the container image, not persisted externally.

**Fix**: Three-layer priority chain in `RSAKeyManager.initialize_keys()`:
1. Environment variables (production) -- base64-encoded PEM from CF Worker secrets
2. File-based keys (local dev)
3. Generate new (first-time setup)

```python
# backend/app/core/rsa_keys.py
def _load_keys_from_env(self) -> tuple[str, str] | None:
    from app.core.config import settings
    private_b64 = settings.RSA_PRIVATE_KEY
    public_b64 = settings.RSA_PUBLIC_KEY
    if not private_b64 or not public_b64:
        return None
    private_pem = base64.b64decode(private_b64).decode("utf-8")
    public_pem = base64.b64decode(public_b64).decode("utf-8")
    return private_pem, public_pem
```

Worker `envVars` mapping passes secrets to container. Dockerfile no longer generates keys. `rotate_keys()` warns when env vars are source of truth (rotation is in-memory only).

**Verified**: Token survived both idle container restart (6min gap) and production deploy (PR #34).

### 2. Datetime Timezone Safety

**Problem**: `TypeError: can't subtract offset-naive and offset-aware datetimes` -- crashed on session pause/stop when computing elapsed time.

**Root cause**: `datetime.now(UTC)` (the replacement for deprecated `datetime.utcnow()`) returns timezone-aware datetimes. SQLAlchemy `DateTime` columns store/return naive datetimes. Mixing them in arithmetic crashes.

**Fix**: Centralized utility:
```python
# backend/app/core/utils.py
def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
```

Replaced across 19 files. JWT `create_access_token`/`create_refresh_token` kept `datetime.now(UTC)` intentionally -- JWT expiry is epoch-based, not stored in DB.

### 3. Migration Neon Compatibility

**Problem**: Deploy failed: `operator does not exist: character varying = sessionstatus`.

**Root cause**: Local DB had a PG enum for `status` (uppercase labels). Neon production has VARCHAR (lowercase strings). The initial migration defines `status` as `String(11)`, not an enum. Local DB was an anomaly.

**Fix**: Plain string comparison matching the migration-defined VARCHAR column:
```sql
CREATE UNIQUE INDEX ix_one_active_session
ON study_sessions (user_id)
WHERE status IN ('in_progress', 'paused')
```

Idempotent -- drops broken old index if it exists. Portable downgrade included.

**Lesson**: Always verify schema from migration files, not local DB queries.

### 4. Dashboard Optimization

Three changes:
- **Redis caching**: 60s TTL per user, `dashboard:{user_id}` cache key
- **Cache invalidation**: `redis_cache.delete()` in session start/pause/resume/stop
- **Query elimination**: Derived global mastery from per-subject results (5 queries -> 3)

### 5. JWT kid Header (RFC 7515)

Moved `kid` from JWT payload to header via `headers={"kid": kid}` in `jwt.encode()`. Backward compatible -- `_find_key_for_token()` checks header first, falls back to claims for old tokens.

### 6. Content Search 422

**Root cause**: FastAPI route ordering -- `/{content_id}` declared before `/search`. Moved explicit routes above parameterized routes.

### 7. SVG Click Intercept

Added `pointer-events-none` to decorative SVG timer ring overlay on Focus page.

---

## Bugs Found During Session

| Bug | Severity | Status |
|-----|----------|--------|
| Content search 500 on Neon | P2 | Todo 027 |
| Refresh token flow broken (30min logout) | P2 | Todo 028 |
| Pre-existing lint errors (ESLint + ruff) | P3 | Todo 026 |
| Concurrency integration tests needed | P3 | Todo 025 |

---

## Prevention Strategies (9 New Rules)

### Anti-patterns identified and codified:

1. **Timezone mismatch**: Use `utcnow()` not `datetime.now(UTC)` for DB columns
2. **Schema divergence**: Verify from migration files, not local DB
3. **Worktree destruction**: Never `git worktree prune/remove` without approval
4. **Direct push to main**: All changes through branches/PRs
5. **Fake smoke tests**: Only `/smoke-test-production` counts
6. **Green-means-clean**: Read review comment bodies, not just check status
7. **Pass-CLI blind retrieval**: Always search before `--item-title`
8. **Route ordering**: Explicit routes before parameterized in FastAPI
9. **Destructive unblocking**: Never `git clean -fd` or `--force` to unblock checkout

**Cross-cutting theme**: 7 of 9 anti-patterns share a root cause -- treating a convenient local observation as ground truth instead of consulting the authoritative source.

---

## Rules & Config Changes

| File | Scope | Change |
|------|-------|--------|
| `~/.claude/rules/pass-cli.md` | Global | Full rewrite for v1.6.1. Search-first behavior, discovery-first commands, verified JSON paths |
| `~/.claude/rules/repo-hygiene.md` | Global | Worktree safety section, branch discipline rule |
| `~/.claude/rules/claude-code-windows.md` | Global | Multi-session worktree safety section |
| `~/.claude/rules/session-completion-checklist.md` | Global | Explicit `/smoke-test-production` reference |
| `~/.claude/CLAUDE.md` | Global | Polling behavior, destructive unblocking, merge review reading |
| Project `CLAUDE.md` | Project | RSA key info, `utcnow()` note, Phase 2 status |

### Feedback Memories Created (5)

| Memory | Lesson |
|--------|--------|
| `feedback_never_delete_worktrees.md` | Worktree prune destroyed parallel session's git state |
| `feedback_verify_schema_from_migrations.md` | Local DB had PG enum, migrations defined VARCHAR |
| `feedback_no_fake_smoke_tests.md` | Ad-hoc browser clicking isn't a smoke test |
| `feedback_pass_search_first.md` | Retrieved wrong Pass item by assuming name |
| `feedback_read_review_comments_before_merge.md` | Merged PR without reading Claude's actual findings |

---

## Cross-References

| Topic | Related Doc |
|-------|------------|
| RSA keys (todo origin) | Session 10 compound (line 480, todo 024) |
| Dashboard timezone crash | Session 8 compound (lines 108-111, `func.timezone()`) |
| Migration portability | Session 8 compound (lines 341-378, enum case) |
| Cache infrastructure bugs | Session 10 compound (lines 218-228, TTL/falsy/timeout fixes) |
| Concept extraction pipeline | Session 9 compound |

---

## Session Statistics

- **Duration**: ~8 hours
- **Commits**: 14 (across 8 PRs)
- **Files changed**: 50+ (PR #31) + review fixes
- **Lines**: +764 / -694 (PR #31), net reduction
- **Review cycles**: 3 rounds on PR #31, 4 iterations on PR #33 migration
- **Tools updated**: pass-cli 1.4.2->1.6.1, wrangler 4.72->4.73
- **RSA secrets stored**: 2 (RSA_PRIVATE_KEY, RSA_PUBLIC_KEY via wrangler)
