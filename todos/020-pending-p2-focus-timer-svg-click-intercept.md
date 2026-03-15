---
status: pending
priority: p2
issue_id: "020"
tags: [ui-bug, focus-timer, production]
dependencies: []
---

# SVG timer ring intercepts pointer events on Focus page buttons

## Problem Statement

On the Focus timer page, the SVG circular progress ring (`absolute -left-10 -top-10`, 280x280px) overlaps the Pause/Resume and Stop buttons. Clicking them fails with "element intercepts pointer events." Keyboard shortcuts (Space, Escape) work as a fallback.

## Reproduction

1. Start a focus session on production
2. Try to click Pause or Stop buttons
3. Click is intercepted by the SVG overlay

## Proposed Solution

Add `pointer-events: none` to the SVG timer ring element, or adjust its z-index/positioning so it doesn't overlap the button area.

## Acceptance Criteria

- [ ] Pause/Stop buttons clickable on desktop
- [ ] Keyboard shortcuts still work
- [ ] Timer ring visual unchanged
