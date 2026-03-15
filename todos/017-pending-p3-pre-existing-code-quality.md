---
status: pending
priority: p3
issue_id: "017"
tags: [code-review, code-quality, pre-existing]
dependencies: []
---

# Pre-existing code quality issues from CE review

## Items

1. **`_current_keys: dict[str, str]`** (security.py:24) — stores float timestamps, type annotation too narrow. Fix: `dict[str, str | float]`

2. **`request.client` could be None** (backup.py:40) — `request.client.host` crashes if client is None (test clients, reverse proxies). Fix: `request.client.host if request and request.client else "unknown"`

3. **CSRF logs user IDs at INFO** (csrf.py:53,56,60) — security monitoring logs include user IDs at INFO level. Consider DEBUG for privacy, or keep as intentional security audit trail.

4. **`DATABASE_URL` property uses `os.getenv` not `self`** (config.py:120) — Pydantic Settings loads .env into self, but property checks os.environ. Could diverge. Fix: use `self.DATABASE_URL`.

5. **`except (JWTError, Exception):` redundant** (dependencies.py:175) — Exception already covers JWTError. Fix: just `except Exception:`.

6. **`datetime.utcnow()` deprecated** (multiple files) — Deprecated in Python 3.12+. Fix: `datetime.now(UTC)`. Affects models, services, endpoints.

## Acceptance Criteria

- [ ] All 6 items fixed or explicitly deferred with rationale
