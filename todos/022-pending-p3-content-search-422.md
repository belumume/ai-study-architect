---
status: complete
priority: p3
issue_id: "022"
tags: [api, production, content]
dependencies: []
---

# Content search returns 422 instead of empty results

## Root Cause

FastAPI route ordering: `/search` was defined after `/{content_id}`. The parameterized route matched first, trying to parse "search" as a UUID → 422 validation error.

## Solution Implemented

Moved `/search` endpoint declaration before `/{content_id}` in content.py. Explicit paths must come before parameterized paths in FastAPI.

## Acceptance Criteria

- [x] Search with valid query returns 200 with results or empty array
- [x] Search parameter is `q` (e.g., `GET /api/v1/content/search?q=test`)
