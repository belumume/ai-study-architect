---
title: "Phase 2 Concept Extraction — 8 Bugs, 3 Pattern Clusters, 7 Prevention Strategies"
category: integration-issues
date: 2026-03-14
tags: [concept-extraction, sqlalchemy, ci-debugging, test-mocking, spa-routing, github-actions, production-debugging, compound-engineering]
module: [dashboard, concept-extraction, ci-cd, frontend, testing]
symptom: "Multiple production failures after Phase 2 deploy — dashboard 500, silent CI review, stuck extraction state"
root_cause: "Test environments more complete than production, CI permissions wrong, exception handling too narrow"
---

# Phase 2 Concept Extraction — Session 9 Compound Document

## Summary

Phase 2 shipped the concept extraction pipeline (Claude Structured Outputs, parallel chunk processing, Subject Detail page, dashboard mastery). After merge and deploy, 3 production bugs were found during UI testing that passed both local tests and CI. Additionally, 4 code bugs and 1 workflow lesson were discovered during implementation and code review.

**Key insight:** Test environments are MORE complete than production, not less. Tests import all models, have all fixtures, and run in a fully-configured session. Production has partial imports, empty data sets, and different initialization order. Bugs hide in the gap.

## Bug Catalog

### Bug 1: SQLAlchemy Model Import Order (Production 500)

**Symptom:** Dashboard returns 500 after deploy. `InvalidRequestError: expression 'User' failed to locate a name`.

**Root cause:** `UserConceptMastery` has `relationship("User")` using a string reference. SQLAlchemy resolves these lazily on first query. If `User` model hasn't been imported, the lookup fails. `main.py` didn't import all models — only those transitively pulled by router imports.

**Fix:** Import ALL 8 model modules explicitly in `main.py`:
```python
import app.models.user  # noqa: F401
import app.models.content  # noqa: F401
import app.models.study_session  # noqa: F401
import app.models.subject  # noqa: F401
import app.models.concept  # noqa: F401
import app.models.user_concept_mastery  # noqa: F401
import app.models.practice  # noqa: F401
import app.models.chat_message  # noqa: F401
```

**Why tests passed:** `conftest.py` imports all models. The test session has every model registered before any query.

**Related:** [sqlalchemy-model-import-order-dashboard-500.md](runtime-errors/sqlalchemy-model-import-order-dashboard-500.md)

---

### Bug 2: SUM Returns None Over Empty Sets

**Symptom:** Dashboard 500 even after model import fix. `TypeError` in mastery_index calculation.

**Root cause:** `func.sum(case(...))` returns `None` (not `0`) when there are zero matching rows. The code did `mastered_concepts / total_concepts * 100` where `mastered_concepts` was `None`.

**Fix:**
```python
# Before (crashes on None):
mastered_concepts = mastery_stats.mastered if mastery_stats else 0

# After (handles None from SUM):
mastered_concepts = (mastery_stats.mastered or 0) if mastery_stats else 0
```

**Why tests passed:** Test user had no mastery records, but the test didn't exercise the dashboard query with that user.

---

### Bug 3: Claude Code Review Action Silent Permission Failure

**Symptom:** Claude Code Review Action ran on every PR ($0.63+ per run), completed "successfully" (green check), but never posted any review comments.

**Root cause:** Workflow had `pull-requests: read`. Action needs `pull-requests: write` to post inline comments. `permission_denials_count: 2` in logs was the only clue.

**Fix:** Change `pull-requests: read` to `pull-requests: write` in both `claude-code-review.yml` and `claude.yml`.

**Impact:** Every PR since setup had its Claude review discarded silently.

**Related:** [claude-code-review-action-silent-permission-failure.md](integration-issues/claude-code-review-action-silent-permission-failure.md)

---

### Bug 4: contentId="" Placeholder

**Symptom:** ExtractionTrigger component received empty string for `contentId`. Every extraction click would fail.

**Root cause:** Subject Detail page had `<ExtractionTrigger contentId="" subjectId={id} .../>` because the endpoint didn't return content items. The developer (Claude) shipped a placeholder without flagging it.

**Fix:** Return `content_items` from subject detail endpoint. Render per-content-item extraction triggers.

**How discovered:** Export search agent found it by grep for `contentId=""`.

---

### Bug 5: `<a href>` vs `<Link to>` in SPA

**Symptom:** Clicking a subject card on the dashboard causes a full page reload, losing React Query cache, auth context, and all client-side state.

**Root cause:** `SubjectList.tsx` used `<a href={...}>` instead of React Router's `<Link to={...}>`. Native `<a>` tags trigger browser navigation, unmounting the React app.

