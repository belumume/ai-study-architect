---
status: pending
priority: p2
issue_id: "009"
tags: [code-review, performance, caching]
dependencies: []
---

# Implement dashboard Redis caching (documented but never built)

## Problem Statement

CLAUDE.md and project memory both reference "Dashboard 3-query: Redis cache 60s TTL" but the dashboard endpoint has zero caching code. All 5 queries run against Neon PostgreSQL on every request. At 100+ concurrent users, this will exhaust Neon's 100-connection limit.

## Proposed Solution

Add per-user Redis caching with 60s TTL. Cache key: `dashboard:{user_id}`. Use existing `app.core.cache` infrastructure (already available but unused by dashboard). Invalidation via TTL expiry — 60s is short enough that session changes reflect within a minute.

## Acceptance Criteria

- [ ] Dashboard response cached in Redis with 60s TTL per user
- [ ] Cache hit skips all 5 database queries
- [ ] Cache miss runs queries and stores result
- [ ] Existing tests still pass
