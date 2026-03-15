---
status: complete
priority: p2
issue_id: "015"
tags: [security, jwt, pre-existing]
dependencies: []
---

# Move JWT kid from payload to header (RFC 7515)

## Problem Statement

`app/core/security.py` puts `kid` (key ID) in the JWT claims body. Per RFC 7515, `kid` belongs in the JWT header.

## Solution Implemented

- `create_access_token` / `create_refresh_token`: Removed `kid` from `to_encode` payload, added `headers={"kid": kid}` to `jwt.encode()`.
- `_find_key_for_token`: Changed from `jwt.get_unverified_claims()` to `jwt.get_unverified_header()` for `kid` lookup. Falls back to claims for backward compatibility with pre-migration tokens.

## Acceptance Criteria

- [x] `kid` set via `headers={"kid": ...}` in `jwt.encode()`
- [x] Read via `jwt.get_unverified_header(token)["kid"]`
- [x] Key rotation still works with archived keys
- [x] Backward compatible — old tokens with kid in payload still verify
