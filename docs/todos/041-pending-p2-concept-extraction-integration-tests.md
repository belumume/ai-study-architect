---
status: pending
priority: p2
issue_id: "041"
tags: [quality, testing, code-review]
---

## Problem Statement
Plan 002 Phase 2b specified `backend/tests/test_concept_extraction_integration.py` — integration tests with real (small) content. File was never created. Extraction service has unit tests with mocked Claude but no integration tests verifying actual extraction output structure.

## Proposed Solution
Create integration test file with small sample content. Test: extraction produces valid SVO concepts, deduplication works, chunking handles edge cases, error handling for malformed content.

## Files Affected
- backend/tests/test_concept_extraction_integration.py (new)

## Effort Estimate
Small-Medium
