---
status: pending
priority: p2
issue_id: "010"
tags: [code-review, testing]
dependencies: []
---

# Write tests for confirm_delete cascade behavior

## Problem Statement

The `confirm_delete` parameter on DELETE /content/{id} is a significant behavioral change to a destructive endpoint but has no dedicated tests.

## Needed Tests

1. DELETE content with concepts -> returns 409 with impact counts
2. DELETE content with `?confirm_delete=true` -> cascades successfully
3. DELETE content with no concepts -> succeeds without confirmation
4. 409 response includes correct concept_count and mastery_records numbers

## Acceptance Criteria

- [ ] 4 test cases covering all confirm_delete paths
- [ ] Tests verify 409 response structure (message, concepts_count, mastery_records)
- [ ] Tests verify cascade actually deletes concepts + mastery records
