---
status: pending
priority: p3
issue_id: "025"
tags: [testing, quality]
---

## Problem Statement

Concurrency and storage integration tests were planned but never created. The system has concurrent session constraints (partial unique index), concurrent extraction requests, and R2 storage operations that lack integration-level test coverage.

## Proposed Solution

Create integration tests covering: concurrent session start (should reject second), concurrent extraction requests for same subject, R2 upload/download/delete operations with error injection.

## Files Affected

- backend/tests/test_concurrency_integration.py (new)
- backend/tests/test_storage_integration.py (new)

## Effort Estimate

Medium
