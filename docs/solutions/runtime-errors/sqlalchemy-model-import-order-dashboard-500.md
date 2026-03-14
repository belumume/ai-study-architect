---
title: "SQLAlchemy string relationship references fail when models not imported"
category: runtime-errors
date: 2026-03-14
tags: [sqlalchemy, relationships, imports, production, dashboard, model-registry]
module: Dashboard, UserConceptMastery
symptom: "Dashboard 500 Internal Server Error on production after Phase 2 deploy"
root_cause: "SQLAlchemy string-based relationship('User') fails when target model not imported before query"
---

# SQLAlchemy Model Import Order Causes Production 500

## Problem

After deploying Phase 2 (concept extraction), the dashboard endpoint returned 500 on production. All tests passed locally and in CI. The error was `InvalidRequestError: expression 'User' failed to locate a name`.

## Root Cause

`UserConceptMastery` model has `user = relationship("User")` using a string reference. SQLAlchemy resolves string references lazily when the mapper is first configured (on first query). If the `User` model class hasn't been imported into the Python process by that point, the string lookup fails.

**Why tests passed:** `conftest.py` imports all models explicitly. The test session has every model registered before any query runs.

**Why production failed:** `main.py` didn't import `UserConceptMastery`, `Subject`, or several other models. Models were only imported transitively through API router imports, and the import order wasn't guaranteed to cover all relationship targets.

## Solution

Import ALL model modules explicitly in `main.py` before the FastAPI app starts:

```python
# main.py — after config imports, before app = FastAPI()
import app.models.user  # noqa: F401
import app.models.content  # noqa: F401
import app.models.study_session  # noqa: F401
import app.models.subject  # noqa: F401
import app.models.concept  # noqa: F401
import app.models.user_concept_mastery  # noqa: F401
import app.models.practice  # noqa: F401
import app.models.chat_message  # noqa: F401
```

## Additional Bug: SUM Returns None Over Empty Set

The dashboard mastery query used `func.sum(case(...))` which returns `None` (not `0`) when there are zero matching rows. This caused a `TypeError` when computing `mastery_index = mastered / total * 100` with `mastered = None`.

Fix: `mastered_concepts = (mastery_stats.mastered or 0) if mastery_stats else 0`

## Prevention

1. **When adding a new model with relationships:** Add its import to `main.py` immediately. Don't rely on transitive imports through routers.
2. **When using aggregate functions (SUM, AVG):** Always handle `None` return for empty result sets. `COUNT` returns `0` but `SUM`/`AVG` return `None`.
3. **Always test on production after deploy:** This class of bug (import order, empty-set edge cases) only surfaces in the deployed environment. Local tests and CI pass because the test harness is more complete than the app's startup sequence.

## Related

- Session 8 compound doc: `docs/solutions/integration-issues/full-product-build-mui-to-tailwind-migration.md` — similar pattern where CI passed but production failed
- MEMORY.md lesson: "Always test endpoints on production after deploy"
