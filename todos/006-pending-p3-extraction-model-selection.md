---
status: pending
priority: p3
issue_id: "006"
tags: [code-review, plan-review, cost, configuration]
dependencies: []
---

# Make extraction model configurable — consider Haiku for cost savings

## Problem Statement

The extraction service defaults to `claude-sonnet-4-6` (same as chat). Sonnet is ~10x more expensive than Haiku for input tokens. For structured extraction (which produces well-constrained JSON), Haiku may be sufficient and would reduce extraction cost from ~$0.10 to ~$0.01 per 10-page document.

## Findings

- SpecFlow Gap 30: "Model selection — consider Haiku for extraction (10x cheaper)"
- Best practices researcher: "Haiku 4.5 supports structured outputs"
- The plan already uses `os.getenv("CLAUDE_EXTRACTION_MODEL", os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"))` — good
- Need empirical testing: does Haiku produce comparable SVO concept quality?

## Proposed Solutions

### Option 1: Default to Sonnet, test Haiku empirically

**Approach:** Ship with Sonnet default. Run extraction on 5 sample documents with both models. Compare concept quality manually. If Haiku is adequate, switch the default.

**Effort:** 1 hour to configure, 2 hours to evaluate
**Risk:** Low

## Acceptance Criteria

- [ ] `CLAUDE_EXTRACTION_MODEL` env var is configurable
- [ ] Extraction works with both Sonnet and Haiku
- [ ] Quality comparison documented (at least 3 sample documents)
