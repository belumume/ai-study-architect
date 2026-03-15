---
status: complete
priority: p3
issue_id: "019"
tags: [code-review, pre-existing, dead-code]
dependencies: []
---

# Fix or remove dead openai_service import in vision_processor

## Solution Implemented

Removed the entire dead OpenAI vision code path:
- Removed `try/except ImportError` block for `openai_service` import
- Removed `extract_with_openai()` method (was permanently unreachable)
- Removed `HAS_OPENAI` flag and OpenAI fallback logic from `extract_from_image()`
- Cleaned `extract_from_image_sync()` to remove `use_fallback` parameter
- Vision processing now exclusively uses Claude (the only working path)

## Acceptance Criteria

- [x] No dead import / unreachable code path
- [x] Vision processing still works via Claude
