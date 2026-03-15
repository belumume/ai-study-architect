---
status: complete
priority: p3
issue_id: "023"
tags: [ui-bug, dashboard, production]
dependencies: []
---

# Subject card progress bar appears full when 0 minutes logged

## Solution Implemented

Conditionally render the inner progress bar div only when `progress > 0`.
At 0%, a `width: "0%"` div with `rounded-full` can still produce a small visible artifact.
By not rendering the element at all, the track shows as empty.

File: `frontend/src/components/dashboard/SubjectList.tsx`

## Acceptance Criteria

- [x] Progress bar shows 0% width when 0 minutes logged (bar not rendered)
- [x] Progress bar scales linearly with minutes/goal ratio (unchanged logic)
