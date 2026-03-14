---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, plan-review, backend, edge-case]
dependencies: []
---

# Handle zero-concept extraction gracefully

## Problem Statement

The plan covers happy path (5-200 concepts extracted) and partial failure (some chunks fail). But there is no defined behavior for when Claude extracts ZERO concepts from valid content. This can happen with:
- Very short content (< 100 words)
- Non-academic content (emails, admin notes uploaded by mistake)
- Image-heavy content where text extraction produced little
- Claude safety refusal (with structured outputs, returns empty arrays)

Without explicit handling, `extraction_status` would be set to "completed" with 0 concepts and 0 mastery records. The Subject Detail page would show an empty concept list with no explanation.

## Findings

- SpecFlow Gap 9: "First-time user / empty state" mentions 0 concepts but only for new users
- No acceptance criterion covers the "extracted 0 concepts" case
- The `ConceptBulkCreateResponse` shows `created_concepts: 0` but frontend toast says "Concepts extracted successfully" — misleading
- Content.extraction_status would be "completed" even with 0 concepts — no way to distinguish "completed with results" from "completed empty"

## Proposed Solutions

### Option 1: Distinct status + user-visible message

**Approach:** If extraction produces 0 concepts, set `extraction_status = 'completed_empty'`. Frontend shows: "No concepts found in this content. Try uploading more detailed study materials, or create concepts manually."

**Effort:** 1 hour
**Risk:** Low

### Option 2: Minimum concept threshold

**Approach:** If < 3 concepts extracted, treat as low-quality extraction. Set status to `partial` and suggest re-extraction with different content.

**Effort:** 1 hour
**Risk:** Low

## Acceptance Criteria

- [ ] Extraction of empty/trivial content does not crash
- [ ] User sees a helpful message explaining why 0 concepts were found
- [ ] Status distinguishes "completed with concepts" from "completed empty"
- [ ] Frontend empty state for Subject Detail works with 0 concepts
