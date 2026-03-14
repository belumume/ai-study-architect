---
title: "Claude Code Review Action silently discards findings with read-only permissions"
category: integration-issues
date: 2026-03-14
tags: [github-actions, claude-code-action, permissions, ci, silent-failure]
module: CI/CD
symptom: "Claude Code Review action completes successfully but posts no review comments"
root_cause: "GITHUB_TOKEN has pull-requests: read, action needs pull-requests: write to post comments"
---

# Claude Code Review Action Silently Discards Findings

## Problem

The Claude Code Review GitHub Action (`anthropics/claude-code-action@v1`) ran on every PR, completed "successfully" (green check), spent $0.63+ per run on API calls, but never posted any review comments. It appeared to be working but was silently discarding all findings.

## Root Cause

The workflow had `pull-requests: read` in the permissions block. The action needs `pull-requests: write` to post inline comments and review summaries. Without write access, the post-review step (`post-buffered-inline-comments.ts`) silently produces "No buffered inline comments" — making it look like the review found nothing, when in reality it found things but couldn't post them.

The `permission_denials_count: 2` in the action logs was the only clue.

## Solution

```yaml
# .github/workflows/claude-code-review.yml
permissions:
  contents: read
  pull-requests: write  # was: read — MUST be write for posting comments
  issues: read
  id-token: write
```

For the interactive Claude Code action (`claude.yml`) that responds to @claude mentions:
```yaml
permissions:
  contents: read
  pull-requests: write  # was: read
  issues: write         # was: read — needs write to respond on issues
  id-token: write
```

## Official Documentation

The [claude-code-action setup docs](https://github.com/anthropics/claude-code-action) specify minimum permissions:
- Contents: Read & Write
- Issues: Read & Write
- Pull requests: Read & Write

## Prevention

When setting up any GitHub Action that posts comments/reviews, always set `write` permissions. `read` is only appropriate for actions that purely analyze without posting results.

## Detection

Look for `permission_denials_count` > 0 in the action logs. Also check for "No buffered inline comments" in a review that should have found issues (e.g., a PR with known test failures).
