---
status: resolved
priority: p2
issue_id: "036"
tags: [code-review, performance]
---

## Problem Statement

`bulk_delete_content` iterates R2 deletions sequentially. 50 items = 2.5-5s blocking.

## Proposed Solution

Use `ThreadPoolExecutor` for parallel R2 deletions.

## Files Affected

- `backend/app/api/v1/content.py:798-807`

## Effort Estimate

Small
