---
status: resolved
priority: p2
issue_id: "046"
tags: [code-review, performance, ux]
---

## Problem Statement

`plainto_tsquery` matches whole words only (stemmed). The previous LIKE-based search matched substrings. Users searching "algo" won't find "algorithm". Short/partial queries return no results where they previously did.

Identified by cubic (PR #53 review).

## Proposed Solution

Add LIKE fallback for short queries (2-3 chars) or use `to_tsquery` with `:*` prefix matching for typeahead behavior. Example: `to_tsquery('english', 'algo:*')` matches "algorithm". Keep tsvector + GIN for full-word queries (4+ chars).

## Files Affected

- `backend/app/api/v1/content.py` (search_content endpoint)

## Effort Estimate

Small
