---
title: "Session 15: Batch Todo Resolution (026, 046-049) + Dependency Cleanup"
session: 15
date: 2026-03-17
type: batch-fix
pr_numbers: [56, 57, 58]
pr_merged: 58
branch: fix/resolve-todos-026-046-049-cache-lint
todos_resolved: ["026", "046", "047", "048", "049"]
todos_created: ["050", "051"]
components_affected:
  - backend/app/api/v1/content.py
  - backend/app/core/cache.py
  - backend/app/core/upstash_cache.py
  - backend/app/api/v1/auth.py
  - backend/app/core/security.py
  - frontend/src/contexts/AuthContext.tsx
  - backend/pyproject.toml
tests_added: 57
tests_total: 599
coverage: "54.94%"
review_rounds: 3
tags: [search, cache, auth, lint, dependency-cleanup, parallel-agents, tsquery, CacheResult, remember_me]
---

## Problem Statement

Session 15 addressed five accumulated technical debt items (todos 026, 046-049) spanning four distinct subsystems, plus unused dependency cleanup. Each todo represented a different deficiency class identified across sessions 10-14.

**Todo 046 (P2)**: Content search used `plainto_tsquery` which requires exact word matches. Partial queries like "algo" failed to match "algorithm." Users searching with incomplete words got zero results despite relevant content existing.

**Todo 047 (P2)**: `RedisCache.get()` returned `None` for both cache misses and connection errors. During an Upstash outage, the refresh token rotation logic would interpret a Redis error as "token family invalidated (theft)" and lock users out. This bug recurred across sessions 10, 14, and 15.

**Todo 048 (P2)**: The refresh endpoint always set persistent cookies with `max_age`, ignoring whether the user selected "remember me." Session cookies became persistent after first refresh.

**Todo 049 (P3)**: Registration success + auto-login failure showed "Registration failed" instead of telling the user their account was created.

**Todo 026 (P3)**: 151 ruff lint errors across `app/` with deprecated config structure.

**Dependency cleanup**: Zustand and Zod installed with zero imports. Husky + lint-staged confirmed active.

## Solutions

### Todo 046 -- Search Prefix Matching

**Root cause**: `plainto_tsquery` does not support prefix matching.

**Solution**: Custom `_build_prefix_tsquery()` with `to_tsquery`:

```python
def _build_prefix_tsquery(raw_query: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", raw_query)
    words = [_sanitize_tsquery_word(w) for w in normalized.split()]
    words = [w for w in words if w]
    if not words:
        return ""
    if len(words) == 1:
        return f"{words[0]}:*"
    return " & ".join(words[:-1]) + f" & {words[-1]}:*"
```

Single word: `algo:*`. Multi-word: `data & struct:*`. All non-alphanumeric chars normalized to spaces (handles `well-known`, `node.js`, `c/c++`). Sanitizer strips tsquery metacharacters to prevent injection.

**Files**: `backend/app/api/v1/content.py`. **Tests**: 33 in `test_content_search.py`.

### Todo 047 -- Redis Cache Error vs Missing Key

**Root cause**: `get()` returns `None` for both missing keys and connection errors.

**Solution**: `CacheResult` frozen dataclass + `get_with_status()`:

```python
@dataclass(frozen=True)
class CacheResult:
    value: Any
    found: bool
    error: bool
```

Auth refresh now branches three ways: `error` = skip replay detection (graceful degradation), `not found` = potential theft, `found` = verify hash. Existing `get()` preserved for ~20 callers.

**Files**: `cache.py`, `upstash_cache.py`, `auth.py`. **Tests**: 12 in `test_cache_result.py` + `test_refresh_improvements.py`.

### Todo 048 -- Refresh Preserve Session Cookie Type

**Root cause**: Refresh always set persistent `max_age`, ignoring login preference.

**Solution**: `"rem"` (remember_me) boolean claim in JWT refresh token:

```python
remember_me = claims.get("rem", True)  # Legacy default persistent
access_max_age = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60 if remember_me else None
```

`max_age=None` omits the attribute, making the browser treat it as a session cookie. Legacy tokens without `rem` default to `True`.

**Files**: `security.py`, `auth.py`. **Tests**: 13 in `test_refresh_improvements.py` (both legacy paths).

### Todo 049 -- Register Error Separation

**Root cause**: Single try/catch for both registration and auto-login.

