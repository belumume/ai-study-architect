---
status: pending
priority: p2
issue_id: "044"
tags: [documentation, code-review]
---

## Problem Statement
Brainstorm body (lines 264-287) says Figma is "integrated from Phase 0" and "Both From Start." The Resolved Questions section (line 459) notes "Figma deferred (plan review decision)" but the body was never updated. Also: Framer Motion is still listed in Technology Stack (line 58) despite being removed (YAGNI). A reader of the body would get wrong information.

## Proposed Solution
Add inline annotations to the brainstorm body noting Figma deferral and Framer Motion removal decisions. Don't rewrite — just add "[DEFERRED: plan review decision]" and "[REMOVED: YAGNI, CSS handles animations]" markers.

## Files Affected
- docs/brainstorms/2026-03-13-mvp-frontend-brainstorm.md

## Effort Estimate
Small
