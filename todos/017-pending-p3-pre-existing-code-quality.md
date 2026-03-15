---
status: complete
priority: p3
issue_id: "017"
tags: [code-review, code-quality, pre-existing]
dependencies: []
---

# Pre-existing code quality issues from CE review

## Items Resolved

1. **`_current_keys: dict[str, str | float]`** (security.py:24) — Fixed: type annotation now includes float for timestamps.

2. **`request.client` could be None** (backup.py) — Fixed: `request.client.host if request and request.client else "unknown"`.

3. **CSRF logs user IDs at INFO** (csrf.py) — Kept as-is: intentional security audit trail.

4. **`DATABASE_URL` property uses `os.getenv`** (config.py) — Kept as-is: correct for CF container runtime injection architecture.

5. **`except (JWTError, Exception):` redundant** (dependencies.py:175) — Fixed: simplified to `except Exception:`, removed unused `JWTError` import.

6. **`datetime.utcnow()` deprecated** — Fixed across all affected files: centralized `utcnow()` utility in `app.core.utils` returning naive UTC datetime for compatibility with `DateTime` columns. 19 files updated.

## Acceptance Criteria

- [x] All 6 items fixed or explicitly deferred with rationale
