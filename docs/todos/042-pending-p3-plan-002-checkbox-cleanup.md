---
status: pending
priority: p3
issue_id: "042"
tags: [documentation, code-review]
---

## Problem Statement
Plan 002 has unchecked deliverable checkboxes for items that were implemented under different names (SubjectConceptList.tsx -> ConceptCard.tsx, ContentExtractionStatus.tsx -> ExtractionTrigger.tsx) and items where work was done but checkbox wasn't updated (dashboard.py mastery fields). Also: Phase 2e checkboxes for SubjectList mastery % and zero-concept dashboard test need verification.

## Proposed Solution
Read plan 002 deliverable checklists. Cross-reference against actual files in frontend/src/components/subject-detail/ and backend/app/api/v1/dashboard.py. Check or annotate each item.

## Files Affected
- docs/plans/2026-03-14-002-feat-concept-extraction-pipeline-plan.md

## Effort Estimate
Small
