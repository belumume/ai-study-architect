---
status: complete
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

## Solution Implemented

**Option 1: Store RSA keys in CF Worker secrets** (base64-encoded PEM as env vars).

Changes:
- `backend/app/core/rsa_keys.py`: Added `_load_keys_from_env()` — decodes base64 PEM from `RSA_PRIVATE_KEY`/`RSA_PUBLIC_KEY` env vars. Priority chain: env vars > file-based > generate new.
- `backend/app/core/config.py`: Added `RSA_PRIVATE_KEY` and `RSA_PUBLIC_KEY` optional settings.
- `worker/src/index.ts`: Added `RSA_PRIVATE_KEY` and `RSA_PUBLIC_KEY` to container `envVars` mapping.
- `backend/Dockerfile`: Removed `RUN python scripts/generate_rsa_keys.py` (no build-time key generation).
- `backend/scripts/export_rsa_keys_b64.py`: New helper to generate base64-encoded keys for `wrangler secret put`.
- 4 new tests in `test_security.py::TestRSAKeyEnvLoading`.

## Deploy Steps

1. Generate keys: `cd backend && python scripts/export_rsa_keys_b64.py`
2. Store in CF: `echo "<value>" | npx wrangler secret put RSA_PRIVATE_KEY` (same for RSA_PUBLIC_KEY)
3. Redeploy worker: `cd worker && npx wrangler deploy`

## Acceptance Criteria

- [x] Users remain logged in after deploy (keys loaded from env vars, not regenerated)
- [x] RSA keys persist across container rebuilds (stored in CF Worker secrets)
- [x] Key rotation still possible (rotate_keys() still works, just regenerates in-memory)
