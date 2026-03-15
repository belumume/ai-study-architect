---
title: "Phase 2 Follow-up: Todo Resolution, Structured Outputs Validation, and CE Review Hardening"
category: integration-issues
date: 2026-03-14
session: 10
tags:
  - phase-2
  - concept-extraction
  - structured-outputs
  - todo-resolution
  - ce-review
  - security-fix
  - performance
  - model-selection
  - monetization
severity: medium
components_affected:
  - backend/app/services/concept_extraction.py
  - backend/app/services/claude_service.py
  - backend/app/api/v1/concepts.py
  - backend/app/api/v1/content.py
  - backend/app/api/v1/dashboard.py
  - backend/app/models/content.py
  - backend/app/schemas/concept.py
  - frontend/src/components/dashboard/HeroMetrics.tsx
  - frontend/src/components/dashboard/SubjectList.tsx
  - frontend/src/components/subject-detail/ExtractionTrigger.tsx
  - frontend/src/components/subject-detail/SubjectMasteryOverview.tsx
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/pages/SubjectDetailPage.tsx
  - frontend/src/types/concept.ts
related_docs:
  - docs/plans/2026-03-14-002-feat-concept-extraction-pipeline-plan.md
  - docs/solutions/integration-issues/phase2-concept-extraction-session9-compound.md
  - docs/brainstorms/2026-03-14-monetization-strategy-brainstorm.md
  - docs/analysis/PRICING_DECISION_CARD.md
  - docs/analysis/AI_EDUCATION_COST_MODELING_2026.md
---

# Phase 2 Follow-up: Session 10 Compound Doc

## Context

