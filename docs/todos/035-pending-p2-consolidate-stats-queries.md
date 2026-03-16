---
status: resolved
priority: p2
issue_id: "035"
tags: [code-review, performance]
---

## Problem Statement

`get_content_stats` makes 5 separate DB queries. Each round-trip to Neon adds 50-150ms on cold start.

## Proposed Solution

Consolidate to 2-3 queries using conditional aggregation.

## Files Affected

- `backend/app/api/v1/content.py:459-500`

## Effort Estimate

Small
