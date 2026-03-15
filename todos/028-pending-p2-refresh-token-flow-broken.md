---
status: pending
priority: p2
issue_id: "028"
tags: [auth, frontend, ux, production]
dependencies: []
---

# Refresh token flow not working — users logged out after 30min

## Problem Statement

Access tokens expire after 30 minutes (JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30). Refresh tokens last 30 days (JWT_REFRESH_TOKEN_EXPIRE_DAYS=30). The frontend should silently refresh the access token before expiry, but it's not — users get redirected to login after 30 minutes of inactivity.

## Evidence

Playwright session logged in at ~20:42 UTC. Navigated at ~21:32 UTC (50 min later). Console showed:
- `/api/v1/auth/me` → 401 (access token expired — expected)
- `/api/v1/auth/refresh` → 401 (unexpected — refresh token should work for 30 days, check if token was stored/sent)

Redirected to login page.

## Investigation Needed

1. Is the refresh token being stored? (localStorage? httpOnly cookie?)
2. Is the frontend interceptor calling /auth/refresh on 401?
3. Is the refresh endpoint itself working? (test via curl)
4. Is the refresh token being sent correctly? (Bearer header? Cookie?)

## Files to investigate
- `frontend/src/services/api.ts` — Axios interceptors
- `frontend/src/services/auth.service.ts` — Token storage/refresh logic
- `frontend/src/contexts/AuthContext.tsx` — Auth state management
- `backend/app/api/v1/auth.py` — Refresh endpoint

## Acceptance Criteria

- [ ] Users stay logged in for 30 days (refresh token lifetime) without re-entering credentials
- [ ] Access token silently refreshed on 401 responses
