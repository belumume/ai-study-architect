---
status: pending
priority: p2
issue_id: "033"
tags: [code-review, security]
---

## Problem Statement

`get_optional_current_user` only checks Bearer header, not cookies. Cookie-authenticated users silently appear unauthenticated on optional-auth endpoints.

## Proposed Solution

Add cookie fallback matching `get_current_user` pattern.

## Files Affected

- `backend/app/api/dependencies.py:119-146`

## Effort Estimate

Small
