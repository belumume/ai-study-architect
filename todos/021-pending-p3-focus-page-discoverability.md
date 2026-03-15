---
status: pending
priority: p3
issue_id: "021"
tags: [ux, navigation, production]
dependencies: []
---

# Focus page not discoverable from empty-state dashboard

## Problem Statement

When a user has no subjects, the dashboard shows "Awaiting Telemetry" with "Start Study Session" (links to /study chat) and "Upload Materials" (links to /content). There is no link to /focus. The Focus page exists and works without subjects ("No subjects yet. You can start a general study session.") but is unreachable by clicking from the empty-state dashboard.

The "Initiate Focus" CTA only appears once subjects exist. The Focus page is also not in the nav bar (Dashboard, Study, Content).

## Proposed Solutions

1. Add Focus to nav bar (Dashboard, Study, Focus, Content)
2. Or change "Start Study Session" CTA to link to /focus instead of /study
3. Or add a third CTA button for Focus in the empty state

## Acceptance Criteria

- [ ] Focus page reachable by clicking from any dashboard state (empty or populated)
