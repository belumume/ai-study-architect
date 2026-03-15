---
status: pending
priority: p2
issue_id: "011"
tags: [code-review, performance]
dependencies: []
---

# Eliminate redundant Query 4 in dashboard — derive from per-subject results

## Problem Statement

Dashboard runs 5 queries. Query 4 (global mastery count) produces `total_concepts` and `mastered_concepts` which can be derived by summing the per-subject mastery results from the new query. This saves one database round-trip.

## Proposed Solution

Replace Query 4 with: `total_concepts = sum(c for c, _ in mastery_by_subject.values())` and `mastered_concepts = sum(m for _, m in mastery_by_subject.values())`. Only keep the separate query if orphaned concepts (no subject_id) are expected.

## Acceptance Criteria

- [ ] Dashboard uses 4 queries instead of 5
- [ ] `total_concepts` and `mastered_concepts` values unchanged
- [ ] Dashboard tests still pass
