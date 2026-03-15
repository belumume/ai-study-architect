---
status: pending
priority: p2
issue_id: "015"
tags: [security, jwt, pre-existing]
dependencies: []
---

# Move JWT kid from payload to header (RFC 7515)

## Problem Statement

`app/core/security.py` puts `kid` (key ID) in the JWT claims body (line 127). Per RFC 7515, `kid` belongs in the JWT header. Current code reads it via `jwt.get_unverified_claims()` — should use `jwt.get_unverified_header()`.

## Acceptance Criteria

- [ ] `kid` set via `headers={"kid": ...}` in `jwt.encode()`
- [ ] Read via `jwt.get_unverified_header(token)["kid"]`
- [ ] Key rotation still works with archived keys
