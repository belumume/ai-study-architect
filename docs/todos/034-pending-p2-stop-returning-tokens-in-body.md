---
status: pending
priority: p2
issue_id: "034"
tags: [code-review, security]
---

## Problem Statement

Login and refresh endpoints return raw JWT tokens in response body alongside httpOnly cookies. XSS can steal tokens from response even though cookies are httpOnly.

## Proposed Solution

Return only `token_type` in response body. Frontend already ignores response body tokens.

## Files Affected

- `backend/app/api/v1/auth.py:172-174`
- `backend/app/api/v1/auth.py:245-249`

## Effort Estimate

Small
