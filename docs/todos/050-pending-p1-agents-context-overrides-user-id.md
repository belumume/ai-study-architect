---
status: pending
priority: p1
issue_id: "050"
tags: [security, code-review]
---

## Problem Statement

In `backend/app/api/v1/agents.py:67`, `**request.context` is unpacked after `user_id` is set from the authenticated user. This allows clients to override `user_id` by including it in the context dict, potentially impersonating other users in agent state operations.

Identified by cubic (PR #56 review).

## Proposed Solution

Unpack `request.context` BEFORE setting `user_id`, or explicitly delete/overwrite `user_id` after unpacking:
```python
input_data = {
    **request.context,
    "user_input": request.message,
    "user_id": str(current_user.id),  # Must come AFTER context unpack
    "action": request.action or "general",
}
```

## Files Affected

- `backend/app/api/v1/agents.py` (line ~67)

## Effort Estimate

Small (but security-critical)
