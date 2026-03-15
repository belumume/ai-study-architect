---
status: pending
priority: p3
issue_id: "023"
tags: [ui-bug, dashboard, production]
dependencies: []
---

# Subject card progress bar appears full when 0 minutes logged

## Problem Statement

On the dashboard, the "Data Structures 0.0/5.0h" subject card shows what appears to be a full-width cyan progress bar even though 0 minutes have been logged against the 5-hour weekly goal. The bar should show 0% width.

## Reproduction

1. Create a subject with default weekly goal (300 min / 5h)
2. Don't log any time against it
3. Observe progress bar — appears to render at full width or has a minimum visual width

## Acceptance Criteria

- [ ] Progress bar shows 0% width when 0 minutes logged
- [ ] Progress bar scales linearly with minutes/goal ratio
