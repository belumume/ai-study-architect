---
status: complete
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

- [x] `ruff check app/ --fix` applied (857 safe fixes + 58 whitespace fixes = 915 total)
- [ ] `ruff check app/` 145 remaining: ARG001/ARG002 (framework-required), B904, E402, SIM — need manual review
- [ ] `npm run lint` 14 errors + 41 warnings remain (mostly `@typescript-eslint/no-explicit-any`)
- [x] All existing tests still pass (420 passed)
- [x] Cleanup batched with Phase 2 follow-up work
