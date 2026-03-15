---
status: pending
priority: p3
issue_id: "019"
tags: [code-review, pre-existing, dead-code]
dependencies: []
---

# Fix or remove dead openai_service import in vision_processor

## Problem Statement

`vision_processor.py` imports from `app.services.openai_service` which doesn't exist. Import fails silently (`HAS_OPENAI = False`), so OpenAI vision path is permanently dead. The fallback to Claude vision works, but the OpenAI code path is unreachable.

## Proposed Solution

Either remove the OpenAI vision code path entirely, or wire it to the actual `openai_fallback` service.

## Acceptance Criteria

- [ ] No dead import / unreachable code path
- [ ] Vision processing still works via Claude
