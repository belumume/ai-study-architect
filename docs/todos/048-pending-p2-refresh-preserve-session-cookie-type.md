---
status: resolved
priority: p2
issue_id: "048"
tags: [code-review, security]
resolved_in: fix/resolve-todos-026-046-049-cache-lint
---

## Problem Statement

The refresh endpoint always sets persistent cookies (`max_age` = token expiry). If user logged in without `remember_me` (session cookies), the refresh should issue session cookies too. Currently a session-only login becomes persistent after the first refresh.

Identified by CodeRabbit (PR #49/52 review).

## Proposed Solution

Embed `remember_me` flag in the refresh token JWT claims (or read from a Redis session store). On refresh, check the flag and only set `max_age` when `remember_me` is True. Otherwise omit `max_age` for session cookies.

## Files Affected

- `backend/app/api/v1/auth.py` (login: add claim, refresh: conditional max_age)
- `backend/app/core/security.py` (create_refresh_token: accept remember_me param)

## Effort Estimate

Small
