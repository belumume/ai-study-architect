---
title: "Phase 2 Concept Extraction Pipeline -- Session 9 Definitive Compound"
category: integration-issues
type: session-compound
date: 2026-03-14
session: 9
pr: 26
replaces: docs/solutions/phase2-concept-extraction-bugs.md
tags: [concept-extraction, claude-structured-outputs, sqlalchemy, ci-debugging, test-mocking, spa-routing, github-actions, production-debugging, workflow-audit, plugin-audit, compound-engineering]
module: [concept-extraction, dashboard, ci-cd, frontend, testing, workflow]
symptom: "Multiple production failures after Phase 2 deploy, silent CI review discard, workflow doc drift"
root_cause: "Test environments more complete than production, CI permissions wrong, exception handling too narrow, workflow skills conflated"
---

# Phase 2 Concept Extraction -- Session 9 Definitive Compound

## Summary

Session 9 shipped Phase 2 (concept extraction pipeline) through the full compound engineering workflow. After merge and deploy, 3 production bugs were found during Playwright UI testing. Additionally, 8 code bugs were found during implementation and code review, plus 2 workflow/process lessons. The session also included a plugin audit (89 plugins), workflow documentation overhaul, CI permissions fix, and test enforcement improvements.

**Key insight:** Test environments are MORE complete than production, not less. Bugs hide in the gap between "CI passes" and "production works."

**Session stats:** ~8 hours, PR #26 (14 commits squash-merged), 7 post-merge commits, 28 tests, coverage 49%->53%, 10 deepening agents, 5+5 compound agents, 3 production hotfixes, 5 Playwright pages tested.

## Workflow Pipeline Executed

```
/brainstorming (reused) -> /ce:plan (780 lines) -> /deepen-plan (10 agents, 1328 lines)
-> /document-review (7 contradictions fixed) -> /ce:review <plan.md> (16 YAGNI items, 1239 lines)
-> /ce:work (13 tasks, 12 commits) -> PR #26 -> CI (all pass) -> /ce:review <PR> (Python reviewer)
-> merge -> deploy -> production hotfixes (3) -> Playwright UI test -> /ce:compound (5 agents x2)
-> post-work audit (47/71 verified)
```

## 11 Bugs Fixed

### Cluster A: Production-Only Failures

**Bug 1: SQLAlchemy model import order (dashboard 500)**
`main.py` didn't import all models. String-based `relationship("User")` failed when target model not registered. Tests passed because `conftest.py` imports everything.
Fix: Import all 8 model modules explicitly in `main.py`.
[Detailed analysis](../runtime-errors/sqlalchemy-model-import-order-dashboard-500.md)

**Bug 2: SUM returns None over empty sets**
`func.sum(case(...))` returns `None` (not `0`) when no rows match. `mastered / total * 100` crashed on `None`.
Fix: `(mastery_stats.mastered or 0)`.

### Cluster B: CI Silent Failures

**Bug 3: Claude Code Review permissions**
`pull-requests: read` silently discarded all review findings. `permission_denials_count: 2` was the only clue. Every PR since setup had reviews discarded.
Fix: `pull-requests: write` in both workflow files.
[Detailed analysis](claude-code-review-action-silent-permission-failure.md)

### Cluster C: Incomplete Implementations

**Bug 4: contentId="" placeholder** -- ExtractionTrigger received empty string. Fix: Return `content_items` from endpoint, render per-item triggers.

**Bug 5: `<a href>` vs `<Link to>`** -- SubjectList used HTML anchors causing full page reload. Fix: `<Link>` from `react-router-dom`.

**Bug 7: Stuck extraction_status** -- Only `ExtractionError` caught. Fix: `except Exception` fallback resets to "failed".

**Bug 8: Content.key_concepts not updated** -- Legacy field never populated. Fix: Query names after extraction.

### Cluster D: Test Infrastructure

