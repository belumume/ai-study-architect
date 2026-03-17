---
status: resolved
priority: p3
issue_id: "026"
tags: [quality, tooling]
---

## Problem Statement

`ruff check app/` reports pre-existing lint errors, mostly ARG001 (unused function argument) false positives from FastAPI rate limiter dependency injection pattern where `request` parameter is required by the decorator but not used in the function body.

## Proposed Solution

Add `# noqa: ARG001` to rate-limited endpoint functions where `request` is required by slowapi but unused. Alternatively, configure ruff to ignore ARG001 for specific patterns. Fix any genuine lint errors (non-ARG001).

## Files Affected

- backend/app/api/v1/*.py (multiple endpoint files)
- backend/pyproject.toml or ruff.toml (if configuring ignore pattern)

## Effort Estimate

Small
