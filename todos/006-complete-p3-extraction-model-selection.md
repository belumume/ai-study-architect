---
status: complete
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

- [x] `CLAUDE_EXTRACTION_MODEL` env var is configurable
- [x] Extraction works with both Sonnet and Haiku (validated in spike tests)
- [x] Quality comparison documented (hash tables academic text):
  - Sonnet: 15 concepts, 21 deps, 51s, $0.057/extraction — better SVO names
  - Haiku: 13 concepts, 18 deps, 20s, $0.016/extraction — 3.6x cheaper, 2.6x faster
  - Default changed to claude-haiku-4-5 for cost/speed; override via CLAUDE_EXTRACTION_MODEL
