---
status: pending
priority: p1
issue_id: "001"
tags: [code-review, plan-review, api, claude]
dependencies: []
---

# Validate Claude Structured Outputs works with raw httpx before building pipeline

## Problem Statement

The plan pivoted to using Claude's `output_config.format` (Structured Outputs, GA) for guaranteed JSON extraction. This eliminates all JSON parsing complexity. However, the existing codebase uses raw httpx for all Claude API calls — NOT the Anthropic SDK. Structured Outputs via raw httpx has not been tested in this codebase. If it doesn't work (wrong API version, missing header, etc.), the entire extraction service design fails.

## Findings

- Best practices researcher confirmed Structured Outputs is GA and works with raw httpx
- The `anthropic-version: 2023-06-01` header (current in `claude_service.py:62`) should support it
- BUT the existing `chat_completion()` method doesn't support `output_config` — the extraction service bypasses it
- Creating a second HTTP call pattern increases maintenance burden (Python reviewer flagged)
- No integration test exists for structured outputs in this project

## Proposed Solutions

### Option 1: Spike test before implementation

**Approach:** Write a quick test script that sends one structured output request to Claude via raw httpx with the project's existing headers. Verify response format.

**Effort:** 30 minutes
**Risk:** Low

### Option 2: Add `output_config` support to ClaudeService

**Approach:** Extend `chat_completion()` to accept an optional `output_config` parameter. The extraction service uses the existing method instead of bypassing it.

**Effort:** 2 hours
**Risk:** Low — additive change, doesn't break existing callers

## Technical Details

**Affected files:**
- `backend/app/services/claude_service.py` — may need `output_config` support
- `backend/app/services/concept_extraction.py` — new service, depends on this working

## Acceptance Criteria

- [ ] Structured output request succeeds with raw httpx + existing headers
- [ ] Response `content[0]["text"]` is valid JSON matching the schema
- [ ] `json.loads()` parses it without fallback needed
- [ ] Tested with both Sonnet and Haiku models

## Work Log

### 2026-03-14 - Plan Review

**By:** Claude Code (ce-review)
**Actions:** Identified as critical validation step. Structured Outputs is the foundation of the extraction service — if it fails, the fallback is significant rework.
