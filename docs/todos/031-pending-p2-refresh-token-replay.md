---
status: pending
priority: p2
issue_id: "031"
tags: [code-review, security]
---

## Problem Statement

`/auth/refresh` never invalidates old refresh tokens. Stolen token valid for 30 days. No token family tracking or blacklist.

## Proposed Solution

Implement refresh token rotation with family tracking in Redis (Upstash). Mark consumed tokens. If consumed token reused, invalidate entire family.

## Files Affected

- `backend/app/api/v1/auth.py:177-249`
- New Redis key pattern

## Effort Estimate

Medium
