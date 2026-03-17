---
status: resolved
priority: p2
issue_id: "041"
tags: [quality, testing, code-review]
resolved_date: "2026-03-16"
---

## Problem Statement
Plan 002 Phase 2b specified `backend/tests/test_concept_extraction_integration.py` — integration tests with real (small) content. File was never created. Extraction service has unit tests with mocked Claude but no integration tests verifying actual extraction output structure.

## Proposed Solution
Create integration test file with small sample content. Test: extraction produces valid SVO concepts, deduplication works, chunking handles edge cases, error handling for malformed content.

## Resolution
Created `backend/tests/test_concept_extraction_integration.py` with 19 integration tests across 5 test classes:
- **TestExtractionPipelineIntegration** (2 tests): Full end-to-end pipeline with 2 and 3 concepts, DB verification including mastery records
- **TestDeduplicationIntegration** (3 tests): Exact duplicate, normalization-based dedup (casing/articles), non-dedup of distinct concepts
- **TestChunkingEdgeCases** (4 tests): Empty content, whitespace-only, short content (single chunk), oversized text truncation
- **TestMalformedResponseHandling** (6 tests): Missing fields, invalid concept_type, invalid difficulty, empty name, all-invalid returns message, wrong-type estimated_minutes
- **TestAPIErrorHandling** (4 tests): 500 errors, no API key, malformed JSON, 429 rate-limit retry

Mock strategy: HTTP transport level (`httpx.MockTransport`) — only the Claude API HTTP call is mocked. All service logic (chunking, normalization, validation, deduplication, DB inserts) runs for real.

## Files Affected
- backend/tests/test_concept_extraction_integration.py (new)

## Effort Estimate
Small-Medium
