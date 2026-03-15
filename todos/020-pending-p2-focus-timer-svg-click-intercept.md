---
status: complete
priority: p2
issue_id: "020"
tags: [ui-bug, focus-timer, production]
dependencies: []
---

# SVG timer ring intercepts pointer events on Focus page buttons

## Solution Implemented

Added `pointer-events-none` to the SVG velocity ring element in `FocusPage.tsx`. Clicks now pass through the decorative ring to the Pause/Resume/Stop buttons underneath.

## Acceptance Criteria

- [x] Pause/Stop buttons clickable on desktop
- [x] Keyboard shortcuts still work (unchanged — they're window-level)
- [x] Timer ring visual unchanged (pointer-events-none is invisible to rendering)