**Fix:** Import `Link` from `react-router-dom`, replace `<a>` with `<Link>`.

**How discovered:** Export search agent found it.

---

### Bug 6: Test Mocking at Wrong Abstraction Level

**Symptom:** CI tests fail with `IntegrityError: FK violation` on `concepts.content_id`. Also: happy path tests silently pass locally but fail in CI.

**Root cause:** Tests mocked `httpx.AsyncClient` (the transport layer) but `_call_claude` creates its own client internally — the mock never intercepts. Additionally, tests used random UUIDs for `content_id`/`subject_id` without creating actual DB rows, violating FK constraints.

**Fix:** Mock at `_call_claude` method level (your code's boundary, not the library's). Create real `User`/`Subject`/`Content` records via `test_data` fixture.

---

### Bug 7: Stuck `extraction_status` on Unexpected Exceptions

**Symptom:** If extraction fails with anything other than `ExtractionError` (e.g., `httpx.TimeoutException`, `json.JSONDecodeError`), `extraction_status` stays `"extracting"` forever. The concurrency guard then blocks all future extraction attempts.

**Root cause:** `except ExtractionError` only catches the custom exception. All other exceptions propagate without resetting the status.

**Fix:** Add `except Exception` fallback that resets status to `"failed"`:
```python
except ExtractionError as e:
    content.extraction_status = "failed"
    ...
except Exception as e:
    content.extraction_status = "failed"
    content.extraction_error = f"Unexpected: {e!s}"[:500]
    db.commit()
    raise HTTPException(500, "Extraction error") from e
```

---

### Lesson 8: Deepening != Review (Workflow)

**Symptom:** `/plan_review` referenced in workflow docs but doesn't exist as a skill.

**Root cause:** Deepening (adds research/detail, makes plan bigger) was conflated with review (challenges with skepticism, removes YAGNI, makes plan leaner). They serve opposite functions.

**Resolution:** `/plan_review` maps to `/ce:review <plan.md>` (thorough, multi-agent with simplicity reviewer) or `/document-review` (quick clarity check). Session 8 proved `/ce:review` finds items deepening misses — the simplicity reviewer found 7 YAGNI items and forced a 14-point reconciliation.

---

## Pattern Clusters

### Cluster A: "Production-Only Failures"
Bugs 1, 2 — test environments are more complete than production.
- Tests import all models → production doesn't
- Tests don't exercise empty-data edge cases → production has users with 0 concepts
- **Prevention:** Post-deploy UI testing is mandatory. Add `test_dashboard_zero_concepts` test.

### Cluster B: "CI Looks Green But Is Broken"
Bug 3, plus session 8's semgrep config 404.
- Actions complete "successfully" but produce no output
- Green check ≠ working action
- **Prevention:** Verify actions produce output. Check for `permission_denials_count` in logs.

### Cluster C: "Incomplete Implementations Shipped"
Bugs 4, 5, 7 — code that compiles but doesn't work correctly.
- Placeholders, wrong HTML elements, narrow exception handling
- **Prevention:** Export search (grep for TODO/""/placeholder), code review, exception handling patterns.

## Prevention Strategies

1. **Model imports:** Centralize in `main.py`. Add test that resolves all mapper relationships.
2. **SQL aggregates:** Always `or 0` on SUM/AVG results. Test with empty data sets.
3. **CI permissions:** Any action that posts output needs `write`. Verify by checking logs for denials.
4. **No placeholders:** Grep for `=""`, `TODO`, `FIXME` before push. Use sentinel values that fail loudly.
5. **SPA routing:** ESLint or grep for `<a href="/"` in `.tsx` — must be `<Link>`.
6. **Mock at YOUR boundary:** Mock `_call_claude` not `httpx`. Create real FK-valid test data.
7. **State transitions:** Any transitional status MUST have catch-all exception handler that resets.

## Session Metadata

- **Commits:** 7 on main post-merge (squash merge + 3 hotfixes + 2 compound docs + CI fix)
- **PR:** #26 (14 commits on feature branch, squash merged)
- **Tests:** 28 pass (19 extraction + 9 API)
- **Coverage:** 49% → 53% (ratcheted)
- **Export:** `~/.claude/exports/ai-study-architect/2026-03-14-session9-final.txt`

## Related Documentation

- [Session 8 compound doc](integration-issues/full-product-build-mui-to-tailwind-migration.md) — 13 symptoms, 11 solutions, 12 mistakes
- [SQLAlchemy import order](runtime-errors/sqlalchemy-model-import-order-dashboard-500.md) — standalone doc for Bug 1
- [Claude Code Review permissions](integration-issues/claude-code-review-action-silent-permission-failure.md) — standalone doc for Bug 3
