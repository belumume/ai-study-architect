---
status: complete
priority: p2
issue_id: "003"
tags: [code-review, plan-review, ux, data-integrity]
dependencies: []
---

# Warn users before content deletion cascades to concepts + mastery

## Problem Statement

The existing `DELETE /api/v1/content/{id}` endpoint deletes content and its R2 file. With Phase 2, `Concept.content_id` has `ondelete="CASCADE"`, which CASCADE-deletes all concepts extracted from that content. Those concept deletions CASCADE to `user_concept_mastery` records.

Currently this happens silently. A user who deletes a content item loses all associated concepts and mastery progress without warning. In Phase 4+ when mastery data represents weeks of practice, this is significant data loss.

## Findings

- SpecFlow Gap 27: "Content deletion does not address concepts"
- Security reviewer: "Silent data loss"
- Data integrity reviewer: "Re-extraction destroys mastery data — needs warning gate"
- The existing `delete_content` endpoint has no concept-awareness

## Proposed Solutions

### Option 1: API returns cascade impact before deletion

**Approach:** `DELETE /content/{id}` first checks for associated concepts. If found, returns 409 with `{"concepts_count": 15, "mastery_records": 15, "message": "Deleting this content will also delete 15 concepts and mastery progress. Include confirm_delete=true to proceed."}`. Frontend shows a confirmation dialog.

**Effort:** 2 hours
**Risk:** Low

### Option 2: Soft-delete content, orphan concepts

**Approach:** Content uses soft-delete (`is_active = False`). Concepts keep their `content_id` reference to the inactive content. They remain visible and their mastery data is preserved.

**Effort:** 3 hours (more changes to content endpoints)
**Risk:** Medium — orphaned data management complexity

## Acceptance Criteria

- [x] User cannot accidentally delete content with extracted concepts without confirmation
- [ ] Frontend shows count of concepts + mastery records that will be deleted (content page uses MUI — Phase 3)
- [x] API requires explicit confirmation parameter for destructive delete
