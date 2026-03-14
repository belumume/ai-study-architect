---
status: pending
priority: p2
issue_id: "004"
tags: [code-review, plan-review, ux, frontend]
dependencies: []
---

# Design mastery empty state — all concepts show 0% until Phase 4

## Problem Statement

Phase 2 extracts concepts and creates `UserConceptMastery` records with `status=not_started` and `mastery_level=0.0`. Phase 4 (practice generation) is when mastery data actually gets populated. This means for the entire Phase 2-3 period, every concept shows 0% mastery and the dashboard mastery index is 0%.

The Subject Detail page will display a wall of 0% progress bars. The dashboard "Mastery Index" will show 0%. The "Due for Review" count will be 0. This makes the feature feel broken or pointless to users.

## Findings

- SpecFlow Gaps 19-20: "Mastery % is 0% until Phase 4" and "due for review requires SM-2 (Phase 5)"
- Architecture reviewer: "mastery index should be count-based % — but even that is 0% when no concepts are mastered"
- The plan's acceptance criterion says "Dashboard shows aggregate mastery index and due-for-review count" — technically true but all zeros

## Proposed Solutions

### Option 1: "Practice coming soon" indicator

**Approach:** When mastery_level = 0.0 and total_attempts = 0, show "Not yet practiced" instead of "0%". Dashboard mastery card shows "Concepts extracted: 24 | Practice coming in a future update" instead of "Mastery: 0%".

**Effort:** 2 hours (frontend only)
**Risk:** Low

### Option 2: Use extraction_confidence as stand-in

**Approach:** Display the AI's extraction confidence per concept instead of mastery. "AI Confidence: 85%" tells users something useful about the concept quality without implying they've been tested.

**Effort:** 2 hours (frontend only)
**Risk:** Low — but may confuse users about what the number means

## Acceptance Criteria

- [ ] Subject Detail page does not show a wall of "0%" that feels broken
- [ ] Dashboard mastery section is informative even without practice data
- [ ] Users understand that practice features are coming
- [ ] The empty state clearly distinguishes "not yet practiced" from "mastered 0%"
