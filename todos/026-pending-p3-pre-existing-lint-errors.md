---
status: pending
priority: p3
issue_id: "026"
tags: [code-quality, lint, pre-existing]
dependencies: []
---

# Fix pre-existing lint errors (ESLint + ruff)

## ESLint (20 errors, 48 warnings)
- Unescaped entities in JSX (`'`, `"`) — react/no-unescaped-entities
- Unused vars in MUI components — @typescript-eslint/no-unused-vars
- `Function` type usage — @typescript-eslint/ban-types
- Unexpected constant condition — no-constant-condition
- Console statements — no-console

Most are in MUI legacy components (Phase 3 removal will eliminate them).

## Ruff (158 errors)
- ARG002: Unused method arguments (FastAPI endpoint patterns — `request` for rate limiter)
- Config deprecation: top-level linter settings need moving to `lint` section in pyproject.toml

## Acceptance Criteria
- [ ] ESLint: zero errors (warnings acceptable)
- [ ] Ruff: zero errors or all false positives suppressed with comments
