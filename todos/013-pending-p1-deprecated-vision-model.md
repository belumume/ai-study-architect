---
status: pending
priority: p1
issue_id: "013"
tags: [code-review, security, deprecated]
dependencies: []
---

# Update deprecated gpt-4-vision-preview model

## Problem Statement

`backend/app/services/vision_processor.py` uses `gpt-4-vision-preview` which was deprecated by OpenAI in December 2024. API calls using this model will fail.

## Proposed Solution

Replace with `gpt-4o` or `gpt-4o-mini` (both support vision). Verify via OpenAI docs for current model ID before implementing.

## Acceptance Criteria

- [ ] Vision processor uses a current, non-deprecated model
- [ ] Model ID verified from official OpenAI docs (not cached)