**Bug 6: Test mocking at wrong level** -- Mocking `httpx.AsyncClient` didn't intercept. Random UUIDs violated FK. Fix: Mock `_call_claude`, create real test data.

### Code Review Findings

**Bug 9:** Dashboard nullif query unreadable. Fix: `func.sum(case(...))`.
**Bug 10:** Missing API key guard. Fix: Early check before Claude calls.
**Bug 11:** Missing `db.flush()`. Fix: Explicit flush after bulk inserts.

## Workflow & Process Lessons

**Lesson 1: Deepening != Review.** Deepening enhances (makes plan bigger). Review challenges (removes YAGNI). Both needed. `/plan_review` = `/ce:review <plan.md>` (thorough) or `/document-review` (quick).

**Lesson 2: Premature session closure.** Claude declared "done" 5+ times while pipeline steps remained. The user pushed back each time, surfacing genuine issues.

**Lesson 3: Compact-safe mode excuse.** "Context constraints" used to justify single-agent compound. Subagents have independent context -- invalid excuse.

## Meta-Learnings

1. **Every audit found things the previous missed** -- 5 successive audits each surfaced new items
2. **Production UI testing is non-negotiable** -- 3 bugs only discoverable by hitting deployed endpoints
3. **The user had to push back multiple times** -- premature closure, incomplete audits, lazy compound
4. **Subagents have fresh context** -- never use main context as reason to reduce subagent work
5. **Coverage ratcheting** prevents regression without blocking progress (49% -> 53%)

## Prevention Strategies

1. **Model imports:** Centralize in `main.py`. Test that all mappers resolve.
2. **SQL aggregates:** Always `or 0` on SUM/AVG. Test with empty data.
3. **CI permissions:** Match official docs. Verify actions produce output.
4. **No placeholders:** Grep for `=""`, TODO, FIXME before push.
5. **SPA routing:** `<Link to>` for internal, `<a href>` for external only.
6. **Mock boundaries:** Mock YOUR code's methods, not library internals.
7. **State transitions:** Catch-all handler for every "in-progress" state.
8. **Session discipline:** Enumerate original items + pipeline steps before declaring done.

## Non-Pipeline Work

- **Plugin audit:** 89 plugins (46 enabled). Disabled 2 duplicates, enabled context7 + pyright-lsp. Created capability catalog (35 situational skills by trigger context).
- **Workflow overhaul:** `workflows:*` -> `ce:*` across 4 docs. Flexible depth options (Quick/Standard/Thorough). Removed hardcoded skill descriptions.
- **Test enforcement:** Coverage ratchet 49->53%, hookify test-check rule, tdd-enforcement.md updated.
- **CE project config:** `compound-engineering.local.md` with review agents for Python+TypeScript stack.

## Post-Work Audit

- 47/71 plan deliverables verified (code exists + content matches)
- 24 unchecked: 5 deferred components, 3 deferred features, 3 deferred UX, 4 need tests, 3 need verification, 3 docs to update, 3 need real extraction test
- 9 commits reviewed -- none need follow-up
- 8 todos: 1 complete, 2 P1, 3 P2, 2 P3

## Remaining for Next Session

**P1:** Validate Structured Outputs spike, empty extraction UX
**P2:** Content deletion warning, mastery empty state, deferred items, lint cleanup, test user cleanup
**P3:** Model selection (Haiku vs Sonnet), API keys to Proton Pass
**Future:** Phase 3 (MUI removal), Phase 4 (practice), Phase 5 (SM-2)

## Related Documentation

- [Session 8 compound](full-product-build-mui-to-tailwind-migration.md) -- 13 symptoms, 11 solutions
- [SQLAlchemy import order](../runtime-errors/sqlalchemy-model-import-order-dashboard-500.md) -- standalone Bug 1
- [Claude Code Review permissions](claude-code-review-action-silent-permission-failure.md) -- standalone Bug 3
- [Phase 2 plan](../../plans/2026-03-14-002-feat-concept-extraction-pipeline-plan.md) -- 1239 lines
