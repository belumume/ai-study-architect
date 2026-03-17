---
status: resolved
priority: p1
issue_id: "029"
tags: [code-review, performance]
---

## Problem Statement

Content search uses LIKE on `extracted_text` column. No GIN index. O(n * text_size) per query. At 100 docs: 1-3s. At 1000 docs: 10-30s. Catastrophic for 1 GiB container.

## Proposed Solution

Replace with PostgreSQL full-text search (`to_tsvector`/`to_tsquery` + GIN index). Eliminates LIKE and `case()` relevance ordering. Add generated tsvector column + migration.

## Files Affected

- `backend/app/api/v1/content.py:528-552`
- New Alembic migration

## Effort Estimate

Medium