Session 9 shipped Phase 2 concept extraction (PR #26) but left 8 todos from the CE plan review. Session 10 completed those todos, then ran `/ce:review` which found security and performance issues requiring immediate fixes. A monetization strategy brainstorm was also conducted.

## Problem 1: Structured Outputs Untested Against Live API

### Problem
The extraction service used `output_config.format` with JSON schema for guaranteed valid JSON, but this was implemented from documentation without real API validation.

### Root Cause
Structured outputs were implemented during `/ce:work` based on plan deepening research. The spike test was deferred as todo 001.

### Solution
Spike test confirmed both Sonnet 4.6 and Haiku 4.5 return guaranteed-valid JSON via raw httpx with `anthropic-version: 2023-06-01`. No beta header needed. Response at `content[0]["text"]` is valid JSON matching the provided schema. `json.loads()` parses cleanly with zero fallback needed.

### Code Changes
- `backend/app/services/claude_service.py` -- Added `output_config` and `model` params to `chat_completion()` for future callers
- `backend/tests/spike_structured_outputs.py` -- Standalone validation script

## Problem 2: Empty Extraction Shows Misleading Success

### Problem
When Claude extracts 0 concepts from valid content, status showed "completed" and toast said "Extracted 0 concepts successfully" -- misleading.

### Root Cause
Extraction status only had `completed` and `failed`. A successful extraction finding nothing was indistinguishable from one finding 20 concepts.

### Solution
Three-tier status: `completed` (concepts found), `completed_empty` (ran successfully, nothing found), `failed` (API error). Added `message` field to response. Frontend shows warning toast for 0 concepts.

### Code Changes
- `backend/app/services/concept_extraction.py` -- Early return with message when 0 concepts
- `backend/app/api/v1/concepts.py` -- Sets `completed_empty` status
- `backend/app/models/content.py` -- Status comment updated
- `backend/app/schemas/concept.py` -- Added `message: str | None` to `ConceptBulkCreateResponse`
- `frontend/src/components/subject-detail/ExtractionTrigger.tsx` -- Warning toast for 0 concepts
- `frontend/src/pages/SubjectDetailPage.tsx` -- "No concepts found" status text

## Problem 3: Content Deletion Silently Cascades

### Problem
`DELETE /content/{id}` silently cascaded to delete all concepts and mastery records. No warning.

### Root Cause
Database CASCADE on `Concept.content_id` propagated deletions through the entire chain.

### Solution
Added `confirm_delete` query parameter. Without it, returns HTTP 409 with `{concepts_count, mastery_records, message}`. With `?confirm_delete=true`, proceeds with deletion.

### Code Changes
- `backend/app/api/v1/content.py` -- `confirm_delete: bool = False` param, 409 response with impact counts

## Problem 4: Security -- User-Scoping Gaps (Found by CE Review)

### Problem
Two latent cross-user data leakage vulnerabilities found by security-sentinel review agent:
1. Dashboard concept count query didn't filter by `Content.user_id`
2. Delete cascade mastery count didn't filter by `UserConceptMastery.user_id`

### Root Cause
Queries assumed implicit user scoping through ownership chains but didn't enforce it in SQL.

### Solution
Added explicit user-scoping filters:
1. Dashboard: `.join(Content).filter(Content.user_id == current_user.id)`
2. Delete: `.filter(UserConceptMastery.user_id == current_user.id)`

### Code Changes
- `backend/app/api/v1/dashboard.py` -- Added Content join + user_id filter
- `backend/app/api/v1/content.py` -- Added user_id filter to mastery count

## Problem 5: Model Selection -- Haiku vs Sonnet

### Problem
Sonnet used for all extraction. Haiku untested.

### Root Cause
Default "safe choice" during implementation. No quality comparison done.

### Solution
Head-to-head comparison on academic content (hash tables chapter):
- Sonnet: 15 concepts, 21 deps, 51s, $0.057/extraction
- Haiku: 13 concepts, 18 deps, 20s, $0.016/extraction (3.6x cheaper, 2.6x faster)
- Same 0.92 confidence. Haiku names slightly more generic but functionally equivalent.
- Default changed to `claude-haiku-4-5`. Override via `CLAUDE_EXTRACTION_MODEL` env var.

### Code Changes
- `backend/app/services/concept_extraction.py` -- Default model changed to `claude-haiku-4-5`

## Problem 6: Silent Failures in Dashboard (Found by CE Review)

### Problem
4 bare `except Exception: pass` blocks in dashboard silently swallowed query errors.

### Solution
Added `logger.warning("...", exc_info=True)` to all 4 blocks. Fallback values unchanged.

### Code Changes
- `backend/app/api/v1/dashboard.py` -- 4 logging additions

## Additional Work

### Per-Subject Mastery in Dashboard
Added `concept_count` and `mastery_percentage` fields to `SubjectWithProgress` schema. New outerjoin query groups concepts by subject_id with mastery status counts. Frontend SubjectList shows concept count per subject card.

### Mastery Empty State
SubjectMasteryOverview shows "Practice features coming soon" when all concepts are not_started. HeroMetrics shows concept count sublabel instead of misleading "0% ACROSS SUBJECTS".

### Dashboard Tests
4 new tests: empty state, subjects with 0 concepts, heatmap invariant (28 days), auth required.

### Lint Cleanup
915 auto-fixes via ruff (857 safe + 58 whitespace). 145 remaining are framework-required patterns (ARG001/ARG002).

### Test User Cleanup
Deleted `uitest2026` from production Neon via browser SQL Editor. Manually cascaded through all FK-dependent tables.

### Monetization Strategy Brainstorm
Researched 12+ education SaaS products. Documented decisions:
- Internal model routing by task (Haiku for extraction/grading, Sonnet for tutoring)
- Usage-gated freemium at $9.99/mo. Same AI quality across tiers.
- No model picker UI. Product decides, user learns.
- Phase 6 implementation. Strategy doc at `docs/brainstorms/2026-03-14-monetization-strategy-brainstorm.md`.

## Prevention Strategies

### 1. Multi-Tenant Query Scoping
Every query touching user-owned data must filter by `user_id` explicitly -- not rely on implicit ownership chains. Anti-pattern: `func.count()` in a join without re-applying the user filter. Every endpoint returning user-specific data needs a two-user test verifying data isolation.

### 2. Documentation-Reality Gap
Never document implementation details from plans. Only document what exists in code. When writing MEMORY.md entries about features, grep for the actual code pattern first. "Redis cache 60s TTL" was documented from the plan, not the implementation -- and never existed.

### 3. CE Pipeline Continuity
When session todos originate from a prior CE plan, they are part of an ongoing pipeline -- not isolated fixes. First action: read the plan, read the session export, read the todos, assess what remains. Feedback memory created: `feedback_follow_ce_pipeline.md`.

### 4. No Bare Except-Pass
Every exception handler must log. `except: pass` is banned. Acceptable pattern: `except Exception: logger.warning("...", exc_info=True); result = default`. Silent failures mask security bugs.

### 5. Single-User Testing Is Insufficient
The scoping bugs, silent failures, and documentation gaps were all invisible in single-user testing. Standing rule: any endpoint returning user-specific data must have at least one two-user isolation test.

## Review Findings (Todos Created)

| Todo | Priority | Description |
|------|----------|-------------|
| 009 | P2 | Dashboard Redis caching (documented but never implemented) |
| 010 | P2 | confirm_delete cascade tests |
| 011 | P2 | Eliminate redundant Query 4 in dashboard |
| 012 | P3 | Remove 9 unused schemas (~90 LOC YAGNI) |

## Test Results

- Backend: 420 passed, 53.9% coverage (up from 53.48%)
- Frontend: 86 passed, TypeScript clean
- Production: test user deleted, verified COUNT=0
