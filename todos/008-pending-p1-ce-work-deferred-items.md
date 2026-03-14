---
status: pending
priority: p1
issue_id: "008"
tags: [code-review, implementation, deferred]
dependencies: []
---

# Phase 2 /ce:work deferred items — must fix before merge

## Problem Statement

During Phase 2 `/ce:work`, several deliverables were skipped or partially implemented. These need attention before the PR is merge-ready.

## Code Gaps (broken as-is)

1. **`contentId=""` in SubjectDetailPage.tsx line 70** — ExtractionTrigger receives empty string. Extraction requires a content_id. The Subject Detail page needs to show content items linked to the subject and let users extract per-content-item, not per-subject.

2. **Content upload doesn't handle `subject_id`** — ContentUpdate schema has `subject_id` but the upload/update endpoint in `content.py` doesn't read or store it. Users can't associate content with subjects via API.

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

- [ ] ExtractionTrigger receives a real content_id (from content items linked to subject)
- [ ] Content upload/update endpoint handles subject_id
- [ ] All plan deliverable checkboxes checked or explicitly marked deferred
- [ ] Critical tests written (dashboard 0-concepts, extraction integration)
