---
status: complete
priority: p3
issue_id: "012"
tags: [code-review, simplicity, yagni]
dependencies: []
---

# Remove unused schemas from concept.py

## Solution Implemented

Removed 10 unused schemas and related code (~100 LOC):
- ConceptGraphNode, ConceptGraphEdge, ConceptGraph (graph visualization — Phase 5+)
- ConceptDetail (detailed concept with relationships — no endpoint uses it)
- ConceptDependencyBase (inlined into ConceptDependencyCreate)
- ConceptDependencyDetail (full dependency with concept info — unused)
- ConceptDependencyResponse (only used by removed schemas)
- ConceptListResponse, ConceptDependencyListResponse (pagination wrappers — unused)
- ConceptBulkCreate (not ConceptBulkCreateResponse — that one IS used)
- ConceptWithMastery (never imported)

Also removed: `MasteryResponse` import, forward reference resolution block.
Kept: ConceptBase, ConceptCreate, ConceptUpdate, ConceptResponse, ConceptDependencyCreate, ConceptBulkCreateResponse, ConceptExtractionRequest, ExternalResource.

## Acceptance Criteria

- [x] Unused schemas removed
- [x] All imports clean (verified)
- [x] No import errors anywhere in the codebase
