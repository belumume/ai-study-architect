---
status: complete
priority: p2
issue_id: "008"
tags: [code-review, implementation, deferred]
dependencies: []
---

# Phase 2 /ce:work deferred items — must fix before merge

## Problem Statement

During Phase 2 `/ce:work`, several deliverables were skipped or partially implemented. These need attention before the PR is merge-ready.

## Code Gaps (FIXED)

1. ~~`contentId=""` in SubjectDetailPage~~ — FIXED in 7ef197a. Content items now shown with per-item extraction.
2. ~~Content upload subject_id~~ — Already works via generic `setattr` in update endpoint. Schema has `subject_id`.
3. ~~`<a href>` in SubjectList~~ — FIXED in 4e8ba98. Uses `<Link to>` now.
4. ~~`Content.key_concepts` not updated~~ — FIXED in 4e8ba98. Queries concept names after extraction.

## Remaining Gaps

## Missing Components

3. **`SubjectConceptList.tsx`** — Plan deliverable. Concepts are rendered inline in SubjectDetailPage instead of a separate filterable list component. Acceptable for v1 but the plan's filter UI isn't implemented.

4. **`ContentExtractionStatus.tsx`** — Plan deliverable. Shows extraction status per content item. Not created. The Subject Detail page has no content-item section.

5. **`ConceptNotFoundError`** — Plan says add to `exceptions.py`. Not needed until CRUD endpoints exist (deferred). Low priority.

## Missing Tests

6. **`test_concept_extraction_integration.py`** — Integration tests with real (small) content. Plan deliverable, not created.

7. **Dashboard 0-concepts test** — Plan quality gate: "dashboard still works with 0 concepts."

8. **Frontend Subject Detail tests** — Plan quality gates: "renders with 0 concepts" and "renders with 50+ concepts."

## Functional Gaps

9. **Subject mastery % in SubjectList cards** — Plan Phase 2e deliverable. Only the link was added, not mastery data display.

10. **Plan checkboxes not checked off** — `/ce:work` skill requires updating plan checkboxes as tasks complete. Not done.

## Acceptance Criteria

- [x] ExtractionTrigger receives a real content_id (from content items linked to subject)
- [x] Content upload/update endpoint handles subject_id
- [x] All plan deliverable checkboxes checked or explicitly marked deferred
- [x] Critical tests written (dashboard 0-concepts, extraction integration)
- [x] Subject mastery % in SubjectList cards (concept_count + mastery_percentage from dashboard API)
- [x] Zero-concept extraction test (message field validation)

## Remaining Deferred (low priority, v2)
- SubjectConceptList filter component (concepts rendered inline, acceptable for v1)
- ContentExtractionStatus component (status shown in SubjectDetailPage content list)
- ConceptNotFoundError (not needed until CRUD endpoints exist)
