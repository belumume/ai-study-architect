---
status: pending
priority: p2
issue_id: "037"
tags: [code-review, performance]
---

## Problem Statement

Every `GET /{content_id}` triggers UPDATE + COMMIT for `view_count`. Doubles DB work on most common access pattern.

## Proposed Solution

Buffer in Redis INCR, flush periodically. Or remove synchronous tracking.

## Files Affected

- `backend/app/api/v1/content.py:583-593`

## Effort Estimate

Small
