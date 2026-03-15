---
status: complete
priority: p2
issue_id: "010"
tags: [code-review, testing]
dependencies: []
---

# Write tests for confirm_delete cascade behavior

## Solution Implemented

Created `tests/test_content_delete.py` with 4 test cases:
1. `test_delete_with_concepts_returns_409` — verifies 409 with impact counts
2. `test_delete_with_confirm_cascades` — verifies cascade deletes concepts + mastery
3. `test_delete_without_concepts_succeeds` — verifies simple delete without confirmation
4. `test_409_response_structure` — verifies response has message, concepts_count, mastery_records

## Acceptance Criteria

- [x] 4 test cases covering all confirm_delete paths
- [x] Tests verify 409 response structure (message, concepts_count, mastery_records)
- [x] Tests verify cascade actually deletes concepts + mastery records
