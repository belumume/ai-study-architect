---
status: pending
priority: p1
issue_id: "024"
tags: [security, auth, deploy, production]
dependencies: []
---

# Persist RSA keys across deploys (users logged out on every deploy)

## Problem Statement

The Dockerfile generates RS256 keys at build time. Every deploy creates new keys, invalidating all existing JWTs and logging out all active users. The HS256 fallback (`JWT_SECRET_KEY`) survives deploys, but RS256 tokens issued between deploys become invalid.

## Impact

Every deploy = every user logged out. Unacceptable before real users.

## Proposed Solutions

1. **Store RSA keys in CF Worker secrets** — persist private/public key pair as env vars. Generated once, reused across deploys.
2. **Use only HS256** — simpler, JWT_SECRET_KEY already persists. But RS256 is more secure for production.
3. **External key store** — store keys in R2 or KV. More complex but separates key lifecycle from deploy lifecycle.

## Acceptance Criteria

- [ ] Users remain logged in after deploy
- [ ] RSA keys persist across container rebuilds
- [ ] Key rotation still possible (but not forced on every deploy)
