---
status: pending
priority: p3
issue_id: "007"
tags: [code-review, quality, lint]
dependencies: []
---

# Clean up pre-existing lint warnings across backend + frontend

## Problem Statement

During Phase 2 `/ce:work`, several pre-existing lint warnings were discovered but intentionally skipped to keep the PR diff focused on feature changes. These should be cleaned up in a separate PR.

## Findings

### Backend (ruff)
- `app/schemas/concept.py` — ~40 warnings: `Optional[X]` -> `X | None`, `List` -> `list`, `Dict` -> `dict` (typing module deprecations)
- `app/models/concept.py` — unused imports (`Optional`, `List`, `Enum`), import ordering
- `app/api/v1/dashboard.py` — unused variables (`today_start_utc`, `week_start_utc`), `is_active == True` -> `is_active`, `request` ARG001 (required by slowapi)
- `app/core/csrf.py` — ~15 warnings: unused imports, `Optional` -> `X | None`, unused `random_token`, missing `raise from`

### Frontend (eslint)
- 14 pre-existing errors, 41 warnings across non-Phase-2 files
- Mostly `@typescript-eslint/no-explicit-any` warnings

## Proposed Solutions

### Option 1: Batch fix with ruff --fix + eslint --fix

**Approach:** Run `ruff check app/ --fix` and `npx eslint src/ --fix` in a single cleanup PR. Review diff for any behavioral changes.

**Effort:** 30 minutes
**Risk:** Low — ruff and eslint --fix are safe for style-only changes

## Acceptance Criteria

- [ ] `ruff check app/` passes with 0 errors
- [ ] `npm run lint` passes with 0 warnings
- [ ] All existing tests still pass
- [ ] Cleanup is a separate PR from feature work
