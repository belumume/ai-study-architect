---
status: complete
priority: p2
issue_id: "005"
tags: [code-review, plan-review, api, performance]
dependencies: []
---

# Create consolidated GET /subjects/{id}/detail endpoint

## Problem Statement

The original plan proposed 3 separate queries for the Subject Detail page (subject, concepts, mastery). TypeScript reviewer identified this creates waterfall rendering, stale-cache inconsistency, and 3 loading states. The deepened plan updated the frontend to use a single query but the backend endpoint `GET /api/v1/subjects/{id}/detail` is not fully specified.

## Findings

- TypeScript reviewer: "Three separate queries is the wrong pattern. Follow DashboardPage's single-query pattern."
- Performance reviewer: "Use explicit outerjoin for concepts + mastery — single query, N+1 free"
- DB optimizer: `Concept JOIN UserConceptMastery` with user filter in ON clause is the correct pattern
- The plan's Phase 2c endpoint list includes `GET /subjects/{id}/concepts` and `GET /subjects/{id}/mastery` but not `GET /subjects/{id}/detail`
- Phase 2d deliverables now list the consolidated endpoint but Phase 2c does not

## Proposed Solutions

### Option 1: Single consolidated endpoint (recommended)

**Approach:** `GET /api/v1/subjects/{id}/detail` returns `{ subject, concepts: ConceptWithMastery[], mastery_summary }` in one response. Backend uses outerjoin query. One TanStack query, one loading state.

**Effort:** 2 hours
**Risk:** Low

## Acceptance Criteria

- [ ] `GET /subjects/{id}/detail` returns all data needed for Subject Detail page
- [ ] Single outerjoin query (no N+1)
- [ ] Frontend uses single `useQuery` call
- [ ] Cache invalidation is one key (`subject-detail`)
