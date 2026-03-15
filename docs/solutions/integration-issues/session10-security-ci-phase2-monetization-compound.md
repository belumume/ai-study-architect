---
title: "Session 10: Phase 2 Follow-up — Todo Resolution, Security Hardening, Model Routing, Monetization Strategy, and GitHub Actions Infrastructure"
category: integration-issues
date: 2026-03-15
session: 10
tags:
  - phase-2
  - concept-extraction
  - structured-outputs
  - security-hardening
  - model-routing
  - monetization
  - github-actions
  - ci-cd
  - code-review
  - todo-resolution
  - rce-removal
  - info-disclosure
  - user-scoping
  - cache-ttl
  - extraction-status
  - vision-model-update
  - credential-exposure
  - hub-and-spoke
  - shared-workflow
  - pr-review-loop
  - false-positive-analysis
  - todo-tracking
severity: mixed (P1 security fixes, P2 feature work, P3 cleanup)
components_affected:
  - backend/app/api/v1/concepts.py
  - backend/app/api/v1/content.py
  - backend/app/api/v1/dashboard.py
  - backend/app/api/v1/endpoints/backup.py
  - backend/app/core/cache.py
  - backend/app/core/upstash_cache.py
  - backend/app/models/content.py
  - backend/app/schemas/concept.py
  - backend/app/services/claude_service.py
  - backend/app/services/concept_extraction.py
  - backend/app/services/vision_processor.py
  - backend/app/utils/file_validation.py
  - backend/app/utils/sanitization.py
  - backend/tests/test_concept_extraction.py
  - backend/tests/test_dashboard.py
  - backend/tests/test_sanitization.py
  - backend/tests/spike_structured_outputs.py
  - backend/tests/spike_model_comparison.py
  - frontend/src/components/dashboard/HeroMetrics.tsx
  - frontend/src/components/dashboard/SubjectList.tsx
  - frontend/src/components/subject-detail/ExtractionTrigger.tsx
  - frontend/src/components/subject-detail/SubjectMasteryOverview.tsx
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/pages/SubjectDetailPage.tsx
  - frontend/src/types/concept.ts
  - .github/workflows/claude-code-review.yml
  - .github/workflows/claude.yml
  - belumume/.github (new repo)
  - ~/.claude/commands/setup-claude-repo.md
  - ~/.claude/commands/refresh-claude-token.md
  - ~/.claude/rules/no-shortcuts.md
  - ~/.claude/rules/claude-github-actions.md
related_docs:
  - docs/solutions/integration-issues/phase2-concept-extraction-session9-compound.md
  - docs/solutions/integration-issues/phase2-followup-session10-compound.md
  - docs/plans/2026-03-14-002-feat-concept-extraction-pipeline-plan.md
  - docs/brainstorms/2026-03-14-monetization-strategy-brainstorm.md
  - docs/analysis/AI_EDUCATION_COST_MODELING_2026.md
  - docs/analysis/PRICING_DECISION_CARD.md
---

# Session 10: Comprehensive Compound Document

## Overview

Session 10 covered 5 major work phases, solving 36 distinct problems across 95 file changes. Produced 11 new todos (009-019), 3 strategy docs, and infrastructure spanning all 46 GitHub repositories. PR #29 squash-merged to main. 421 backend + 86 frontend tests pass, 53.9% coverage.

---

## Phase 1: Todo Completion (Problems 1-8)

### Problem 1: Structured Outputs API Contract Unvalidated

**Problem:** Concept extraction used `output_config.format` with `json_schema` but was never tested against the real API. Model IDs in the initial spike script were stale (from training data).

**Solution:** Spike test confirmed both `claude-sonnet-4-6` and `claude-haiku-4-5` return guaranteed-valid JSON via raw httpx with `anthropic-version: 2023-06-01`. No beta header needed (GA). Added `output_config` and `model` params to `ClaudeService.chat_completion()`.

**Code Changes:** `spike_structured_outputs.py` (new), `claude_service.py` (output_config + model params)

### Problem 2: No UX for Zero-Concept Extraction

**Problem:** Zero-concept extraction showed success toast and `completed` status. No distinction between "found concepts" and "found nothing."

**Solution:** Three-tier status: `completed`, `completed_empty`, `failed`. Added `message` field to `ConceptBulkCreateResponse`. Frontend warning toast for 0 concepts. Content items show "No concepts found" for `completed_empty`.

