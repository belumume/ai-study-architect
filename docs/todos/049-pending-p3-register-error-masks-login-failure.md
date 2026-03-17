---
status: resolved
priority: p3
issue_id: "049"
tags: [code-review, ux]
---

## Problem Statement

`AuthContext.register()` calls `register()` then `login()` in sequence. The catch block shows "Registration failed" for both cases. If registration succeeds but auto-login fails, the user sees a misleading error message.

Identified by cubic (PR #54 review, P2).

## Proposed Solution

Separate the try/catch blocks so registration errors and login errors show appropriate messages. Or wrap login() in its own try/catch that sets a different error message like "Account created but login failed. Please log in manually."

## Files Affected

- `frontend/src/contexts/AuthContext.tsx` (register function)

## Effort Estimate

Small (Phase 3 auth restyle scope)
