---
status: complete
priority: p3
issue_id: "021"
tags: [ux, navigation, production]
dependencies: []
---

# Focus page not discoverable from empty-state dashboard

## Solution Implemented

Added Focus to the navigation bar: Dashboard, Study, **Focus**, Content.
Now accessible from any dashboard state (empty or populated).

File: `frontend/src/app/layout/TopNav.tsx` — added `{ path: '/focus', label: 'Focus' }` to NAV_LINKS.

## Acceptance Criteria

- [x] Focus page reachable by clicking from any dashboard state (empty or populated)