**Code Changes:** `concept.py` (message field), `concept_extraction.py` (early return), `concepts.py` (status logic), `ExtractionTrigger.tsx` (warning toast), `SubjectDetailPage.tsx` (status text)

### Problem 3: Dashboard Tests and Per-Subject Mastery

**Problem:** No dashboard tests. Per-subject mastery missing from API and UI. Coverage 53.48%.

**Solution:** 4 dashboard tests, zero-concept extraction test. Per-subject mastery query with `Concept` + `UserConceptMastery` outerjoin grouped by `subject_id`. Coverage rose to 54.29%.

**Code Changes:** `test_dashboard.py` (new), `test_concept_extraction.py` (+33 lines), `dashboard.py` (mastery query), `SubjectList.tsx` (concept count display)

### Problem 4: Content Deletion Silently Cascades

**Problem:** DELETE destroyed concepts and mastery records without warning.

**Solution:** `confirm_delete` query parameter. Without it: 409 with `{concepts_count, mastery_records}`. With `?confirm_delete=true`: proceeds.

**Code Changes:** `content.py` (confirm_delete param, cascade impact check)

### Problem 5: Misleading Mastery Empty States

**Problem:** Dashboard showed "0% ACROSS SUBJECTS." Subject Detail showed wall of zeros.

**Solution:** HeroMetrics shows concept count sublabel. SubjectMasteryOverview shows "Practice features coming soon" when all concepts are not_started.

**Code Changes:** `HeroMetrics.tsx` (totalConcepts prop, sublabel logic), `SubjectMasteryOverview.tsx` (not_started check), `DashboardPage.tsx` (pass totalConcepts)

### Problem 6: Lint Issues Accumulated

**Problem:** 1000+ lint warnings across backend.

**Solution:** ruff `--fix` applied 915 auto-fixes (857 safe + 58 whitespace). 145 remaining are framework-required.

### Problem 7: Extraction Model Cost Optimization

**Problem:** Sonnet used for all extraction without quality comparison.

**Solution:** Comparison: Haiku 3.6x cheaper ($0.016 vs $0.057), 2.6x faster (20s vs 51s), comparable quality (13 vs 15 concepts, same 0.92 confidence). Default changed to `claude-haiku-4-5`.

**Code Changes:** `spike_model_comparison.py` (new), `concept_extraction.py` (default model changed)

### Problem 8: Test User in Production

**Problem:** `uitest2026` remained in production Neon.

**Solution:** Deleted via browser automation (Neon SQL Editor). Manual cascade through all FK-dependent tables. Verified COUNT=0.

---

## Phase 2: Security Hardening (Problems 9-22)

### Problem 9: Dashboard Concept Count Not User-Scoped

**Problem:** Per-subject mastery query did not filter by `Content.user_id` -- latent cross-user data leak.

**Solution:** Added `.join(Content).filter(Content.user_id == current_user.id)`.

### Problem 10: Delete Cascade Mastery Count Not User-Scoped

**Problem:** Mastery count in 409 response included other users' records.

**Solution:** Added `UserConceptMastery.user_id == current_user.id` filter.

### Problem 11: Bare `except: pass` in Dashboard

**Problem:** 4 bare `except: pass` blocks swallowed all errors silently.

**Solution:** Added `logger.warning("...", exc_info=True)` to all 4.

### Problem 12: Backup Token Predictable Fallback

**Problem:** `BACKUP_TOKEN = "not-configured"` when env var missing -- known backdoor value.

**Solution:** `BACKUP_TOKEN = None` + 503 "Backup service not configured" when None. Fail-closed.

### Problem 13: Filename Sanitization Directory Traversal

**Problem:** `sanitize_filename(".....")` returned `".."` -- directory traversal.

**Solution:** Strip leading `..` sequences while preserving extensions. `"....pdf"` -> `".pdf"`, `".."` -> `"unnamed_file"`.

### Problem 14: Stack Trace Exposure in Backup Response

**Problem:** `traceback.format_exc()[-1000:]` leaked in HTTP response.

**Solution:** `logger.error(..., exc_info=True)` server-side. Generic `"Backup failed unexpectedly"` in response.

### Problem 15: Subprocess Output Leakage in Backup

**Problem:** `result.stdout[-1000:]` and `result.stderr[-1000:]` leaked in HTTP error responses.

**Solution:** Log server-side, generic error in HTTP response.

