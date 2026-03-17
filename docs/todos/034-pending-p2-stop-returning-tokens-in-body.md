---
status: resolved
priority: p2
issue_id: "034"
tags: [code-review, security]
---

## Problem Statement

Login and refresh endpoints return raw JWT tokens in response body alongside httpOnly cookies. XSS can steal tokens from response even though cookies are httpOnly.

## Resolution

Both `/auth/login` and `/auth/refresh` now return only `{"token_type": "bearer"}` in the response body. New `TokenResponse` schema added. `AuthResponse` interface in frontend updated. All tests updated to assert tokens are NOT in response body.

## Files Changed

- `backend/app/api/v1/auth.py` — response bodies stripped of tokens
- `backend/app/schemas/user.py` — added `TokenResponse` schema
- `frontend/src/services/auth.service.ts` — simplified `AuthResponse` interface
- `frontend/src/test/mocks.ts`, `frontend/src/test/test-utils.tsx` — mock data updated
- `frontend/src/services/__tests__/api.test.ts` — refresh mock updated
- `backend/tests/test_auth.py` — assertions updated
- `backend/tests/conftest.py` — `authenticated_client` fixture reads token from cookie
- `backend/tests/test_concepts_api.py` — login token extraction from cookie
