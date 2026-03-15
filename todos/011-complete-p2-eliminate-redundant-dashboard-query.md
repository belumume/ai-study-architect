---
status: complete
priority: p2
issue_id: "011"
tags: [code-review, performance]
dependencies: []
---

# Eliminate redundant Query 4 in dashboard — derive from per-subject results

## Solution Implemented

Replaced Query 4 (separate `UserConceptMastery` aggregation) with:
```python
total_concepts = sum(c for c, _ in mastery_by_subject.values())
mastered_concepts = sum(m for _, m in mastery_by_subject.values())
```

Dashboard now runs 3 queries instead of 4 (28-day aggregation, active session, streak).

## Acceptance Criteria

- [x] Dashboard uses fewer queries (4→3, was 5→4 counting subject query)
- [x] `total_concepts` and `mastered_concepts` values derived from per-subject results
- [x] Dashboard tests still pass