### Problem 16: Extraction Status Logic Ordering

**Problem:** `created_concepts == 0` checked before `chunks_failed`, masking failures as "completed_empty." Flagged by 3 independent reviewers.

**Solution:** Check `chunks_failed` first.

### Problem 17: Unsafe Deserialization (RCE) in Cache

**Problem:** `cache.py` used unsafe deserialization as fallback from Redis -- RCE vector if cache compromised.

**Solution:** Removed entirely. JSON-only serialization.

### Problem 18: Deprecated Vision Model

**Problem:** `gpt-4-vision-preview` hardcoded -- confirmed retired via OpenAI docs.

**Solution:** Changed to `os.getenv("OPENAI_MODEL", "gpt-5.4")`.

### Problem 19: psql Credential Exposure

**Problem:** `subprocess.run(["psql", db_url, ...])` exposed DATABASE_URL (with password) in process list.

**Solution:** Replaced with SQLAlchemy `engine.connect()` + `text()` query.

### Problem 20: Upstash Cache Missing Timeouts

**Problem:** 7 HTTP calls with no timeout -- could hang indefinitely.

**Solution:** `timeout=5` on all 7 calls.

### Problem 21: Cache TTL=0 Bug

**Problem:** `if ex:` treated TTL=0 as falsy, skipping expiration. Redis also rejects EX 0.

**Solution:** `if ex is not None and ex > 0:`.

### Problem 22: Cache Falsy Value Treated as Miss

**Problem:** `if result:` treated `0`, `""`, `false` as cache misses.

**Solution:** `if result is not None:`.

---

## Phase 3: Frontend Fixes (Problems 23-27)

### Problem 23: Missing `extracting` Status

**Problem:** No handling for in-progress extraction.

**Solution:** "Extracting concepts..." text + disabled extract button.

### Problem 24: Cache Key URL Encoding

**Problem:** Keys with `/` or `?` broke Upstash REST GET URL.

**Solution:** `quote(key, safe='')` for GET requests.

### Problem 25: Missing `partial` Extraction Status

**Problem:** No UI handling for partial extraction failures.

**Solution:** "Partial extraction -- some sections failed" text.

### Problem 26: Mastery Overview Ignoring `reviewing` State

**Problem:** `mastered === 0 && learning === 0` misclassified reviewing concepts as empty.

**Solution:** Changed to `not_started_count === total_concepts`.

### Problem 27: Model Override Reporting Wrong Model

**Problem:** Success response used `self.model` instead of `model or self.model` when override was passed.

**Solution:** Fixed in success path (line 146).

---

## Phase 4: GitHub Actions Infrastructure (Problems 28-32)

### Problem 28: Claude Review Action Not Posting Comments

