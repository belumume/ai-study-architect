---
status: pending
priority: p3
issue_id: "012"
tags: [code-review, simplicity, yagni]
dependencies: []
---

# Remove 9 unused schemas from concept.py (~90 LOC)

## Problem Statement

ConceptGraphNode, ConceptGraphEdge, ConceptGraph, ConceptDetail, ConceptDependencyDetail, ConceptDependencyListResponse, ConceptListResponse, ConceptBulkCreate, ExternalResource — all defined but never imported or used outside concept.py itself. Pre-built for future phases that don't exist.

## Acceptance Criteria

- [ ] All 9 unused schemas removed
- [ ] All tests pass
- [ ] No import errors anywhere in the codebase
