---
status: pending
priority: p3
issue_id: "022"
tags: [api, production, content]
dependencies: []
---

# Content search returns 422 instead of empty results

## Problem Statement

`GET /api/v1/content/search?q=test` returns 422 (validation error) instead of an empty array. The search endpoint may have a different parameter name or require additional params.

## Acceptance Criteria

- [ ] Search with valid query returns 200 with results or empty array
- [ ] Search parameter documented in API reference