**Problem:** `@v1` has broken comment posting (anthropics/claude-code-action#567). 5 permission denials without `--allowedTools`. Workflow file validation fails when PR branch differs from main.

**Solution:** Reverted to `@beta` + `direct_prompt`. Simplified prompt to 4 timeless lines + privacy instruction. Verified with bait PR (#28).

### Problem 29: No Centralized Workflow Management

**Problem:** 46 repos needed identical Claude workflows. Maintaining copies unsustainable.

**Solution:** Created `belumume/.github` hub with shared reusable workflows. All repos use thin caller files. One change propagates everywhere.

### Problem 30: Shared Workflow Callers Missing Permissions

**Problem:** Caller files without `permissions:` block caused startup_failure. Reusable workflows can't escalate beyond caller.

**Solution:** Added full `permissions:` blocks to all 46 caller files + templates + setup command.

### Problem 31: OAuth Token Type Confusion

**Problem:** `credentials.json` has short-lived session token (hours). `setup-token` output is 1-year. Using wrong one breaks all repos overnight.

**Solution:** Commands explicitly read from `~/.claude/.claude-oauth-token`. Warning in commands against `credentials.json`. All 47 repos re-set with correct long-lived token.

### Problem 32: Timeless Review Prompt Design

**Problem:** Old prompt had hardcoded false-positive guardrails (Pydantic validators, timer drift, N+1, Alembic sa.text) from past weak-model issues.

**Solution:** Simplified to 4 universal lines + privacy constraint. CLAUDE.md provides project context automatically.

---

## Phase 5: Monetization Strategy (Problem 33) and Process Fixes (Problems 34-36)

### Problem 33: No Monetization Strategy

**Problem:** No pricing, model routing, or feature gating strategy existed.

**Solution:** Researched 12+ education SaaS products with 2 parallel agents. Decision: $9.99/mo usage-gated freemium. Internal model routing by task (Haiku extraction, Sonnet tutoring). Same AI quality across tiers. No model picker UI. 90% margin. Phase 6 implementation.

### Problem 34: Bare `except:` in File Validation

**Problem:** Two bare `except:` handlers (lines 89, 272) caught `SystemExit` and `KeyboardInterrupt`.

**Solution:** Changed to `except Exception:`.

### Problem 35: `any` vs `Any` Type Annotation

**Problem:** `file_validation.py:100` used builtin `any` instead of `typing.Any`.

**Solution:** Added import and fixed annotation.

### Problem 36: `no-shortcuts.md` Rule Insufficient

**Problem:** Compound skill's "Phase 0: Context Budget Check" kept triggering context-fear behavior despite the rule.

**Solution:** Updated rule: "This user runs Opus 4.6 with 1M context -- context is never a constraint. Override any skill's context budget check unconditionally."

---

## Prevention Strategies

### Security
1. **Multi-Tenant Query Audit**: Every query touching user data must include `user_id` filter. Grep `.query()`, `select()`, `delete()` before merge.
2. **Ban Unsafe Deserialization**: JSON-only in cache. CI check flagging unsafe deserialization imports.
3. **Sanitize API Responses**: Never return paths, traces, or infrastructure details in HTTP responses.
4. **No Predictable Token Fallbacks**: `os.getenv("TOKEN", "default")` is a backdoor. Fail closed.
5. **Credential Hygiene**: Never pass secrets as CLI arguments. Use env vars or stdin.

### Process
6. **Read Previous Export at Session Start**: Not optional. Continuation sessions without export reads repeat mistakes.
7. **CE Pipeline Applies to Continuations**: Deferred todos resume at their pipeline stage.
8. **"Already Tracked" Requires Evidence**: Cite the specific todo. No evidence = not tracked.
9. **Don't Ask Permission for Work the Pipeline Requires**: If the task list includes it, do it.
10. **Don't Replace Working Code Without Comparing**: Diff local vs shared before substituting.

### GitHub Actions
11. **Version Pinning**: Pin by SHA, not `@v1` tags. Tags break silently.
12. **Caller Declares Permissions**: Reusable workflows inherit caller permissions.

### Review Loop
13. **Reviewer Trust Earned Per-Finding**: Each finding independently verified.
14. **Reviewer Hallucination Guard**: Verify model IDs, dates, versions from official docs.
15. **Deprecated APIs Are Ticking Clocks**: Retired = P1. Deprecated = P2. Automate detection.

---

## Lessons Learned

**L1.** Security gaps cluster around authorization, not authentication. Per-query scoping is where leaks happen.

**L2.** "Context constraints" is a fabricated excuse. Appeared 3 times despite a rule against it. The trigger was a skill's built-in Phase 0 check.

**L3.** Reusable workflow permissions are the caller's responsibility. The hub can't escalate for the caller.

**L4.** Sticky review comments degrade after many updates. Close and reopen PRs for clean review cycles.

**L5.** Continuation sessions without export reads repeat mistakes. The export provides continuity.

**L6.** `bare except: pass` is a bug factory. Catches `SystemExit` and `KeyboardInterrupt`.

**L7.** False positive dismissal requires the same rigor as investigation. "Pre-existing and minor" without evidence = ignoring.

**L8.** Each review run re-flags pre-existing issues. The reviewer has no memory. Fix or accept the loop.

**L9.** OAuth session tokens (hours) vs setup tokens (1 year) serve different purposes. Wrong one = time bomb.

**L10.** Hub-and-spoke architecture works. One change to `belumume/.github` propagates to 46 repos. But callers must declare permissions.

### Additional Prevention Strategies (from post-merge work)

16. **Production smoke test must be click-only**: Never type URLs after the login page. Direct URL navigation hides UX gaps (Focus page unreachable from empty dashboard was invisible until click-testing).
17. **Credential exposure requires immediate acknowledgment**: `credentials.json` was dumped in-session with live tokens for 10+ services. Flag immediately, not 2 hours later. Add credential files to "never read directly" list.
18. **Break infinite review loops with squash + fresh PR**: 7+ review runs re-flagging the same issues. Fix: squash all commits, close old PR, open fresh one. Limit to 3 review cycles per PR.
19. **Test user lifecycle is atomic**: Create, test, delete in the same session. `uitest2026` leaked from session 9. `smoketest2026` leaked from session 10. An admin delete endpoint would prevent this.
20. **"Design choice" is not a valid dismissal without a decision record**: Focus page inaccessibility was called a "known design choice" — nobody decided it, it was an oversight.
21. **Shared workflow callers must declare permissions**: First deploy to 46 repos failed because callers lacked `permissions:` blocks. Reusable workflows inherit, not escalate.
22. **Verify reviewer claims from official sources, not training data**: "claude-sonnet-4-6 is invalid" was false. Exact deprecation dates need web verification.
23. **Multi-round PR reviews have diminishing returns**: 7 runs cost ~$3.50. After run 3, marginal value drops sharply. Fix remaining findings in follow-up PRs.

### Additional Lessons Learned (from post-merge work)

**L11.** UI testing vs API testing: click-through tests discoverability and user flows. Direct URL tests routing and rendering. Both needed, different purposes.

**L12.** The "design choice" dodge is deferral without evidence. If no one explicitly decided it, it's a bug.

**L13.** Credential files dumped in session are a security incident, not an FYI.

**L14.** Multi-round PR review loops are expensive ($3.50 for 7 runs) with 60-70% duplicate findings per run.

**L15.** Hub-and-spoke eliminates per-repo maintenance but introduces single point of failure. One broken `.github` change breaks all 46 repos.

**L16.** Production smoke tests must exercise the full data lifecycle (create subject, run session, check dashboard), not just empty states.

**L17.** Pass-cli slowness in Bash tool is real operational friction. Direct lookups (~2s) work; list+filter (~10s) often times out.

**L18.** `/audit-staleness` command created to prevent cross-file contradictions. Added to session-discipline rule as required before session close.

---

## Related Documents

### Created This Session
- `docs/brainstorms/2026-03-14-monetization-strategy-brainstorm.md` -- Monetization strategy
- `docs/analysis/AI_EDUCATION_COST_MODELING_2026.md` -- AI cost modeling (~400 lines)
- `docs/analysis/PRICING_DECISION_CARD.md` -- Pricing decision card (~200 lines)
- `docs/analysis/COST_COMPARISON_TABLE.csv` -- Cost comparison spreadsheet
- `docs/solutions/integration-issues/phase2-followup-session10-compound.md` -- Earlier partial compound
- `~/.claude/projects/.../memory/ai-api-cost-research-march2026.md` -- Cost research (subagent)
- `~/.claude/projects/.../memory/education-saas-pricing-research.md` -- Pricing research (subagent)
- `~/.claude/projects/.../memory/feedback_follow_ce_pipeline.md` -- CE pipeline continuity feedback

### Prior Sessions
- `docs/solutions/integration-issues/phase2-concept-extraction-session9-compound.md` -- Session 9
- `docs/solutions/integration-issues/full-product-build-mui-to-tailwind-migration.md` -- Session 8
- `docs/solutions/integration-issues/claude-code-review-action-silent-permission-failure.md` -- CI permissions fix
- `docs/solutions/runtime-errors/sqlalchemy-model-import-order-dashboard-500.md` -- Dashboard 500 fix
- `docs/plans/2026-03-14-002-feat-concept-extraction-pipeline-plan.md` -- Phase 2 plan (1328 lines)

### New Infrastructure
- `belumume/.github` repo -- Shared workflows hub (reusable workflows + templates for 46 repos)
- `~/.claude/commands/setup-claude-repo.md` -- Repo setup slash command
- `~/.claude/commands/refresh-claude-token.md` -- Token refresh slash command
- `~/.claude/commands/audit-staleness.md` -- Staleness audit slash command
- `~/.claude/commands/session-complete.md` -- 7-check session completion checklist command
- `~/.claude/commands/smoke-test-production.md` -- Full production smoke test (extracted from session-complete)
- `~/.claude/rules/session-completion-checklist.md` -- Rule enforcing 7 checks before session close
- `~/.claude/rules/claude-github-actions.md` -- Actions configuration rule
- `~/.claude/rules/no-shortcuts.md` -- Updated: override context budget checks unconditionally
- `~/.claude/rules/pass-cli.md` -- Updated: performance patterns, Pass-Query recommendation
- `~/.claude/.claude-oauth-token` -- 1-year token for GitHub Actions (from `claude setup-token`)
- `~/.claude/projects/C--Users-elzai/memory/automation-reference.md` -- Updated: GitHub Actions Management section
- `~/.local/bin/setup-claude-repo.sh` -- Shell script version

### Spike Tests
- `backend/tests/spike_structured_outputs.py` -- Structured Outputs validation
- `backend/tests/spike_model_comparison.py` -- Sonnet vs Haiku quality/cost comparison

### New Tests
- `backend/tests/test_dashboard.py` -- Dashboard endpoint tests (4 tests)
- `backend/tests/test_concept_extraction.py` -- Zero-concept extraction test added
- `backend/tests/test_sanitization.py` -- Traversal + extension preservation tests added

### Session Export
- `~/.claude/exports/ai-study-architect/2026-03-15-session10-phase2-followup-security-actions-monetization.txt` -- Full export (9103 lines)

### External References
- `anthropics/claude-code-action#567` -- @v1 breaks PR comment posting (confirmed, unresolved)
- `anthropics/claude-code-action@beta` -- working version used (posts comments correctly)
- `github.com/apps/claude` -- GitHub App installed across all repos
- `platform.claude.com/docs/en/api/versioning` -- 2023-06-01 is current/only API version
- `platform.openai.com/docs/deprecations` -- gpt-4-vision-preview confirmed retired

### Todos

| Todo | Priority | Description | Status |
|------|----------|-------------|--------|
| 009 | P2 | Dashboard Redis caching | Pending |
| 010 | P2 | confirm_delete tests | Pending |
| 011 | P2 | Redundant dashboard query | Pending |
| 012 | P3 | Unused schemas cleanup | Pending |
| 013 | P1 | Vision model update | Complete |
| 014 | P2 | Session unique constraint | Pending |
| 015 | P2 | JWT kid in header | Pending |
| 016 | P2 | psql credential exposure | Complete |
| 017 | P3 | Pre-existing code quality (6 items) | Pending |
| 018 | P3 | Backup rate limit scope | Pending |
| 019 | P3 | Vision processor dead import | Pending |
| 020 | P2 | SVG timer ring intercepts button clicks on Focus | Pending |
| 021 | P3 | Focus page not discoverable from empty dashboard | Pending |
| 022 | P3 | Content search returns 422 | Pending |
| 023 | P3 | Subject card progress bar at 0% | Pending |
| 024 | P1 | RSA key persistence (users logged out on deploy) | Pending |

---

## Production Smoke Test (Post-Merge)

Comprehensive browser + API test on https://aistudyarchitect.com after deploy.

**UI Routes Tested (click-only navigation):**
- Login/Register: Working, dark theme
- Dashboard (empty + with data): Working, correct empty states, HeroMetrics sublabels
- Study/Chat: Working (streaming, Socratic), MUI white panel (Phase 3)
- Content: Working, MUI white panel (Phase 3)
- Subject Detail: Working, mastery ring, empty state
- Focus (setup/timer/complete): Working, session recorded to dashboard

**API Endpoints Verified:** dashboard, subjects, subject detail, content, sessions, auth, health, CSRF — all 200. Unauthenticated = 401. Nonexistent = 404. API docs blocked = 404.

**Bugs Found:** 4 (todos 020-023 above)

---

## Test Results

- Backend: 422 passed, 53.98% coverage
- Frontend: 86 passed, TypeScript clean
- PR #29 squash-merged to main
- Production smoke test: all routes functional, 4 bugs tracked
- Test users: uitest2026 deleted, smoketest2026 needs Neon cleanup
- PR lifecycle: #27 (closed), #28 (bait test, closed), #29 (merged)
- 13 stale local branches cleaned up during session-complete
- Session close sequence established: `/session-complete` -> `/ce:compound` -> `/export`

## Session Exports

- `~/.claude/exports/ai-study-architect/2026-03-15-session10-phase2-followup-security-actions-monetization.txt` (mid-session)
- `~/.claude/exports/ai-study-architect/2026-03-15-session10-final-export.txt` (post-merge)
- `~/.claude/exports/ai-study-architect/2026-03-15-session10-absolute-final-export.txt` (post-staleness-audit)
- `~/.claude/exports/ai-study-architect/2026-03-15-session10-pre-final-compound-export.txt` (pre-session-complete)