**Solution**: Separated try/catch scopes. Auto-login failure shows "Account created successfully. Please log in." and navigates to `/login`.

**Files**: `frontend/src/contexts/AuthContext.tsx`. **Tests**: Covered by existing auth tests.

### Todo 026 -- Lint Cleanup (151 to 0)

**Root cause**: Deprecated ruff config + accumulated violations.

**Solution**: Restructured `pyproject.toml` to `[tool.ruff.lint]`. Added per-file-ignores for FastAPI DI (`ARG001`) and test fixtures (`ARG001` + `ARG002`). Fixed B904, I001, E402, F841, F401, SIM102, E712, E722 across 20+ files.

**Files**: `pyproject.toml` + 20+ backend files. **Tests**: Lint-only.

### Review-Driven Improvements

The tsquery sanitizer evolved through 3 iterations as reviewers caught edge cases:
1. **v1**: Stripped hyphens as injection chars. Cubic: `"well-known"` becomes `"wellknown"`.
2. **v2**: Replaced hyphens with spaces. Cubic: `"node.js"` still breaks.
3. **v3**: `re.sub(r"[^a-zA-Z0-9\s]", " ", ...)` -- whitelist, not blacklist.

Other fixes: PropertyMock simplified to direct attribute, backup `find_spec` reverted to actual Fernet import, legacy token test split into two paths (with-fid-no-rem + no-fid-no-rem), em dash replaced with ASCII dash.

## Prevention & Best Practices

### Whitelist, Don't Blacklist
When sanitizing input for a structured query language, strip everything except known-safe characters. Blacklists always miss characters. The `[^a-zA-Z0-9\s]` whitelist should have been the first attempt, not the third.

### Three-State Error Handling for Service Wrappers
Never let a wrapper function return the same value for "nothing there" and "couldn't reach the service." Design the error channel before the happy path. Use typed result objects (`CacheResult`, `Result[T]`) from the start.

### Adversarial Input Testing
For any sanitization function, parametrize tests across every ASCII punctuation character. Don't test just the happy path and one injection. A `@pytest.mark.parametrize("char", string.punctuation)` test costs one line and prevents three review rounds.

### Mock Hygiene
Prefer `mock.attr = value` over `type(mock).attr = PropertyMock(...)`. PropertyMock sets descriptors on the class, not the instance. Only needed when patching real `@property` on real classes. Watch for `type(mock).` in code review.

### Smaller PRs Over Large Multi-Todo PRs
Session 14's pattern (4 PRs for 16 todos, grouped by domain) had smoother reviews than session 15's pattern (1 PR for 5 todos, 3 close/reopen cycles). The overhead of separate PRs is less than the overhead of accumulated stale comments.

### File Pre-Existing Issues Immediately
Track pre-existing findings as todos on first mention. Referencing todo numbers in PR responses prevents reviewers from re-flagging the same issue across PR reopens.

## Related Documentation

- **Session 14 compound**: `docs/solutions/integration-issues/session14-batch-todo-resolution-auth-search-compound.md` -- direct predecessor, created todos 046-049
- **Session 13 compound**: `docs/solutions/integration-issues/session13-content-search-refresh-token-auth-fixes-compound.md` -- original search fix, refresh race condition
- **Session 10 compound**: `docs/solutions/integration-issues/session10-security-ci-phase2-monetization-compound.md` -- earliest cache bugs (TTL=0, falsy values)
- **Redis cache usage rule**: `.claude/rules/redis-cache-usage.md` -- updated with CacheResult pattern
- **Todos created**: `docs/todos/050-pending-p1-agents-context-overrides-user-id.md`, `docs/todos/051-pending-p2-agents-404-swallowed-by-except.md`

## Execution Approach

4 parallel agents (046 solo, 047+048 combined due to shared auth.py, 049 solo, 026 solo). Post-merge integration gate: full test suite + ruff + typecheck. 3 PR review rounds (cubic + CodeRabbit + claude-review), close-and-reopen pattern for stale comment hygiene. 10 review findings fixed, 3 tracked as pre-existing todos.

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Backend tests | 452 | 508 |
| Frontend tests | 91 | 91 |
| Coverage | 54% | 54.94% |
| Ruff errors | 151 | 0 |
| Open todos | 7 | 4 |
| Unused deps | zustand, zod | removed |
